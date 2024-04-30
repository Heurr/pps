import datetime as dt

from sqlalchemy import Connection
from sqlalchemy import text as sa_text


def create_product_prices_part_tables_for_day(
    db_conn: Connection, day: dt.date, hash_tables: int, fill_factor: int = 80
):
    next_day = day + dt.timedelta(days=1)
    table_name = f"product_prices_{day.strftime('%Y%m%d')}"

    stmt = sa_text(
        f"""
        CREATE TABLE product_prices_{day.strftime('%Y%m%d')}
        PARTITION OF product_prices
        FOR VALUES FROM ('{day}') TO ('{next_day}')
        PARTITION BY HASH (product_id);
        """
    )
    db_conn.execute(stmt)

    for i in range(hash_tables):
        stmt = sa_text(
            f"""
            CREATE TABLE {table_name}_{i:02d}
            PARTITION OF {table_name}
            FOR VALUES WITH (MODULUS {hash_tables}, REMAINDER {i})
            WITH (FILLFACTOR = {fill_factor});
            """
        )
        db_conn.execute(stmt)
