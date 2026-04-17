"""add_face_history_table

Revision ID: 3d6d2f579e9b
Revises: 9feae9648337
Create Date: 2025-11-05 11:43:07.060783

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d6d2f579e9b'
down_revision = '9feae9648337'
branch_labels = None
depends_on = None


def upgrade():
    # Create face_history table
    op.create_table('face_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('face_encoding', sa.Text(), nullable=False),
        sa.Column('face_image_path', sa.String(length=500), nullable=True),
        sa.Column('operation_type', sa.Enum('register', 'update', 'delete', name='operation_type'), nullable=False),
        sa.Column('previous_face_id', sa.Integer(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('verification_method', sa.Enum('auto', 'manual', 'comparison', name='verification_method'), nullable=True),
        sa.Column('verification_score', sa.Float(), nullable=True),
        sa.Column('verification_admin_id', sa.Integer(), nullable=True),
        sa.Column('verification_note', sa.Text(), nullable=True),
        sa.Column('verification_time', sa.DateTime(), nullable=True),
        sa.Column('device_info', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('active', 'inactive', 'suspicious', 'rejected', name='face_status'), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['verification_admin_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_face_history_user_id'), 'face_history', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_face_history_user_id'), table_name='face_history')
    op.drop_table('face_history')
