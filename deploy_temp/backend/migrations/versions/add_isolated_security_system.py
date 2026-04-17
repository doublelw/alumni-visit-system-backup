"""add isolated security system

Revision ID: add_isolated_security_system
Revises:
Create Date: 2026-03-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_isolated_security_system'
down_revision = None  # 或者是上一个迁移的ID
branch_labels = None
depends_on = None


def upgrade():
    """创建内外网隔离架构所需的新表"""

    # ========================================
    # 外网数据库表（外网服务器）
    # ========================================

    # 1. 为users表添加新字段
    # 注意：如果表已存在，使用ALTER TABLE
    try:
        op.add_column('users',
            sa.Column('pin_hash', sa.String(64), nullable=True, comment='2位PIN的SHA256哈希')
        )
        op.add_column('users',
            sa.Column('key_version', sa.Integer(), nullable=True, default=1, comment='密钥版本号')
        )
        op.add_column('users',
            sa.Column('key_expires_at', sa.DateTime(), nullable=True, comment='密钥过期时间')
        )
        op.add_column('users',
            sa.Column('private_key', sa.Text(), nullable=True, comment='用户私钥（Base64）')
        )
        op.add_column('users',
            sa.Column('public_key', sa.Text(), nullable=True, comment='用户公钥（Base64）')
        )
    except Exception as e:
        print(f"添加users字段失败（可能已存在）: {e}")

    # 2. 创建学生请假表
    op.create_table(
        'leave_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False, comment='学生ID'),
        sa.Column('leave_type', sa.String(20), nullable=False, comment='请假类型: sick/personal/other'),
        sa.Column('leave_reason', sa.Text(), nullable=False, comment='请假事由'),
        sa.Column('leave_start_time', sa.DateTime(), nullable=False, comment='请假开始时间'),
        sa.Column('leave_end_time', sa.DateTime(), nullable=False, comment='请假结束时间'),
        sa.Column('parent_phone', sa.String(20), nullable=False, comment='家长手机号'),
        sa.Column('teacher_status', sa.String(20), nullable=False, default='pending', comment='老师审批状态'),
        sa.Column('teacher_approved_by', sa.Integer(), nullable=True, comment='审批老师ID'),
        sa.Column('teacher_approved_at', sa.DateTime(), nullable=True, comment='审批时间'),
        sa.Column('teacher_rejection_reason', sa.Text(), nullable=True, comment='拒绝原因'),
        sa.Column('parent_verify_code', sa.String(6), nullable=True, comment='家长验证码'),
        sa.Column('parent_verified', sa.Boolean(), nullable=False, default=False, comment='家长是否已验证'),
        sa.Column('parent_verified_at', sa.DateTime(), nullable=True, comment='家长验证时间'),
        sa.Column('leave_pass_code', sa.String(6), nullable=True, comment='离校通行码'),
        sa.Column('pass_status', sa.String(20), nullable=False, default='pending', comment='通行状态'),
        sa.Column('used_count', sa.Integer(), nullable=False, default=0, comment='使用次数'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='过期时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['teacher_approved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_leave_requests_student_id', 'leave_requests', ['student_id'])
    op.create_index('idx_leave_requests_teacher_status', 'leave_requests', ['teacher_status'])
    op.create_index('idx_leave_requests_pass_code', 'leave_requests', ['leave_pass_code'])

    # 3. 创建访问日志表（外网）
    op.create_table(
        'access_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID（访客可为NULL）'),
        sa.Column('access_type', sa.String(20), nullable=False, comment='访问类型: dynamic_code/visit/leave'),
        sa.Column('access_code', sa.String(6), nullable=False, comment='访问码'),
        sa.Column('verification_result', sa.Boolean(), nullable=False, comment='验证结果'),
        sa.Column('verified_by', sa.String(50), nullable=True, comment='门卫用户名'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_access_logs_type', 'access_logs', ['access_type'])
    op.create_index('idx_access_logs_created_at', 'access_logs', ['created_at'])

    # 4. 为event_registrations表添加二维码字段（如果需要）
    try:
        op.add_column('event_registrations',
            sa.Column('qr_code', sa.String(100), nullable=True, comment='活动签到二维码')
        )
    except Exception as e:
        print(f"添加event_registrations字段失败: {e}")

    # ========================================
    # 内网数据库表（门卫系统）
    # ========================================

    # 5. 创建用户验证信息表（内网）
    op.create_table(
        'user_verification',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='外网用户ID'),
        sa.Column('phone', sa.String(20), nullable=False, comment='手机号'),
        sa.Column('pin_hash', sa.String(64), nullable=False, comment='2位PIN的SHA256哈希'),
        sa.Column('real_name', sa.String(100), nullable=False, comment='真实姓名'),
        sa.Column('user_type', sa.String(20), nullable=False, comment='用户类型'),
        sa.Column('student_no', sa.String(50), nullable=True, comment='学号'),
        sa.Column('employee_no', sa.String(50), nullable=True, comment='工号'),
        sa.Column('photo_url', sa.String(255), nullable=True, comment='照片URL'),
        sa.Column('key_version', sa.Integer(), nullable=False, default=1, comment='密钥版本'),
        sa.Column('synced_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='同步时间'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='数据过期时间'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='是否激活'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone')
    )
    op.create_index('idx_user_verification_phone', 'user_verification', ['phone'])
    op.create_index('idx_user_verification_user_id', 'user_verification', ['user_id'])

    # 6. 创建动态码缓存表（内网，用于快速验证）
    op.create_table(
        'dynamic_codes_cache',
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('timestamp', sa.Integer(), nullable=False, comment='生成时间戳（分钟级）'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='过期时间'),
        sa.Column('blacklisted', sa.Boolean(), nullable=False, default=False, comment='是否被撤销'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('code'),
        sa.ForeignKeyConstraint(['user_id'], ['user_verification.id'], )
    )
    op.create_index('idx_dynamic_codes_expires', 'dynamic_codes_cache', ['expires_at'])

    # 7. 创建访客通行码表（内网）
    op.create_table(
        'visit_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('visitor_name', sa.String(100), nullable=False),
        sa.Column('id_card_last4', sa.String(4), nullable=True),
        sa.Column('host_name', sa.String(100), nullable=False),
        sa.Column('visit_reason', sa.Text(), nullable=False),
        sa.Column('visit_date', sa.Date(), nullable=False),
        sa.Column('approved', sa.Boolean(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_uses', sa.Integer(), nullable=False, default=1),
        sa.Column('synced_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_visit_codes_code', 'visit_codes', ['code'])
    op.create_index('idx_visit_codes_expires', 'visit_codes', ['expires_at'])

    # 8. 创建离校通行码表（内网）
    op.create_table(
        'leave_passes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('student_name', sa.String(100), nullable=False),
        sa.Column('leave_type', sa.String(20), nullable=False),
        sa.Column('leave_start_time', sa.DateTime(), nullable=False),
        sa.Column('leave_end_time', sa.DateTime(), nullable=False),
        sa.Column('teacher_approved', sa.Boolean(), nullable=False),
        sa.Column('parent_verified', sa.Boolean(), nullable=False),
        sa.Column('pass_status', sa.String(20), nullable=False),
        sa.Column('used_count', sa.Integer(), nullable=False, default=0),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('synced_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_leave_passes_code', 'leave_passes', ['code'])
    op.create_index('idx_leave_passes_expires', 'leave_passes', ['expires_at'])

    # 9. 创建验证日志表（内网）
    op.create_table(
        'verification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code_type', sa.String(20), nullable=False, comment='类型: dynamic/visit/leave'),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('verification_result', sa.Boolean(), nullable=False),
        sa.Column('verified_by', sa.String(50), nullable=False, comment='门卫用户名'),
        sa.Column('user_name', sa.String(100), nullable=True, comment='用户姓名'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_verification_logs_type', 'verification_logs', ['code_type'])
    op.create_index('idx_verification_logs_created', 'verification_logs', ['created_at'])


def downgrade():
    """回滚迁移"""

    # 删除内网表
    op.drop_index('idx_verification_logs_created', table_name='verification_logs')
    op.drop_index('idx_verification_logs_type', table_name='verification_logs')
    op.drop_table('verification_logs')

    op.drop_index('idx_leave_passes_expires', table_name='leave_passes')
    op.drop_index('idx_leave_passes_code', table_name='leave_passes')
    op.drop_table('leave_passes')

    op.drop_index('idx_visit_codes_expires', table_name='visit_codes')
    op.drop_index('idx_visit_codes_code', table_name='visit_codes')
    op.drop_table('visit_codes')

    op.drop_index('idx_dynamic_codes_expires', table_name='dynamic_codes_cache')
    op.drop_table('dynamic_codes_cache')

    op.drop_index('idx_user_verification_user_id', table_name='user_verification')
    op.drop_index('idx_user_verification_phone', table_name='user_verification')
    op.drop_table('user_verification')

    # 删除外网表
    try:
        op.drop_column('event_registrations', 'qr_code')
    except:
        pass

    op.drop_index('idx_access_logs_created_at', table_name='access_logs')
    op.drop_index('idx_access_logs_type', table_name='access_logs')
    op.drop_table('access_logs')

    op.drop_index('idx_leave_requests_pass_code', table_name='leave_requests')
    op.drop_index('idx_leave_requests_teacher_status', table_name='leave_requests')
    op.drop_index('idx_leave_requests_student_id', table_name='leave_requests')
    op.drop_table('leave_requests')

    # 删除users表新增字段
    try:
        op.drop_column('users', 'public_key')
        op.drop_column('users', 'private_key')
        op.drop_column('users', 'key_expires_at')
        op.drop_column('users', 'key_version')
        op.drop_column('users', 'pin_hash')
    except:
        pass
