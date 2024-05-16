from datetime import timedelta

import freezegun
import pytest
from sqlalchemy.exc import IntegrityError

from app import crud
from app.constants import ProductPriceType
from app.custom_types import ProductPriceDeletePk, ProductPricePk
from app.utils import utc_now, utc_today
from tests.factories import product_price_factory
from tests.utils import compare, custom_uuid


@pytest.mark.anyio
async def test_get_in_product_prices(db_conn):
    product_price = await product_price_factory(db_conn, product_id=custom_uuid(1))

    product_price_db = await crud.product_price.get_in(
        db_conn, [(product_price.day, product_price.product_id, product_price.price_type)]
    )

    compare(product_price, product_price_db[0])


@pytest.mark.anyio
async def test_upsert_product_prices(db_conn):
    # Create one product price
    await product_price_factory(db_conn, product_id=custom_uuid(1), min_price=2)
    # Update first created product price via min price change
    update_product_price = await product_price_factory(
        product_id=custom_uuid(1), min_price=1
    )

    # Create 4 new product prices
    product_prices_new = [
        await product_price_factory(product_id=custom_uuid(10)) for _ in range(4)
    ]
    # Each product price has a unique PK but in different columns
    product_prices_new[1].day = (utc_now() + timedelta(days=2)).date()
    product_prices_new[2].price_type = ProductPriceType.ALL_OFFERS
    product_prices_new[3].product_id = custom_uuid(11)

    product_prices = [update_product_price] + product_prices_new

    # Upsert all
    upserted_ids = await crud.product_price.upsert_many(db_conn, product_prices)
    assert len(upserted_ids) == 5
    # Check if all product_prices are upserted
    assert set(upserted_ids) == {
        (price.day, price.product_id, price.price_type) for price in product_prices
    }

    product_price_db = await crud.product_price.get_many(db_conn)
    product_price_db_by_pk = {
        (price.day, price.product_id, price.price_type): price
        for price in product_price_db
    }
    assert len(product_price_db) == 5
    # Check if the first product price is updated
    assert (
        product_price_db_by_pk[
            (
                update_product_price.day,
                update_product_price.product_id,
                update_product_price.price_type,
            )
        ].min_price
        == 1
    )


@pytest.mark.anyio
async def test_upsert_product_prices_duplicate_pk(db_conn):
    # Create one product price
    await product_price_factory(db_conn, product_id=custom_uuid(1), min_price=2)
    # Update first created product price via min price change
    update_product_price = await product_price_factory(
        product_id=custom_uuid(1), min_price=1
    )

    with pytest.raises(IntegrityError):
        await crud.product_price.create_many(db_conn, [update_product_price])


@pytest.mark.anyio
async def test_delete_product_prices(db_conn):
    product_prices = [
        await product_price_factory(db_conn, product_id=custom_uuid(i), min_price=2)
        for i in range(2)
    ]
    offer_pk = ProductPricePk(
        product_prices[0].day,
        product_prices[0].product_id,
        product_prices[0].price_type,
    )

    deleted_ids = await crud.product_price.remove_many(
        db_conn,
        [
            ProductPriceDeletePk(
                product_prices[0].product_id, product_prices[0].price_type
            )
        ],
        utc_today(),
    )

    assert deleted_ids == [offer_pk]

    product_price_db = await crud.product_price.get_many(db_conn)
    assert len(product_price_db) == 1
    assert product_price_db[0].product_id == product_prices[1].product_id


@pytest.mark.anyio
async def test_delete_product_prices_empty(db_conn):
    await product_price_factory(db_conn)
    deleted_ids = await crud.product_price.remove_many(db_conn, [], utc_today())

    assert deleted_ids == []

    product_price_db = await crud.product_price.get_many(db_conn)
    assert len(product_price_db) == 1


@pytest.mark.anyio
async def test_remove_history(db_conn):
    # We can't create in the past because partition tables are only created
    # for the future
    # Delete this
    await product_price_factory(db_conn, product_id=custom_uuid(1))
    # Don't delete since its yesterdays data
    with freezegun.freeze_time(utc_now() + timedelta(days=1)):
        await product_price_factory(db_conn, product_id=custom_uuid(2))
    # Don't delete since its today data
    with freezegun.freeze_time(utc_now() + timedelta(days=2)):
        await product_price_factory(db_conn, product_id=custom_uuid(3))

        await crud.product_price.remove_history(
            # Keep 1 days history, that means keeping today and yesterday, delete rest
            db_conn,
            utc_now() - timedelta(days=1),
        )

    product_prices = await crud.product_price.get_many(db_conn)
    assert len(product_prices) == 2


@pytest.mark.anyio
async def test_duplicate_day(db_conn):
    await product_price_factory(db_conn, product_id=custom_uuid(1))
    await product_price_factory(db_conn, product_id=custom_uuid(2), min_price=1)
    await product_price_factory(
        db_conn,
        product_id=custom_uuid(2),
        day=utc_today() + timedelta(days=1),
        min_price=2,
    )

    await crud.product_price.duplicate_day(db_conn, utc_now().date())

    product_prices = await crud.product_price.get_many(db_conn)
    assert len(product_prices) == 4
    product_prices_map = {
        (price.product_id, price.day): price for price in product_prices
    }
    # Copied product price is the same
    compare(
        product_prices_map[(custom_uuid(1), utc_today())],
        product_prices_map[(custom_uuid(1), utc_today() + timedelta(days=1))],
        ignore_keys=["day"],
    )
    # Already created product price is not overridden
    assert (
        product_prices_map[(custom_uuid(2), utc_today() + timedelta(days=1))].min_price
        == 2
    )
