# Generated by Django 3.1.4 on 2021-01-17 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ccfit_app', '0008_auto_20210115_1841'),
    ]

    operations = [
        migrations.AddField(
            model_name='yoga',
            name='date_audit',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='yoga',
            name='hour_audit',
            field=models.TimeField(auto_now_add=True, null=True),
        ),
    ]