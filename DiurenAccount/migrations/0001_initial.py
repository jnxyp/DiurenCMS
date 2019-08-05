# Generated by Django 2.2.3 on 2019-08-02 06:13

import DiurenAccount.fields
import DiurenAccount.models
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
                ('avatar', DiurenAccount.fields.FileSizeRestrictedImageField(blank=True, max_length=256, null=True, upload_to=DiurenAccount.models.get_avatar_upload_filename, verbose_name='头像')),
                ('email_activated', models.BooleanField(default=False, verbose_name='邮箱已激活')),
                ('last_validation_mail_sent', models.IntegerField(default=0)),
                ('email_validation_tokens', DiurenAccount.fields.DictField(default='{}')),
                ('used_emails', DiurenAccount.fields.DictField(default='{}')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
