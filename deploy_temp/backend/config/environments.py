"""
环境配置管理
支持开发、测试和生产环境的配置
"""

import os
from typing import Dict, Any

class EnvironmentConfig:
    """环境配置类"""

    def __init__(self):
        self.env = os.environ.get('FLASK_ENV', 'development')
        self.config = self._get_config()

    def _get_config(self) -> Dict[str, Any]:
        """根据环境获取配置"""
        if self.env == 'production':
            return self._production_config()
        elif self.env == 'testing':
            return self._testing_config()
        else:
            return self._development_config()

    def _development_config(self) -> Dict[str, Any]:
        """开发环境配置"""
        return {
            'DEBUG': True,
            'TESTING': False,

            # 数据库配置
            'SQLALCHEMY_DATABASE_URI': os.environ.get(
                'DEV_DATABASE_URL',
                'sqlite:///alumni_system.db'
            ),
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,

            # SSL配置
            'SSL_ENABLED': os.environ.get('SSL_ENABLED', 'true').lower() == 'true',
            'SSL_CERT': os.environ.get('SSL_CERT', '../config/certificates/localhost.crt'),
            'SSL_KEY': os.environ.get('SSL_KEY', '../config/certificates/localhost.key'),

            # 服务器配置
            'HOST': os.environ.get('HOST', '0.0.0.0'),
            'PORT': int(os.environ.get('PORT', 5000)),

            # JWT配置
            'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production'),
            'JWT_ACCESS_TOKEN_EXPIRES': 3600,  # 1小时

            # 邮件配置
            'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'localhost'),
            'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
            'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS', 'false').lower() == 'true',
            'MAIL_USERNAME': os.environ.get('MAIL_USERNAME', ''),
            'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD', ''),

            # 文件上传配置
            'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
            'UPLOAD_FOLDER': os.environ.get('UPLOAD_FOLDER', 'uploads'),

            # 应用配置
            'SITE_NAME': '校友入校登记系统',
            'ADMIN_EMAIL': os.environ.get('ADMIN_EMAIL', 'admin@school.edu'),
            'TIMEZONE': 'Asia/Shanghai'
        }

    def _testing_config(self) -> Dict[str, Any]:
        """测试环境配置"""
        config = self._development_config()
        config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'JWT_ACCESS_TOKEN_EXPIRES': 60  # 1分钟
        })
        return config

    def _production_config(self) -> Dict[str, Any]:
        """生产环境配置"""
        return {
            'DEBUG': False,
            'TESTING': False,

            # 数据库配置
            'SQLALCHEMY_DATABASE_URI': os.environ.get(
                'DATABASE_URL',
                'mysql+pymysql://lsalumni:password@localhost/lsalumni'
            ),
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_size': 10,
                'pool_recycle': 120,
                'pool_pre_ping': True
            },

            # SSL配置
            'SSL_ENABLED': os.environ.get('SSL_ENABLED', 'true').lower() == 'true',
            'SSL_CERT': os.environ.get('SSL_CERT', '/etc/ssl/certs/alumni_system.crt'),
            'SSL_KEY': os.environ.get('SSL_KEY', '/etc/ssl/private/alumni_system.key'),

            # 服务器配置
            'HOST': os.environ.get('HOST', '127.0.0.1'),
            'PORT': int(os.environ.get('PORT', 5000)),

            # JWT配置
            'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY'),
            'JWT_ACCESS_TOKEN_EXPIRES': 1800,  # 30分钟

            # 邮件配置
            'MAIL_SERVER': os.environ.get('MAIL_SERVER'),
            'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
            'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true',
            'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
            'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),

            # 文件上传配置
            'MAX_CONTENT_LENGTH': 10 * 1024 * 1024,  # 10MB
            'UPLOAD_FOLDER': os.environ.get('UPLOAD_FOLDER', '/var/www/alumni_system/uploads'),

            # 应用配置
            'SITE_NAME': os.environ.get('SITE_NAME', '校友入校登记系统'),
            'ADMIN_EMAIL': os.environ.get('ADMIN_EMAIL'),
            'TIMEZONE': 'Asia/Shanghai'
        }

    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)

    def update_from_env(self):
        """从环境变量更新配置"""
        # 允许通过环境变量覆盖任何配置
        for key, value in os.environ.items():
            if key.startswith('ALUMNI_'):
                config_key = key[7:]  # 移除 'ALUMNI_' 前缀
                if config_key in self.config:
                    # 类型转换
                    if isinstance(self.config[config_key], bool):
                        self.config[config_key] = value.lower() in ('true', '1', 'yes')
                    elif isinstance(self.config[config_key], int):
                        self.config[config_key] = int(value)
                    else:
                        self.config[config_key] = value

# 全局配置实例
env_config = EnvironmentConfig()
env_config.update_from_env()

def get_config(key: str, default=None):
    """获取配置的便捷函数"""
    return env_config.get(key, default)

def is_development() -> bool:
    """是否为开发环境"""
    return env_config.env == 'development'

def is_production() -> bool:
    """是否为生产环境"""
    return env_config.env == 'production'

def is_testing() -> bool:
    """是否为测试环境"""
    return env_config.env == 'testing'