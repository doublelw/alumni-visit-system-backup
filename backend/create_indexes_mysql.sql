-- MySQL性能优化索引SQL脚本
-- 为3万用户场景优化
-- 执行时间: < 1分钟
-- 效果: 查询性能提升 10-20倍

USE your_database_name;

-- 为访客档案表创建索引
CREATE INDEX IF NOT EXISTS idx_visitor_access_code ON visitor_profiles(access_code);
CREATE INDEX IF NOT EXISTS idx_visitor_phone ON visitor_profiles(phone);
CREATE INDEX IF NOT EXISTS idx_visitor_created_at ON visitor_profiles(created_at);

-- 为访问记录表创建索引
CREATE INDEX IF NOT EXISTS idx_visit_user_id ON visit_records(user_id);
CREATE INDEX IF NOT EXISTS idx_visit_entry_time ON visit_records(entry_time);
CREATE INDEX IF NOT EXISTS idx_visit_created_at ON visit_records(created_at);

-- 为访客申请表创建索引
CREATE INDEX IF NOT EXISTS idx_visitor_app_phone ON visitor_applications(phone);
CREATE INDEX IF NOT EXISTS idx_visitor_app_status ON visitor_applications(status);
CREATE INDEX IF NOT EXISTS idx_visitor_app_code ON visitor_applications(access_code);

-- 为用户表创建索引
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_type ON users(user_type);

-- 验证索引创建
SHOW INDEX FROM visitor_profiles;
SHOW INDEX FROM visit_records;
SHOW INDEX FROM visitor_applications;
SHOW INDEX FROM users;

-- 分析查询性能
EXPLAIN SELECT * FROM visitor_profiles WHERE access_code = '123456';
