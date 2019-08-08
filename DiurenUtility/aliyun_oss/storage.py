# Author: xiewenya
# https://github.com/xiewenya/django-aliyun-oss2-storage/blob/master/aliyun_oss2_storage/backends.py

# Modified by jn_xyp @ 2019-07-19

# Configure OSS keys in settings.py
# Bucket ACL should be set to PRIVATE

import datetime
import os

import six
import posixpath

from urllib.parse import urljoin

from django.core.files import File
from django.utils.encoding import force_text, force_bytes
from oss2 import Auth, Service, Bucket, ObjectIterator, OBJECT_ACL_PUBLIC_READ
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.files.storage import Storage
from django.conf import settings
from oss2.api import _normalize_endpoint
from oss2.models import PartInfo

import logging

from DiurenUtility.apps import logger, CONTENT_DISPOSITION_INLINE_FILE_EXTS
from DiurenUtility.utility import gen_random_char_string


class AliyunOperationError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


# 为返回文件添加 Content-Disposition 属性，以便用户能以原名下载文件
def _make_content_headers(name):
    params = dict()
    file_name = name.split('/')[-1]
    if name.split('.')[-1].lower() in CONTENT_DISPOSITION_INLINE_FILE_EXTS:
        val = 'inline'
    else:
        val = 'attachment; filename="{name}"'.format(
            name=file_name)
    params['response-content-disposition'] = val
    return params


class AliyunBaseStorage(Storage):
    """
    Aliyun OSS2 Storage
    """

    location = ""
    base_url = ''

    def __init__(self):
        self.access_key_id = self._get_config('ACCESS_KEY_ID')
        self.access_key_secret = self._get_config('ACCESS_KEY_SECRET')
        self.end_point = _normalize_endpoint(self._get_config('END_POINT').strip())
        self.bucket_name = self._get_config('BUCKET_NAME')
        self.cname = self._get_config('ALIYUN_OSS_CNAME')

        self.auth = Auth(self.access_key_id, self.access_key_secret)
        self.service = Service(self.auth, self.end_point)

        self.bucket = self._get_bucket(self.auth)
        self.bucket = self._get_bucket(self.auth)

    def _get_bucket(self, auth):
        if self.cname:
            return Bucket(auth, self.cname, self.bucket_name, is_cname=True)
        else:
            return Bucket(auth, self.end_point, self.bucket_name)

    @staticmethod
    def _get_config(name):
        try:
            return settings.ALIYUN_OSS_STORAGE[name]
        except KeyError:
            raise ImproperlyConfigured("Can't find config for '%s' in setting.py" % name)

    @staticmethod
    def _clean_name(name):
        """
        Cleans the name so that Windows style paths work
        """
        # Normalize Windows style paths
        clean_name = posixpath.normpath(name).replace('\\', '/')

        # os.path.normpath() can strip trailing slashes so we implement
        # a workaround here.
        if name.endswith('/') and not clean_name.endswith('/'):
            # Add a trailing slash as it was stripped.
            return clean_name + '/'
        else:
            return clean_name

    def _normalize_name(self, name):
        """
        Normalizes the name so that paths like /path/to/ignored/../foo.txt
        work. We check to make sure that the path pointed to is not outside
        the directory specified by the LOCATION setting.
        """

        base_path = force_text(self.location)
        base_path = base_path.rstrip('/')

        final_path = urljoin(base_path + "/", name)

        base_path_len = len(base_path)
        if (not final_path.startswith(base_path) or
                final_path[base_path_len:base_path_len + 1] not in ('', '/')):
            raise SuspiciousOperation("Attempted access to '%s' denied." %
                                      name)
        return final_path.lstrip('/')

    def _get_target_name(self, name):
        name = self._normalize_name(self._clean_name(name))
        return name

    def _open(self, name, mode='rb'):
        name = self._get_target_name(name)
        logger.debug('OSS存储后端：打开文件 {name}，模式 {mode}'.format(name=name, mode=mode))
        file = AliyunFile(name, self, mode)
        return file

    def _save(self, name, content: File):
        # 为保证django行为的一致性，保存文件时，应该返回相对于`media path`的相对路径。

        target_name = self._get_target_name(name)

        logger.debug('OSS存储后端：保存文件 %s' % target_name)

        content.open()

        # 默认分片大小 1MB
        DEFAULT_CHUNK_SIZE = 1 * 1024 * 1024

        logger.debug('OSS存储后端：读取完成，文件大小 %d' % content.size)
        if not content.multiple_chunks(chunk_size=DEFAULT_CHUNK_SIZE):
            logger.debug('OSS存储后端：不分片，开始上传')
            # 不分片
            content_str = content.file.read()
            self.bucket.put_object(target_name, content_str)
        else:
            logger.debug('OSS存储后端：分片，开始上传')
            # 改用分片上传方式
            upload_id = self.bucket.init_multipart_upload(target_name).upload_id
            parts = []
            part_id = 1

            for chunk in content.chunks(chunk_size=DEFAULT_CHUNK_SIZE):
                # TODO Create an API endpoint for getting uploading process
                result = self.bucket.upload_part(target_name, upload_id, part_id, chunk)
                parts.append(
                    PartInfo(part_id, result.etag))
                part_id += 1
                logger.debug('OSS存储后端：上传分片 #%d' % part_id)
            result = self.bucket.complete_multipart_upload(target_name, upload_id, parts)

        logger.debug('OSS存储后端：上传完毕，关闭文件')
        content.close()
        return self._clean_name(name)

    def get_file_header(self, name):
        name = self._get_target_name(name)
        return self.bucket.head_object(name)

    def get_file_acl(self, name):
        name = self._get_target_name(name)
        return self.bucket.get_object_acl(name)

    def put_file_acl(self, name, acl):
        name = self._get_target_name(name)
        return self.bucket.put_object_acl(name, acl)

    def exists(self, name):
        name = self._get_target_name(name)
        return self.bucket.object_exists(name)

    def size(self, name):
        file_info = self.get_file_header(name)
        return file_info.content_length

    def get_modified_time(self, name):
        file_info = self.get_file_header(name)
        return self._datetime_from_timestamp(file_info.last_modified)

    def _datetime_from_timestamp(self, ts):
        """
        If timezone support is enabled, make an aware datetime object in UTC;
        otherwise make a naive one in the local timezone.
        """
        if settings.USE_TZ:
            # Safe to use .replace() because UTC doesn't have DST
            return datetime.datetime.utcfromtimestamp(ts).replace(tzinfo=datetime.timezone.utc)
        else:
            return datetime.datetime.fromtimestamp(ts)

    def listdir(self, name):
        name = self._get_target_name(name)
        logger.debug('OSS存储后端：列目录 {path}'.format(path=name))
        if name and name.endswith('/'):
            name = name[:-1]

        files = []
        dirs = set()

        for obj in ObjectIterator(self.bucket, prefix=name, delimiter='/'):
            if obj.is_prefix():
                dirs.add(obj.key)
            else:
                files.append(obj.key)

        return list(dirs), files

    def url(self, name, sign: bool = True):
        name = self._get_target_name(name)
        logger.debug('OSS存储后端：生成url {path}，签名：{sign}'.format(path=name, sign=sign))
        params = dict()
        params.update(_make_content_headers(name))
        if sign:
            return self.bucket.sign_url('GET', name, 5 * 60,
                                        params=params)  # default access link expire time: 5min
        else:
            return self.bucket._make_url(self.bucket_name, name)

    def read(self, name):
        pass

    def delete(self, name):
        name = self._get_target_name(name)
        result = self.bucket.delete_object(name)
        if result.status >= 400:
            raise AliyunOperationError(result.resp)

    def copy(self, source, target):
        source = self._get_target_name(source)
        target = self._get_target_name(target)

        result = self.bucket.copy_object(self.bucket.bucket_name, source, target)
        if result.status >= 400:
            raise AliyunOperationError(result.resp)


class AliyunMediaStorage(AliyunBaseStorage):
    base_url = settings.MEDIA_URL
    location = settings.MEDIA_ROOT

    def _save(self, name, content: File):
        name = self.get_available_name(name)
        return super()._save(name, content)

    def get_available_name(self, name, max_length=None):
        while self.exists(name):
            name, ext = os.path.splitext(name)
            name += '_' + gen_random_char_string(5) + ext
            logger.info('OSS存储后端：文件名重复，生成文件名 {name}'.format(name=name))
        return name


class AliyunStaticStorage(AliyunBaseStorage):
    base_url = settings.STATIC_URL
    location = settings.STATIC_ROOT

    def url(self, name, sign: bool = False):
        return super().url(name, sign)

    def _save(self, name, content):
        path = super()._save(name, content)
        # 设置静态文件的访问权限为公共读
        self.bucket.put_object_acl(self._get_target_name(name), OBJECT_ACL_PUBLIC_READ)
        return path


class AliyunFile(File):
    def __init__(self, name, storage, mode):
        self._storage = storage
        # self._name = name[len(self._storage.location):]
        self._name = name
        self._mode = mode
        self.file = six.BytesIO()
        self._is_dirty = False
        self._is_read = False
        super(AliyunFile, self).__init__(self.file, self._name)

    def read(self, num_bytes=None):
        if not self._is_read:
            content = self._storage.bucket.get_object(self._name)
            self.file = six.BytesIO(content.read())
            self._is_read = True

        if num_bytes is None:
            data = self.file.read()
        else:
            data = self.file.read(num_bytes)

        if 'b' in self._mode:
            return data
        else:
            return force_text(data)

    def write(self, content):
        if 'w' not in self._mode:
            raise AliyunOperationError("Operation write is not allowed.")

        self.file.write(force_bytes(content))
        self._is_dirty = True
        self._is_read = True

    def close(self):
        if self._is_dirty:
            self.file.seek(0)
            self._storage._save(self._name, self.file)
        self.file.close()
