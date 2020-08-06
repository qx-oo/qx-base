from django.apps import apps
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

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


def load_set_queryset_object(queryset, model, field_id, set_field,
                             select_related=[]):
    """
    Load model queryset by obj_id
        queryset: model queryset
        model: django model
        field_id: queryset model field
        set_field: set field
    """
    ids = [getattr(ins, field_id) for ins in queryset]
    data = {
        ins.id: ins
        for ins in list(model.objects.select_related(
            *select_related).filter(id__in=ids))
    }
    for ins in queryset:
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
            # TODO:
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
