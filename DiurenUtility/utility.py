import random
import string
from io import BytesIO

from PIL import Image
from django.core.files import File
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.translation import gettext, gettext_lazy as _

from DiurenUtility.apps import logger


def gen_random_char_string(length: int) -> str:
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def resize_image(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
    logger.debug('图片缩放：缩放图片 {image}，'
                 '目标尺寸 {width} * {height}'.format(image=image, width=max_width,
                                                  height=max_height))
    w, h = image.size
    if w > max_width or h > max_height:
        ratio = min(max_width / w, max_height / h)
        image = image.resize((int(w * ratio), int(h * ratio)), Image.ANTIALIAS)
    logger.debug('图片缩放：完成√')
    return image


def crop_image(image: Image.Image, x: int, y: int, w: int, h: int) -> Image.Image:
    logger.debug(
        '图片裁剪：裁剪图片 {image}，'
        '裁剪区域 x:{x}+{w} y:{y}+{h}'.format(image=image, x=x, y=y, w=w, h=h))
    image = image.crop((x, y, x + w, y + h))
    logger.debug('图片裁剪：完成√')
    return image


def compress_image(image: Image.Image, target_size: int, target_format: str = 'PNG',
                   target_mode: str = 'RGBA', optimize: bool = False) -> BytesIO:
    image = image.convert(mode=target_mode)
    temp_io = BytesIO()
    image.save(temp_io, target_format, optimize=optimize)
    w, h = image.size
    ratio = 1
    logger.debug(
        '图片压缩：压缩图片 {image}({size})，目标大小 {target_size}，'
        '目标格式 {target_format}'.format(image=image,
                                      size=temp_io.tell(),
                                      target_size=target_size,
                                      target_format=target_format))
    while temp_io.tell() > target_size:
        ratio -= 0.1
        if ratio <= 0:
            raise Exception(_('图片压缩失败！'))
        resized_image = image.resize(w * ratio, h * ratio)
        temp_io = BytesIO()
        resized_image.save(temp_io, target_format, optimize=optimize)
    logger.debug('图片压缩：完成√')
    return temp_io


def generate_thumbnails(image: Image, sizes: dict, target_format: str = 'PNG',
                        target_mode: str = 'RGBA', optimize: bool = False) -> dict:
    thumbs = {}
    for size, limits in sizes.items():
        logger.debug('缩略图生成：生成缩略图 {size} {limits}'.format(size=size, limits=limits))
        resized_image = resize_image(image, limits['WIDTH'], limits['HEIGHT'])
        compressed_io = compress_image(resized_image, limits['SIZE'], target_format, target_mode,
                                       optimize)
        thumbs[size] = compressed_io
    logger.debug('缩略图生成：完成√')
    return thumbs


def send_mail(context, from_email, to_email, subject_template_name=None,
              email_template_name=None, html_email_template_name=None):
    if subject_template_name is None:
        subject_template_name = 'mail_subject.txt'
    if email_template_name is None:
        email_template_name = 'mail_base.xhtml'

    subject = loader.render_to_string(subject_template_name, context)
    subject = ''.join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
    if html_email_template_name is not None:
        html_email = loader.render_to_string(html_email_template_name, context)
        email_message.attach_alternative(html_email, 'text/html')

    email_message.send()


class dotdict(dict):
    def __getattr__(self, item):
        item = self.__dict__.get(item, None)
        if item is None:
            item = self.get(item)
            if type(item) is dict:
                item = dotdict(item)
        return item

    def __setattr__(self, key, value):
        if key in self.__dict__:
            self.__dict__[key] = value
        else:
            self.__setitem__(key, value)

    def __delattr__(self, item):
        if item in self.__dict__:
            del __dict__[item]
        else:
            self.__delitem__(item)


if __name__ == '__main__':
    print(gen_random_char_string(20))
