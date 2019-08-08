from ast import literal_eval

from django.db.models import ImageField, TextField

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
