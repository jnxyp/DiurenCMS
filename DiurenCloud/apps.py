from django.apps import AppConfig
from django.utils.translation import gettext, gettext_lazy as _

VERBOSE_NAME = _('文件管理')

APP_UPLOAD_ROOT = 'cloud/'
USER_UPLOAD_PATH = APP_UPLOAD_ROOT + 'user/'

FILE_BUFFER_MAX_SIZE = 15 * 1024 * 1024


class DiurencloudConfig(AppConfig):
    name = 'DiurenCloud'
    verbose_name = VERBOSE_NAME


import logging

logger = logging.getLogger(DiurencloudConfig.name)
