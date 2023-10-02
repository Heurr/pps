from typing import Callable, Generic, Type, TypeVar
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import JSON, Column, Table, bindparam
from sqlalchemy import and_ as sa_and
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql.elements import Label
from sqlalchemy_utils import Ltree

from app.constants import CountryCode
from app.utils import dump_to_json, utc_now

DBSchemaTypeT = TypeVar("DBSchemaTypeT", bound=BaseModel)
CreateSchemaTypeT = TypeVar("CreateSchemaTypeT", bound=BaseModel)
UpdateSchemaTypeT = TypeVar("UpdateSchemaTypeT", bound=BaseModel)

json_encoder = {Ltree: lambda v: v, Range: lambda v: v}


class CRUDBase(Generic[DBSchemaTypeT, CreateSchemaTypeT, UpdateSchemaTypeT]):
    def __init__(
        self,
        table: Table,
        db_scheme: Type[DBSchemaTypeT],
        create_scheme: Type[CreateSchemaTypeT],
        update_scheme: Type[UpdateSchemaTypeT],
        custom_encoder: dict[str, Callable] | None = None,
        local_id_column: Column | None = None,
    ):
        self.table = table
        self.db_scheme = db_scheme
        self.create_scheme = create_scheme
        self.update_scheme = update_scheme
        self.custom_encoder = json_encoder.copy()
        self.custom_encoder.update(custom_encoder or {})  # type: ignore
        self.local_id_column = local_id_column
        self.has_updated_at = "updated_at" in self.table.c

    @staticmethod
    def prefixed_columns(table: Table) -> list[Label]:
        return [c.label(f"{table.name}_{c.name}") for c in table.columns]

    async def get(self, db_conn: AsyncConnection, obj_id: UUID) -> DBSchemaTypeT | None:
        stmt = self.table.select().where(self.table.c.id == obj_id)
        row = (await db_conn.execute(stmt)).one_or_none()
        return self.db_scheme.from_orm(row) if row else None

    async def get_many(
        self, db_conn: AsyncConnection, *, skip: int = 0, limit: int = 100
    ) -> list[DBSchemaTypeT]:
        stmt = self.table.select().offset(skip).limit(limit)
        rows = await db_conn.execute(stmt)
        return [self.db_scheme.from_orm(row) for row in rows]

    async def get_in(
        self, db_conn: AsyncConnection, obj_ids: list[UUID]
    ) -> list[DBSchemaTypeT]:
        stmt = self.table.select().where(self.table.c.id.in_(obj_ids))
        rows = await db_conn.execute(stmt)
        return [self.db_scheme.from_orm(row) for row in rows]

    async def get_by_local_keys(
        self, db_conn: AsyncConnection, local_id, country: CountryCode
    ) -> DBSchemaTypeT | None:
        stmt = self.table.select().where(
            sa_and(
                self.local_id_column == local_id,
                self.table.c.country == country,
            )
        )
        row = (await db_conn.execute(stmt)).one_or_none()
        return self.db_scheme.from_orm(row) if row else None

    async def get_local_key_mapping(
        self, db_conn: AsyncConnection, local_keys: list[tuple[str, CountryCode]]
    ) -> dict[tuple[str, CountryCode], UUID]:
        stmt = sa_text(
            """
            SELECT id, {table}.{local_id}, {table}.country
            FROM {table}
            JOIN (
                SELECT
                    (value->>0)::varchar AS {local_id},
                    (value->>1)::varchar AS country
                FROM json_array_elements(:json_data)
            ) local_ids
            ON {table}.{local_id} = local_ids.{local_id}
            AND {table}.country = local_ids.country
        """.format(
                table=self.table.name,
                local_id=self.local_id_column.name,  # type: ignore[union-attr]
            )
        ).bindparams(bindparam("json_data", value=local_keys, type_=JSON))

        res = await db_conn.execute(stmt)
        local_key_mapping = {(r[1], CountryCode(r[2])): r[0] for r in res}
        return local_key_mapping

    async def find_existing_ids(
        self, db_conn: AsyncConnection, uuids: list[UUID]
    ) -> set[UUID]:
        stmt = self.table.select().where(self.table.c.id.in_(uuids))
        res = await db_conn.execute(stmt)
        return {r.id for r in res}

    async def create(
        self, db_conn: AsyncConnection, obj_in: CreateSchemaTypeT
    ) -> DBSchemaTypeT:
        values = jsonable_encoder(obj_in, custom_encoder=self.custom_encoder)
        values["created_at"] = utc_now()
        if self.has_updated_at:
            values["updated_at"] = values["created_at"]

        stmt = self.table.insert().values(**values).returning(self.table)
        row = (await db_conn.execute(stmt)).one()
        return self.db_scheme.from_orm(row)

    async def create_many(
        self, db_conn: AsyncConnection, objs_in: list[CreateSchemaTypeT]
    ) -> None:
        now = utc_now()
        all_values = [
            jsonable_encoder(obj_in, custom_encoder=self.custom_encoder)
            for obj_in in objs_in
        ]
        for values in all_values:
            values["created_at"] = now
            if self.has_updated_at:
                values["updated_at"] = now

        stmt = self.table.insert().values(all_values)
        await db_conn.execute(stmt)

    async def update(
        self, db_conn: AsyncConnection, obj_in: UpdateSchemaTypeT
    ) -> DBSchemaTypeT:
        values = jsonable_encoder(
            obj_in,
            exclude={"id", self.local_id_column},  # type: ignore[arg-type]
            exclude_unset=True,
            custom_encoder=self.custom_encoder,
        )
        stmt = (
            self.table.update()
            .values({**values, "updated_at": utc_now()})
            .where(self.table.c.id == obj_in.id)  # type: ignore[attr-defined]
            .returning(self.table)
        )
        row = (await db_conn.execute(stmt)).one()
        return self.db_scheme.from_orm(row)

    async def create_or_update_many(self, db_conn: AsyncConnection) -> None:
        pass

    async def create_many_or_do_nothing(  # type: ignore[empty-body]
        self, db_conn: AsyncConnection, entities: list[CreateSchemaTypeT]
    ) -> list[UUID]:
        pass

    async def update_many(  # type: ignore[empty-body]
        self, db_conn: AsyncConnection, entities: list[UpdateSchemaTypeT]
    ) -> list[UUID]:
        pass

    async def remove(
        self, db_conn: AsyncConnection, db_obj: DBSchemaTypeT
    ) -> UUID | None:
        return await self.remove_by_id(db_conn, db_obj.id)  # type: ignore[attr-defined]

    async def remove_by_id(self, db_conn: AsyncConnection, obj_id: UUID) -> UUID | None:
        stmt = (
            self.table.delete()
            .where(self.table.c.id == obj_id)
            .returning(self.table.c.id)
        )
        res = (await db_conn.execute(stmt)).scalar()
        return res

    async def remove_many_with_version_checking(
        self, db_conn: AsyncConnection, ids_versions: list[tuple[UUID, int]]
    ) -> list[UUID]:
        ids_versions.sort(key=lambda item: item[0])
        json_data = dump_to_json(ids_versions)

        stmt = sa_text(
            """
            WITH q AS (
              SELECT (value->>0)::uuid AS id, (value->>1)::bigint AS version
              FROM json_array_elements('{json_data}')
            )
            DELETE FROM {table}
            USING q
            WHERE {table}.id = q.id AND {table}.version < q.version
            RETURNING {table}.id
            """.format(
                table=self.table.name, json_data=json_data
            )
        )
        res = await db_conn.execute(stmt)
        deleted_ids = [r.id for r in res]
        return deleted_ids

    @staticmethod
    def sort_entities_by_id(
        entities: list[CreateSchemaTypeT] | list[UpdateSchemaTypeT],
    ) -> None:
        entities.sort(key=lambda e: e.id)  # type: ignore[attr-defined]
