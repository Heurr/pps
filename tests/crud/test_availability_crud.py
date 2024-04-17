import pytest

from app import crud
from app.schemas.availability import AvailabilityCreateSchema
from tests.factories import availability_factory
from tests.utils import compare, random_int, random_one_id


@pytest.fixture
async def availabilities(db_conn) -> list[AvailabilityCreateSchema]:
    return [await availability_factory(db_conn, create=False) for _i in range(5)]


@pytest.mark.anyio
async def test_create_many_availabilities_or_do_nothing(db_conn):
    availability_0 = await availability_factory(db_conn)
    availability_1_id = random_one_id()
    availability_2 = await availability_factory(db_conn)
    availability_3_id = random_one_id()

    availabilities_in = [
        await availability_factory(
            db_conn,
            create=False,
            availability_id=availability_0.id,
            country_code=availability_0.country_code,
            version=availability_0.version - 1,
        ),
        await availability_factory(
            db_conn,
            create=False,
            availability_id=availability_1_id,
            version=random_int(a=1001, b=2000),
        ),
        await availability_factory(
            db_conn,
            create=False,
            availability_id=availability_2.id,
            country_code=availability_2.country_code,
            version=random_int(a=1001, b=2000),
        ),
        await availability_factory(
            db_conn,
            create=False,
            availability_id=availability_3_id,
            version=random_int(a=1001, b=2000),
        ),
    ]

    inserted_ids = await crud.availability.upsert_many_with_version_checking(
        db_conn, availabilities_in
    )
    assert set(inserted_ids) == {availability_1_id, availability_2.id, availability_3_id}

    availabilities_in_db = await crud.availability.get_many(db_conn)
    assert len(availabilities_in_db) == 4

    availability_map = {s.id: s for s in availabilities_in_db}
    compare(availability_0, availability_map[availabilities_in[0].id])
    compare(availabilities_in[1], availability_map[availabilities_in[1].id])
    compare(availabilities_in[2], availability_map[availabilities_in[2].id])
    compare(availabilities_in[3], availability_map[availabilities_in[3].id])


@pytest.mark.anyio
async def test_update_many_with_version_checking_availability(
    db_conn, availabilities: list[AvailabilityCreateSchema]
):
    await crud.availability.create_many(db_conn, availabilities)

    create_objs = [
        await availability_factory(
            db_conn,
            create=False,
            availability_id=availability.id,
            country_code=availability.country_code,
            version=random_int(a=1001, b=2000),
        )
        for availability in availabilities[:3]
    ]
    create_objs[0].version = availabilities[0].version - 1
    assert len(create_objs) == 3
    update_objs = [
        AvailabilityCreateSchema(**availability.model_dump())
        for availability in create_objs
    ]

    res = await crud.availability.upsert_many_with_version_checking(db_conn, update_objs)

    # First one doesn't get updated, rest do
    assert len(res) == 2

    assert res
    for res_availability in create_objs[1:]:
        compare(
            res_availability, await crud.availability.get(db_conn, res_availability.id)
        )
