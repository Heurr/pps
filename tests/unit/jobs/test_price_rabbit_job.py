from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from freezegun import freeze_time
from pytest_mock import MockFixture

from app import crud
from app.config.settings import JobSettings
from app.constants import (
    PRICE_EVENT_QUEUE,
    Action,
    CountryCode,
    CurrencyCode,
    ProductPriceType,
)
from app.jobs.price_publish import PublishingPriceJob
from app.schemas.product_price import (
    ProductPriceDBSchema,
    ProductPricePricesRabbitSchema,
    ProductPriceRabbitSchema,
)
from app.utils import utc_now, utc_today
from tests.factories import product_price_factory
from tests.utils import custom_uuid


@pytest.fixture
def job_settings() -> JobSettings:
    return JobSettings()


@pytest.fixture
async def mock_price_to_rabbit_event_job(
    job_settings: JobSettings,
    mocker: MockFixture,
) -> PublishingPriceJob:
    client_mock = mocker.patch(
        "app.utils.product_price_entity_client.ProductPriceEntityClient", autospec=True
    )
    client_mock_instance = client_mock.return_value
    client_mock.return_value.__aenter__ = AsyncMock(return_value=client_mock_instance)

    job = PublishingPriceJob(
        PRICE_EVENT_QUEUE,
        AsyncMock(),
        AsyncMock(),
        job_settings,
    )
    get_db_mock = mocker.patch.object(job, "get_db_conn")
    get_db_mock.return_value.__aenter__ = AsyncMock()

    return job


@pytest.mark.anyio
@pytest.mark.parametrize(
    "redis_queue, result_list",
    [
        ([b"\x00" * 16], [UUID(bytes=b"\x00" * 16)]),
        (
            [b"\xAF" * 16, b"\x23" * 16],
            [UUID(bytes=b"\xAF" * 16), UUID(bytes=b"\x23" * 16)],
        ),
        ([], []),
    ],
)
async def test_price_to_rabbit_read(
    mock_price_to_rabbit_event_job, redis_queue, result_list
):
    mock_price_to_rabbit_event_job.redis.rpop.return_value = []

    result = await mock_price_to_rabbit_event_job.read()

    assert result == []


@pytest.mark.anyio
@freeze_time("2024-04-26 12:00:00")
async def test_process_sends_entities_to_rabbitmq(mock_price_to_rabbit_event_job, mocker):
    crud_mock = mocker.patch.object(crud.product_price, "get_by_product_id_and_day")
    mock_price_to_rabbit_event_job.rmq = AsyncMock()

    crud_mock.return_value = [
        await product_price_factory(
            db_schema=True,
            product_id=custom_uuid(2),
            price_type=ProductPriceType.ALL_OFFERS,
        ),
        await product_price_factory(
            db_schema=True,
            product_id=custom_uuid(2),
            price_type=ProductPriceType.MARKETPLACE,
        ),
        await product_price_factory(
            db_schema=True,
            product_id=custom_uuid(0),
            price_type=ProductPriceType.ALL_OFFERS,
        ),
    ]
    await mock_price_to_rabbit_event_job.process([custom_uuid(2), custom_uuid(0)])
    assert mock_price_to_rabbit_event_job.rmq.send_entity.await_args.args[0][
        0
    ].product_id == custom_uuid(2)
    assert mock_price_to_rabbit_event_job.rmq.send_entity.await_args.args[0][
        1
    ].product_id == custom_uuid(0)

    mock_price_to_rabbit_event_job.rmq.send_entity.assert_awaited_once()


@pytest.mark.anyio
@freeze_time("2024-04-26 12:00:00")
async def test_prepare_rabbit_msg(
    mock_price_to_rabbit_event_job,
):
    data = {
        ProductPriceType.ALL_OFFERS: ProductPriceDBSchema(
            day=utc_today(),
            product_id=custom_uuid(1),
            country_code=CountryCode.CZ,
            price_type=ProductPriceType.ALL_OFFERS,
            min_price=1.0,
            max_price=10.0,
            currency_code=CurrencyCode.CZK,
            updated_at=utc_now(),
        )
    }
    result = await mock_price_to_rabbit_event_job.prepare_rabbit_msg(data)

    assert result == ProductPriceRabbitSchema(
        product_id=custom_uuid(1),
        currency_code=CurrencyCode.CZK,
        country_code=CountryCode.CZ,
        prices=[
            ProductPricePricesRabbitSchema(
                min=1.0, max=10.0, price_drop=None, type=ProductPriceType.ALL_OFFERS
            )
        ],
        version=1714132800,
        action=Action.UPDATE,
    )
