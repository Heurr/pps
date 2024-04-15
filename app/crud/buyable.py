from uuid import UUID

from sqlalchemy import JSON, bindparam
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.crud.base import CRUDBase
from app.db.tables.buyable import buyable_table
from app.schemas.buyable import BuyableCreateSchema, BuyableDBSchema, BuyableUpdateSchema


class CRUDBuyable(CRUDBase[BuyableDBSchema, BuyableCreateSchema, BuyableUpdateSchema]):
    async def upsert_many_with_version_checking(
        self,
        db_conn: AsyncConnection,
        buyables: list[BuyableCreateSchema | BuyableUpdateSchema],
    ) -> list[UUID]:
        data = [
            (
                b.id,
                b.country_code,
                b.version,
                b.buyable,
            )
            for b in buyables
        ]

        stmt = sa_text(
            """
        WITH input_rows AS (
            SELECT
                (value->>0)::uuid,
                (value->>1)::countrycode,
                (value->>2)::bigint,
                (value->>3)::boolean,
                NOW(),
                NOW()
            FROM json_array_elements(:json_data)
        )
        , inserted AS (
            INSERT INTO {table}
            (id, country_code, version, buyable, created_at, updated_at)
            SELECT * FROM input_rows
            ON CONFLICT (id) DO
                UPDATE SET
                    buyable = EXCLUDED.buyable,
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
        upserted_ids = [r.id for r in res]
        return upserted_ids


crud_buyable = CRUDBuyable(
    table=buyable_table,
    db_scheme=BuyableDBSchema,
    create_scheme=BuyableCreateSchema,
    update_scheme=BuyableUpdateSchema,
)
