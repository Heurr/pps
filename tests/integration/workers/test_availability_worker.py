import pytest

from app import crud
from app.constants import Action, Entity
from tests.factories import offer_factory
from tests.msg_templator.base import entity_msg
from tests.utils import push_messages_and_process_them_by_worker


@pytest.mark.anyio
async def test_process_many_availability_create_update_messages(
    db_conn, worker_redis, availability_worker, caplog
):
    availability_1 = await offer_factory(db_conn, availability_version=2)
    availability_2 = await offer_factory(db_conn, availability_version=2)

    availability_msgs = [
        entity_msg(
            Entity.AVAILABILITY,
            Action.CREATE,
            {
                "offerId": str(availability_1.id),
                "version": 3,
            },
        ),
        entity_msg(
            Entity.AVAILABILITY,
            Action.UPDATE,
            {
                "offerId": str(availability_2.id),
                "version": 1,
            },
        ),
    ]

    await push_messages_and_process_them_by_worker(
        worker_redis, availability_worker, *availability_msgs
    )
    assert "Successfully upserted 1 availabilitys." in caplog.messages[-2]
    availabilities = await crud.availability.get_many(db_conn)
    assert len(availabilities) == 2
    availabilities_by_id = {b.id: b for b in availabilities}
    assert availabilities_by_id[availability_1.id].availability_version == 3
    assert availabilities_by_id[availability_2.id].availability_version == 2


@pytest.mark.anyio
async def test_process_many_availability_delete_messages(
    db_conn, worker_redis, availability_worker, caplog
):
    availability_1 = await offer_factory(db_conn, availability_version=2)
    availability_2 = await offer_factory(db_conn, availability_version=2)

    availability_msgs = [
        entity_msg(
            Entity.AVAILABILITY,
            Action.DELETE,
            {
                "offerId": str(availability_1.id),
                "version": 3,
            },
        ),
        entity_msg(
            Entity.AVAILABILITY,
            Action.DELETE,
            {
                "offerId": str(availability_2.id),
                "version": 1,
            },
        ),
    ]

    await push_messages_and_process_them_by_worker(
        worker_redis, availability_worker, *availability_msgs
    )
    assert "Successfully delete 1 availabilitys." in caplog.messages[-2]
    availabilities = await crud.availability.get_many(db_conn)
    assert len(availabilities) == 2
    availabilities_by_id = {b.id: b for b in availabilities}
    assert availabilities_by_id[availability_2.id].availability_version == 2
