from ast import literal_eval
from os import environ

if 'USE_ENVIRON' in environ and environ['USE_ENVIRON']:
    SECRET_KEY = environ.get('SECRET_KEY')

    EMAIL_HOST = environ.get('EMAIL_HOST')
    EMAIL_PORT = environ.get('EMAIL_PORT')
    EMAIL_HOST_USER = environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = environ.get('EMAIL_HOST_PASSWORD')

    ALIYUN_OSS_STORAGE = literal_eval(environ.get('ALIYUN_OSS_STORAGE'))
else:
    from .secrets import *
