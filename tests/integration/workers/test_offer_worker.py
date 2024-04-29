import orjson
import pytest

from app import crud
from app.constants import PRICE_EVENT_QUEUE, Action, CountryCode, CurrencyCode, Entity
from tests.factories import offer_factory, shop_factory
from tests.integration.consumer.test_consumer import wait_for_redis
from tests.msg_templator.base import entity_msg
from tests.utils import (
    custom_uuid,
    push_messages_and_process_them_by_worker,
    random_one_id,
)


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


@pytest.mark.anyio
async def test_update_price_events(db_conn, worker_redis, offer_worker, caplog):
    shop = await shop_factory(db_conn, certified=True)
    offer = await offer_factory(
        db_conn, shop_id=shop.id, in_stock=True, price=1, version=1
    )
    offer_msgs = [
        # New offer, should generate ALL_OFFERS event
        entity_msg(
            Entity.OFFER,
            Action.CREATE,
            {"id": str(random_one_id()), "productId": str(custom_uuid(1))},
        ),
        # Update offer in stock from certified shop,
        # should generate ALL_OFFERS, IN_STOCK and IN_STOCK_CERTIFIED events
        entity_msg(
            Entity.OFFER,
            Action.UPDATE,
            {"id": str(offer.id), "productId": str(offer.product_id), "version": 2},
        ),
    ]

    await push_messages_and_process_them_by_worker(
        worker_redis, offer_worker, *offer_msgs
    )
    assert "Successfully upserted 2 offers." in caplog.messages
    assert "4 price events sent" in caplog.messages

    await wait_for_redis(worker_redis, 1)
    assert await worker_redis.llen(PRICE_EVENT_QUEUE) == 4
    events = [
        orjson.loads(event) for event in await worker_redis.rpop(PRICE_EVENT_QUEUE, 4)
    ]

    assert events[0]["product_id"] == str(custom_uuid(1))
    assert events[0]["action"] == "upsert"
    assert events[0]["type"] == "ALL_OFFERS"
    assert events[0]["price"] == 13237.0
    assert events[0]["country_code"] == "CZ"
    assert events[0]["currency_code"] == "CZK"

    assert events[1]["product_id"] == str(offer.product_id)
    assert events[1]["action"] == "upsert"
    assert events[1]["type"] == "ALL_OFFERS"
    assert events[1]["price"] == 13237.0
    assert events[1]["country_code"] == "CZ"
    assert events[1]["currency_code"] == "CZK"

    assert events[2]["product_id"] == str(offer.product_id)
    assert events[2]["action"] == "upsert"
    assert events[2]["type"] == "IN_STOCK"
    assert events[2]["price"] == 13237.0
    assert events[2]["country_code"] == "CZ"
    assert events[2]["currency_code"] == "CZK"

    assert events[3]["product_id"] == str(offer.product_id)
    assert events[3]["action"] == "upsert"
    assert events[3]["type"] == "IN_STOCK_CERTIFIED"
    assert events[3]["price"] == 13237.0
    assert events[3]["country_code"] == "CZ"
    assert events[3]["currency_code"] == "CZK"


@pytest.mark.anyio
async def test_delete_price_events(db_conn, worker_redis, offer_worker, caplog):
    offer = await offer_factory(
        db_conn,
        buyable=True,
        price=42,
        country_code=CountryCode.CZ,
        currency_code=CurrencyCode.CZK,
        version=1,
    )
    offer_msgs = [
        # Attempt to delete nonexistent offer, do not generate anything
        entity_msg(Entity.OFFER, Action.DELETE, {"id": str(random_one_id())}),
        # Delete buyable offer, should generate ALL_OFFERS and MARKETPLACE events
        entity_msg(Entity.OFFER, Action.DELETE, {"id": str(offer.id), "version": 2}),
    ]

    await push_messages_and_process_them_by_worker(
        worker_redis, offer_worker, *offer_msgs
    )
    assert "Successfully delete 1 offers." in caplog.messages
    assert "2 price events sent" in caplog.messages

    await wait_for_redis(worker_redis, 1)
    assert await worker_redis.llen(PRICE_EVENT_QUEUE) == 2
    events = [
        orjson.loads(event) for event in await worker_redis.rpop(PRICE_EVENT_QUEUE, 2)
    ]

    assert events[0]["product_id"] == str(offer.product_id)
    assert events[0]["action"] == "delete"
    assert events[0]["type"] == "ALL_OFFERS"
    assert events[0]["price"] == 42.0
    assert events[0]["country_code"] == "CZ"
    assert events[0]["currency_code"] == "CZK"

    assert events[1]["product_id"] == str(offer.product_id)
    assert events[1]["action"] == "delete"
    assert events[1]["type"] == "MARKETPLACE"
    assert events[1]["price"] == 42.0
    assert events[1]["country_code"] == "CZ"
    assert events[1]["currency_code"] == "CZK"
