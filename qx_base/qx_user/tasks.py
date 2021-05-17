import logging
from celery import shared_task
from ..settings import base_settings

logger = logging.getLogger(__name__)


@shared_task()
def user_accesstime_task():
    """
    更新用户最近访问时间, 每天24点过后执行
    """
    logger.info(
        'UserLastAccessTimeTask user save')
    base_settings.USERLASTACCESS_CLASS().save_access_time_to_db()
    return True
