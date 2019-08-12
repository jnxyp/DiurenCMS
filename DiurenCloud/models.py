import hashlib

from django.conf import settings
from django.conf.global_settings import MEDIA_ROOT
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.storage import default_storage, Storage
from django.db import models
from django.db.models import QuerySet
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext, gettext_lazy as _

# Create your models here.
from DiurenCloud.apps import USER_UPLOAD_PATH, logger
from DiurenCloud.validators import validate_object_name_special_characters
from DiurenUtility.aliyun_oss.storage import AliyunMediaStorage


class CloudUser(models.Model):
    class Meta:
        verbose_name = _('云用户')
        verbose_name_plural = _('云用户')

    user = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name='cloud_user')

    @property  # (Media Root/)cloud/user/<username>/
    def object_path(self):
        return USER_UPLOAD_PATH + str(self.user.username) + '/'

    def __str__(self):
        return self.user.username


class CloudObject(models.Model):
    class Meta:
        abstract = True

    # 注意：在修改文件名称或虚拟名称后，必须保存以使路径字段刷新，
    # 或者也可以调用 obj._path obj._virtual_path 来强制计算最新路径
    name = models.CharField(max_length=128, blank=True, auto_created=True,
                            validators=(validate_object_name_special_characters,), editable=False)
    virtual_name = models.CharField(max_length=128,
                                    validators=(validate_object_name_special_characters,))

    # 注意：所有路径均使用UNIX分隔符（‘/’）
    # 在存储后端上的真实路径
    path = models.CharField(max_length=256, blank=True, editable=False, auto_created=True)
    # 面向用户的虚拟路径
    virtual_path = models.CharField(max_length=256, blank=True, editable=False, auto_created=True)

    last_modified = models.DateTimeField(auto_now=True)

    owner = models.ForeignKey(to=CloudUser, on_delete=models.CASCADE)
    parent = models.ForeignKey(to='CloudDirectory', on_delete=models.CASCADE,
                               null=True, blank=True)

    def __eq__(self, other):
        return self.virtual_path.rstrip('/') == getattr(other, 'virtual_path', None).rstrip('/')

    def __str__(self):
        return '{virtual_path} ({path})'.format(virtual_path=self.virtual_path, path=self.path)

    def clean(self):
        if not self.name:
            self.name = self.virtual_name

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if hasattr(self, 'owner'):
            # 重新计算路径，并保存到持久化字段中
            self.path = self._path
            self.virtual_path = self._virtual_path
        instance = super().save(force_insert, force_update, using, update_fields)
        return instance

    # 因为覆盖 __eq__ 方法会导致 __hash__ 无法继承，在这再定义一次。
    def __hash__(self):
        if self.pk is None:
            raise TypeError("Model instances without primary key value are unhashable")
        return hash(self.pk)

    @property
    # (Media Root/)cloud/user/<username>/<path>
    def _path(self):
        if self.parent:
            path = self.parent._path + self.name
        else:
            path = self.name
        return self.owner.object_path + path

    @property
    # 返回包括用户根虚拟路径的路径 <username>/<virtual_path>
    def _virtual_path(self):
        if self.parent:
            return self.parent._virtual_path + self.virtual_name
        else:
            return self.owner.user.username + '/' + self.virtual_name


class CloudDirectory(CloudObject):
    owner = models.ForeignKey(to=CloudUser, on_delete=models.CASCADE, related_name='directories')
    parent = models.ForeignKey(to='self', on_delete=models.CASCADE, related_name='directories',
                               null=True, blank=True)

    def validate_unique(self, exclude=None):
        if hasattr(self, 'owner'):
            directories = CloudDirectory.objects.filter(parent=self.parent,
                                                        owner=self.owner)  # type:QuerySet
            files = CloudFile.objects.filter(parent=self.parent, owner=self.owner)  # type:QuerySet
            if not self._state.adding:
                directories = directories.exclude(pk=self.pk)
            unique = True
            for d in directories:
                if self == d:
                    unique = False
            for f in files:
                if self == f:
                    unique = False
            if not unique:
                raise ValidationError(_('对象名称重复！'))

    @property
    def _path(self):
        return super()._path + '/'

    @property
    def _virtual_path(self):
        return super()._virtual_path + '/'


class CloudFile(CloudObject):
    owner = models.ForeignKey(to=CloudUser, on_delete=models.CASCADE, related_name='files')
    parent = models.ForeignKey(to=CloudDirectory, on_delete=models.CASCADE, related_name='files',
                               null=True, blank=True)

    size = models.IntegerField(default=0)
    md5 = models.CharField(max_length=32)
    uploaded = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = default_storage  # type:Storage

    def validate_unique(self, exclude=None):
        if hasattr(self, 'owner'):
            directories = CloudDirectory.objects.filter(parent=self.parent,
                                                        owner=self.owner)  # type:QuerySet
            files = CloudFile.objects.filter(parent=self.parent, owner=self.owner)  # type:QuerySet
            if not self._state.adding:
                files = files.exclude(pk=self.pk)
            unique = True
            for d in directories:
                if self == d:
                    unique = False
            for f in files:
                if self == f:
                    unique = False
            if not unique:
                raise ValidationError(_('对象名称重复！'))

    @property
    def _md5(self):
        # todo 大文件分部分hash
        hasher = hashlib.md5()
        buf = self.file.read()
        hasher.update(buf)
        return hasher.hexdigest()

    @property
    def url(self):
        if self.uploaded:
            # todo 此部分逻辑可能存在问题，需要测试
            # 如果使用阿里云存储，传递虚拟名称参数，以使用户下载的文件名与虚拟名称一致
            if settings.USE_OSS:
                oss_storage = self.storage  # type:AliyunMediaStorage
                return oss_storage.url(self.path, virtual_name=self.virtual_name)
            return self.storage.url(self.path)
        else:
            return None

    @property
    def file(self):
        logger.debug('云文件：打开文件 {file}'.format(file=self))
        return self.storage.open(self.path)

    @file.setter
    def file(self, file_obj: File):
        self.path = self.storage.save(self.path, file_obj)
        self.name = self.path.split('/')[-1]
        logger.debug('云文件：保存文件 {file}'.format(file=self))
        self.uploaded = True

    @file.deleter
    def file(self):
        logger.debug('云文件：删除文件 {file}'.format(file=self))
        self.storage.delete(self.path)
        self.uploaded = False
