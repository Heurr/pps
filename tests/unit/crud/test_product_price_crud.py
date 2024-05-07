from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app import crud
from app.constants import ProductPriceType
from app.custom_types import ProductPricePk
from app.utils import utc_now
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

    deleted_ids = await crud.product_price.remove_many_for_all_days(
        db_conn, [(product_prices[0].product_id, product_prices[0].price_type)]
    )

    assert deleted_ids == [offer_pk]

    product_price_db = await crud.product_price.get_many(db_conn)
    assert len(product_price_db) == 1
    assert product_price_db[0].product_id == product_prices[1].product_id
