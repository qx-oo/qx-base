from django.conf import settings
from django.apps import apps
from django.utils.module_loading import import_string
from .qx_core.tools import DictInstance


QX_BASE_SETTINGS = {
    'SEND_MOBILE_MSG_CLASS': "qx_base.qx_user.mixins.SendMobileMsgMixin",
    'SEND_EMAIL_MSG_CLASS': "qx_base.qx_user.mixins.SendEmailMsgMixin",
    'USERLASTACCESS_CLASS': "qx_base.qx_user.tools.UserLastAccessTime",
    'USERINFO_MODEL': None,
    'USERINFO_SERIALIZER_CLASS': None,
}

_b_settings = QX_BASE_SETTINGS

_settings = getattr(settings, 'QX_BASE_SETTINGS', QX_BASE_SETTINGS)

if _settings:
    _b_settings.update(_settings)


def get_attr(key, val):
    if key.endswith('_CLASS'):
        if val:
            return import_string(val)
        else:
            raise ImportError('Settings {} import error.'.format(key))
    elif key.endswith('_MODEL'):
        if val:
            return apps.get_model(val)
        else:
            raise ImportError('Settings model {} import error.'.format(key))
    return val


base_settings = DictInstance(**QX_BASE_SETTINGS)
for key, val in _b_settings.items():
    setattr(base_settings, key, get_attr(key, val))
