from datetime import timedelta
from unittest.mock import AsyncMock

import freezegun
import pytest
from pytest_mock import MockFixture

from app import crud
from app.config.settings import MaintenanceJobSettings
from app.jobs.maintenance import MaintenanceJob
from app.utils import utc_today


@pytest.fixture
def missing_job_settings() -> MaintenanceJobSettings:
    return MaintenanceJobSettings()


@pytest.fixture
async def maintenance_job(
    missing_job_settings: MaintenanceJobSettings, mocker: MockFixture
) -> MaintenanceJob:
    job = MaintenanceJob(
        AsyncMock(),
        missing_job_settings,
    )
    get_db_mock = mocker.patch.object(job, "get_db_conn")
    get_db_mock.return_value.__aenter__ = AsyncMock()

    return job


@pytest.mark.anyio
async def test_create_new_product_prices_partition(
    maintenance_job: MaintenanceJob, mocker: MockFixture, caplog
):
    """
    Create tables 3 days ahead, that means 4 tables wille exist
    - today's table
    - create tomorrow's table (20240404) -- this one is already created, skit it
    - create 2 days ahead (20240406)
    - create 3 days ahead (20240407)
    """
    maintenance_job.partitions_ahead = 3

    create_partition_mock = mocker.patch(
        "app.jobs.maintenance.async_create_product_prices_part_tables_for_day"
    )
    with freezegun.freeze_time("2024-04-04"):
        table_names_mock = mocker.patch("app.jobs.maintenance.get_table_names")
        table_names_mock.return_value = [
            f"product_prices_{(utc_today() + timedelta(days=1)).strftime('%Y%m%d')}"
        ]

        await maintenance_job.create_new_product_prices_partition(AsyncMock())

        assert create_partition_mock.call_count == 2
        assert create_partition_mock.call_args_list[0][0][1] == utc_today() + timedelta(
            days=2
        )
        assert create_partition_mock.call_args_list[1][0][1] == utc_today() + timedelta(
            days=3
        )

    assert caplog.messages[-2] == "Creating table product_prices_20240407"
    assert caplog.messages[-3] == "Creating table product_prices_20240406"


@pytest.mark.anyio
async def test_delete_old_product_prices(
    maintenance_job: MaintenanceJob, mocker: MockFixture, caplog
):
    maintenance_job.history_interval = 3

    delete_after = utc_today() - timedelta(days=3)
    db_mock = AsyncMock()
    crud_mock = mocker.patch.object(crud.product_price, "remove_history")
    crud_mock.return_value = 4
    await maintenance_job.delete_old_product_prices(db_mock)

    crud_mock.assert_called_once_with(db_mock, delete_after)

    assert caplog.messages[-2] == f"Deleting product prices older than {delete_after}"
    assert caplog.messages[-1] == "Done deleting"


@pytest.mark.anyio
async def test_create_new_product_prices(
    maintenance_job: MaintenanceJob, mocker: MockFixture, caplog
):
    db_mock = AsyncMock()
    create_mock = mocker.patch.object(crud.product_price, "duplicate_day")
    await maintenance_job.create_new_product_prices(db_mock)

    create_mock.assert_called_once_with(db_mock, utc_today())
    assert caplog.messages[-2] == f"Duplicating {utc_today()} product prices to tomorrow"
