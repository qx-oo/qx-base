try:
    from django_filters import Filter
except ImportError:
    Filter = object
from django.utils import timezone
from ..qx_core.tools import convert_week
from .exceptions import ApiParamsError


class WeekFilter(Filter):

    def filter(self, qs, value):
        if not value:
            return qs
        try:
            start = convert_week(value)
        except Exception:
            raise ApiParamsError('week error')
        stop = start + timezone.timedelta(days=6)
        kwargs = {
            '{}__date__gte'.format(self.field_name): start,
            '{}__date__lte'.format(self.field_name): stop,
        }
        return qs.filter(**kwargs).distinct()


class EmptyFilter(Filter):

    def filter(self, qs, value):
        return qs
