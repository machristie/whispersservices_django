# Generated by Django 2.2.16 on 2020-11-03 13:45

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations
import datetime


def create_admin_user_if_missing(apps, schema_editor):
    # Check if the admin user id is already configured
    Configuration = apps.get_model("whispersapi", "Configuration")
    db_alias = schema_editor.connection.alias
    admin_user_id = get_admin_user_id(apps, schema_editor)
    User = apps.get_model("whispersapi", "User")
    if admin_user_id is None or not User.objects.using(db_alias).filter(pk=admin_user_id).exists():
        random_password = User.objects.make_random_password()
        admin_user = User.objects.using(db_alias).create(username="admin", is_superuser=True, is_staff=True)
        admin_user.password = make_password(random_password)
        admin_user.save()
        Configuration.objects.using(db_alias).create(name="whispers_admin_user", value=admin_user.id)
        print(f"Created admin user with password '{random_password}' - use 'python manage.py changepassword admin' to change the password")


def get_admin_user_id(apps, schema_editor):
    Configuration = apps.get_model("whispersapi", "Configuration")
    db_alias = schema_editor.connection.alias
    whispers_admin_user_record = Configuration.objects.using(db_alias).filter(name='whispers_admin_user')
    if whispers_admin_user_record.exists():
        return int(whispers_admin_user_record.first().value)
    if hasattr(settings, "WHISPERS_ADMIN_USER_ID") and isinstance(settings.WHISPERS_ADMIN_USER_ID, int):
        return settings.WHISPERS_ADMIN_USER_ID
    else:
        return None


def create_roles_if_missing(apps, schema_editor):
    Role = apps.get_model("whispersapi", "Role")
    db_alias = schema_editor.connection.alias
    admin_user_id = get_admin_user_id(apps, schema_editor)
    for role_name in ["SuperAdmin",
                      "Admin",
                      "PartnerAdmin",
                      "PartnerManager",
                      "Partner",
                      "Affiliate",
                      "Public"]:
        role, created = Role.objects.using(db_alias).get_or_create(
            name=role_name, defaults=dict(
                created_date=datetime.date.today(),
                modified_date=datetime.date.today(),
                created_by_id=admin_user_id,
                modified_by_id=admin_user_id
            ))
        # Give admin the SuperAdmin role
        if created and role_name == "SuperAdmin":
            User = apps.get_model("whispersapi", "User")
            admin_user = User.objects.using(db_alias).get(pk=admin_user_id)
            admin_user.role = role
            admin_user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('whispersapi', '0053_merge_20200521_1119'),
    ]

    operations = [
        migrations.RunPython(create_admin_user_if_missing,
                             migrations.RunPython.noop),
        migrations.RunPython(create_roles_if_missing,
                             migrations.RunPython.noop),
    ]
