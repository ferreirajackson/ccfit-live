# Generated by Django 3.1.4 on 2021-01-26 22:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ccfit_app', '0018_auto_20210123_1733'),
    ]

    operations = [
        migrations.AddField(
            model_name='maxsession',
            name='a_classes',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='maxsession',
            name='enrolment',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='maxsession',
            name='w_only',
            field=models.IntegerField(null=True),
        ),
    ]
