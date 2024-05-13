import logging

from asyncpg.exceptions import (
    DataError,
    InterfaceError,
    TransactionRollbackError,
)
from sqlalchemy import tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.custom_types import BasePricePk
from app.db.tables.base_price import base_price_table
from app.schemas.base_price import BasePriceCreateSchema, BasePriceDBSchema
from app.utils import utc_now
from app.utils.sentry import set_sentry_context


class CRUDBasePrice:
    def __init__(self):
        self.table = base_price_table
        self.updatable_columns = ["price", "updated_at"]
        self.db_scheme = BasePriceDBSchema
        self.logger = logging.getLogger(__name__)

    async def get_many(
        self, db_conn: AsyncConnection, *, skip: int = 0, limit: int = 100
    ) -> list[BasePriceDBSchema]:
        stmt = self.table.select().offset(skip).limit(limit)
        rows = await db_conn.execute(stmt)
        return [self.db_scheme.model_validate(row) for row in rows]

    async def get_in(
        self, db_conn: AsyncConnection, obj_pks: list[BasePricePk]
    ) -> list[BasePriceDBSchema]:
        stmt = self.table.select().where(
            tuple_(self.table.c.product_id, self.table.c.price_type).in_(obj_pks)
        )
        rows = await db_conn.execute(stmt)
        return [self.db_scheme.model_validate(row) for row in rows]

    async def create_many(
        self, db_conn: AsyncConnection, base_prices_in: list[BasePriceCreateSchema]
    ) -> list[BasePriceDBSchema]:
        now = utc_now()
        values = [
            {**obj_in.model_dump(), "created_at": now, "updated_at": now}
            for obj_in in base_prices_in
        ]
        stmt = self.table.insert().values(values).returning(self.table)
        rows = (await db_conn.execute(stmt)).fetchall()
        return [self.db_scheme.model_validate(row) for row in rows]

    async def upsert_many(
        self,
        db_conn: AsyncConnection,
        base_prices_in: list[BasePriceCreateSchema],
    ) -> list[BasePricePk]:
        # Sort before upserting to avoid conflicts
        base_prices_in.sort(key=lambda bp: (bp.product_id, bp.price_type))

        now = utc_now()
        values = [
            {**bp.model_dump(), "created_at": now, "updated_at": now}
            for bp in base_prices_in
        ]

        stmt = insert(self.table).values(values)
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=self.table.primary_key.columns,
            # When updating, do only for specified columns
            set_={k: getattr(stmt.excluded, k) for k in self.updatable_columns},
        ).returning(self.table.c.product_id, self.table.c.price_type)

        try:
            res = await db_conn.execute(on_conflict_stmt)
        except (InterfaceError, TransactionRollbackError, DataError) as err:
            self.logger.error("Query raised error: %s\n%s", stmt, values)
            set_sentry_context("pg", {"stmt": stmt, "values": values})
            raise err

        upserted_ids = [
            BasePricePk(product_id=r.product_id, price_type=r.price_type) for r in res
        ]
        return upserted_ids


crud_base_price = CRUDBasePrice()
