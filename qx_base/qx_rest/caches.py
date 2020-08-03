import json
import urllib
import hashlib
from collections import OrderedDict
from ..qx_core.storage import RedisClient
from ..qx_core.storage.caches import DecimalEncoder


class RestCacheKey():

    @staticmethod
    def _get_cls_name(cls) -> str:
        if isinstance(cls, str):
            return cls.lower()
        return cls.__class__.__name__.lower()

    @staticmethod
    def clear_cache_keys(cls, action: str) -> bool:
        key = "viewset:{}:{}*".format(
            RestCacheKey._get_cls_name(cls), action)
        RedisClient().clear_by_pattern(key)
        return True

    @staticmethod
    def clear_cache_key(cls, action: str, obj_id: str) -> bool:
        key = "viewset:{}:{}:{}".format(
            RestCacheKey._get_cls_name(cls), action, obj_id)
        client = RedisClient().get_conn()
        client.delete(key)
        return True

    @staticmethod
    def get_chache_key(cls, action: str) -> str:
        return "viewset:{}:{}".format(
            RestCacheKey._get_cls_name(cls), action)

    @staticmethod
    def _cache_keys(cls) -> str:
        return "viewset:{}:{}".format(
            RestCacheKey._get_cls_name(cls), cls.action)


class RestCacheMeta(type):
    """
    api缓存
    ---
    cache_retrieve: bool
    is_paginate: bool,
    cache_list: bool,
    cache_fields: set(), {"a", "b"}
    rename_query_params = 'cache_query_params'

    cache_time_by_action: dict, {'list': 60}
    cache_onlyuser_by_action: dict, {"list": False}
    """

    def __new__(cls, *args, **kwargs):  # noqa
        cls = super().__new__(cls, *args, **kwargs)
        if not hasattr(cls, 'cache_onlyuser_by_action'):
            cls.cache_onlyuser_by_action = {}
        """
        Config rest retrieve mixin cache
        """
        cls.get_cache_retrieve_key = \
            RestCacheMeta.get_cache_retrieve_key
        cls.get_cache_retrieve_keys = \
            RestCacheMeta.get_cache_retrieve_keys
        if hasattr(cls, 'cache_retrieve') and cls.cache_retrieve:
            cls._default_retrieve = cls._retrieve
            cls._retrieve = RestCacheMeta._cache_retrieve
        else:
            cls.cache_retrieve = False
        """
        Config rest list mixin cache
        """
        cls.get_cache_list_key = RestCacheMeta.get_cache_list_key
        cls.get_cache_list_keys = RestCacheMeta.get_cache_list_keys
        if hasattr(cls, 'cache_list') and cls.cache_list:
            cls._default_list = cls._list
            cls._list = RestCacheMeta._cache_list
            query_keys = set()
            if cls.is_paginate:
                query_keys |= {'page', 'count'}
            if hasattr(cls, "cache_fields"):
                query_keys |= set(cls.cache_fields)
            else:
                if hasattr(cls, "filterset_class"):
                    query_keys |= set(cls.filterset_class.get_fields())
                elif hasattr(cls, "filter_fields"):
                    query_keys |= set(cls.filter_fields)
            if hasattr(cls, "ordering_fields"):
                # query_keys.add("ordering_fields")
                query_keys.add("ordering")
            cls.cache_keys = query_keys
        else:
            cls.cache_list = False
        if not hasattr(cls, 'cache_time_by_action'):
            cls.cache_time_by_action = {}
        if hasattr(cls, 'rename_query_params'):
            cls._query_params = cls.rename_query_params
        else:
            cls._query_params = "query_params"
        return cls

    def _cache_list(self, request, *args, **kwargs):
        r_client = RedisClient().get_conn()
        key = self.get_cache_list_key(request)
        data = r_client.get(key)
        if data:
            data = json.loads(data)
        else:
            data = self._default_list(request, *args, **kwargs)
            ts = 60
            if self.is_paginate:
                if data.get('count'):
                    ts = self.cache_time_by_action.get(
                        self.action, (60 * 60 * 24) * 10)
            else:
                if data:
                    ts = self.cache_time_by_action.get(
                        self.action, (60 * 60 * 24) * 10)
            r_client.set(
                key, json.dumps(data, cls=DecimalEncoder), ts)
        return data

    def _cache_retrieve(self, request, *args, **kwargs):
        r_client = RedisClient().get_conn()
        key = self.get_cache_retrieve_key(request)
        data = r_client.get(key)
        if data:
            data = json.loads(data)
        else:
            data = self._default_retrieve(request, *args, **kwargs)
            ts = self.cache_time_by_action.get(
                self.action, (60 * 60 * 24) * 10)
            r_client.set(
                key, json.dumps(data, cls=DecimalEncoder), ts)
        return data

    def get_cache_retrieve_key(self, request) -> str:
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        obj_id = self.kwargs[lookup_url_kwarg]
        onlyuser = self.cache_onlyuser_by_action.get(self.action, False)
        if onlyuser:
            key = "{}:{}:{}".format(
                RestCacheKey._cache_keys(self), request.user.id, obj_id)
        else:
            key = "{}:{}".format(
                RestCacheKey._cache_keys(self), obj_id)
        return key

    @staticmethod
    def get_cache_retrieve_keys(cls) -> str:
        return "{}:*".format(RestCacheKey._cache_keys(cls))

    def get_cache_list_key(self, request) -> str:
        onlyuser = self.cache_onlyuser_by_action.get(self.action, False)
        if self.cache_keys:
            query_data = OrderedDict(sorted(
                [
                    (key, None)
                    for key in self.cache_keys
                ]
            ))
            for key, val in getattr(request, self._query_params).items():
                if key in self.cache_keys:
                    query_data[key] = val
            query_str = urllib.parse.urlencode(query_data)
            key = hashlib.md5(query_str.encode()).hexdigest()
            if onlyuser:
                key = "{}:{}:{}".format(
                    RestCacheKey._cache_keys(self), request.user.id, key)
            else:
                key = "{}:{}".format(
                    RestCacheKey._cache_keys(self), key)
        else:
            if onlyuser:
                key = "{}:{}".format(
                    RestCacheKey._cache_keys(self), request.user.id)
            else:
                key = RestCacheKey._cache_keys(self)
        return key

    @staticmethod
    def get_cache_list_keys(cls) -> str:
        return "{}:*".format(RestCacheKey._cache_keys(cls))


class CacheSet:
    """
    使用方法: 配合装饰器
        @model_cacheset('cache_name:{}', 'user_id', 'data_id')

    需要对redis set存储一个0进行占位

    model通过by_field缓存field到redis的set类型,如点赞
    重置model的save,delete方法,对redis同步读写
    """

    def __init__(self, cache_key: str, cache_by_field: str, cache_field: str):
        self.cache_key = cache_key
        self.cache_by_field = cache_by_field
        self.cache_field = cache_field

    def cacheset(self, c_func):
        def wrap(func):
            def _func(cls, *args, **kwargs):
                by_val = getattr(cls, self.cache_by_field)
                val = getattr(cls, self.cache_field)
                ret = func(cls, *args, **kwargs)
                c_func(cls, by_val, [val])
                return ret
            return _func
        return wrap

    def add_values(self):
        def _func(cls, by_val: str, value_list: "list"):
            key = self.cache_key.format(by_val)
            client = RedisClient().get_conn()
            client.sadd(key, *value_list)
        return _func

    def add_not_exists(self):
        def _func(cls, by_val: str, value_list: "list"):
            client = RedisClient().get_conn()
            key = self.cache_key.format(by_val)
            if not client.exists(key):
                self.cache_all()(cls, by_val)
            else:
                self.add_values()(cls, by_val, value_list)
        return _func

    def get_all_by_db(self):
        def _func(cls, by_val: str) -> list:
            queryset = cls.__class__.objects.filter(
                **{self.cache_by_field: by_val})
            vals = list(queryset.values_list(
                self.cache_field, flat=True))
            return vals
        return _func

    def exists(self) -> bool:
        def _func(cls, by_val: str, val: str):
            key = self.cache_key.format(by_val)
            client = RedisClient().get_conn()
            status = client.sismember(key, val)
            # if not status:
            #     if not client.exists(key):
            #         self.cache_all()(cls, by_val)
            return status
        return _func

    def cache_all(self):
        def _func(cls, by_val: str):
            ids = self.get_all_by_db()(cls, by_val)
            ids.append(0)
            self.add_values()(cls, by_val, ids)
        return _func

    def get_all(self):
        def _func(cls, by_val: str) -> list:
            key = self.cache_key.format(by_val)
            client = RedisClient().get_conn()
            ids = client.smembers(key)
            if not ids:
                self.cache_all()(cls)
            return ids

    def del_values(self):
        def _func(cls, by_val: str, value_list: "list"):
            key = self.cache_key.format(by_val)
            client = RedisClient().get_conn()
            client.srem(key, *value_list)
        return _func


def model_cacheset(cache_key: str, cache_by_field: str, cache_field: str):
    """
    同步model数据到redis, 同步读写
    """
    c_set = CacheSet(cache_key, cache_by_field, cache_field)

    def _cls(cls):
        cls.cacheset_add_values = classmethod(c_set.add_values())
        cls.cacheset_del_values = classmethod(c_set.del_values())
        cls.cacheset_exists = classmethod(c_set.exists())
        cls.cacheset_cache_all = classmethod(c_set.cache_all())
        cls.cacheset_get_all = classmethod(c_set.get_all())
        cls.save = c_set.cacheset(c_set.add_not_exists())(cls.save)
        cls.delete = c_set.cacheset(c_set.del_values())(cls.delete)
        return cls
    return _cls
