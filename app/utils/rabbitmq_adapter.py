import logging

from aio_pika import connect_robust
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection

logger = logging.getLogger(__name__)


class BaseRabbitmqAdapter:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.connection: AbstractRobustConnection | None = None
        self.channel: AbstractRobustChannel | None = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self):
        logger.info("Connecting to RabbitMQ %s", self.dsn)
        self.connection = await connect_robust(self.dsn)
        self.channel = await self.connection.channel()

    async def disconnect(self):
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ server")
