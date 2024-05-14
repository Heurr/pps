"""Create partitioned product price table

Revision ID: 8a48744218a7
Revises: f8e7f76575b5
Create Date: 2024-04-29 13:47:11.308930

"""

import datetime as dt

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as sa_pg

from alembic import op
from app.utils.pg_partitions import sync_create_product_prices_part_tables_for_day

# revision identifiers, used by Alembic.
revision = "8a48744218a7"
down_revision = "f8e7f76575b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    country_code_type = sa_pg.ENUM(name="countrycode", create_type=False)
    country_code_type.create(conn, checkfirst=True)
    currency_code_type = sa_pg.ENUM(name="currencycode", create_type=False)
    currency_code_type.create(conn, checkfirst=True)
    product_price_type = sa_pg.ENUM(
        "ALL_OFFERS",
        "MARKETPLACE",
        "IN_STOCK",
        "IN_STOCK_CERTIFIED",
        name="product_price_type",
        create_type=False,
    )
    product_price_type.create(conn, checkfirst=True)

    op.create_table(
        "product_prices",
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column(
            "country_code",
            country_code_type,
            nullable=False,
        ),
        sa.Column(
            "price_type",
            product_price_type,
            nullable=False,
        ),
        sa.Column("min_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("max_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "currency_code",
            currency_code_type,
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint(
            "day", "product_id", "price_type", name=op.f("pk_product_price")
        ),
        postgresql_partition_by="RANGE (day)",
    )

    day = dt.date.today()
    for _ in range(20):
        sync_create_product_prices_part_tables_for_day(conn, day, 10)
        day += dt.timedelta(days=1)


def downgrade() -> None:
    op.drop_table("product_prices")
