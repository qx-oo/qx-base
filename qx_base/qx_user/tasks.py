import logging
try:
    from celery.task import Task
except ImportError:
    Task = object
from ..settings import base_settings

logger = logging.getLogger(__name__)


class UserAccessTimeTask(Task):
    """
    更新用户最近访问时间
    """

    def run(self):
        logger.info(
            'UserLastAccessTimeTask user save')
        base_settings.USERLASTACCESS_CLASS().save_access_time_to_db()
        return True
