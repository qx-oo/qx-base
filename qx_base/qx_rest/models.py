import logging
from django.db import models
from ..qx_core.models import AbstractBaseModel
from .caches import RestCacheKey, VIEWSET_CACHE_CONFIG, ProxyCache
from .tasks import async_clear_cache_task


logger = logging.getLogger(__name__)


def _empty_func():
    pass


class RestModelMixin(models.Model):
    '''
    重置model的save和delete方法, 可以同步model的rest接口对应缓存
    !async_actions,async需要celery支持

    cache_config = {
        "default": {
            "viewset": {
                "actions": [
                    "xxx1",
                    "xxx2",
                ],
                "by_user_field": "user_id",
                "create": True,  # 创建是否清理
                "update": False, # 更新是否清理
                "delete": True,  # 删除是否清理
                "async_actions": [  # 是否异步执行
                    "xxx3",
                ],
            }
        },
        "custom": {
            "test:test:{}:{}": {
                "args": [
                    'args1',
                    '*',
                    func,  # func(instance)
                ],
                "create": True,
                "update": False,
                "delete": True,
                "async": True,
            },
        },
        "foreign": {
            "viewset": {
                "actions": [
                    "xxx3",
                ],
                "foreign_set": "test_set",
                "foreign_set_func": "xxxx",
                "retrieve_field": "id",
                "field_only": True,
                "field_name": "user_id" // or baby__user_id
                "create": True,
                "update": False,
                "delete": True,
                "async_actions": [
                    "xxx3",
                ],
            }
        },
        "reload_data": bool, # 是否载入原数据
    }
    '''

    cache_config = None

    def _get_skip_status(self, val, method):
        skip = False
        if method == 'create':
            if not val.get('create', True):
                skip = True
        elif method == 'update':
            if not val.get('update', True):
                skip = True
        elif method == 'delete':
            if not val.get('delete', True):
                skip = True
        return skip

    def _get_relate_field(self, ins, only_field_lst: list, index=0):
        """
        get relate field, example: foreign_key1__foreign_key2__user_id
        """
        if index < len(only_field_lst) - 1:
            n_ins = getattr(ins, only_field_lst[index])
            index += 1
            return self._get_relate_field(n_ins, only_field_lst, index)
        else:
            return getattr(ins, only_field_lst[index])

    def _foreign_clear_cache(self, ins, cls, val: dict, method='create'):
        """
        一对多缓存删除
        """
        if self._get_skip_status(val, method):
            return _empty_func
        keys = []
        keys_async = []
        objs = getattr(ins, val['foreign_set']).all()
        for action in val['actions']:
            cfg = VIEWSET_CACHE_CONFIG.get(cls.lower(), {}).get(action)
            for obj in objs:
                detail_id = None
                user_id = None
                if cfg['detail']:
                    only_field_lst = cfg['detail_field'].split("__")
                    detail_id = str(
                        self._get_relate_field(obj, only_field_lst))
                if cfg['by_user']:
                    only_field_lst = val['by_user_field'].split("__")
                    user_id = str(
                        self._get_relate_field(obj, only_field_lst))

                key = RestCacheKey.get_rest_cache_key(
                    cls, action,
                    detail_id=detail_id, user_id=user_id, code='', cfg=cfg,
                )
                is_pattern = True if cfg['query_params'] else False
                if action in val.get('async_actions', []):
                    keys_async.append((key, is_pattern))
                else:
                    keys.append((key, is_pattern))

        return keys, keys_async

    def _custom_clear_cache(self, ins, key, val: dict, method='create'):
        """
        定制缓存删除
        """
        if self._get_skip_status(val, method):
            return _empty_func
        _args = []
        keys = []
        keys_async = []
        for arg in val.get('args'):
            if arg == '*':
                _args.append('*')
            else:
                if callable(arg):
                    f_val = arg(ins)
                else:
                    arg_field_lst = arg.split("__")
                    f_val = str(self._get_relate_field(ins, arg_field_lst))
                _args.append(f_val)

        key = key.format(*_args)
        is_pattern = True if '*' in key else False
        if val.get('async'):
            keys_async.append((key, is_pattern))
        else:
            keys.append((key.format(*_args), is_pattern))

        return keys, keys_async

    def _default_clear_cache(self, ins, cls, val: dict, method='create'):
        """
        默认缓存删除
        """
        if self._get_skip_status(val, method):
            return _empty_func
        keys = []
        keys_async = []
        for action in val['actions']:
            cfg = VIEWSET_CACHE_CONFIG.get(cls.lower(), {}).get(action)
            detail_id = None
            user_id = None
            if cfg['detail']:
                only_field_lst = cfg['detail_field'].split("__")
                detail_id = str(self._get_relate_field(ins, only_field_lst))
            if cfg['by_user']:
                only_field_lst = val['by_user_field'].split("__")
                user_id = str(self._get_relate_field(ins, only_field_lst))

            key = RestCacheKey.get_rest_cache_key(
                cls, action,
                detail_id=detail_id, user_id=user_id, code='', cfg=cfg,
            )
            is_pattern = True if cfg['query_params'] else False
            if action in val.get('async_actions', []):
                keys_async.append((key, is_pattern))
            else:
                keys.append((key, is_pattern))

        return keys, keys_async

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        method = 'create' if self.pk is None else 'update'
        objs = [self]
        if self.cache_config:
            if self.cache_config.get('reload_data', False) and self.id:
                origin = self.__class__.objects.get(id=self.id)
                objs.append(origin)

        super().save(force_insert, force_update, using,
                     update_fields)

        if self.cache_config:
            keys_async = []
            for ins in objs:
                for cls, val in self.cache_config.get(
                        'default', {}).items():
                    _keys, _keys_async = self._default_clear_cache(
                        ins, cls, val, method)
                    RestCacheKey.clear_action_cache(_keys)
                    keys_async.extend(_keys_async)
                for cls, val in self.cache_config.get(
                        'foreign', {}).items():
                    _keys, _keys_async = self._foreign_clear_cache(
                        ins, cls, val, method)
                    RestCacheKey.clear_action_cache(_keys)
                    keys_async.extend(_keys_async)
                for cls, val in self.cache_config.get(
                        'custom', {}).items():
                    _keys, _keys_async = self._custom_clear_cache(
                        ins, cls, val, method)
                    RestCacheKey.clear_action_cache(_keys)
                    keys_async.extend(_keys_async)
            if keys_async:
                async_clear_cache_task.apply_async(args=[keys_async])

    def delete(self, using=None, keep_parents=False):
        keys = []
        keys_async = []
        if self.cache_config:
            ins = self
            for cls, val in self.cache_config.get('default', {}).items():
                _keys, _keys_async = self._default_clear_cache(
                    ins, cls, val, 'delete')
                keys.extend(_keys)
                keys_async.extend(_keys_async)
            for cls, val in self.cache_config.get('foreign', {}).items():
                _keys, _keys_async = self._foreign_clear_cache(
                    ins, cls, val, 'delete')
                RestCacheKey.clear_action_cache(_keys)
                keys_async.extend(_keys_async)
            for cls, val in self.cache_config.get('custom', {}).items():
                _keys, _keys_async = self._custom_clear_cache(
                    ins, cls, val, 'delete')
                keys.extend(_keys)
                keys_async.extend(_keys_async)
        ret = super().delete(using, keep_parents)
        if keys:
            RestCacheKey.clear_action_cache(keys)
        if keys_async:
            async_clear_cache_task.apply_async(args=[keys_async])
        return ret

    class Meta:
        abstract = True


class CacheModelMixin(models.Model):
    """
    Model缓存处理, 如果:
        class User(CacheModelMixin):
            ....
            objects_cache_fields = {
                'object': ['id',],
                'query': ['user_id',],
            }
            ....

        user.cache_get(id=15)
        user.cache_query(id=15) # queryset max length 100
    """

    objects_cache_fields = {
        'object': ['id', ],
        'query': [],
    }

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save(force_insert, force_update, using,
                     update_fields)
        try:
            if self.objects_cache_fields.get('object'):
                kwargs = self.__cache_kwargs__()
                ProxyCache(
                    *self.__cache_key__(**kwargs), convert='object'
                ).set(self)
            if self.objects_cache_fields.get('query'):
                q_kwargs = self.__cache_query_kwargs__()
                ProxyCache(
                    *self.__cache_query_key__(**q_kwargs), convert='object'
                ).delete()
        except Exception:
            logger.exception('set cache error')

    def delete(self, using=None, keep_parents=False):
        try:
            kwargs = self.__cache_kwargs__()
            q_kwargs = self.__cache_query_kwargs__()
        except Exception:
            logger.exception('set cache error')
        ret = super().delete(using, keep_parents)
        try:
            if self.objects_cache_fields.get('object'):
                ProxyCache(
                    *self.__cache_key__(**kwargs), convert='object'
                ).delete()
            if self.objects_cache_fields.get('query'):
                ProxyCache(
                    *self.__cache_query_key__(**q_kwargs), convert='object'
                ).delete()
        except Exception:
            logger.exception('set cache error')
        return ret

    @classmethod
    def cache_get(cls, _validate=True, **kwargs):
        n_kwargs = {
            key: val
            for key, val in kwargs.items()
            if key not in cls.objects_cache_fields.get('object')
        }
        ins = ProxyCache(
            *cls.__cache_key__(**kwargs), convert='object'
        ).get_or_cache(cls.objects.get, **kwargs)
        if _validate:
            for key, val in n_kwargs.items():
                if getattr(ins, key) != val:
                    raise cls.DoesNotExist
        return ins

    @classmethod
    def cache_query(cls, **kwargs):
        """
        queryset cache
        """
        n_kwargs = {
            key: val
            for key, val in kwargs.items()
            if key not in cls.objects_cache_fields.get('query')
        }
        proxy = ProxyCache(
            *cls.__cache_query_key__(**kwargs), convert='object'
        )
        if (queryset := proxy.get()) is None:
            queryset = cls.objects.filter(**kwargs)[:100]
            if queryset:
                proxy.set(queryset)

        if n_kwargs:
            filter_queryset = []
            for ins in queryset:
                flag = True
                for key, val in kwargs.items():
                    if getattr(ins, key) != val:
                        flag = False
                        break
                if flag:
                    filter_queryset.append(ins)
            return filter_queryset
        else:
            return list(queryset)

    @classmethod
    def __cache_key__(cls, **kwargs):
        key = 'qx_base:model:object:{}:'.format(
            cls.__name__).lower()
        args = []
        for field in sorted(cls.objects_cache_fields.get('object')):
            if val := kwargs.get(field):
                val = str(val)
                if len(val) > 10:
                    raise ValueError('%s: %s length too long.' % (field, val))
                args.append("{}_{}".format(field, val))
            else:
                raise KeyError('{} get params error {}'.format(
                    cls.__name__, kwargs))
        key = key + ':'.join(args)
        if len(key) > 100:
            raise ValueError('key: %s length too long.' % key)
        return key, 60 * 60 * 24 * 30

    @classmethod
    def __cache_query_key__(cls, **kwargs):
        key = 'qx_base:q_model:object:{}:'.format(
            cls.__name__).lower()
        args = []
        for field in sorted(cls.objects_cache_fields.get('query')):
            if val := kwargs.get(field):
                val = str(val)
                if len(val) > 10:
                    raise ValueError('%s: %s length too long.' % (field, val))
                args.append("{}_{}".format(field, val))
            else:
                raise KeyError('{} get params error {}'.format(
                    cls.__name__, kwargs))
        key = key + ':'.join(args)
        if len(key) > 100:
            raise ValueError('key: %s length too long.' % key)
        return key, 60 * 60 * 24 * 7

    def __cache_kwargs__(self):
        kwargs = {
            field: getattr(self, field)
            for field in self.objects_cache_fields.get('object')
        }
        return kwargs

    def __cache_query_kwargs__(self):
        kwargs = {
            field: getattr(self, field)
            for field in self.objects_cache_fields.get('query')
        }
        return kwargs

    class Meta:
        abstract = True


class RestModel(AbstractBaseModel, RestModelMixin):

    class Meta:
        abstract = True
