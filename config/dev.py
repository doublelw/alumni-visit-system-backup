"""
开发环境配置
"""

import os

class DevelopmentConfig:
    """开发环境配置"""

    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = True

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'sqlite:///alumni_system_dev.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时

    # 文件上传配置
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # 人脸识别配置
    FACE_RECOGNITION_TOLERANCE = 0.6
    FACE_IMAGE_SIZE = (300, 300)

    # HTTPS配置
    SSL_CERT = '../config/certificates/localhost.crt'
    SSL_KEY = '../config/certificates/localhost.key'

    # 邮件配置（开发环境使用测试配置）
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'test@example.com'
    MAIL_PASSWORD = 'test-password'

    # 微信公众号配置（测试）
    WECHAT_APP_ID = 'test-app-id'
    WECHAT_APP_SECRET = 'test-app-secret'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}