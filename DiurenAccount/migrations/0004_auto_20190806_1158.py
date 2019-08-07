# Generated by Django 2.2.3 on 2019-08-06 03:58

import DiurenAccount.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('DiurenAccount', '0003_auto_20190806_0944'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='email_validation_tokens',
            field=DiurenAccount.fields.DictField(blank=True, default={}, verbose_name='激活邮件验证Token'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='last_validation_mail_sent',
            field=models.IntegerField(default=0, help_text='时间戳（秒）', verbose_name='上次激活邮件发送时间'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='used_emails',
            field=DiurenAccount.fields.DictField(blank=True, default={}, verbose_name='曾用邮箱'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL, verbose_name='所属用户'),
        ),
    ]
