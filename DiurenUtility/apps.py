from django.apps import AppConfig

import logging

CONTENT_DISPOSITION_INLINE_FILE_EXTS = ('jpeg', 'jpg', 'png', 'bmp', 'gif', 'webp', 'svg', 'ico')

class DiurenutilityConfig(AppConfig):
    name = 'DiurenUtility'

logger = logging.getLogger(DiurenutilityConfig.name)