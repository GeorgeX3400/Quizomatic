# Generated by Django 5.2 on 2025-05-05 08:34

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_alter_chat_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2025, 5, 5, 11, 34, 29, 396480)),
        ),
    ]
