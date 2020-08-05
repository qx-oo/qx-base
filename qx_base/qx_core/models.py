from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
# from django.apps import apps

# Create your models here.


def get_model_id(model):
    return ContentType.objects.get_for_model(
        model).id


def load_queryset_type_object(queryset, field, model):
    ids = []
    for ins in queryset:
        ids.append(getattr(ins, field))
    return {
        ins.id: ins
        for ins in list(model.objects.filter(id__in=ids))
    }


class AbstractBaseModel(models.Model):

    created = models.DateTimeField(
        verbose_name='创建时间', default=timezone.now, editable=False)

    class Meta:
        abstract = True


class ContentTypeRelate(models.Model):
    """
    related model
    ---
    class Message(ContentTypeRelate):
        type_map_model = {
            "user": User,
            "article": Article,
            "post": None,
        }
        class Meta:
            verbose_name = 'Message'
            verbose_name_plural = verbose_name
    """

    @property
    def type_map_model(self):
        raise NotImplementedError()

    type = models.CharField(
        verbose_name='类型', db_index=True, max_length=10)
    object_id = models.PositiveIntegerField(
        verbose_name='对象Id', db_index=True)

    @staticmethod
    def prefetch_type_object(queryset):
        pass

    class Meta:
        abstract = True
