from fastapi import APIRouter, Depends
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncConnection
from starlette.status import HTTP_200_OK

from app.api.deps import get_db_conn
from app.api.response import ORJsonResponse
from app.api.schemas import HealthcheckStatus

router = APIRouter(default_response_class=ORJsonResponse)


@router.get(
    "/-/liveness",
    response_model=HealthcheckStatus,
    description="Basic healthcheck endpoint if API application is running.",
    responses={HTTP_200_OK: {"description": "One Offer Rank API is running."}},
    tags=["healthcheck"],
)
async def liveness() -> HealthcheckStatus:
    return HealthcheckStatus(status="success", description="API is running.")


@router.get(
    "/-/readiness",
    response_model=HealthcheckStatus,
    description=(
        "Healthcheck endpoint if API application is ready "
        "and all database connections are available."
    ),
    responses={
        HTTP_200_OK: {"description": "One Offer Rank API is ready."},
    },
    tags=["healthcheck"],
)
async def readiness(
    db_conn: AsyncConnection = Depends(get_db_conn),
) -> HealthcheckStatus:
    postgres_version = (await db_conn.execute(sa_text("SELECT VERSION()"))).scalar()
    return HealthcheckStatus(
        status="success",
        description="API is ready.",
        connections={"postgres": postgres_version},
    )
