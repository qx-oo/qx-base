import typing
import redis
import logging
import json
import decimal
from django.conf import settings
from django.utils import timezone
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
        if not key_pattern.endswith('*'):
            key = "{}*".format(key_pattern)
        else:
            key = key_pattern
        client = self.get_conn()
        cur = '0'
        while True:
            cur, data = client.scan(cur, key, 50000)
            if len(data) > 30:
                for _key in data:
                    client.delete(_key)
            else:
                if data:
                    client.delete(*data)
            if int(cur) == 0:
                break
        return True


class RedisExpiredHash():
    """
    使用最多三个hash实现hash中field的清理(冗余超时)
    每个hash到期时间1分钟
    """

    def __init__(self, name, expired=5 * 60):
        """
        name: hash name
        expired: field expire time
        """
        if expired > 60 * 60 * 1:
            raise ValueError("expired too big")
        self.retval = int(decimal.Decimal(
            expired / 60).quantize(0, rounding=decimal.ROUND_UP)) * 60

        self.time = timezone.now()
        self.current = int(self.time.timestamp())
        self.name = name
        self.expired = expired
        self.client = RedisClient().get_conn()

    def get_key_name(self, tm):
        return "qx_base:expiredhash:{}:{}".format(self.name, tm)

    def get_cur_hash_name(self):
        diff = decimal.Decimal(self.current).quantize(
            0, rounding=decimal.ROUND_UP) % self.retval
        tm = self.current - int(diff)
        return tm

    def get_save_tm(self) -> typing.Tuple[str, int]:
        """
        获取存储时间
        """
        cur_tm = self.get_cur_hash_name()
        next_tm = cur_tm + self.retval
        if (self.expired + cur_tm) >= next_tm:
            return next_tm, self.retval + 1
        else:
            return cur_tm, next_tm - self.current + 1

    def hset(self, key, value):
        """
        设置值
        """
        expire_tm = self.current + self.expired
        val = json.dumps({
            'tm': expire_tm,
            'val': value,
        })
        self.hdel(key)
        save_tm, timeout = self.get_save_tm()
        name = self.get_key_name(save_tm)
        self.client.hset(name, key, val)
        self.client.expire(name, timeout)

    def _query_name(self):
        cur_tm, _ = self.get_save_tm()
        last_tm = cur_tm - self.retval
        next_tm = cur_tm + self.retval
        for tm in [last_tm, cur_tm, next_tm]:
            name = self.get_key_name(tm)
            yield name

    def hget(self, key):
        """
        获取值
        """
        for name in self._query_name():
            if data := self.client.hget(name, key):
                val = json.loads(data)
                if val['tm'] > self.current:
                    return val['val']
        return None

    def hdel(self, key):
        for name in self._query_name():
            self.client.hdel(name, key)
