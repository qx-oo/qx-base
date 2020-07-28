from django.conf import settings
from django.utils.module_loading import import_string


QX_BASE_SETTINGS = {
    'SEND_MOBILE_MSG_CLASS': "qx_base.qx_user.mixins.SendMobileMsgMixin",
    'SEND_EMAIL_MSG_CLASS': "qx_base.qx_user.mixins.SendEmailMsgMixin",
}

_b_settings = QX_BASE_SETTINGS

_settings = getattr(settings, 'QX_BASE_SETTINGS', None)

if _settings:
    _b_settings.update(_settings)


def get_attr(key, val):
    if key.endswith('_CLASS'):
        return import_string(val)
    return val


base_settings = object()
for key, val in base_settings.items():
    setattr(base_settings, key, get_attr(val))
