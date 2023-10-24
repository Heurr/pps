import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_pg

from app.db.pg import sa_metadata

shop_table = sa.Table(
    "shops",
    sa_metadata,
    sa.Column("id", sa_pg.UUID, primary_key=True),
    sa.Column("certified", sa.Boolean, nullable=False, server_default="False"),
    sa.Column("verified", sa.Boolean, nullable=False, server_default="False"),
    sa.Column("paying", sa.Boolean, nullable=False, server_default="False"),
    sa.Column("enabled", sa.Boolean, nullable=False, server_default="False"),
    sa.Column("version", sa.BigInteger, nullable=False),
    sa.Column("created_at", sa.DateTime(), nullable=False),
    sa.Column("updated_at", sa.DateTime(), nullable=False),
)
