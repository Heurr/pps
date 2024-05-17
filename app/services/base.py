from logging import getLogger
from typing import Generic, TypeVar
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncConnection

from app.config.settings import ServiceSettings
from app.constants import ENTITY_VERSION_COLUMNS, PRICE_EVENT_QUEUE, Entity
from app.crud import crud_from_entity
from app.crud.base import CreateSchemaTypeT, CRUDBase, DBSchemaTypeT
from app.metrics import UPDATE_METRICS
from app.schemas.price_event import PriceEvent
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
        price_events: list[PriceEvent] = []

        for incoming_msg_id, incoming_msg in msg_map.items():
            obj_from_db = objs_from_db.get(incoming_msg_id)
            if self.should_be_updated(obj_from_db, incoming_msg):
                if obj_from_db is None:
                    price_events.extend(
                        await self.generate_price_events_for_new(db_conn, incoming_msg)
                    )
                else:
                    price_events.extend(
                        await self.generate_price_events_for_updated(
                            db_conn, obj_from_db, incoming_msg
                        )
                    )
                objs_to_upsert.append(incoming_msg)

        if not objs_to_upsert:
            return []

        upserted_ids = await self.crud.upsert_many(db_conn, objs_to_upsert)
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
                return True

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
        self,
        db_conn: AsyncConnection,
        redis: Redis,
        ids_versions: list[tuple[UUID, int]],
    ) -> list[UUID]:
        if not ids_versions:
            return []
        old_entities = await self.crud.get_in(db_conn, [idv[0] for idv in ids_versions])
        version_column = ENTITY_VERSION_COLUMNS.get(self.entity, "version")
        versions = {e.id: getattr(e, version_column) for e in old_entities}
        ids_versions_newer = [
            idv
            for idv in ids_versions
            if idv[0] in versions and idv[1] >= versions[idv[0]]
        ]

        deleted_ids = await self.crud.remove_many(db_conn, ids_versions_newer)
        deleted_ids_set = set(deleted_ids)
        old_entities = [e for e in old_entities if e.id in deleted_ids_set]

        price_events = []
        for old_entity in old_entities:
            price_events.extend(
                await self.generate_price_events_for_delete(db_conn, old_entity)
            )
        await self.send_price_events(redis, price_events)
        return deleted_ids

    async def generate_price_events_for_new(
        self, db_conn: AsyncConnection, new_entity: CreateSchemaTypeT
    ) -> list[PriceEvent]:
        """
        Generate price events for entity that are new. Because Availability and Buyable
        entities are part of Offer entity/table their first incoming messages
        should not be considered as new events.

        :param db_conn: It is only needed to generate price events related to shop changes.
        :param new_entity: Create schemas of new entity.
        """
        raise NotImplementedError()

    async def generate_price_events_for_updated(
        self,
        db_conn: AsyncConnection,
        orig_db_entity: DBSchemaTypeT,
        new_entity: CreateSchemaTypeT,
    ) -> list[PriceEvent]:
        """
        Generate price events for entity that was changed.
        It requires both original db record and a new create schema.

        :param db_conn: It is only needed to generate price events related to shop changes.
        :param new_entity: Create schemas of new entity.
        :param orig_db_entity: Original db entity, usually OfferDB.
        """
        raise NotImplementedError()

    async def generate_price_events_for_delete(
        self, db_conn: AsyncConnection, orig_db_entity: DBSchemaTypeT
    ) -> list[PriceEvent]:
        """
        Generate price event for entity that was deleted.
        Only original db entity is needed.

        :param db_conn: It is only needed to generate price events related to shop changes.
        :param orig_db_entity: Original db entity, usually OfferDB.
        """
        raise NotImplementedError()

    async def send_price_events(self, redis: Redis, events: list[PriceEvent]):
        if events:
            events_json = [dump_to_json(e) for e in events]
            await redis.lpush(PRICE_EVENT_QUEUE, *events_json)
            self.logger.info("%i price events sent", len(events_json))
