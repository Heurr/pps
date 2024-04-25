import logging
from enum import Enum

from aio_pika import connect_robust
from aio_pika.abc import (
    AbstractQueueIterator,
    AbstractRobustChannel,
    AbstractRobustConnection,
    AbstractRobustQueue,
)

from app.config.settings import ConsumerSettings
from app.constants import Entity

logger = logging.getLogger(__name__)


class Action(Enum):
    UPSERT = "upsert"
    DELETE = "delete"


class RMQClient:
    def __init__(self, entity: Entity, settings: ConsumerSettings):
        self.settings = settings
        self.entity = entity
        self.rmq_url = settings.rabbitmq_dsn(entity)
        self.exchange_name = settings.rabbitmq_exchange_name(entity)
        self.queue_name = f"op-pps-consumer-{entity.value}"
        if settings.RABBITMQ_QUEUE_POSTFIX:
            self.queue_name += f"-{settings.RABBITMQ_QUEUE_POSTFIX}"
        self.create_queues = settings.RABBITMQ_CREATE_QUEUES
        self.prefetch_count = settings.RABBITMQ_PREFETCH_COUNT
        self.push_interval = settings.redis_push_interval(entity)
        self.connection: AbstractRobustConnection
        self.channel: AbstractRobustChannel
        self.queue: AbstractRobustQueue

    async def __aenter__(self):
        self.connection = await connect_robust(self.rmq_url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=self.prefetch_count)
        logger.info("Connected to RabbitMQ %s", self.rmq_url)
        await self._init_queue()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.connection.close()

    async def _init_queue(self):
        if self.create_queues:
            queue_operation = "Declare"
            routing_keys = self.settings.rabbitmq_entity_queue_mapping(self.entity)[
                "routingKeys"
            ]
            if not isinstance(routing_keys, list):
                routing_keys = [routing_keys]
            # Use for testing, it ensures the queue is empty at the start of each test
            self.queue = await self.channel.declare_queue(
                self.queue_name, durable=False, auto_delete=True
            )
            # Binding the queue to the exchange by all routing keys for tests
            for routing_key in routing_keys:
                await self.queue.bind(self.exchange_name, routing_key)
                logger.info(
                    "Bind routing key %s to queue %s",
                    routing_key,
                    self.queue_name,
                )
        else:
            queue_operation = "Using"
            self.queue = await self.channel.get_queue(self.queue_name)
        logger.info("%s queue %s", queue_operation, self.queue_name)

    def iterator(self) -> AbstractQueueIterator:
        return self.queue.iterator(timeout=self.push_interval, no_ack=True)
