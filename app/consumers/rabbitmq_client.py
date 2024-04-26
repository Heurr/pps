import logging

from aio_pika.abc import AbstractQueueIterator, AbstractRobustQueue

from app.config.settings import ConsumerSettings
from app.constants import Entity
from app.utils.rabbitmq_adapter import BaseRabbitmqAdapter

logger = logging.getLogger(__name__)


class RabbitmqConsumerClient(BaseRabbitmqAdapter):
    def __init__(self, entity: Entity, settings: ConsumerSettings):
        super().__init__(settings.rabbitmq_dsn(entity))
        self.settings = settings
        self.entity = entity
        self.exchange_name = settings.rabbitmq_exchange_name(entity)
        self.queue_name = f"op-pps-consumer-{entity.value}"
        if settings.CONSUMER_RABBITMQ_QUEUE_POSTFIX:
            self.queue_name += f"-{settings.CONSUMER_RABBITMQ_QUEUE_POSTFIX}"
        self.create_queues = settings.CONSUMER_RABBITMQ_CREATE_QUEUES
        self.prefetch_count = settings.RABBITMQ_PREFETCH_COUNT
        self.push_interval = settings.redis_push_interval(entity)
        self.queue: AbstractRobustQueue

    async def connect(self):
        await super().connect()
        await self.channel.set_qos(prefetch_count=self.prefetch_count)
        await self._init_queue()

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
