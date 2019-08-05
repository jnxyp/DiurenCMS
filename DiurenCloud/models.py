from django.conf.global_settings import MEDIA_ROOT
from django.contrib.auth.models import User
from django.core.files.storage import default_storage, Storage
from django.db import models
from django.utils.translation import gettext, gettext_lazy as _

# Create your models here.
from DiurenCloud.apps import USER_UPLOAD_PATH


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


# todo 添加文件名校验 Validator
class CloudObjectBase(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=128)
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE)

    date_updated = models.DateTimeField(verbose_name=_('修改时间'), auto_created=True, auto_now=True)


class CloudDirectory(CloudObjectBase):
    class Meta:
        verbose_name = _('云文件夹')

    parent = models.ForeignKey(to='self', verbose_name=_('上级文件夹'), on_delete=models.CASCADE,
                               related_name='directories', null=True, blank=True)

    def __init__(self):
        super().__init__()
        self._meta.get_field('name').verbose_name = _('文件夹名')

    def get_object_by_path(self, path: str):
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
    def path(self):
        if self.parent:
            p = self.parent.path
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
    def path(self):
        if self.parent:
            p = self.parent.path
        else:
            p = self.owner.cloud_profile.user_upload_root
        return p + self.name

    @property
    def exists(self):
        storage = default_storage  # type:Storage
        return storage.exists(MEDIA_ROOT + self.path)
