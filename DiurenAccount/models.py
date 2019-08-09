import time

from PIL import Image
from django.core.files import File
from django.core.files.storage import default_storage, Storage
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext, gettext_lazy as _
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.templatetags.static import static

from DiurenAccount.apps import logger, EMAIL_TOKEN_EXPIRE, \
    TOKEN_LENGTH, USER_UPLOAD_PATH, AVATAR_SIZES, AVATAR_FORMAT, AVATAR_COLOR_MODE, \
    AVATAR_ORIGINAL_SIZE_NAME
from DiurenAccount.fields import DictField
from DiurenUtility.aliyun_oss.storage import AliyunBaseStorage
from DiurenUtility.utility import send_mail, gen_random_char_string, dotdict, generate_thumbnails

DEFAULT_LANGUAGE_CODE = settings.LANGUAGE_CODE
AVAILABLE_LANGUAGES = settings.LANGUAGES


class UserProfile(models.Model):
    class Meta:
        verbose_name = _('用户资料')
        verbose_name_plural = _('用户资料')

    # 字段定义

    user = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name='profile',
                                verbose_name=_('所属用户'))
    nick = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('昵称'))
    language = models.CharField(max_length=16, choices=AVAILABLE_LANGUAGES,
                                default=DEFAULT_LANGUAGE_CODE, verbose_name=_('偏好语言'))

    email_activated = models.BooleanField(verbose_name=_('邮箱已激活'), default=False)

    last_validation_mail_sent = models.IntegerField(default=0,
                                                    verbose_name=_('上次激活邮件发送时间'),
                                                    help_text=_('时间戳（秒）'))
    # {
    #   '<token>':{
    #     'email':<email>,
    #     'expire':<expire>,
    #   }
    # }
    email_validation_tokens = DictField(
        verbose_name=_('激活邮件验证Token'), blank=True)
    # {
    #   '<used_email>':{
    #     'activated':<email_activated>
    #   }
    # }
    used_emails = DictField(verbose_name=_('曾用邮箱'), blank=True)
    # {
    #   "<size_name>:'(Media Root/)account/user/<username>/avatar/<size_name>.<ext>',
    # }
    _avatar = DictField(verbose_name=_('头像'), blank=True)

    # 特殊方法

    def __str__(self):
        return self.user.username

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        val = super().save(force_insert, force_update, using, update_fields)
        self._clear_cache()
        return val

    def _clear_cache(self):
        self.__dict__.pop('home_path', None)
        self.__dict__.pop('avatar_path', None)
        self.__dict__.pop('avatar_urls', None)

    # 属性定义

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

    @cached_property  # (Media Root/)account/user/<username>/
    def home_path(self):
        return USER_UPLOAD_PATH + str(self.user.username) + '/'

    # 头像相关方法

    @cached_property  # (Media Root/)account/user/<username>/avatar/
    def avatar_path(self):
        return self.home_path + 'avatar/'

    @cached_property
    def avatar_urls(self):
        logger.debug('头像urls：开始生成头像urls')
        avatar_urls = dotdict()
        storage = default_storage  # type:Storage
        for size in AVATAR_SIZES.keys():
            if size in self._avatar:
                if getattr(settings, 'USE_OSS', False):
                    oss_storage = storage  # type:AliyunBaseStorage
                    url = oss_storage.url(self._avatar[size], sign=False)
                else:
                    url = storage.url(self._avatar[size])
            else:
                url = static('account/default.gif')
            avatar_urls[size] = url
        logger.debug('头像urls：完成√')
        return avatar_urls

    @property
    def avatar(self):
        if self._avatar:
            name = self.avatar_path + self._avatar[AVATAR_ORIGINAL_SIZE_NAME]
            storage = default_storage  # type:Storage
            return storage.open(name)
        return None

    @avatar.setter
    def avatar(self, avatar: File):
        logger.debug('设定头像：开始设定头像')
        if self._avatar:
            logger.debug('设定头像：删除旧头像')
            del self.avatar
        storage = default_storage  # type:Storage
        logger.debug('设定头像：打开传入头像文件 {file}'.format(file=avatar))
        image = Image.open(avatar)
        logger.debug('设定头像：生成不同尺寸头像')
        thumbs = generate_thumbnails(image, sizes=AVATAR_SIZES, target_format=AVATAR_FORMAT,
                                     target_mode=AVATAR_COLOR_MODE)
        logger.debug('设定头像：生成完成，尺寸 {sizes}'.format(sizes=list(thumbs.keys())))
        for size, io in thumbs.items():
            path = storage.save(self.avatar_path + size + '.' + AVATAR_FORMAT, io)
            # 如果启用了OSS，为了提高加载速度，将头像文件权限设置为公共读
            if getattr(settings, 'USE_OSS', False):
                oss_storage = storage  # type:AliyunBaseStorage
                from oss2 import OBJECT_ACL_PUBLIC_READ
                oss_storage.put_file_acl(path, OBJECT_ACL_PUBLIC_READ)
            self._avatar[size] = path
        logger.debug('设定头像：完成√')

    @avatar.deleter
    def avatar(self):
        logger.debug('删除头像：开始删除头像')
        storage = default_storage  # type:Storage
        for name in self._avatar.values():
            storage.delete(name)
            logger.debug('删除头像：删除 {name}'.format(name=name))
        self._avatar = dict()
        logger.debug('删除头像：完成√')

    # 邮件验证相关方法

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
        # 更新最后发送验证邮件的时间
        self.last_validation_mail_sent = int(time.time())
        self.save()

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
        logger.debug('邮件验证Token生成：token %s，邮件地址 %s，过期时间 %d' % (token, email, token_expire))
        return token

    def destroy_email_validation_token(self, token_to_destroy: str, commit=True):
        if token_to_destroy in self.email_validation_tokens:
            token_info = self.email_validation_tokens.pop(token_to_destroy)
            if commit:
                self.save()
            logger.debug('邮件验证Token销毁：token %s，邮件地址 %s，过期时间 %d' % (
                token_to_destroy, token_info['email'], token_info['expire']))
            return True
        logger.debug('邮件验证Token销毁：token %s 不存在' % token_to_destroy)
        return False


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile.objects.create(user=instance)
        profile.save()
