import logging
from datetime import date
from uuid import UUID

from asyncpg.exceptions import (
    DataError,
    InterfaceError,
    TransactionRollbackError,
)
from sqlalchemy import Table, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.custom_types import ProductPriceDeletePk, ProductPricePk
from app.db.tables.product_price import product_price_table
from app.schemas.product_price import ProductPriceCreateSchema, ProductPriceDBSchema
from app.utils.sentry import set_sentry_context


class CRUDProductPrice:
    def __init__(self, table: Table):
        self.table = table
        self.updatable_columns = ["min_price", "max_price", "updated_at"]
        self.db_scheme = ProductPriceDBSchema
        self.logger = logging.getLogger(__name__)

    async def get_many(
        self, db_conn: AsyncConnection, *, skip: int = 0, limit: int = 100
    ) -> list[ProductPriceDBSchema]:
        stmt = self.table.select().offset(skip).limit(limit)
        rows = await db_conn.execute(stmt)
        return [self.db_scheme.model_validate(row) for row in rows]

    async def get_in(
        self, db_conn: AsyncConnection, obj_pks: list[ProductPricePk]
    ) -> list[ProductPriceDBSchema]:
        stmt = self.table.select().where(
            tuple_(
                self.table.c.day, self.table.c.product_id, self.table.c.price_type
            ).in_(obj_pks)
        )
        rows = await db_conn.execute(stmt)
        return [self.db_scheme.model_validate(row) for row in rows]

    async def get_by_product_id_and_day(
        self, db_conn: AsyncConnection, day: date, product_ids: list[UUID]
    ) -> list[ProductPriceDBSchema]:
        stmt = self.table.select().where(
            self.table.c.day == day, self.table.c.product_id.in_(product_ids)
        )
        rows = await db_conn.execute(stmt)
        return [self.db_scheme.model_validate(row) for row in rows]

    async def create_many(
        self, db_conn: AsyncConnection, objs_in: list[ProductPriceCreateSchema]
    ) -> list[ProductPriceDBSchema]:
        all_values = [{**obj_in.model_dump()} for obj_in in objs_in]

        stmt = self.table.insert().values(all_values).returning(self.table)
        rows = (await db_conn.execute(stmt)).fetchall()
        return [self.db_scheme.model_validate(row) for row in rows]

    async def _do_upsert_many(
        self,
        db_conn: AsyncConnection,
        cols_to_update_on_conflict: list[str],
        values: list[dict],
    ) -> list[ProductPricePk]:
        # Sort before upserting to avoid conflicts
        values.sort(key=lambda x: [x["day"], x["product_id"], x["price_type"]])

        stmt = insert(self.table).values(values)
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=self.table.primary_key.columns,
            # When updating, do only for specified columns
            set_={k: getattr(stmt.excluded, k) for k in cols_to_update_on_conflict},
        ).returning(self.table.c.product_id, self.table.c.day, self.table.c.price_type)

        try:
            res = await db_conn.execute(on_conflict_stmt)
        except (InterfaceError, TransactionRollbackError, DataError) as err:
            self.logger.error("Query raised error: %s\n%s", stmt, values)
            set_sentry_context("pg", {"stmt": stmt, "values": values})
            raise err

        upserted_ids = [
            ProductPricePk(day=r.day, product_id=r.product_id, price_type=r.price_type)
            for r in res
        ]
        return upserted_ids

    async def upsert_many(
        self,
        db_conn: AsyncConnection,
        entities: list[ProductPriceCreateSchema],
    ) -> list[ProductPricePk]:
        values = [{**e.model_dump()} for e in entities]
        return await self._do_upsert_many(db_conn, self.updatable_columns, values)

    async def remove_many(
        self,
        db_conn: AsyncConnection,
        delete_pks: list[ProductPriceDeletePk],
        day: date,
    ) -> list[ProductPricePk]:
        if not delete_pks:
            return []
        # Sort by PKs
        delete_pks.sort(key=lambda item: [item.product_id, item.price_type])
        obj_pks = [(day, pk.product_id, pk.price_type) for pk in delete_pks]

        stmt = (
            self.table.delete()
            .where(
                tuple_(
                    self.table.c.day, self.table.c.product_id, self.table.c.price_type
                ).in_(obj_pks)
            )
            .returning(self.table.c.product_id, self.table.c.day, self.table.c.price_type)
        )

        res = await db_conn.execute(stmt)
        deleted_ids = [ProductPricePk(r.day, r.product_id, r.price_type) for r in res]
        return deleted_ids


crud_product_price = CRUDProductPrice(table=product_price_table)
