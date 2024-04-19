from app.constants import Entity
from app.db import db_adapter
from app.utils.redis_adapter import RedisAdapter
from app.workers import WORKER_CLASS_MAP
from app.workers.base import BaseMessageWorker


async def run_message_worker(entity: Entity) -> None:
    from app.config.settings import WorkerSetting

    worker_settings = WorkerSetting()

    async with (
        db_adapter as db_engine,
        RedisAdapter(
            worker_settings.redis_dsn, encoding="utf-8", decode_responses=True
        ) as redis,
    ):
        worker_class, message_schema = WORKER_CLASS_MAP[entity]
        worker: BaseMessageWorker = worker_class(
            entity=entity,
            settings=worker_settings,
            db_engine=db_engine,
            redis=redis,
            message_schema=message_schema,
        )

        await worker.consume_and_process_messages()
