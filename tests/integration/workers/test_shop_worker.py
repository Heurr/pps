import pytest

from app import crud
from app.constants import Action, Entity
from tests.factories import shop_factory
from tests.msg_templator.base import entity_msg
from tests.utils import push_messages_and_process_them_by_worker


@pytest.mark.anyio
async def test_process_many_shop_create_update_messages(
    db_conn, worker_redis, shop_worker, caplog
):
    shop_1 = await shop_factory(db_conn, version=2)
    shop_2 = await shop_factory(db_conn, version=2)

    shop_msgs = [
        entity_msg(
            Entity.SHOP, Action.CREATE, {"version": 3, "shop": {"id": str(shop_1.id)}}
        ),
        entity_msg(
            Entity.SHOP, Action.CREATE, {"version": 1, "shop": {"id": str(shop_2.id)}}
        ),
    ]

    await push_messages_and_process_them_by_worker(worker_redis, shop_worker, *shop_msgs)
    assert "Successfully upserted 1 shops." in caplog.messages[-2]
    shops = await crud.shop.get_many(db_conn)
    assert len(shops) == 2
    shops_by_id = {b.id: b for b in shops}
    assert shops_by_id[shop_1.id].version == 3
    assert shops_by_id[shop_2.id].version == 2


@pytest.mark.anyio
async def test_process_many_shop_create_update_messages_no_true_flags(
    db_conn, worker_redis, shop_worker, caplog
):
    shop_1 = await shop_factory(db_conn, version=2)

    shop_msgs = [
        entity_msg(
            Entity.SHOP,
            Action.CREATE,
            {
                "shop": {
                    "id": str(shop_1.id),
                    "state": {"verified": False, "paying": False, "enabled": False},
                    "certificate": {"enabled": False},
                }
            },
        ),
    ]

    await push_messages_and_process_them_by_worker(worker_redis, shop_worker, *shop_msgs)
    assert "Successfully upserted 0 shops." in caplog.messages[-2]
    assert "Filtered out 1 messages" in caplog.messages[-3]
    shops = await crud.shop.get_many(db_conn)
    assert len(shops) == 1
    db_shop = shops[0]
    assert db_shop.version == 2


@pytest.mark.anyio
async def test_process_many_shop_delete_messages(
    db_conn, worker_redis, shop_worker, caplog
):
    shop_1 = await shop_factory(db_conn, version=2)
    shop_2 = await shop_factory(db_conn, version=2)

    shop_msgs = [
        entity_msg(
            Entity.SHOP, Action.DELETE, {"version": 3, "shop": {"id": str(shop_1.id)}}
        ),
        entity_msg(
            Entity.SHOP, Action.DELETE, {"version": 1, "shop": {"id": str(shop_2.id)}}
        ),
    ]

    await push_messages_and_process_them_by_worker(worker_redis, shop_worker, *shop_msgs)
    assert "Successfully delete 1 shops." in caplog.messages[-2]
    shops = await crud.shop.get_many(db_conn)
    assert len(shops) == 1
    shops_by_id = {b.id: b for b in shops}
    assert shops_by_id[shop_2.id].version == 2
