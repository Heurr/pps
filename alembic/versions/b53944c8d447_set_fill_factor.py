"""Set fill factor

Revision ID: b53944c8d447
Revises: 735f11dd2cd8
Create Date: 2024-04-15 11:39:41.989690

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "b53944c8d447"
down_revision = "0f829de42ead"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE offers SET (FILLFACTOR = 70)")
    op.execute("ALTER TABLE buyables SET (FILLFACTOR = 70)")
    op.execute("ALTER TABLE availabilities SET (FILLFACTOR = 70)")


def downgrade() -> None:
    op.execute("ALTER TABLE offers RESET (FILLFACTOR)")
    op.execute("ALTER TABLE buyables RESET (FILLFACTOR)")
    op.execute("ALTER TABLE availabilities RESET (FILLFACTOR)")
