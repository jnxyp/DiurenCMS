from ast import literal_eval

from django.db.models import ImageField, TextField
from django.forms import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

from DiurenAccount.apps import logger

DEFAULT_SIZE_LIMIT = 1 * 1024 * 1024
DEFAULT_WIDTH_LIMIT = 1000
DEFAULT_HEIGHT_LIMIT = 1000


class DictField(TextField):
    def get_internal_type(self):
        return "DictField"

    def __init__(self, default=None, *args, **kwargs):
        if not default:
            default = dict()
        super().__init__(default=default, *args, **kwargs)

    # 为啥这方法父类里面没有呢？
    def from_db_value(self, value, expression, connection):
        logger.debug('字典字段：反序列化数据(from_db_value) %s' % value)
        if value:
            data = literal_eval(value)
        else:
            data = dict()
        if not isinstance(data, dict):
            raise TypeError('字典字段格式非法：反序列化结果不是字典。')
        return data

    def to_python(self, value):
        logger.debug('字典字段：反序列化数据(to_python) %s' % value)
        if value:
            data = literal_eval(value)
        else:
            data = dict()
        if not isinstance(data, dict):
            raise TypeError('字典字段格式非法：反序列化结果不是字典。')
        return data

    def get_prep_value(self, value):
        logger.debug('字典字段：序列化数据 %s' % value)
        return str(value)


class FileSizeRestrictedImageField(ImageField):
    def __init__(self, *args, **kwargs):
        self.max_upload_size = kwargs.pop("max_upload_size", DEFAULT_SIZE_LIMIT)
        self.max_width = kwargs.pop("max_width", DEFAULT_WIDTH_LIMIT)
        self.max_height = kwargs.pop("max_height", DEFAULT_HEIGHT_LIMIT)

        self.help_text = _('头像文件大小上限为 {max_upload_size}，最大尺寸：{max_width}×{max_height}'.format(
            max_upload_size=filesizeformat(self.max_upload_size), max_width=self.max_width,
            max_height=self.max_height))
        super().__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super().clean(*args, **kwargs)
        size = data.size
        width, height = data.width, data.height

        try:
            if size > self.max_upload_size:
                raise forms.ValidationError(
                    _('超过上传大小上限 {max_upload_size}。当前文件大小为 {size}。'.format(
                        max_upload_size=filesizeformat(self.max_upload_size),
                        size=filesizeformat(size))))
            if width > self.max_width or height > self.max_height:
                raise forms.ValidationError(
                    _('图片尺寸超过上限 {max_img_size}。当前图片尺寸为 {img_size}。'.format(
                        max_img_size=(self.max_width, self.max_height), img_size=(width, height)))
                )
        except AttributeError as e:
            raise e

        return data
