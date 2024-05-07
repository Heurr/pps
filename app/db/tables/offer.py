import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_pg

from app.constants import PRICE_PRECISION, PRICE_SCALE, CountryCode, CurrencyCode
from app.db.pg import sa_metadata

# fill factor = 70 pct managed by alembic (on partitions)
offer_table = sa.Table(
    "offers",
    sa_metadata,
    sa.Column("id", sa_pg.UUID, nullable=False, index=True),
    sa.Column("product_id", sa_pg.UUID, nullable=False),
    sa.Column("shop_id", sa_pg.UUID, nullable=False, index=True),
    sa.Column("country_code", sa.Enum(CountryCode), nullable=False),
    sa.Column("currency_code", sa.Enum(CurrencyCode), nullable=False),
    sa.Column("price", sa.Numeric(PRICE_PRECISION, PRICE_SCALE), nullable=False),
    sa.Column("version", sa.BigInteger, nullable=False),
    sa.Column("in_stock", sa.Boolean, nullable=True),
    sa.Column("availability_version", sa.BigInteger, nullable=False, server_default="-1"),
    sa.Column("buyable", sa.Boolean, nullable=True),
    sa.Column("buyable_version", sa.BigInteger, nullable=False, server_default="-1"),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint("product_id", "id"),
    postgresql_partition_by="HASH (product_id, id)",
)
