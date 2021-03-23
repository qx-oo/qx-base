import urllib
import hashlib
from collections import OrderedDict
from ..qx_core.storage import ProxyCache, RedisClient


VIEWSET_CACHE_CONFIG = {}


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
    cache_config = {
        'action1': {
            'query_params': bool, # 是否缓存查询参数
            'cache_fields': ['user', 'name'], # 缓存参数
            # 'by_field': 'user_id', # 通过field缓存
            'timeout': 24 * 60, # 缓存时间
            'by_user': bool, # 通过登录用户缓存
            'is_paginate': bool, # 是否分页
        },
    }
    """

    def __new__(cls, *args, **kwargs):  # noqa
        cls = super().__new__(cls, *args, **kwargs)

        if hasattr(cls, 'cache_config'):
            cls.cache_config = RestCacheMeta.parse_cache_config(cls)
            VIEWSET_CACHE_CONFIG[cls.__class__.__name__.lower()
                                 ] = cls.cache_config
            cls.get_cache_key = RestCacheMeta.get_cache_key
            cls.get_data_by_redis = RestCacheMeta.get_data_by_redis
            cls.set_data_to_redis = RestCacheMeta.set_data_to_redis
            cls.get_query_params_encode = RestCacheMeta.get_query_params_encode
            """
            Config rest retrieve mixin cache
            """
            if hasattr(cls, '_retrieve'):
                cls._default_retrieve = cls._retrieve
                cls._retrieve = RestCacheMeta._cache_retrieve
            """
            Config rest list mixin cache
            """
            if hasattr(cls, '_list'):
                cls._default_list = cls._list
                cls._list = RestCacheMeta._cache_list
        return cls

    @staticmethod
    def parse_cache_config(cls):
        cache_config = {}
        if hasattr(cls, 'cache_config'):
            for action, cfg in cls.cache_config.items():
                if action == 'list':
                    detail = False
                elif action == 'retrieve':
                    detail = True
                else:
                    detail = getattr(cls, action).detail

                default = RestCacheMeta.get_default_detail_action(detail)
                default.update(cfg)
                if not detail and default['cache_fields'] is None:
                    default['cache_fields'] = RestCacheMeta.get_cache_fields(
                        cls, default['is_paginate'])
                cache_config[action] = default
        return cache_config

    @staticmethod
    def get_default_detail_action(detail):
        if detail:
            return {
                'detail': True,
                'query_params': False,
                'cache_fields': [],
                'timeout': (60 * 60 * 24) * 10,
                'by_user': False,
                'is_paginate': None,
            }
        else:
            return {
                'detail': False,
                'query_params': True,
                'cache_fields': None,
                'timeout': (60 * 60 * 24) * 10,
                'by_user': False,
                'is_paginate': True,
            }

    @staticmethod
    def get_cache_fields(cls, is_paginate):
        query_keys = set()
        if hasattr(cls, "filterset_class"):
            query_keys |= set(cls.filterset_class.get_fields())
        elif hasattr(cls, "filter_fields"):
            query_keys |= set(cls.filter_fields)
        if hasattr(cls, "ordering_fields"):
            query_keys.add("ordering")
        if is_paginate:
            query_keys |= set(['page', 'count'])
        return query_keys

    def get_query_params_encode(self, request, cfg):
        if cfg['cache_fields']:
            query_data = OrderedDict(sorted(
                [
                    (key, None)
                    for key in cfg['cache_fields']
                ]
            ))
            for key, val in getattr(request, 'query_params').items():
                if key in cfg['cache_fields']:
                    query_data[key] = val
            query_str = urllib.parse.urlencode(query_data)
            key = hashlib.md5(query_str.encode()).hexdigest()
            return key
        else:
            return None

    def _cache_list(self, request, *args, **kwargs):
        is_cache = self.action in list(self.cache_config.keys())
        if not is_cache:
            return self._default_list(request, *args, **kwargs)
        else:
            key, ts = self.get_cache_key(request)
            data = self.get_data_by_redis(key, ts)
            if not data:
                data = self._default_list(request, *args, **kwargs)
                self.set_data_to_redis(key, ts, data)
            return data

    def _cache_retrieve(self, request, *args, **kwargs):
        is_cache = self.action in list(self.cache_config.keys())
        if not is_cache:
            return self._default_retrieve(request, *args, **kwargs)
        else:
            key, ts = self.get_cache_key(request)
            data = self.get_data_by_redis(key, ts)
            if not data:
                data = self._default_retrieve(request, *args, **kwargs)
                self.set_data_to_redis(key, ts, data)
            return data

    def get_data_by_redis(self, key, ts):
        if key is not None:
            return ProxyCache(key, ts).get()
        return None

    def set_data_to_redis(self, key, ts, data):
        if key is not None:
            ProxyCache(key, ts).set(data)

    def get_cache_key(self, request) -> str:
        cfg = self.cache_config.get(self.action)
        if not cfg:
            return None, None
        by_user = cfg.get('by_user')
        code = self.get_query_params_encode(request, cfg)
        if cfg['detail']:
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

            assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". ' %
                (self.__class__.__name__, lookup_url_kwarg)
            )

            obj_id = self.kwargs[lookup_url_kwarg]
            code = self.get_query_params_encode(request, cfg)
            if by_user:
                key = "{}:{}:{}".format(
                    RestCacheKey._cache_keys(self), request.user.id, obj_id)
            else:
                key = "{}:{}".format(
                    RestCacheKey._cache_keys(self), obj_id)
        else:
            if by_user and request.user.is_authenticated:
                key = "{}:{}".format(
                    RestCacheKey._cache_keys(self), request.user.id)
            else:
                key = "{}".format(
                    RestCacheKey._cache_keys(self))
        if code:
            key = "{}:{}".format(key, code)
        return key, cfg['timeout']
