import pytest

from app import crud
from app.constants import CountryCode
from app.schemas.shop import ShopCreateSchema, ShopDBSchema
from tests.factories import shop_factory
from tests.utils import custom_uuid


@pytest.fixture
async def shops() -> list[ShopDBSchema]:
    return [
        await shop_factory(
            db_schema=True,
            shop_id=custom_uuid(i + 1),
            country_code=CountryCode.CZ,
            version=2,
            paying=False,
        )
        for i in range(3)
    ]


@pytest.mark.anyio
async def test_upsert_many(shop_service, shops: list[ShopDBSchema], mocker):
    crud_get_in_mock = mocker.patch.object(crud.shop, "get_in")
    crud_get_in_mock.return_value = shops
    crud_upsert_mock = mocker.patch.object(crud.shop, "upsert_many")
    crud_upsert_mock.side_effect = lambda _db_conn, entities: [e.id for e in entities]

    new_shop_msgs = [
        await shop_factory(
            shop_id=custom_uuid(1),
            country_code=CountryCode.CZ,
            version=1,  # lower version - no update
        ),
        await shop_factory(
            shop_id=custom_uuid(2),
            country_code=CountryCode.CZ,
            version=99,  # higher version, but no fields changed - no update
        ),
        await shop_factory(
            shop_id=custom_uuid(3),
            country_code=CountryCode.CZ,
            certified=True,
            version=99,  # higher version, fields changed - should be updated
        ),
        await shop_factory(
            shop_id=custom_uuid(5),
            country_code=CountryCode.CZ,
            version=1,  # new shop ID - should be inserted
        ),
    ]

    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()
    updated_ids = await shop_service.upsert_many(db_conn_mock, redis_mock, new_shop_msgs)
    assert set(updated_ids) == {custom_uuid(3), custom_uuid(5)}
    crud_upsert_mock.assert_called_once_with(
        db_conn_mock, [new_shop_msgs[2], new_shop_msgs[3]]
    )


@pytest.mark.anyio
async def test_remove_many(shop_service, shops: list[ShopDBSchema], mocker):
    crud_get_in_mock = mocker.patch.object(crud.shop, "get_in")
    crud_get_in_mock.return_value = shops
    crud_delete_mock = mocker.patch.object(crud.shop, "remove_many")
    crud_delete_mock.side_effect = lambda _db_conn, ids_versions: [
        idv[0] for idv in ids_versions
    ]
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    to_delete = [
        (custom_uuid(1), 1),  # lower version - no delete
        (custom_uuid(2), 3),  # higher version - should be deleted
        (custom_uuid(5), 3),  # nonexistent ID - ignore
    ]

    deleted_ids = await shop_service.remove_many(db_conn_mock, redis_mock, to_delete)
    assert deleted_ids == [custom_uuid(2)]
    crud_delete_mock.assert_called_once_with(db_conn_mock, [(custom_uuid(2), 3)])


@pytest.mark.anyio
@pytest.mark.parametrize(
    "column, old_value_in_db, new_value_in_msg",
    [
        ("country_code", CountryCode.CZ, CountryCode.BA),
        ("paying", True, False),
        ("certified", True, False),
        ("verified", True, False),
        ("enabled", True, False),
    ],
)
async def test_shop_should_be_updated_with_newer_object(
    column, old_value_in_db, new_value_in_msg, shop_service
):
    # obj in DB and incoming msg have all values equal except one column
    obj_in = await shop_factory(db_schema=True)
    msg_in = ShopCreateSchema(**obj_in.model_dump())
    setattr(obj_in, column, old_value_in_db)
    setattr(msg_in, column, new_value_in_msg)

    # check the object in DB should be updated with the incoming msg
    assert shop_service.should_be_updated(obj_in, msg_in) is True

    # but if the version of incoming msg is lower than version in DB
    obj_in.version = 10
    msg_in.version = 9

    # the object in DB should not be updated with that incoming msg
    assert shop_service.should_be_updated(obj_in, msg_in) is False
