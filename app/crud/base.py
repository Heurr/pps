from typing import Generic, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Table
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql.elements import Label

from app.utils import dump_to_json, utc_now

DBSchemaTypeT = TypeVar("DBSchemaTypeT", bound=BaseModel)
CreateSchemaTypeT = TypeVar("CreateSchemaTypeT", bound=BaseModel)


class CRUDBase(Generic[DBSchemaTypeT, CreateSchemaTypeT]):
    def __init__(
        self,
        table: Table,
        db_scheme: Type[DBSchemaTypeT],
        create_scheme: Type[CreateSchemaTypeT],
    ):
        self.table = table
        self.db_scheme = db_scheme
        self.create_scheme = create_scheme
        self.has_updated_at = "updated_at" in self.table.c

    @staticmethod
    def prefixed_columns(table: Table) -> list[Label]:
        return [c.label(f"{table.name}_{c.name}") for c in table.columns]

    async def get(self, db_conn: AsyncConnection, obj_id: UUID) -> DBSchemaTypeT | None:
        """
        Get one row table

        :param db_conn: Database connection
        :param obj_id: ID of primary keys of the object to get
        :return: If found the object corresponding to the id, else nothing
        """
        stmt = self.table.select().where(self.table.c.id == obj_id)
        row = (await db_conn.execute(stmt)).one_or_none()
        return self.db_scheme.model_validate(row) if row else None

    async def get_many(
        self, db_conn: AsyncConnection, *, skip: int = 0, limit: int = 100
    ) -> list[DBSchemaTypeT]:
        """
        Get many rows from db based on limit and offset

        :param db_conn: Database connection
        :param skip: Offset
        :param limit: Limit to return
        :return: List of rows
        """
        stmt = self.table.select().offset(skip).limit(limit)
        rows = await db_conn.execute(stmt)
        return [self.db_scheme.model_validate(row) for row in rows]

    async def get_in(
        self, db_conn: AsyncConnection, obj_ids: list[UUID]
    ) -> list[DBSchemaTypeT]:
        """
        Get all rows matching provided ids

        :param db_conn: Database connection
        :param obj_ids: List of UUIDs to get
        :return: List of rows
        """
        stmt = self.table.select().where(self.table.c.id.in_(obj_ids))
        rows = await db_conn.execute(stmt)
        return [self.db_scheme.model_validate(row) for row in rows]

    async def find_existing_ids(
        self, db_conn: AsyncConnection, pks: list[UUID]
    ) -> set[UUID]:
        """
        Get IDs of rows that match provided IDs

        :param db_conn: Database connection
        :param pks: UUIDs to find
        :return: A subset of provided IDs that were found in db
        """
        stmt = self.table.select().where(self.table.c.id.in_(pks))
        res = await db_conn.execute(stmt)
        return {r.id for r in res}

    async def create(
        self, db_conn: AsyncConnection, obj_in: CreateSchemaTypeT
    ) -> DBSchemaTypeT:
        """
        Create one row using provided object

        :param db_conn: Database connection
        :param obj_in: Object to create
        :return: Created object
        """
        values = obj_in.model_dump()

        values["created_at"] = utc_now()
        if self.has_updated_at:
            values["updated_at"] = values["created_at"]

        stmt = self.table.insert().values(**values).returning(self.table)
        row = (await db_conn.execute(stmt)).one()
        return self.db_scheme.model_validate(row)

    async def create_many(
        self, db_conn: AsyncConnection, objs_in: list[CreateSchemaTypeT]
    ) -> None:
        """
        Create many rows using provided object

        :param db_conn: Database connection
        :param objs_in: Objects to create
        :return: Nothing
        """
        now = utc_now()
        all_values = [{**obj_in.model_dump(), "created_at": now} for obj_in in objs_in]

        for values in all_values:
            values["created_at"] = now
            if self.has_updated_at:
                values["updated_at"] = now

        stmt = self.table.insert().values(all_values)
        await db_conn.execute(stmt)

    async def upsert_many_with_version_checking(  # type: ignore[empty-body]
        self,
        db_conn: AsyncConnection,
        entities: list[CreateSchemaTypeT],
    ) -> list[UUID]:
        """
        Create many rows using Common Table Expression (CTE) or update while version checking
        specific for each CRUD

        :param db_conn: Database connection
        :param entities: List of entities to be upserted
        :return: List of primary keys, can return tuples if table has composite primary key
        """

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
        """
        Only remove rows with version bigger then old version

        :param db_conn: Database connection
        :param ids_versions: Tuple of primary keys and versions corresponding to the primary key
        :return: IDs of deleted rows
        """
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

    async def upsert_many(  # type: ignore[empty-body]
        self, db_conn: AsyncConnection, entities: list[CreateSchemaTypeT]
    ) -> list[UUID]:
        # TODO logic that samo does
        pass
