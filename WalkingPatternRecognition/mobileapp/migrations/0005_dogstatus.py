# Generated by Django 3.0.5 on 2020-09-16 12:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mobileapp', '0004_motionactivity'),
    ]

    operations = [
        migrations.CreateModel(
            name='DogStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('time', models.DateTimeField()),
                ('activity', models.IntegerField(null=True)),
                ('dog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mobileapp.Dog')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]