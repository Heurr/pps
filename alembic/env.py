import re

from sqlalchemy import engine_from_config, pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# if config.config_file_name is not None:
#    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from app.db.alembic import sa_metadata

target_metadata = sa_metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


excluded_tables = [
    r"offers_\d{2}",
    r"product_prices_\d{8}",
    r"product_prices_\d{8}_\d{2}",
]
excluded_indices = []


# Function for excluding partitioned tables
def include_object(obj, name, type_, reflected, compare_to):  # noqa: ARG001
    if type_ == "table":
        for table_pattern in excluded_tables:  # noqa: SIM110
            if re.match(table_pattern, name):
                return False
        return True
    elif type_ == "index":
        for index_pattern in excluded_indices:  # noqa: SIM110
            if re.match(index_pattern, name):
                return False
        return True
    else:
        return True


def _get_database_url():
    from app.config.settings import base_settings

    return base_settings.postgres_db_dsn.replace("+asyncpg", "", 1)


def run_migrations_offline(url) -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online(url) -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=url,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


def main():
    url = _get_database_url()

    if context.is_offline_mode():
        run_migrations_offline(url)
    else:
        run_migrations_online(url)


main()
