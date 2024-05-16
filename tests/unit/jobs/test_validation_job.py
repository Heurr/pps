from unittest.mock import AsyncMock

import pytest

from app import crud
from app.config.settings import ValidationJobSettings
from app.constants import ProductPriceType
from app.crud.product_price import crud_product_price
from app.custom_types import MinMaxPrice, ProductPriceDeletePk
from app.jobs.validation import ValidationJob
from tests.utils import custom_uuid


@pytest.fixture
async def validation_job_mock(
    mocker,
) -> ValidationJob:
    job = ValidationJob(AsyncMock(), ValidationJobSettings())
    get_db_mock = mocker.patch.object(job, "get_db_conn")
    get_db_mock.return_value.__aenter__ = AsyncMock()
    get_db_mock.return_value.__aexit__ = AsyncMock()

    return job


@pytest.mark.anyio
async def test_get_sample_from_product_price(validation_job_mock, mocker):
    mocker.patch.object(crud_product_price, "get_sample_for_day", return_value=[])
    job = validation_job_mock
    sample = await job.get_sample_from_product_price()

    assert crud_product_price.get_sample_for_day.call_count == 1
    assert sample == []


@pytest.mark.anyio
async def test_get_sample_from_offers(validation_job_mock, mocker):
    mocker.patch.object(crud.offer, "get_price_for_product", return_value=10)
    job = validation_job_mock
    product_keys = [ProductPriceDeletePk(custom_uuid(1), ProductPriceType.ALL_OFFERS)]
    sample = await job.get_sample_from_offers(product_keys)

    assert crud.offer.get_price_for_product.call_count == 2
    assert sample == [
        MinMaxPrice(
            product_id=custom_uuid(1),
            price_type=ProductPriceType.ALL_OFFERS,
            min_price=10,
            max_price=10,
        )
    ]


@pytest.mark.parametrize(
    "product_price_sample, offers_sample, diff_count",
    [
        (
            [
                MinMaxPrice(
                    product_id=custom_uuid(1),
                    price_type=ProductPriceType.ALL_OFFERS,
                    min_price=10,
                    max_price=10,
                )
            ],
            [
                MinMaxPrice(
                    product_id=custom_uuid(1),
                    price_type=ProductPriceType.ALL_OFFERS,
                    min_price=10,
                    max_price=10,
                )
            ],
            0,
        ),  # No difference
        (
            [
                MinMaxPrice(
                    product_id=custom_uuid(1),
                    price_type=ProductPriceType.ALL_OFFERS,
                    min_price=10,
                    max_price=15,
                )
            ],
            [
                MinMaxPrice(
                    product_id=custom_uuid(1),
                    price_type=ProductPriceType.ALL_OFFERS,
                    min_price=10,
                    max_price=10,
                )
            ],
            1,
        ),  # max price is different -> 1 difference
        (
            [
                MinMaxPrice(
                    product_id=custom_uuid(1),
                    price_type=ProductPriceType.ALL_OFFERS,
                    min_price=10,
                    max_price=10,
                )
            ],
            [
                MinMaxPrice(
                    product_id=custom_uuid(1),
                    price_type=ProductPriceType.ALL_OFFERS,
                    min_price=15,
                    max_price=10,
                )
            ],
            1,
        ),  # min_price is different -> 1 difference
        (
            [
                MinMaxPrice(
                    product_id=custom_uuid(1),
                    price_type=ProductPriceType.ALL_OFFERS,
                    min_price=10,
                    max_price=10,
                )
            ],
            [
                MinMaxPrice(
                    product_id=custom_uuid(1),
                    price_type=ProductPriceType.ALL_OFFERS,
                    min_price=5,
                    max_price=15,
                )
            ],
            1,
        ),  # 1 difference
    ],
)
def test_find_diff(validation_job_mock, product_price_sample, offers_sample, diff_count):
    job = validation_job_mock
    diff = job.find_diff(product_price_sample, offers_sample)

    assert len(diff) == diff_count
