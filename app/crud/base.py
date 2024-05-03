import logging
from typing import Generic, Type, TypeVar
from uuid import UUID

from asyncpg.exceptions import (
    DataError,
    InterfaceError,
    TransactionRollbackError,
)
from sqlalchemy import Table
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.schemas.base import EntityModel
from app.utils import dump_to_json, utc_now
from app.utils.sentry import set_sentry_context

DBSchemaTypeT = TypeVar("DBSchemaTypeT", bound=EntityModel)
CreateSchemaTypeT = TypeVar("CreateSchemaTypeT", bound=EntityModel)


class CRUDBase(Generic[DBSchemaTypeT, CreateSchemaTypeT]):
    def __init__(
        self,
        table: Table,
        db_scheme: Type[DBSchemaTypeT],
        updatable_columns: list[str],
    ):
        self.table = table
        self.db_scheme = db_scheme
        self.has_updated_at = "updated_at" in self.table.c
        self.updatable_columns = updatable_columns
        self.logger = logging.getLogger(__name__)

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

    async def create_many(
        self, db_conn: AsyncConnection, objs_in: list[CreateSchemaTypeT]
    ) -> list[DBSchemaTypeT]:
        """
        Create many rows using provided object, used only for tests

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

        stmt = self.table.insert().values(all_values).returning(self.table)
        rows = (await db_conn.execute(stmt)).fetchall()
        return [self.db_scheme.model_validate(row) for row in rows]

    async def _do_upsert_many(
        self,
        db_conn: AsyncConnection,
        cols_to_update_on_conflict: list[str],
        values: list[dict],
    ) -> list[UUID]:
        # Sort before upserting to avoid conflicts
        values.sort(key=lambda x: x["id"])

        stmt = insert(self.table).values(values)
        on_conflict_stmt = stmt.on_conflict_do_update(
            index_elements=self.table.primary_key.columns,
            # When updating, do only for specified columns
            set_={k: getattr(stmt.excluded, k) for k in cols_to_update_on_conflict},
        ).returning(self.table.c.id)

        try:
            res = await db_conn.execute(on_conflict_stmt)
        except (InterfaceError, TransactionRollbackError, DataError) as err:
            self.logger.error("Query raised error: %s\n%s", stmt, values)
            set_sentry_context("pg", {"stmt": stmt, "values": values})
            raise err

        upserted_ids = [i[0] for i in res.fetchall()]
        return upserted_ids

    async def upsert_many(
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
        now = utc_now()
        values = [
            {**e.model_dump(), "created_at": now, "updated_at": now} for e in entities
        ]
        return await self._do_upsert_many(db_conn, self.updatable_columns, values)

    async def remove_many(
        self, db_conn: AsyncConnection, ids_versions: list[tuple[UUID, int]]
    ) -> list[UUID]:
        """
        Delete rows with given IDs.

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
            WHERE {table}.id = q.id
            RETURNING {table}.id
            """.format(
                table=self.table.name, json_data=json_data
            )
        )
        res = await db_conn.execute(stmt)
        deleted_ids = [r.id for r in res]
        return deleted_ids
