import pytest

from app import crud
from app.schemas.buyable import BuyableCreateSchema, BuyableUpdateSchema
from tests.factories import buyable_factory
from tests.utils import compare, random_int, random_one_id


@pytest.fixture
async def buyables(db_conn) -> list[BuyableCreateSchema]:
    return [await buyable_factory(db_conn, create=False) for _i in range(5)]


@pytest.mark.anyio
async def test_create_many_buyables_or_update(db_conn):
    buyable_0 = await buyable_factory(db_conn)
    buyable_1_id = random_one_id()
    buyable_2 = await buyable_factory(db_conn)
    buyable_3_id = random_one_id()

    buyables_in = [
        await buyable_factory(
            db_conn, create=False, buyable_id=buyable_0.id, version=buyable_0.version - 1
        ),
        await buyable_factory(
            db_conn,
            create=False,
            buyable_id=buyable_1_id,
            version=random_int(a=1001, b=2000),
        ),
        await buyable_factory(
            db_conn,
            create=False,
            buyable_id=buyable_2.id,
            version=random_int(a=1001, b=2000),
        ),
        await buyable_factory(
            db_conn,
            create=False,
            buyable_id=buyable_3_id,
            version=random_int(a=1001, b=2000),
        ),
    ]
    inserted_ids = await crud.buyable.upsert_many_with_version_checking(
        db_conn, buyables_in
    )
    assert set(inserted_ids) == {buyable_1_id, buyable_2.id, buyable_3_id}

    buyables_in_db = await crud.buyable.get_many(db_conn)
    assert len(buyables_in_db) == 4

    buyable_in_db_map = {s.id: s for s in buyables_in_db}
    compare(buyable_0, buyable_in_db_map[buyables_in[0].id])
    compare(buyables_in[1], buyable_in_db_map[buyables_in[1].id])
    compare(buyables_in[2], buyable_in_db_map[buyables_in[2].id])
    compare(buyables_in[3], buyable_in_db_map[buyables_in[3].id])


@pytest.mark.anyio
async def test_update_many_with_version_checking_buyable(
    db_conn, buyables: list[BuyableCreateSchema]
):
    # Create Buyables
    await crud.buyable.create_many(db_conn, buyables)

    # Create update objects
    update_objs = [
        await buyable_factory(
            db_conn,
            create=False,
            buyable_id=buyable.id,
            version=random_int(a=1001, b=2000),
        )
        for buyable in buyables[:3]
    ]
    update_objs[0].version = buyables[0].version - 1
    assert len(update_objs) == 3
    update_schemas = [
        BuyableUpdateSchema(**buyable.model_dump()) for buyable in update_objs
    ]

    # Update Buyables
    res = await crud.buyable.upsert_many_with_version_checking(db_conn, update_schemas)
    # First one doesn't get updated, rest do
    assert len(res) == 2

    assert res
    for res_buyable in update_objs[1:]:
        compare(res_buyable, await crud.buyable.get(db_conn, res_buyable.id))
