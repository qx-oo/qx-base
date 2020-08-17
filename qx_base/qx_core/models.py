import json
from django.apps import apps
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .storage import RedisClient

# Create your models here.


def get_model_id(model):
    return ContentType.objects.get_for_model(
        model).id


def load_queryset_type_object(queryset, field, model, _type='',
                              select_related=[]):
    ids = []
    for ins in queryset:
        ids.append(getattr(ins, field))
    return {
        "{}_{}".format(ins.id, _type): ins
        for ins in list(
            model.objects.select_related(
                *select_related).filter(id__in=ids))
    }


def load_set_queryset_object(queryset, model, field_map: dict,
                             select_related=[]):
    """
    Load model queryset by obj_id
        queryset: model queryset
        model: django model
        field_map: get and set field_map,
                   example {'user1_id': 'user1', 'user2_id': 'user2'}
    """
    ids = [
        getattr(ins, field_id)
        for ins in queryset
        for field_id in field_map.keys()
        if getattr(ins, field_id)
    ]
    data = {
        ins.id: ins
        for ins in list(model.objects.select_related(
            *select_related).filter(id__in=ids))
    }
    for ins in queryset:
        for field_id, set_field in field_map.items():
            setattr(ins, set_field, data.get(getattr(ins, field_id)))
    return queryset


class AbstractBaseModel(models.Model):

    created = models.DateTimeField(
        verbose_name='创建时间', default=timezone.now, editable=False)

    class Meta:
        abstract = True


class ContentTypeRelated(models.Model):
    """
    related model
    ---
    class Message(ContentTypeRelated):
        type_map_model = {
            "user": "user.User",
            "article": "article.Article",
            "post": None,
        }
        class Meta:
            verbose_name = 'Message'
            verbose_name_plural = verbose_name

    query:
        queryset = Message.prefetch_type_object(queryset)
    set object:
        message.set_type_object(user)
        message.save()
    """

    type = models.CharField(
        verbose_name='类型', db_index=True, max_length=10)
    object_id = models.PositiveIntegerField(
        verbose_name='对象Id', db_index=True, null=True)

    @property
    def type_map_model(self):
        raise NotImplementedError()

    @staticmethod
    def qx_apps_ready(model):
        model.type_map_model = {
            _type: apps.get_model(model_str) if model_str else model_str
            for _type, model_str in model.type_map_model.items()
        }

    @classmethod
    def prefetch_type_object(cls, queryset):
        data = {}
        for ins in queryset:
            data.setdefault(ins.type, []).append(ins)
        objs_data = {}
        for _type, _queryset in data.items():
            model = cls.type_map_model.get(_type)
            if model:
                objs_data.update(load_queryset_type_object(
                    _queryset, 'object_id', model, _type))
        for ins in queryset:
            key = "{}_{}".format(ins.object_id, ins.type)
            obj = objs_data.get(key)
            setattr(ins, 'type_object', obj)
        return queryset

    def set_type_object(self, obj):
        _t = None
        for _type, cls in self.type_map_model.items():
            if cls == obj.__class__:
                _t = _type
        if not _t:
            raise TypeError('obj model not support')
        self.type = _t
        self.object_id = obj.id

    class Meta:
        abstract = True


class ModelCountMixin():
    """
    Django model integer field count, cache to redis and sync to db.
    ---
    model_count_timeout: default timeout times to db
    model_count_day_only: every day once

    example:

        class TestModel(models.Model, ModelCountMixin):
            star_count = models.PositiveIntegerField(
                verbose_name="点赞数", default=0)
            ...
            model_count_field_name = 'star_count'
            ...

            model_count_timeout = 1
            model_count_day_only = False

        test = TestModel.objects.create(star_count=2)
        test.load_field_count()
        test.add_field_count(10)
    """

    @property
    def model_count_field_name(self):
        raise NotImplementedError()

    model_count_timeout = 3
    model_count_day_only = False

    @classmethod
    def model_count_key(cls):
        return "qx_base:{}:{}".format(
            cls.__name__.lower(), cls.model_count_field_name.lower())

    @classmethod
    def prefetch_field_count(cls, ids: list):
        """
        load not in redis instance to redis
        """
        client = RedisClient().get_conn()
        key = cls.model_count_key()
        field = cls.model_count_field_name
        vals = client.hmget(key, ids)

        pre_ids = []
        ret = {}
        for _id, val in zip(ids, vals):
            if val is None:
                pre_ids.append(_id)
            else:
                ret[_id] = val

        save_data = {
            _id: json.dumps([val, cls.model_count_timeout, ''])
            for _id, val in cls.objects.filter(
                id__in=pre_ids).values_list('id', field)
        }
        if save_data:
            client.hmset(key, save_data)
        save_data.update(ret)
        return save_data

    @classmethod
    def sync_field_count_to_db(cls):
        """
        Sync redis data to db
        """
        client = RedisClient().get_conn()
        key = cls.model_count_key()
        field = cls.model_count_field_name

        data = client.hgetall(key)
        new_data = {}
        for id, val in data.items():
            num, timeout, unique = json.loads(val)
            cls.objects.filter(id=int(id)).update(**{field: num})
            if timeout > 0:
                new_data[id] = json.dumps([num, timeout - 1, unique])
        client.delete(key)
        if new_data:
            # TODO:
            # client.hset(key, mapping=new_data)
            client.hmset(key, new_data)

    @classmethod
    def _load_model_field_value(cls, id):
        ins = cls.objects.filter(id=id).first()
        if not ins:
            return None
        return getattr(ins, cls.model_count_field_name)

    @classmethod
    def _load_field_count(cls, id):
        """
        load field num
        """
        key = cls.model_count_key()
        client = RedisClient().get_conn()

        data = client.hget(key, id)

        if data is None:

            num = cls._load_model_field_value(id)
            if num is None:
                return None, None
            client.hset(key, id, json.dumps(
                [num, cls.model_count_timeout, '']))
            return int(num), cls.model_count_timeout, ''
        else:
            num, timeout, unique = json.loads(data)
            return int(num), timeout, unique

    @classmethod
    def load_field_count(cls, id):
        num, _, _ = cls._load_field_count(id)
        return num

    @classmethod
    def batch_load_field_count(cls, ids):
        data = cls.prefetch_field_count(ids)
        return {
            id: json.loads(item)[0]
            for id, item in data.items()
        }

    @classmethod
    def add_field_count(cls, id, num):
        """
        add field num
        """
        key = cls.model_count_key()
        client = RedisClient().get_conn()

        only = timezone.localtime(
            timezone.now()).date().strftime("%Y%m%d")

        origin_num, timeout, unique = cls._load_field_count(id)

        if origin_num is None:
            return None

        if cls.model_count_day_only and only == unique:
            return origin_num

        num = origin_num + num

        client.hset(key, id, json.dumps([num, timeout + 1, only]))
        return num
