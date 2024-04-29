import pytest
from _pytest.mark import param

from app.constants import Action, CountryCode
from app.schemas.buyable import BuyableCreateSchema, BuyableLegacy, BuyableMessageSchema
from app.workers import BuyableMessageWorker
from tests.utils import custom_uuid


@pytest.mark.parametrize(
    "message,create_obj",
    [
        param(
            BuyableMessageSchema(
                id=custom_uuid(1),
                buyable=True,
                legacy=BuyableLegacy(country_code=CountryCode.SK),
                version=1,
                action=Action.CREATE,
            ),
            BuyableCreateSchema(
                id=custom_uuid(1),
                country_code=CountryCode.SK,
                version=1,
                buyable=True,
            ),
            id="buyable_true",
        ),
        param(
            BuyableMessageSchema(
                id=custom_uuid(1),
                buyable=False,
                legacy=BuyableLegacy(country_code=CountryCode.SK),
                version=1,
                action=Action.CREATE,
            ),
            BuyableCreateSchema(
                id=custom_uuid(1),
                country_code=CountryCode.SK,
                version=1,
                buyable=False,
            ),
            id="buyable_false",
        ),
    ],
)
def test_parse_buyable_message(
    buyable_worker: BuyableMessageWorker,
    message: BuyableMessageSchema,
    create_obj: BuyableCreateSchema,
):
    assert buyable_worker.to_create_schema(message) == create_obj
