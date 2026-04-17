"""
添加微信登录密码字段

Revision ID: add_wechat_password
Revises:
Create Date: 2026-03-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_wechat_password'
down_revision = None  # 设置为最近的迁移ID


def upgrade():
    """添加微信密码字段"""
    # 添加微信密码字段到users表
    op.add_column('users',
        sa.Column('wechat_password', sa.String(4), nullable=True, comment='微信登录密码（2-4位数字）')
    )

    # 为现有用户设置默认密码（老师：1234，家长：88，学生：空）
    # 注意：这里使用原生SQL，因为ORM可能不可用
    op.execute("""
        UPDATE users
        SET wechat_password = CASE
            WHEN user_type LIKE '%teacher%' THEN '1234'
            WHEN user_type LIKE '%parent%' THEN '88'
            ELSE NULL
        END
        WHERE wechat_password IS NULL
    """)


def downgrade():
    """移除微信密码字段"""
    op.drop_column('users', 'wechat_password')
