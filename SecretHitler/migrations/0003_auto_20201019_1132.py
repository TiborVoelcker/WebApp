# Generated by Django 3.1.2 on 2020-10-19 09:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('SecretHitler', '0002_user_game'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='User',
            new_name='Players',
        ),
    ]
