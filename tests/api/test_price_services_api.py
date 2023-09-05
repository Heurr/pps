import pytest
from httpx import AsyncClient
from starlette.status import HTTP_200_OK

from tests.factories import product_factory
from tests.utils import random_one_id


@pytest.mark.anyio
async def test_product_detail_api(api_app, db_conn):
    product_id = random_one_id()
    product = await product_factory(db_conn, product_id=product_id)

    async with AsyncClient(app=api_app, base_url="http://price-services-api") as client:
        res = await client.post(
            "/v1/product-price-history",
            json={"product_id": str(product_id)},
        )

    assert res.status_code == HTTP_200_OK

    data = res.json()

    assert data["product_name"] == product.name
    assert data["product_local_id"] == product.local_product_id
