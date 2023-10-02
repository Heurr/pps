from logging import getLogger
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from app.crud.base import (
    CreateSchemaTypeT,
    CRUDBase,
    DBSchemaTypeT,
    UpdateSchemaTypeT,
)
from app.exceptions import EntityNotFoundError

CRUDTypeT = TypeVar("CRUDTypeT", bound=CRUDBase)
RabbitMessageSchemeT = TypeVar("RabbitMessageSchemeT", bound=BaseModel)


class BaseService(
    Generic[
        CRUDTypeT,
        DBSchemaTypeT,
    ]
):
    def __init__(self, crud_: CRUDTypeT, entity_name: str, logger_name: str):
        self.crud = crud_
        self.entity_name = entity_name
        self.logger = getLogger(logger_name)

    async def get(self, db_conn: AsyncConnection, obj_id: UUID) -> DBSchemaTypeT | None:
        return await self.crud.get(db_conn, obj_id)

    async def get_many(
        self, db_conn: AsyncConnection, skip: int = 0, limit: int = 100
    ) -> list[DBSchemaTypeT]:
        return await self.crud.get_many(db_conn, skip=skip, limit=limit)

    async def get_in(
        self, db_conn: AsyncConnection, obj_ids: list[UUID]
    ) -> list[DBSchemaTypeT]:
        return await self.crud.get_in(db_conn, obj_ids)

    async def create(
        self, db_conn: AsyncConnection, obj_in: CreateSchemaTypeT
    ) -> DBSchemaTypeT:
        return await self.crud.create(db_conn, obj_in)

    async def update(
        self, db_conn: AsyncConnection, obj_in: UpdateSchemaTypeT
    ) -> DBSchemaTypeT:
        return await self.crud.update(db_conn, obj_in)

    async def remove(
        self, db_conn: AsyncConnection, db_obj: DBSchemaTypeT
    ) -> UUID | None:
        return await self.crud.remove(db_conn, db_obj)

    async def remove_or_not_found(self, db_conn: AsyncConnection, obj_id: UUID) -> UUID:
        res_id = await self.crud.remove_by_id(db_conn, obj_id)
        if res_id is None:
            raise EntityNotFoundError(
                f"{self.entity_name} with id '{obj_id}' could not be deleted. "
                f"{self.entity_name} does not exist."
            )
        return res_id
