"""
应用配置
"""

import os
from datetime import timedelta

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-secret-key-change-in-production'
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

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 使用SQLite数据库，避免MySQL连接问题
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", "alumni_system_prod.db")}'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'production-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)  # 30分钟
    UPLOAD_FOLDER = '/var/www/alumni_system/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    FACE_RECOGNITION_TOLERANCE = 0.5
    FACE_IMAGE_SIZE = (400, 400)
    SSL_CERT = '/etc/ssl/certs/alumni_system.crt'
    SSL_KEY = '/etc/ssl/private/alumni_system.key'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}