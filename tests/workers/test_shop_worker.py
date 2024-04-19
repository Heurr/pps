from uuid import UUID

import pytest

from app.utils import dump_to_json

SHOP_ONE_ID = UUID("3e3eb8b1-b88f-4c5e-80b1-e11809f6c612")
LOCAL_SHOP_ID = 40


@pytest.fixture
def shop_insert_msg_body() -> dict:
    return {
        "version": 12345,
        "action": "create",
        "shop": {
            "id": str(SHOP_ONE_ID),
            "legacy": {
                "platformShopId": LOCAL_SHOP_ID,
                "platformId": "CEN",
                "countryCode": "SI",
            },
            "name": "Rolan's",
            "longName": "",
            "ownerId": 1,
            "email": "enakup@rolan.si",
            "phone": "080 18 20",
            "homepage": "www.rolan.si",
            "facebook": "",
            "registeredAt": "2005-01-11T00:00:00+00:00",
            "termsAcceptedVersion": 0,
            "imageIds": [],
            "imageUrls": [],
            "description": "",
            "promo": "",
            "vip": False,
            "flags": [],
            "balanceAmount": "250.00",
            "hasCredit": True,
            "state": {
                "verified": None,
                "paying": True,
                "enabled": True,
                "deleted": None,
            },
            "certificate": {"enabled": False, "value": None},
            "keys": {"export": "", "api": ""},
            "branches": [],
        },
    }


@pytest.mark.anyio
async def test_parse_message_body_shop(shop_insert_msg_body, shop_worker):
    msg = shop_worker.parse_redis_message(dump_to_json(shop_insert_msg_body))
    shop_in = shop_worker.to_message_schema(msg)

    assert shop_in.shop.id == SHOP_ONE_ID
