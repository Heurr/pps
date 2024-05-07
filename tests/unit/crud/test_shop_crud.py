import pytest

from app import crud
from app.schemas.shop import ShopDBSchema
from tests.factories import offer_factory, shop_factory
from tests.utils import compare, custom_uuid


@pytest.fixture
async def shops(db_conn) -> list[ShopDBSchema]:
    return [
        await shop_factory(db_conn, shop_id=custom_uuid(1), certified=False, version=2),
        await shop_factory(db_conn, shop_id=custom_uuid(2), certified=False, version=2),
        await shop_factory(db_conn, shop_id=custom_uuid(3), certified=False, version=2),
    ]


@pytest.mark.anyio
async def test_upsert_many(db_conn, shops: list[ShopDBSchema]):
    """
    First two shops should be updated regardless of version
    because we don't check versions at CRUD level.
    However the `version` is updated in both cases.
    Third shops should be created because of nonexistent offer ID
    """
    shops_in = [
        await shop_factory(
            shop_id=custom_uuid(1),
            country_code=shops[0].country_code,
            certified=True,
            version=3,
        ),
        await shop_factory(
            shop_id=custom_uuid(2),
            country_code=shops[1].country_code,
            certified=True,
            version=1,
        ),
        await shop_factory(
            shop_id=custom_uuid(4),
            country_code=shops[2].country_code,
            certified=True,
            version=3,
        ),
    ]

    upserted_ids = await crud.shop.upsert_many(db_conn, shops_in)
    assert set(upserted_ids) == {o.id for o in shops_in}

    shops_in_db = await crud.shop.get_many(db_conn)
    shops_in_db.sort(key=lambda o: o.id)
    assert len(shops_in_db) == 4

    compare(shops_in[0], shops_in_db[0])
    compare(shops_in[1], shops_in_db[1])
    compare(shops[2], shops_in_db[2])
    compare(shops_in[2], shops_in_db[3])


@pytest.mark.anyio
async def test_delete_shops(db_conn, shops: list[ShopDBSchema]):
    """
    First two shops should be deleted regardless of version,
    because we don't check version at CRUD level.
    Third ID is ignored because of nonexistent shop.
    """
    ids_versions = [(custom_uuid(1), 3), (custom_uuid(2), 1), (custom_uuid(4), 3)]
    deleted_ids = await crud.shop.remove_many(db_conn, ids_versions)

    assert set(deleted_ids) == {custom_uuid(1), custom_uuid(2)}
    shops_in_db = await crud.shop.get_many(db_conn)
    assert len(shops_in_db) == 1
    compare(shops[2], shops_in_db[0])


@pytest.mark.anyio
async def test_get_product_ids_in_stock(db_conn, shops: list[ShopDBSchema]):
    offers = [
        await offer_factory(
            db_conn, offer_id=custom_uuid(1), shop_id=shops[0].id, in_stock=True
        ),
        await offer_factory(
            db_conn, offer_id=custom_uuid(2), shop_id=shops[0].id, in_stock=True
        ),
        await offer_factory(
            db_conn, offer_id=custom_uuid(3), shop_id=shops[0].id, in_stock=False
        ),
        await offer_factory(
            db_conn, offer_id=custom_uuid(4), shop_id=shops[1].id, in_stock=True
        ),
        await offer_factory(db_conn, offer_id=custom_uuid(5), shop_id=shops[1].id),
    ]
    offers_in_stock = await crud.shop.get_offers_in_stock_for_shops(
        db_conn, [s.id for s in shops]
    )
    assert set(offers_in_stock) == {offers[0], offers[1], offers[3]}
