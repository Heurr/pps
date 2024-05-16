import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app.config.settings import MaintenanceJobSettings
from app.jobs.maintenance import MaintenanceJob
from tests.utils import override_obj_get_db_conn


@pytest.fixture
async def maintenance_job(
    db_engine: AsyncEngine,
    db_conn: AsyncConnection,
    redis: Redis,
):
    job = MaintenanceJob(db_engine, redis, MaintenanceJobSettings())
    override_obj_get_db_conn(db_conn, job)
    yield job
