from string import ascii_lowercase, digits
from random import choice
import time
import random
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..qx_core.storage import RedisClient, RedisExpiredHash


class AccessTimeMixin():

    def __init__(self):
        self.client = RedisClient().get_conn()
        self.model = get_user_model()
        self.field = 'id'

    def save_access_time_to_db(self):
        for page in range(self.total_page):
            key, ts = self.format_key(page)
            self._save_data_to_db(key, self.model, 'id')

    def update_access_time(self, filter_id, page_params=0):
        raise NotImplementedError()


class UserLastAccessTime(AccessTimeMixin):
    """
    用户最近访问时间记录
    ---
        存储用户id到redis的zset为最近访问时间
        通过用户page_params进行数据分页total_page
    """
    total_page = 500

    CACHE_KEY = "qx_user:{}:{}:lastaccesstime"

    def format_key(self, page):
        key, ts = self.CACHE_KEY, 60 * 60 * 24
        return key.format(self.field, page), ts

    def update_access_time(self, filter_id, page_params=0):
        page = page_params % self.total_page
        key, ts = self.format_key(page)
        access_time = int(time.time())
        self.client.zadd(key, {filter_id: access_time})

    def _save_data_to_db(self, key, model, filter_field):
        for item in self.client.zrevrange(key, 0, -1, withscores=True):
            object_id = item[0]
            last_access_time = timezone.datetime.fromtimestamp(
                item[1], tz=timezone.utc)
            model.objects.filter(
                **{
                    filter_field: object_id}
            ).update(last_access_time=last_access_time)


class CodeMsg():
    """
    验证码生成
    """

    def __init__(self, object_id, _type='', expire_time=60 * 10):
        self.key = object_id
        self.cache = RedisExpiredHash('codemsg{}'.format(_type))

    def get_new_code(self) -> (bool, str):
        """
        return: 是否缓存, code
        """
        # TODO:
        # if code := self.cache.hget(self.key):
        code = self.cache.hget(self.key)
        if code:
            return True, code
        code = random.sample(list(range(10)), 6)
        code = ''.join([str(i) for i in code])
        self.cache.hset(self.key, code)
        return False, code

    def get_code(self):
        return self.cache.hget(self.key)

    def query_code(self):
        return self.cache.hget(self.key)

    def del_code(self):
        return self.cache.hdel(self.key)


def generate_random_account(length=16, chars=ascii_lowercase+digits, split=4,
                            delimiter='-', depth=1):
    if depth > 50:
        return None
    User = get_user_model()

    account_list = set()

    if split:
        for index in range(5):
            account = ''.join([choice(chars) for i in range(length)])
            account = delimiter.join([
                account[start:start+split]
                for start in range(0, len(account), split)
            ])
            account_list.add(account)
    else:
        raise ValueError('split error: {}'.format(split))

    exist_list = list(User.objects.filter(
        account__in=account_list).values_list('account', flat=True))
    diff_list = account_list - set(exist_list)
    if diff_list:
        return diff_list.pop()
    else:
        return generate_random_account(
            length=length, chars=chars, split=split, delimiter=delimiter,
            depth=depth + 1)
