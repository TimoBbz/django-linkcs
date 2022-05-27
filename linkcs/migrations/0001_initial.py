# Generated by Django 3.2.4 on 2022-05-08 15:59
from django.conf import settings
from django.contrib.auth import get_user_model
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkCSProfile',
            fields=[
                ('user_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('linkcs_id', models.IntegerField(help_text='The LinkCS id (if the user has LinkCS)', null=True, unique=True, verbose_name='LinkCS ID')),
            ],
            options={
                'verbose_name': 'LinkCS profile',
                'permissions': [('request_linkcs', 'Can make a request to LinkCS')],
                'swappable': 'AUTH_PROFILE_MODEL',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
