# Generated by Django 3.1.4 on 2021-01-11 22:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ccfit_app', '0002_invoice'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofileinfo',
            name='membership',
            field=models.CharField(choices=[('WORKOUT ONLY', 'WORKOUT ONLY'), ('ALL CLASSES', 'ALL CLASSES')], max_length=15, null=True),
        ),
    ]