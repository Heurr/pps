import pytest

from app import crud
from app.schemas.product_price_history import (
    ProductPriceHistoryCreateSchema,
    ProductPriceHistoryUpdateSchema,
)
from tests.factories import product_price_history_factory
from tests.utils import (
    compare,
    date_now,
    random_country_code,
    random_int,
    random_one_id,
)


async def product_price_history_fixture_base(db_conn, create: bool):
    histories = [
        await product_price_history_factory(db_conn, create=create) for _i in range(3)
    ]
    random_country = random_country_code(
        {histories[0].country_code, histories[1].country_code}
    )
    histories.extend(
        [
            await product_price_history_factory(
                db_conn,
                create=create,
                product_id=histories[0].id,
                country_code=random_country,
                date=histories[0].date,
            ),
            await product_price_history_factory(
                db_conn,
                create=create,
                product_id=histories[1].id,
                country_code=random_country,
                date=histories[1].date,
            ),
        ]
    )
    return histories


@pytest.fixture
async def product_price_histories_create(
    db_conn,
) -> list[ProductPriceHistoryCreateSchema]:
    return await product_price_history_fixture_base(db_conn, True)


@pytest.fixture
async def product_price_histories(db_conn) -> list[ProductPriceHistoryCreateSchema]:
    return await product_price_history_fixture_base(db_conn, False)


@pytest.mark.anyio
async def test_get_id_country(
    db_conn, product_price_histories_create: list[ProductPriceHistoryCreateSchema]
):
    history_get = product_price_histories_create[0]
    res = await crud.product_price_history.get(
        db_conn,
        (history_get.id, history_get.country_code, history_get.date),
    )

    assert res
    compare(history_get, res)


@pytest.mark.anyio
async def test_get_in_country_id(
    db_conn, product_price_histories_create: list[ProductPriceHistoryCreateSchema]
):
    history_1 = product_price_histories_create[0]
    history_2 = product_price_histories_create[2]
    res = await crud.product_price_history.get_in(
        db_conn,
        [
            (history_1.id, history_1.country_code, history_1.date),
            (history_2.id, history_2.country_code, history_2.date),
        ],
    )

    assert len(res) == 2
    product_map = {
        (p.id, p.country_code, p.date): p for p in product_price_histories_create
    }
    for r in res:
        compare(r, product_map[(r.id, r.country_code, r.date)])


@pytest.mark.anyio
async def test_get_existing_ids(
    db_conn, product_price_histories_create: list[ProductPriceHistoryCreateSchema]
):
    history_1 = product_price_histories_create[0]
    history_2 = product_price_histories_create[2]
    ids = [
        (history_1.id, history_1.country_code, history_1.date),
        (history_2.id, history_2.country_code, history_2.date),
    ]
    res = await crud.product_price_history.find_existing_ids(db_conn, ids)

    assert len(res) == 2
    assert set(ids) == res


@pytest.mark.anyio
async def test_delete_by_id(db_conn):
    to_delete = await product_price_history_factory(db_conn)
    await product_price_history_factory(db_conn)
    history_id = (to_delete.id, to_delete.country_code, to_delete.date)

    res = await crud.product_price_history.remove_by_id(db_conn, history_id)

    assert res == history_id
    assert len(await crud.product_price_history.get_many(db_conn)) == 1


@pytest.mark.anyio
async def test_delete(db_conn):
    to_delete = await product_price_history_factory(db_conn)
    await product_price_history_factory(db_conn)

    res = await crud.product_price_history.remove(db_conn, to_delete)

    assert res == (to_delete.id, to_delete.country_code, to_delete.date)
    assert len(await crud.product_price_history.get_many(db_conn)) == 1


@pytest.mark.anyio
async def test_delete_shop_with_version_checking(db_conn):
    histories = [
        await product_price_history_factory(db_conn, version=10),
        await product_price_history_factory(db_conn, version=10),
        await product_price_history_factory(db_conn, version=10),
        await product_price_history_factory(db_conn, version=10),
        await product_price_history_factory(db_conn, version=10),
    ]
    assert len(await crud.product_price_history.get_many(db_conn)) == 5
    # Only create 4 deletes
    to_delete = [((h.id, h.country_code, h.date), 11) for h in histories[:4]]
    assert len(to_delete) == 4
    # First one doesn't get deleted because of lower version
    to_delete[0] = (to_delete[0][0], 9)

    deleted_ids = await crud.product_price_history.remove_many_with_version_checking(
        db_conn, to_delete
    )
    assert len(await crud.product_price_history.get_many(db_conn)) == 2
    assert len(deleted_ids) == 3
    assert set(deleted_ids) == {(h.id, h.country_code, h.date) for h in histories[1:4]}


@pytest.mark.anyio
async def test_create_many_product_price_history_or_do_nothing(db_conn):
    price_history_0 = await product_price_history_factory(db_conn)
    price_history_1_id = random_one_id(), random_country_code(), date_now()
    price_history_2 = await product_price_history_factory(db_conn)
    price_history_3_id = random_one_id(), random_country_code(), date_now()

    price_histories_in = [
        await product_price_history_factory(
            db_conn,
            create=False,
            product_id=price_history_0.id,
            country_code=price_history_0.country_code,
            date=price_history_0.date,
            version=price_history_0.version - 1,
        ),
        await product_price_history_factory(
            db_conn,
            create=False,
            product_id=price_history_1_id[0],
            country_code=price_history_1_id[1],
            date=price_history_1_id[2],
            version=random_int(a=1001, b=2000),
        ),
        await product_price_history_factory(
            db_conn,
            create=False,
            product_id=price_history_2.id,
            country_code=price_history_2.country_code,
            date=price_history_2.date,
            version=random_int(a=1001, b=2000),
        ),
        await product_price_history_factory(
            db_conn,
            create=False,
            product_id=price_history_3_id[0],
            country_code=price_history_3_id[1],
            date=price_history_3_id[2],
            version=random_int(a=1001, b=2000),
        ),
    ]

    inserted_ids = await crud.product_price_history.upsert_many_with_version_checking(
        db_conn, price_histories_in
    )
    assert set(inserted_ids) == {
        price_history_1_id,
        (price_history_2.id, price_history_2.country_code, price_history_2.date),
        price_history_3_id,
    }

    price_histories_in_db = await crud.product_price_history.get_many(db_conn)
    assert len(price_histories_in_db) == 4

    price_history_map = {s.id: s for s in price_histories_in_db}
    compare(price_history_0, price_history_map[price_histories_in[0].id])
    compare(price_histories_in[1], price_history_map[price_histories_in[1].id])
    compare(price_histories_in[2], price_history_map[price_histories_in[2].id])
    compare(price_histories_in[3], price_history_map[price_histories_in[3].id])


@pytest.mark.anyio
async def test_update_many_with_version_checking_product_price_history(
    db_conn, product_price_histories: list[ProductPriceHistoryCreateSchema]
):
    # Create ProductPriceHistories
    await crud.product_price_history.create_many(db_conn, product_price_histories)

    # Create update objects
    update_objs = [
        await product_price_history_factory(
            db_conn,
            create=False,
            product_id=product_price_history.id,
            country_code=product_price_history.country_code,
            date=product_price_history.date,
            version=random_int(a=1001, b=2000),
        )
        for product_price_history in product_price_histories[:3]
    ]
    update_objs[0].version = product_price_histories[0].version - 1
    assert len(update_objs) == 3
    update_schemas = [
        ProductPriceHistoryUpdateSchema(**product_price_history.dict())
        for product_price_history in update_objs
    ]

    # Update ProductPriceHistories
    res = await crud.product_price_history.upsert_many_with_version_checking(
        db_conn, update_schemas
    )
    # First one doesn't get updated, rest do
    assert len(res) == 2

    for obj in update_objs[1:]:
        compare(
            obj,
            await crud.product_price_history.get(
                db_conn, (obj.id, obj.country_code, obj.date)
            ),
        )
