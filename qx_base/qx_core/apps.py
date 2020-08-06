from django.apps import AppConfig
from django.apps import apps


class QxCoreConfig(AppConfig):
    name = 'qx_base.qx_core'

    def ready(self):
        for model in apps.get_models():
            if hasattr(model, 'qx_apps_ready'):
                model.qx_apps_ready(model)
