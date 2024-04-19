import pytest

from app import crud
from app.schemas.shop import ShopCreateSchema
from tests.factories import shop_factory
from tests.utils import compare, random_int, random_one_id


@pytest.mark.anyio
async def test_update_shops(db_conn, shops: list[ShopCreateSchema]):
    # Create shops
    await crud.shop.create_many(db_conn, shops)
    create_objs = [
        await shop_factory(
            shop_id=shop.id,
            version=random_int(a=1001, b=2000),
            country_code=shop.country_code,
            certified=not shop.certified,
            verified=not shop.verified,
            paying=not shop.paying,
            enabled=not shop.enabled,
        )
        for shop in shops[:3]
    ]
    create_objs[0].version = shops[0].version - 1
    assert len(create_objs) == 3
    create_objs = [ShopCreateSchema(**shop.model_dump()) for shop in create_objs]

    res = await crud.shop.upsert_many(db_conn, create_objs)

    # All get updated since we don't check version
    assert len(res) == 3

    assert res
    for res_shop in create_objs[1:]:
        compare(res_shop, (await crud.shop.get_in(db_conn, [res_shop.id]))[0])


@pytest.mark.anyio
async def test_create_shops(db_conn):
    shop_0 = await shop_factory(db_conn)
    shop_1_id = random_one_id()
    shop_2 = await shop_factory(db_conn)
    shop_3_id = random_one_id()

    shops_in = [
        await shop_factory(
            shop_id=shop_0.id,
            version=shop_0.version - 1,
            country_code=shop_0.country_code,
        ),
        await shop_factory(shop_id=shop_1_id, version=random_int(a=1001, b=2000)),
        await shop_factory(
            shop_id=shop_2.id,
            version=random_int(a=1001, b=2000),
            country_code=shop_2.country_code,
        ),
        await shop_factory(shop_id=shop_3_id, version=random_int(a=1001, b=2000)),
    ]

    inserted_ids = await crud.shop.upsert_many(db_conn, shops_in)
    assert set(inserted_ids) == {shop_0.id, shop_1_id, shop_2.id, shop_3_id}

    shops_in_db = await crud.shop.get_many(db_conn)
    assert len(shops_in_db) == 4

    shop_map = {s.id: s for s in shops_in_db}
    compare(shops_in[0], shop_map[shops_in[0].id])
    compare(shops_in[1], shop_map[shops_in[1].id])
    compare(shops_in[2], shop_map[shops_in[2].id])
    compare(shops_in[3], shop_map[shops_in[3].id])
