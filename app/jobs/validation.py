import logging
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncEngine

from app import crud
from app.config.settings import ValidationJobSettings
from app.constants import Aggregate
from app.crud.product_price import crud_product_price
from app.custom_types import MinMaxPrice, ProductPriceDeletePk
from app.metrics import VALIDATION_METRIC
from app.utils import utc_today


class ValidationJob:
    def __init__(
        self,
        db_engine: AsyncEngine,
        settings: ValidationJobSettings,
    ):
        self.db_engine = db_engine
        self.settings = settings
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def get_db_conn(self):
        async with self.db_engine.begin() as conn:
            yield conn

    async def get_sample_from_product_price(self) -> list[MinMaxPrice]:
        async with self.get_db_conn() as conn:
            self.logger.info("Getting rows from product_prices")
            return await crud_product_price.get_sample_for_day(
                conn,
                utc_today(),
                pct=self.settings.BERNOULLI_PCT,
                limit=self.settings.LIMIT,
            )

    async def get_sample_from_offers(
        self, product_keys: list[ProductPriceDeletePk]
    ) -> list[MinMaxPrice]:
        """For the sample from product_prices table,
        get corresponding data from offers table."""
        res = []
        async with self.get_db_conn() as conn:
            self.logger.info("Getting rows from offers")
            for product_id, price_type in product_keys:
                mn = await crud.offer.get_price_for_product(
                    conn, product_id, price_type, Aggregate.MIN
                )
                mx = await crud.offer.get_price_for_product(
                    conn, product_id, price_type, Aggregate.MAX
                )
                res.append(MinMaxPrice(product_id, price_type, mn, mx))
        return res

    @staticmethod
    def find_diff(
        product_price_sample: list[MinMaxPrice], offers_sample: list[MinMaxPrice]
    ) -> list[UUID]:
        """Compare min and max prices, find which records of the two table samples
        do not match and return its product_ids."""
        diff = []
        for i, j in zip(product_price_sample, offers_sample, strict=True):
            if i.min_price != j.min_price or i.max_price != j.max_price:
                diff.append(i.product_id)
        return diff

    async def run(self):
        """
        Main entry point.
        Get random data sample from product_prices.
        Get corresponding offers for this data sample.
        Compare the two samples and get diff.
        Draw metrics.
        """
        product_price_sample = await self.get_sample_from_product_price()
        product_keys = [
            ProductPriceDeletePk(i.product_id, i.price_type) for i in product_price_sample
        ]
        offers_sample = await self.get_sample_from_offers(product_keys)
        diff = self.find_diff(product_price_sample, offers_sample)

        # add logs & metrics
        self.logger.info(
            "From total rows of %d, " "found %d rows that did not match",
            len(product_price_sample),
            len(diff),
        )
        VALIDATION_METRIC.labels(status="all").inc(self.settings.LIMIT)
        VALIDATION_METRIC.labels(status="not matched").inc(len(diff))
