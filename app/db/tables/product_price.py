import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_pg

from app.constants import (
    PRICE_PRECISION,
    PRICE_SCALE,
    CountryCode,
    CurrencyCode,
    ProductPriceType,
)
from app.db.pg import sa_metadata

# fill factor = 70 pct managed by alembic (on partitions)
product_price_table = sa.Table(
    "product_prices",
    sa_metadata,
    sa.Column("day", sa.Date, nullable=False),
    sa.Column("product_id", sa_pg.UUID, nullable=False),
    sa.Column("country_code", sa.Enum(CountryCode), nullable=False),
    sa.Column(
        "price_type", sa.Enum(ProductPriceType, name="product_price_type"), nullable=False
    ),
    sa.Column("min_price", sa.Numeric(PRICE_PRECISION, PRICE_SCALE), nullable=False),
    sa.Column("max_price", sa.Numeric(PRICE_PRECISION, PRICE_SCALE), nullable=False),
    sa.Column("currency_code", sa.Enum(CurrencyCode), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint("day", "product_id", "price_type"),
    postgresql_partition_by="RANGE (day)",
)
