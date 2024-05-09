import pytest
from freezegun import freeze_time

from app import crud
from app.constants import CountryCode, ProductPriceType
from app.schemas.availability import AvailabilityCreateSchema
from app.schemas.offer import OfferDBSchema
from app.schemas.price_event import PriceEventAction
from tests.factories import offer_factory
from tests.utils import custom_uuid


@pytest.fixture
async def offers() -> list[OfferDBSchema]:
    return [
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(1),
            product_id=custom_uuid(1),
            country_code=CountryCode.CZ,
            price=10,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(2),
            product_id=custom_uuid(2),
            country_code=CountryCode.CZ,
            price=20,
            availability_version=2,
            in_stock=False,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(3),
            product_id=custom_uuid(3),
            country_code=CountryCode.CZ,
            price=30,
            availability_version=2,
            in_stock=False,
            certified_shop=True,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(4),
            product_id=custom_uuid(4),
            country_code=CountryCode.CZ,
            price=40,
            availability_version=2,
            in_stock=True,
            certified_shop=True,
        ),
    ]


@pytest.mark.anyio
async def test_upsert_many(availability_service, offers: list[OfferDBSchema], mocker):
    crud_get_in_mock = mocker.patch.object(crud.availability, "get_in")
    crud_get_in_mock.return_value = offers
    crud_upsert_mock = mocker.patch.object(crud.availability, "upsert_many")
    crud_upsert_mock.side_effect = lambda _db_conn, entities: [e.id for e in entities]
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    availabilities = [
        AvailabilityCreateSchema(
            id=custom_uuid(1),
            country_code=CountryCode.CZ,
            in_stock=True,
            version=3,  # offer has no availability set yet - should be updated
        ),
        AvailabilityCreateSchema(
            id=custom_uuid(2),
            country_code=CountryCode.CZ,
            in_stock=True,
            version=3,  # higher version, availability change - should be updated
        ),
        AvailabilityCreateSchema(
            id=custom_uuid(3),
            country_code=CountryCode.CZ,
            in_stock=True,
            version=1,  # lower version - no update
        ),
        AvailabilityCreateSchema(
            id=custom_uuid(4),
            country_code=CountryCode.CZ,
            in_stock=True,
            version=3,  # higher version, no availability change - no update
        ),
        AvailabilityCreateSchema(
            id=custom_uuid(5),
            country_code=CountryCode.CZ,
            in_stock=True,
            version=3,  # nonexistent offer ID - no update
        ),
    ]

    updated_ids = await availability_service.upsert_many(
        db_conn_mock, redis_mock, availabilities
    )
    assert set(updated_ids) == {availabilities[0].id, availabilities[1].id}
    crud_upsert_mock.assert_called_once_with(
        db_conn_mock, [availabilities[0], availabilities[1]]
    )


@pytest.mark.anyio
async def test_remove_many(availability_service, offers: list[OfferDBSchema], mocker):
    crud_get_in_mock = mocker.patch.object(crud.availability, "get_in")
    crud_get_in_mock.return_value = offers
    crud_delete_mock = mocker.patch.object(crud.availability, "remove_many")
    crud_delete_mock.side_effect = lambda _db_conn, ids_versions: [
        idv[0] for idv in ids_versions
    ]
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    to_delete = [
        (custom_uuid(2), 1),  # lower version - no delete
        (custom_uuid(3), 3),  # higher version - should be deleted
        (custom_uuid(5), 3),  # nonexistent ID - ignore
    ]

    deleted_ids = await availability_service.remove_many(
        db_conn_mock, redis_mock, to_delete
    )
    assert deleted_ids == [custom_uuid(3)]
    crud_delete_mock.assert_called_once_with(db_conn_mock, [(custom_uuid(3), 3)])


@pytest.mark.anyio
@freeze_time("2024-04-30")
async def test_upsert_generate_events(
    availability_service, offers: list[OfferDBSchema], mocker
):
    crud_get_in_mock = mocker.patch.object(crud.availability, "get_in")
    crud_get_in_mock.return_value = offers
    mocker.patch.object(crud.availability, "upsert_many")
    send_price_events_mock = mocker.patch.object(
        availability_service, "send_price_events"
    )
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    availabilities = [
        AvailabilityCreateSchema(
            id=custom_uuid(1), country_code=CountryCode.CZ, in_stock=True, version=2
        ),
        AvailabilityCreateSchema(
            id=custom_uuid(2), country_code=CountryCode.CZ, in_stock=False, version=2
        ),
        AvailabilityCreateSchema(
            id=custom_uuid(3), country_code=CountryCode.CZ, in_stock=True, version=2
        ),
        AvailabilityCreateSchema(
            id=custom_uuid(4), country_code=CountryCode.CZ, in_stock=False, version=2
        ),
    ]
    await availability_service.upsert_many(db_conn_mock, redis_mock, availabilities)
    events = send_price_events_mock.call_args.args[1]
    assert len(events) == 5

    # first message, change in_stock from None to True - IN_STOCK/UPSERT
    assert events[0].product_id == custom_uuid(1)
    assert events[0].type == ProductPriceType.IN_STOCK
    assert events[0].action == PriceEventAction.UPSERT
    assert events[0].price == 10.0
    assert events[0].old_price is None

    # second message, availability remains False - do not generate anything
    # third message, change in_stock from False to True, offer is from certified shop
    # -> IN_STOCK/UPSERT and IN_STOCK_CERTIFIED/UPSERT
    assert events[1].product_id == custom_uuid(3)
    assert events[1].type == ProductPriceType.IN_STOCK
    assert events[1].action == PriceEventAction.UPSERT
    assert events[1].price == 30.0
    assert events[1].old_price is None

    assert events[2].product_id == custom_uuid(3)
    assert events[2].type == ProductPriceType.IN_STOCK_CERTIFIED
    assert events[2].action == PriceEventAction.UPSERT
    assert events[2].price == 30.0
    assert events[2].old_price is None

    # fourth message, change in_stock from True to False, offer is from certified shop
    # -> IN_STOCK/DELETE, IN_STOCK_CERTIFIED/DELETE
    assert events[3].product_id == custom_uuid(4)
    assert events[3].type == ProductPriceType.IN_STOCK
    assert events[3].action == PriceEventAction.DELETE
    assert events[3].price is None
    assert events[3].old_price == 40.0

    assert events[4].product_id == custom_uuid(4)
    assert events[4].type == ProductPriceType.IN_STOCK_CERTIFIED
    assert events[4].action == PriceEventAction.DELETE
    assert events[4].price is None
    assert events[4].old_price == 40.0


@pytest.mark.anyio
@freeze_time("2024-04-30")
async def test_delete_generate_events(
    availability_service, offers: list[OfferDBSchema], mocker
):
    crud_get_in_mock = mocker.patch.object(crud.availability, "get_in")
    crud_get_in_mock.return_value = offers
    crud_delete_mock = mocker.patch.object(crud.availability, "remove_many")
    crud_delete_mock.side_effect = lambda _db_conn, ids_versions: [
        idv[0] for idv in ids_versions
    ]
    send_price_events_mock = mocker.patch.object(
        availability_service, "send_price_events"
    )
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    to_delete = [
        (custom_uuid(1), 3),
        (custom_uuid(2), 3),
        (custom_uuid(4), 3),
    ]
    await availability_service.remove_many(db_conn_mock, redis_mock, to_delete)
    events = send_price_events_mock.call_args.args[1]
    assert len(events) == 2

    # first message, in_stock is not set - do not generate anything
    # second message, change in_stock from False to None - do not generate anything
    # third message, change in_stock from True to None, offer is from certified shop
    # -> IN_STOCK/DELETE and IN_STOCK_CERTIFIED/DELETE
    assert events[0].product_id == custom_uuid(4)
    assert events[0].type == ProductPriceType.IN_STOCK
    assert events[0].action == PriceEventAction.DELETE
    assert events[0].price is None
    assert events[0].old_price == 40.0

    assert events[1].product_id == custom_uuid(4)
    assert events[1].type == ProductPriceType.IN_STOCK_CERTIFIED
    assert events[1].action == PriceEventAction.DELETE
    assert events[1].price is None
    assert events[1].old_price == 40.0
