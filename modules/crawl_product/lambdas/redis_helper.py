import redis
import os
from aws_lambda_powertools import Logger

from merchants import self

logger = Logger()


# 在 Lambda 初始化阶段(冷启动)创建全局变量
_redis_client = None


def initialize_redis():
    """初始化 Redis 连接，只在冷启动时执行"""
    global _redis_client

    try:
        redis_endpoint = os.environ['REDIS_ENDPOINT']
        redis_port = int(os.environ.get('REDIS_PORT', '6379'))
        redis_password = os.environ.get('REDIS_PASSWORD')

        # 创建连接池
        pool = redis.ConnectionPool(
            host=redis_endpoint,
            port=redis_port,
            password=redis_password,
            max_connections=20,  # 根据 Lambda 并发设置
            socket_connect_timeout=5,  # 连接超时5秒
            socket_timeout=5,  # 操作超时5秒
            decode_responses=True,
        )

        _redis_client = redis.Redis(connection_pool=pool)

        # 测试连接
        _redis_client.ping()
        logger.info("Redis connection initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize Redis connection: {str(e)}")
        raise


# 在模块加载时执行初始化(冷启动阶段)
try:
    initialize_redis()
except:
    # 初始化失败不影响 Lambda 加载，但第一次调用会失败
    pass



class CacheBase(object):
    EXPIRE = 60 * 60 * 24 * 7

    @property
    def key(self):
        raise NotImplementedError

    def _client(self):
        return _redis_client

    def expire(self, seconds):
        return self._client().expire(self.key, seconds)

    def get(self):
        return self._client().get(self.key)

    def set(self, value):
        return self._client().set(self.key, value, self.EXPIRE)

    def hset(self, field, value):
        return self._client().hset(self.key, field, value)

    def hgetall(self):
        return self._client().hgetall(self.key)

    def hincr(self, field, amount=1):
        return self._client().hincrby(self.key, field, amount)

    def zincr(self, field, amount=1):
        return self._client().zincrby(self.key,amount, field)

    def zmerge(self, old_key):
        return self._client().zunionstore(self.key, [old_key])

    def zscore(self, bid):
        return self._client().zscore(self.key, bid) or 0

    def exists(self):
        return self._client().exists(self.key)

    def delete(self, pattern=None):
        if pattern is None:
            return self._client().delete(self.key)

        return self._client().delete(pattern)

class ProductCache(CacheBase):
    EXPIRE = 60 * 60 * 3
    prefix = "productcrawl:v1:"

    def __init__(self, pid, key=None):
        self.pid = pid

    @property
    def key(self):
        return self.prefix+f"{self.pid}"

    def expire(self, seconds=None):
        return super().expire(self.EXPIRE)

    # @classmethod
    # def find_exists(cls, pid):
    #     pattern = cls.prefix+f"{pid}"
    #     ret = cls._client(cls).keys(pattern)
    #     if ret:
    #         return ret[0].lstrip(cls.prefix)
    #
    #     return

