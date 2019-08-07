from ast import literal_eval

from django.db.models import ImageField, TextField
from django.forms import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

from DiurenAccount.apps import logger


class DictField(TextField):
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
            raise TypeError('字典字段：格式非法，反序列化结果不是字典。')
        return data

    def to_python(self, value):
        logger.debug('字典字段：反序列化数据(to_python) %s' % value)
        if value:
            data = literal_eval(value)
        else:
            data = dict()
        if not isinstance(data, dict):
            raise TypeError('字典字段：格式非法，反序列化结果不是字典。')
        return data

    def get_prep_value(self, value):
        logger.debug('字典字段：序列化数据 %s' % value)
        return repr(value)


class FileSizeRestrictedImageField(ImageField):
    def __init__(self, *args, **kwargs):
        self.max_upload_size = kwargs.pop("max_upload_size", None)
        self.max_width = kwargs.pop("max_width", None)
        self.max_height = kwargs.pop("max_height", None)

        super().__init__(*args, **kwargs)

        self.help_text = _('头像文件大小上限为 {max_upload_size}，最大尺寸：{max_width}×{max_height}'.format(
            max_upload_size=filesizeformat(self.max_upload_size) if self.max_upload_size else _(
                '无限制'), max_width=self.max_width if self.max_width else _('无限制'),
            max_height=self.max_height if self.max_height else _('无限制')))

    def clean(self, *args, **kwargs):
        data = super().clean(*args, **kwargs)
        size = data.size
        width, height = data.width, data.height

        try:
            if self.max_upload_size and size > self.max_upload_size:
                raise forms.ValidationError(
                    _('超过上传大小上限 {max_upload_size}。当前文件大小为 {size}。'.format(
                        max_upload_size=filesizeformat(self.max_upload_size),
                        size=filesizeformat(size))))
            if (self.max_width and width > self.max_width) or (self.max_height and height > self.max_height):
                raise forms.ValidationError(
                    _('图片尺寸超过上限 {max_img_size}。当前图片尺寸为 {img_size}。'.format(
                        max_img_size=(self.max_width, self.max_height), img_size=(width, height)))
                )
        except AttributeError as e:
            raise e

        return data
