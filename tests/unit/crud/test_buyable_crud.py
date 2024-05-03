import pytest

from app import crud
from app.constants import CountryCode
from app.schemas.buyable import BuyableCreateSchema
from app.schemas.offer import OfferDBSchema
from tests.factories import offer_factory
from tests.utils import custom_uuid


@pytest.fixture
async def offers(db_conn) -> list[OfferDBSchema]:
    return [
        await offer_factory(
            db_conn,
            offer_id=custom_uuid(1),
            buyable=None,
            buyable_version=2,
        ),
        await offer_factory(
            db_conn,
            offer_id=custom_uuid(2),
            buyable=False,
            buyable_version=2,
        ),
        await offer_factory(
            db_conn,
            offer_id=custom_uuid(3),
            buyable=False,
            buyable_version=2,
        ),
    ]


@pytest.mark.anyio
async def test_update_buyables(db_conn, offers: list[OfferDBSchema]):
    """
    First two offers should be updated regardless of version,
    because we don't check version at CRUD level.
    However, the buyable_versions are updated in both cases.
    Third message is ignored because of nonexistent offer ID
    """
    buyables_in = [
        BuyableCreateSchema(
            id=custom_uuid(1),
            country_code=CountryCode.CZ,
            buyable=True,
            version=3,
        ),
        BuyableCreateSchema(
            id=custom_uuid(2),
            country_code=CountryCode.CZ,
            buyable=True,
            version=1,
        ),
        BuyableCreateSchema(
            id=custom_uuid(4),
            country_code=CountryCode.CZ,
            buyable=True,
            version=3,
        ),
    ]

    updated_ids = await crud.buyable.upsert_many(db_conn, buyables_in)
    assert set(updated_ids) == {custom_uuid(1), custom_uuid(2)}

    offers_in_db = await crud.offer.get_many(db_conn)
    offers_in_db.sort(key=lambda o: o.id)
    assert offers_in_db[0].id == offers[0].id
    assert offers_in_db[0].buyable is True
    assert offers_in_db[0].buyable_version == 3
    assert offers_in_db[1].id == offers[1].id
    assert offers_in_db[1].buyable is True
    assert offers_in_db[1].buyable_version == 1
    assert offers_in_db[2].id == offers[2].id
    assert offers_in_db[2].buyable is False
    assert offers_in_db[2].buyable_version == 2


@pytest.mark.anyio
async def test_delete_buyables(db_conn, offers: list[OfferDBSchema]):
    """
    First two offers should be updated (buyable set to NULL), regardless of version,
    because we don't check versions on CRUD level.
    However, the buyable_versions are updated in both cases.
    Third ID is ignored because of nonexistent offer ID.
    """
    pks_versions = [
        (custom_uuid(1), 3),
        (custom_uuid(2), 1),
        (custom_uuid(4), 3),
    ]

    deleted_ids = await crud.buyable.remove_many(db_conn, pks_versions)
    assert set(deleted_ids) == {custom_uuid(1), custom_uuid(2)}

    offers_in_db = await crud.offer.get_many(db_conn)
    offers_in_db.sort(key=lambda o: o.id)

    assert len(offers_in_db) == 3
    assert offers_in_db[0].id == offers[0].id
    assert offers_in_db[0].buyable is None
    assert offers_in_db[0].buyable_version == 3
    assert offers_in_db[1].id == offers[1].id
    assert offers_in_db[1].buyable is None
    assert offers_in_db[1].buyable_version == 1
    assert offers_in_db[2].id == offers[2].id
    assert offers_in_db[2].buyable is False
    assert offers_in_db[2].buyable_version == 2
