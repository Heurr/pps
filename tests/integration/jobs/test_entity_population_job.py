import json
from contextlib import asynccontextmanager
from datetime import timedelta

import freezegun
import pytest
from aio_pika.abc import AbstractIncomingMessage, AbstractQueue
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app import crud
from app.config.settings import EntityPopulationJobSettings, RepublishSettings
from app.constants import Entity
from app.jobs.entity_population import EntityPopulationJob
from app.utils import utc_now
from tests.factories import offer_factory
from tests.utils import custom_uuid, override_obj_get_db_conn


@pytest.fixture
async def entity_population_job(
    db_engine: AsyncEngine,
    db_conn: AsyncConnection,
    missing_job_settings: EntityPopulationJobSettings,
    republish_settings: RepublishSettings,
):
    job = EntityPopulationJob(
        db_engine,
        [Entity.BUYABLE, Entity.AVAILABILITY],
        missing_job_settings,
        republish_settings,
    )
    override_obj_get_db_conn(db_conn, job)

    @asynccontextmanager
    async def get_db_conn():
        yield db_conn

    job.get_db_conn_auto_commit = get_db_conn
    return job


@pytest.fixture
async def rmq_queue(rmq_channel, republish_settings: RepublishSettings) -> AbstractQueue:
    queue = await rmq_channel.declare_queue(
        "testing-queue", durable=False, auto_delete=True
    )
    for routing_key in republish_settings.TARGET_ROUTING_KEY_MAP.values():
        await queue.bind("test-ex", routing_key)
    yield queue


@pytest.mark.anyio
async def test_missing_entities_job(
    rmq_exchange,
    rmq_channel,
    rmq_queue,
    entity_population_job: EntityPopulationJob,
    db_conn: AsyncConnection,
    caplog,
):
    """
    Integration test for the EntityPopulationJob class, testing if newly created offers
    which don't have buyable/availability are correctly repushed to the
    correct routing keys
    """
    version = [(-1, -1), (-1, 0), (0, -1), (0, 0)]
    offers = [
        await offer_factory(
            db_conn,
            availability_version=versions[0],
            buyable_version=versions[1],
            offer_id=custom_uuid(i + 1),
        )
        for i, versions in enumerate(version)
    ]

    await entity_population_job.run()
    assert "Pushed 2 ids for republish to availability.v1.republish" in caplog.messages
    assert "Pushed 2 ids for republish to om-buyable.v1.republish" in caplog.messages

    # Read all msgs from queue
    msgs: list[AbstractIncomingMessage] = []
    async with rmq_queue.iterator(timeout=1) as queue_iterator:
        async for msg in queue_iterator:
            msgs.append(msg)
            if len(msgs) == 2:
                break

    msgs_by_routing_key = {msg.routing_key: msg.body for msg in msgs}
    assert str(offers[0].id) in msgs_by_routing_key["om-buyable.v1.republish"].decode(
        "utf-8"
    )
    assert str(offers[2].id) in msgs_by_routing_key["om-buyable.v1.republish"].decode(
        "utf-8"
    )
    assert str(offers[1].id) in msgs_by_routing_key["availability.v1.republish"].decode(
        "utf-8"
    )
    assert str(offers[0].id) in msgs_by_routing_key["availability.v1.republish"].decode(
        "utf-8"
    )


@pytest.mark.anyio
async def test_missing_entities_job_expire_entities(
    rmq_exchange,
    rmq_channel,
    rmq_queue,
    entity_population_job: EntityPopulationJob,
    db_conn: AsyncConnection,
    caplog,
):
    """
    Integration test for the EntityPopulationJob class, testing if newly created offers
    which expire are correctly marked as expired
    """
    version = [(-1, -1), (-1, 1), (1, -1), (1, 2)]
    offers = [
        await offer_factory(
            db_conn,
            availability_version=versions[0],
            buyable_version=versions[1],
            offer_id=custom_uuid(i + 1),
        )
        for i, versions in enumerate(version)
    ]
    entity_population_job.expire_time = 1

    with freezegun.freeze_time(utc_now() + timedelta(seconds=2)):
        await entity_population_job.run()

    assert "Expired 2 buyable entities" in caplog.messages
    assert "Expired 2 availability entities" in caplog.messages
    assert "Pushed 2 ids for republish to om-buyable.v1.republish" in caplog.messages
    assert "Pushed 2 ids for republish to availability.v1.republish" in caplog.messages

    offers_in_db = {o.id: o for o in await crud.offer.get_many(db_conn)}
    assert offers_in_db[offers[0].id].buyable_version == 0
    assert offers_in_db[offers[0].id].availability_version == 0

    assert offers_in_db[offers[1].id].availability_version == 0
    assert offers_in_db[offers[1].id].buyable_version == 1

    assert offers_in_db[offers[2].id].availability_version == 1
    assert offers_in_db[offers[2].id].buyable_version == 0

    assert offers_in_db[offers[3].id].availability_version == 1
    assert offers_in_db[offers[3].id].buyable_version == 2

    # Read all msgs from queue
    msgs: list[AbstractIncomingMessage] = []
    async with rmq_queue.iterator(timeout=1) as queue_iterator:
        async for msg in queue_iterator:
            msgs.append(msg)
            if len(msgs) == 2:
                break

    msgs_by_routing_key = {msg.routing_key: msg.body for msg in msgs}
    buyable_ids = json.loads(
        msgs_by_routing_key["om-buyable.v1.republish"].decode("utf-8")
    )["ids"]
    availability_ids = json.loads(
        msgs_by_routing_key["availability.v1.republish"].decode("utf-8")
    )["ids"]
    assert set(buyable_ids) == {str(offers[0].id), str(offers[2].id)}
    assert set(availability_ids) == {str(offers[1].id), str(offers[0].id)}
