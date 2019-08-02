from io import BytesIO

from PIL import Image
from django.test import TestCase

# Create your tests here.
import os
from django.core.mail import send_mail

os.environ['DJANGO_SETTINGS_MODULE'] = 'DiurenCMS.settings'

if __name__ == '__main__':
    # send_mail(
    #     '来自Django的测试邮件',
    #     '测试，测试一波~',
    #     'system@fossic.org',
    #     ['jn_xyp@163.com'],
    # )

    img = Image.open(
        'D:/My File/Projects/DiurenCMS/media/user_uploads/1/avatar/icon.png')  # type:Image.Image
    img = img.convert(mode='RGB')

    quality = 100
    limit = 100 * 1024

    while True:
        temp_io = BytesIO()
        img.save(temp_io, format='JPEG', quality=quality, optimize=True)
        print(quality, temp_io.tell())
        if temp_io.tell() > limit:
            quality -= 10
        else:
            break

    img.save('D:/My File/Projects/DiurenCMS/media/user_uploads/1/avatar/icon.jpeg', format='JPEG',
             quality=quality, optimize=True)
