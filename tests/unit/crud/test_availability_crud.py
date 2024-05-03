import pytest

from app import crud
from app.constants import CountryCode
from app.schemas.availability import AvailabilityCreateSchema
from app.schemas.offer import OfferDBSchema
from tests.factories import offer_factory
from tests.utils import custom_uuid


@pytest.fixture
async def offers(db_conn) -> list[OfferDBSchema]:
    return [
        await offer_factory(
            db_conn,
            offer_id=custom_uuid(1),
            in_stock=None,
            availability_version=2,
        ),
        await offer_factory(
            db_conn,
            offer_id=custom_uuid(2),
            in_stock=False,
            availability_version=2,
        ),
        await offer_factory(
            db_conn,
            offer_id=custom_uuid(3),
            in_stock=False,
            availability_version=2,
        ),
    ]


@pytest.mark.anyio
async def test_update_availabilities(db_conn, offers: list[OfferDBSchema]):
    """
    First two offers should be updated regardless of versions,
    because we don't check version at CRUD level.
    However, the availability_versions are updated in both cases.
    Third message is ignored because of nonexistent offer ID.
    """
    availabilities_in = [
        AvailabilityCreateSchema(
            id=custom_uuid(1), country_code=CountryCode.CZ, in_stock=True, version=3
        ),
        AvailabilityCreateSchema(
            id=custom_uuid(2), country_code=CountryCode.CZ, in_stock=True, version=1
        ),
        AvailabilityCreateSchema(
            id=custom_uuid(9), country_code=CountryCode.CZ, in_stock=True, version=3
        ),
    ]

    updated_ids = await crud.availability.upsert_many(db_conn, availabilities_in)
    assert set(updated_ids) == {custom_uuid(1), custom_uuid(2)}

    offers_in_db = await crud.offer.get_many(db_conn)
    offers_in_db.sort(key=lambda o: o.id)
    assert offers_in_db[0].id == offers[0].id
    assert offers_in_db[0].in_stock is True
    assert offers_in_db[0].availability_version == 3
    assert offers_in_db[1].id == offers[1].id
    assert offers_in_db[1].in_stock is True
    assert offers_in_db[1].availability_version == 1
    assert offers_in_db[2].id == offers[2].id
    assert offers_in_db[2].in_stock is False
    assert offers_in_db[2].availability_version == 2


@pytest.mark.anyio
async def test_delete_availabilities(db_conn, offers: list[OfferDBSchema]):
    """
    First two offers should be updated (in_stock set to NULL), regardless of version,
    because we don't check versions on CRUD level.
    However, the availability_versions are updated in both cases.
    The third ID is ignored because the corresponding offer does not exist.
    """
    ids_versions = [(custom_uuid(1), 3), (custom_uuid(2), 1), (custom_uuid(4), 3)]

    deleted_ids = await crud.availability.remove_many(db_conn, ids_versions)
    assert set(deleted_ids) == {custom_uuid(1), custom_uuid(2)}

    offers_in_db = await crud.offer.get_many(db_conn)
    offers_in_db.sort(key=lambda o: o.id)

    assert len(offers_in_db) == 3
    assert offers_in_db[0].id == offers[0].id
    assert offers_in_db[0].in_stock is None
    assert offers_in_db[0].availability_version == 3
    assert offers_in_db[1].id == offers[1].id
    assert offers_in_db[1].in_stock is None
    assert offers_in_db[1].availability_version == 1
    assert offers_in_db[2].id == offers[2].id
    assert offers_in_db[2].in_stock is False
    assert offers_in_db[2].availability_version == 2
