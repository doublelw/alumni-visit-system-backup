"""remove_unique_username_constraint_and_enhance_registration

Revision ID: remove_unique_username_constraint
Revises: allow_null_email_and_id_card_sqlite
Create Date: 2025-11-14 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_unique_username_constraint'
down_revision = 'allow_null_email_and_id_card_sqlite'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite compatible approach: create new users table without UNIQUE constraint on username

    # 1. Create new users table without UNIQUE constraint on username
    op.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            real_name VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20) NOT NULL,
            user_type VARCHAR(255) DEFAULT 'alumni' NOT NULL,
            status VARCHAR(20) DEFAULT 'pending' NOT NULL,
            organization_id INTEGER,
            student_id VARCHAR(50),
            employee_id VARCHAR(50),
            is_visitable BOOLEAN DEFAULT 0 NOT NULL,
            class_id VARCHAR(50),
            grade VARCHAR(20),
            parent_student_id INTEGER,
            student_parent_id INTEGER,
            wechat VARCHAR(50),
            wechat_openid VARCHAR(100),
            wechat_nickname VARCHAR(100),
            is_class_teacher BOOLEAN DEFAULT 0 NOT NULL,
            uuid VARCHAR(36) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organization_id) REFERENCES organizations (id),
            FOREIGN KEY (parent_student_id) REFERENCES users (id),
            FOREIGN KEY (student_parent_id) REFERENCES users (id)
        )
    """)

    # 2. Copy data from users to users_new
    op.execute("""
        INSERT INTO users_new (
            id, uuid, username, password_hash, real_name, email, phone, user_type, status,
            organization_id, student_id, employee_id, is_visitable, class_id, grade,
            parent_student_id, student_parent_id, wechat, wechat_openid, wechat_nickname,
            is_class_teacher, created_at, updated_at
        )
        SELECT
            id, uuid, username, password_hash, real_name, email, phone, user_type, status,
            organization_id, student_id, employee_id, is_visitable, class_id, grade,
            parent_student_id, student_parent_id, wechat, wechat_openid, wechat_nickname,
            is_class_teacher, created_at, updated_at
        FROM users
    """)

    # 3. Drop old users table and rename users_new to users
    op.execute("DROP TABLE users")
    op.execute("ALTER TABLE users_new RENAME TO users")

    # 4. Recreate indexes (except unique constraint on username)
    op.execute("CREATE INDEX ix_users_uuid ON users(uuid)")
    op.execute("CREATE INDEX ix_users_phone ON users(phone)")

    # Keep partial unique index on email for non-NULL values
    op.execute("CREATE UNIQUE INDEX ix_users_email_partial ON users(email) WHERE email IS NOT NULL AND email != ''")


def downgrade():
    # Revert back to original schema with UNIQUE constraint on username

    # 1. Create original users table structure with UNIQUE constraint on username
    op.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid VARCHAR(36) UNIQUE NOT NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            real_name VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20) NOT NULL,
            user_type VARCHAR(255) DEFAULT 'alumni' NOT NULL,
            status VARCHAR(20) DEFAULT 'pending' NOT NULL,
            organization_id INTEGER,
            student_id VARCHAR(50),
            employee_id VARCHAR(50),
            is_visitable BOOLEAN DEFAULT 0 NOT NULL,
            class_id VARCHAR(50),
            grade VARCHAR(20),
            parent_student_id INTEGER,
            student_parent_id INTEGER,
            wechat VARCHAR(50),
            wechat_openid VARCHAR(100),
            wechat_nickname VARCHAR(100),
            is_class_teacher BOOLEAN DEFAULT 0 NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organization_id) REFERENCES organizations (id),
            FOREIGN KEY (parent_student_id) REFERENCES users (id),
            FOREIGN KEY (student_parent_id) REFERENCES users (id)
        )
    """)

    # 2. Copy data back
    op.execute("""
        INSERT INTO users_new (
            id, uuid, username, password_hash, real_name, email, phone, user_type, status,
            organization_id, student_id, employee_id, is_visitable, class_id, grade,
            parent_student_id, student_parent_id, wechat, wechat_openid, wechat_nickname,
            is_class_teacher, created_at, updated_at
        )
        SELECT
            id, uuid, username, password_hash, real_name, email, phone, user_type, status,
            organization_id, student_id, employee_id, is_visitable, class_id, grade,
            parent_student_id, student_parent_id, wechat, wechat_openid, wechat_nickname,
            is_class_teacher, created_at, updated_at
        FROM users
    """)

    # 3. Replace table
    op.execute("DROP TABLE users")
    op.execute("ALTER TABLE users_new RENAME TO users")

    # 4. Recreate indexes
    op.execute("CREATE UNIQUE INDEX ix_users_uuid ON users(uuid)")
    op.execute("CREATE UNIQUE INDEX ix_users_username ON users(username)")
    op.execute("CREATE INDEX ix_users_phone ON users(phone)")
    op.execute("CREATE UNIQUE INDEX ix_users_email_partial ON users(email) WHERE email IS NOT NULL AND email != ''")