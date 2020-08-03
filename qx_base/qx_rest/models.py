from ..qx_core.storage import RedisClient
from ..qx_core.models import AbstractBaseModel
from .caches import RestCacheKey

# Create your models here.


class RestCacheModel(AbstractBaseModel):
    '''
    重置model的save和delete方法, 可以同步model的rest接口对应缓存

    REST_CACHE_CLASS = {
        "default": {
            "cls_name": {
                "list_action": [
                    "list",
                ],
                "retrieve_action": [
                    "retrieve",
                ],
                "retrieve_field": "id",
                "field_only": True,
                "field_name": "user__baby__name"
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
            "cls_name": {
                "list_action": [
                    "list",
                ],
                "retrieve_action": [
                    "retrieve",
                ],
                "foreign_set": "test_set",
                "foreign_set_func": "xxxx",
                "retrieve_field": "id",
                "field_only": True,
                "field_name": "user_id" // or baby__user_id
            }
        },
    }
    '''

    REST_CACHE_CLASS = None

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

    def _get_action(self, cls: "class", val: dict):
        list_action = val.get('list_action', [])
        retrieve_action = val.get('retrieve_action', [])
        if val.get("field_only"):
            only_field_lst = val['field_name'].split("__")
            _id = str(self._get_relate_field(self, only_field_lst))
            list_action = [
                item + ":" + _id
                for item in list_action
            ]
            retrieve_action = [
                item + ":" + _id
                for item in retrieve_action
            ]
        return list_action, retrieve_action

    def _foreign_clear_cache(self, cls: "class", val: dict):
        list_action, retrieve_action = self._get_action(cls, val)
        if val.get('foreign_set'):
            obj_ids = getattr(self, val['foreign_set']).all().values_list(
                val.get("retrieve_field", 'id'), flat=True)
        else:
            obj_ids = getattr(self, val['foreign_set_func'])()

        def _func():
            for item in list_action:
                RestCacheKey.clear_cache_keys(
                    cls, item)
            for item in retrieve_action:
                for _id in obj_ids:
                    RestCacheKey.clear_cache_key(
                        cls, item, _id)
        return _func

    def _custom_clear_cache(self, key, args):
        _args = []
        for arg in args:
            if arg == '*':
                _args.append('*')
            else:
                arg_field_lst = arg.split("__")
                _id = str(self._get_relate_field(self, arg_field_lst))
                _args.append(_id)

        def _func():
            item = key.format(*_args)
            RedisClient().clear_by_pattern(item)
        return _func

    def _default_clear_cache(self, cls: "class", val: dict):
        list_action, retrieve_action = self._get_action(cls, val)
        if retrieve_action:
            _id = getattr(self, val.get("retrieve_field", 'id'))
        else:
            _id = None

        def _func():
            for item in list_action:
                RestCacheKey.clear_cache_keys(
                    cls, item)
            for item in retrieve_action:
                RestCacheKey.clear_cache_key(
                    cls, item, _id)
        return _func

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save(force_insert, force_update, using,
                     update_fields)

        if self.REST_CACHE_CLASS:
            for cls, val in self.REST_CACHE_CLASS.get('default', {}).items():
                self._default_clear_cache(cls, val)()
            for cls, val in self.REST_CACHE_CLASS.get('foreign', {}).items():
                self._foreign_clear_cache(cls, val)()
            for cls, val in self.REST_CACHE_CLASS.get('custom', {}).items():
                self._custom_clear_cache(cls, val)()

    def delete(self, using=None, keep_parents=False):
        cache_func = []
        if self.REST_CACHE_CLASS:
            for cls, val in self.REST_CACHE_CLASS.get('default', {}).items():
                cache_func.append(self._default_clear_cache(cls, val))
            for cls, val in self.REST_CACHE_CLASS.get('foreign', {}).items():
                self._foreign_clear_cache(cls, val)()
            for cls, val in self.REST_CACHE_CLASS.get('custom', {}).items():
                cache_func.append(self._custom_clear_cache(cls, val))
        ret = super().delete(using, keep_parents)
        for func in cache_func:
            func()
        return ret

    class Meta:
        abstract = True
