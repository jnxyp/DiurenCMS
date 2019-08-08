# Generated by Django 2.2.3 on 2019-08-08 02:07

import DiurenAccount.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nick', models.CharField(blank=True, max_length=32, null=True, verbose_name='昵称')),
                ('language', models.CharField(choices=[('en', 'English'), ('zh-hans', '中文简体'), ('zh-hant', '中文繁體')], default='zh-hans', max_length=16, verbose_name='偏好语言')),
                ('email_activated', models.BooleanField(default=False, verbose_name='邮箱已激活')),
                ('last_validation_mail_sent', models.IntegerField(default=0, help_text='时间戳（秒）', verbose_name='上次激活邮件发送时间')),
                ('email_validation_tokens', DiurenAccount.fields.DictField(blank=True, default={}, verbose_name='激活邮件验证Token')),
                ('used_emails', DiurenAccount.fields.DictField(blank=True, default={}, verbose_name='曾用邮箱')),
                ('_avatar', DiurenAccount.fields.DictField(blank=True, default={}, verbose_name='头像')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL, verbose_name='所属用户')),
            ],
            options={
                'verbose_name': '用户资料',
                'verbose_name_plural': '用户资料',
            },
        ),
    ]
