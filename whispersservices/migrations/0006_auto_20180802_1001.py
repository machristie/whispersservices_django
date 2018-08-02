# Generated by Django 2.0 on 2018-08-02 15:01

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('whispersservices', '0005_auto_20180730_1547'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventLocationFlyway',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True)),
                ('modified_date', models.DateField(auto_now=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='eventlocationflyway_creator', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'whispers_eventlocationflyway',
            },
        ),
        migrations.CreateModel(
            name='Flyway',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True)),
                ('modified_date', models.DateField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='flyway_creator', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='flyway_modifier', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'whispers_flyway',
            },
        ),
        migrations.RemoveField(
            model_name='eventlocation',
            name='flyway',
        ),
        migrations.AddField(
            model_name='eventlocationflyway',
            name='event_location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='whispersservices.EventLocation'),
        ),
        migrations.AddField(
            model_name='eventlocationflyway',
            name='flyway',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='whispersservices.Flyway'),
        ),
        migrations.AddField(
            model_name='eventlocationflyway',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='eventlocationflyway_modifier', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='eventlocation',
            name='flyways',
            field=models.ManyToManyField(related_name='eventlocations', through='whispersservices.EventLocationFlyway', to='whispersservices.Flyway'),
        ),
    ]
