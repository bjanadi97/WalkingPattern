# Generated by Django 3.0.5 on 2020-09-16 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapp', '0006_auto_20200916_1232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='motionactivity',
            name='activity',
            field=models.IntegerField(null=True),
        ),
    ]