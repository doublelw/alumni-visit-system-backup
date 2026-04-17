"""
添加特批功能字段

Revision ID: add_special_approval_fields
Revises:
Create Date: 2026-03-27

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_special_approval_fields'
down_revision = None  # 根据实际迁移历史调整
branch_labels = None
depends_on = None


def upgrade():
    """添加特批相关字段"""
    # 为visit_applications表添加特批标记字段
    op.add_column('visit_applications',
                  sa.Column('is_special_approval', sa.Boolean(), nullable=False, server_default='0',
                            comment='是否为班主任特批（无家长确认）'))
    op.add_column('visit_applications',
                  sa.Column('special_approval_reason', sa.Text(), nullable=True,
                            comment='特批原因'))

    # 确保wechat_password字段可以为空（支持2位密码）
    # 注意：如果字段已存在则跳过
    try:
        op.alter_column('users', 'wechat_password',
                       existing_type=sa.String(4),
                       type_=sa.String(6),
                       nullable=True,
                       comment='微信H5密码（2-6位数字，家长2位，老师/门卫4-6位）')
    except:
        pass  # 字段可能已存在或结构不同


def downgrade():
    """回滚迁移"""
    op.drop_column('visit_applications', 'special_approval_reason')
    op.drop_column('visit_applications', 'is_special_approval')
