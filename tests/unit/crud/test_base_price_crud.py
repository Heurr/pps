import pytest

from app import crud
from app.constants import ProductPriceType
from app.custom_types import BasePricePk
from app.schemas.base_price import BasePriceDBSchema
from tests.factories import base_price_factory
from tests.utils import compare, custom_uuid


@pytest.fixture
async def base_prices(db_conn) -> list[BasePriceDBSchema]:
    return [
        await base_price_factory(
            db_conn,
            product_id=custom_uuid(1),
            price_type=ProductPriceType.ALL_OFFERS,
            price=1,
        ),
        await base_price_factory(
            db_conn,
            product_id=custom_uuid(2),
            price_type=ProductPriceType.ALL_OFFERS,
            price=2,
        ),
    ]


@pytest.mark.anyio
async def test_upsert_many(db_conn, base_prices: list[BasePriceDBSchema]):
    """
    First message should update the first base price,
    second and third should create new base prices
    """
    base_prices_in = [
        await base_price_factory(
            product_id=custom_uuid(1),
            price_type=ProductPriceType.ALL_OFFERS,
            price=10,
        ),
        await base_price_factory(
            product_id=custom_uuid(1),
            price_type=ProductPriceType.IN_STOCK,
            price=11,
        ),
        await base_price_factory(
            product_id=custom_uuid(2),
            price_type=ProductPriceType.IN_STOCK,
            price=13,
        ),
    ]

    upserted_pks = await crud.base_price.upsert_many(db_conn, base_prices_in)
    assert set(upserted_pks) == {
        BasePricePk(bp.product_id, bp.price_type) for bp in base_prices_in
    }

    base_prices_in_db = await crud.base_price.get_many(db_conn)
    base_prices_in_db.sort(key=lambda bp: (bp.product_id, bp.price_type))
    assert len(base_prices_in_db) == 4

    compare(base_prices_in[0], base_prices_in_db[0])
    compare(base_prices_in[1], base_prices_in_db[1])
    compare(base_prices[1], base_prices_in_db[2])
    compare(base_prices_in[2], base_prices_in_db[3])
