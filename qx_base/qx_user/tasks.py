import logging
from qx_base.qx_core.tasks import Task
from ..settings import base_settings

logger = logging.getLogger(__name__)


class UserAccessTimeTask(Task):
    """
    更新用户最近访问时间, 每天24点过后执行
    """

    def run(self):
        logger.info(
            'UserLastAccessTimeTask user save')
        base_settings.USERLASTACCESS_CLASS().save_access_time_to_db()
        return True
