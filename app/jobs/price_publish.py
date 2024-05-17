import asyncio
from typing import cast
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config.settings import JobSettings, ProductPricePublishSettings
from app.constants import (
    Action,
    ProductPriceType,
)
from app.exceptions import PriceServiceError
from app.jobs.base import BaseJob
from app.schemas.product_price import (
    ProductPriceDBSchema,
    ProductPricePricesRabbitSchema,
    ProductPriceRabbitSchema,
)
from app.services.product_price import ProductPriceService
from app.utils import version_now
from app.utils.product_price_entity_client import ProductPriceEntityClient


class PublishingPriceJob(BaseJob):
    def __init__(
        self,
        name: str,
        db_engine: AsyncEngine,
        redis: Redis,
        settings: JobSettings,
        product_price_publish_settings: ProductPricePublishSettings | None = None,
    ):
        super().__init__(name, db_engine, redis, settings)
        self.rmq: ProductPriceEntityClient | None = None
        self.product_price_publish_settings = (
            product_price_publish_settings or ProductPricePublishSettings()
        )
        self.product_price_service = ProductPriceService()

    async def run(self):
        async with ProductPriceEntityClient(self.product_price_publish_settings) as rmq:
            self.rmq = rmq
            await super().run()

    async def read(self) -> list[UUID]:
        res = cast(
            list[bytes], await self.redis.rpop(self.redis_queue, count=self.buffer_size)
        )
        if not res:
            await asyncio.sleep(self.redis_pop_timeout)
            return []

        return [UUID(bytes=obj) for obj in res]

    async def process(self, obj_ids: list[UUID]):
        if not self.rmq:
            raise PriceServiceError("RabbitMQ client is not initialized")
        async with self.get_db_conn() as conn:
            product_prices = (
                await self.product_price_service.get_today_prices_for_products(
                    conn, obj_ids
                )
            )
            if not product_prices:
                return

            processed_entities = [
                await self.prepare_rabbit_msg(product_prices[obj_id])
                for obj_id in obj_ids
            ]
            await self.rmq.send_entity(processed_entities)
            self.logger.info(
                "Published %i price entities to RabbitMQ", len(processed_entities)
            )
            self.metrics.labels(name=self.name, stage="publish").inc(
                len(processed_entities)
            )

    @staticmethod
    async def prepare_rabbit_msg(
        prices: dict[ProductPriceType, ProductPriceDBSchema],
    ) -> ProductPriceRabbitSchema:
        return ProductPriceRabbitSchema(
            product_id=prices[ProductPriceType.ALL_OFFERS].product_id,
            currency_code=prices[ProductPriceType.ALL_OFFERS].currency_code,
            country_code=prices[ProductPriceType.ALL_OFFERS].country_code,
            prices=[
                ProductPricePricesRabbitSchema(
                    min=schema.min_price, max=schema.max_price, type=price_type
                )
                for price_type, schema in prices.items()
            ],
            version=version_now(),
            action=Action.UPDATE,
        )
