from logging import getLogger
from typing import Generic, TypeVar
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncConnection

from app.config.settings import ServiceSettings
from app.constants import PRICE_EVENT_QUEUE, Entity
from app.crud import crud_from_entity
from app.crud.base import CreateSchemaTypeT, CRUDBase, DBSchemaTypeT
from app.metrics import UPDATE_METRICS
from app.schemas.price_event import EntityUpdate, PriceEvent
from app.utils import dump_to_json

CRUDTypeT = TypeVar("CRUDTypeT", bound=CRUDBase)


class BaseEntityService(
    Generic[
        DBSchemaTypeT,
        CreateSchemaTypeT,
    ]
):
    def __init__(self, entity: Entity):
        self.crud = crud_from_entity(entity)
        self.entity = entity
        self.logger = getLogger(self.__class__.__name__)
        self.force_entity_update = ServiceSettings().FORCE_ENTITY_UPDATE

    async def get_many(self, db_conn: AsyncConnection, skip: int = 0, limit: int = 100):
        return await self.crud.get_many(db_conn, skip=skip, limit=limit)

    async def get_many_by_ids(
        self, db_conn: AsyncConnection, obj_ids: list[UUID]
    ) -> list[DBSchemaTypeT]:
        return await self.crud.get_in(db_conn, obj_ids)

    async def upsert_many(
        self, db_conn: AsyncConnection, redis: Redis, msgs: list[CreateSchemaTypeT]
    ) -> list[UUID]:
        if not msgs:
            return []
        msg_map = {msg.id: msg for msg in msgs}
        objs_from_db = {
            i.id: i for i in await self.crud.get_in(db_conn, list(msg_map.keys()))
        }
        objs_to_upsert: list[CreateSchemaTypeT] = []
        updated_entities: list[EntityUpdate[DBSchemaTypeT, CreateSchemaTypeT]] = []

        for incoming_msg_id, incoming_msg in msg_map.items():
            obj_from_db = objs_from_db.get(incoming_msg_id)
            if self.should_be_updated(obj_from_db, incoming_msg):
                objs_to_upsert.append(incoming_msg)
                updated_entities.append(EntityUpdate(old=obj_from_db, new=incoming_msg))

        upserted_ids = await self.crud.upsert_many(db_conn, objs_to_upsert)
        price_events = await self.generate_price_events(db_conn, updated_entities)
        await self.send_price_events(redis, price_events)
        return upserted_ids

    def should_be_updated(
        self, obj_in: DBSchemaTypeT | None, msg_in: CreateSchemaTypeT
    ) -> bool:
        if obj_in is None:
            return True

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
        self, db_conn: AsyncConnection, redis: Redis, ids_versions: list[tuple[UUID, int]]
    ) -> list[UUID]:
        old_entities = await self.crud.get_in(db_conn, [idv[0] for idv in ids_versions])
        deleted_ids = await self.crud.remove_many_with_version_checking(
            db_conn, ids_versions
        )
        deleted_ids_set = set(deleted_ids)
        price_events = await self.generate_price_events(
            db_conn,
            [
                EntityUpdate(new=None, old=e)
                for e in old_entities
                if e.id in deleted_ids_set
            ],
        )
        await self.send_price_events(redis, price_events)
        return deleted_ids

    async def generate_price_events(
        self,
        _db_conn: AsyncConnection,
        _entities: list[EntityUpdate[DBSchemaTypeT, CreateSchemaTypeT]],
    ) -> list[PriceEvent]:
        """Override to generate appropriate price events for the given entity upserts/deletes"""
        return []

    async def send_price_events(self, redis: Redis, events: list[PriceEvent]):
        if events:
            events_json = [dump_to_json(e) for e in events]
            await redis.lpush(PRICE_EVENT_QUEUE, *events_json)
            self.logger.info("%i price events sent", len(events_json))
