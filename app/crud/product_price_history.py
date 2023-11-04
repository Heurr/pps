import datetime
from uuid import UUID

import pendulum
from pendulum import Date
from sqlalchemy import JSON, and_, bindparam, tuple_
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.constants import CountryCode
from app.crud.base import CRUDBase
from app.db.tables.prodcut_price_history import product_price_history_table
from app.schemas.product_price_history import (
    ProductPriceHistoryCreateSchema,
    ProductPriceHistoryDBSchema,
    ProductPriceHistoryUpdateSchema,
)
from app.types import IdCountryDatePk
from app.utils import dump_to_json


class CRUDProductPriceHistory(
    CRUDBase[
        ProductPriceHistoryDBSchema,
        ProductPriceHistoryCreateSchema,
        ProductPriceHistoryUpdateSchema,
        IdCountryDatePk,
    ]
):
    async def get(
        self, db_conn: AsyncConnection, obj_id: IdCountryDatePk
    ) -> ProductPriceHistoryDBSchema | None:
        stmt = self.table.select().where(
            and_(
                self.table.c.id == obj_id[0],
                self.table.c.country_code == obj_id[1],
                self.table.c.date == obj_id[2],
            )
        )
        row = (await db_conn.execute(stmt)).one_or_none()
        return self.db_scheme.from_orm(row) if row else None

    async def get_in(
        self, db_conn: AsyncConnection, obj_ids: list[IdCountryDatePk]
    ) -> list[ProductPriceHistoryDBSchema]:
        stmt = self.table.select().where(
            tuple_(self.table.c.id, self.table.c.country_code, self.table.c.date).in_(
                obj_ids
            )
        )
        rows = await db_conn.execute(stmt)
        return [self.db_scheme.from_orm(row) for row in rows]

    async def find_existing_ids(
        self, db_conn: AsyncConnection, pks: list[IdCountryDatePk]
    ) -> set[IdCountryDatePk]:
        stmt = self.table.select().where(
            tuple_(self.table.c.id, self.table.c.country_code, self.table.c.date).in_(pks)
        )
        res = await db_conn.execute(stmt)
        return {(r.id, r.country_code, r.date) for r in res}

    async def remove(
        self, db_conn: AsyncConnection, db_obj: ProductPriceHistoryDBSchema
    ) -> IdCountryDatePk | None:
        return await self.remove_by_id(
            db_conn, (db_obj.id, db_obj.country_code, db_obj.date)
        )

    async def remove_by_id(
        self, db_conn: AsyncConnection, obj_id: IdCountryDatePk
    ) -> IdCountryDatePk | None:
        stmt = (
            self.table.delete()
            .where(
                and_(
                    self.table.c.id == obj_id[0],
                    self.table.c.country_code == obj_id[1],
                    self.table.c.date == obj_id[2],
                )
            )
            .returning(self.table.c.id, self.table.c.country_code, self.table.c.date)
        )
        res = (await db_conn.execute(stmt)).one_or_none()
        return res  # type: ignore[return-value]

    async def remove_many_with_version_checking(
        self, db_conn: AsyncConnection, ids_versions: list[tuple[IdCountryDatePk, int]]
    ) -> list[IdCountryDatePk]:
        # Sort by id only
        ids_versions.sort(key=lambda item: item[0][0])
        reduced_ids_versions: list[tuple[UUID, CountryCode, Date, int]] = [
            # Transform a list of tuple tuples into a list of tuples
            (id_version[0][0], id_version[0][1], id_version[0][2], id_version[1])
            for id_version in ids_versions
        ]
        json_data = dump_to_json(reduced_ids_versions)

        stmt = sa_text(
            """
            WITH q AS (
              SELECT
                (value->>0)::uuid AS id,
                (value->>1)::countrycode AS country_code,
                (value->>2)::date AS date,
                (value->>3)::bigint AS version
              FROM json_array_elements('{json_data}')
            )
            DELETE FROM {table}
            USING q
            WHERE
                {table}.id = q.id AND
                {table}.country_code = q.country_code AND
                {table}.date = q.date AND
                {table}.version < q.version
            RETURNING {table}.id, {table}.country_code, {table}.date
            """.format(
                table=self.table.name, json_data=json_data
            )
        )
        res = await db_conn.execute(stmt)
        deleted_ids = [(r.id, r.country_code, r.date) for r in res]
        return deleted_ids

    async def upsert_many_with_version_checking(
        self,
        db_conn: AsyncConnection,
        price_history: list[
            ProductPriceHistoryCreateSchema | ProductPriceHistoryUpdateSchema
        ],
    ) -> list[IdCountryDatePk]:
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
                self.jsonable_date(pp.date),
            )
            for pp in price_history
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
                (value->>8)::date,
                NOW(),
                NOW()
            FROM json_array_elements(:json_data)
        )
        , inserted AS (
            INSERT INTO {table}
                (id, version, country_code, currency_code, max_price,
                 min_price, avg_price, price_type, date, created_at, updated_at)
            SELECT * FROM input_rows
            ON CONFLICT (id, country_code, date) DO
                UPDATE SET
                    country_code = EXCLUDED.country_code,
                    currency_code = EXCLUDED.currency_code,
                    max_price = EXCLUDED.max_price,
                    min_price = EXCLUDED.min_price,
                    avg_price = EXCLUDED.avg_price,
                    price_type = EXCLUDED.price_type,
                    date = EXCLUDED.date,
                    version = EXCLUDED.version,
                    updated_at = NOW()
                WHERE
                    {table}.id = EXCLUDED.id
                    AND {table}.country_code = EXCLUDED.country_code
                    AND {table}.date = EXCLUDED.date
                    AND {table}.version <= EXCLUDED.version
            RETURNING id, country_code, date
        )
        SELECT id, country_code, date FROM inserted
        """.format(
                table=self.table.name
            )
        ).bindparams(bindparam("json_data", value=data, type_=JSON))

        res = await db_conn.execute(stmt)
        inserted_ids = [(r.id, r.country_code, r.date) for r in res]
        return inserted_ids

    @staticmethod
    def jsonable_date(date: datetime.date | pendulum.Date):
        return date.for_json() if isinstance(date, pendulum.Date) else date


crud_product_price_history = CRUDProductPriceHistory(
    table=product_price_history_table,
    db_scheme=ProductPriceHistoryDBSchema,
    create_scheme=ProductPriceHistoryCreateSchema,
    update_scheme=ProductPriceHistoryUpdateSchema,
)
