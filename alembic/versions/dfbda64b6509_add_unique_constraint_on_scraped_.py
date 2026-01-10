"""add unique constraint on scraped_resources

Revision ID: dfbda64b6509
Revises: 8580b0d4e78b
Create Date: 2026-01-08 22:49:52.844005

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "dfbda64b6509"
down_revision: Union[str, Sequence[str], None] = "8580b0d4e78b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
