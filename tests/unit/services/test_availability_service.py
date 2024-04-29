import pytest

from app import crud
from app.constants import CountryCode
from app.schemas.availability import AvailabilityCreateSchema
from tests.factories import offer_factory
from tests.utils import custom_uuid


@pytest.mark.anyio
async def test_upsert_many(availability_service, mocker):
    crud_get_in_mock = mocker.patch.object(crud.availability, "get_in")
    crud_get_in_mock.return_value = [
        await offer_factory(
            db_schema=True, offer_id=custom_uuid(1), country_code=CountryCode.CZ
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(2),
            country_code=CountryCode.CZ,
            availability_version=1,
            in_stock=False,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(3),
            country_code=CountryCode.CZ,
            availability_version=3,
            in_stock=False,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(4),
            country_code=CountryCode.CZ,
            availability_version=1,
            in_stock=True,
        ),
    ]
    crud_upsert_mock = mocker.patch.object(crud.availability, "upsert_many")
    crud_upsert_mock.side_effect = lambda _db_conn, entities: [e.id for e in entities]
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    availabilities = [
        AvailabilityCreateSchema(
            id=custom_uuid(i + 1),
            country_code=CountryCode.CZ,
            in_stock=True,
            version=2,
        )
        for i in range(5)
    ]

    # First availability should be updated because the offer has no availability
    # information yet
    # Second availability should be updated because of new version and value change
    # Third availability shouldn't be updated because of old version
    # Fourth availability shouldn't be updated because of no value change
    # Fifth availability shouldn't be updated because of nonexistent offer
    updated_ids = await availability_service.upsert_many(
        db_conn_mock, redis_mock, availabilities
    )
    assert set(updated_ids) == {availabilities[0].id, availabilities[1].id}
    crud_upsert_mock.assert_called_once_with(
        db_conn_mock, [availabilities[0], availabilities[1]]
    )
