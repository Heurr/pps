import logging
from uuid import UUID

from sqlalchemy import JSON, bindparam
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.tables.offer import offer_table
from app.schemas.offer import OfferCreateSchema, OfferDBSchema, OfferUpdateSchema

from .base import CRUDBase

logger = logging.getLogger(__name__)


class CRUDOffer(CRUDBase[OfferDBSchema, OfferCreateSchema, OfferUpdateSchema]):
    async def upsert_many_with_version_checking(
        self,
        db_conn: AsyncConnection,
        entities: list[OfferCreateSchema | OfferUpdateSchema],
    ) -> list[UUID]:
        data = [
            (
                o.id,
                o.version,
                o.product_id,
                o.country_code,
                o.shop_id,
                o.amount,
                o.currency_code,
            )
            for o in entities
        ]

        stmt = sa_text(
            """
        WITH input_rows AS (
            SELECT
                (value->>0)::uuid,
                (value->>1)::bigint,
                (value->>2)::uuid,
                (value->>3)::countrycode,
                (value->>4)::uuid,
                (value->>5)::numeric,
                (value->>6)::currencycode,
                NOW(),
                NOW()
            FROM json_array_elements(:json_data)
        )
        , inserted AS (
            INSERT INTO {table}
                (id, version, product_id, country_code, shop_id, amount, currency_code, created_at, updated_at)
            SELECT * FROM input_rows
            ON CONFLICT (id) DO
                UPDATE SET
                    product_id = excluded.product_id,
                    shop_id = EXCLUDED.shop_id,
                    amount = EXCLUDED.amount,
                    currency_code = EXCLUDED.currency_code,
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


crud_offer = CRUDOffer(
    table=offer_table,
    db_scheme=OfferDBSchema,
    create_scheme=OfferCreateSchema,
    update_scheme=OfferUpdateSchema,
)
