# Generated by Django 2.1.3 on 2019-03-11 19:30

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        ('whispersservices', '0033_auto_20190227_1611'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventEventGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True)),
                ('modified_date', models.DateField(auto_now=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='eventeventgroup_creator', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'whispers_eventeventgroup',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='EventGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True)),
                ('modified_date', models.DateField(auto_now=True, null=True)),
                ('category', models.IntegerField(null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='eventgroup_creator', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='eventgroup_modifier', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'whispers_eventgroup',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='HistoricalEventEventGroup',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_date', models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True)),
                ('modified_date', models.DateField(blank=True, editable=False, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('created_by', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical event event group',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.RenameModel(
            old_name='HistoricalSuperEvent',
            new_name='HistoricalEventGroup',
        ),
        migrations.RemoveField(
            model_name='eventsuperevent',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='eventsuperevent',
            name='event',
        ),
        migrations.RemoveField(
            model_name='eventsuperevent',
            name='modified_by',
        ),
        migrations.RemoveField(
            model_name='eventsuperevent',
            name='superevent',
        ),
        migrations.RemoveField(
            model_name='historicaleventsuperevent',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='historicaleventsuperevent',
            name='event',
        ),
        migrations.RemoveField(
            model_name='historicaleventsuperevent',
            name='history_user',
        ),
        migrations.RemoveField(
            model_name='historicaleventsuperevent',
            name='modified_by',
        ),
        migrations.RemoveField(
            model_name='historicaleventsuperevent',
            name='superevent',
        ),
        migrations.RemoveField(
            model_name='superevent',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='superevent',
            name='modified_by',
        ),
        migrations.AlterModelOptions(
            name='historicaleventgroup',
            options={'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical event group'},
        ),
        migrations.RemoveField(
            model_name='event',
            name='superevents',
        ),
        migrations.DeleteModel(
            name='EventSuperEvent',
        ),
        migrations.DeleteModel(
            name='HistoricalEventSuperEvent',
        ),
        migrations.DeleteModel(
            name='SuperEvent',
        ),
        migrations.AddField(
            model_name='historicaleventeventgroup',
            name='event',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='whispersservices.Event'),
        ),
        migrations.AddField(
            model_name='historicaleventeventgroup',
            name='eventgroup',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='whispersservices.EventGroup'),
        ),
        migrations.AddField(
            model_name='historicaleventeventgroup',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicaleventeventgroup',
            name='modified_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='eventeventgroup',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='whispersservices.Event'),
        ),
        migrations.AddField(
            model_name='eventeventgroup',
            name='eventgroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='whispersservices.EventGroup'),
        ),
        migrations.AddField(
            model_name='eventeventgroup',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='eventeventgroup_modifier', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='event',
            name='eventgroups',
            field=models.ManyToManyField(related_name='events', through='whispersservices.EventEventGroup', to='whispersservices.EventGroup'),
        ),
    ]
