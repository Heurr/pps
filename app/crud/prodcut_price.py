from sqlalchemy import JSON, bindparam
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.crud.id_country_base import CRUDIdCountryBase
from app.db.tables.product_price import product_price_table
from app.schemas.product_price import (
    ProductPriceCreateSchema,
    ProductPriceDBSchema,
    ProductPriceUpdateSchema,
)
from app.types import IdCountryPk


class CRUDProductPrice(
    CRUDIdCountryBase[
        ProductPriceDBSchema, ProductPriceCreateSchema, ProductPriceUpdateSchema
    ]
):
    async def upsert_many_with_version_checking(
        self,
        db_conn: AsyncConnection,
        product_prices: list[ProductPriceCreateSchema | ProductPriceUpdateSchema],
    ) -> list[IdCountryPk]:
        data = [
            (
                pp.id,
                pp.version,
                pp.country_code,
                pp.currency_code,
                pp.max_price,
                pp.min_price,
                pp.avg_price,
                pp.price_type,
            )
            for pp in product_prices
        ]

        stmt = sa_text(
            """
        WITH input_rows AS (
            SELECT
                (value->>0)::uuid,
                (value->>1)::bigint,
                (value->>2)::countrycode,
                (value->>3)::currencycode,
                (value->>4)::numeric,
                (value->>5)::numeric,
                (value->>6)::numeric,
                (value->>7)::productpricetype,
                NOW(),
                NOW()
            FROM json_array_elements(:json_data)
        )
        , inserted AS (
            INSERT INTO {table}
                (id, version, country_code, currency_code, max_price, min_price, avg_price, price_type, created_at, updated_at)
            SELECT * FROM input_rows
            ON CONFLICT (id, country_code) DO
                UPDATE SET
                    currency_code = EXCLUDED.currency_code,
                    max_price = EXCLUDED.max_price,
                    min_price = EXCLUDED.min_price,
                    avg_price = EXCLUDED.avg_price,
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


crud_product_price = CRUDProductPrice(
    table=product_price_table,
    db_scheme=ProductPriceDBSchema,
    create_scheme=ProductPriceCreateSchema,
    update_scheme=ProductPriceUpdateSchema,
)
