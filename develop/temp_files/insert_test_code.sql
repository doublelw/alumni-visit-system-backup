-- 创建测试验证码的SQL脚本
-- 先创建测试用户（如果不存在）
INSERT OR IGNORE INTO user_verification (username, real_name, user_type, student_no, phone, is_active, created_at)
VALUES ('test_user_2026', '测试学生', 'student', '2026001', '13800138000', 1, datetime('now'));

-- 获取用户ID并创建验证码（24小时有效）
INSERT INTO dynamic_codes_cache (code, user_id, expires_at, blacklisted, created_at)
SELECT
    '888888',  -- 测试验证码：888888
    (SELECT id FROM user_verification WHERE username = 'test_user_2026'),
    datetime('now', '+24 hours'),
    0,
    datetime('now')
WHERE NOT EXISTS (
    SELECT 1 FROM dynamic_codes_cache WHERE code = '888888' AND expires_at > datetime('now')
);

-- 查看创建的验证码
SELECT
    dc.code as '验证码',
    uv.real_name as '姓名',
    uv.user_type as '身份',
    uv.student_no as '学号',
    datetime(dc.expires_at) as '过期时间'
FROM dynamic_codes_cache dc
JOIN user_verification uv ON dc.user_id = uv.id
WHERE dc.code = '888888' AND dc.expires_at > datetime('now');
