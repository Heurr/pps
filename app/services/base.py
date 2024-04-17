from logging import getLogger
from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from app.constants import Entity
from app.crud.base import (
    CreateSchemaTypeT,
    CRUDBase,
    DBSchemaTypeT,
)

CRUDTypeT = TypeVar("CRUDTypeT", bound=CRUDBase)


class BaseMessageService(
    Generic[
        CRUDTypeT,
        DBSchemaTypeT,
        CreateSchemaTypeT,
    ]
):
    def __init__(
        self,
        crud: CRUDTypeT,
        entity: Entity,
        create_schema: Type[CreateSchemaTypeT],
    ):
        self.crud = crud
        self.entity = entity
        self.create_schema = create_schema
        self.logger = getLogger(self.__class__.__name__)

    async def get_many(
        self, db_conn: AsyncConnection, skip: int = 0, limit: int = 100
    ) -> list[DBSchemaTypeT]:
        return await self.crud.get_many(db_conn, skip=skip, limit=limit)

    async def get_many_by_ids(
        self, db_conn: AsyncConnection, obj_ids: list[UUID]
    ) -> list[DBSchemaTypeT]:
        return await self.crud.get_in(db_conn, obj_ids)

    async def upsert_many(
        self, db_conn: AsyncConnection, msgs: list[CreateSchemaTypeT]
    ) -> list[UUID]:
        objs_to_upsert = [self.create_schema(**msg.model_dump()) for msg in msgs]
        return await self.crud.upsert_many(db_conn, objs_to_upsert)

    async def remove_many(
        self, db_conn: AsyncConnection, ids_versions: list[tuple[UUID, int]]
    ) -> list[UUID]:
        return await self.crud.remove_many_with_version_checking(db_conn, ids_versions)
