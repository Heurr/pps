import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_postgresql
from sqlalchemy import text

from app.constants import COUNTRY_CODE_STRING_LENGTH, LOCAL_PRODUCT_ID_STRING_LENGTH
from app.db.pg import sa_metadata


product_table = sa.Table(
    "products",
    sa_metadata,
    sa.Column("id", sa_postgresql.UUID, primary_key=True),
    sa.Column(
        "local_product_id",
        sa.String(length=LOCAL_PRODUCT_ID_STRING_LENGTH),
        nullable=True,
    ),
    sa.Column("name", sa.String(length=255), nullable=False),
    sa.Column(
        "country",
        sa.String(length=COUNTRY_CODE_STRING_LENGTH),
        nullable=False,
        index=True,
    ),
    sa.Column("version", sa.BigInteger, nullable=False),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    ),
    sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    ),
    sa.Index("ix_products_local_key", "local_product_id", "country"),
)
