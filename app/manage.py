import logging
from pathlib import Path

import click
import typer

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from app.utils.log import prepare_logging

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


if __name__ == "__main__":
    app()
