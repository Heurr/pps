import pytest

from app import crud
from app.constants import CountryCode
from app.schemas.availability import AvailabilityCreateSchema
from app.schemas.offer import OfferDBSchema
from tests.factories import offer_factory
from tests.utils import custom_uuid


@pytest.fixture
async def offers() -> list[OfferDBSchema]:
    return [
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(1),
            country_code=CountryCode.CZ,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(2),
            country_code=CountryCode.CZ,
            availability_version=2,
            in_stock=False,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(3),
            country_code=CountryCode.CZ,
            availability_version=2,
            in_stock=False,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(4),
            country_code=CountryCode.CZ,
            availability_version=2,
            in_stock=False,
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
            in_stock=False,
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
