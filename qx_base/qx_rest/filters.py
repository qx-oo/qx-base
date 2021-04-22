try:
    from django_filters import Filter
except ImportError:
    Filter = object
from rest_framework import filters
from ..qx_core.tools import convert_week_daterange
from .exceptions import ApiParamsError


class OrderingFilter(filters.OrderingFilter):

    def get_schema_fields(self, view):
        if hasattr(view, 'ordering_fields'):
            self.ordering_description = "Fields for sorting: " + \
                ', '.join(view.ordering_fields)
        return super().get_schema_fields(view)


class WeekFilter(Filter):

    def filter(self, qs, value):
        if not value:
            return qs
        try:
            start, stop = convert_week_daterange(value)
        except Exception:
            raise ApiParamsError('week error')
        kwargs = {
            '{}__date__gte'.format(self.field_name): start,
            '{}__date__lte'.format(self.field_name): stop,
        }
        return qs.filter(**kwargs).distinct()


class EmptyFilter(Filter):

    def filter(self, qs, value):
        return qs
