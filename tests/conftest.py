from pathlib import Path

import pytest
from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from app.api.deps import get_db_conn
from app.api_app import create_api_app
from app.config.settings import WorkerSetting, base_settings
from app.constants import Entity
from app.db.pg import drop_db_tables
from app.schemas.availability import AvailabilityMessageSchema
from app.schemas.buyable import BuyableMessageSchema
from app.schemas.offer import OfferMessageSchema
from app.schemas.shop import ShopCreateSchema, ShopDBSchema, ShopMessageSchema
from app.services.availability import AvailabilityService
from app.services.buyable import BuyableService
from app.services.offer import OfferService
from app.services.shop import ShopService
from app.utils import dump_to_json
from app.utils.redis_adapter import RedisAdapter
from app.workers.availability import AvailabilityMessageWorker
from app.workers.buyable import BuyableMessageWorker
from app.workers.offer import OfferMessageWorker
from app.workers.shop import ShopMessageWorker
from tests.factories import shop_factory
from tests.utils import override_obj_get_db_conn

# pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def db_engine() -> AsyncEngine:
    engine = create_async_engine(
        base_settings.postgres_db_dsn,
        json_serializer=dump_to_json,
    )
    # await drop_db_tables(engine)

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


@pytest.fixture()
async def redis() -> Redis:
    async with RedisAdapter(base_settings.redis_dsn, decode_responses=False) as redis:
        await redis.flushdb()
        yield redis


@pytest.fixture(autouse=True)
async def api_app(db_conn) -> FastAPI:
    api = create_api_app()
    api.dependency_overrides[get_db_conn] = lambda: db_conn
    yield api


@pytest.fixture
async def shops_create(db_conn) -> list[ShopDBSchema]:
    return [await shop_factory(db_conn) for _i in range(5)]


@pytest.fixture
async def shops(db_conn) -> list[ShopCreateSchema]:
    return [await shop_factory(db_conn, create=False) for _i in range(5)]


@pytest.fixture
async def availability_service() -> AvailabilityService:
    yield AvailabilityService()


@pytest.fixture
async def buyable_service() -> BuyableService:
    yield BuyableService()


@pytest.fixture
async def offer_service() -> OfferService:
    yield OfferService()


@pytest.fixture
async def shop_service() -> ShopService:
    yield ShopService()


@pytest.fixture
def worker_settings() -> WorkerSetting:
    settings = WorkerSetting()
    return settings


@pytest.fixture
async def worker_redis(worker_settings) -> Redis:
    async with RedisAdapter(
        worker_settings.redis_dsn, encoding="utf-8", decode_responses=True
    ) as redis:
        await redis.flushdb()
        yield redis


@pytest.fixture
async def buyable_worker(db_engine, db_conn, worker_settings, worker_redis):
    yield override_obj_get_db_conn(
        db_conn,
        BuyableMessageWorker(
            Entity.BUYABLE, worker_settings, db_engine, worker_redis, BuyableMessageSchema
        ),
    )


@pytest.fixture
async def availability_worker(db_engine, db_conn, worker_settings, worker_redis):
    yield override_obj_get_db_conn(
        db_conn,
        AvailabilityMessageWorker(
            Entity.AVAILABILITY,
            worker_settings,
            db_engine,
            worker_redis,
            AvailabilityMessageSchema,
        ),
    )


@pytest.fixture
async def offer_worker(db_engine, db_conn, worker_settings, worker_redis):
    yield override_obj_get_db_conn(
        db_conn,
        OfferMessageWorker(
            Entity.OFFER, worker_settings, db_engine, worker_redis, OfferMessageSchema
        ),
    )


@pytest.fixture
async def shop_worker(db_engine, db_conn, worker_settings, worker_redis):
    yield override_obj_get_db_conn(
        db_conn,
        ShopMessageWorker(
            Entity.SHOP, worker_settings, db_engine, worker_redis, ShopMessageSchema
        ),
    )
