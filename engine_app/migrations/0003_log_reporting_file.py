# Generated by Django 3.0.7 on 2020-08-27 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('engine_app', '0002_auto_20200827_0924'),
    ]

    operations = [
        migrations.AddField(
            model_name='log_reporting',
            name='file',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
    ]
