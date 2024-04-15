import pytest

from app import crud
from app.schemas.shop import ShopCreateSchema, ShopUpdateSchema
from tests.factories import shop_factory
from tests.utils import compare, random_int


@pytest.mark.anyio
async def test_create_shop(db_conn, shops: list[ShopCreateSchema]):
    shop_in = shops[0]

    res = await crud.shop.create(db_conn, obj_in=shop_in)
    assert res
    compare(shop_in, res)


@pytest.mark.anyio
async def test_update_shop(db_conn, shops: list[ShopCreateSchema]):
    to_update = shops[0]
    await crud.shop.create(db_conn, to_update)

    new_version = random_int(a=1001, b=2000)
    create_obj = await shop_factory(
        db_conn, create=False, shop_id=to_update.id, version=new_version
    )
    update_obj = ShopUpdateSchema(**create_obj.model_dump())
    res = await crud.shop.update(db_conn, update_obj)

    assert res
    assert res.version == new_version
    compare(create_obj, await crud.shop.get(db_conn, res.id))


@pytest.mark.anyio
async def test_delete_shop(db_conn):
    to_delete = await shop_factory(db_conn)
    await shop_factory(db_conn)

    # Create delete object
    delete_obj = await shop_factory(
        db_conn,
        create=False,
        shop_id=to_delete.id,
        version=to_delete.version,
    )
    update_obj_schema = ShopUpdateSchema(**delete_obj.model_dump())

    res = await crud.shop.remove(db_conn, update_obj_schema)

    assert res == to_delete.id
    assert len(await crud.shop.get_many(db_conn)) == 1


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
async def test_delete_by_id_shop(db_conn):
    to_delete = await shop_factory(db_conn)
    await shop_factory(db_conn)

    res = await crud.shop.remove_by_id(db_conn, to_delete.id)

    assert res == to_delete.id
    assert len(await crud.shop.get_many(db_conn)) == 1


@pytest.mark.anyio
async def test_create_many(db_conn, shops: list[ShopCreateSchema]):
    res = await crud.shop.create_many(db_conn, shops)

    assert not res
    inserted_shops = await crud.shop.get_many(db_conn)
    shop_map = {s.id: s for s in shops}
    for res_shop in inserted_shops:
        compare(shop_map[res_shop.id], res_shop)


@pytest.mark.anyio
async def test_get_shop(db_conn, shops_create: list[ShopCreateSchema]):
    res = await crud.shop.get(db_conn, shops_create[0].id)

    assert res

    compare(shops_create[0], res)


@pytest.mark.anyio
async def test_get_many_shop(db_conn, shops_create: list[ShopCreateSchema]):
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


@pytest.mark.anyio
async def test_get_existing_ids(db_conn, shops_create: list[ShopCreateSchema]):
    ids = [shops_create[0].id, shops_create[2].id]
    res = await crud.shop.find_existing_ids(db_conn, ids)

    assert len(res) == 2
    assert set(ids) == res
