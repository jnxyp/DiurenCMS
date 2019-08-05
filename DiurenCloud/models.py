from django.conf.global_settings import MEDIA_ROOT
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage, Storage
from django.db import models
from django.utils.translation import gettext, gettext_lazy as _

# Create your models here.
from DiurenCloud.apps import USER_UPLOAD_PATH
from DiurenCloud.validators import validate_object_name_special_characters


class CloudUserProfile(models.Model):
    user = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name='cloud_profile')

    @property
    def user_upload_root(self):
        return USER_UPLOAD_PATH + self.user.username

    @property
    def root_directory(self):
        return CloudDirectory.objects.get_or_create(owner=self, name=self.user.username,
                                                    parent=None)[0]

    @classmethod
    def get_object_by_path(cls, path: str):
        path_split = path.split('/')
        profile = cls.objects.get(path_split[0])
        profile.root_directory.get_object_by_path('/'.join(path_split[1:]))


# 云对象分为文件和文件夹两类，同目录下对象不允许重名。
class CloudObjectBase(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=128, validators=[validate_object_name_special_characters])
    owner = models.ForeignKey(verbose_name=_('所有者'), to=User, on_delete=models.CASCADE)

    date_updated = models.DateTimeField(verbose_name=_('修改时间'), auto_created=True, auto_now=True)
    # 文件夹的路径必须在结尾添加'/'
    path = models.CharField(verbose_name=_('路径'), max_length=256, auto_created=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.path = self._path
        return super().save(force_insert, force_update, using, update_fields)

    def validate_unique(self, exclude=None):
        val = super().validate_unique(exclude)
        dirs = [d.name for d in self.parent.directories]
        files = [f.name for f in self.parent.files]
        if self.name in dirs or self.name in files:
            raise ValidationError(_('对象名称重复！'), code='duplicate_object_name')
        return val

    @property
    def _path(self):
        raise NotImplementedError()

    @classmethod
    def get_object_by_path(cls, path: str):
        cls.objects.get(path=path)


class CloudDirectory(CloudObjectBase):
    class Meta:
        verbose_name = _('云文件夹')

    parent = models.ForeignKey(to='self', verbose_name=_('上级文件夹'), on_delete=models.CASCADE,
                               related_name='directories', null=True, blank=True)

    def __init__(self):
        super().__init__()
        self._meta.get_field('name').verbose_name = _('文件夹名')

    def get_object_by_path_recursive(self, path: str):
        if '/' not in path:  # 如果是一个文件名
            return self.files.get(name=path)
        else:
            path_split = path.split('/')
            if len(path_split) == 2:  # 如果是一个目录名
                return self.directories.get(name=path_split[0])
            else:  # 如果是一个路径
                dir = self.directories.get(name=path_split[0])
                return dir.get_object_by_path('/'.join(path_split[1:]))

    @property
    def _path(self):
        if self.parent:
            p = self.parent._path
        else:
            p = self.owner.cloud_profile.user_upload_root
        return p + self.name + '/'


class CloudFile(CloudObjectBase):
    class Meta:
        verbose_name = _('云文件')

    parent = models.ForeignKey(to=CloudDirectory, verbose_name=_('上级文件夹'), on_delete=models.CASCADE,
                               related_name='files')
    size = models.PositiveIntegerField(verbose_name=_('文件大小'))

    def __init__(self):
        super().__init__()
        self._meta.get_field('name').verbose_name = _('文件名')

    @property
    def _path(self):
        if self.parent:
            p = self.parent._path
        else:
            p = self.owner.cloud_profile.user_upload_root
        return p + self.name

    @property
    def exists(self):
        storage = default_storage  # type:Storage
        return storage.exists(MEDIA_ROOT + self.path)
