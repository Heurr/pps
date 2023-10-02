import logging
from uuid import UUID

from asyncpg.exceptions import (
    DataError,
    InterfaceError,
    TransactionRollbackError,
)
from sqlalchemy import JSON, bindparam
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.tables.product import product_table
from app.schemas.product import (
    ProductCreateSchema,
    ProductDBSchema,
    ProductUpdateSchema,
)
from app.utils.sentry import set_sentry_context

from .base import CRUDBase

logger = logging.getLogger(__name__)


class CRUDProduct(CRUDBase[ProductDBSchema, ProductCreateSchema, ProductUpdateSchema]):
    async def create_many_or_do_nothing(
        self, db_conn: AsyncConnection, entities: list[ProductCreateSchema]
    ) -> list[UUID]:
        self.sort_entities_by_id(entities)
        data = [
            (
                p.id,
                p.local_product_id,
                p.version,
                p.name,
                p.country.value if p.country else None,
            )
            for p in entities
        ]

        stmt = sa_text(
            """
        WITH input_rows AS (
            SELECT
                (value->>0)::uuid,
                (value->>1)::varchar,
                (value->>2)::bigint,
                (value->>3)::varchar,
                (value->>4)::varchar,
                NOW(),
                NOW()
            FROM json_array_elements(:json_data)
        )
        , inserted AS (
            INSERT INTO {table}
                (id, local_product_id, version, name, country, created_at, updated_at)
            SELECT * FROM input_rows
            ON CONFLICT (id) DO NOTHING
            RETURNING id
        )
        SELECT id FROM inserted
        """.format(
                table=self.table.name
            )
        ).bindparams(bindparam("json_data", value=data, type_=JSON))

        try:
            res = await db_conn.execute(stmt)
        except (
            InterfaceError,
            TransactionRollbackError,
            DataError,
        ) as err:
            logger.warning("Query raised error during fetch all: %s\n%s", stmt, data)
            set_sentry_context("pg", {"stmt": stmt, "json_data": data})
            raise err

        inserted_ids = [r.id for r in res]
        return inserted_ids

    async def update_many(
        self, db_conn: AsyncConnection, entities: list[ProductUpdateSchema]
    ) -> list[UUID]:
        self.sort_entities_by_id(entities)
        data = [(p.id, p.version, p.name) for p in entities]

        stmt = sa_text(
            """
            UPDATE {table} SET
                name = input_rows.name,
                version = input_rows.version,
                updated_at = NOW()
            FROM (
                SELECT
                    (value->>0)::uuid AS id,
                    (value->>1)::bigint AS version,
                    (value->>2)::varchar AS name
                FROM json_array_elements(:json_data)
            ) AS input_rows
            WHERE {table}.id = input_rows.id AND {table}.version <= input_rows.version
            RETURNING {table}.id
            """.format(
                table=self.table.name
            )
        ).bindparams(bindparam("json_data", value=data, type_=JSON))

        res = await db_conn.execute(stmt)
        updated_ids = [r.id for r in res]
        return updated_ids


crud_product = CRUDProduct(
    table=product_table,
    db_scheme=ProductDBSchema,
    create_scheme=ProductCreateSchema,
    update_scheme=ProductUpdateSchema,
    local_id_column=product_table.c.local_product_id,
)
