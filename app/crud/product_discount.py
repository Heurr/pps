from sqlalchemy import JSON, bindparam
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.crud.id_country_base import CRUDIdCountryBase
from app.db.tables.product_discount import product_discount_table
from app.schemas.product_discount import (
    ProductDiscountCreateSchema,
    ProductDiscountDBSchema,
    ProductDiscountUpdateSchema,
)
from app.types import IdCountryPk


class CRUDProductDiscount(
    CRUDIdCountryBase[
        ProductDiscountDBSchema,
        ProductDiscountCreateSchema,
        ProductDiscountUpdateSchema,
    ]
):
    async def upsert_many_with_version_checking(
        self,
        db_conn: AsyncConnection,
        discounts: list[ProductDiscountCreateSchema | ProductDiscountUpdateSchema],
    ) -> list[IdCountryPk]:
        data = [
            (
                pd.id,
                pd.version,
                pd.country_code,
                pd.discount,
                pd.price_type,
            )
            for pd in discounts
        ]

        stmt = sa_text(
            """
        WITH input_rows AS (
            SELECT
                (value->>0)::uuid,
                (value->>1)::bigint,
                (value->>2)::countrycode,
                (value->>3)::numeric,
                (value->>4)::productpricetype,
                NOW(),
                NOW()
            FROM json_array_elements(:json_data)
        )
        , inserted AS (
            INSERT INTO {table}
                (id, version, country_code, discount, price_type, created_at, updated_at)
            SELECT * FROM input_rows
            ON CONFLICT (id, country_code) DO
                UPDATE SET
                    discount = EXCLUDED.discount,
                    price_type = EXCLUDED.price_type,
                    version = EXCLUDED.version,
                    updated_at = NOW()
                WHERE
                    {table}.id = EXCLUDED.id
                    AND {table}.country_code = EXCLUDED.country_code
                    AND {table}.version <= EXCLUDED.version
            RETURNING id, country_code
        )
        SELECT id, country_code FROM inserted
        """.format(
                table=self.table.name
            )
        ).bindparams(bindparam("json_data", value=data, type_=JSON))

        res = await db_conn.execute(stmt)
        inserted_ids = [(r.id, r.country_code) for r in res]
        return inserted_ids


crud_product_discount = CRUDProductDiscount(
    table=product_discount_table,
    db_scheme=ProductDiscountDBSchema,
    create_scheme=ProductDiscountCreateSchema,
    update_scheme=ProductDiscountUpdateSchema,
)
