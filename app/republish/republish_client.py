import logging
from uuid import UUID

import orjson
from aio_pika import Message
from aio_pika.abc import AbstractExchange, HeadersType

from app.config.settings import RepublishSettings
from app.constants import Entity
from app.exceptions import PriceServiceError
from app.republish.headers import RepublishHeaders
from app.utils.rabbitmq_adapter import BaseRabbitmqAdapter

logger = logging.getLogger(__name__)


class RabbitmqRepublishClient(BaseRabbitmqAdapter):
    def __init__(self, entity: Entity, settings: RepublishSettings | None = None):
        republish_settings = settings or RepublishSettings()
        super().__init__(republish_settings.rabbitmq_dsn(entity))
        self.exchange_name = republish_settings.RABBITMQ_EXCHANGE_NAME
        self.republish_batch = republish_settings.REPUBLISH_BATCH
        self.entity = entity
        self.republish_to_routing_key = (
            republish_settings.REPUBLISH_TO_ROUTING_KEY_MAP.get(entity)
        )
        self.target_routing_key = republish_settings.TARGET_ROUTING_KEY_MAP.get(entity)
        self.reply_to_routing_key = republish_settings.REPLY_TO_ROUTING_KEY
        self.user_agent = republish_settings.USER_AGENT
        self.content_type = republish_settings.CONTENT_TYPE
        self.exchange: AbstractExchange | None = None

    async def connect(self):
        await super().connect()
        self.exchange = await self.channel.get_exchange(self.exchange_name)

    async def republish_ids(self, ids: list[UUID]) -> None:
        try:
            if not ids:
                return
            if not self.target_routing_key:
                raise PriceServiceError(
                    f"Entity {self.entity} is not supported for republishing"
                )
            if not self.exchange:
                raise PriceServiceError("Exchange is not initialized")
            # Batch over ids with batch_size
            for i in range(0, len(ids), self.republish_batch):
                batch = ids[i : i + self.republish_batch]
                message = Message(
                    body=orjson.dumps({"ids": batch}), headers=self._headers
                )
                await self.exchange.publish(message, self.target_routing_key)
        except Exception as exc:
            logger.error("Error while republishing ids, %s", exc, exc_info=exc)

    @property
    def _headers(self) -> HeadersType:
        return RepublishHeaders(
            user_agent=self.user_agent,
            content_type=self.content_type,
            hg_republish_to=self.republish_to_routing_key,  # type: ignore
            hg_reply_to=self.reply_to_routing_key,
        ).model_dump()
