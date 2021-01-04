# Generated by Django 3.0.5 on 2020-10-08 18:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import djongo.models.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mobileapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Breed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, null=True)),
                ('slug', models.CharField(max_length=20, null=True)),
                ('restingMinutes', djongo.models.fields.JSONField(blank=True, default=list, null=True)),
                ('activityPerDay', models.IntegerField(null=True)),
                ('walkPerWeek', models.IntegerField(null=True)),
            ],
        ),
        migrations.AddField(
            model_name='dog',
            name='imageUrl',
            field=models.CharField(default='https://via.placeholder.com/150', max_length=500),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='DogStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('activity', models.IntegerField(null=True)),
                ('status', models.CharField(max_length=25, null=True)),
                ('dog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mobileapp.Dog')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
