# Generated by Django 2.2.4 on 2019-08-13 00:55

import DiurenCloud.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('DiurenCloud', '0004_auto_20190812_1424'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clouddirectory',
            name='name',
            field=models.CharField(auto_created=True, blank=True, editable=False, max_length=128, validators=[DiurenCloud.validators.validate_object_name_special_characters]),
        ),
        migrations.AlterField(
            model_name='clouddirectory',
            name='path',
            field=models.CharField(auto_created=True, blank=True, editable=False, max_length=256),
        ),
        migrations.AlterField(
            model_name='clouddirectory',
            name='virtual_path',
            field=models.CharField(auto_created=True, blank=True, editable=False, max_length=256),
        ),
        migrations.AlterField(
            model_name='cloudfile',
            name='name',
            field=models.CharField(auto_created=True, blank=True, editable=False, max_length=128, validators=[DiurenCloud.validators.validate_object_name_special_characters]),
        ),
        migrations.AlterField(
            model_name='cloudfile',
            name='path',
            field=models.CharField(auto_created=True, blank=True, editable=False, max_length=256),
        ),
        migrations.AlterField(
            model_name='cloudfile',
            name='virtual_path',
            field=models.CharField(auto_created=True, blank=True, editable=False, max_length=256),
        ),
    ]
