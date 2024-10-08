# Generated by Django 5.1.1 on 2024-09-15 22:01

import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arena', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='auth_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='player',
            name='last_seen',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 15, 22, 1, 31, 181810, tzinfo=datetime.timezone.utc)),
        ),
    ]
