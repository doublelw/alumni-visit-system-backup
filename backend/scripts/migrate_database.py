#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
校友入校登记系统 - 数据库迁移脚本
功能: 创建家长和访客数据模型表
使用: python migrate_database.py
"""

import os
import sys

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    app = create_app()

    with app.app_context():
        print("🚀 开始数据库迁移...")

        # 读取迁移SQL
        migration_sql = """
-- 创建家长档案表
CREATE TABLE IF NOT EXISTS parent_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    real_name VARCHAR(50) NOT NULL,
    id_card VARCHAR(18) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    wechat VARCHAR(100),
    occupation VARCHAR(100),
    workplace VARCHAR(200),
    work_address VARCHAR(200),
    relationship_type VARCHAR(20) NOT NULL,
    emergency_contact_name VARCHAR(50),
    emergency_contact_phone VARCHAR(20),
    emergency_contact_relationship VARCHAR(20),
    home_address VARCHAR(300),
    is_primary BOOLEAN DEFAULT 0,
    can_pick_up BOOLEAN DEFAULT 1,
    wechat_password VARCHAR(4),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- 创建家长-学生关联表
CREATE TABLE IF NOT EXISTS parent_student_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    relationship_type VARCHAR(20) NOT NULL,
    is_primary BOOLEAN DEFAULT 0,
    is_emergency_contact BOOLEAN DEFAULT 1,
    can_pick_up BOOLEAN DEFAULT 1,
    priority INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT 0,
    verified_at DATETIME,
    verified_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES users (id),
    FOREIGN KEY (student_id) REFERENCES users (id),
    FOREIGN KEY (verified_by) REFERENCES users (id),
    UNIQUE (parent_id, student_id)
);

-- 创建访客档案表
CREATE TABLE IF NOT EXISTS visitor_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    real_name VARCHAR(50) NOT NULL,
    id_card VARCHAR(18) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    visitor_type VARCHAR(20) DEFAULT 'individual',
    visitor_type_label VARCHAR(50),
    organization VARCHAR(200),
    organization_address VARCHAR(300),
    has_vehicle BOOLEAN DEFAULT 0,
    vehicle_plate VARCHAR(20),
    vehicle_type VARCHAR(20),
    vehicle_color VARCHAR(20),
    visit_purpose TEXT,
    target_department VARCHAR(100),
    target_person VARCHAR(100),
    target_person_id INTEGER,
    estimated_visit_date DATE,
    estimated_visit_duration INTEGER,
    companion_count INTEGER DEFAULT 0,
    companion_names TEXT,
    has_items BOOLEAN DEFAULT 0,
    items_description TEXT,
    health_declaration BOOLEAN DEFAULT 1,
    safety_agreement BOOLEAN DEFAULT 0,
    application_status VARCHAR(20) DEFAULT 'pending',
    approved_by INTEGER,
    approved_at DATETIME,
    rejection_reason TEXT,
    access_code VARCHAR(20) UNIQUE,
    qr_code VARCHAR(500),
    actual_visit_time DATETIME,
    actual_leave_time DATETIME,
    visit_completed BOOLEAN DEFAULT 0,
    is_blacklisted BOOLEAN DEFAULT 0,
    blacklist_reason TEXT,
    blacklisted_at DATETIME,
    blacklisted_by INTEGER,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (target_person_id) REFERENCES users (id),
    FOREIGN KEY (approved_by) REFERENCES users (id),
    FOREIGN KEY (blacklisted_by) REFERENCES users (id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_parent_profiles_user_id ON parent_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_parent_profiles_id_card ON parent_profiles(id_card);
CREATE INDEX IF NOT EXISTS idx_parent_student_relations_parent_id ON parent_student_relations(parent_id);
CREATE INDEX IF NOT EXISTS idx_parent_student_relations_student_id ON parent_student_relations(student_id);
CREATE INDEX IF NOT EXISTS idx_visitor_profiles_user_id ON visitor_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_visitor_profiles_access_code ON visitor_profiles(access_code);
CREATE INDEX IF NOT EXISTS idx_visitor_profiles_application_status ON visitor_profiles(application_status);
        """

        # 执行SQL
        from app.models import VisitApplication

        # 使用SQLAlchemy执行原始SQL
        db.session.execute(db.text(migration_sql))
        db.session.commit()

        print("✅ 数据库表创建完成")
        print("✅ 索引创建完成")

        print("\n📋 已创建以下表:")
        print("  ✅ parent_profiles - 家长档案表")
        print("  ✅ parent_student_relations - 家长-学生关联表")
        print("  ✅ visitor_profiles - 访客档案表")

        print("\n🎉 数据库迁移完成！")

if __name__ == '__main__':
    try:
        migrate_database()
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
