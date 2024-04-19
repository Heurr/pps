import pytest

from app import crud
from app.constants import CountryCode
from app.schemas.buyable import BuyableCreateSchema
from tests.factories import offer_factory
from tests.utils import custom_uuid


@pytest.mark.anyio
async def test_upsert_many(buyable_service, mocker):
    crud_get_in_mock = mocker.patch.object(crud.buyable, "get_in")
    crud_get_in_mock.return_value = [
        await offer_factory(
            db_schema=True, offer_id=custom_uuid(1), country_code=CountryCode.CZ
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(2),
            country_code=CountryCode.CZ,
            buyable_version=1,
            buyable=False,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(3),
            country_code=CountryCode.CZ,
            buyable_version=3,
            buyable=False,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(4),
            country_code=CountryCode.CZ,
            buyable_version=1,
            buyable=True,
        ),
    ]
    crud_upsert_mock = mocker.patch.object(crud.buyable, "upsert_many")
    crud_upsert_mock.side_effect = lambda _db_conn, entities: [e.id for e in entities]
    db_conn_mock = mocker.AsyncMock()

    buyables = [
        BuyableCreateSchema(
            id=custom_uuid(i + 1),
            country_code=CountryCode.CZ,
            buyable=True,
            version=2,
        )
        for i in range(5)
    ]

    # First buyable should be updated because the offer has no buyable information yet
    # Second buyable should be updated because of new version and value change
    # Third buyable shouldn't be updated because of old version
    # Fourth buyable shouldn't be updated because of no value change
    # Fifth buyable shouldn't be updated because of nonexistent offer
    updated_ids = await buyable_service.upsert_many(db_conn_mock, buyables)
    assert set(updated_ids) == {buyables[0].id, buyables[1].id}
    crud_upsert_mock.assert_called_once_with(db_conn_mock, [buyables[0], buyables[1]])
