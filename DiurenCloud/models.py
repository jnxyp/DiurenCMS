from django.conf.global_settings import MEDIA_ROOT
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage, Storage
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext, gettext_lazy as _

# Create your models here.
from DiurenCloud.apps import USER_UPLOAD_PATH
from DiurenCloud.validators import validate_object_name_special_characters


class CloudUser(models.Model):
    class Meta:
        verbose_name = _('云用户档案')
        verbose_name_plural = _('云用户档案')

    user = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name='cloud_user')

    @property  # (Media Root/cloud/user/)<username>/
    def object_relative_path(self):
        return str(self.user.username) + '/'

    @property
    def files(self):
        return CloudFile.objects.filter(owner=self, parent=None)

    @property
    def directories(self):
        return CloudDirectory.objects.filter(owner=self, parent=None)

    def contains(self, cloud_obj):
        if (cloud_obj.name in [o.name for o in self.directories]
                or cloud_obj.name in [o.name for o in self.files]):
            return True
        return False

    def __str__(self):
        return self.user.username


# 云对象分为文件和文件夹两类，同目录下对象不允许重名。
class CloudObjectBase(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(verbose_name=_('名称'), max_length=128,
                            validators=[validate_object_name_special_characters])
    owner = models.ForeignKey(verbose_name=_('所有者'), to=CloudUser, on_delete=models.CASCADE)

    date_updated = models.DateTimeField(verbose_name=_('修改时间'), auto_created=True, auto_now=True)
    # 文件夹的路径必须在结尾添加'/'
    path = models.CharField(verbose_name=_('路径'), max_length=256, auto_created=True, editable=False)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.path = self._path
        return super().save(force_insert, force_update, using, update_fields)

    def validate_unique(self, exclude=None):
        val = super().validate_unique(exclude)
        if hasattr(self, 'parent') and self.parent:
            if self.parent.contains(self):
                raise ValidationError(_('对象名称重复！'), code='duplicate_object_name')
        elif hasattr(self, 'owner') and self.owner:
            if self.owner.contains(self):
                raise ValidationError(_('对象名称重复！'), code='duplicate_object_name')
        return val

    @property
    def _path(self):
        raise NotImplementedError()

    @classmethod
    def get_object_by_path(cls, path: str):
        cls.objects.get(path=path)

    def __str__(self):
        return '{name} ({path})'.format(name=self.name, path=self.path)


class CloudDirectory(CloudObjectBase):
    class Meta:
        verbose_name = _('云文件夹')
        verbose_name_plural = _('云文件夹')

    parent = models.ForeignKey(to='self', verbose_name=_('上级文件夹'), on_delete=models.CASCADE,
                               related_name='directories', null=True, blank=True)

    def contains(self, cloud_obj: CloudObjectBase):
        if (cloud_obj.name in [o.name for o in self.directories.all()]
                or cloud_obj.name in [o.name for o in self.files.all()]):
            return True
        return False

    @property
    def _path(self):
        if self.parent:
            p = self.parent._path
        else:
            p = self.owner.object_relative_path
        return p + self.name + '/'


class CloudFile(CloudObjectBase):
    class Meta:
        verbose_name = _('云文件')
        verbose_name_plural = _('云文件')

    parent = models.ForeignKey(to=CloudDirectory, verbose_name=_('上级文件夹'), on_delete=models.CASCADE,
                               related_name='files', null=True, blank=True)
    size = models.PositiveIntegerField(verbose_name=_('文件大小'))

    @property
    def _path(self):
        if self.parent:
            p = self.parent._path
        else:
            p = self.owner.object_relative_path
        return p + self.name

    @property
    def exists(self):
        storage = default_storage  # type:Storage
        return storage.exists(MEDIA_ROOT + USER_UPLOAD_PATH + self.path)
