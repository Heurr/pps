import asyncio
from datetime import timedelta
from typing import cast
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app import crud
from app.config.settings import JobSettings
from app.constants import (
    PROCESS_SAFE_FLAG_REDIS_QUEUE_NAME,
    PUBLISHER_REDIS_QUEUE_NAME,
)
from app.custom_types import BasePricePk, ProductPricePk
from app.jobs.base import BaseJob
from app.schemas.price_event import PriceEvent
from app.schemas.product_price import ProductPriceDBSchema
from app.services.event_processing import EventProcessingService
from app.services.product_price import ProductPriceService
from app.utils import utc_today


class PriceEventJob(BaseJob):
    def __init__(
        self, name: str, db_engine: AsyncEngine, redis: Redis, settings: JobSettings
    ):
        super().__init__(name, db_engine, redis, settings)
        self.publisher_queue = PUBLISHER_REDIS_QUEUE_NAME
        self.process_safe_flag_name = PROCESS_SAFE_FLAG_REDIS_QUEUE_NAME
        self.product_price_service = ProductPriceService()
        self.event_processing_service = EventProcessingService()

    async def read(self) -> list[PriceEvent]:
        res = cast(
            list[bytes], await self.redis.lpop(self.redis_queue, count=self.buffer_size)
        )
        if not res:
            await asyncio.sleep(self.redis_pop_timeout)
            return []

        return [PriceEvent.model_validate_json(obj) for obj in res]

    async def process(self, objs: list[PriceEvent]) -> None:
        async with self.get_db_conn() as conn:
            product_prices = await self.get_product_prices_by_events(conn, objs)
            proc_result = await self.event_processing_service.process_events_bulk(
                conn, objs, product_prices
            )

            updated = await self.product_price_service.upsert_many(
                conn, proc_result.upserted, list(product_prices.values())
            )
            deleted = await crud.product_price.remove_many(
                conn, proc_result.deletes, utc_today()
            )

        self.logger.info(
            "upserted %i | deleted %i | obsolete %i | unchanged %i",
            len(updated),
            len(deleted),
            proc_result.obsolete,
            proc_result.unchanged,
        )
        self.metrics.labels(name=self.name, stage="upsert").inc(len(updated))
        self.metrics.labels(name=self.name, stage="delete").inc(len(deleted))
        self.metrics.labels(name=self.name, stage="not_changed").inc(
            proc_result.unchanged
        )
        self.metrics.labels(name=self.name, stage="obsolete").inc(proc_result.obsolete)

        publish_ids = {pk.product_id for pk in updated}
        if deleted:
            publish_ids |= {pk.product_id for pk in deleted}
        # Temporary disabled publishing until publisher job is implemented
        # await self.push_to_publisher_queue(publish_ids)

    async def push_to_publisher_queue(self, product_ids: set[UUID]) -> None:
        if product_ids:
            self.logger.info(
                "Push %i product ids to the publisher queue", len(product_ids)
            )
            await self.redis.sadd(
                self.publisher_queue, *[product_id.bytes for product_id in product_ids]
            )

    async def get_process_safe_flag(self) -> bool:
        """
        This flag is used during a period where we are migrating
        today's data to tomorrow's data where it might happen that
        the copying process is not yet done
        """
        res = await self.redis.get(self.process_safe_flag_name)
        if res:
            return res == b"1"
        return False

    async def get_product_prices_by_events(
        self, conn: AsyncConnection, events: list[PriceEvent]
    ) -> dict[BasePricePk, ProductPriceDBSchema]:
        """
        Get product prices from the database, if safe processing is enabled
        (during the copying of yesterday's prices), get the missing prices
        from the previous day as a fallback
        """
        product_prices = await crud.product_price.get_in(
            conn,
            [
                ProductPricePk(utc_today(), event.product_id, event.type)
                for event in events
            ],
        )

        if await self.get_process_safe_flag():
            product_price_ids = {price.product_id for price in product_prices}
            yesterdays_product_prices = await crud.product_price.get_in(
                conn,
                [
                    ProductPricePk(
                        utc_today() - timedelta(days=1), event.product_id, event.type
                    )
                    for event in events
                    if event.product_id not in product_price_ids
                ],
            )
            product_prices.extend(yesterdays_product_prices)
        return {
            BasePricePk(product_price.product_id, product_price.price_type): product_price
            for product_price in product_prices
        }
