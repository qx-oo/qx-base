import json
import datetime
from rest_framework import serializers
from rest_framework.utils import humanize_datetime
from django.utils import timezone


def check_json_safey(json_data: json, max_json_length=250, include_fields=None,
                     current_depth=1, max_depth=3, replace_blank=True):
    """
    Check Json Safey
    """
    if current_depth > max_depth:
        return False, json_data, '数据错误'
    elif current_depth == 1:
        json_length = len(json.dumps(json_data))
        if json_length > max_json_length:
            return False, json_data, '数据超出最大长度'

    if isinstance(json_data, dict):
        new_data = {}
        for key, val in json_data.items():
            if include_fields is not None and key not in include_fields:
                continue

            if isinstance(val, str) and replace_blank:
                new_data[key] = val.replace(' ', '')
            elif isinstance(val, dict) or isinstance(val, list):
                ret = check_json_safey(
                    val, current_depth=current_depth+1,
                    max_depth=max_depth, replace_blank=replace_blank)
                if not ret[0]:
                    return ret
                _, new_data[key], _ = ret
            else:
                new_data[key] = val
        return True, new_data, ""
    elif isinstance(json_data, list):
        new_data = []
        for val in json_data:

            if isinstance(val, str) and replace_blank:
                new_data.append(val.replace(' ', ''))
            elif isinstance(val, dict) or isinstance(val, list):
                ret = check_json_safey(
                    val, current_depth=current_depth+1,
                    max_depth=max_depth, replace_blank=replace_blank)
                if not ret[0]:
                    return ret
                _, ret, _ = ret
                new_data.append(ret)
            else:
                new_data.append(val)
        return True, new_data, ""
    return False, json_data, "参数错误"


class SafeJSONField(serializers.JSONField):
    """
    Safe JsonField
        filter_fields: only use fields
        required_fields: required fields
        max_json_length: json data dumps max length

    example
        test = SafeJSONField(
            label='Test',
            include_fields=['test1', 'test2'],
            required_fields=['test1'],
        )
    """

    def __init__(self, include_fields, *args,
                 required_fields=None, max_json_length=250, max_depth=3,
                 replace_blank=True, **kwargs):
        self.include_fields = include_fields
        self.max_json_length = max_json_length
        self.max_depth = max_depth
        self.replace_blank = replace_blank
        self.required_fields = required_fields
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        status, data, msg = check_json_safey(
            data, include_fields=self.include_fields,
            max_json_length=self.max_json_length, max_depth=self.max_depth,
            replace_blank=self.replace_blank)
        if isinstance(self.required_fields, dict):
            data_keys = list(data.keys())
            for field in self.required_fields:
                if field not in data_keys:
                    raise serializers.ValidationError(
                        "{} required.".format(field))
        if not status:
            raise serializers.ValidationError(msg)
        return data


class DateTimeField(serializers.DateTimeField):
    '''
    Serializer Input DateTime Field, input native time and auto format utc time

    input: 2020-01-01 01:00:00
    '''

    def to_internal_value(self, value):
        input_formats = "%Y-%m-%d %H:%M:%S+08:00"

        if isinstance(value, datetime.date) and \
                not isinstance(value, datetime.datetime):
            self.fail('date')

        if isinstance(value, datetime.datetime):
            return self.enforce_timezone(value)

        try:
            value = "%s+08:00" % value
            _time = timezone.datetime.strptime(value, input_formats)
            return _time
        except (ValueError, TypeError):
            pass

        humanized_format = humanize_datetime.datetime_formats(input_formats)
        self.fail('invalid', format=humanized_format)
