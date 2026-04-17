"""创建学生请假申请表

Revision ID: create_student_leave
Revises:
Create Date: 2026-03-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = 'create_student_leave'
down_revision = None  # 根据实际情况设置
branch_labels = None
depends_on = None


def upgrade():
    """创建学生请假申请表"""
    op.create_table(
        'student_leave_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('student_name', sa.String(length=50), nullable=False),
        sa.Column('class_name', sa.String(length=50), nullable=False),
        sa.Column('grade', sa.String(length=20), nullable=True),
        sa.Column('parent_name', sa.String(length=50), nullable=False),
        sa.Column('parent_phone', sa.String(length=20), nullable=False),
        sa.Column('parent_id_card', sa.String(length=18), nullable=True),
        sa.Column('leave_reason', sa.Text(), nullable=False),
        sa.Column('leave_type', sa.String(length=20), nullable=False),
        sa.Column('expected_return_time', sa.DateTime(), nullable=False),
        sa.Column('leave_code', sa.String(length=6), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('teacher_id', sa.Integer(), nullable=True),
        sa.Column('teacher_name', sa.String(length=50), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_emergency', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('emergency_approver_id', sa.Integer(), nullable=True),
        sa.Column('emergency_approver_name', sa.String(length=50), nullable=True),
        sa.Column('emergency_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['emergency_approver_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('leave_code')
    )

    # 创建索引
    op.create_index('ix_student_leave_code', 'student_leave_applications', ['leave_code'])
    op.create_index('ix_student_leave_status', 'student_leave_applications', ['status'])
    op.create_index('ix_student_leave_student_id', 'student_leave_applications', ['student_id'])
    op.create_index('ix_student_leave_is_emergency', 'student_leave_applications', ['is_emergency'])


def downgrade():
    """删除学生请假申请表"""
    op.drop_index('ix_student_leave_is_emergency', table_name='student_leave_applications')
    op.drop_index('ix_student_leave_student_id', table_name='student_leave_applications')
    op.drop_index('ix_student_leave_status', table_name='student_leave_applications')
    op.drop_index('ix_student_leave_code', table_name='student_leave_applications')
    op.drop_table('student_leave_applications')
