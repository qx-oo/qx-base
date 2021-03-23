import json
import datetime
import pickle
import ast
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from .redis import RedisClient


class ApiJSONEncoder(DjangoJSONEncoder):

    def default(self, o):
        if isinstance(o, datetime.datetime):
            o = timezone.localtime(o)
        return super().default(o)


class ProxyCache():

    def __init__(self, key, ts, args=[], convert='json'):
        self.client = RedisClient().get_conn()
        self.key = key
        if args:
            self.key = self.key.format(*args)
        self.ts = ts
        self.convert = convert

    def get(self):
        data = self.client.get(self.key)
        if data:
            if self.convert == 'json':
                return json.loads(data)
            elif self.convert == 'pickle':
                data = ast.literal_eval(data)
                return pickle.loads(data)
            else:
                raise NotImplementedError
        return data

    def set(self, data):
        if data is None:
            return
        if self.convert == 'json':
            data = json.dumps(data, cls=ApiJSONEncoder)
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
        RedisClient().clear_by_pattern(self.key)
        return True
