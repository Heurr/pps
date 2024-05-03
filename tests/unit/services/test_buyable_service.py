import pytest

from app import crud
from app.constants import CountryCode
from app.schemas.buyable import BuyableCreateSchema
from app.schemas.offer import OfferDBSchema
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
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(2),
            product_id=custom_uuid(2),
            country_code=CountryCode.CZ,
            buyable_version=2,
            buyable=False,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(3),
            product_id=custom_uuid(3),
            country_code=CountryCode.CZ,
            buyable_version=2,
            buyable=False,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(4),
            product_id=custom_uuid(4),
            country_code=CountryCode.CZ,
            buyable_version=2,
            buyable=False,
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
            buyable=False,
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
