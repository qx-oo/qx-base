import logging
try:
    from celery.app.task import Task
except ImportError:
    Task = object
from .caches import RestCacheKey

logger = logging.getLogger(__name__)


class AsyncClearCacheTask(Task):
    """
    异步删除缓存
    """

    def run(self, keys):
        if keys:
            RestCacheKey.clear_action_cache(keys)
        return True
