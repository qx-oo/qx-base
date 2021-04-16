import json
import hashlib
import urllib
from collections import OrderedDict
from django.utils import timezone


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def param_sort(params: dict, pop_keys=[], _json=False) -> str:
    if isinstance(params, dict):
        query_dict = dict(params)
        new_query_dict = {}
        for key, val in query_dict.items():
            if isinstance(val, dict) or isinstance(val, list):
                pass
            else:
                new_query_dict[key] = val
    else:
        if _json:
            query_dict = json.loads(params)
            if not isinstance(query_dict, dict):
                query_dict = {}
            new_query_dict = {}
            for key, val in query_dict.items():
                if isinstance(val, dict) or isinstance(val, list):
                    pass
                else:
                    new_query_dict[key] = val
        else:
            new_query_dict = dict(urllib.parse.parse_qsl(params))
    for key in pop_keys:
        new_query_dict.pop(key, None)
    ordered_query_dict = OrderedDict(
        sorted(new_query_dict.items()))
    return urllib.parse.urlencode(ordered_query_dict)


def encode_md5(data_str: str) -> str:
    return hashlib.md5(data_str).hexdigest()


def get_ios8601_time(value):
    value = value.isoformat()
    if value.endswith('+00:00'):
        value = value[:-6] + 'Z'
    return value


def enforce_timezone(value):
    field_timezone = timezone.get_current_timezone()

    if timezone.is_aware(value):
        return value.astimezone(field_timezone)
    return timezone.make_aware(value, field_timezone)


def convert_week(yearweek, day=1):
    """
    Convert week to date
        week: 201001, 2010 year first week
    """
    year = int(str(yearweek)[:4])
    week = int(str(yearweek)[4:])
    first = timezone.datetime(int(year), 1, 1).date()
    base = 1 if first.isocalendar()[1] == 1 else 8
    date = first + timezone.timedelta(
        days=base - first.isocalendar()[2] + 7 * (int(week) - 1))
    return date + timezone.timedelta(days=day - 1)


class DictInstance(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)
