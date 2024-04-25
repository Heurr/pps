import pytest

from app import crud
from app.constants import CountryCode
from tests.factories import offer_factory
from tests.utils import custom_uuid


@pytest.mark.anyio
async def test_upsert_many(offer_service, mocker):
    crud_get_in_mock = mocker.patch.object(crud.offer, "get_in")
    crud_get_in_mock.return_value = [
        await offer_factory(
            db_schema=True,
            product_id=custom_uuid(i),
            offer_id=custom_uuid(i),
            country_code=CountryCode.CZ,
            version=i,
        )
        for i in range(3)
    ]

    new_offers_msgs = [
        await offer_factory(
            product_id=custom_uuid(2),
            offer_id=custom_uuid(2),
            country_code=CountryCode.CZ,
            version=1,  # lower version = will not get updated
        ),
        await offer_factory(
            product_id=custom_uuid(1),
            offer_id=custom_uuid(1),
            country_code=CountryCode.CZ,
            version=1,  # same version + different fields = will get updated
        ),
        await offer_factory(
            product_id=custom_uuid(5),
            offer_id=custom_uuid(5),
            country_code=CountryCode.CZ,
            version=5,  # completely new one - will get inserted
        ),
    ]
    crud_upsert_mock = mocker.patch.object(crud.offer, "upsert_many")
    crud_upsert_mock.side_effect = lambda _db_conn, entities: [e.id for e in entities]
    db_conn_mock = mocker.AsyncMock()
    updated_ids = await offer_service.upsert_many(db_conn_mock, new_offers_msgs)
    assert set(updated_ids) == {custom_uuid(1), custom_uuid(5)}
    crud_upsert_mock.assert_called_once_with(
        db_conn_mock, [new_offers_msgs[1], new_offers_msgs[2]]
    )
