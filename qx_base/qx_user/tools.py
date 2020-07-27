import time
from django.apps import apps
from django.utils import timezone
from ..qx_core.storage import RedisClient


class AccessTimeMixin():

    def __init__(self):
        self.client = RedisClient().get_conn()
        self.model = apps.get_model('qx_user.User')
        self.field = 'user'

    def save_access_time_to_db(self):
        for page in range(self.total_page):
            key, ts = self.format_key(page)
            self._save_data_to_db(key, self.model, 'platform_id')

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

    CACHE_KEY = "user:{}:{}:lastaccesstime"

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
            last_updated = timezone.datetime.fromtimestamp(
                item[1], tz=timezone.utc)
            model.objects.filter(
                **{
                    filter_field: object_id}
            ).update(last_updated=last_updated)
