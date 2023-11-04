import pytest

from app import crud
from app.schemas.shop import ShopCreateSchema, ShopUpdateSchema
from tests.factories import shop_factory
from tests.utils import compare, random_int, random_one_id


@pytest.mark.anyio
async def test_update_many_with_version_checking_shop(
    db_conn, shops: list[ShopCreateSchema]
):
    # Create shops
    await crud.shop.create_many(db_conn, shops)

    # Create update objects
    update_objs = [
        await shop_factory(
            db_conn,
            create=False,
            shop_id=shop.id,
            version=random_int(a=1001, b=2000),
            certificated=not shop.certificated,
            verified=not shop.verified,
            paying=not shop.paying,
            enabled=not shop.enabled,
        )
        for shop in shops[:3]
    ]
    update_objs[0].version = shops[0].version - 1
    assert len(update_objs) == 3
    update_schemas = [ShopUpdateSchema(**shop.dict()) for shop in update_objs]

    # Update shops
    res = await crud.shop.upsert_many_with_version_checking(db_conn, update_schemas)
    # First one doesnt get updated, rest do
    assert len(res) == 2

    assert res
    for res_shop in update_objs[1:]:
        compare(res_shop, await crud.shop.get(db_conn, res_shop.id))


@pytest.mark.anyio
async def test_create_many_or_do_nothing(db_conn):
    shop_0 = await shop_factory(db_conn)
    shop_1_id = random_one_id()
    shop_2 = await shop_factory(db_conn)
    shop_3_id = random_one_id()

    shops_in = [
        await shop_factory(
            db_conn, create=False, shop_id=shop_0.id, version=shop_0.version - 1
        ),
        await shop_factory(
            db_conn, create=False, shop_id=shop_1_id, version=random_int(a=1001, b=2000)
        ),
        await shop_factory(
            db_conn, create=False, shop_id=shop_2.id, version=random_int(a=1001, b=2000)
        ),
        await shop_factory(
            db_conn, create=False, shop_id=shop_3_id, version=random_int(a=1001, b=2000)
        ),
    ]

    inserted_ids = await crud.shop.upsert_many_with_version_checking(db_conn, shops_in)
    assert set(inserted_ids) == {shop_1_id, shop_2.id, shop_3_id}

    shops_in_db = await crud.shop.get_many(db_conn)
    assert len(shops_in_db) == 4

    shop_map = {s.id: s for s in shops_in_db}
    compare(shop_0, shop_map[shops_in[0].id])
    compare(shops_in[1], shop_map[shops_in[1].id])
    compare(shops_in[2], shop_map[shops_in[2].id])
    compare(shops_in[3], shop_map[shops_in[3].id])
