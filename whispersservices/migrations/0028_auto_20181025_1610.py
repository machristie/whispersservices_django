# Generated by Django 2.1 on 2018-10-25 21:10

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whispersservices', '0027_auto_20181023_2141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='administrativeleveltwo',
            name='centroid_latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=8, null=True),
        ),
        migrations.AlterField(
            model_name='administrativeleveltwo',
            name='centroid_longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AlterField(
            model_name='servicerequest',
            name='created_time',
            field=models.TimeField(blank=True, default=datetime.time(16, 10, 0, 339206), null=True),
        ),
    ]
