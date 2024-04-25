import asyncio
import logging
from pathlib import Path

import click
import typer

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from app.constants import Entity
from app.consumer_app import run_entity_consumer
from app.utils.log import prepare_logging
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


if __name__ == "__main__":
    app()
