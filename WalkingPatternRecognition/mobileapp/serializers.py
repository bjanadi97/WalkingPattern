from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth.models import User
from .models import Dog, MotionActivityPerDay, Activity, MotionActivity, DogStatus, Breed


class UserSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=User.objects.all(),
                fields=['username', 'email']
            )
        ]


class DogSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dog
        fields = ('id', 'name', 'birthday', 'breed', 'gender', 'user')


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ('name', 'activity_id')


class MotionActivityPerDaySerializer(serializers.ModelSerializer):

    class Meta:
        model = MotionActivityPerDay
        fields = ('user', 'dog', 'date', 'activity', 'timePeriod', 'week', 'month', 'year')


class MotionActivitySerializer(serializers.ModelSerializer):

    class Meta:
        model = MotionActivity
        fields = ('user_id', 'dog_id', 'date', 'time', 'activity')


class DogStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = DogStatus
        fields = ('user_id', 'dog_id', 'date', 'activity', 'status')


class BreedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Breed
        fields = ('name', 'slug', 'restingMinutes', 'activityPerDay', 'walkPerWeek')




