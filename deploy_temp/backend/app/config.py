"""
应用配置
"""

import os
from datetime import timedelta

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-secret-key-change-in-production'
    ELECTRONIC_CARD_SECRET_KEY = os.environ.get('ELECTRONIC_CARD_SECRET_KEY') or 'electronic-card-hmac-secret-key-2026-please-change-in-production'

    # HMAC动态码密钥配置
    # 前端和后端使用相同的密钥
    HMAC_SECRET_KEY = os.environ.get('HMAC_SECRET_KEY') or 'ls-alumni-access-code-hmac-2026-secret-do-not-expose'

    # 时间窗口配置（分钟）
    HMAC_TIME_WINDOW_TEACHER = 24 * 60  # 老师审批：24小时（1440分钟）
    HMAC_TIME_WINDOW_GUARD = 3  # 门卫验证：3分钟

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # 1小时

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    # 使用绝对路径确保数据库文件能被正确找到
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", "alumni_system_dev.db")}'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-alumni-jwt-secret-key-2025'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # 开发环境24小时，方便测试
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    FACE_RECOGNITION_TOLERANCE = 0.6
    FACE_IMAGE_SIZE = (300, 300)
    SSL_CERT = '../config/certificates/localhost.crt'
    SSL_KEY = '../config/certificates/localhost.key'

    # === Redis缓存配置 ===
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    REDIS_DB = int(os.environ.get('REDIS_DB') or 0)
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD') or None
    CACHE_ENABLED = True  # 开发环境启用缓存

    # === 数据库连接池优化（开发环境）===
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,           # 开发环境适中配置
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 3600,      # 1小时回收
        'pool_pre_ping': True,     # 连接前ping测试
        'echo_pool': False,        # 开发环境关闭连接池日志
    }

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

    # 数据库配置 - 支持MySQL和SQLite
    # 优先使用环境变量DATABASE_URL（支持腾讯云MySQL、微信云数据库等）
    # 如果未设置，则使用SQLite（微信云托管建议使用云数据库）
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        SQLALCHEMY_DATABASE_URI = database_url
    elif os.environ.get('WECHAT_CLOUD'):
        # 微信云托管环境 - 使用云数据库
        # 需要在环境变量中设置 DATABASE_URL
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            'sqlite:///alumni_system.db'
    else:
        # 默认使用SQLite
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", "alumni_system_prod.db")}'

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'production-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)  # 30分钟

    # 上传文件夹配置 - 兼容本地和云端
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or '/app/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    FACE_RECOGNITION_TOLERANCE = 0.5
    FACE_IMAGE_SIZE = (400, 400)

    # SSL证书配置（仅在需要HTTPS时使用）
    SSL_CERT = os.environ.get('SSL_CERT_PATH') or '/etc/ssl/certs/alumni_system.crt'
    SSL_KEY = os.environ.get('SSL_KEY_PATH') or '/etc/ssl/private/alumni_system.key'

    # === Redis缓存配置（生产环境）===
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    REDIS_DB = int(os.environ.get('REDIS_DB') or 0)
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD') or None
    CACHE_ENABLED = os.environ.get('CACHE_ENABLED', 'true').lower() == 'true'  # 生产环境默认启用缓存

    # === 数据库连接池优化（生产环境 - 3万用户场景）===
    # 如果使用SQLite，连接池配置会被忽略
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,           # 核心连接数（支持高并发）
        'max_overflow': 40,        # 最大溢出连接（峰值连接数 = 20 + 40 = 60）
        'pool_timeout': 30,        # 连接超时时间
        'pool_recycle': 1800,      # 连接回收时间（30分钟，防止连接泄漏）
        'pool_pre_ping': True,     # 连接前ping测试（确保连接有效）
        'echo_pool': False,        # 生产环境关闭连接池日志
    }

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}