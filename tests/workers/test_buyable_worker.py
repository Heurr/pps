from uuid import UUID

import pytest

from tests.factories import buyable_factory
from tests.utils import push_messages_and_process_them_by_worker


@pytest.fixture
def buyable_upsert_msg() -> str:
    return """{
        "id": "00fef34a-3f70-5828-85f6-e79ebd963db3",
        "offerId": "637a3a78-7878-7878-7878-783531353630",
        "productId": "637a3a78-7878-7878-7878-783531353631",
        "categoryId": "637a3a78-7878-7878-7878-783531353632",
        "sellerId": "637a3a78-7878-7878-7878-783531353633",
        "buyable": true,
        "action": "create",
        "version": 123,
        "legacy": {
            "countryCode": "HU",
            "platformOfferId": "546974",
            "platformProductId": "m123456",
            "platformCategoryId": "3277",
            "platformShopId": "K417655"
        }
    }"""


@pytest.fixture
def buyable_delete_msg() -> str:
    return """{
        "action": "delete",
        "id":  "00fef34a-3f70-5828-85f6-e79ebd963db3",
        "offerId": "637a3a78-7878-7878-7878-783531353630",
        "version": 1234,
        "buyable": false,
        "legacy": {"countryCode": "HU"}
    }"""


@pytest.mark.anyio
async def test_parse_create_msg(buyable_worker, buyable_upsert_msg):
    msg = buyable_worker.parse_redis_message(buyable_upsert_msg)
    buyable = buyable_worker.to_message_schema(msg)
    assert buyable.id == UUID("637a3a78-7878-7878-7878-783531353630")
    assert buyable.buyable is True
    assert buyable.version == 123


@pytest.mark.anyio
async def test_process_many_create_update_messages(
    db_conn, worker_redis, buyable_worker, caplog
):
    buyable_1 = await buyable_factory(db_conn, version=2)
    buyable_2 = await buyable_factory(db_conn, version=2)

    buyable_msgs = [
        {
            "offerId": str(buyable_1.id),
            "buyable": True,
            "version": 3,
            "action": "create",
            "legacy": {"countryCode": "CZ"},
        },
        {
            "offerId": str(buyable_2.id),
            "countryCode": "CZ",
            "buyable": True,
            "version": 1,
            "action": "create",
            "legacy": {"countryCode": "CZ"},
        },
    ]

    await push_messages_and_process_them_by_worker(
        worker_redis, buyable_worker, *buyable_msgs
    )
    assert "Successfully upserted 1 buyables." in caplog.messages[-2]
