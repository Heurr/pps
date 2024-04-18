from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import api_router
from app.api.v1.price_services import v1_price_services_router
from app.config.api import api_settings
from app.db import db_adapter
from app.utils.log import prepare_logging
from app.utils.sentry import init_sentry

prepare_logging()
init_sentry(server_name="api-server", component="api")


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
    await db_adapter.connect()
    yield
    await db_adapter.disconnect()


def create_api_app():
    app = FastAPI(
        title="Price Services API",
        docs_url=api_settings.DOC_URL,
        redoc_url=api_settings.REDOC_URL,
        openapi_url=api_settings.OPENAPI_URL,
        debug=api_settings.is_dev,
        lifespan=lifespan,
    )

    app.include_router(api_router)
    app.include_router(v1_price_services_router)
    return app
