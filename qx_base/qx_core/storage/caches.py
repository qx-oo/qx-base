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
            if self.convert == 'json':
                return json.loads(data.decode())
            elif self.convert == 'object':
                return pickle.loads(data)
            elif self.convert == 'pickle':
                data = ast.literal_eval(data.decode())
                return pickle.loads(data)
            else:
                raise NotImplementedError
        return data

    def set(self, data):
        if data is None:
            return
        if self.convert == 'json':
            data = json.dumps(data, cls=ApiJSONEncoder)
        elif self.convert == 'object':
            data = pickle.dumps(data)
        elif self.convert == 'pickle':
            data = str(pickle.dumps(data))
        else:
            raise NotImplementedError
        if self.ts:
            self.client.set(self.key, data, self.ts)
        else:
            self.client.set(self.key, data)

    def delete(self):
        self.client.delete(self.key)

    def delete_keys(self):
        self.client.clear_by_pattern(self.key)
        return True
