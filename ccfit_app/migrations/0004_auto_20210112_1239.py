# Generated by Django 3.1.4 on 2021-01-12 12:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ccfit_app', '0003_userprofileinfo_membership'),
    ]

    operations = [
        migrations.RenameField(
            model_name='invoice',
            old_name='valor',
            new_name='cost',
        ),
    ]