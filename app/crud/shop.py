import logging
from uuid import UUID

from sqlalchemy import JSON, bindparam
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.tables.shop import shop_table
from app.schemas.shop import ShopCreateSchema, ShopDBSchema

from .base import CRUDBase

logger = logging.getLogger(__name__)


class CRUDShop(CRUDBase[ShopDBSchema, ShopCreateSchema]):
    async def upsert_many_with_version_checking(
        self,
        db_conn: AsyncConnection,
        entities: list[ShopCreateSchema],
    ) -> list[UUID]:
        data = [
            (
                s.id,
                s.country_code,
                s.version,
                s.paying,
                s.certified,
                s.enabled,
                s.verified,
            )
            for s in entities
        ]

        stmt = sa_text(
            """
        WITH input_rows AS (
            SELECT
                (value->>0)::uuid,
                (value->>1)::countrycode,
                (value->>2)::bigint,
                (value->>3)::boolean,
                (value->>4)::boolean,
                (value->>5)::boolean,
                (value->>6)::boolean,
                NOW(),
                NOW()
            FROM json_array_elements(:json_data)
        )
        , inserted AS (
            INSERT INTO {table}
                (id, country_code, version, paying, certified, enabled, verified, created_at, updated_at)
            SELECT * FROM input_rows
            ON CONFLICT (id) DO
                UPDATE SET
                    paying = EXCLUDED.paying,
                    enabled = EXCLUDED.enabled,
                    verified = EXCLUDED.verified,
                    certified = EXCLUDED.certified,
                    version = EXCLUDED.version,
                    updated_at = NOW()
                WHERE {table}.id = EXCLUDED.id AND {table}.version <= EXCLUDED.version
            RETURNING id
        )
        SELECT id FROM inserted
        """.format(
                table=self.table.name
            )
        ).bindparams(bindparam("json_data", value=data, type_=JSON))

        res = await db_conn.execute(stmt)
        inserted_ids = [r.id for r in res]
        return inserted_ids


crud_shop = CRUDShop(
    table=shop_table,
    db_scheme=ShopDBSchema,
    create_scheme=ShopCreateSchema,
)
