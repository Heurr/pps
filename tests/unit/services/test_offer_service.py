import pytest
from freezegun import freeze_time

from app import crud
from app.constants import ProductPriceType
from app.schemas.offer import OfferCreateSchema, OfferDBSchema
from app.schemas.price_event import PriceEventAction
from app.services import OfferService
from tests.factories import offer_factory
from tests.utils import custom_uuid


@pytest.fixture
async def offers() -> list[OfferDBSchema]:
    return [
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(1),
            product_id=custom_uuid(1),
            price=1,
            version=2,
            certified_shop=True,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(2),
            product_id=custom_uuid(2),
            price=1,
            version=2,
            in_stock=True,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(3),
            product_id=custom_uuid(3),
            price=1,
            version=2,
            in_stock=True,
            buyable=True,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(4),
            product_id=custom_uuid(4),
            price=1,
            version=2,
            in_stock=True,
            certified_shop=True,
        ),
        await offer_factory(
            db_schema=True,
            offer_id=custom_uuid(5),
            product_id=custom_uuid(5),
            price=1,
            version=2,
        ),
    ]


@pytest.mark.anyio
async def test_upsert_many(
    offer_service: OfferService, offers: list[OfferDBSchema], mocker
):
    crud_get_in_mock = mocker.patch.object(crud.offer, "get_in")
    crud_get_in_mock.return_value = offers
    crud_upsert_mock = mocker.patch.object(crud.offer, "upsert_many")
    crud_upsert_mock.side_effect = lambda _db_conn, entities: [e.id for e in entities]
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    new_offers_msgs = [
        # higher version, fields changed - should be updated
        await offer_factory(offer_id=custom_uuid(1), price=2, version=3),
        # old version - no update
        await offer_factory(offer_id=custom_uuid(2), price=2, version=1),
        # higher version, same fields - no update
        OfferCreateSchema(**offers[2].model_dump(exclude={"version"}), version=3),
        # new offer ID - should be inserted
        await offer_factory(offer_id=custom_uuid(5)),
    ]

    updated_ids = await offer_service.upsert_many(
        db_conn_mock, redis_mock, new_offers_msgs
    )
    assert set(updated_ids) == {custom_uuid(1), custom_uuid(5)}
    crud_upsert_mock.assert_called_once_with(
        db_conn_mock, [new_offers_msgs[0], new_offers_msgs[3]]
    )


@pytest.mark.anyio
@freeze_time("2024-04-26")
async def test_generate_price_event_upsert(
    offer_service: OfferService, offers: list[OfferDBSchema], mocker
):
    crud_get_in_mock = mocker.patch.object(crud.offer, "get_in")
    crud_get_in_mock.return_value = offers
    mocker.patch.object(crud.offer, "upsert_many")
    send_price_events_mock = mocker.patch.object(offer_service, "send_price_events")
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    new_offers_msgs = [
        await offer_factory(
            offer_id=custom_uuid(1), product_id=custom_uuid(1), price=2, version=3
        ),
        await offer_factory(
            offer_id=custom_uuid(2), product_id=custom_uuid(2), price=2, version=3
        ),
        await offer_factory(
            offer_id=custom_uuid(3), product_id=custom_uuid(3), price=2, version=3
        ),
        await offer_factory(
            offer_id=custom_uuid(4), product_id=custom_uuid(4), price=2, version=3
        ),
        await offer_factory(
            offer_id=custom_uuid(5), product_id=custom_uuid(5), price=2, version=1
        ),
        await offer_factory(
            offer_id=custom_uuid(99), product_id=custom_uuid(6), price=2, version=3
        ),
    ]
    await offer_service.upsert_many(db_conn_mock, redis_mock, new_offers_msgs)
    events = send_price_events_mock.call_args.args[1]
    assert len(events) == 10

    # first message - only ALL_OFFERS, the IN_STOCK_CERTIFIED is not sent because the offer is
    # not in stock
    assert events[0].product_id == custom_uuid(1)
    assert events[0].type == ProductPriceType.ALL_OFFERS
    assert events[0].action == PriceEventAction.UPSERT

    # second message - ALL_OFFERS and IN_STOCK
    assert events[1].product_id == custom_uuid(2)
    assert events[1].type == ProductPriceType.ALL_OFFERS
    assert events[1].action == PriceEventAction.UPSERT

    assert events[2].product_id == custom_uuid(2)
    assert events[2].type == ProductPriceType.IN_STOCK
    assert events[2].action == PriceEventAction.UPSERT

    # third message - ALL_OFFERS, IN_STOCK and MARKETPLACE
    assert events[3].product_id == custom_uuid(3)
    assert events[3].type == ProductPriceType.ALL_OFFERS
    assert events[3].action == PriceEventAction.UPSERT

    assert events[4].product_id == custom_uuid(3)
    assert events[4].type == ProductPriceType.IN_STOCK
    assert events[4].action == PriceEventAction.UPSERT

    assert events[5].product_id == custom_uuid(3)
    assert events[5].type == ProductPriceType.MARKETPLACE
    assert events[5].action == PriceEventAction.UPSERT

    # fourth message - ALL_OFFERS, IN_STOCK and IN_STOCK_CERTIFIED
    assert events[6].product_id == custom_uuid(4)
    assert events[6].type == ProductPriceType.ALL_OFFERS
    assert events[6].action == PriceEventAction.UPSERT

    assert events[7].product_id == custom_uuid(4)
    assert events[7].type == ProductPriceType.IN_STOCK
    assert events[7].action == PriceEventAction.UPSERT

    assert events[8].product_id == custom_uuid(4)
    assert events[8].type == ProductPriceType.IN_STOCK_CERTIFIED
    assert events[8].action == PriceEventAction.UPSERT

    # fifth message - no event generated because of old version
    # sixth message - only ALL_OFFERS, because new offers have no availability and
    # buyability yet
    assert events[9].product_id == custom_uuid(6)
    assert events[9].type == ProductPriceType.ALL_OFFERS
    assert events[9].action == PriceEventAction.UPSERT


@pytest.mark.anyio
@freeze_time("2024-04-26")
async def test_generate_price_event_delete(
    offer_service: OfferService, offers: list[OfferDBSchema], mocker
):
    offer_ids = {o.id for o in offers}
    crud_get_in_mock = mocker.patch.object(crud.offer, "get_in")
    crud_get_in_mock.return_value = offers
    crud_delete_mock = mocker.patch.object(crud.offer, "remove_many")
    crud_delete_mock.side_effect = lambda _db_conn, ids_versions: [
        idv[0] for idv in ids_versions if idv[0] in offer_ids and idv[1] >= 2
    ]
    send_price_events_mock = mocker.patch.object(offer_service, "send_price_events")
    db_conn_mock = mocker.AsyncMock()
    redis_mock = mocker.AsyncMock()

    to_delete = [
        (custom_uuid(1), 2),
        (custom_uuid(2), 2),
        (custom_uuid(3), 2),
        (custom_uuid(4), 2),
        (custom_uuid(5), 1),
        (custom_uuid(99), 2),
    ]
    await offer_service.remove_many(db_conn_mock, redis_mock, to_delete)
    events = send_price_events_mock.call_args.args[1]
    assert len(events) == 9

    # first message - only ALL_OFFERS, the IN_STOCK_CERTIFIED is not sent because the offer is
    # not in stock
    assert events[0].product_id == custom_uuid(1)
    assert events[0].type == ProductPriceType.ALL_OFFERS
    assert events[0].action == PriceEventAction.DELETE

    # second message - ALL_OFFERS and IN_STOCK
    assert events[1].product_id == custom_uuid(2)
    assert events[1].type == ProductPriceType.ALL_OFFERS
    assert events[1].action == PriceEventAction.DELETE

    assert events[2].product_id == custom_uuid(2)
    assert events[2].type == ProductPriceType.IN_STOCK
    assert events[2].action == PriceEventAction.DELETE

    # third message - ALL_OFFERS, IN_STOCK and MARKETPLACE
    assert events[3].product_id == custom_uuid(3)
    assert events[3].type == ProductPriceType.ALL_OFFERS
    assert events[3].action == PriceEventAction.DELETE

    assert events[4].product_id == custom_uuid(3)
    assert events[4].type == ProductPriceType.IN_STOCK
    assert events[4].action == PriceEventAction.DELETE

    assert events[5].product_id == custom_uuid(3)
    assert events[5].type == ProductPriceType.MARKETPLACE
    assert events[5].action == PriceEventAction.DELETE

    # fourth message - ALL_OFFERS, IN_STOCK and IN_STOCK_CERTIFIED
    assert events[6].product_id == custom_uuid(4)
    assert events[6].type == ProductPriceType.ALL_OFFERS
    assert events[6].action == PriceEventAction.DELETE

    assert events[7].product_id == custom_uuid(4)
    assert events[7].type == ProductPriceType.IN_STOCK
    assert events[7].action == PriceEventAction.DELETE

    assert events[8].product_id == custom_uuid(4)
    assert events[8].type == ProductPriceType.IN_STOCK_CERTIFIED
    assert events[8].action == PriceEventAction.DELETE

    # fifth message - no event generated because of old version
    # sixth message - no event generated because of nonexistent offer
