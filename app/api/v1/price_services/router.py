from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from app.api.deps import get_db_conn
from app.api.response import ORJsonResponse

router = APIRouter(prefix="/v1", default_response_class=ORJsonResponse)


@router.get(
    "/ping",
    description="Ping pong",
)
async def product_detail(db_conn: AsyncConnection = Depends(get_db_conn)) -> dict:  # noqa
    return {"pong": True}
