from logging import getLogger
from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from app.config.settings import ServiceSettings
from app.constants import Entity
from app.crud.base import CreateSchemaTypeT, CRUDBase, DBSchemaTypeT
from app.metrics import UPDATE_METRICS

CRUDTypeT = TypeVar("CRUDTypeT", bound=CRUDBase)


class BaseEntityService(
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
        self.force_entity_update = ServiceSettings().FORCE_ENTITY_UPDATE

    async def get_many(self, db_conn: AsyncConnection, skip: int = 0, limit: int = 100):
        return await self.crud.get_many(db_conn, skip=skip, limit=limit)

    async def get_many_by_ids(
        self, db_conn: AsyncConnection, obj_ids: list[UUID]
    ) -> list[DBSchemaTypeT]:
        return await self.crud.get_in(db_conn, obj_ids)

    async def upsert_many(
        self, db_conn: AsyncConnection, msgs: list[CreateSchemaTypeT]
    ) -> list[UUID]:
        if not msgs:
            return []
        msg_map = {msg.id: msg for msg in msgs}
        objs_from_db = {
            i.id: i for i in await self.crud.get_in(db_conn, list(msg_map.keys()))
        }
        objs_to_upsert: list[CreateSchemaTypeT] = []

        for incoming_msg_id, incoming_msg in msg_map.items():
            obj_from_db = objs_from_db.get(incoming_msg_id)
            if obj_from_db is None or self.should_be_updated(obj_from_db, incoming_msg):
                objs_to_upsert.append(self.create_schema(**incoming_msg.model_dump()))

        objs_to_upsert = [
            self.create_schema(**objs.model_dump()) for objs in objs_to_upsert
        ]
        return await self.crud.upsert_many(db_conn, objs_to_upsert)

    def should_be_updated(self, obj_in: DBSchemaTypeT, msg_in: CreateSchemaTypeT) -> bool:
        is_newer = msg_in >= obj_in
        if is_newer:
            UPDATE_METRICS.labels(update_type="forced", entity=self.entity.value).inc()
            if self.force_entity_update:
                return is_newer

        compared_fields = obj_in.model_fields.keys() & msg_in.model_fields.keys() - {
            "version"
        }
        _should_be_updated = is_newer and obj_in.model_dump(
            include=compared_fields
        ) != msg_in.model_dump(include=compared_fields)
        if _should_be_updated:
            UPDATE_METRICS.labels(update_type="standard", entity=self.entity.value).inc()
        return _should_be_updated

    async def remove_many(
        self, db_conn: AsyncConnection, ids_versions: list[tuple[UUID, int]]
    ) -> list[UUID]:
        return await self.crud.remove_many_with_version_checking(db_conn, ids_versions)
