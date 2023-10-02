from pathlib import Path
from typing import Any, AsyncGenerator

import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from app.api.deps import get_db_conn
from app.api_app import create_api_app
from app.config.settings import base_settings
from app.db.pg import drop_db_tables
from app.utils import dump_to_json

# pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine, Any]:
    engine = create_async_engine(
        base_settings.postgres_db_dsn,
        json_serializer=dump_to_json,
    )
    await drop_db_tables(engine)

    alembic_config_path = Path(__name__).absolute().parent / "alembic.ini"
    alembic_command.upgrade(AlembicConfig(str(alembic_config_path)), "head")

    yield engine

    await drop_db_tables(engine)
    await engine.dispose()


@pytest.fixture
async def db_conn(db_engine) -> AsyncConnection:
    async with db_engine.begin() as conn:
        yield conn
        await conn.rollback()


@pytest.fixture(autouse=True)
async def api_app(db_conn) -> FastAPI:
    api = create_api_app()
    api.dependency_overrides[get_db_conn] = lambda: db_conn
    yield api
