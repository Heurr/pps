import pytest

from app import crud
from app.schemas.product_price import ProductPriceCreateSchema
from tests.factories import product_price_factory
from tests.utils import compare


@pytest.mark.anyio
async def test_get_id_country(
    db_conn, product_prices_create: list[ProductPriceCreateSchema]
):
    product_price_get = product_prices_create[0]
    res = await crud.product_price.get(
        db_conn, (product_price_get.id, product_price_get.country_code)
    )

    assert res

    compare(product_price_get, res)


@pytest.mark.anyio
async def test_get_in_country_id(
    db_conn, product_prices_create: list[ProductPriceCreateSchema]
):
    res = await crud.product_price.get_in(
        db_conn,
        [
            (product_prices_create[0].id, product_prices_create[0].country_code),
            (product_prices_create[2].id, product_prices_create[2].country_code),
        ],
    )

    assert len(res) == 2
    product_map = {(p.id, p.country_code): p for p in product_prices_create}
    for r in res:
        compare(r, product_map[(r.id, r.country_code)])


@pytest.mark.anyio
async def test_get_existing_ids(
    db_conn, product_prices_create: list[ProductPriceCreateSchema]
):
    ids = [
        (product_prices_create[0].id, product_prices_create[0].country_code),
        (product_prices_create[2].id, product_prices_create[2].country_code),
    ]
    res = await crud.product_price.find_existing_ids(db_conn, ids)

    assert len(res) == 2
    assert set(ids) == res


@pytest.mark.anyio
async def test_delete_by_id(db_conn):
    to_delete = await product_price_factory(db_conn)
    await product_price_factory(db_conn)

    res = await crud.product_price.remove_by_id(
        db_conn, (to_delete.id, to_delete.country_code)
    )

    assert res == (to_delete.id, to_delete.country_code)
    assert len(await crud.product_price.get_many(db_conn)) == 1


@pytest.mark.anyio
async def test_delete(db_conn):
    to_delete = await product_price_factory(db_conn)
    await product_price_factory(db_conn)

    res = await crud.product_price.remove(db_conn, to_delete)

    assert res == (to_delete.id, to_delete.country_code)
    assert len(await crud.product_price.get_many(db_conn)) == 1


@pytest.mark.anyio
async def test_delete_shop_with_version_checking(db_conn):
    product_prices = [
        await product_price_factory(db_conn, version=10),
        await product_price_factory(db_conn, version=10),
        await product_price_factory(db_conn, version=10),
        await product_price_factory(db_conn, version=10),
        await product_price_factory(db_conn, version=10),
    ]
    assert len(await crud.product_price.get_many(db_conn)) == 5
    # Only create 4 deletes
    to_delete = [((pp.id, pp.country_code), 11) for pp in product_prices[:4]]
    assert len(to_delete) == 4
    # First one doesn't get deleted because of lower version
    to_delete[0] = (to_delete[0][0], 9)

    deleted_ids = await crud.product_price.remove_many_with_version_checking(
        db_conn, to_delete
    )
    assert len(await crud.product_price.get_many(db_conn)) == 2
    assert len(deleted_ids) == 3
    assert set(deleted_ids) == {(pp.id, pp.country_code) for pp in product_prices[1:4]}
