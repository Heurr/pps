import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_pg

from app.constants import (
    DISCOUNT_PRECISION,
    DISCOUNT_SCALE,
    CountryCode,
    ProductPriceType,
)
from app.db.pg import sa_metadata

product_discount_table = sa.Table(
    "product_discounts",
    sa_metadata,
    sa.Column("id", sa_pg.UUID, primary_key=True),
    sa.Column("country_code", sa.Enum(CountryCode), primary_key=True),
    sa.Column("discount", sa.Numeric(DISCOUNT_PRECISION, DISCOUNT_SCALE), nullable=False),
    sa.Column("price_type", sa.Enum(ProductPriceType), nullable=False),
    sa.Column("version", sa.BigInteger, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)
