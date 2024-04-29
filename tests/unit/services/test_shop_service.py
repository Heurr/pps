import pytest

from app import crud
from app.constants import CountryCode
from tests.factories import shop_factory
from tests.utils import custom_uuid


@pytest.mark.anyio
async def test_upsert_many(shop_service, mocker):
    crud_get_in_mock = mocker.patch.object(crud.shop, "get_in")
    crud_get_in_mock.return_value = [
        await shop_factory(
            db_schema=True,
            shop_id=custom_uuid(i),
            country_code=CountryCode.CZ,
            version=i,
            paying=False,
        )
        for i in range(3)
    ]

    new_shop_msgs = [
        await shop_factory(
            shop_id=custom_uuid(2),
            country_code=CountryCode.CZ,
            version=1,  # lower version = will not get updated
        ),
        await shop_factory(
            shop_id=custom_uuid(1),
            country_code=CountryCode.CZ,
            version=99,  # higher version, but no fields changed - no update
        ),
        await shop_factory(
            shop_id=custom_uuid(5),
            country_code=CountryCode.CZ,
            version=1,  # completely new one - will get inserted
        ),
    ]

    crud_upsert_mock = mocker.patch.object(crud.shop, "upsert_many")
    crud_upsert_mock.side_effect = lambda _db_conn, entities: [e.id for e in entities]
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()
    updated_ids = await shop_service.upsert_many(db_conn_mock, redis_mock, new_shop_msgs)
    assert set(updated_ids) == {custom_uuid(5)}
