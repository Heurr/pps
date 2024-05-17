import pytest
from freezegun import freeze_time

from app import crud
from app.constants import CountryCode, ProductPriceType
from app.schemas.buyable import BuyableCreateSchema
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
            buyable_version=2,
            buyable=False,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(3),
            product_id=custom_uuid(3),
            country_code=CountryCode.CZ,
            price=30,
            buyable_version=2,
            buyable=False,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(4),
            product_id=custom_uuid(4),
            country_code=CountryCode.CZ,
            price=40,
            buyable_version=2,
            buyable=True,
        ),
    ]


@pytest.mark.anyio
async def test_upsert_many(buyable_service, offers: list[OfferDBSchema], mocker):
    crud_get_in_mock = mocker.patch.object(crud.buyable, "get_in")
    crud_get_in_mock.return_value = offers
    crud_upsert_mock = mocker.patch.object(crud.buyable, "upsert_many")
    crud_upsert_mock.side_effect = lambda _db_conn, entities: [e.id for e in entities]
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    buyables = [
        BuyableCreateSchema(
            id=custom_uuid(1),
            product_id=custom_uuid(1),
            country_code=CountryCode.CZ,
            buyable=True,
            version=3,  # offer has no buyability set yet - should be updated
        ),
        BuyableCreateSchema(
            id=custom_uuid(2),
            product_id=custom_uuid(2),
            country_code=CountryCode.CZ,
            buyable=True,
            version=3,  # higher version, buyability change - should be updated
        ),
        BuyableCreateSchema(
            id=custom_uuid(3),
            product_id=custom_uuid(3),
            country_code=CountryCode.CZ,
            buyable=True,
            version=1,  # lower version - no update
        ),
        BuyableCreateSchema(
            id=custom_uuid(4),
            product_id=custom_uuid(4),
            country_code=CountryCode.CZ,
            buyable=True,
            version=3,  # higher version, no buyability change - no update
        ),
        BuyableCreateSchema(
            id=custom_uuid(5),
            product_id=custom_uuid(6),
            country_code=CountryCode.CZ,
            buyable=True,
            version=3,  # nonexistent PK - no update
        ),
    ]

    updated_ids = await buyable_service.upsert_many(db_conn_mock, redis_mock, buyables)
    assert set(updated_ids) == {buyables[0].id, buyables[1].id}
    crud_upsert_mock.assert_called_once_with(db_conn_mock, [buyables[0], buyables[1]])


@pytest.mark.anyio
async def test_remove_many(buyable_service, offers: list[OfferDBSchema], mocker):
    crud_get_in_mock = mocker.patch.object(crud.buyable, "get_in")
    crud_get_in_mock.return_value = offers
    crud_delete_mock = mocker.patch.object(crud.buyable, "remove_many")
    crud_delete_mock.side_effect = lambda _db_conn, ids_versions: [
        idv[0] for idv in ids_versions
    ]
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    to_delete = [
        (custom_uuid(2), 1),  # lower version - no delete
        (custom_uuid(3), 3),  # higher version - should be deleted
        (custom_uuid(9), 3),  # nonexistent ID - ignore
    ]

    deleted_ids = await buyable_service.remove_many(db_conn_mock, redis_mock, to_delete)
    assert deleted_ids == [custom_uuid(3)]
    crud_delete_mock.assert_called_once_with(db_conn_mock, [(custom_uuid(3), 3)])


@pytest.mark.anyio
@freeze_time("2024-04-30")
async def test_upsert_generate_events(
    buyable_service, offers: list[OfferDBSchema], mocker
):
    crud_get_in_mock = mocker.patch.object(crud.buyable, "get_in")
    crud_get_in_mock.return_value = offers
    mocker.patch.object(crud.buyable, "upsert_many")
    send_price_events_mock = mocker.patch.object(buyable_service, "send_price_events")
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    buyables = [
        BuyableCreateSchema(
            id=custom_uuid(1), country_code=CountryCode.CZ, buyable=True, version=2
        ),
        BuyableCreateSchema(
            id=custom_uuid(2), country_code=CountryCode.CZ, buyable=False, version=2
        ),
        BuyableCreateSchema(
            id=custom_uuid(4), country_code=CountryCode.CZ, buyable=False, version=2
        ),
    ]
    await buyable_service.upsert_many(db_conn_mock, redis_mock, buyables)
    events = send_price_events_mock.call_args.args[1]
    assert len(events) == 2

    # first message, change buyable from None to True - generate MARKETPLACE/UPSERT
    assert events[0].product_id == custom_uuid(1)
    assert events[0].type == ProductPriceType.MARKETPLACE
    assert events[0].action == PriceEventAction.UPSERT
    assert events[0].price == 10.0
    assert events[0].old_price is None

    # second message, buyable remains False - do not generate anything
    # third message, change buyable from True to False - generate MARKETPLACE/DELETE
    assert events[1].product_id == custom_uuid(4)
    assert events[1].type == ProductPriceType.MARKETPLACE
    assert events[1].action == PriceEventAction.DELETE
    assert events[1].price == 40.0
    assert events[1].old_price is None


@pytest.mark.anyio
@freeze_time("2024-04-30")
async def test_delete_generate_events(
    buyable_service, offers: list[OfferDBSchema], mocker
):
    crud_get_in_mock = mocker.patch.object(crud.buyable, "get_in")
    crud_get_in_mock.return_value = offers
    crud_delete_mock = mocker.patch.object(crud.buyable, "remove_many")
    crud_delete_mock.side_effect = lambda _db_conn, ids_versions: [
        idv[0] for idv in ids_versions
    ]
    send_price_events_mock = mocker.patch.object(buyable_service, "send_price_events")
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    to_delete = [
        (custom_uuid(1), 3),
        (custom_uuid(2), 3),
        (custom_uuid(4), 3),
    ]
    await buyable_service.remove_many(db_conn_mock, redis_mock, to_delete)
    events = send_price_events_mock.call_args.args[1]
    assert len(events) == 1

    # first message, buyable is not set - do not generate anything
    # second message, change buyable from False to None - do not generate anything
    # third message, change buyable from True to None - generate MARKETPLACE/DELETE
    assert events[0].product_id == custom_uuid(4)
    assert events[0].type == ProductPriceType.MARKETPLACE
    assert events[0].action == PriceEventAction.DELETE
    assert events[0].price == 40.0
    assert events[0].old_price is None
