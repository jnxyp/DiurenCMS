from django.conf import settings
from django.utils import translation

from DiurenAccount.models import UserProfile
from DiurenUtility.apps import logger

'''
根据登录用户Accept-Language/Cookie/UserProfile中的设置切换当前会话语言。
'''


# TODO 切换到中文繁体无反应
class SessionLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    LANGUAGE_CODE_MAPPING = {
        'zh-CN': 'zh-hans',
        'zh-TW': 'zh-hant',
        'en-CA': 'en',
        'en-US': 'en',
        'en': 'en'
    }

    @classmethod
    def get_preferred_language(cls, request):
        try:
            lang_codes = request.headers['Accept-Language'].split(';')
            lang_codes = [x.split(',') for x in lang_codes]

            accept_langs = set()
            accept_langs.add(cls.LANGUAGE_CODE_MAPPING[lang_codes[0][0]])
            for lang in lang_codes[1:]:
                try:
                    accept_langs.add(cls.LANGUAGE_CODE_MAPPING[lang[1]])
                except KeyError:
                    pass
            for lang in accept_langs:
                if lang in settings.LANGUAGES:
                    return lang
        except Exception:
            pass  # 忽略处理过程中的所有错误，并返回网站默认语言
            logger.debug('语言中间件：读取Accept-Language发生错误，返回系统默认语言')
        return settings.LANGUAGE_CODE

    def __call__(self, request):
        logger.debug('语言中间件：收到请求，开始处理。')
        user = request.user
        if user.is_authenticated:
            profile = user.profile
            lang = profile.language
            logger.debug('语言中间件：成功获取到UserProfile')
            translation.activate(lang)
            response = self.get_response(request)
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
        elif settings.LANGUAGE_COOKIE_NAME in request.COOKIES:
            logger.debug('语言中间件：用户未登录，读取COOKIE')
            lang = request.COOKIES[settings.LANGUAGE_COOKIE_NAME]
            if lang in settings.LANGUAGES:
                translation.activate(lang)
            response = self.get_response(request)
        else:
            logger.debug('语言中间件：用户未登录，读取Accept-Language请求头')
            lang = self.get_preferred_language(request)
            translation.activate(lang)
            response = self.get_response(request)
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
        logger.debug('语言中间件：语言已设定为 %s' % lang)
        return response
