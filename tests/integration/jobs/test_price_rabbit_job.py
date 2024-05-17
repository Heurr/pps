import asyncio
from uuid import UUID

import orjson
import pytest
from aio_pika.abc import (
    AbstractChannel,
    AbstractExchange,
    AbstractIncomingMessage,
    AbstractQueue,
)
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app import crud
from app.config.settings import JobSettings, ProductPricePublishSettings
from app.constants import PRICE_EVENT_QUEUE, ProductPriceType
from app.jobs.base import BaseJob
from app.jobs.price_publish import PublishingPriceJob
from tests.factories import offer_factory, product_price_factory
from tests.utils import custom_uuid, override_obj_get_db_conn


@pytest.fixture
async def settings() -> ProductPricePublishSettings:
    settings = ProductPricePublishSettings()
    settings.RABBITMQ_EXCHANGE_NAME = "test-ex"
    return settings


@pytest.fixture
async def rmq_queue(
    rmq_channel: AbstractChannel,
    rmq_exchange: AbstractExchange,
    settings: ProductPricePublishSettings,
) -> AbstractQueue:
    queue = await rmq_channel.declare_queue(
        "testing-queue", durable=False, auto_delete=True
    )
    await queue.bind("test-ex", settings.ROUTING_KEY)
    yield queue


@pytest.fixture
async def rabbit_feeder_job(
    rmq_queue: AbstractQueue,
    db_engine: AsyncEngine,
    db_conn: AsyncConnection,
    redis: Redis,
    settings: ProductPricePublishSettings,
):
    job = PublishingPriceJob(PRICE_EVENT_QUEUE, db_engine, redis, JobSettings(), settings)
    override_obj_get_db_conn(db_conn, job)
    job_task = asyncio.create_task(job.run())
    await asyncio.sleep(0.1)
    yield job

    job.stop()
    await asyncio.wait_for(job_task, timeout=1)


async def push_to_redis_queue(
    job: BaseJob, product_ids: list[UUID], wait: float = 0.3
) -> None:
    await job.redis.lpush(job.redis_queue, *[obj.bytes for obj in product_ids])
    await asyncio.sleep(wait)


@pytest.mark.anyio
async def test_price_rabbit_job(
    db_conn,
    rabbit_feeder_job: PublishingPriceJob,
    caplog,
    rmq_queue,
    rmq_exchange,
    rmq_channel,
    settings: ProductPricePublishSettings,
):
    products = [
        await product_price_factory(
            product_id=custom_uuid(i), min_price=1, price_type=ProductPriceType.ALL_OFFERS
        )
        for i in range(3)
    ]
    products.append(
        await product_price_factory(
            product_id=custom_uuid(2),
            min_price=1,
            price_type=ProductPriceType.MARKETPLACE,
        )
    )  # add to last two price types

    await crud.product_price.create_many(db_conn, products)

    [
        await offer_factory(
            db_conn=db_conn,
            offer_id=custom_uuid(i),
            product_id=custom_uuid(3),
            price=10 + i,
        )
        for i in range(3)
    ]
    await push_to_redis_queue(
        rabbit_feeder_job,
        [
            # Create an upsert
            custom_uuid(0),
            custom_uuid(1),
            custom_uuid(2),
        ],
    )

    msgs: list[AbstractIncomingMessage] = []
    async with rmq_queue.iterator(timeout=1) as queue_iterator:
        async for msg in queue_iterator:
            msgs.append(msg)
            if len(msgs) == 1:
                break

    msgs_by_routing_key = {msg.routing_key: msg.body for msg in msgs}
    msg = orjson.loads(msgs_by_routing_key[settings.ROUTING_KEY])

    assert list(msgs_by_routing_key.keys()) == [settings.ROUTING_KEY]

    assert len(msg) == 3

    assert msg[0]["product_id"] == str(custom_uuid(0))
    assert msg[1]["product_id"] == str(custom_uuid(1))
    assert msg[2]["product_id"] == str(custom_uuid(2))

    assert len(msg[0]["prices"]) == 1
    assert len(msg[1]["prices"]) == 1
    assert len(msg[2]["prices"]) == 2

    assert caplog.messages == [
        "Processing 3 objects",
        "Published 3 price entities to RabbitMQ",
    ]
