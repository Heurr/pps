# mypy: disable-error-code="union-attr"
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncConnection

from app.db import db_adapter
from app.metrics import DB_CONNECTIONS

checked_in = DB_CONNECTIONS.labels(state="checkedin")
checked_out = DB_CONNECTIONS.labels(state="checkedout")


async def get_db_conn() -> AsyncGenerator[AsyncConnection, Any]:
    async with db_adapter.engine.begin() as conn:
        pool = db_adapter.engine.pool
        checked_in.set(pool.checkedin())
        checked_out.set(pool.checkedout())
        yield conn
