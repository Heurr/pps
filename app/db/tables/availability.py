import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_pg

from app.constants import CountryCode
from app.db.pg import sa_metadata

availability_table = sa.Table(
    "availabilities",
    sa_metadata,
    sa.Column("id", sa_pg.UUID, primary_key=True),
    sa.Column("country_code", sa.Enum(CountryCode), nullable=False),
    sa.Column("in_stock", sa.Boolean, nullable=False, server_default="False"),
    sa.Column("version", sa.BigInteger, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)
