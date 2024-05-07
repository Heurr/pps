from app.config.settings import JobSettings
from app.constants import Job
from app.db import db_adapter
from app.jobs import JOB_CLASS_MAP, BaseJob
from app.utils.redis_adapter import RedisAdapter


async def job_app(name: Job):
    settings = JobSettings()
    async with (
        db_adapter as db_engine,
        RedisAdapter(settings.redis_dsn, decode_responses=False) as redis,
    ):
        job_class = JOB_CLASS_MAP.get(name, BaseJob)
        job: BaseJob = job_class(
            name=name, db_engine=db_engine, redis=redis, settings=settings
        )
        await job.run()
