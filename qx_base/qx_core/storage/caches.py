import json
import datetime
import pickle
import ast
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from .redis import OriginRedisClient


class ApiJSONEncoder(DjangoJSONEncoder):

    def default(self, o):
        if isinstance(o, datetime.datetime):
            o = timezone.localtime(o)
        return super().default(o)


class ProxyCache():

    def __init__(self, key, ts, args=[], convert='json'):
        """
        Cache Data
            key: cache key
            ts: cache time
            args: cache key params
            convert: json|pickle|object
        """
        self.client = OriginRedisClient().get_conn()
        self.key = key
        if args:
            self.key = self.key.format(*args)
        self.ts = ts
        self.convert = convert

    @classmethod
    def loads(cls, data, convert):
        if convert == 'json':
            return json.loads(data.decode())
        elif convert == 'object':
            return pickle.loads(data)
        elif convert == 'pickle':
            data = ast.literal_eval(data.decode())
            return pickle.loads(data)
        else:
            raise NotImplementedError

    @classmethod
    def dumps(cls, data, convert):
        if convert == 'json':
            return json.dumps(data, cls=ApiJSONEncoder)
        elif convert == 'object':
            return pickle.dumps(data)
        elif convert == 'pickle':
            return str(pickle.dumps(data))
        else:
            raise NotImplementedError

    def get_or_cache(self, callback, *args, **kwargs):
        if (data := self.get()) is not None:
            return data
        data = callback(*args, **kwargs)
        if data:
            self.set(data)
        return data

    def get(self):
        data = self.client.get(self.key)
        if data:
            return self.loads(data, self.convert)
        return data

    def set(self, data):
        if data is None:
            return
        data = self.dumps(data, self.convert)
        if self.ts:
            self.client.set(self.key, data, self.ts)
        else:
            self.client.set(self.key, data)

    def delete(self):
        self.client.delete(self.key)

    def delete_keys(self):
        self.client.clear_by_pattern(self.key)
        return True
