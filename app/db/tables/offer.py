import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_pg

from app.constants import PRICE_PRECISION, PRICE_SCALE, CountryCode, CurrencyCode
from app.db.pg import sa_metadata

offer_table = sa.Table(
    "offers",
    sa_metadata,
    sa.Column("id", sa_pg.UUID, primary_key=True),
    sa.Column("product_id", sa_pg.UUID, nullable=False, index=True),
    sa.Column("shop_id", sa_pg.UUID, nullable=False),
    sa.Column("country_code", sa.Enum(CountryCode), nullable=False, index=True),
    sa.Column("currency_code", sa.Enum(CurrencyCode), nullable=False),
    sa.Column("amount", sa.Numeric(PRICE_PRECISION, PRICE_SCALE), nullable=False),
    sa.Column("version", sa.BigInteger, nullable=False),
    sa.Column("created_at", sa.DateTime(), nullable=False),
    sa.Column("updated_at", sa.DateTime(), nullable=False),
    # TODO: index for country and id together
)
