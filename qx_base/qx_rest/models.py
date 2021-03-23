from django.db import models
from ..qx_core.storage import RedisClient
from ..qx_core.models import AbstractBaseModel
from .caches import RestCacheKey, VIEWSET_CACHE_CONFIG

# Create your models here.


class RestModelMixin(models.Model):
    '''
    重置model的save和delete方法, 可以同步model的rest接口对应缓存

    cache_config = {
        "default": {
            "viewset": {
                "actions": [
                    "xxx1",
                    "xxx2",
                ],
                "by_user_field": "user_id"
            }
        },
        "custom": {
            "test:test:{}:{}": [
                'args1',
                '*',
                'args2',
            ]
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
            }
        },
        "reload_data": bool, # 是否载入原数据
    }
    '''

    cache_config = None

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

    def _foreign_clear_cache(self, ins, cls, val: dict):
        """
        一对多缓存删除
        """
        keys = []
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
                keys.append((key, is_pattern))

        def _func():
            for key, is_pattern in keys:
                RestCacheKey.clear_cache(key, is_pattern)
        return _func

    def _custom_clear_cache(self, ins, key, args):
        """
        定制缓存删除
        """
        _args = []
        for arg in args:
            if arg == '*':
                _args.append('*')
            else:
                arg_field_lst = arg.split("__")
                _id = str(self._get_relate_field(ins, arg_field_lst))
                _args.append(_id)

        def _func():
            item = key.format(*_args)
            RedisClient().clear_by_pattern(item)
        return _func

    def _default_clear_cache(self, ins, cls, val):
        """
        默认缓存删除
        """
        keys = []
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
            keys.append((key, is_pattern))

        def _func():
            for key, is_pattern in keys:
                RestCacheKey.clear_cache(key, is_pattern)
        return _func

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        objs = [self]
        if self.cache_config:
            if self.cache_config.get('reload_data', False) and self.id:
                origin = self.__class__.objects.get(id=self.id)
                objs.append(origin)

        super().save(force_insert, force_update, using,
                     update_fields)

        if self.cache_config:
            for ins in objs:
                for cls, val in self.cache_config.get(
                        'default', {}).items():
                    self._default_clear_cache(ins, cls, val)()
                for cls, val in self.cache_config.get(
                        'foreign', {}).items():
                    self._foreign_clear_cache(ins, cls, val)()
                for cls, args in self.cache_config.get(
                        'custom', {}).items():
                    self._custom_clear_cache(ins, cls, args)()

    def delete(self, using=None, keep_parents=False):
        cache_func = []
        if self.cache_config:
            ins = self
            for cls, val in self.cache_config.get('default', {}).items():
                cache_func.append(self._default_clear_cache(ins, cls, val))
            for cls, val in self.cache_config.get('foreign', {}).items():
                self._foreign_clear_cache(ins, cls, val)()
            for cls, val in self.cache_config.get('custom', {}).items():
                cache_func.append(self._custom_clear_cache(ins, cls, val))
        ret = super().delete(using, keep_parents)
        for func in cache_func:
            func()
        return ret

    class Meta:
        abstract = True


class RestModel(AbstractBaseModel, RestModelMixin):

    class Meta:
        abstract = True
