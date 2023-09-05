from copy import deepcopy

import pytest

from app import crud
from app.schemas.product import (
    ProductDBSchema,
    ProductCreateSchema,
    ProductUpdateSchema,
)

from ..factories import (
    product_factory,
    product_create_schema_factory,
)
from ..utils import random_string, random_int, random_one_id, random_country_code


@pytest.fixture
async def product(db_conn) -> ProductDBSchema:
    await product_factory(db_conn)
    product = await product_factory(db_conn)
    await product_factory(db_conn)
    return product


@pytest.mark.anyio
async def test_create_product(db_conn):
    product_in = ProductCreateSchema(
        id=random_one_id(),
        local_product_id=random_string(8),
        name=random_string(),
        version=random_int(),
        country=random_country_code(),
    )

    res = await crud.product.create(db_conn, obj_in=product_in)
    assert res
    assert res.local_product_id == product_in.local_product_id
    assert res.name == product_in.name
    assert res.country == product_in.country
    assert res.version == product_in.version
    assert res.created_at
    assert res.updated_at


@pytest.mark.anyio
async def test_get_product(db_conn, product: ProductDBSchema):
    res = await crud.product.get(db_conn, product.id)
    assert res
    assert res == product


@pytest.mark.anyio
async def test_update_product(db_conn, product: ProductDBSchema):
    product_in = ProductUpdateSchema(
        id=product.id,
        name=random_string(),
        version=product.version + 1,
    )

    res = await crud.product.update(db_conn, product_in)
    assert res.id == product.id
    assert res.name == product_in.name
    assert res.version == product_in.version
    assert res.updated_at > product.updated_at


@pytest.mark.anyio
async def test_delete_product(db_conn, product: ProductDBSchema):
    product_id = product.id

    res = await crud.product.remove(db_conn, product)
    assert res == product_id

    res = await crud.product.get(db_conn, product_id)
    assert res is None


@pytest.mark.anyio
async def test_create_many_or_do_nothing(db_conn):
    product_1 = await product_factory(db_conn)
    product_2_id = random_one_id()
    product_3 = await product_factory(db_conn)
    product_4_id = random_one_id()

    products_in = [
        await product_create_schema_factory(db_conn, product_id=product_1.id),
        await product_create_schema_factory(db_conn, product_id=product_2_id),
        await product_create_schema_factory(db_conn, product_id=product_3.id),
        await product_create_schema_factory(
            db_conn, product_id=product_4_id, name=":colon test"
        ),
    ]

    inserted_ids = await crud.product.create_many_or_do_nothing(
        db_conn, deepcopy(products_in)
    )
    assert set(inserted_ids) == {product_2_id, product_4_id}

    products = await crud.product.get_many(db_conn)
    assert len(products) == 4

    product_map = {s.id: s for s in products}
    assert product_map[product_1.id].name == product_1.name
    assert product_map[product_1.id].version == product_1.version

    assert product_map[product_2_id].name == products_in[1].name
    assert product_map[product_2_id].version == products_in[1].version

    assert product_map[product_3.id].name == product_3.name
    assert product_map[product_3.id].version == product_3.version

    assert product_map[product_4_id].name == products_in[3].name
    assert product_map[product_4_id].version == products_in[3].version


@pytest.mark.anyio
async def test_update_many(db_conn):
    products = [
        await product_factory(db_conn, version=1),
        await product_factory(db_conn, version=5),
        await product_factory(db_conn, version=2),
    ]

    for p in products:
        p.version = 3
    products_in = [ProductUpdateSchema(**p.dict()) for p in products]
    updated_ids = await crud.product.update_many(db_conn, deepcopy(products_in))

    assert set(updated_ids) == {products[0].id, products[2].id}

    products_db = await crud.product.get_many(db_conn)
    assert len(products_db) == 3

    product_map = {s.id: s for s in products_db}
    assert product_map[products[0].id].name == products_in[0].name
    assert product_map[products[0].id].version == 3

    assert product_map[products[1].id].name == products[1].name
    assert product_map[products[1].id].version == 5

    assert product_map[products[2].id].name == products_in[2].name
    assert product_map[products[2].id].version == 3


@pytest.mark.anyio
async def test_delete_many_products_with_version_checking(db_conn):
    product_1 = await product_factory(db_conn, version=8)
    product_2 = await product_factory(db_conn, version=12)
    product_3 = await product_factory(db_conn, version=6)

    ids_versions = [
        (str(product_1.id), 10),
        (str(product_2.id), 15),
        (str(product_3.id), 4),
    ]
    await crud.product.remove_many_with_version_checking(db_conn, ids_versions)
    products = await crud.product.get_many(db_conn)
    assert products == [product_3]


@pytest.mark.anyio
async def test_local_keys(db_conn):
    products = [await product_factory(db_conn) for _ in range(4)]
    local_keys = [(c.local_product_id, c.country.value) for c in products[1:3]]
    res = await crud.product.get_local_key_mapping(db_conn, local_keys)

    assert len(res) == 2
    assert (
        res[(products[1].local_product_id, products[1].country.value)] == products[1].id
    )
    assert (
        res[(products[2].local_product_id, products[2].country.value)] == products[2].id
    )
