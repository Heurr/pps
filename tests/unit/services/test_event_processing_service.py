import datetime
from typing import Any

import pytest
from _pytest.mark import param
from pytest_mock import MockFixture

from app import crud
from app.constants import Aggregate, CountryCode, CurrencyCode, ProductPriceType
from app.schemas.price_event import PriceChange, PriceEvent, PriceEventAction
from app.schemas.product_price import ProductPriceCreateSchema, ProductPriceDBSchema
from app.services.event_processing import EventProcessingService, ProcessResultType
from app.utils import utc_today
from tests.factories import price_event_factory, product_price_factory
from tests.utils import custom_uuid


@pytest.fixture
def event_processing_service() -> EventProcessingService:
    return EventProcessingService()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "event,price",
    [
        param(price_event_factory(), None, id="no_price"),
        param(
            price_event_factory(price=10),
            product_price_factory(db_schema=True, min_price=5, max_price=1),
            id="no_change",
        ),
    ],
)
async def test_process_delete_event_not_changed(
    mocker: MockFixture,
    event_processing_service: EventProcessingService,
    event: PriceEvent,
    price: ProductPriceDBSchema,
):
    """
    Price does not change if the price is not min or max
    """
    db_conn_mock = mocker.AsyncMock()
    if price:
        price = await price

    res = await event_processing_service._process_delete_event(db_conn_mock, event, price)

    assert res[0] == ProcessResultType.NOT_CHANGED
    assert not res[1]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "event_price, aggregate, mock_return, res_type, res_data",
    [
        param(
            1,
            Aggregate.MIN,
            0.5,
            ProcessResultType.UPDATED,
            PriceChange(min_price=0.5, max_price=5),
            id="min_price_change",
        ),
        param(
            5,
            Aggregate.MAX,
            10.0,
            ProcessResultType.UPDATED,
            PriceChange(min_price=1, max_price=10),
            id="max_price_change",
        ),
        param(
            5,
            Aggregate.MAX,
            None,
            ProcessResultType.DELETED,
            (custom_uuid(1), ProductPriceType.ALL_OFFERS),
            id="offers deleted with max price",
        ),
        param(
            1,
            Aggregate.MIN,
            None,
            ProcessResultType.DELETED,
            (custom_uuid(1), ProductPriceType.ALL_OFFERS),
            id="offers deleted with min price",
        ),
    ],
)
async def test_process_delete_event(
    mocker: MockFixture,
    event_processing_service: EventProcessingService,
    event_price: float,
    aggregate: Aggregate,
    mock_return: float | None,
    res_data: Any,
    res_type: ProcessResultType,
):
    db_conn_mock = mocker.AsyncMock()
    crud_mock = mocker.patch.object(crud.offer, "get_price_for_product")
    crud_mock.return_value = mock_return
    price = await product_price_factory(
        db_schema=True,
        min_price=1,
        max_price=5,
        product_id=custom_uuid(1),
        price_type=ProductPriceType.ALL_OFFERS,
    )
    event = price_event_factory(
        old_price=event_price,
        price=None,
        product_id=price.product_id,
        price_type=price.price_type,
    )

    res = await event_processing_service._process_delete_event(db_conn_mock, event, price)

    crud_mock.assert_called_once()
    call_args = crud_mock.call_args_list[0][0]
    assert call_args == (db_conn_mock, event.product_id, price.price_type, aggregate)
    assert res == (res_type, res_data)


@pytest.mark.anyio
async def test_process_upsert_event_no_result(
    mocker: MockFixture,
    event_processing_service: EventProcessingService,
):
    """
    Price does not change if the price is not min or max
    """
    db_conn_mock = mocker.AsyncMock()
    price = await product_price_factory(db_schema=True, min_price=1, max_price=5)
    event = price_event_factory(price=2, old_price=1.1)

    res = await event_processing_service._process_upsert_event(db_conn_mock, event, price)

    assert res == (ProcessResultType.NOT_CHANGED, None)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "event_price, res_type, res_data",
    [
        param(
            0.5,
            ProcessResultType.UPDATED,
            PriceChange(min_price=0.5, max_price=5),
            id="min_price_changed",
        ),
        param(
            6,
            ProcessResultType.UPDATED,
            PriceChange(min_price=1, max_price=6),
            id="max_price_changed",
        ),
    ],
)
async def test_process_upsert_event_no_thresholds(
    mocker: MockFixture,
    event_processing_service: EventProcessingService,
    event_price: float,
    res_data: Any,
    res_type: ProcessResultType,
):
    """
    Price changes if new price is a new min or max
    """
    db_conn_mock = mocker.AsyncMock()
    price = await product_price_factory(db_schema=True, min_price=1, max_price=5)
    event = price_event_factory(price=event_price, old_price=2)

    res = await event_processing_service._process_upsert_event(db_conn_mock, event, price)

    assert res == (res_type, res_data)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "event_price, old_event_price, aggregate, mock_return, res_type, res_data",
    [
        param(
            0.5,
            5,
            Aggregate.MAX,
            7,
            ProcessResultType.UPDATED,
            PriceChange(min_price=0.5, max_price=7),
            id="min_price_and_max_threshold_changed",
        ),
        param(
            6,
            1,
            Aggregate.MIN,
            0.6,
            ProcessResultType.UPDATED,
            PriceChange(min_price=0.6, max_price=6),
            id="max_price_and_min_threshold_changed",
        ),
        param(
            2,
            1,
            Aggregate.MIN,
            0.6,
            ProcessResultType.UPDATED,
            PriceChange(min_price=0.6, max_price=5),
            id="min_threshold_changed",
        ),
        param(
            2,
            5,
            Aggregate.MAX,
            6,
            ProcessResultType.UPDATED,
            PriceChange(min_price=1, max_price=6),
            id="max_threshold_changed",
        ),
    ],
)
async def test_process_upsert_event_with_thresholds(  # noqa
    mocker: MockFixture,
    event_processing_service: EventProcessingService,
    event_price: float,
    old_event_price: float,
    aggregate: Aggregate,
    mock_return: float | None,
    res_data: Any,
    res_type: ProcessResultType,
):
    """
    Test if the price changes if the old price is a threshold and the new price
    is a new min or max
    """
    db_conn_mock = mocker.AsyncMock()
    crud_mock = mocker.patch.object(crud.offer, "get_price_for_product")
    crud_mock.return_value = mock_return

    price = await product_price_factory(db_schema=True, min_price=1, max_price=5)
    event = price_event_factory(price=event_price, old_price=old_event_price)

    res = await event_processing_service._process_upsert_event(db_conn_mock, event, price)

    crud_mock.assert_called_once()
    call_args = crud_mock.call_args_list[0][0]
    assert call_args == (db_conn_mock, event.product_id, event.type, aggregate)
    assert res == (res_type, res_data)


@pytest.mark.anyio
async def test_process_upsert_event_create_new(
    mocker: MockFixture, event_processing_service: EventProcessingService
):
    """
    Price changes if new price is new
    """
    db_conn_mock = mocker.AsyncMock()
    price = None
    event = price_event_factory(price=100)

    res = await event_processing_service._process_upsert_event(db_conn_mock, event, price)

    assert res[0] == ProcessResultType.UPDATED
    assert res[1] == PriceChange(min_price=100, max_price=100)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "event, process_result_type, process_result_data, mock_name, result_data",
    [
        param(  # Not changed from upsert action
            price_event_factory(action=PriceEventAction.UPSERT),
            ProcessResultType.NOT_CHANGED,
            None,
            "_process_upsert_event",
            None,
            id="not_changed_upsert",
        ),
        param(  # Not changed from delete action
            price_event_factory(action=PriceEventAction.DELETE),
            ProcessResultType.NOT_CHANGED,
            None,
            "_process_delete_event",
            None,
            id="not_changed_delete",
        ),
        param(  # Deleted result from delete action
            price_event_factory(action=PriceEventAction.DELETE),
            ProcessResultType.DELETED,
            (custom_uuid(1), ProductPriceType.ALL_OFFERS),
            "_process_delete_event",
            (custom_uuid(1), ProductPriceType.ALL_OFFERS),
            id="deleted_delete",
        ),
        param(  # Upsert from upsert action
            price_event_factory(
                action=PriceEventAction.UPSERT,
                product_id=custom_uuid(1),
                price=100,
                price_type=ProductPriceType.ALL_OFFERS,
                country_code=CountryCode.SI,
                currency_code=CurrencyCode.EUR,
                created_at=datetime.datetime(2021, 1, 1, 0, 0, 0),
            ),
            ProcessResultType.UPDATED,
            PriceChange(min_price=100, max_price=100),
            "_process_upsert_event",
            ProductPriceCreateSchema(
                day=utc_today(),
                product_id=custom_uuid(1),
                country_code=CountryCode.SI,
                price_type=ProductPriceType.ALL_OFFERS,
                min_price=100,
                max_price=100,
                currency_code=CurrencyCode.EUR,
                updated_at=datetime.datetime(2021, 1, 1, 0, 0, 0),
            ),
            id="updated_upsert",
        ),
        param(  # Updated from delete action
            price_event_factory(
                action=PriceEventAction.DELETE,
                product_id=custom_uuid(1),
                price=100,
                price_type=ProductPriceType.ALL_OFFERS,
                country_code=CountryCode.SI,
                currency_code=CurrencyCode.EUR,
                created_at=datetime.datetime(2021, 1, 1, 0, 0, 0),
            ),
            ProcessResultType.UPDATED,
            PriceChange(min_price=100, max_price=100),
            "_process_delete_event",
            ProductPriceCreateSchema(
                day=utc_today(),
                product_id=custom_uuid(1),
                country_code=CountryCode.SI,
                price_type=ProductPriceType.ALL_OFFERS,
                min_price=100,
                max_price=100,
                currency_code=CurrencyCode.EUR,
                updated_at=datetime.datetime(2021, 1, 1, 0, 0, 0),
            ),
            id="updated_delete",
        ),
    ],
)
async def test_process_event(
    mocker: MockFixture,
    event_processing_service: EventProcessingService,
    event: PriceEvent,
    process_result_type: ProcessResultType,
    process_result_data,
    mock_name: str,
    result_data,
):
    db_conn_mock = mocker.AsyncMock()
    process_mock = mocker.patch.object(event_processing_service, mock_name)
    process_mock.return_value = (process_result_type, process_result_data)

    price = await product_price_factory(db_schema=True)

    res = await event_processing_service._process_event(db_conn_mock, event, price)
    process_mock.assert_called_once()
    assert process_mock.call_args_list[0][0] == (db_conn_mock, event, price)

    assert res[0] == process_result_type
    assert res[1] == result_data


@pytest.mark.anyio
async def test_process_events_bulk(
    mocker: MockFixture, event_processing_service: EventProcessingService
):
    """
    Create 30 events, then mock the process event function to return
    10 times NOT_CHANGED, 10 times DELETED and 10 times UPDATED.

    Check if the function calls the process event function with the correct arguments
    Check if the NOT_CHANGED events are not returned
    CHeck if the DELETED and UPDATED events are returned
    """
    # Mock
    db_conn_mock = mocker.AsyncMock()
    process_event_mock = mocker.patch.object(event_processing_service, "_process_event")
    events = [
        price_event_factory(
            product_id=custom_uuid(i), price_type=ProductPriceType.ALL_OFFERS
        )
        for i in range(30)
    ]
    product_prices = [
        await product_price_factory(
            product_id=custom_uuid(i), price_type=ProductPriceType.ALL_OFFERS
        )
        for i in range(30)
    ]
    product_prices = {(pp.product_id, pp.price_type): pp for pp in product_prices}
    process_event_mock.side_effect = (
        10 * [(ProcessResultType.NOT_CHANGED, None)]
        + [
            (ProcessResultType.DELETED, (custom_uuid(i), ProductPriceType.ALL_OFFERS))
            for i in range(10)
        ]
        + [
            (
                ProcessResultType.UPDATED,
                await product_price_factory(product_id=custom_uuid(i)),
            )
            for i in range(10)
        ]
    )

    # Call
    res = await event_processing_service.process_events_bulk(
        db_conn_mock,
        events,
        product_prices,
    )

    # Check
    assert process_event_mock.call_count == 30
    for i, call in enumerate(process_event_mock.call_args_list):
        assert call[0] == (db_conn_mock, events[i], list(product_prices.values())[i])

    assert len(res[0]) == 10
    assert len(res[1]) == 10
