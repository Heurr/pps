import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app import crud
from app.config.settings import EntityPopulationJobSettings, RepublishSettings
from app.constants import ENTITY_VERSION_COLUMNS, Entity
from app.custom_types import OfferPk
from app.metrics import UNPOPULATED_ENTITIES
from app.republish.republish_client import RabbitmqRepublishClient
from app.schemas.offer import PopulationOfferSchema
from app.utils import utc_now


class EntityPopulationJob:
    def __init__(
        self,
        db_engine: AsyncEngine,
        entities: list[Entity],
        job_settings: EntityPopulationJobSettings | None = None,
        republish_settings: RepublishSettings | None = None,
    ):
        job_settings = job_settings or EntityPopulationJobSettings()
        self.republish_settings = republish_settings or RepublishSettings()
        self.batch_size = job_settings.BATCH_SIZE
        self.expire_time = job_settings.EXPIRE_TIME
        self.db_engine = db_engine
        self.entities = entities
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def get_db_conn(self):
        async with self.db_engine.begin() as conn:
            yield conn

    async def run(self):
        """
        Main method of the job. It fetches unpopulated offers from the database
        and processes them in batches. Then it uses the republish client to request
        a republish for unpopulated offers.
        """
        missing_ids = defaultdict(list)
        async with self.get_db_conn() as conn:
            async for batch in crud.offer.get_unpopulated_offers(conn, self.batch_size):
                self.logger.info("Processing batch of %d offers", len(batch))
                for entity, ids in (await self.process(conn, batch)).items():
                    missing_ids[entity].extend(ids)
        for entity, ids in missing_ids.items():
            async with RabbitmqRepublishClient(entity, self.republish_settings) as rmq:
                UNPOPULATED_ENTITIES.labels(entity=entity.value).inc(len(ids))
                await rmq.republish_ids(ids)

    async def process(
        self, db_conn: AsyncConnection, batch: list[PopulationOfferSchema]
    ) -> dict[Entity, list[UUID]]:
        """
        Process a batch of offers. It checks if the offers are expired, if
        they are expired, it marks them as populated. If they are not expired,
        it returns them for further processing
        """
        expire_threshold = utc_now() - timedelta(seconds=self.expire_time)
        expired_pks = []
        unpopulated_ids = defaultdict(list)
        for offer in batch:
            if offer.created_at < expire_threshold:
                expired_pks.append(OfferPk(offer.product_id, offer.id))
                continue
            for entity in self.entities:
                if getattr(offer, ENTITY_VERSION_COLUMNS[entity]) == -1:
                    unpopulated_ids[entity].append(offer.id)

        await crud.offer.set_offers_as_populated(db_conn, self.entities, expired_pks)
        self.logger.info("Expired %d offers", len(expired_pks))
        return unpopulated_ids
