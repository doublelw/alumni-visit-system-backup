"""Merge migration heads before adding electronic card tables

Revision ID: d3221b5120aa
Revises: add_isolated_security_system, allow_null_email_and_id_card, bd854d32111e, d4342a3ce55d, remove_unique_username_constraint
Create Date: 2026-03-27 00:43:05.155209

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3221b5120aa'
down_revision = ('add_isolated_security_system', 'allow_null_email_and_id_card', 'bd854d32111e', 'd4342a3ce55d', 'remove_unique_username_constraint')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
