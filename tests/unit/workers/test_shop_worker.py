import pytest
from _pytest.mark import param

from app.constants import Action, CountryCode
from app.schemas.shop import (
    Shop,
    ShopCertificate,
    ShopCreateSchema,
    ShopLegacy,
    ShopMessageSchema,
    ShopState,
)
from app.workers import ShopMessageWorker
from tests.utils import custom_uuid


@pytest.mark.parametrize(
    "message,create_obj",
    [
        param(
            ShopMessageSchema(
                shop=Shop(
                    id=custom_uuid(1),
                    legacy=ShopLegacy(country_code=CountryCode.SK),
                    state=ShopState(verified=True, paying=True, enabled=False),
                    certificate=ShopCertificate(enabled=False),
                ),
                action=Action.CREATE,
                version=1,
            ),
            ShopCreateSchema(
                id=custom_uuid(1),
                country_code=CountryCode.SK,
                version=1,
                certified=False,
                enabled=False,
                verified=True,
                paying=True,
            ),
            id="verified_paying",
        ),
    ],
)
def test_parse_shop_message(
    shop_worker: ShopMessageWorker,
    message: ShopMessageSchema,
    create_obj: ShopCreateSchema,
):
    assert shop_worker.to_create_schema(message) == create_obj
