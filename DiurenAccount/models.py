import json
import os
import time
from ast import literal_eval
from datetime import datetime
from io import BytesIO

from PIL import Image
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files import File
from django.db.models.signals import post_save
from django.dispatch import receiver

from DiurenAccount.apps import DiurenaccountConfig, AVATAR_FORMAT, AVATAR_COLOR_MODE, \
    AVATAR_SIZE_LIMIT, logger, AVATAR_WIDTH_LIMIT, AVATAR_HEIGHT_LIMIT, EMAIL_TOKEN_EXPIRE,TOKEN_LENGTH
from DiurenAccount.fields import FileSizeRestrictedImageField, DictField
from django.db import models
from django.utils.translation import gettext, gettext_lazy as _

from DiurenUtility.utility import send_mail, gen_random_char_string

DEFAULT_LANGUAGE_CODE = settings.LANGUAGE_CODE
AVAILABLE_LANGUAGES = settings.LANGUAGES


def get_avatar_upload_filename(instance, filename):
    return instance.avatar_path + filename


class UserProfile(models.Model):

    user = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name='profile')
    nick = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('昵称'))
    language = models.CharField(max_length=16, choices=AVAILABLE_LANGUAGES,
                                default=DEFAULT_LANGUAGE_CODE, verbose_name=_('偏好语言'))

    avatar = FileSizeRestrictedImageField(verbose_name=_('头像'), blank=True, null=True,
                                          upload_to=get_avatar_upload_filename, max_length=256,
                                          max_upload_size=AVATAR_SIZE_LIMIT)

    email_activated = models.BooleanField(verbose_name=_('邮箱已激活'), default=False)

    last_validation_mail_sent = models.IntegerField(default=0)
    email_validation_tokens = DictField(default=None)
    used_emails = DictField(default=None)

    def delete(self, using=None, keep_parents=False):
        # 删除对应的头像文件
        self.avatar.delete()
        return super().delete(using, keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # 如果头像为空，删除现有的头像文件（如果有的话）
        if not self.avatar:
            try:
                profile = self.__class__.objects.get(pk=self.id)
            except UserProfile.DoesNotExist:
                pass
            else:
                old_avatar = profile.avatar
                if old_avatar:
                    old_avatar.delete(False)
        return super().save(force_insert, force_update, using, update_fields)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _compress_avatar(self, size_limit: int, format: str, image: Image.Image) -> BytesIO:
        logger.debug('压缩图片：%s，格式： %s' % (image, format))
        MAX_ATTEMPTS = 10
        attempt = 1
        if format == 'JPEG':
            quality = 100
            while attempt < MAX_ATTEMPTS:
                if quality <= 0:
                    raise Exception(_('压缩失败。'))
                logger.debug('压缩图片：JPEG模式 第%d次尝试，质量：%d' % (attempt, quality))
                temp_io = BytesIO()
                image.save(temp_io, format='JPEG', quality=quality, optimize=False)
                logger.debug('压缩图片：结果大小：%d，目标：%d' % (temp_io.tell(), size_limit))
                if temp_io.tell() > size_limit:
                    quality -= 5
                else:
                    break
                attempt += 1
            return temp_io
        elif format == 'PNG':  # 如果格式为PNG
            size_mult = 1
            while attempt < MAX_ATTEMPTS:
                logger.debug('压缩图片：PNG模式 第%d次尝试，缩放比率：%f' % (attempt, size_mult))
                temp_io = BytesIO()
                if size_mult < 1:
                    image = image.resize(
                        (int(image.width * size_mult), int(image.height * size_mult)))
                image.save(temp_io, format='PNG', optimize=False)
                logger.debug('压缩图片：结果大小：%d，目标：%d' % (temp_io.tell(), size_limit))
                if temp_io.tell() <= size_limit:
                    break
                else:
                    size_mult = 0.8
                attempt += 1
            logger.debug('压缩图片：完成')
            return temp_io
        else:
            raise ValueError(_("不支持的图片格式 '%s'" % format))

    def crop_avatar(self, x: float, y: float, w: float, h: float, save=True):
        filename_without_ext = os.path.splitext(self.avatar.name)[0]
        # 确保头像文件已经打开
        self.avatar.open()

        image = Image.open(self.avatar)
        image = image.convert(AVATAR_COLOR_MODE)
        cropped_image = image.crop((x, y, w + x, h + y))  # type:Image.Image

        # 如果裁剪后图像尺寸超标，对整张图片进行resize
        if w > AVATAR_WIDTH_LIMIT or h > AVATAR_HEIGHT_LIMIT:
            resize_ratio = min(AVATAR_WIDTH_LIMIT / w, AVATAR_HEIGHT_LIMIT / h)
            cropped_image = cropped_image.resize((int(w * resize_ratio), int(h * resize_ratio)))

        # 删除旧头像
        self.avatar.close()
        self.avatar.delete(save)

        # 保存前压缩以保证裁剪后保存的图片大小不超过限制
        temp_io = self._compress_avatar(AVATAR_SIZE_LIMIT, AVATAR_FORMAT, cropped_image)

        self.avatar.save(
            name=filename_without_ext.split('/')[-1] + '.' + AVATAR_FORMAT.lower(),
            content=File(temp_io), save=save)

    @property
    def language_name(self):
        lang_dict = dict(AVAILABLE_LANGUAGES)
        return lang_dict[self.language]

    @property
    def html_lang_code(self):
        return self.language.split('-')[0]

    @property
    def name(self):
        return self.nick if self.nick else self.user.username

    @property
    def home_path(self):
        return 'user_uploads/' + str(self.user.id) + '/'

    @property
    def avatar_path(self):
        return self.home_path + 'avatar/'

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        else:
            return settings.STATIC_URL + 'account/avatar/default.gif'

    def email_token_valid(self, email, token) -> bool:
        if token in self.email_validation_tokens:
            token_info = self.email_validation_tokens[token]
            if token_info['email'] == email and token_info['expire'] >= int(time.time()):
                return True
        return False

    def send_mail(self, context, from_email=None, subject_template_name=None,
                  email_template_name=None, html_email_template_name=None):
        return send_mail(context, from_email=from_email, to_email=self.user.email,
                         subject_template_name=subject_template_name,
                         email_template_name=email_template_name,
                         html_email_template_name=html_email_template_name)

    def send_email_validation_mail(self, context, request):
        token = self.create_email_validation_token()
        # 生成并发送邮件
        mail_context = {
            'user': self.user,
            'protocol': 'https' if request.is_secure() else 'http',
            'domain': request.get_host(),
            'token': token
        }
        if context:
            mail_context.update(context)
        self.send_mail(context=mail_context,
                       email_template_name='email/mail_email_validate.xhtml',
                       subject_template_name='email/mail_email_validate_subject.txt')

    def create_email_validation_token(self, commit=True) -> str:
        # 生成token，指定token过期时间
        token_expire = int(time.time()) + EMAIL_TOKEN_EXPIRE
        token = gen_random_char_string(TOKEN_LENGTH)
        email = self.user.email
        # 存储该token
        self.email_validation_tokens[token] = {
            'email': email,
            'expire': token_expire
        }
        if commit:
            self.save()
        logger.debug('邮件验证Token生成：生成token %s，邮件地址 %s，过期时间 %d' % (token, email, token_expire))
        return token

    def destroy_email_validation_token(self, token_to_destroy: str, commit=True):
        if token_to_destroy in self.email_validation_tokens:
            token_info = self.email_validation_tokens.pop(token_to_destroy)
            if commit:
                self.save()
            logger.debug('邮件验证Token销毁：生成token %s，邮件地址 %s，过期时间 %d' % (
                token_to_destroy, token_info['email'], token_info['expire']))
            return True
        logger.debug('邮件验证Token销毁：token %s 不存在' % token_to_destroy)
        return False


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile.objects.create(user=instance)
        profile.save()
