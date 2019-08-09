from ast import literal_eval
from os import environ

if 'USE_ENVIRON' in environ and environ['USE_ENVIRON']:
    SECRET_KEY = environ.get('SECRET_KEY')
else:
    from .secrets import *
