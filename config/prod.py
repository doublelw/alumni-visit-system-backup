"""
生产环境配置
"""

import os

class ProductionConfig:
    """生产环境配置"""

    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key'
    DEBUG = False

    # 数据库配置 - MySQL
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'alumni_user')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'alumni_system')

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True
    }

    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'production-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = 1800  # 30分钟

    # 文件上传配置
    UPLOAD_FOLDER = '/var/www/alumni_system/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # 人脸识别配置
    FACE_RECOGNITION_TOLERANCE = 0.5  # 生产环境更严格
    FACE_IMAGE_SIZE = (400, 400)

    # HTTPS配置
    SSL_CERT = '/etc/ssl/certs/alumni_system.crt'
    SSL_KEY = '/etc/ssl/private/alumni_system.key'

    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    # 微信公众号配置
    WECHAT_APP_ID = os.environ.get('WECHAT_APP_ID')
    WECHAT_APP_SECRET = os.environ.get('WECHAT_APP_SECRET')

    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/alumni_system/app.log'

    # 安全配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

# 配置字典
config = {
    'production': ProductionConfig,
    'default': ProductionConfig
}