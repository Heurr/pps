import pytest

from app import crud
from app.schemas.product_price import ProductPriceCreateSchema, ProductPriceUpdateSchema
from tests.factories import product_price_factory
from tests.utils import compare, random_country_code, random_int, random_one_id


@pytest.mark.anyio
async def test_create_many_product_prices_or_do_nothing(db_conn):
    product_price_0 = await product_price_factory(db_conn)
    product_price_1_id = random_one_id(), random_country_code()
    product_price_2 = await product_price_factory(db_conn)
    product_price_3_id = random_one_id(), random_country_code()

    product_prices_in = [
        await product_price_factory(
            db_conn,
            create=False,
            product_id=product_price_0.id,
            country_code=product_price_0.country_code,
            version=product_price_0.version - 1,
        ),
        await product_price_factory(
            db_conn,
            create=False,
            product_id=product_price_1_id[0],
            country_code=product_price_1_id[1],
            version=random_int(a=1001, b=2000),
        ),
        await product_price_factory(
            db_conn,
            create=False,
            product_id=product_price_2.id,
            country_code=product_price_2.country_code,
            version=random_int(a=1001, b=2000),
        ),
        await product_price_factory(
            db_conn,
            create=False,
            product_id=product_price_3_id[0],
            country_code=product_price_3_id[1],
            version=random_int(a=1001, b=2000),
        ),
    ]

    inserted_ids = await crud.product_price.upsert_many_with_version_checking(
        db_conn, product_prices_in
    )
    assert set(inserted_ids) == {
        product_price_1_id,
        (product_price_2.id, product_price_2.country_code),
        product_price_3_id,
    }

    product_prices_in_db = await crud.product_price.get_many(db_conn)
    assert len(product_prices_in_db) == 4

    product_price_map = {s.id: s for s in product_prices_in_db}
    compare(product_price_0, product_price_map[product_prices_in[0].id])
    compare(product_prices_in[1], product_price_map[product_prices_in[1].id])
    compare(product_prices_in[2], product_price_map[product_prices_in[2].id])
    compare(product_prices_in[3], product_price_map[product_prices_in[3].id])


@pytest.mark.anyio
async def test_update_many_with_version_checking_product_price(
    db_conn, product_prices: list[ProductPriceCreateSchema]
):
    await crud.product_price.create_many(db_conn, product_prices)
    create_objs = [
        await product_price_factory(
            db_conn,
            create=False,
            product_id=product_price.id,
            country_code=product_price.country_code,
            version=random_int(a=1001, b=2000),
        )
        for product_price in product_prices[:3]
    ]
    create_objs[0].version = product_prices[0].version - 1
    assert len(create_objs) == 3
    update_objs = [
        ProductPriceUpdateSchema(**product_price.model_dump())
        for product_price in create_objs
    ]

    res = await crud.product_price.upsert_many_with_version_checking(db_conn, update_objs)

    # First one doesn't get updated, rest do
    assert len(res) == 2

    for res_product_price in create_objs[1:]:
        compare(
            res_product_price,
            await crud.product_price.get(
                db_conn, (res_product_price.id, res_product_price.country_code)
            ),
        )
