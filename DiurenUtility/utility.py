import random
import string

from django.core.mail import EmailMultiAlternatives
from django.template import loader


def gen_random_char_string(length: int):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


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


if __name__ == '__main__':
    print(gen_random_char_string(20))
