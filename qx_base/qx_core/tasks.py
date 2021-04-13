try:
    from celery import Task as BaseTask
except ImportError:
    Task = object


class Task(BaseTask):

    @property
    def name(self):
        return self.__module__ + '.' + self.__name__

    def run(self):
        raise NotImplementedError()
