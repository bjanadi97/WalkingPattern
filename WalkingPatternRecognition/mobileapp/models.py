import django
# from django.db import models
from djongo import models
from django.utils import timezone
from django.contrib.auth.models import User


class Dog(models.Model):
    GENDER_TYPES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('U', 'Unknown'),
    )
    name = models.CharField(max_length=50)
    birthday = models.DateField()
    breed = models.CharField(max_length=20)
    gender = models.CharField(max_length=1, choices=GENDER_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    imageUrl = models.CharField(max_length=500)

    def __str__(self):
        return self.name


class Activity(models.Model):
    name = models.CharField(max_length=10)
    activity_id = models.IntegerField()

    def __str__(self):
        "{}".format(self.name)


class MotionActivityPerDay(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE)
    date = models.DateField(default=django.utils.timezone.now)
    activity = models.IntegerField()
    timePeriod = models.IntegerField()
    week = models.IntegerField(null=True)
    month = models.IntegerField(null=True)
    year = models.IntegerField(null=True)

    def __str__(self):
        "{} - {} - {} - {}".format(self.dog, self.date, self.activity, self.timePeriod)


class MotionActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE)
    date = models.DateField(default=django.utils.timezone.now)
    time = models.DateTimeField()
    hour = models.IntegerField(null=True)
    activity = models.IntegerField(null=True)

    def __str__(self):
        "{} - {} - {} - {} - {}".format(self.dog, self.date, self.activity, self.date, self.time)


class DogStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE)
    date = models.DateField(default=django.utils.timezone.now)
    activity = models.IntegerField(null=True)
    status = models.CharField(null=True, max_length=25)

    def __str__(self):
        "{} - {} - {} - {} ".format(self.dog, self.date, self.activity, self.date)


class Breed(models.Model):
    name = models.CharField(null=True, max_length=30)
    slug = models.CharField(null=True, max_length=20)
    restingMinutes = models.JSONField(default=list, blank=True, null=True)
    activityPerDay = models.IntegerField(null=True)
    walkPerWeek = models.IntegerField(null=True)

    def __str__(self):
        "{} - {} - {} - {} ".format(self.name, self.slug, self.restingMinutes, self.restingMinutes, self.activityPerDay,
                                    self.walkPerWeek)
