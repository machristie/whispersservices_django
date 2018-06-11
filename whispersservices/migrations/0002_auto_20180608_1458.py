# Generated by Django 2.0 on 2018-06-08 19:58

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('whispersservices', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True)),
                ('modified_date', models.DateField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=128, unique=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='commenttype_creator', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='commenttype_modifier', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'whispers_commenttype',
            },
        ),
        migrations.CreateModel(
            name='ContactType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True)),
                ('modified_date', models.DateField(auto_now=True, null=True)),
                ('name', models.CharField(blank=True, default='', max_length=128)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='contacttype_creator', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='contacttype_modifier', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'whispers_contacttype',
            },
        ),
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateField(blank=True, db_index=True, default=datetime.date.today, null=True)),
                ('modified_date', models.DateField(auto_now=True, null=True)),
                ('first_name', models.CharField(max_length=128)),
                ('last_name', models.CharField(max_length=128)),
                ('active', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='staff_creator', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='staff_modifier', to=settings.AUTH_USER_MODEL)),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='staff', to='whispersservices.Role')),
            ],
            options={
                'db_table': 'whispers_staff',
            },
        ),
        migrations.RemoveField(
            model_name='contact',
            name='owner_organization',
        ),
        migrations.RemoveField(
            model_name='event',
            name='epi_staff',
        ),
        migrations.AddField(
            model_name='search',
            name='name',
            field=models.CharField(default='', max_length=128, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='organization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='contacts', to='whispersservices.Organization'),
        ),
        migrations.AddField(
            model_name='comment',
            name='comment_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='comments', to='whispersservices.CommentType'),
        ),
        migrations.AddField(
            model_name='event',
            name='staff',
            field=models.ForeignKey(null=True, on_delete='events', to='whispersservices.Staff'),
        ),
        migrations.AddField(
            model_name='eventlocationcontact',
            name='contact_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='eventlocationcontacts', to='whispersservices.ContactType'),
        ),
    ]
