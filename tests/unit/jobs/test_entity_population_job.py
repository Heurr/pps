from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from freezegun import freeze_time
from pytest_mock import MockFixture

from app.config.settings import EntityPopulationJobSettings, RepublishSettings
from app.constants import Entity
from app.custom_types import OfferPk
from app.jobs.entity_population import EntityPopulationJob
from app.schemas.offer import PopulationOfferSchema
from app.utils import utc_now
from tests.utils import custom_uuid


@pytest.fixture
async def entity_population_job_mock(
    missing_job_settings: EntityPopulationJobSettings,
    rmq_settings: RepublishSettings,
    mocker,
) -> EntityPopulationJob:
    job = EntityPopulationJob(
        AsyncMock(),
        [Entity.BUYABLE, Entity.AVAILABILITY],
        missing_job_settings,
        rmq_settings,
    )
    get_db_mock = mocker.patch.object(job, "get_db_conn")
    get_db_mock.return_value.__aenter__ = AsyncMock()
    get_db_mock.return_value.__aexit__ = AsyncMock()

    return job


@pytest.mark.anyio
async def test_process(entity_population_job_mock: EntityPopulationJob, mocker):
    """
    Test if the process method of the EntityPopulationJob class calls
    and returns the correct ids
    """
    mock_crud = mocker.patch(
        "app.jobs.entity_population.crud.offer.set_offers_as_populated"
    )
    dates = [utc_now() - timedelta(hours=7), utc_now(), utc_now()]
    versions = [(-1, None), (0, -1), (-1, -1)]
    objects = [
        PopulationOfferSchema(
            id=custom_uuid(i),
            product_id=custom_uuid(1),
            created_at=date,
            availability_version=version[0],
            buyable_version=version[1],
        )
        for i, date, version in zip(range(len(dates)), dates, versions)
    ]
    with freeze_time(utc_now()):
        result = await entity_population_job_mock.process(AsyncMock(), objects)

    assert result == {
        Entity.BUYABLE: [objects[1].id, objects[2].id],
        Entity.AVAILABILITY: [objects[2].id],
    }
    mock_crud.assert_called_once()
    assert mock_crud.call_args.args[1] == [Entity.BUYABLE, Entity.AVAILABILITY]
    assert mock_crud.call_args.args[2] == [OfferPk(objects[0].product_id, objects[0].id)]


@pytest.mark.anyio
async def test_run(entity_population_job_mock: EntityPopulationJob, mocker: MockFixture):
    """
    Test the run method of the EntityPopulationJob class, test if the
    RMQ repusher is called with correct arguments and if the published
    ids are correct
    """

    async def get_unpopulated_offers_mock():
        batch = 3
        objects = [
            PopulationOfferSchema(
                id=custom_uuid(i + 1), product_id=custom_uuid(i + 1), created_at=utc_now()
            )
            # 5 Batches of 3 objects
            for i in range(15)
        ]
        for i in range(0, len(objects), batch):
            yield objects[i : i + batch]

    async def process_side_effect(*args, **kwargs):
        objects = args[1]
        return {
            Entity.AVAILABILITY: [objects[0].id, objects[1].id],
            Entity.BUYABLE: [objects[2].id],
        }

    process_mock = mocker.patch.object(entity_population_job_mock, "process")
    process_mock.side_effect = process_side_effect

    mock_crud = mocker.patch(
        "app.jobs.entity_population.crud.offer.get_unpopulated_offers"
    )
    mock_crud.return_value = get_unpopulated_offers_mock()

    rmq_mock = mocker.patch("app.jobs.entity_population.RabbitmqRepublishClient")
    aenter_mock = AsyncMock()
    publish_ids_mock = AsyncMock()

    rmq_mock.return_value.__aenter__ = aenter_mock
    aenter_mock.return_value.republish_ids = publish_ids_mock

    await entity_population_job_mock.run()

    mock_crud.assert_called_once()

    # Assert creation of RMQ clients
    assert rmq_mock.call_count == 2
    assert rmq_mock.call_args_list[0].args[0] == Entity.AVAILABILITY
    assert rmq_mock.call_args_list[1].args[0] == Entity.BUYABLE

    # Assert context manager usage
    assert aenter_mock.call_count == 2

    # Assert the correct ids are published
    assert publish_ids_mock.call_count == 2
    assert publish_ids_mock.call_args_list[0].args[0] == [
        custom_uuid(i + 1) for i in range(15) if (i + 1) % 3 != 0
    ]
    assert publish_ids_mock.call_args_list[1].args[0] == [
        custom_uuid(i + 1) for i in range(15) if (i + 1) % 3 == 0
    ]
