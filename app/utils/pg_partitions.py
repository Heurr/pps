import datetime as dt

from sqlalchemy import Connection, TextClause
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncConnection


def get_product_price_partition_name(day: dt.date) -> str:
    return f"product_prices_{day.strftime('%Y%m%d')}"


def get_stmts_for_product_prices_part_tables_for_day(
    day: dt.date, hash_tables: int, fill_factor: int = 80
) -> tuple[TextClause, list[TextClause]]:
    next_day = day + dt.timedelta(days=1)
    table_name = get_product_price_partition_name(day)

    day_partition_stmt = sa_text(
        f"""
        CREATE TABLE product_prices_{day.strftime('%Y%m%d')}
        PARTITION OF product_prices
        FOR VALUES FROM ('{day}') TO ('{next_day}')
        PARTITION BY HASH (product_id);
        """
    )

    hash_partitions_stmts = []
    for i in range(hash_tables):
        stmt = sa_text(
            f"""
            CREATE TABLE {table_name}_{i:02d}
            PARTITION OF {table_name}
            FOR VALUES WITH (MODULUS {hash_tables}, REMAINDER {i})
            WITH (FILLFACTOR = {fill_factor});
            """
        )
        hash_partitions_stmts.append(stmt)
    return day_partition_stmt, hash_partitions_stmts


def sync_create_product_prices_part_tables_for_day(
    db_conn: Connection, day: dt.date, hash_tables: int, fill_factor: int = 80
):
    (
        day_partition_stmt,
        hash_partitions_stmts,
    ) = get_stmts_for_product_prices_part_tables_for_day(day, hash_tables, fill_factor)
    db_conn.execute(day_partition_stmt)

    for stmt in hash_partitions_stmts:
        db_conn.execute(stmt)


async def async_create_product_prices_part_tables_for_day(
    db_conn: AsyncConnection, day: dt.date, hash_tables: int, fill_factor: int = 80
):
    (
        day_partition_stmt,
        hash_partitions_stmts,
    ) = get_stmts_for_product_prices_part_tables_for_day(day, hash_tables, fill_factor)
    await db_conn.execute(day_partition_stmt)

    for stmt in hash_partitions_stmts:
        await db_conn.execute(stmt)
