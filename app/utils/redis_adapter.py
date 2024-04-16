import logging

import redis.asyncio as async_redis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisAdapter:
    def __init__(self, dsn: str, **kwargs) -> None:
        self.dsn = dsn
        self.redis: Redis | None = None
        self.config = kwargs

    async def __aenter__(self) -> Redis:
        self.redis = await async_redis.from_url(self.dsn, **self.config).client()
        logger.info("Connected to Redis server.")
        return self.redis

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.redis:
            await self.redis.aclose()  # type: ignore[attr-defined]
            await self.redis.connection_pool.disconnect()
            logger.info("Disconnected from Redis server")
