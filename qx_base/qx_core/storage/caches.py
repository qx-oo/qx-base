import json
import decimal
from .redis import RedisClient


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)


class ProxyCache():

    def __init__(self, key, ts, args=[]):
        self.client = RedisClient().get_conn()
        self.key = key
        if args:
            self.key = self.key.format(*args)
        self.ts = ts

    def get(self):
        data = self.client.get(self.key)
        if data:
            return json.loads(data)
        return data

    def set(self, data):
        if data is None:
            return
        data = json.dumps(data, cls=DecimalEncoder)
        if self.ts:
            self.client.set(self.key, data, self.ts)
        else:
            self.client.set(self.key, data)

    def delete(self):
        self.client.delete(self.key)

    def delete_keys(self):
        RedisClient().clear_by_pattern(self.key)
        return True
