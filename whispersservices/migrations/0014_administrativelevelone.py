# Generated by Django 2.0 on 2018-05-24 22:59

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('whispersservices', '0013_merge_20180524_0941'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdministrativeLevelOne',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True)),
                ('modified_date', models.DateField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('abbreviation', models.CharField(blank=True, default='', max_length=128)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='administrativelevelone', to='whispersservices.Country')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='administrativelevelone_creator', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='administrativelevelone_modifier', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'whispers_administrativelevelone',
            },
        ),
    ]
