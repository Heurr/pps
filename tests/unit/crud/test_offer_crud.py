import pytest
from _pytest.mark import param
from sqlalchemy.exc import DBAPIError

from app import crud
from app.constants import Aggregate, Entity, ProductPriceType
from app.custom_types import OfferPk
from app.schemas.offer import OfferDBSchema
from tests.factories import offer_factory, shop_factory
from tests.utils import compare, custom_uuid


@pytest.fixture
async def offers(db_conn) -> list[OfferDBSchema]:
    return [
        await offer_factory(
            db_conn,
            offer_id=custom_uuid(1),
            product_id=custom_uuid(1),
            price=1,
            version=2,
        ),
        await offer_factory(
            db_conn,
            offer_id=custom_uuid(2),
            product_id=custom_uuid(2),
            price=1,
            version=2,
        ),
        await offer_factory(
            db_conn,
            offer_id=custom_uuid(3),
            product_id=custom_uuid(3),
            price=1,
            version=2,
        ),
    ]


@pytest.mark.anyio
async def test_create_offer_test_numeric_limit_after_decimal(db_conn):
    """
    Test rounding price to 2 decimal places when storing to db
    """
    price = 123.654194949169149
    offer_in = await offer_factory(price=price)

    res = (await crud.offer.create_many(db_conn, [offer_in]))[0]
    assert res
    compare(offer_in, res, ["price"])
    assert res.price == round(price, 2)


@pytest.mark.anyio
async def test_create_offer_test_numeric_limit_before_decimal(db_conn):
    """
    Test max price value 10^10 when storing to db
    """
    price = (10**10 - 1) + 0.524
    offer_in = await offer_factory(price=price)

    res = (await crud.offer.create_many(db_conn, [offer_in]))[0]
    assert res
    compare(offer_in, res, ignore_keys=["price"])
    assert res.price == round(price, 2)


@pytest.mark.anyio
async def test_create_offer_test_numeric_limit_before_decimal_error(db_conn):
    """
    Test attempt to storing price higher than max price value 10^10
    """
    price = (10**10) + 0.524
    offer_in = await offer_factory(price=price)

    with pytest.raises(DBAPIError):
        await crud.offer.create_many(db_conn, [offer_in])


@pytest.mark.anyio
async def test_get_in(db_conn):
    """
    Test retrieving offers with `certified_shop` set
    """
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


@pytest.mark.anyio
async def test_upsert_many(db_conn, offers: list[OfferDBSchema]):
    """
    First two offers should be updated regardless of version
    because we don't check versions at CRUD level.
    However the `version` is updated in both cases.
    Third offer should be created because of nonexistent offer ID
    """
    offers_in = [
        await offer_factory(
            offer_id=custom_uuid(1),
            product_id=custom_uuid(1),
            country_code=offers[0].country_code,
            price=2,
            version=3,
        ),
        await offer_factory(
            offer_id=custom_uuid(2),
            product_id=custom_uuid(2),
            country_code=offers[1].country_code,
            price=2,
            version=1,
        ),
        await offer_factory(
            offer_id=custom_uuid(4),
            product_id=custom_uuid(4),
            country_code=offers[2].country_code,
            price=2,
            version=3,
        ),
    ]

    upserted_ids = await crud.offer.upsert_many(db_conn, offers_in)
    assert set(upserted_ids) == {o.id for o in offers_in}

    offers_in_db = await crud.offer.get_many(db_conn)
    offers_in_db.sort(key=lambda o: o.id)
    assert len(offers_in_db) == 4

    compare(offers_in[0], offers_in_db[0])
    compare(offers_in[1], offers_in_db[1])
    compare(offers[2], offers_in_db[2])
    compare(offers_in[2], offers_in_db[3])


@pytest.mark.anyio
async def test_remove_many(db_conn, offers: list[OfferDBSchema]):
    """
    First two offers should be deleted regardless of version
    because we don't check versions at CRUD level.
    Third offer is ignored because of nonexistent offer ID.
    """
    ids_versions = [
        (custom_uuid(1), 3),
        (custom_uuid(2), 1),
        (custom_uuid(4), 3),
    ]

    deleted_ids = await crud.offer.remove_many(db_conn, ids_versions)
    assert set(deleted_ids) == {custom_uuid(1), custom_uuid(2)}

    offers_in_db = await crud.offer.get_many(db_conn)
    assert len(offers_in_db) == 1
    compare(offers[2], offers_in_db[0])


@pytest.mark.anyio
async def test_remove_many_empty(db_conn, offers: list[OfferDBSchema]):
    deleted_ids = await crud.offer.remove_many(db_conn, [])
    assert set(deleted_ids) == set()

    offers_in_db = await crud.offer.get_many(db_conn)
    assert len(offers_in_db) == 3


@pytest.mark.anyio
async def test_get_unpopulated_offers(db_conn):
    version = [(-1, -1), (-1, 0), (0, -1), (0, 0)]
    offers = [
        await offer_factory(
            db_conn,
            availability_version=versions[0],
            buyable_version=versions[1],
            offer_id=custom_uuid(i + 1),
        )
        for i, versions in enumerate(version)
    ]

    results = []
    batches = 0
    async for batch in crud.offer.get_unpopulated_offers(db_conn, 1):
        batches += 1
        results.extend([offer.id for offer in batch])

    assert len(results) == 3
    assert batches == 3
    assert {offers[0].id, offers[1].id, offers[2].id} == set(results)


@pytest.mark.anyio
async def test_set_offers_as_populated(db_conn):
    version = [(-1, -1), (-1, 0), (0, -1), (2, 2)]
    offers = [
        await offer_factory(
            db_conn,
            availability_version=versions[0],
            buyable_version=versions[1],
            offer_id=custom_uuid(i + 1),
        )
        for i, versions in enumerate(version)
    ]

    await crud.offer.set_offers_as_populated(
        db_conn,
        [Entity.AVAILABILITY],
        [OfferPk(offer.product_id, offer.id) for offer in offers],
    )

    db_offers = {offer.id: offer for offer in await crud.offer.get_many(db_conn)}
    assert db_offers[offers[0].id].availability_version == 0
    assert db_offers[offers[0].id].buyable_version == -1
    assert db_offers[offers[1].id].availability_version == 0
    assert db_offers[offers[1].id].buyable_version == 0
    assert db_offers[offers[2].id].availability_version == 0
    assert db_offers[offers[2].id].buyable_version == -1
    assert db_offers[offers[3].id].availability_version == 0
    assert db_offers[offers[3].id].buyable_version == 2


@pytest.mark.anyio
@pytest.mark.parametrize(
    "price_type, aggregate, expected",
    [
        param(ProductPriceType.ALL_OFFERS, Aggregate.MIN, 1.0, id="min_all_offers"),
        param(ProductPriceType.ALL_OFFERS, Aggregate.MAX, 8.0, id="max_all_offers"),
        param(ProductPriceType.IN_STOCK, Aggregate.MIN, 3.0, id="min_in_stock_offers"),
        param(ProductPriceType.IN_STOCK, Aggregate.MAX, 8.0, id="max_in_stock_offers"),
        param(
            ProductPriceType.MARKETPLACE, Aggregate.MIN, 4.0, id="min_marketplace_offers"
        ),
        param(
            ProductPriceType.MARKETPLACE, Aggregate.MAX, 6.0, id="max_marketplace_offers"
        ),
        param(
            ProductPriceType.IN_STOCK_CERTIFIED,
            Aggregate.MIN,
            7.0,
            id="min_certified_offers",
        ),
        param(
            ProductPriceType.IN_STOCK_CERTIFIED,
            Aggregate.MAX,
            8.0,
            id="max_certified_offers",
        ),
    ],
)
async def test_get_price(db_conn, price_type, aggregate, expected):
    """
    Offer 1 -- ALL OFFERS
    Offer 2 -- ALL OFFERS
    Offer 3 -- IN STOCK
    Offer 4 -- IN STOCK, BUYABLE
    Offer 5 -- BUYABLE
    Offer 6 -- BUYABLE
    Offer 7 -- CERTIFIED
    Offer 8 -- CERTIFIED
    """
    product_id = custom_uuid(1)
    in_stocks = [False, False, True, True, False, False, True, True]
    buyables = [False, False, False, True, True, True, False, False]
    shop_ids = [None, None, None, None, None, None, custom_uuid(1), custom_uuid(1)]
    await shop_factory(db_conn, certified=True, shop_id=custom_uuid(1))
    offers = [
        await offer_factory(
            db_conn,
            price=i + 1,
            offer_id=custom_uuid(i + 1),
            product_id=product_id,
            in_stock=in_stock,
            buyable=buyable,
            shop_id=shop_id,
        )
        for in_stock, buyable, i, shop_id in zip(in_stocks, buyables, range(8), shop_ids)
    ]

    price = await crud.offer.get_price_for_product(
        db_conn, product_id, price_type, aggregate
    )
    assert float(price) == expected
