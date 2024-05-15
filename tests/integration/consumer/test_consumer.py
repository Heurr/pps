import asyncio
from asyncio import QueueEmpty

import pytest
from aio_pika import IncomingMessage
from aio_pika.abc import AbstractChannel
from redis.asyncio import Redis

from app.config.settings import ConsumerSettings
from app.constants import Entity
from app.consumers.consumer import Consumer
from app.exceptions import RedisFullError
from tests.integration.consumer.conftest import REDIS_KEYS_MAP, publish
from tests.utils import custom_uuid


def msg_body(
    entity_type: str,
    action: str,
    i: int = 1,
    version: int = 1,
    country: str | None = None,
) -> dict:
    msg = {
        entity_type: {"id": custom_uuid(i)},
        "action": action,
        "version": version,
    }
    if country:
        msg["legacy"] = {"countryCode": country}
    return msg


def get_queue_name(settings: ConsumerSettings, entity: Entity) -> str:
    return f"op-pps-consumer-{entity.value}-{settings.CONSUMER_RABBITMQ_QUEUE_POSTFIX}"


async def wait_for_empty_rmq_queue(
    channel: AbstractChannel, entity: Entity, settings: ConsumerSettings, max_retries: int
):
    queue = await channel.get_queue(get_queue_name(settings, entity))
    for _ in range(max_retries):
        try:
            msg = await queue.get()
            await msg.reject(requeue=True)
        except QueueEmpty:
            break
        await asyncio.sleep(0.05)


async def wait_for_redis(redis: Redis, seconds: int):
    timeout = 0.05
    for _ in range(int((1 / timeout)) * seconds):
        if await redis.keys():
            return
        await asyncio.sleep(timeout)


async def wait_for_redis_key(redis: Redis, seconds: int, key: str, target: int):
    timeout = 0.05
    for _ in range(int((1 / timeout)) * seconds):
        if (await redis.llen(key)) == target:
            return
        await asyncio.sleep(timeout)


@pytest.mark.anyio
@pytest.mark.parametrize("entity", [Entity.OFFER])
async def test_empty_message_list(
    rmq_exchange, rmq_channel, redis, consumer, settings, caplog
):
    await consumer.process_message_buffer([])
    assert "No messages, nothing to be pushed to Redis" in caplog.messages


@pytest.mark.anyio
@pytest.mark.parametrize("action", ["insert", "update", "delete"])
@pytest.mark.parametrize("entity", list(Entity))
async def test_consume_non_filtered_country(
    rmq_exchange, rmq_channel, redis, settings, consumer, entity, action
):
    """
    Test consuming every entity type with every action, simulating real life flow.
    Consumer is dynamically changed based on entity given.
    No country is filtered out so all messages will be processed.
    Assert against values retrieved from REDIS_KEYS_MAP.
    """
    for _ in range(4):
        await publish(
            rmq_exchange,
            f"op.pps.{entity.value}.{action}",
            msg_body(entity.value, action, country=None),  # all will be processed
        )

    await asyncio.sleep(0.4)

    await wait_for_empty_rmq_queue(rmq_channel, entity, settings, 20)
    await wait_for_redis(redis, 5)
    assert await redis.keys() == [REDIS_KEYS_MAP[entity].encode("UTF-8")]
    await wait_for_redis_key(redis, seconds=5, key=REDIS_KEYS_MAP[entity], target=4)
    assert await redis.llen(REDIS_KEYS_MAP[entity]) == 4


@pytest.mark.anyio
@pytest.mark.parametrize("action", ["insert", "update", "delete"])
@pytest.mark.parametrize("entity", [Entity.OFFER])
async def test_consume_filtered_country_is_skipped(  # noqa: PLR0913
    rmq_exchange, rmq_channel, redis, consumer, settings, caplog, action, entity
):
    """
    Test consuming entity which has country set to be skipped.
    See fixture Setting Entity.OFFER: {"filteredCountries": ["CZ"]}.
    """
    await publish(
        rmq_exchange,
        f"op.pps.{entity.value}.{action}",
        msg_body(entity.value, action, country="CZ"),  # skip CZ
    )

    await asyncio.sleep(0.2)

    await wait_for_empty_rmq_queue(rmq_channel, entity, settings, 20)
    assert await redis.keys() == []
    assert await redis.llen(REDIS_KEYS_MAP[entity.value]) == 0
    assert caplog.messages[0] == "Messages skipped: 1. Countries skipped: {'CZ'}"
    assert caplog.messages[-1] == "No messages, nothing to be pushed to Redis"


@pytest.mark.anyio
async def test_stop_all_after_exc(rmq_exchange, settings, caplog):
    """
    Test against a consumer that throws error.
    """

    class BadConsumer(Consumer):
        async def process_message(self, orig_message: IncomingMessage):  # noqa: ARG002
            raise Exception("Test exception")

    consumer = BadConsumer(Entity.OFFER, settings)
    task = asyncio.create_task(consumer.run())
    await asyncio.sleep(0.05)
    await publish(rmq_exchange, "op.pps.offer.insert", msg={})
    await task
    assert "Stopping offer consumer" in caplog.messages
    assert (
        "Consumer offer for queue op-pps-consumer-offer-test stopped" in caplog.messages
    )


@pytest.mark.parametrize("free_memory_in_pct", [5])
@pytest.mark.parametrize("entity", [Entity.OFFER])
@pytest.mark.anyio
async def test_consumer_pushes_to_redis_when_full(
    rmq_exchange,
    consumer,
    caplog,
    settings,
    redis_full,
):
    """
    Test redis will get no message if it is full.
    """
    with pytest.raises(RedisFullError):
        await consumer.push_messages_to_redis([b"message1", b"message2"])

    assert await redis_full.llen(REDIS_KEYS_MAP[Entity.OFFER]) == 0
    assert caplog.messages[0] == "Pushing 2 message(s) to redis list rmq-offer"
    assert caplog.messages[-1] == "Redis is 90 pct full, 2 messages are nacked"


@pytest.mark.parametrize("free_memory_in_pct", [50])
@pytest.mark.parametrize("entity", [Entity.OFFER])
@pytest.mark.anyio
async def test_consumer_pushes_to_redis_when_not_full(
    rmq_exchange,
    rmq_channel,
    consumer,
    caplog,
    settings,
    redis_full,
):
    """
    Test redis will get message if it is not yet full.
    """
    await publish(rmq_exchange, "op.pps.offer.insert", msg={})
    await wait_for_empty_rmq_queue(rmq_channel, Entity.OFFER, settings, 20)
    await wait_for_redis(redis_full, 10)
    assert await redis_full.llen(REDIS_KEYS_MAP[Entity.OFFER]) == 1
    assert "Pushing 1 message(s) to redis list rmq-offer" in caplog.messages


@pytest.mark.anyio
@pytest.mark.parametrize("entity", [Entity.OFFER])
async def test_timeout_error(rmq_exchange, redis, caplog, consumer, mocker):
    """
    Test message will not be delivered to redis due to timeout
    """
    consumer_mock = mocker.patch(
        f"{Consumer.__module__}.{Consumer.__qualname__}.on_message"
    )
    consumer_mock.side_effect = [None] * 4 + [asyncio.exceptions.TimeoutError()]
    for _i in range(5):
        await publish(rmq_exchange, "op.pps.offer.insert", msg={})
    await asyncio.sleep(1)
    await wait_for_redis(redis, 10)
    assert await redis.llen(REDIS_KEYS_MAP[Entity.OFFER]) == 4
