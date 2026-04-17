"""Add survey tables

Revision ID: add_survey_tables
Revises: 9feae9648337
Create Date: 2025-11-09 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_survey_tables'
down_revision = '9feae9648337'
branch_labels = None
depends_on = None

def upgrade():
    # 创建 surveys 表
    op.create_table('surveys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False, comment='问卷标题'),
        sa.Column('description', sa.Text(), nullable=True, comment='问卷描述'),
        sa.Column('event_id', sa.Integer(), nullable=True, comment='关联的校历事件ID'),
        sa.Column('is_anonymous', sa.Boolean(), nullable=True, default=False, comment='是否匿名问卷'),
        sa.Column('is_public', sa.Boolean(), nullable=True, default=True, comment='是否公开'),
        sa.Column('require_login', sa.Boolean(), nullable=True, default=True, comment='是否需要登录'),
        sa.Column('start_time', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP'), comment='开始时间'),
        sa.Column('end_time', sa.DateTime(), nullable=True, comment='结束时间'),
        sa.Column('status', sa.Enum('draft', 'published', 'closed', 'archived'), nullable=True, default='draft', comment='状态'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['event_id'], ['school_calendar.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_surveys_created_by'), 'surveys', ['created_by'], unique=False)
    op.create_index(op.f('ix_surveys_event_id'), 'surveys', ['event_id'], unique=False)
    op.create_index(op.f('ix_surveys_id'), 'surveys', ['id'], unique=False)

    # 创建 survey_questions 表
    op.create_table('survey_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('survey_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False, comment='问题内容'),
        sa.Column('question_type', sa.Enum('single_choice', 'multiple_choice', 'text', 'textarea', 'rating', 'number'), nullable=False, comment='问题类型'),
        sa.Column('options', sa.Text(), nullable=True, comment='选项JSON，用于选择题'),
        sa.Column('is_required', sa.Boolean(), nullable=True, default=True, comment='是否必答'),
        sa.Column('order_index', sa.Integer(), nullable=True, default=0, comment='排序索引'),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['survey_id'], ['surveys.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_survey_questions_id'), 'survey_questions', ['id'], unique=False)
    op.create_index(op.f('ix_survey_questions_survey_id'), 'survey_questions', ['survey_id'], unique=False)

    # 创建 survey_responses 表
    op.create_table('survey_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('survey_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='回答用户ID'),
        sa.Column('answers', sa.Text(), nullable=False, comment='回答内容JSON'),
        sa.Column('status', sa.Enum('draft', 'completed'), nullable=True, default='draft', comment='状态'),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        sa.ForeignKeyConstraint(['survey_id'], ['surveys.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_survey_responses_id'), 'survey_responses', ['id'], unique=False)
    op.create_index(op.f('ix_survey_responses_survey_id'), 'survey_responses', ['survey_id'], unique=False)
    op.create_index(op.f('ix_survey_responses_user_id'), 'survey_responses', ['user_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_survey_responses_user_id'), table_name='survey_responses')
    op.drop_index(op.f('ix_survey_responses_survey_id'), table_name='survey_responses')
    op.drop_index(op.f('ix_survey_responses_id'), table_name='survey_responses')
    op.drop_table('survey_responses')
    op.drop_index(op.f('ix_survey_questions_survey_id'), table_name='survey_questions')
    op.drop_index(op.f('ix_survey_questions_id'), table_name='survey_questions')
    op.drop_table('survey_questions')
    op.drop_index(op.f('ix_surveys_event_id'), table_name='surveys')
    op.drop_index(op.f('ix_surveys_created_by'), table_name='surveys')
    op.drop_index(op.f('ix_surveys_id'), table_name='surveys')
    op.drop_table('surveys')