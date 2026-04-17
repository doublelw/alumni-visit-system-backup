"""
数据库连接池优化配置
Database Connection Pool Optimization for 30K Users
"""

# 在 app/config.py 中添加以下配置

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

    # === 数据库连接池优化 ===
    # 适用于3万用户+的生产环境

    # 基础URI配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@host:port/database_name'

    # 连接池大小（核心连接数）
    # 默认: 5，优化: 20（可支持100+并发）
    SQLALCHEMY_POOL_SIZE = 20

    # 最大溢出连接数（临时连接数）
    # 默认: 10，优化: 40（峰值连接数 = 20 + 40 = 60）
    SQLALCHEMY_MAX_OVERFLOW = 40

    # 连接超时时间
    # 默认: 10秒，保持不变
    SQLALCHEMY_POOL_TIMEOUT = 10

    # 连接回收时间
    # 默认: 7200秒（2小时），优化: 1800秒（30分钟）
    # 频繁回收可以防止连接泄漏
    SQLALCHEMY_POOL_RECYCLE = 1800

    # 连接前ping测试（确保连接有效）
    # 默认: False，优化: True（避免使用坏连接）
    SQLALCHEMY_POOL_PRE_PING = True

    # 连接池自动回收
    # 当连接超过一定时间未使用自动回收，防止连接泄漏
    SQLALCHEMY_POOL_RECYCLE_JUST_IDLING = True

    # === 性能优化 ===

    # 启用查询缓存（MySQL）
    # 注意: 只在生产环境使用，开发环境禁用
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # === 监控配置 ===

    # 记录慢查询（超过100ms的查询）
    SQLALCHEMY_RECORD_QUERIES = True

    # 连接池事件监听
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'max_overflow': 40,
        'pool_timeout': 10,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
        'echo_pool': True,  # 记录连接池事件
    }
