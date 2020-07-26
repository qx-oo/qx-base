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
