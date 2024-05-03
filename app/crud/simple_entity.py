from typing import Generic, Type
from uuid import UUID

from sqlalchemy import Table
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.constants import (
    ENTITY_DATA_COLUMNS,
    ENTITY_VERSION_COLUMNS,
    Entity,
)
from app.crud.base import CreateSchemaTypeT, CRUDBase, DBSchemaTypeT
from app.utils import dump_to_json


class CRUDSimpleEntityBase(
    CRUDBase[DBSchemaTypeT, CreateSchemaTypeT], Generic[DBSchemaTypeT, CreateSchemaTypeT]
):
    """CRUD for entities without table, corresponding to one column only"""

    def __init__(
        self,
        table: Table,
        db_scheme: Type[DBSchemaTypeT],
        entity: Entity,
    ):
        super().__init__(table, db_scheme, [])
        self.column = ENTITY_DATA_COLUMNS[entity]
        self.version_column = ENTITY_VERSION_COLUMNS[entity]
        self.db_column_type = table.columns[self.column].type

    async def upsert_many(
        self, db_conn: AsyncConnection, entities: list[CreateSchemaTypeT]
    ) -> list[UUID]:
        """
        Update column value for all entities with given IDs.
        """
        entities.sort(key=lambda e: e.id)
        json_data = dump_to_json(
            [(e.id, getattr(e, self.column), e.version) for e in entities]
        )

        stmt = sa_text(
            """
            WITH q AS (
              SELECT (value->>0)::uuid AS id, (value->>1)::{db_column_type} AS value, (value->>2)::bigint AS version
              FROM json_array_elements('{json_data}')
            )
            UPDATE {table}
            SET {column} = q.value, {version_column} = q.version
            FROM q
            WHERE {table}.id = q.id
            RETURNING {table}.id
            """.format(
                table=self.table.name,
                column=self.column,
                db_column_type=self.db_column_type,
                version_column=self.version_column,
                json_data=json_data,
            )
        )
        res = await db_conn.execute(stmt)
        updated_ids = [r.id for r in res]
        return updated_ids

    async def remove_many(
        self, db_conn: AsyncConnection, ids_versions: list[tuple[UUID, int]]
    ) -> list[UUID]:
        """
        Set column value to NULL for all entities with given IDs.
        """
        ids_versions.sort(key=lambda item: item[0])
        json_data = dump_to_json(ids_versions)

        stmt = sa_text(
            """
            WITH q AS (
              SELECT (value->>0)::uuid AS id, (value->>1)::bigint AS version
              FROM json_array_elements('{json_data}')
            )
            UPDATE {table} SET {column} = NULL, {version_column} = q.version
            FROM q
            WHERE {table}.id = q.id
            RETURNING {table}.id
            """.format(
                table=self.table.name,
                column=self.column,
                version_column=self.version_column,
                json_data=json_data,
            )
        )
        res = await db_conn.execute(stmt)
        deleted_ids = [r.id for r in res]
        return deleted_ids
