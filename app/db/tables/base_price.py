import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_pg

from app.constants import PRICE_PRECISION, PRICE_SCALE, ProductPriceType
from app.db.pg import sa_metadata

base_price_table = sa.Table(
    "base_prices",
    sa_metadata,
    sa.Column("product_id", sa_pg.UUID, nullable=False),
    sa.Column(
        "price_type", sa.Enum(ProductPriceType, name="product_price_type"), nullable=False
    ),
    sa.Column("price", sa.Numeric(PRICE_PRECISION, PRICE_SCALE), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint("product_id", "price_type"),
    postgresql_partition_by="HASH (product_id)",
)
