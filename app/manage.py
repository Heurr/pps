import asyncio
import logging
from pathlib import Path
from time import sleep

import click
import typer

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from app.config.settings import (
    JobSettings,
    MaintenanceJobSettings,
    ValidationJobSettings,
    WorkerSetting,
)
from app.constants import PRICE_EVENT_QUEUE, Entity, Job
from app.consumer_app import run_entity_consumer
from app.db import db_adapter
from app.job_app import job_app
from app.jobs.entity_population import EntityPopulationJob
from app.jobs.maintenance import MaintenanceJob
from app.jobs.price_publish import PublishingPriceJob
from app.jobs.validation import ValidationJob
from app.utils.log import prepare_logging
from app.utils.redis_adapter import RedisAdapter
from app.utils.sentry import init_sentry
from app.worker_app import run_message_worker

prepare_logging()

logger = logging.getLogger(__name__)

app = typer.Typer()


def get_alembic_config() -> AlembicConfig:
    config_path = Path(__name__).absolute().parent / "alembic.ini"
    return AlembicConfig(str(config_path))


@app.command()
def upgrade_db(revision: str = "head"):
    alembic_command.upgrade(get_alembic_config(), revision)
    click.secho("Migration done!", fg="green")


@app.command()
def downgrade_db(revision: str = "base"):
    alembic_command.downgrade(get_alembic_config(), revision)
    click.secho("Downgrade of database done!", fg="green")


@app.command()
def make_db_migration(message: str):
    alembic_command.revision(get_alembic_config(), message, autogenerate=True)


@app.command()
def run_worker(entity: Entity):
    init_sentry(server_name=f"{entity}-worker", component="worker")
    cname = entity.value.capitalize()
    try:
        asyncio.run(run_message_worker(entity))
    except asyncio.CancelledError:
        logger.info("%s consuming and processing task cancelled", cname)
    except Exception as exc:
        logger.exception("%s consuming and processing task failed", cname, exc_info=exc)
    finally:
        logger.info("%s consuming and processing shutdown complete", cname)


@app.command()
def run_consumer(entity: Entity):
    init_sentry(server_name=f"{entity}-consumer", component="consumer")
    cname = entity.value.capitalize()

    try:
        asyncio.run(run_entity_consumer(entity))
    except asyncio.CancelledError:
        logger.info("%s consumer task cancelled", cname)
    except Exception as exc:
        logger.exception("%s consumer task failed", cname, exc_info=exc)
    finally:
        logger.info("%s consumer shutdown complete", cname)


@app.command()
def run_job(name: Job):
    init_sentry(server_name=name, component="job")
    try:
        asyncio.run(job_app(name))
    except asyncio.CancelledError:
        logger.info("%s job cancelled", name)
    except Exception as exc:
        logger.exception("%s job failed", name, exc_info=exc)
    finally:
        logger.info("%s job shutdown complete", name)


@app.command()
def entity_population_job(entities: list[Entity]):
    logger.info("Starting entity population job")

    async def run_entity_population_job():
        try:
            async with db_adapter as db_engine:
                job = EntityPopulationJob(db_engine, entities)
                await job.run()
        except Exception as exc:
            logger.exception("Entity population job failed", exc_info=exc)

    asyncio.run(run_entity_population_job())

    sleep_duration = 60
    logger.info("Sleeping for %s seconds to let metrics be scraped", sleep_duration)
    sleep(sleep_duration)
    logger.info("Entity population job finished")


@app.command()
def validation_job():
    logger.info("Starting validation job")
    init_sentry(server_name="validation-job", component="job")

    async def run_validation_job():
        try:
            async with db_adapter as db_engine:
                job = ValidationJob(db_engine, ValidationJobSettings())
                await job.run()
        except Exception as exc:
            logger.exception("Validation job failed", exc_info=exc)

    asyncio.run(run_validation_job())

    sleep_duration = 60
    logger.info("Sleeping for %s seconds to let metrics be scraped", sleep_duration)
    sleep(sleep_duration)
    logger.info("Validation job finished")


@app.command()
def publish_price_job():
    logger.info("Starting price publishing job")

    init_sentry(server_name="product-price-rabbit", component="job")

    async def run_publish_price_job():
        try:
            worker_settings = WorkerSetting()
            job_settings = JobSettings()
            async with (
                db_adapter as db_engine,
                RedisAdapter(worker_settings.redis_dsn) as redis,
            ):
                job = PublishingPriceJob(
                    PRICE_EVENT_QUEUE.value, db_engine, redis, job_settings
                )
                await job.run()
        except Exception as exc:
            logger.exception("Entity population job failed", exc_info=exc)

    asyncio.run(run_publish_price_job())


@app.command()
def maintenance_job():
    logger.info("Starting maintenance job")

    init_sentry(server_name="maintenance-job", component="job")

    async def run_maintenance_job():
        maintenance_job_settings = MaintenanceJobSettings()
        try:
            async with (
                db_adapter as db_engine,
                RedisAdapter(maintenance_job_settings.redis_dsn) as redis,
            ):
                job = MaintenanceJob(db_engine, redis, maintenance_job_settings)
                await job.run()
        except Exception as exc:
            logger.exception("Maintenance job failed", exc_info=exc)

    asyncio.run(run_maintenance_job())

    sleep_duration = 60
    logger.info("Sleeping for %s seconds to let metrics be scraped", sleep_duration)
    sleep(sleep_duration)
    logger.info("Maintenance job finished")


if __name__ == "__main__":
    app()
