import pytest

from app import crud
from app.schemas.shop import ShopCreateSchema
from tests.utils import compare


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
