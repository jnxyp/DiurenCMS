from django.conf.global_settings import MEDIA_ROOT
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage, Storage
from django.db import models
from django.db.models import QuerySet
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext, gettext_lazy as _

# Create your models here.
from DiurenCloud.apps import USER_UPLOAD_PATH
from DiurenCloud.validators import validate_object_name_special_characters


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

    name = models.CharField(max_length=128, blank=True, auto_created=True,
                            validators=(validate_object_name_special_characters,))
    virtual_name = models.CharField(max_length=128,
                                    validators=(validate_object_name_special_characters,))

    # 注意：所有路径均使用UNIX分隔符（‘/’）
    # 在存储后端上的真实路径
    path = models.CharField(max_length=256, blank=True, auto_created=True)
    # 面向用户的虚拟路径
    virtual_path = models.CharField(max_length=256, blank=True, auto_created=True)

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
        if hasattr(self, 'owner'):
            # 重新计算路径，并保存到持久化字段中
            self.path = self._path
            self.virtual_path = self._virtual_path

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
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
            if self._state.adding:
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

    def validate_unique(self, exclude=None):
        if hasattr(self, 'owner'):
            directories = CloudDirectory.objects.filter(parent=self.parent,
                                                        owner=self.owner)  # type:QuerySet
            files = CloudFile.objects.filter(parent=self.parent, owner=self.owner)  # type:QuerySet
            if self._state.adding:
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
    def file(self):
        storage = default_storage  # type:Storage
        return storage.open(self.path)
