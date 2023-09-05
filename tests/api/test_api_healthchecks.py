import pytest
from httpx import AsyncClient
from starlette.status import HTTP_200_OK


@pytest.mark.anyio
async def test_api_app_liveness(api_app):
    async with AsyncClient(app=api_app, base_url="http://price-services-api") as client:
        res = await client.get("/-/liveness")
    assert res.status_code == HTTP_200_OK

    data = res.json()
    assert data["status"] == "success"


@pytest.mark.anyio
async def test_api_app_readiness(api_app):
    async with AsyncClient(app=api_app, base_url="http://price-services-api") as client:
        res = await client.get("/-/readiness")
    assert res.status_code == HTTP_200_OK

    data = res.json()
    assert data["status"] == "success"
