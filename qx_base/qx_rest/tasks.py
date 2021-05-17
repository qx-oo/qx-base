import logging
from celery import shared_task
from .caches import RestCacheKey

logger = logging.getLogger(__name__)


@shared_task
def async_clear_cache_task(keys):
    """
    异步删除缓存
    """
    if keys:
        RestCacheKey.clear_action_cache(keys)
    return True
