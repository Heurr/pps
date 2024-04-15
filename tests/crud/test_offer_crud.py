import pytest
from sqlalchemy.exc import DBAPIError

from app import crud
from app.schemas.offer import OfferCreateSchema, OfferUpdateSchema
from tests.factories import offer_factory
from tests.utils import compare, random_int, random_one_id


@pytest.fixture
async def offers(db_conn) -> list[OfferCreateSchema]:
    return [await offer_factory(db_conn, create=False) for _i in range(5)]


@pytest.mark.anyio
async def test_create_offer_test_numeric_limit_after_decimal(db_conn):
    amount = 123.654194949169149
    offer_in = await offer_factory(db_conn, amount=amount, create=False)

    res = await crud.offer.create(db_conn, obj_in=offer_in)
    assert res
    compare(offer_in, res, ["amount"])
    assert res.amount == round(amount, 2)


@pytest.mark.anyio
async def test_create_offer_test_numeric_limit_before_decimal(db_conn):
    # Max value is 10^10
    amount = (10**10 - 1) + 0.524
    offer_in = await offer_factory(db_conn, amount=amount, create=False)

    res = await crud.offer.create(db_conn, obj_in=offer_in)
    assert res
    compare(offer_in, res, ignore_keys=["amount"])
    assert res.amount == round(amount, 2)


@pytest.mark.anyio
async def test_create_offer_test_numeric_limit_before_decimal_error(db_conn):
    # Max value is 10^10
    amount = (10**10) + 0.524
    offer_in = await offer_factory(db_conn, amount=amount, create=False)

    with pytest.raises(DBAPIError):
        await crud.offer.create(db_conn, obj_in=offer_in)


@pytest.mark.anyio
async def test_create_many_or_do_nothing(db_conn):
    offer_0 = await offer_factory(db_conn)
    offer_1_id = random_one_id()
    offer_2 = await offer_factory(db_conn)
    offer_3_id = random_one_id()

    offers_in = [
        await offer_factory(
            db_conn, create=False, offer_id=offer_0.id, version=offer_0.version - 1
        ),
        await offer_factory(
            db_conn, create=False, offer_id=offer_1_id, version=random_int(a=1001, b=2000)
        ),
        await offer_factory(
            db_conn, create=False, offer_id=offer_2.id, version=random_int(a=1001, b=2000)
        ),
        await offer_factory(
            db_conn, create=False, offer_id=offer_3_id, version=random_int(a=1001, b=2000)
        ),
    ]

    inserted_ids = await crud.offer.upsert_many_with_version_checking(db_conn, offers_in)
    assert set(inserted_ids) == {offer_1_id, offer_2.id, offer_3_id}

    offers_in_db = await crud.offer.get_many(db_conn)
    assert len(offers_in_db) == 4

    offer_map = {s.id: s for s in offers_in_db}
    compare(offer_0, offer_map[offers_in[0].id])
    compare(offers_in[1], offer_map[offers_in[1].id])
    compare(offers_in[2], offer_map[offers_in[2].id])
    compare(offers_in[3], offer_map[offers_in[3].id])


@pytest.mark.anyio
async def test_update_many_with_version_checking_offer(
    db_conn, offers: list[OfferCreateSchema]
):
    await crud.offer.create_many(db_conn, offers)
    create_obj = [
        await offer_factory(
            db_conn,
            create=False,
            offer_id=offer.id,
            version=random_int(a=1001, b=2000),
        )
        for offer in offers[:3]
    ]
    create_obj[0].version = offers[0].version - 1
    assert len(create_obj) == 3
    update_objs = [OfferUpdateSchema(**offer.model_dump()) for offer in create_obj]

    res = await crud.offer.upsert_many_with_version_checking(db_conn, update_objs)

    # First one doesnt get updated, rest do
    assert len(res) == 2

    assert res
    for res_offer in create_obj[1:]:
        compare(res_offer, await crud.offer.get(db_conn, res_offer.id))
