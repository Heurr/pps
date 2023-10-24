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

product_price_table = sa.Table(
    "product_prices",
    sa_metadata,
    sa.Column("id", sa_pg.UUID, primary_key=True),
    sa.Column("country_code", sa.Enum(CountryCode), primary_key=True),
    sa.Column("currency_code", sa.Enum(CurrencyCode), nullable=False),
    sa.Column("min_price", sa.Numeric(PRICE_PRECISION, PRICE_SCALE), nullable=False),
    sa.Column("max_price", sa.Numeric(PRICE_PRECISION, PRICE_SCALE), nullable=False),
    sa.Column("avg_price", sa.Numeric(PRICE_PRECISION, PRICE_SCALE), nullable=False),
    sa.Column("price_type", sa.Enum(ProductPriceType), nullable=False),
    sa.Column("version", sa.BigInteger, nullable=False),
    sa.Column("created_at", sa.DateTime(), nullable=False),
    sa.Column("updated_at", sa.DateTime(), nullable=False),
)
