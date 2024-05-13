import pytest

from app.services import AvailabilityService, BuyableService, OfferService, ShopService
from tests.factories import (
    availability_factory,
    buyable_factory,
    offer_factory,
    shop_factory,
)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "service, factory, expected_result",
    [
        (OfferService(), offer_factory, True),
        (ShopService(), shop_factory, True),
        (AvailabilityService(), availability_factory, False),
        (BuyableService(), buyable_factory, False),
    ],
)
async def test_should_be_updated_if_obj_in_is_none(service, factory, expected_result):
    assert service.should_be_updated(None, await factory()) is expected_result


@pytest.mark.anyio
@pytest.mark.parametrize(
    "entity, service, factory, obj_in_version, msg_in_version, expected",
    [
        ("offer", OfferService(), offer_factory, 10, 10, True),
        ("offer", OfferService(), offer_factory, 10, 9, False),
        ("shop", ShopService(), shop_factory, 10, 10, True),
        ("shop", ShopService(), shop_factory, 10, 9, False),
    ],
)
async def test_should_be_updated_with_forced_update(
    entity, service, factory, obj_in_version, msg_in_version, expected, mocker
):
    service.force_entity_update = True
    obj_in = await factory(db_schema=True, version=obj_in_version)
    msg_in = await factory(version=msg_in_version)
    metrics = mocker.patch("app.services.base.UPDATE_METRICS.labels")
    assert service.should_be_updated(obj_in, msg_in) is expected
    if expected:
        metrics.assert_called_once_with(update_type="forced", entity=entity)
    else:
        metrics.assert_not_called()
