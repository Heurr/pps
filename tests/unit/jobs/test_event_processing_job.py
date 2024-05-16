from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockFixture

from app import crud
from app.config.settings import JobSettings
from app.constants import ProductPriceType
from app.custom_types import ProductPricePk
from app.jobs.price_event import PriceEventJob
from app.utils import utc_today
from tests.factories import price_event_factory, product_price_factory
from tests.utils import custom_uuid


@pytest.fixture
async def job_settings() -> JobSettings:
    return JobSettings()


@pytest.fixture
async def event_processing_job(
    job_settings: JobSettings,
    mocker: MockFixture,
) -> PriceEventJob:
    job = PriceEventJob(
        "event-processing-job",
        AsyncMock(),
        AsyncMock(),
        job_settings,
    )
    get_db_mock = mocker.patch.object(job, "get_db_conn")
    get_db_mock.return_value.__aenter__ = AsyncMock()

    return job


@pytest.mark.anyio
async def test_get_product_prices_by_events_no_flag(
    event_processing_job: PriceEventJob, mocker: MockFixture
):
    """
    Only todays product prices should be retrieved if flag is set to false
    """
    get_flag_mock = mocker.patch.object(event_processing_job, "get_process_safe_flag")
    get_flag_mock.return_value = False

    crud_mock = mocker.patch.object(crud.product_price, "get_in")
    events = [
        price_event_factory(
            product_id=custom_uuid(1), price_type=ProductPriceType.ALL_OFFERS
        )
    ]
    product_prices = [
        await product_price_factory(
            product_id=events[0].product_id,
            price_type=events[0].type,
            updated_at=events[0].created_at,
        )
    ]
    crud_mock.return_value = product_prices

    res = await event_processing_job.get_product_prices_by_events(AsyncMock(), events)
    get_flag_mock.assert_called_once()

    crud_mock.assert_called_once()
    assert crud_mock.call_args_list[0][0][1] == [
        ProductPricePk(utc_today(), events[0].product_id, events[0].type)
    ]
    assert len(res) == 1
    assert res == {(events[0].product_id, events[0].type): product_prices[0]}


@pytest.mark.anyio
async def test_get_product_prices_by_events_with_flag(
    event_processing_job: PriceEventJob, mocker: MockFixture
):
    """
    Test if missing product prices are retrieved from the previous day if
    the process safe flag is set
    """
    get_flag_mock = mocker.patch.object(event_processing_job, "get_process_safe_flag")
    get_flag_mock.return_value = True

    crud_mock = mocker.patch.object(crud.product_price, "get_in")

    events = [
        price_event_factory(
            product_id=custom_uuid(i), price_type=ProductPriceType.ALL_OFFERS
        )
        for i in range(2)
    ]
    product_prices = [
        await product_price_factory(
            product_id=events[i].product_id,
            price_type=events[i].type,
            updated_at=events[i].created_at,
        )
        for i in range(2)
    ]

    # Return pp 0 if day is today, pp 1 if day is yesterday
    crud_mock.side_effect = lambda _, pks: (
        [product_prices[0]]
        if pks[0].day == utc_today() - timedelta(days=1)
        else [product_prices[1]]
    )

    res = await event_processing_job.get_product_prices_by_events(AsyncMock(), events)

    get_flag_mock.assert_called_once()
    assert crud_mock.call_count == 2
    assert crud_mock.call_args_list[0][0][1] == [
        ProductPricePk(utc_today(), events[i].product_id, events[i].type)
        for i in range(2)
    ]
    assert crud_mock.call_args_list[1][0][1] == [
        ProductPricePk(
            utc_today() - timedelta(days=1), events[0].product_id, events[0].type
        )
    ]

    assert len(res) == 2
    assert res == {
        (events[i].product_id, events[i].type): product_prices[i] for i in range(2)
    }


@pytest.mark.anyio
@pytest.mark.parametrize("get_return, flag", [(b"0", False), (b"1", True), (None, False)])
async def test_get_process_safe_flag(
    event_processing_job: PriceEventJob, mocker: MockFixture, get_return, flag
):
    redis_mock = mocker.patch.object(event_processing_job.redis, "get")
    redis_mock.return_value = get_return

    res = await event_processing_job.get_process_safe_flag()

    redis_mock.assert_called_once()
    assert res is flag


@pytest.mark.anyio
async def test_push_to_publisher_queue(
    event_processing_job: PriceEventJob, mocker: MockFixture
):
    redis_mock = mocker.patch.object(event_processing_job.redis, "sadd")

    await event_processing_job.push_to_publisher_queue({custom_uuid(1), custom_uuid(2)})

    redis_mock.assert_called_once()
    assert redis_mock.call_args[0][0] == "price-publish"
    assert redis_mock.call_args[0][1] == custom_uuid(1).bytes
    assert redis_mock.call_args[0][2] == custom_uuid(2).bytes


@pytest.mark.anyio
async def test_push_to_publisher_queue_empty_set(
    event_processing_job: PriceEventJob, mocker: MockFixture
):
    redis_mock = mocker.patch.object(event_processing_job.redis, "sadd")

    await event_processing_job.push_to_publisher_queue(set())

    redis_mock.assert_not_called()
