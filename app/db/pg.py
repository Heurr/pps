import logging
import re

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from app.utils import dump_to_json

logger = logging.getLogger(__name__)

sa_metadata = sa.MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class DBAdapter:
    def __init__(self, dsn, **kwargs) -> None:
        self.engine: AsyncEngine | None = None
        self.dsn = dsn
        self.config = {"json_serializer": dump_to_json, **kwargs}

    async def __aenter__(self) -> AsyncEngine:
        return await self.connect()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()

    async def connect(self) -> AsyncEngine:
        if self.engine:
            logger.info("DB engine already exists")
            return self.engine

        self.engine = create_async_engine(self.dsn, **self.config)
        logger.info("Connected to Postgresql server.")
        return self.engine

    async def disconnect(self) -> None:
        if self.engine:
            await self.engine.dispose()
            logger.info("Disconnected from Postgresql server")


def get_all_table_names_select() -> sa.sql.Select:
    return (
        sa.select(sa.column("tablename").label("name"))
        .select_from(sa.text("pg_tables"))
        .where(sa.literal_column("schemaname") == "public")
    )


def custom_types() -> list[str]:
    return ["currencycode", "countrycode"]


async def drop_db_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as db_conn:
        for table in await db_conn.execute(get_all_table_names_select()):
            # Don't delete partition tables since deleting the product_prices_history
            # table deletes all partition tables
            if bool(re.search(r"\d", table.name)):
                continue
            stmt = sa.text(f"DROP TABLE {table.name} CASCADE")
            await db_conn.execute(stmt)
        for type_name in custom_types():
            await db_conn.execute(sa.text(f"DROP TYPE {type_name} CASCADE"))


async def truncate_db(engine: AsyncEngine) -> None:
    async with engine.begin() as db_conn:
        for table in await db_conn.execute(get_all_table_names_select()):
            if table.name in ["alembic_version"]:
                continue

            stmt = sa.text(f"TRUNCATE {table.name} RESTART IDENTITY CASCADE")
            await db_conn.execute(stmt)


async def get_table_names(db_conn: AsyncConnection) -> list[str]:
    return [table.name for table in await db_conn.execute(get_all_table_names_select())]
