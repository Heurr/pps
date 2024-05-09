import asyncio

import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app import crud
from app.config.settings import JobSettings
from app.constants import PUBLISHER_REDIS_QUEUE_NAME, ProductPriceType
from app.jobs.base import BaseJob
from app.jobs.price_event import PriceEventJob
from app.schemas.price_event import PriceEvent, PriceEventAction
from app.utils import dump_to_json
from tests.factories import offer_factory, price_event_factory
from tests.utils import custom_uuid, override_obj_get_db_conn


@pytest.fixture
async def entity_population_job(
    db_engine: AsyncEngine,
    db_conn: AsyncConnection,
    redis: Redis,
):
    job = PriceEventJob("price-event", db_engine, redis, JobSettings())
    override_obj_get_db_conn(db_conn, job)
    job_task = asyncio.create_task(job.run())
    await asyncio.sleep(0.1)
    yield job

    job.stop()
    await asyncio.wait_for(job_task, timeout=1)


async def push_to_redis_queue(
    job: BaseJob, ids: list[PriceEvent], wait: float = 0.3
) -> None:
    await job.redis.lpush(job.redis_queue, *[dump_to_json(obj) for obj in ids])
    await asyncio.sleep(wait)


@pytest.mark.anyio
async def test_price_event_job(
    db_conn, entity_population_job: PriceEventJob, caplog, redis
):
    """
    Generate 3 waves of events, test the most common scenarios, see comments
    below for more details.
    """

    # Create offers for product 4 to get a new max
    await offer_factory(
        db_conn=db_conn,
        offer_id=custom_uuid(1),
        product_id=custom_uuid(1),
        buyable=False,
        price=10,
    )

    await push_to_redis_queue(
        entity_population_job,
        [
            # Create a product price
            price_event_factory(
                action=PriceEventAction.UPSERT,
                product_id=custom_uuid(1),
                price_type=ProductPriceType.ALL_OFFERS,
                price=1,
                old_price=None,
            ),
            # Don't change product price, because there is no price for product 2
            price_event_factory(
                action=PriceEventAction.DELETE,
                product_id=custom_uuid(2),
                price_type=ProductPriceType.ALL_OFFERS,
                price=2,
                old_price=None,
            ),
            # Create a new product price, different price type same id as previous
            price_event_factory(
                action=PriceEventAction.UPSERT,
                product_id=custom_uuid(1),
                price_type=ProductPriceType.MARKETPLACE,
                price=4,
                old_price=None,
            ),
            # Create a new product price
            price_event_factory(
                action=PriceEventAction.UPSERT,
                product_id=custom_uuid(3),
                price_type=ProductPriceType.IN_STOCK_CERTIFIED,
                price=2,
                old_price=None,
            ),
        ],
    )

    product_prices = await crud.product_price.get_many(db_conn)
    assert len(product_prices) == 3

    assert {
        (pp.product_id, pp.price_type, pp.max_price, pp.min_price)
        for pp in product_prices
    } == {
        (custom_uuid(1), ProductPriceType.ALL_OFFERS, 1.0, 1.0),
        (custom_uuid(1), ProductPriceType.MARKETPLACE, 4.0, 4.0),
        (custom_uuid(3), ProductPriceType.IN_STOCK_CERTIFIED, 2.0, 2.0),
    }

    assert await redis.scard(PUBLISHER_REDIS_QUEUE_NAME) == 2
    assert await redis.spop(PUBLISHER_REDIS_QUEUE_NAME, 100) == [
        custom_uuid(1).bytes,
        custom_uuid(3).bytes,
    ]

    await push_to_redis_queue(
        entity_population_job,
        [
            # Create a change with new max price
            price_event_factory(
                action=PriceEventAction.UPSERT,
                product_id=custom_uuid(1),
                price_type=ProductPriceType.ALL_OFFERS,
                old_price=None,
                price=2,
            ),
            # Create a change (deletion) with old max price, delete price
            # even when offer with id 1 exists, but it's not buyable
            price_event_factory(
                action=PriceEventAction.DELETE,
                product_id=custom_uuid(1),
                price_type=ProductPriceType.MARKETPLACE,
                price=None,
                old_price=4,
            ),
            # Do nothing
            price_event_factory(
                action=PriceEventAction.DELETE,
                product_id=custom_uuid(3),
                price_type=ProductPriceType.IN_STOCK_CERTIFIED,
                price=None,
                old_price=1.2,
            ),
        ],
    )

    product_prices = await crud.product_price.get_many(db_conn)
    assert len(product_prices) == 2
    assert {
        (pp.product_id, pp.price_type, pp.max_price, pp.min_price)
        for pp in product_prices
    } == {
        (custom_uuid(1), ProductPriceType.ALL_OFFERS, 2.0, 1.0),
        (custom_uuid(3), ProductPriceType.IN_STOCK_CERTIFIED, 2.0, 2.0),
    }
    assert await redis.scard(PUBLISHER_REDIS_QUEUE_NAME) == 1
    assert await redis.spop(PUBLISHER_REDIS_QUEUE_NAME, 100) == [custom_uuid(1).bytes]

    await push_to_redis_queue(
        entity_population_job,
        [
            # Create a change with new max price and new min price
            price_event_factory(
                action=PriceEventAction.UPSERT,
                product_id=custom_uuid(1),
                price_type=ProductPriceType.ALL_OFFERS,
                old_price=2.0,
                price=0.5,
            ),
        ],
    )

    product_prices = await crud.product_price.get_many(db_conn)
    assert len(product_prices) == 2
    assert {
        (pp.product_id, pp.price_type, pp.max_price, pp.min_price)
        for pp in product_prices
    } == {
        (custom_uuid(1), ProductPriceType.ALL_OFFERS, 10.0, 0.5),
        (custom_uuid(3), ProductPriceType.IN_STOCK_CERTIFIED, 2.0, 2.0),
    }
    assert await redis.scard(PUBLISHER_REDIS_QUEUE_NAME) == 1
    assert await redis.spop(PUBLISHER_REDIS_QUEUE_NAME, 100) == [custom_uuid(1).bytes]

    assert caplog.messages[-12] == "Processing 4 objects"
    assert caplog.messages[-11] == "Upsert 3 product prices"
    assert caplog.messages[-10] == "Delete 0 product prices"
    assert caplog.messages[-9] == "Push 2 product ids to the publisher queue"
    assert caplog.messages[-8] == "Processing 3 objects"
    assert caplog.messages[-7] == "Upsert 1 product prices"
    assert caplog.messages[-6] == "Delete 1 product prices"
    assert caplog.messages[-5] == "Push 1 product ids to the publisher queue"
    assert caplog.messages[-4] == "Processing 1 objects"
    assert caplog.messages[-3] == "Upsert 1 product prices"
    assert caplog.messages[-2] == "Delete 0 product prices"
    assert caplog.messages[-1] == "Push 1 product ids to the publisher queue"