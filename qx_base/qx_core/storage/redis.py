import time
import redis
import logging
from django.conf import settings
from ..tools import Singleton

logger = logging.getLogger(__name__)


class RedisClient(metaclass=Singleton):
    '''
    Get redis pool client
    '''

    def __init__(self):
        logger.debug("RedisClient Init")
        self.pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            db=0
        )

    def get_conn(self) -> "redis.Redis":
        return redis.Redis(connection_pool=self.pool)

    def clear_by_pattern(self, key_pattern: str) -> bool:
        key = "{}*".format(key_pattern)
        client = self.get_conn()
        cur = '0'
        while True:
            cur, data = client.scan(cur, key, 50000)
            for _key in data:
                client.delete(_key)
            if int(cur) == 0:
                break
        return True


class RedisExpiredHash():
    """
    使用最多三个hash实现hash中field的清理(冗余超时)
    每16分钟一次清理
    """

    def __init__(self, name, expired=5 * 60):
        """
        name: hash name
        expired: field expire time
        """
        if expired > 16 * 60:
            raise ValueError("expired too big")
        self.current = time.time()
        self.name = name
        self.expired = expired
        self.client = RedisClient().get_conn()

    def get_key_name(self, tm):
        return "qx_base:expiredhash:{}:{}".format(self.name, tm)

    def get_save_tm(self):
        """
        获取存储时间
        """
        cur_tm = int(self.current / 1000)
        next_tm = cur_tm + 1
        if (self.expired + self.current) >= next_tm * 1000:
            return next_tm, 1000 + 1
        else:
            return cur_tm, next_tm * 1000 - int(self.current) + 1

    def hset(self, key, value):
        """
        设置值
        """
        save_tm, timeout = self.get_save_tm()
        name = self.get_key_name(save_tm)
        self.client.hset(name, key, value)
        self.client.expire(name, timeout)

    def hget(self, key):
        """
        获取值
        """
        cur_tm = int(self.current / 1000)
        last_tm = cur_tm - 1
        next_tm = cur_tm + 1
        for tm in [last_tm, cur_tm, next_tm]:
            name = self.get_key_name(tm)
            if data := self.client.hget(name, key):
                return data
        return None
