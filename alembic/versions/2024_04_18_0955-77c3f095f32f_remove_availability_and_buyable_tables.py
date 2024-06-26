"""remove availability and buyable tables

Revision ID: 77c3f095f32f
Revises: b53944c8d447
Create Date: 2024-04-18 09:55:15.622925

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "77c3f095f32f"
down_revision = "b53944c8d447"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("buyables")
    op.drop_table("availabilities")
    op.add_column("offers", sa.Column("in_stock", sa.Boolean(), nullable=True))
    op.add_column(
        "offers",
        sa.Column(
            "availability_version", sa.BigInteger(), nullable=False, server_default="-1"
        ),
    )
    op.add_column("offers", sa.Column("buyable", sa.Boolean(), nullable=True))
    op.add_column(
        "offers",
        sa.Column(
            "buyable_version", sa.BigInteger(), nullable=False, server_default="-1"
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("offers", "buyable_version")
    op.drop_column("offers", "buyable")
    op.drop_column("offers", "availability_version")
    op.drop_column("offers", "in_stock")
    op.create_table(
        "availabilities",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "country_code",
            postgresql.ENUM(
                "BA", "BG", "HR", "CZ", "HU", "RO", "RS", "SI", "SK", name="countrycode"
            ),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "in_stock",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("version", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_availabilities"),
    )
    op.create_table(
        "buyables",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "country_code",
            postgresql.ENUM(
                "BA", "BG", "HR", "CZ", "HU", "RO", "RS", "SI", "SK", name="countrycode"
            ),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "buyable",
            sa.BOOLEAN(),
            server_default=sa.text("false"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("version", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_buyables"),
    )
    # ### end Alembic commands ###
