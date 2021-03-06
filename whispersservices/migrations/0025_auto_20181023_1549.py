# Generated by Django 2.1 on 2018-10-23 20:49

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('whispersservices', '0024_auto_20181019_1411'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='comment_type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='comments', to='whispersservices.CommentType'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='created_time',
            field=models.TimeField(blank=True, default=datetime.time(15, 49, 5, 714952), null=True),
        ),
    ]
