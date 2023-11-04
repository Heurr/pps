import pytest
from httpx import AsyncClient
from starlette.status import HTTP_200_OK


@pytest.mark.anyio
async def test_product_detail_api(api_app, db_conn):
    async with AsyncClient(app=api_app, base_url="http://price-services-api") as client:
        res = await client.get("/v1/ping")

    assert res.status_code == HTTP_200_OK

    data = res.json()

    assert data["pong"]
