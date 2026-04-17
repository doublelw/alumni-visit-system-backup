"""
Redis缓存管理器 - 为3万用户场景优化
Redis Cache Manager for 30K Users Scenario

功能:
- 缓存热点数据（访客信息）
- 缓存验证结果（24小时有效）
- 自动缓存过期管理
"""

import redis
import json
import hashlib
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis缓存管理器"""

    def __init__(self, redis_host='localhost', redis_port=6379,
                 redis_db=0, password=None):
        """初始化Redis连接"""
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=password,
            decode_responses=True,  # 自动解码
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )

        # 测试连接
        try:
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}")
            logger.warning("将使用降级模式（无缓存）")
            self.redis_client = None

    def is_available(self):
        """检查Redis是否可用"""
        return self.redis_client is not None

    def cache_visitor(self, access_code, visitor_data, ttl=3600):
        """
        缓存访客信息

        Args:
            access_code: 6位访问码
            visitor_data: 访客数据字典
            ttl: 缓存时间（秒），默认1小时
        """
        if not self.is_available():
            return False

        try:
            key = f"visitor:access_code:{access_code}"
            self.redis_client.setex(key, ttl, json.dumps(visitor_data, ensure_ascii=False))
            logger.debug(f"缓存访客信息: {access_code}")
            return True
        except Exception as e:
            logger.error(f"缓存访客信息失败: {e}")
            return False

    def get_cached_visitor(self, access_code):
        """
        获取缓存的访客信息

        Args:
            access_code: 6位访问码

        Returns:
            访客数据字典或None
        """
        if not self.is_available():
            return None

        try:
            key = f"visitor:access_code:{access_code}"
            data = self.redis_client.get(key)
            if data:
                logger.debug(f"缓存命中: {access_code}")
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None

    def cache_verification_result(self, phone, result, ttl=86400):
        """
        缓存验证结果（24小时有效）

        Args:
            phone: 手机号
            result: 验证结果字典
            ttl: 缓存时间（秒），默认24小时
        """
        if not self.is_available():
            return False

        try:
            # 使用手机号的MD5作为key的一部分
            phone_hash = hashlib.md5(phone.encode()).hexdigest()
            key = f"verify:phone:{phone_hash}"
            self.redis_client.setex(key, ttl, json.dumps(result, ensure_ascii=False))
            logger.debug(f"缓存验证结果: {phone}")
            return True
        except Exception as e:
            logger.error(f"缓存验证结果失败: {e}")
            return False

    def get_cached_verification(self, phone):
        """获取缓存的验证结果"""
        if not self.is_available():
            return None

        try:
            phone_hash = hashlib.md5(phone.encode()).hexdigest()
            key = f"verify:phone:{phone_hash}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"获取验证缓存失败: {e}")
            return None

    def cache_user_info(self, user_id, user_data, ttl=1800):
        """
        缓存用户信息（30分钟）
        """
        if not self.is_available():
            return False

        try:
            key = f"user:info:{user_id}"
            self.redis_client.setex(key, ttl, json.dumps(user_data, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"缓存用户信息失败: {e}")
            return False

    def get_cached_user_info(self, user_id):
        """获取缓存的用户信息"""
        if not self.is_available():
            return None

        try:
            key = f"user:info:{user_id}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"获取用户缓存失败: {e}")
            return None

    def cache_statistics(self, stats_key, stats_data, ttl=300):
        """
        缓存统计数据（5分钟）
        """
        if not self.is_available():
            return False

        try:
            key = f"stats:{stats_key}"
            self.redis_client.setex(key, ttl, json.dumps(stats_data, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"缓存统计失败: {e}")
            return False

    def get_cached_statistics(self, stats_key):
        """获取缓存的统计数据"""
        if not self.is_available():
            return None

        try:
            key = f"stats:{stats_key}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"获取统计缓存失败: {e}")
            return None

    def invalidate_cache(self, pattern):
        """
        批量失效缓存

        Args:
            pattern: 匹配模式，如 "visitor:*"
        """
        if not self.is_available():
            return

        try:
            cursor = self.redis_client.scan_iter(match=pattern, count=100)
            for key in cursor:
                self.redis_client.delete(key)
            logger.info(f"批量失效缓存: {pattern}")
        except Exception as e:
            logger.error(f"失效缓存失败: {e}")

    def get_cache_stats(self):
        """获取缓存统计信息"""
        if not self.is_available():
            return None

        try:
            info = self.redis_client.info('stats')
            return {
                'total_keys': info.get('keyspace', 0),
                'used_memory': info.get('used_memory_human', 'N/A'),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
            }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return None

    def clear_all_cache(self):
        """清空所有缓存（慎用）"""
        if not self.is_available():
            return

        try:
            self.redis_client.flushdb()
            logger.warning("已清空所有Redis缓存")
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")

    def warm_up_cache(self, app):
        """缓存预热 - 预加载热点数据"""
        if not self.is_available():
            logger.warning("Redis不可用，跳过缓存预热")
            return

        logger.info("开始缓存预热...")

        with app.app_context():
            from app.models.visitor_profile import VisitorProfile
            from app.models.user import User

            try:
                # 预加载最近活跃的访客
                recent_visitors = VisitorProfile.query.filter(
                    VisitorProfile.created_at >= datetime.now() - timedelta(days=7)
                ).limit(100).all()

                for visitor in recent_visitors:
                    self.cache_visitor(visitor.access_code, visitor.to_dict())

                logger.info(f"预热缓存: {len(recent_visitors)} 个访客")

                # 缓存活跃用户
                active_users = User.query.filter(
                    User.status == 'active',
                    User.created_at >= datetime.now() - timedelta(days=7)
                ).limit(100).all()

                for user in active_users:
                    self.cache_user_info(user.id, {
                        'id': user.id,
                        'real_name': user.real_name,
                        'phone': user.phone,
                        'user_type': user.user_type
                    })

                logger.info(f"预热缓存: {len(active_users)} 个用户")

            except Exception as e:
                logger.error(f"缓存预热失败: {e}")


# 全局缓存实例
_cache_manager = None

def get_cache_manager():
    """获取缓存管理器单例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cache_visitor(visitor_data, ttl=3600):
    """快捷函数：缓存访客信息"""
    cache = get_cache_manager()
    if cache:
        cache.cache_visitor(visitor_data.get('access_code'), visitor_data, ttl)


def get_cached_visitor(access_code):
    """快捷函数：获取缓存访客"""
    cache = get_cache_manager()
    if cache:
        return cache.get_cached_visitor(access_code)
    return None


if __name__ == '__main__':
    # 测试Redis连接
    cache = CacheManager()

    if cache.is_available():
        print("✅ Redis连接成功")

        stats = cache.get_cache_stats()
        print(f"缓存统计: {stats}")
    else:
        print("❌ Redis连接失败，请在生产环境配置Redis")
