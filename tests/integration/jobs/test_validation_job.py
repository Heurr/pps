import pytest
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app.config.settings import ValidationJobSettings
from app.constants import ProductPriceType
from app.custom_types import ProductPriceDeletePk
from app.jobs.validation import ValidationJob
from tests.factories import offer_factory, product_price_factory, shop_factory
from tests.utils import custom_uuid, override_obj_get_db_conn


@pytest.fixture
async def job(
    db_engine: AsyncEngine,
    db_conn: AsyncConnection,
):
    settings = ValidationJobSettings(BERNOULLI_PCT=100, LIMIT=100)
    job = ValidationJob(db_engine, settings)

    override_obj_get_db_conn(db_conn, job)

    yield job


@pytest.fixture()
async def product_prices(db_conn):
    product_prices = [  # all 4 different price_types with product_id=1
        await product_price_factory(
            db_conn,
            product_id=custom_uuid(1),
            price_type=ProductPriceType.ALL_OFFERS,
            min_price=10,
            max_price=19,
        ),
        await product_price_factory(
            db_conn,
            product_id=custom_uuid(1),
            price_type=ProductPriceType.MARKETPLACE,
            min_price=10,
            max_price=19,
        ),
        await product_price_factory(
            db_conn,
            product_id=custom_uuid(1),
            price_type=ProductPriceType.IN_STOCK,
            min_price=10,
            max_price=20,  # different max price than offers fixture
        ),
        await product_price_factory(
            db_conn,
            product_id=custom_uuid(1),
            price_type=ProductPriceType.IN_STOCK_CERTIFIED,
            min_price=10,
            max_price=19,
        ),
    ]
    return product_prices


@pytest.fixture()
async def offers(db_conn):
    shop = await shop_factory(db_conn, shop_id=custom_uuid(8), certified=True)
    # all offers have the same product_id=1 as is in the product_prices, so that they match
    offers = [
        await offer_factory(
            db_conn,
            price=10,  # all min prices are as in product_price fixture
            product_id=custom_uuid(1),
            shop_id=shop.id,
            buyable=True,
            in_stock=True,
        ),
        await offer_factory(
            db_conn,
            price=11,
            product_id=custom_uuid(1),
            shop_id=shop.id,
            buyable=True,
            in_stock=True,
        ),
        await offer_factory(
            db_conn,
            price=19,  # max price is the same as in product_price fixture except for IN_STOCK
            product_id=custom_uuid(1),
            shop_id=shop.id,
            buyable=True,
            in_stock=True,
        ),
    ]
    return offers


@pytest.mark.anyio
async def test_prices_run(product_prices, offers, db_conn, job):
    product_price_sample = await job.get_sample_from_product_price()
    product_keys = [
        ProductPriceDeletePk(i.product_id, i.price_type) for i in product_price_sample
    ]
    offers_sample = await job.get_sample_from_offers(product_keys)

    # there should be 1 diff - the one defined in product_prices - IN_STOCK
    diff = job.find_diff(product_price_sample, offers_sample)
    assert len(diff) == 1
