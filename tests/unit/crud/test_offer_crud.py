import pytest
from sqlalchemy.exc import DBAPIError

from app import crud
from app.schemas.offer import OfferCreateSchema
from tests.factories import offer_factory, shop_factory
from tests.utils import compare, random_int, random_one_id


@pytest.fixture
async def offers(db_conn) -> list[OfferCreateSchema]:
    return [await offer_factory() for _ in range(5)]


@pytest.mark.anyio
async def test_create_offer_test_numeric_limit_after_decimal(db_conn):
    price = 123.654194949169149
    offer_in = await offer_factory(price=price)

    res = (await crud.offer.create_many(db_conn, [offer_in]))[0]
    assert res
    compare(offer_in, res, ["price"])
    assert res.price == round(price, 2)


@pytest.mark.anyio
async def test_create_offer_test_numeric_limit_before_decimal(db_conn):
    # Max value is 10^10
    price = (10**10 - 1) + 0.524
    offer_in = await offer_factory(price=price)

    res = (await crud.offer.create_many(db_conn, [offer_in]))[0]
    assert res
    compare(offer_in, res, ignore_keys=["price"])
    assert res.price == round(price, 2)


@pytest.mark.anyio
async def test_create_offer_test_numeric_limit_before_decimal_error(db_conn):
    # Max value is 10^10
    price = (10**10) + 0.524
    offer_in = await offer_factory(price=price)

    with pytest.raises(DBAPIError):
        await crud.offer.create_many(db_conn, [offer_in])


@pytest.mark.anyio
@pytest.mark.skip(
    reason="This will be fixed in next MR "
    "We need to update application code to use composite PK."
)
@pytest.mark.anyio
async def test_create_offers(db_conn):
    offer_0 = await offer_factory(db_conn)
    offer_1_id = random_one_id()
    offer_2 = await offer_factory(db_conn)
    offer_3_id = random_one_id()

    offers_in = [
        await offer_factory(
            offer_id=offer_0.id,
            version=offer_0.version - 1,
            country_code=offer_0.country_code,
        ),
        await offer_factory(offer_id=offer_1_id, version=random_int(a=1001, b=2000)),
        await offer_factory(
            offer_id=offer_2.id,
            version=random_int(a=1001, b=2000),
            country_code=offer_2.country_code,
        ),
        await offer_factory(offer_id=offer_3_id, version=random_int(a=1001, b=2000)),
    ]

    inserted_ids = await crud.offer.upsert_many(db_conn, offers_in)
    assert set(inserted_ids) == {offer_0.id, offer_1_id, offer_2.id, offer_3_id}

    offers_in_db = await crud.offer.get_many(db_conn)
    assert len(offers_in_db) == 4

    offer_map = {s.id: s for s in offers_in_db}
    compare(offers_in[0], offer_map[offers_in[0].id])
    compare(offers_in[1], offer_map[offers_in[1].id])
    compare(offers_in[2], offer_map[offers_in[2].id])
    compare(offers_in[3], offer_map[offers_in[3].id])


@pytest.mark.skip(
    reason="This will be fixed in next MR "
    "We need to update application code to use composite PK."
)
@pytest.mark.anyio
async def test_update_offers(db_conn, offers: list[OfferCreateSchema]):
    await crud.offer.create_many(db_conn, offers)
    create_obj = [
        await offer_factory(
            offer_id=offer.id,
            country_code=offer.country_code,
            version=random_int(a=1001, b=2000),
        )
        for offer in offers[:3]
    ]
    create_obj[0].version = offers[0].version - 1
    assert len(create_obj) == 3
    update_objs = [OfferCreateSchema(**offer.model_dump()) for offer in create_obj]

    res = await crud.offer.upsert_many(db_conn, update_objs)

    # First one doesnt get updated, rest do
    assert len(res) == 3

    assert res
    for res_offer in create_obj[1:]:
        compare(res_offer, (await crud.offer.get_in(db_conn, [res_offer.id]))[0])


@pytest.mark.anyio
async def test_get_in(db_conn):
    shops = [
        await shop_factory(db_conn, certified=True),
        await shop_factory(db_conn, certified=False),
    ]
    offers = [
        await offer_factory(db_conn, shop_id=shops[0].id),
        await offer_factory(db_conn, shop_id=shops[1].id),
        await offer_factory(db_conn),
    ]
    offers_db = await crud.offer.get_in(db_conn, [o.id for o in offers])
    offers_db_map = {o.id: o for o in offers_db}

    assert len(offers_db_map) == 3
    for i in range(3):
        assert offers_db_map[offers[i].id].price == offers[i].price
        assert offers_db_map[offers[i].id].in_stock is None
        assert offers_db_map[offers[i].id].buyable is None
        assert offers_db_map[offers[i].id].availability_version == -1
        assert offers_db_map[offers[i].id].buyable_version == -1

    assert offers_db_map[offers[0].id].certified_shop is True
    assert offers_db_map[offers[1].id].certified_shop is False
    assert offers_db_map[offers[2].id].certified_shop is None
