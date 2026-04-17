"""add key history table

Revision ID: add_key_history_table
Revises:
Create Date: 2026-03-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_key_history_table'
down_revision = None  # This will be set when merge is done
branch_labels = None
depends_on = None


def upgrade():
    """创建密钥历史表"""
    op.create_table(
        'key_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('key_type', sa.String(50), nullable=False),
        sa.Column('old_key', sa.String(100)),
        sa.Column('new_key', sa.String(100)),
        sa.Column('changed_by', sa.String(100), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('reason', sa.String(200))
    )

    # 创建索引以加快按密钥类型查询
    op.create_index('ix_key_history_key_type', 'key_history', ['key_type'])


def downgrade():
    """删除密钥历史表"""
    op.drop_index('ix_key_history_key_type', table_name='key_history')
    op.drop_table('key_history')
