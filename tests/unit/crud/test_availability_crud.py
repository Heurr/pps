import pytest

from app import crud
from app.schemas.availability import AvailabilityCreateSchema
from tests.factories import offer_factory
from tests.utils import custom_uuid


@pytest.mark.anyio
async def test_update_availabilities(db_conn):
    offers = [
        await offer_factory(db_conn, offer_id=custom_uuid(i), availability_version=1)
        for i in range(4)
    ]
    availabilities_in = [
        AvailabilityCreateSchema(
            id=custom_uuid(i),
            country_code=offers[i].country_code,
            in_stock=True,
            version=i,
        )
        for i in range(4)
    ]

    # First two availabilities are not updated because of old version
    # Second two availabilities are updated
    updated_ids = await crud.availability.upsert_many(db_conn, availabilities_in)
    assert set(updated_ids) == {offers[2].id, offers[3].id}

    offers_in_db = await crud.offer.get_many(db_conn)
    offers_in_db.sort(key=lambda o: o.id)
    assert len(offers) == 4
    for i in range(4):
        old_offer = offers[i].model_dump()
        new_offer = offers_in_db[i].model_dump()
        if i >= 2:
            old_offer["in_stock"] = True
            old_offer["availability_version"] = i
        assert old_offer == new_offer


@pytest.mark.anyio
async def test_delete_availabilities(db_conn):
    offers = [
        await offer_factory(db_conn, offer_id=custom_uuid(i), availability_version=1)
        for i in range(4)
    ]
    ids_to_delete = [(custom_uuid(i), i) for i in range(4)]

    # First two availabilities are not deleted because of old version
    # Second two availabilities are deleted (=set to NULL)
    deleted_ids = await crud.availability.remove_many_with_version_checking(
        db_conn, ids_to_delete
    )
    assert set(deleted_ids) == {offers[2].id, offers[3].id}

    offers_in_db = await crud.offer.get_many(db_conn)
    offers_in_db.sort(key=lambda o: o.id)
    assert len(offers) == 4
    for i in range(4):
        old_offer = offers[i].model_dump()
        new_offer = offers_in_db[i].model_dump()
        if i >= 2:
            old_offer["in_stock"] = None
            old_offer["availability_version"] = i
        assert old_offer == new_offer
