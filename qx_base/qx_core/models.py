from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
# from django.apps import apps

# Create your models here.


def get_model_id(model):
    return ContentType.objects.get_for_model(
        model).id


class AbstractBaseModel(models.Model):

    created = models.DateTimeField(
        verbose_name='创建时间', default=timezone.now, editable=False)

    class Meta:
        abstract = True
