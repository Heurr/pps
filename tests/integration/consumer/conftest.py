import asyncio

import orjson
import pytest
from aio_pika import ExchangeType, Message, connect_robust
from aio_pika.abc import AbstractChannel, AbstractExchange, DeliveryMode
from redis.asyncio import Redis

from app.config.settings import ConsumerSettings
from app.constants import RABBITMQ_MSG_CONTENT_TYPE_JSON, Entity
from app.consumers.consumer import Consumer
from app.utils.redis_adapter import RedisAdapter

REDIS_KEYS_MAP = {
    Entity.OFFER: "rmq-offer",
    Entity.SHOP: "rmq-shop",
    Entity.BUYABLE: "rmq-buyable",
    Entity.AVAILABILITY: "rmq-availability",
}


@pytest.fixture
def settings() -> ConsumerSettings:
    settings = ConsumerSettings()
    settings.CONSUMER_RABBITMQ_CREATE_QUEUES = True
    settings.CONSUMER_RABBITMQ_QUEUE_POSTFIX = "test"
    settings.RABBITMQ_EXCHANGE_NAME = "test-ex"
    settings.CONSUMER_RABBITMQ_ENTITIES = {
        Entity.SHOP: {},
        Entity.OFFER: {"filteredCountries": ["CZ"]},
        Entity.BUYABLE: {},
        Entity.AVAILABILITY: {},
    }
    settings.RABBITMQ_PREFETCH_COUNT = 1
    settings.CONSUMER_RABBITMQ_QUEUE_MAPPING = {
        Entity.SHOP: {
            "redisPushInterval": 0.05,
            "routingKeys": [
                "op.pps.shop.insert",
                "op.pps.shop.update",
                "op.pps.shop.delete",
            ],
            "exchange": "test-ex",
        },
        Entity.OFFER: {
            "redisPushInterval": 0.05,
            "routingKeys": [
                "op.pps.offer.insert",
                "op.pps.offer.update",
                "op.pps.offer.delete",
            ],
            "exchange": "test-ex",
        },
        Entity.AVAILABILITY: {
            "redisPushInterval": 0.05,
            "routingKeys": [
                "op.pps.availability.insert",
                "op.pps.availability.update",
                "op.pps.availability.delete",
            ],
            "exchange": "test-ex",
        },
        Entity.BUYABLE: {
            "redisPushInterval": 0.05,
            "routingKeys": [
                "op.pps.buyable.insert",
                "op.pps.buyable.update",
                "op.pps.buyable.delete",
            ],
            "exchange": "test-ex",
        },
    }
    return settings


@pytest.fixture
async def rmq_channel(settings) -> AbstractChannel:
    connection = await connect_robust(settings.rabbitmq_dsn())
    channel = await connection.channel()
    yield channel
    await connection.close()


@pytest.fixture
async def rmq_exchange(rmq_channel: AbstractChannel, settings) -> AbstractExchange:
    exchange = await rmq_channel.declare_exchange(
        settings.RABBITMQ_EXCHANGE_NAME,
        type=ExchangeType.TOPIC,
        auto_delete=True,
    )
    yield exchange


@pytest.fixture
async def redis_full(settings, free_memory_in_pct: int) -> Redis:
    async with RedisAdapter(settings.redis_dsn, decode_responses=False) as redis:
        await redis.flushdb()

        mem = await redis.info("memory")
        original_max_memory = mem["maxmemory"]
        new_max_memory = mem["used_memory"] * 100 / (100 - free_memory_in_pct)
        await redis.config_set("maxmemory", int(new_max_memory))
        yield redis
        await redis.config_set("maxmemory", original_max_memory)
        await redis.info("memory")


async def publish(
    exchange: AbstractExchange,
    routing_key: str,
    msg: dict | None = None,
) -> None:
    msg = Message(
        body=orjson.dumps(msg),
        content_type=RABBITMQ_MSG_CONTENT_TYPE_JSON,
        delivery_mode=DeliveryMode.NOT_PERSISTENT,
    )
    await exchange.publish(msg, routing_key)


@pytest.fixture()
async def consumer(settings: ConsumerSettings, entity: Entity):
    """
    Parametrized consumer, changes based on entity given.
    It is used in test_consume
    """
    consumer = Consumer(entity, settings)
    consumer.redis_capacity = 90
    task = asyncio.create_task(consumer.run())
    await asyncio.sleep(0.05)
    yield consumer
    consumer.stop_consuming()
    await task
