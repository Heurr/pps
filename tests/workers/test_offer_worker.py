from uuid import UUID

import pytest

from app.constants import CountryCode
from app.schemas.offer import OfferCreateSchema, OfferMessageSchema
from app.utils import dump_to_json
from tests.factories import shop_factory
from tests.utils import push_messages_and_process_them_by_worker

OFFER_ONE_ID = UUID("415ac1f8-f33b-1f5d-9e00-a4c707cea1ec")
LOCAL_PRODUCT_ID = "1636"
PRODUCT_ID = UUID("21e13089-0e54-5648-88d6-da63340935af")
LOCAL_SHOP_ID = "92670"
SHOP_ID = UUID("fc085ece-edff-589d-b546-0b0e6ed09136")
COUNTRY_CODE = CountryCode.SI


@pytest.fixture
def offer_insert_msg_body() -> dict:
    return {
        "version": 100,
        "action": "create",
        "id": str(OFFER_ONE_ID),
        "legacy": {
            "platformId": "cen",
            "countryCode": COUNTRY_CODE.value,
            "platformSellerId": LOCAL_SHOP_ID,
            "platformOfferId": "483_8659",
            "platformProductId": LOCAL_PRODUCT_ID,
            "parameters": [{"name": "Farba", "value": "čierna", "unit": ""}],
        },
        "shopId": SHOP_ID,
        "productId": PRODUCT_ID,
        "sellerOfferId": "8659",
        "groupId": "1636",
        "name": "SONY HVL-F1000 ",
        "description": "\u003cdiv\u003eTehnične lastnosti: ",
        "url": "http://www.odaz.si/si/page/detail/gitm/8659/?wsref=ceneje-si",
        "medias": [
            {
                "type": "image",
                "url": "http://www.odaz.si/inc/image/type;item;size;large;name;$$A_1FAF2CAF_wshimppictf2390406.jpg",
                "isMain": True,
            }
        ],
        "prices": [
            {"type": "regular", "amount": "161.22", "currencyCode": "EUR", "vat": "0"}
        ],
        "tags": None,
        "attributes": [
            {"name": "Velikost", "value": "2.5", "unit": "l"},
            {"name": "Barva", "value": "rdeča"},
        ],
        "categoryText": "",
        "manufacturer": "",
        "brand": "SONY",
        "productNumber": "",
        "ean": "",
        "isbn": "",
        "maxClickPrice": None,
        "deliveries": None,
        "accessories": None,
        "extraFee": None,
        "gifts": None,
        "coupons": None,
        "pickupPoints": None,
        "deliveryTimeMin": 0,
        "deliveryTimeMax": 0,
    }


@pytest.mark.anyio
async def test_parse_message_body_offer(offer_insert_msg_body, offer_worker):
    msg = offer_worker.parse_redis_message(dump_to_json(offer_insert_msg_body))
    offer_in: OfferCreateSchema = offer_worker.to_message_schema(msg)

    assert offer_in.id == OFFER_ONE_ID
    assert offer_in.product_id == PRODUCT_ID


@pytest.mark.anyio
async def test_parse_message_body_offer_empty_product_id(
    offer_insert_msg_body, offer_worker
):
    offer_insert_msg_body["productId"] = ""
    msg = offer_worker.parse_redis_message(dump_to_json(offer_insert_msg_body))
    offer_in: OfferMessageSchema = offer_worker.to_message_schema(msg)

    assert offer_in.id == OFFER_ONE_ID
    assert not offer_in.product_id


@pytest.mark.anyio
async def test_consume_offer_create_message_empty_product(
    db_conn, worker_redis, offer_service, offer_worker, offer_insert_msg_body, caplog
):
    shop = await shop_factory(db_conn, shop_id=SHOP_ID)

    offer_insert_msg_body["legacy"]["platformProductId"] = ""
    offer_insert_msg_body["productId"] = ""
    await push_messages_and_process_them_by_worker(
        worker_redis, offer_worker, offer_insert_msg_body
    )

    assert "Successfully upserted 0 offers." in caplog.messages[-2]
    assert "Filtered out 1 messages" in caplog.messages[-3]

    offer = await offer_service.get_many_by_ids(db_conn, [OFFER_ONE_ID])
    assert not offer


@pytest.mark.anyio
async def test_consume_offer_create_message_product(
    db_conn, worker_redis, offer_service, offer_worker, offer_insert_msg_body, caplog
):
    shop = await shop_factory(db_conn, shop_id=SHOP_ID)

    offer_insert_msg_body["legacy"]["platformProductId"] = ""
    await push_messages_and_process_them_by_worker(
        worker_redis, offer_worker, offer_insert_msg_body
    )

    assert "Successfully upserted 1 offers." in caplog.messages[-2]
    offer = await offer_service.get_many_by_ids(db_conn, [OFFER_ONE_ID])
    assert offer[0].product_id == PRODUCT_ID
    assert offer[0].id == OFFER_ONE_ID
