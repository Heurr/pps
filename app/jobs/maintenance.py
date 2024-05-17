import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import timedelta

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app import crud
from app.config.settings import MaintenanceJobSettings
from app.constants import PROCESS_SAFE_FLAG_REDIS_QUEUE_NAME
from app.db.pg import get_table_names
from app.utils import utc_now, utc_today
from app.utils.pg_partitions import (
    async_create_product_prices_part_tables_for_day,
    get_product_price_partition_name,
)


class MaintenanceJob:
    def __init__(
        self,
        db_engine: AsyncEngine,
        redis: Redis,
        job_settings: MaintenanceJobSettings | None = None,
    ):
        job_settings = job_settings or MaintenanceJobSettings()
        self.db_engine = db_engine
        self.history_interval = job_settings.HISTORY_INTERVAL_IN_DAYS
        self.partitions_ahead = job_settings.PARTITIONS_AHEAD
        self.partitions_fill_factor = job_settings.PARTITIONS_FILL_FACTOR
        self.process_safe_flag_name = PROCESS_SAFE_FLAG_REDIS_QUEUE_NAME
        self.wait_for_new_day = job_settings.WAIT_FOR_NEW_DAY
        self.redis = redis
        self.timeout = job_settings.SLEEP_TIMEOUT

        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def get_db_conn(self):
        async with self.db_engine.begin() as conn:
            yield conn

    async def run(self):
        """
        Run the maintenance job only when the next day
        starts, we don't want to start copying data to the new
        day without being sure that the previous day is over.
        """
        if self.wait_for_new_day:
            self.logger.info("Waiting for new day to start")

        start_day = utc_today()
        while start_day == utc_today() and self.wait_for_new_day:
            await asyncio.sleep(self.timeout)

        await self.set_process_safe_flag(True)
        async with self.get_db_conn() as conn:
            await self.delete_old_product_prices(conn)
            await self.create_new_product_prices_partition(conn)
            await self.create_new_product_prices(conn)
        await self.set_process_safe_flag(False)

    async def delete_old_product_prices(self, db_conn: AsyncConnection):
        delete_before = utc_today() - timedelta(days=self.history_interval)
        self.logger.info("Deleting product prices older than %s", delete_before)
        try:
            await crud.product_price.remove_history(db_conn, delete_before)
        except Exception as ex:
            self.logger.error("Deletion failed", exc_info=ex)
        self.logger.info("Done deleting")

    async def create_new_product_prices_partition(self, db_conn: AsyncConnection):
        existing_tables = await get_table_names(db_conn)
        today = utc_today()
        timerange = [
            today + timedelta(days=i) for i in range(1, self.partitions_ahead + 1)
        ]

        for day in timerange:
            new_table = get_product_price_partition_name(day)
            if new_table in existing_tables:
                continue
            self.logger.info("Creating table %s", new_table)
            await async_create_product_prices_part_tables_for_day(
                db_conn, day, self.partitions_fill_factor
            )
        self.logger.info("Done creating new partitions")

    async def create_new_product_prices(self, db_conn: AsyncConnection):
        now = utc_now()
        yesterday = now.date() - timedelta(days=1)
        self.logger.info("Duplicating %s product prices to today", yesterday)
        await crud.product_price.duplicate_day(db_conn, yesterday)
        end = utc_now()
        self.logger.info("Done duplicating in %s", end - now)

    async def set_process_safe_flag(self, flag: bool):
        self.logger.info("Setting process safe flag to %s", flag)
        await self.redis.set(self.process_safe_flag_name, "1" if flag else "0")
