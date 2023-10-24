import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_pg

from app.db.pg import sa_metadata

availability_table = sa.Table(
    "availabilities",
    sa_metadata,
    sa.Column("id", sa_pg.UUID, primary_key=True),
    sa.Column("in_stock", sa.Boolean, nullable=False, server_default="False"),
    sa.Column("version", sa.BigInteger, nullable=False),
    sa.Column("created_at", sa.DateTime(), nullable=False),
    sa.Column("updated_at", sa.DateTime(), nullable=False),
)
