import pytest
from httpx import AsyncClient
from starlette.status import HTTP_200_OK

from tests.utils import random_one_id


@pytest.mark.anyio
async def test_product_detail_api(api_app, db_conn):
    product_id = random_one_id()

    async with AsyncClient(app=api_app, base_url="http://price-services-api") as client:
        res = await client.get("/v1/ping")

    assert res.status_code == HTTP_200_OK

    data = res.json()

    assert data["pong"]
