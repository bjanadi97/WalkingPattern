# Generated by Django 3.0.5 on 2020-09-16 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapp', '0005_dogstatus'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dogstatus',
            name='time',
        ),
        migrations.AddField(
            model_name='dogstatus',
            name='status',
            field=models.CharField(max_length=25, null=True),
        ),
    ]
