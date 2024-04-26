import signal
from logging import getLogger

from aio_pika.abc import AbstractIncomingMessage
from api_principles.message import Message  # type: ignore[import-untyped]
from api_principles.rabbitmq import (  # type: ignore[import-untyped]
    ContentTypeDecoder,
    RabbitMQBatchConsumer,
)
from redis import RedisError
from redis.asyncio import Redis

from app.config.settings import ConsumerSettings
from app.constants import Entity
from app.consumers.rabbitmq_client import RabbitmqConsumerClient
from app.exceptions import RedisFullError
from app.metrics import ENTITY_METRICS
from app.parsers import parser_from_entity
from app.schemas.message import InvalidMessageSchema
from app.utils.redis_adapter import RedisAdapter


#
class DummyDecoder(ContentTypeDecoder):
    def decode(self, original_message: AbstractIncomingMessage) -> Message:
        return Message(
            headers=original_message.headers,
            body=[original_message.body],
            metadata={
                "routing_key": original_message.routing_key,
            },
        )


class Consumer(RabbitMQBatchConsumer):
    def __init__(self, entity: Entity, settings: ConsumerSettings):
        self.entity = entity
        self.rmq = RabbitmqConsumerClient(entity, settings)
        self.redis: Redis | None = None
        self.redis_dsn = settings.redis_dsn
        self.redis_list = f"rmq-{entity.value}"
        self.redis_capacity = settings.CONSUMER_REDIS_CAPACITY_THRESHOLD_IN_PERCENT
        self.parser = parser_from_entity(entity, throw_errors=False)
        self.filtered_countries = settings.filtered_countries(entity)
        self.register_signals()
        self.logger = getLogger(self.__class__.__name__)

    async def run(self):
        try:
            async with RedisAdapter(self.redis_dsn) as redis, self.rmq:
                super().__init__(
                    self.rmq.queue,
                    decoder=DummyDecoder(),
                    max_delay=self.rmq.push_interval,
                    max_item_count=self.rmq.prefetch_count,
                    iterator_timeout=1,
                    iterator_timeout_sleep=0.05,
                )
                self.redis = redis

                self.logger.info(
                    "Start consuming %s queue %s",
                    self.entity.value,
                    self.rmq.queue_name,
                )
                await self.consume()

        except Exception as exc:
            self.stop()
            self.logger.error(
                "Consumer stopping due to error: type: %s, message: %s",
                type(exc),
                str(exc),
            )
            ENTITY_METRICS.labels(
                entity=self.entity.value, phase="consumer", operation="discard"
            )
        finally:
            self.logger.info(
                "Consumer %s for queue %s stopped",
                self.entity.value,
                self.rmq.queue_name,
            )

    async def get_redis_memory_usage(self) -> float:
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        memory = await self.redis.info("memory")
        return memory["used_memory"] / memory["maxmemory"] * 100

    async def on_batch(self, messages: list[Message]):
        if messages:
            ENTITY_METRICS.labels(
                entity=self.entity.value, phase="consumer", operation="read"
            )
            if not self.redis:
                raise RuntimeError("Redis not initialized")

            await self.process_message_buffer(messages)

    async def process_message_buffer(self, messages: list[Message]):
        msg_bodies = []
        skipped_messages, skipped_countries = 0, set()

        for msg in messages:
            msg_schema = self.parser.parse_message_body(msg.body[0])
            if isinstance(msg_schema, InvalidMessageSchema):
                continue

            if msg_schema.country_code in self.filtered_countries:
                skipped_messages += 1
                skipped_countries.add(msg_schema.country_code)
                continue

            msg_bodies.append(msg.body[0])

        if skipped_messages:
            self.logger.info(
                "Messages skipped: %d. Countries skipped: %s",
                skipped_messages,
                skipped_countries,
            )

        if not msg_bodies:
            self.logger.info("No messages, nothing to be pushed to Redis")
        else:
            await self.push_messages_to_redis(msg_bodies)

    async def push_messages_to_redis(self, msg_bodies: list[bytes]) -> None:
        self.logger.info(
            "Pushing %i message(s) to redis list %s",
            len(msg_bodies),
            self.redis_list,
        )
        try:
            if await self.get_redis_memory_usage() > self.redis_capacity:
                self.logger.error(
                    "Redis is %i pct full, %i messages are nacked",
                    self.redis_capacity,
                    len(msg_bodies),
                )
                ENTITY_METRICS.labels(
                    entity=self.entity.value, phase="consumer", operation="nacked"
                )
                raise RedisFullError("Redis is full.")
            else:
                await self.redis.lpush(  # type: ignore[union-attr]
                    self.redis_list, *msg_bodies
                )
        except RedisError as exc:
            self.logger.error("Error while pushing messages to redis: %s", exc)
            ENTITY_METRICS.labels(
                entity=self.entity.value, phase="consumer", operation="discard"
            )

    def stop(self, _signum=None, _frame=None) -> None:
        self.logger.info("Stopping %s consumer", self.entity.value)
        self.stop_consuming()

    def register_signals(self) -> None:
        for signum in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(signum, self.stop)
