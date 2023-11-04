from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import and_, tuple_
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.constants import CountryCode
from app.crud.base import CRUDBase
from app.schemas.base import (
    BaseIdCountryModel,
    DBBaseIdCountryModel,
)
from app.types import IdCountryPk
from app.utils import dump_to_json

DBIdCountrySchemaTypeT = TypeVar("DBIdCountrySchemaTypeT", bound=DBBaseIdCountryModel)
IdCountryCreateSchemaTypeT = TypeVar(
    "IdCountryCreateSchemaTypeT", bound=BaseIdCountryModel
)
IdCountryUpdateSchemaTypeT = TypeVar(
    "IdCountryUpdateSchemaTypeT", bound=BaseIdCountryModel
)


class CRUDIdCountryBase(
    CRUDBase[
        DBIdCountrySchemaTypeT,
        IdCountryCreateSchemaTypeT,
        IdCountryUpdateSchemaTypeT,
        IdCountryPk,
    ],
    Generic[
        DBIdCountrySchemaTypeT, IdCountryCreateSchemaTypeT, IdCountryUpdateSchemaTypeT
    ],
):
    async def get(
        self, db_conn: AsyncConnection, obj_id: IdCountryPk
    ) -> DBIdCountrySchemaTypeT | None:
        stmt = self.table.select().where(
            and_(self.table.c.id == obj_id[0], self.table.c.country_code == obj_id[1])
        )
        row = (await db_conn.execute(stmt)).one_or_none()
        return self.db_scheme.from_orm(row) if row else None

    async def get_in(
        self, db_conn: AsyncConnection, obj_ids: list[IdCountryPk]
    ) -> list[DBIdCountrySchemaTypeT]:
        stmt = self.table.select().where(
            tuple_(self.table.c.id, self.table.c.country_code).in_(obj_ids)
        )
        rows = await db_conn.execute(stmt)
        return [self.db_scheme.from_orm(row) for row in rows]

    async def find_existing_ids(
        self, db_conn: AsyncConnection, pks: list[IdCountryPk]
    ) -> set[IdCountryPk]:
        stmt = self.table.select().where(
            tuple_(self.table.c.id, self.table.c.country_code).in_(pks)
        )
        res = await db_conn.execute(stmt)
        return {(r.id, r.country_code) for r in res}

    async def remove(
        self, db_conn: AsyncConnection, db_obj: DBIdCountrySchemaTypeT
    ) -> IdCountryPk | None:
        return await self.remove_by_id(db_conn, (db_obj.id, db_obj.country_code))

    async def remove_by_id(
        self, db_conn: AsyncConnection, obj_id: IdCountryPk
    ) -> IdCountryPk | None:
        stmt = (
            self.table.delete()
            .where(
                and_(self.table.c.id == obj_id[0], self.table.c.country_code == obj_id[1])
            )
            .returning(self.table.c.id, self.table.c.country_code)
        )
        res = (await db_conn.execute(stmt)).one_or_none()
        return res  # type: ignore[return-value]

    async def remove_many_with_version_checking(
        self, db_conn: AsyncConnection, ids_versions: list[tuple[IdCountryPk, int]]
    ) -> list[IdCountryPk]:
        # Sort by id only
        ids_versions.sort(key=lambda item: item[0][0])
        reduced_ids_versions: list[tuple[UUID, CountryCode, int]] = [
            # Transform a list of tuple tuples into a list of tuples
            (id_version[0][0], id_version[0][1], id_version[1])
            for id_version in ids_versions
        ]
        json_data = dump_to_json(reduced_ids_versions)

        stmt = sa_text(
            """
            WITH q AS (
              SELECT
                (value->>0)::uuid AS id,
                (value->>1)::countrycode AS country_code,
                (value->>2)::bigint AS version
              FROM json_array_elements('{json_data}')
            )
            DELETE FROM {table}
            USING q
            WHERE
                {table}.id = q.id AND
                {table}.country_code = q.country_code AND
                {table}.version < q.version
            RETURNING {table}.id, {table}.country_code
            """.format(
                table=self.table.name, json_data=json_data
            )
        )
        res = await db_conn.execute(stmt)
        deleted_ids = [(r.id, r.country_code) for r in res]
        return deleted_ids
