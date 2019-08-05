from django.apps import AppConfig
from django.utils.translation import gettext, gettext_lazy as _

VERBOSE_NAME = _('文件管理')

USER_UPLOAD_PATH = 'users/'

class DiurencloudConfig(AppConfig):
    name = 'DiurenCloud'
    verbose_name = VERBOSE_NAME
