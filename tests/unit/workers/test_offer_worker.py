import pytest
from _pytest.mark import param

from app.constants import Action, CountryCode, CurrencyCode, PriceType
from app.schemas.offer import (
    OfferCreateSchema,
    OfferLegacy,
    OfferMessageSchema,
    OfferPrice,
)
from app.workers import OfferMessageWorker
from tests.utils import custom_uuid


@pytest.mark.parametrize(
    "message,create_obj",
    [
        param(
            OfferMessageSchema(
                id=custom_uuid(1),
                product_id=custom_uuid(2),
                shop_id=custom_uuid(3),
                legacy=OfferLegacy(country_code=CountryCode.SK),
                prices=[
                    OfferPrice(
                        type=PriceType.REGULAR,
                        amount=31.4,
                        currency_code=CurrencyCode.EUR,
                    ),
                    OfferPrice(
                        type=PriceType.DISCOUNT,
                        amount=31.5,
                        currency_code=CurrencyCode.EUR,
                    ),
                ],
                action=Action.CREATE,
                version=1,
            ),
            OfferCreateSchema(
                id=custom_uuid(1),
                country_code=CountryCode.SK,
                version=1,
                product_id=custom_uuid(2),
                shop_id=custom_uuid(3),
                price=31.4,
                currency_code=CurrencyCode.EUR,
            ),
            id="multiple_prices",
        ),
    ],
)
def test_parse_offer_message(
    offer_worker: OfferMessageWorker,
    message: OfferMessageSchema,
    create_obj: OfferCreateSchema,
):
    assert offer_worker.to_create_schema(message) == create_obj
