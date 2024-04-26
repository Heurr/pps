import pytest

from app import crud
from app.constants import Action, Entity
from tests.factories import offer_factory
from tests.msg_templator.base import entity_msg
from tests.utils import push_messages_and_process_them_by_worker


@pytest.mark.anyio
async def test_process_many_buyable_create_update_messages(
    db_conn, worker_redis, buyable_worker, caplog
):
    buyable_1 = await offer_factory(db_conn, buyable_version=2)
    buyable_2 = await offer_factory(db_conn, buyable_version=2)

    buyable_msgs = [
        entity_msg(
            Entity.BUYABLE,
            Action.CREATE,
            {
                "offerId": str(buyable_1.id),
                "version": 3,
            },
        ),
        entity_msg(
            Entity.BUYABLE,
            Action.UPDATE,
            {
                "offerId": str(buyable_2.id),
                "version": 1,
            },
        ),
    ]

    await push_messages_and_process_them_by_worker(
        worker_redis, buyable_worker, *buyable_msgs
    )
    assert "Successfully upserted 1 buyables." in caplog.messages[-2]
    buyables = await crud.buyable.get_many(db_conn)
    assert len(buyables) == 2
    buyables_by_id = {b.id: b for b in buyables}
    assert buyables_by_id[buyable_1.id].buyable_version == 3
    assert buyables_by_id[buyable_2.id].buyable_version == 2


@pytest.mark.anyio
async def test_process_many_buyable_delete_messages(
    db_conn, worker_redis, buyable_worker, caplog
):
    buyable_1 = await offer_factory(db_conn, buyable_version=2)
    buyable_2 = await offer_factory(db_conn, buyable_version=2)

    buyable_msgs = [
        entity_msg(
            Entity.BUYABLE,
            Action.DELETE,
            {
                "offerId": str(buyable_1.id),
                "version": 3,
            },
        ),
        entity_msg(
            Entity.BUYABLE,
            Action.DELETE,
            {
                "offerId": str(buyable_2.id),
                "version": 1,
            },
        ),
    ]

    await push_messages_and_process_them_by_worker(
        worker_redis, buyable_worker, *buyable_msgs
    )
    assert "Successfully delete 1 buyables." in caplog.messages[-2]
    buyables = await crud.buyable.get_many(db_conn)
    assert len(buyables) == 2
    buyables_by_id = {b.id: b for b in buyables}
    assert buyables_by_id[buyable_2.id].buyable_version == 2
