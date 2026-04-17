-- 校友入校登记系统MySQL数据库设置脚本
-- 请在MySQL中执行此脚本来创建数据库和用户

-- 创建数据库
CREATE DATABASE IF NOT EXISTS alumni_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建专用用户（推荐）
CREATE USER IF NOT EXISTS 'alumni_user'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON alumni_system.* TO 'alumni_user'@'localhost';
FLUSH PRIVILEGES;

-- 显示创建的数据库
SHOW DATABASES LIKE 'alumni_system';

-- 显示用户权限
SHOW GRANTS FOR 'alumni_user'@'localhost';