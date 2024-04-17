import pytest

from app import crud
from app.schemas.shop import ShopCreateSchema
from tests.factories import shop_factory
from tests.utils import compare


@pytest.mark.anyio
async def test_create_shop(db_conn, shops: list[ShopCreateSchema]):
    shop_in = shops[0]

    res = (await crud.shop.create_many(db_conn, [shop_in]))[0]
    assert res
    compare(shop_in, res)


@pytest.mark.anyio
async def test_delete_shop_with_version_checking(db_conn):
    shops = [
        await shop_factory(db_conn, version=10),
        await shop_factory(db_conn, version=10),
        await shop_factory(db_conn, version=10),
        await shop_factory(db_conn, version=10),
        await shop_factory(db_conn, version=10),
    ]
    assert len(await crud.shop.get_many(db_conn)) == 5
    # Only create 4 deletes
    to_delete = [(shop.id, 11) for shop in shops[:4]]
    assert len(to_delete) == 4
    # First one doesn't get deleted because of lower version
    to_delete[0] = (to_delete[0][0], 9)

    deleted_ids = await crud.shop.remove_many_with_version_checking(db_conn, to_delete)
    assert len(await crud.shop.get_many(db_conn)) == 2
    assert len(deleted_ids) == 3
    assert set(deleted_ids) == {shop.id for shop in shops[1:4]}


@pytest.mark.anyio
async def test_create(db_conn, shops: list[ShopCreateSchema]):
    res = await crud.shop.create_many(db_conn, shops)

    assert res
    inserted_shops = await crud.shop.get_many(db_conn)
    shop_map = {s.id: s for s in shops}
    for res_shop in inserted_shops:
        compare(shop_map[res_shop.id], res_shop)


@pytest.mark.anyio
async def test_get_shop(db_conn, shops_create: list[ShopCreateSchema]):
    res = await crud.shop.get_many(db_conn)

    assert len(shops_create) == len(res)
    shop_map = {s.id: s for s in shops_create}
    for res_shop in res:
        compare(res_shop, shop_map[res_shop.id])


@pytest.mark.anyio
async def test_get_in_shop(db_conn, shops_create: list[ShopCreateSchema]):
    res = await crud.shop.get_in(db_conn, [shops_create[0].id, shops_create[2].id])

    assert len(res) == 2
    shop_map = {s.id: s for s in shops_create}
    for res_shop in res:
        compare(res_shop, shop_map[res_shop.id])
