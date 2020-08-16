from django.conf import settings
from django.apps import apps
from django.utils.module_loading import import_string
from .qx_core.tools import DictInstance


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


def get_settings(attr_name, defaults):
    _b_settings = defaults

    _settings = getattr(settings, attr_name,
                        defaults)

    if _settings:
        _b_settings.update(_settings)

    ret_settings = DictInstance(**defaults)
    for key, val in _b_settings.items():
        setattr(ret_settings, key, get_attr(key, val))
    return ret_settings


QX_BASE_SETTINGS = {
    'SEND_MOBILE_MSG_CLASS': "qx_base.qx_user.mixins.SendMobileMsgMixin",
    'SEND_EMAIL_MSG_CLASS': "qx_base.qx_user.mixins.SendEmailMsgMixin",
    'USERLASTACCESS_CLASS': "qx_base.qx_user.tools.UserLastAccessTime",
    'USERINFO_MODEL': None,
    'USERINFO_SERIALIZER_CLASS': None,
}

base_settings = get_settings('QX_BASE_SETTINGS', QX_BASE_SETTINGS)
