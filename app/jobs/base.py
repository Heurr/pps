import logging
from contextlib import asynccontextmanager

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config.settings import JobSettings
from app.metrics import JOB_METRICS, JOB_TIMER, PerformanceTimer


class BaseJob:
    def __init__(
        self, name: str, db_engine: AsyncEngine, redis: Redis, settings: JobSettings
    ):
        self.db_engine = db_engine
        self.name = name
        self.redis = redis
        self.redis_queue = name
        self.buffer_size = settings.JOB_BATCH_SIZE
        self.redis_pop_timeout = settings.JOB_QUEUE_POP_TIMEOUT
        self.logger = logging.getLogger(__name__)
        self.should_compute = True
        self.metrics = JOB_METRICS
        self.performance_metrics = JOB_TIMER

    @asynccontextmanager
    async def get_db_conn(self):
        async with self.db_engine.begin() as conn:
            yield conn

    async def read(self) -> list:
        raise NotImplementedError("Method read not implemented")

    async def process(self, ids: list) -> None:
        raise NotImplementedError("Method process not implemented")

    async def run(self) -> None:
        self.logger.info("Job started, reading queue %s", self.redis_queue)
        try:
            while self.should_compute:
                objs = await self.read()
                if len(objs) != 0:
                    self.logger.info("Processing %i objects", len(objs))
                    self.metrics.labels(name=self.name, stage="load").inc(len(objs))
                    with PerformanceTimer(
                        self.performance_metrics.labels(name=self.name)
                    ):
                        await self.process(objs)
        except Exception as ex:
            self.logger.error("Job execution failed", exc_info=ex)
        self.logger.info("Job with queue %s stopped", self.redis_queue)

    def stop(self) -> None:
        self.should_compute = False
