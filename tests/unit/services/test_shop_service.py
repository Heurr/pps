import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from app import crud
from app.constants import CountryCode, ProductPriceType
from app.schemas.offer import OfferDBSchema
from app.schemas.price_event import PriceEventAction
from app.schemas.shop import ShopCreateSchema, ShopDBSchema
from app.services import ShopService
from tests.factories import offer_factory, shop_factory
from tests.utils import custom_uuid


@pytest.fixture
async def shops() -> list[ShopDBSchema]:
    return [
        await shop_factory(
            db_schema=True,
            shop_id=custom_uuid(1),
            country_code=CountryCode.CZ,
            certified=False,
            version=2,
        ),
        await shop_factory(
            db_schema=True,
            shop_id=custom_uuid(2),
            country_code=CountryCode.CZ,
            certified=False,
            version=2,
        ),
        await shop_factory(
            db_schema=True,
            shop_id=custom_uuid(3),
            country_code=CountryCode.CZ,
            certified=True,
            version=2,
        ),
    ]


@pytest.fixture
async def offers(shops: list[ShopDBSchema]) -> list[OfferDBSchema]:
    return [
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(1),
            product_id=custom_uuid(1),
            price=10,
            shop_id=shops[0].id,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(2),
            product_id=custom_uuid(2),
            price=20,
            shop_id=shops[0].id,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(3),
            product_id=custom_uuid(3),
            price=30,
            shop_id=shops[1].id,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(4),
            product_id=custom_uuid(4),
            price=40,
            shop_id=shops[1].id,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(5),
            product_id=custom_uuid(5),
            price=50,
            shop_id=shops[2].id,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(6),
            product_id=custom_uuid(6),
            price=60,
            shop_id=shops[2].id,
        ),
    ]


@pytest.mark.anyio
async def test_upsert_many(shop_service: ShopService, shops: list[ShopDBSchema], mocker):
    crud_get_in_mock = mocker.patch.object(crud.shop, "get_in")
    crud_get_in_mock.return_value = shops
    crud_upsert_mock = mocker.patch.object(crud.shop, "upsert_many")
    crud_upsert_mock.side_effect = lambda _db_conn, entities: [e.id for e in entities]

    new_shop_msgs = [
        await shop_factory(
            shop_id=custom_uuid(1),
            country_code=CountryCode.CZ,
            certified=True,
            version=1,  # lower version - no update
        ),
        await shop_factory(
            shop_id=custom_uuid(2),
            country_code=CountryCode.CZ,
            certified=True,
            version=3,  # higher version, fields changed - should be updated
        ),
        await shop_factory(
            shop_id=custom_uuid(3),
            country_code=CountryCode.CZ,
            certified=True,
            version=3,  # higher version, but no fields changed - no update
        ),
        await shop_factory(
            shop_id=custom_uuid(5),
            country_code=CountryCode.CZ,
            certified=True,
            version=1,  # new shop ID - should be inserted
        ),
    ]

    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()
    updated_ids = await shop_service.upsert_many(db_conn_mock, redis_mock, new_shop_msgs)
    assert set(updated_ids) == {custom_uuid(2), custom_uuid(5)}
    crud_upsert_mock.assert_called_once_with(
        db_conn_mock, [new_shop_msgs[1], new_shop_msgs[3]]
    )


@pytest.mark.anyio
async def test_remove_many(shop_service: ShopService, shops: list[ShopDBSchema], mocker):
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


@pytest.mark.anyio
async def test_generate_price_event_upsert(
    db_conn: AsyncConnection,
    shop_service: ShopService,
    shops: list[ShopDBSchema],
    offers: list[OfferDBSchema],
    mocker,
):
    crud_get_in_mock = mocker.patch.object(crud.shop, "get_in")
    crud_get_in_mock.return_value = shops
    crud_get_offers_in_stock = mocker.patch.object(
        crud.shop, "get_offers_in_stock_for_shops"
    )
    crud_get_offers_in_stock.side_effect = lambda _db_conn, shop_ids: [
        o for o in offers if o.shop_id in shop_ids
    ]
    mocker.patch.object(crud.shop, "upsert_many")
    send_price_events_mock = mocker.patch.object(shop_service, "send_price_events")
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    new_shops_msgs = [
        await shop_factory(shop_id=custom_uuid(1), certified=True, version=3),
        await shop_factory(
            shop_id=custom_uuid(2),
            certified=False,
            version=3,
        ),
        await shop_factory(
            shop_id=custom_uuid(3),
            certified=False,
            version=3,
        ),
        await shop_factory(shop_id=custom_uuid(99), certified=True, version=3),
    ]
    await shop_service.upsert_many(db_conn_mock, redis_mock, new_shops_msgs)
    events = send_price_events_mock.call_args.args[1]
    assert len(events) == 4

    # first message - certified shop changed to True
    # generate UPSERT/IN_STOCK_CERTIFIED for both offers of the first shop
    assert events[0].product_id == custom_uuid(1)
    assert events[0].type == ProductPriceType.IN_STOCK_CERTIFIED
    assert events[0].action == PriceEventAction.UPSERT
    assert events[0].price == 10.0
    assert events[0].old_price is None

    assert events[1].product_id == custom_uuid(2)
    assert events[1].type == ProductPriceType.IN_STOCK_CERTIFIED
    assert events[1].action == PriceEventAction.UPSERT
    assert events[1].price == 20.0
    assert events[1].old_price is None

    # second message - no events generated because the certified flag is not changed

    # third message - certified shop changed to False
    # generate DELETE/IN_STOCK_CERTIFIED for both offers of the third shop
    assert events[2].product_id == custom_uuid(5)
    assert events[2].type == ProductPriceType.IN_STOCK_CERTIFIED
    assert events[2].action == PriceEventAction.DELETE
    assert events[2].price == 50.0
    assert events[2].old_price is None

    assert events[3].product_id == custom_uuid(6)
    assert events[3].type == ProductPriceType.IN_STOCK_CERTIFIED
    assert events[3].action == PriceEventAction.DELETE
    assert events[3].price == 60.0
    assert events[3].old_price is None


@pytest.mark.anyio
async def test_generate_price_event_delete(
    db_conn: AsyncConnection,
    shop_service: ShopService,
    shops: list[ShopDBSchema],
    offers: list[OfferDBSchema],
    mocker,
):
    crud_get_in_mock = mocker.patch.object(crud.shop, "get_in")
    crud_get_in_mock.return_value = shops
    crud_get_offers_in_stock = mocker.patch.object(
        crud.shop, "get_offers_in_stock_for_shops"
    )
    crud_get_offers_in_stock.side_effect = lambda _db_conn, shop_ids: [
        o for o in offers if o.shop_id in shop_ids
    ]
    crud_delete_mock = mocker.patch.object(crud.shop, "remove_many")
    crud_delete_mock.side_effect = lambda _db_conn, ids_versions: [
        idv[0] for idv in ids_versions
    ]
    send_price_events_mock = mocker.patch.object(shop_service, "send_price_events")
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    to_delete = [(custom_uuid(2), 3), (custom_uuid(3), 3)]
    await shop_service.remove_many(db_conn_mock, redis_mock, to_delete)
    events = send_price_events_mock.call_args.args[1]
    assert len(events) == 2

    # first message - deleted shop was not certified, do not generate anything

    # second message - deleted shop was certified
    # generate DELETE/IN_STOCK_CERTIFIED for both offers of the third shop
    assert events[0].product_id == custom_uuid(5)
    assert events[0].type == ProductPriceType.IN_STOCK_CERTIFIED
    assert events[0].action == PriceEventAction.DELETE
    assert events[0].price == 50.0
    assert events[0].old_price is None

    assert events[1].product_id == custom_uuid(6)
    assert events[1].type == ProductPriceType.IN_STOCK_CERTIFIED
    assert events[1].action == PriceEventAction.DELETE
    assert events[1].price == 60.0
    assert events[1].old_price is None
