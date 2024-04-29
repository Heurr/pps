import pytest

from app import crud
from app.constants import Action, Entity
from tests.factories import offer_factory
from tests.msg_templator.base import entity_msg
from tests.utils import push_messages_and_process_them_by_worker


@pytest.mark.skip(
    reason="This will be fixed in next MR "
    "We need to update application code to use composite PK."
)
@pytest.mark.anyio
async def test_process_many_offer_create_update_messages(
    db_conn, worker_redis, offer_worker, caplog
):
    offer_1 = await offer_factory(db_conn, version=2)
    offer_2 = await offer_factory(db_conn, version=2)

    offer_msgs = [
        entity_msg(
            Entity.OFFER,
            Action.CREATE,
            {
                "id": str(offer_1.id),
                "version": 3,
            },
        ),
        entity_msg(
            Entity.OFFER,
            Action.UPDATE,
            {
                "id": str(offer_2.id),
                "version": 1,
            },
        ),
    ]

    await push_messages_and_process_them_by_worker(
        worker_redis, offer_worker, *offer_msgs
    )
    assert "Successfully upserted 1 offers." in caplog.messages[-2]
    offers = await crud.offer.get_many(db_conn)
    assert len(offers) == 2
    offers_by_id = {b.id: b for b in offers}
    assert offers_by_id[offer_1.id].version == 3
    assert offers_by_id[offer_2.id].version == 2


@pytest.mark.anyio
async def test_process_many_offer_create_update_messages_missing_product(
    db_conn, worker_redis, offer_worker, caplog
):
    offer_1 = await offer_factory(db_conn, version=2)

    offer_msgs = [
        entity_msg(
            Entity.OFFER,
            Action.CREATE,
            {
                "id": str(offer_1.id),
                "productId": "",
                "version": 3,
            },
        ),
    ]

    await push_messages_and_process_them_by_worker(
        worker_redis, offer_worker, *offer_msgs
    )
    assert "Successfully upserted 0 offers." in caplog.messages[-2]
    assert "Filtered out 1 messages" in caplog.messages[-3]
    offers = await crud.offer.get_many(db_conn)
    assert len(offers) == 1
    db_offer = offers[0]
    assert db_offer.version == 2


@pytest.mark.anyio
async def test_process_many_offer_delete_messages(
    db_conn, worker_redis, offer_worker, caplog
):
    offer_1 = await offer_factory(db_conn, version=2)
    offer_2 = await offer_factory(db_conn, version=2)

    offer_msgs = [
        entity_msg(
            Entity.OFFER,
            Action.DELETE,
            {
                "id": str(offer_1.id),
                "version": 3,
            },
        ),
        entity_msg(
            Entity.OFFER,
            Action.DELETE,
            {
                "id": str(offer_2.id),
                "version": 1,
            },
        ),
    ]

    await push_messages_and_process_them_by_worker(
        worker_redis, offer_worker, *offer_msgs
    )
    assert "Successfully delete 1 offers." in caplog.messages[-2]
    offers = await crud.offer.get_many(db_conn)
    assert len(offers) == 1
    offers_by_id = {b.id: b for b in offers}
    assert offers_by_id[offer_2.id].version == 2
