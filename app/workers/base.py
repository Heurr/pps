import asyncio
import signal
from contextlib import asynccontextmanager
from dataclasses import dataclass
from logging import getLogger
from typing import Any, Generator, Generic, Type, TypeVar
from uuid import UUID

import orjson
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app.config.settings import WorkerSetting
from app.constants import Action, Entity
from app.exceptions import (
    WorkerError,
    WorkerFailedParseMsgError,
)
from app.metrics import ENTITY_METRICS
from app.parsers import parser_from_entity
from app.schemas.base import MessageModel
from app.services import service_from_entity

MessageSchemaT = TypeVar("MessageSchemaT", bound=MessageModel)


@dataclass
class Message:
    identifier: UUID
    version: int
    body: dict[str, Any]
    action: Action


class Metrics:
    def __init__(self, entity: Entity):
        self.read_entities = ENTITY_METRICS.labels(
            entity=entity.value, phase="worker", operation="read"
        )  # Entities read from Redis
        self.filtered_entities = ENTITY_METRICS.labels(
            entity=entity.value, phase="worker", operation="filtered"
        )  # Entities filtered by country code
        self.created_entities = ENTITY_METRICS.labels(
            entity=entity.value, phase="worker", operation="create"
        )  # Entities created in DB
        self.updated_entities = ENTITY_METRICS.labels(
            entity=entity.value, phase="worker", operation="update"
        )  # Entities updated in DB
        self.deleted_entities = ENTITY_METRICS.labels(
            entity=entity.value, phase="worker", operation="delete"
        )  # Entities deleted in DB
        self.not_found_entities = ENTITY_METRICS.labels(
            entity=entity.value, phase="worker", operation="not_found"
        )  # Entities with missing referenced entity (for UPSERT messages)
        # or with missing ID (for DELETE messages)
        self.invalid_entities = ENTITY_METRICS.labels(
            entity=entity.value, phase="worker", operation="invalid"
        )  # Entities not parsed


class BaseMessageWorker(Generic[MessageSchemaT]):
    def __init__(  # noqa
        self,
        entity: Entity,
        settings: WorkerSetting,
        db_engine: AsyncEngine,
        redis: Redis,
        message_schema: Type[MessageSchemaT],
    ):
        self.messages_buffer: dict[UUID, Message] = {}
        self.message_schema = message_schema
        self.should_consume = True

        self.entity = entity
        self.db_engine = db_engine
        self.redis = redis
        self.service = service_from_entity(entity)
        self.parser = parser_from_entity(entity, throw_errors=True)

        self.buffer_size = settings.WORKER_BUFFER_SIZE
        self.redis_pop_timeout = settings.WORKER_POP_TIMEOUT
        self.message_log_interval = settings.WORKER_MESSAGE_LOG_INTERVAL

        self.metrics = Metrics(entity)
        self._logger = getLogger(__name__)
        self._register_signals()

    def is_desired_message(self, _message: MessageSchemaT) -> bool:
        """
        Override this method if you want to filter out any messages before they are
        upserted to the database
        """
        return True

    def to_message_schema(self, message: Message) -> MessageSchemaT:
        """
        Will convert a Message into a EntityMessageSchema
        """
        return self.message_schema(**message.body)

    def to_create_schema(self, message: MessageSchemaT):
        """
        Implement for every worker, will convert EntityMessageSchema to
        EntityCreateSchema which is used for upserting into the DB
        """
        raise NotImplementedError("Not implemented")

    @asynccontextmanager
    async def get_db_conn(self):
        async with self.db_engine.connect() as conn:
            await conn.execution_options(isolation_level="AUTOCOMMIT")
            yield conn

    async def consume_and_process_messages(self) -> None:
        if self.redis is None:
            raise WorkerError("Redis in worker is not connected.")

        redis_list = f"rmq-{self.entity.value}"
        self._logger.info(
            "Start consuming %ss from redis queue %s.", self.entity.value, redis_list
        )

        counter = 0
        while self.should_consume:
            res = await self.redis.brpop(
                keys=[redis_list], timeout=self.redis_pop_timeout
            )
            if res is None:
                await self.process_messages_in_buffer_bulk()
                continue

            _, msg = res
            msgs = await self.redis.rpop(redis_list, count=self.buffer_size)
            msgs = [msg] if msgs is None else [msg, *msgs]

            self.metrics.read_entities.inc(len(msgs))

            counter += len(msgs)
            if counter >= self.message_log_interval:
                self._logger.info("Message sample:\n%s", msgs[0])
                counter = 0

            await self.append_messages_to_buffer(msgs)
            if len(self.messages_buffer) >= self.buffer_size:
                await self.process_messages_in_buffer_bulk()

        self._logger.info("Stop consuming %ss", self.entity.value)

    async def append_messages_to_buffer(self, redis_messages: list[str]) -> None:
        self._logger.debug('Receive redis messages "%s"', redis_messages)

        for redis_msg in redis_messages:
            try:
                msg = self.parse_redis_message(redis_msg)
            except WorkerFailedParseMsgError as exc:
                self._logger.error(
                    "Failed to parse incoming redis message: %s, due to: %s.",
                    redis_msg,
                    str(exc),
                )
                self.metrics.invalid_entities.inc()
                return

            if (
                msg.identifier in self.messages_buffer
                and self.messages_buffer[msg.identifier].version < msg.version  # noqa
            ):
                self.messages_buffer.pop(msg.identifier)

            self.messages_buffer[msg.identifier] = msg

    @staticmethod
    def batched(
        msgs: list[Message], batch_size: int
    ) -> Generator[list[Message], None, None]:
        for i in range(0, len(msgs), batch_size):
            yield msgs[i + i : batch_size]

    async def process_messages_in_buffer_bulk(self) -> None:
        if not self.messages_buffer:
            return

        upsert_messages = []
        delete_messages = []
        for msg in self.messages_buffer.values():
            if msg.action == Action.DELETE:
                delete_messages.append(msg)
            else:
                upsert_messages.append(msg)

        if upsert_messages:
            async with self.get_db_conn() as db_conn:
                for batch in self.batched(upsert_messages, self.buffer_size):
                    await self.process_many_create_update_messages(db_conn, batch)

        if delete_messages:
            async with self.get_db_conn() as db_conn:
                for batch in self.batched(delete_messages, self.buffer_size):
                    await self.process_many_delete_messages(db_conn, batch)

        self.messages_buffer.clear()

    def parse_redis_message(self, redis_message: str) -> Message:
        try:
            msg_body = orjson.loads(redis_message)
        except orjson.JSONDecodeError as exc:
            raise WorkerFailedParseMsgError from exc
        if not isinstance(msg_body, dict):
            raise WorkerFailedParseMsgError("Message body is not json dict object.")

        return Message(
            identifier=self.parser.get_message_id(msg_body),
            version=self.parser.get_version(msg_body),
            action=Action(self.parser.get_action(msg_body)),
            body=msg_body,
        )

    def to_message_schemas(self, messages: list[Message]) -> list:
        msgs_in = []
        for msg in messages:
            try:
                parsed_msg = self.to_message_schema(msg)
                msgs_in.append(parsed_msg)
            except Exception as exc:  # noqa: PERF203
                self._logger.warning(
                    "Failed parsing %s message: %s. Message body: %s.",
                    self.entity.value,
                    str(exc),
                    msg.body,
                )
                self.metrics.invalid_entities.inc()

        return msgs_in

    def to_create_schemas(self, messages: list[MessageSchemaT]) -> list:
        data_in = []
        for msg in messages:
            try:
                data = self.to_create_schema(msg)
                data_in.append(data)
            except Exception as exc:  # noqa: PERF203
                self._logger.warning(
                    "Failed parsing %s message: %s. Message body: %s.",
                    self.entity.value,
                    str(exc),
                    msg,
                )
                self.metrics.invalid_entities.inc()

        return data_in

    async def process_many_create_update_messages(
        self, db_conn: AsyncConnection, messages: list[Message]
    ) -> None:
        try:
            msgs_in = self.to_message_schemas(messages)

            msgs_in = [msg for msg in msgs_in if self.is_desired_message(msg)]
            filtered_out_msgs_len = len(messages) - len(msgs_in)
            if filtered_out_msgs_len != 0:
                self._logger.info("Filtered out %s messages", filtered_out_msgs_len)
            self.metrics.filtered_entities.inc(len(msgs_in))

            data_in = self.to_create_schemas(msgs_in)

            self._logger.debug("Messages: %s", data_in)
            upserted_ids = await self.service.upsert_many(db_conn, data_in)
            self._logger.info(
                "Successfully upserted %i %ss.",
                len(upserted_ids),
                self.entity.value,
            )

            self.metrics.updated_entities.inc(len(upserted_ids))
        except Exception as exc:
            self._logger.error(
                "Error in process many create update %s messages: %s",
                self.entity.value,
                str(exc),
            )

    async def process_many_delete_messages(
        self, db_conn: AsyncConnection, messages: list[Message]
    ) -> None:
        ids_versions = [(msg.identifier, msg.version) for msg in messages]
        self._logger.debug("ids versions: %s", ids_versions)
        deleted_ids = await self.service.remove_many(db_conn, ids_versions)
        self._logger.info(
            "Successfully delete %i %ss.", len(deleted_ids), self.entity.value
        )
        self.metrics.deleted_entities.inc(len(deleted_ids))

    def stop_consuming(self) -> None:
        self.should_consume = False

    def _register_signals(self) -> None:
        """Graceful stopping consuming on signal."""
        loop = asyncio.get_event_loop()

        for signum in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(signum, self.stop_consuming)
