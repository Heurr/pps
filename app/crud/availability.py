from uuid import UUID

from sqlalchemy import JSON, bindparam
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.crud.base import CRUDBase
from app.db.tables.availability import availability_table
from app.schemas.availability import (
    AvailabilityCreateSchema,
    AvailabilityDBSchema,
    AvailabilityUpdateSchema,
)


class CRUDAvailability(
    CRUDBase[
        AvailabilityDBSchema, AvailabilityCreateSchema, AvailabilityUpdateSchema, UUID
    ]
):
    async def upsert_many_with_version_checking(
        self,
        db_conn: AsyncConnection,
        availabilities: list[AvailabilityCreateSchema | AvailabilityUpdateSchema],
    ) -> list[UUID]:
        data = [
            (
                a.id,
                a.version,
                a.in_stock,
            )
            for a in availabilities
        ]

        stmt = sa_text(
            """
        WITH input_rows AS (
            SELECT
                (value->>0)::uuid,
                (value->>1)::bigint,
                (value->>2)::boolean,
                NOW(),
                NOW()
            FROM json_array_elements(:json_data)
        )
        , inserted AS (
            INSERT INTO {table}
            (id, version, in_stock, created_at, updated_at)
            SELECT * FROM input_rows
            ON CONFLICT (id) DO
                UPDATE SET
                    version = EXCLUDED.version,
                    in_stock = EXCLUDED.in_stock,
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


crud_availability = CRUDAvailability(
    table=availability_table,
    db_scheme=AvailabilityDBSchema,
    create_scheme=AvailabilityCreateSchema,
    update_scheme=AvailabilityUpdateSchema,
)
