import pytest
from _pytest.mark import param

from app.constants import Action, CountryCode, StockInfo
from app.schemas.availability import (
    Availability,
    AvailabilityCreateSchema,
    AvailabilityLegacy,
    AvailabilityMessageSchema,
)
from app.workers import AvailabilityMessageWorker
from tests.utils import custom_uuid


@pytest.mark.parametrize(
    "message,create_obj",
    [
        param(
            AvailabilityMessageSchema(
                id=custom_uuid(1),
                availability=Availability(
                    stock_info=StockInfo.IN_STOCK,
                    legacy=AvailabilityLegacy(country_code=CountryCode.SK),
                ),
                action=Action.CREATE,
                version=1,
            ),
            AvailabilityCreateSchema(
                id=custom_uuid(1), country_code=CountryCode.SK, version=1, in_stock=True
            ),
            id="in_stock",
        ),
        param(
            AvailabilityMessageSchema(
                id=custom_uuid(1),
                availability=Availability(
                    stock_info=StockInfo.PREORDER,
                    legacy=AvailabilityLegacy(country_code=CountryCode.SK),
                ),
                action=Action.CREATE,
                version=1,
            ),
            AvailabilityCreateSchema(
                id=custom_uuid(1), country_code=CountryCode.SK, version=1, in_stock=False
            ),
            id="pre_order",
        ),
        param(
            AvailabilityMessageSchema(
                id=custom_uuid(1),
                availability=Availability(
                    stock_info=StockInfo.OUT_OF_STOCK,
                    legacy=AvailabilityLegacy(country_code=CountryCode.SK),
                ),
                action=Action.CREATE,
                version=1,
            ),
            AvailabilityCreateSchema(
                id=custom_uuid(1), country_code=CountryCode.SK, version=1, in_stock=False
            ),
            id="out_of_stock",
        ),
    ],
)
def test_parse_availability_message(
    availability_worker: AvailabilityMessageWorker,
    message: AvailabilityMessageSchema,
    create_obj: AvailabilityCreateSchema,
):
    assert availability_worker.to_create_schema(message) == create_obj
