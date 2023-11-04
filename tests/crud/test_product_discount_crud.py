import pytest

from app import crud
from app.schemas.product_discount import (
    ProductDiscountCreateSchema,
    ProductDiscountUpdateSchema,
)
from tests.factories import product_discount_factory
from tests.utils import compare, random_country_code, random_int, random_one_id


@pytest.fixture
async def product_discounts(db_conn) -> list[ProductDiscountCreateSchema]:
    product_discounts = [
        await product_discount_factory(db_conn, create=False) for _i in range(3)
    ]
    random_country = random_country_code(
        {product_discounts[0].country_code, product_discounts[1].country_code}
    )
    product_discounts.extend(
        [
            await product_discount_factory(
                db_conn,
                create=False,
                product_id=product_discounts[0].id,
                country_code=random_country,
            ),
            await product_discount_factory(
                db_conn,
                create=False,
                product_id=product_discounts[1].id,
                country_code=random_country,
            ),
        ]
    )
    return product_discounts


@pytest.mark.anyio
async def test_create_many_product_discounts_or_do_nothing(db_conn):
    product_discount_0 = await product_discount_factory(db_conn)
    product_discount_1_id = random_one_id(), random_country_code()
    product_discount_2 = await product_discount_factory(db_conn)
    product_discount_3_id = random_one_id(), random_country_code()

    product_discounts_in = [
        await product_discount_factory(
            db_conn,
            create=False,
            product_id=product_discount_0.id,
            country_code=product_discount_0.country_code,
            version=product_discount_0.version - 1,
        ),
        await product_discount_factory(
            db_conn,
            create=False,
            product_id=product_discount_1_id[0],
            country_code=product_discount_1_id[1],
            version=random_int(a=1001, b=2000),
        ),
        await product_discount_factory(
            db_conn,
            create=False,
            product_id=product_discount_2.id,
            country_code=product_discount_2.country_code,
            version=random_int(a=1001, b=2000),
        ),
        await product_discount_factory(
            db_conn,
            create=False,
            product_id=product_discount_3_id[0],
            country_code=product_discount_3_id[1],
            version=random_int(a=1001, b=2000),
        ),
    ]

    inserted_ids = await crud.product_discount.upsert_many_with_version_checking(
        db_conn, product_discounts_in
    )
    assert set(inserted_ids) == {
        product_discount_1_id,
        (product_discount_2.id, product_discount_2.country_code),
        product_discount_3_id,
    }

    product_discounts_in_db = await crud.product_discount.get_many(db_conn)
    assert len(product_discounts_in_db) == 4

    product_discount_map = {s.id: s for s in product_discounts_in_db}
    compare(product_discount_0, product_discount_map[product_discounts_in[0].id])
    compare(product_discounts_in[1], product_discount_map[product_discounts_in[1].id])
    compare(product_discounts_in[2], product_discount_map[product_discounts_in[2].id])
    compare(product_discounts_in[3], product_discount_map[product_discounts_in[3].id])


@pytest.mark.anyio
async def test_update_many_with_version_checking_product_discount(
    db_conn, product_discounts: list[ProductDiscountCreateSchema]
):
    # Create ProductDiscounts
    await crud.product_discount.create_many(db_conn, product_discounts)

    # Create update objects
    update_objs = [
        await product_discount_factory(
            db_conn,
            create=False,
            product_id=product_discount.id,
            country_code=product_discount.country_code,
            version=random_int(a=1001, b=2000),
        )
        for product_discount in product_discounts[:3]
    ]
    update_objs[0].version = product_discounts[0].version - 1
    assert len(update_objs) == 3
    update_schemas = [
        ProductDiscountUpdateSchema(**product_discount.dict())
        for product_discount in update_objs
    ]

    # Update ProductDiscounts
    res = await crud.product_discount.upsert_many_with_version_checking(
        db_conn, update_schemas
    )
    # First one doesn't get updated, rest do
    assert len(res) == 2
    for res_product_discount in update_objs[1:]:
        compare(
            res_product_discount,
            await crud.product_discount.get(
                db_conn, (res_product_discount.id, res_product_discount.country_code)
            ),
        )
