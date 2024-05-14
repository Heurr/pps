import logging

from aio_pika import Message
from aio_pika.abc import AbstractExchange, HeadersType

from app.config.settings import ProductPricePublishSettings
from app.exceptions import PriceServiceError
from app.schemas.base import EntityHeaders
from app.schemas.product_price import ProductPriceRabbitSchema
from app.utils import dump_to_json_bytes
from app.utils.rabbitmq_adapter import BaseRabbitmqAdapter

logger = logging.getLogger(__name__)


class ProductPriceEntityClient(BaseRabbitmqAdapter):
    def __init__(self, settings: ProductPricePublishSettings | None = None):
        entity_publish_settings = settings or ProductPricePublishSettings()
        super().__init__(entity_publish_settings.rabbitmq_dsn())
        self.exchange_name = entity_publish_settings.RABBITMQ_EXCHANGE_NAME
        self.target_routing_key = entity_publish_settings.ROUTING_KEY
        self.user_agent = entity_publish_settings.USER_AGENT
        self.content_type = entity_publish_settings.CONTENT_TYPE
        self.exchange: AbstractExchange | None = None

    async def connect(self):
        await super().connect()
        self.exchange = await self.channel.get_exchange(self.exchange_name)

    async def send_entity(self, entity: list[ProductPriceRabbitSchema]) -> None:
        try:
            if not self.exchange:
                raise PriceServiceError("Exchange is not initialized")

            message = Message(body=dump_to_json_bytes(entity), headers=self._headers)
            await self.exchange.publish(message, self.target_routing_key)
        except Exception as exc:
            logger.error(
                "Error while publishing Product Pride entity, %s", exc, exc_info=exc
            )

    @property
    def _headers(self) -> HeadersType:
        return EntityHeaders(
            user_agent=self.user_agent,
            content_type=self.content_type,
        ).model_dump()
