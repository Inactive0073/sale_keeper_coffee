"""add server_default_value_for_user

Revision ID: 43547f78a7b2
Revises: 7e31850d3770
Create Date: 2025-07-07 14:48:00.471360

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43547f78a7b2'
down_revision: Union[str, None] = '7e31850d3770'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'users', 'timezone',
        server_default=sa.text("'Europe/Moscow'"),
        existing_type=sa.String()
    )


def downgrade() -> None:
    op.alter_column(
        'users', 'timezone',
        server_default=None,
        existing_type=sa.String()
    )

