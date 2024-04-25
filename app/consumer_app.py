import logging

from app.config.settings import ConsumerSettings
from app.constants import Entity
from app.consumers.consumer import Consumer

logger = logging.getLogger(__name__)


async def run_entity_consumer(entity: Entity) -> None:
    consumer = Consumer(entity, ConsumerSettings())
    await consumer.run()
