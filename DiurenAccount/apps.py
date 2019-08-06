from datetime import timedelta

from django.apps import AppConfig
from django.utils.translation import gettext, gettext_lazy as _

VERBOSE_NAME = _('用户账户')

# 头像上传设置
# 注意，前端长宽比限制代码请直接更改 templates/account/avatar_input_and_edit_widget.html <script
# type="application/javascript">avatar_edit_init('avatar', {{ 最小比例 }}, {{ 最大比例 }})</script>
# 前端长宽比限制应该比此处更加严格，以避免因js计算误差导致的验证失败
AVATAR_MAX_ASPECT_RATIO = 1 / 0.618
AVATAR_MIN_ASPECT_RATIO = 0.618

AVATAR_FORMAT = 'PNG'
AVATAR_COLOR_MODE = 'RGBA'

AVATAR_SIZE_LIMIT = 1.5 * 1024 * 1024
AVATAR_WIDTH_LIMIT = 512
AVATAR_HEIGHT_LIMIT = 512

TOKEN_LENGTH = 32


# 邮件验证Token过期时间（秒）
EMAIL_TOKEN_EXPIRE = 15 * 60
# 验证邮件发送间隔（秒）
EMAIL_VALIDATION_COOLDOWN = 1 * 60

APP_UPLOAD_ROOT = 'account/'
USER_UPLOAD_PATH = APP_UPLOAD_ROOT + 'user/'

class DiurenaccountConfig(AppConfig):
    name = 'DiurenAccount'
    verbose_name = VERBOSE_NAME

import logging
logger = logging.getLogger(DiurenaccountConfig.name)

if __name__ == '__main__':
    logger.error('[ERROR]测试一波')
