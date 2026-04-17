"""allow_null_email_and_id_card_sqlite

Revision ID: allow_null_email_and_id_card_sqlite
Revises:
Create Date: 2025-11-13 02:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'allow_null_email_and_id_card_sqlite'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # SQLite compatible approach: create new tables, copy data, replace old tables

    # 1. Create new users table without UNIQUE constraint on email and allowing NULL
    op.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120),
            password_hash VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT 0 NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Copy data from users to users_new, converting empty strings to NULL
    op.execute("""
        INSERT INTO users_new (id, username, email, password_hash, is_admin, created_at, updated_at)
        SELECT id, username,
               CASE WHEN email = '' THEN NULL ELSE email END,
               password_hash, is_admin, created_at, updated_at
        FROM users
    """)

    # 3. Drop old users table and rename users_new to users
    op.execute("DROP TABLE users")
    op.execute("ALTER TABLE users_new RENAME TO users")

    # Create partial unique index on email for non-NULL values
    op.execute("CREATE UNIQUE INDEX ix_users_email_partial ON users(email) WHERE email IS NOT NULL AND email != ''")

    # 4. Do the same for alumni_profiles table
    op.execute("""
        CREATE TABLE alumni_profiles_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            real_name VARCHAR(100) NOT NULL,
            graduation_year INTEGER NOT NULL,
            class_number VARCHAR(20) NOT NULL,
            division VARCHAR(100) NOT NULL,
            major VARCHAR(100) NOT NULL,
            class_teacher VARCHAR(100) NOT NULL,
            current_city VARCHAR(100) NOT NULL,
            work_unit VARCHAR(200) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            wechat VARCHAR(100),
            emergency_contact VARCHAR(100),
            emergency_phone VARCHAR(20),
            id_card VARCHAR(20),
            face_encoding TEXT,
            is_approved BOOLEAN DEFAULT 0 NOT NULL,
            approved_at DATETIME,
            approved_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (approved_by) REFERENCES users (id)
        )
    """)

    # 5. Copy data from alumni_profiles to alumni_profiles_new, converting empty strings to NULL
    op.execute("""
        INSERT INTO alumni_profiles_new (
            id, user_id, real_name, graduation_year, class_number, division, major,
            class_teacher, current_city, work_unit, phone, wechat, emergency_contact,
            emergency_phone, id_card, face_encoding, is_approved, approved_at,
            approved_by, created_at, updated_at
        )
        SELECT
            id, user_id, real_name, graduation_year, class_number, division, major,
            class_teacher, current_city, work_unit, phone, wechat, emergency_contact,
            emergency_phone,
            CASE WHEN id_card = '' THEN NULL ELSE id_card END,
            face_encoding, is_approved, approved_at, approved_by, created_at, updated_at
        FROM alumni_profiles
    """)

    # 6. Drop old alumni_profiles table and rename new one
    op.execute("DROP TABLE alumni_profiles")
    op.execute("ALTER TABLE alumni_profiles_new RENAME TO alumni_profiles")

    # Create partial unique index on id_card for non-NULL values
    op.execute("CREATE UNIQUE INDEX uq_alumni_profiles_id_card_partial ON alumni_profiles(id_card) WHERE id_card IS NOT NULL AND id_card != ''")


def downgrade():
    # Revert back to original schema with NOT NULL and UNIQUE constraints

    # 1. Create original users table structure
    op.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT 0 NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Copy data, converting NULL to empty string
    op.execute("""
        INSERT INTO users_new (id, username, email, password_hash, is_admin, created_at, updated_at)
        SELECT id, username,
               COALESCE(email, ''),
               password_hash, is_admin, created_at, updated_at
        FROM users
    """)

    # 3. Replace table
    op.execute("DROP TABLE users")
    op.execute("ALTER TABLE users_new RENAME TO users")

    # 4. Create original alumni_profiles table structure
    op.execute("""
        CREATE TABLE alumni_profiles_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            real_name VARCHAR(100) NOT NULL,
            graduation_year INTEGER NOT NULL,
            class_number VARCHAR(20) NOT NULL,
            division VARCHAR(100) NOT NULL,
            major VARCHAR(100) NOT NULL,
            class_teacher VARCHAR(100) NOT NULL,
            current_city VARCHAR(100) NOT NULL,
            work_unit VARCHAR(200) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            wechat VARCHAR(100),
            emergency_contact VARCHAR(100),
            emergency_phone VARCHAR(20),
            id_card VARCHAR(20) UNIQUE NOT NULL,
            face_encoding TEXT,
            is_approved BOOLEAN DEFAULT 0 NOT NULL,
            approved_at DATETIME,
            approved_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (approved_by) REFERENCES users (id)
        )
    """)

    # 5. Copy data, converting NULL to empty string
    op.execute("""
        INSERT INTO alumni_profiles_new (
            id, user_id, real_name, graduation_year, class_number, division, major,
            class_teacher, current_city, work_unit, phone, wechat, emergency_contact,
            emergency_phone, id_card, face_encoding, is_approved, approved_at,
            approved_by, created_at, updated_at
        )
        SELECT
            id, user_id, real_name, graduation_year, class_number, division, major,
            class_teacher, current_city, work_unit, phone, wechat, emergency_contact,
            emergency_phone,
            COALESCE(id_card, ''),
            face_encoding, is_approved, approved_at, approved_by, created_at, updated_at
        FROM alumni_profiles
    """)

    # 6. Replace table
    op.execute("DROP TABLE alumni_profiles")
    op.execute("ALTER TABLE alumni_profiles_new RENAME TO alumni_profiles")