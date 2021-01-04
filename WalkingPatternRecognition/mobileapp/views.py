import json
from datetime import timedelta

from background_task import background
from background_task.models import Task
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from numba.cuda import const
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Dog, MotionActivityPerDay, Activity, Breed, DogStatus, MotionActivity
from .serializers import DogSerializer, MotionActivityPerDaySerializer, ActivitySerializer, BreedSerializer, \
    DogStatusSerializer, MotionActivitySerializer
from .serializers import UserSerializer
import calendar
import requests
from django.http import HttpResponse, response, request
from apscheduler.schedulers.background import BackgroundScheduler
from csv import writer
import joblib
import pandas as pd
import numpy as np
from sympy import fft
from datetime import datetime
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import make_password


def index(request):
    return render(request, 'user_example/index.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            # return redirect('user_example/index.html')
            return JsonResponse({'user': user, 'error': 'No error'}, safe=False, status=status.HTTP_201_CREATED)
    else:
        form = UserCreationForm()
    context = {'form': form}
    return render(request, 'registration/register.html', context)


@api_view(["POST"])
@csrf_exempt
def registerUser(request):
    payload = json.loads(request.body)
    try:
        user = authenticate(username=payload['username'], password=payload['password'])

        userObject = User.objects.create(
            username=payload["username"],
            password=make_password(payload['password']),
            email=payload["email"]
        )
        serializer = UserSerializer(userObject)
        user = authenticate(username=payload['username'], password=make_password(payload['password']))
        login(request, user)
        return JsonResponse({'user': 'data', 'error': 'No'}, safe=False, status=status.HTTP_201_CREATED)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'NoUserError': 'error'}, safe=False,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserRecordView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, format=None):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=ValueError):
            serializer.create(validated_data=request.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "error": True,
                "error_msg": serializer.error_messages,
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })

# DOGS


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getDogsBasedOnUser(request):
    payload = json.loads(request.body)
    dog = Dog.objects.filter(user_id=payload['userId'])
    serializer = DogSerializer(dog, many=True)
    return JsonResponse([{'dog': serializer.data[0]}], safe=False, status=status.HTTP_200_OK)


class DogList(APIView):
    def get(self, request):
        dogs = Dog.objects.all()
        serializer = DogSerializer(dogs, many=True)
        return Response(serializer.data)

    def post(self):
        pass


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def add_DogProfile(request):
    payload = json.loads(request.body)
    user = request.user
    try:
        dog = Dog.objects.create(
            name=payload["name"],
            birthday=payload["birthday"],
            breed=payload["breed"],
            gender=payload["gender"],
            user=user,
            imageUrl=payload['imageUrl']
        )
        serializer = DogSerializer(dog)
        return JsonResponse({'dog': serializer.data}, safe=False, status=status.HTTP_201_CREATED)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def update_DogProfile(request, dog_id):
    payload = json.loads(request.body)
    try:
        item = Dog.objects.filter(id=dog_id)
        # returns 1 or 0
        item.update(**payload)
        dog = Dog.objects.get(id=dog_id)
        serializer = DogSerializer(dog)
        return JsonResponse({'dog': serializer.data}, safe=False, status=status.HTTP_200_OK)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'error': Exception}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["DELETE"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def delete_DogProfile(request):
    payload = json.loads(request.body)
    try:
        dog = Dog.objects.get(id=payload["id"])
        dog.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'error': 'Something went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ACTIVITY

@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def add_Activity(request):
    payload = json.loads(request.body)
    try:
        activity = Activity.objects.create(
            name=payload["name"],
            activity_id=payload["activity_id"],

        )
        serializer = ActivitySerializer(activity)
        return JsonResponse({'activity': serializer.data}, safe=False, status=status.HTTP_201_CREATED)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR) @ api_view(["POST"])


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getActivityNameById(request):
    payload = json.loads(request.body)
    activity = Activity.objects.filter(activity_id=payload['id'])
    serializer = ActivitySerializer(activity, many=True)
    return JsonResponse([{'activity': serializer.data[0]['name']}], safe=False, status=status.HTTP_200_OK)


# MOTION ACTIVITY PER DAY

@api_view(["GET"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def DataBasedOnActivity(request, activity_id):
    activities = MotionActivityPerDay.objects.filter(activity_id=activity_id)
    serializer = MotionActivityPerDaySerializer(activities, many=True)
    return JsonResponse({'activities': serializer.data}, safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def add_motionActivityPerDay(request):
    payload = json.loads(request.body)
    user = request.user
    dog = Dog.objects.get(id=payload["dog"])
    activity = Activity.objects.get(activity_id=payload["activity"])
    ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
    week = ConvertedDate.isocalendar()[1]
    month = ConvertedDate.month
    year = ConvertedDate.year
    try:
        motion = MotionActivityPerDay.objects.create(
            user=user,
            dog=dog,
            date=payload["date"],
            activity=payload["activity"],
            timePeriod=payload["timePeriod"],
            week=week,
            month=month,
            year=year
        )
        serializer = MotionActivityPerDaySerializer(motion)
        return JsonResponse({'motions': serializer.data}, safe=False, status=status.HTTP_201_CREATED)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({Exception}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR) @ api_view(["POST"])


@api_view(["PUT"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def update_MotionActivityPerDay(request, id):
    payload = json.loads(request.body)
    try:
        item = MotionActivityPerDay.objects.filter(id=id)
        # returns 1 or 0
        ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
        item.week = ConvertedDate.isocalendar()[1]
        item.month = ConvertedDate.month
        item.year = ConvertedDate.year
        item.update(**payload)
        motion = MotionActivityPerDay.objects.get(id=id)
        serializer = MotionActivityPerDaySerializer(motion)
        return JsonResponse({'motion': serializer.data}, safe=False, status=status.HTTP_200_OK)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MotionActivityPerDayList(APIView):
    def get(self, request):
        activities = MotionActivityPerDay.objects.all()
        serializer = MotionActivityPerDaySerializer(activities, many=True)
        return Response(serializer.data)


@api_view(["DELETE"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def delete_motionActivityPerDay(request, motion_id):
    try:
        motion = MotionActivityPerDay.objects.get(id=motion_id)
        motion.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'error': 'Something went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# DAILY

@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getTotalMinutesPerDay(request):
    payload = json.loads(request.body)
    minutes = MotionActivity.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                  date=payload['date'])
    serializer = MotionActivitySerializer(minutes, many=True)

    if len(serializer.data) > 0:
        dailyTotal = 0
        for i in range(len(serializer.data)):
            dailyTotal += 1
        return JsonResponse([{'minutes per day': dailyTotal}], safe=False,
                            status=status.HTTP_200_OK)
    else:
        return JsonResponse([{'minutes per day': 0}], safe=False,
                            status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getTotalMinutesPerHour(request):
    payload = json.loads(request.body)
    n = 24
    hours = [None] * n
    for i in range(24):
        period = MotionActivity.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                               date=payload['date'], hour=i)
        serializer1 = MotionActivitySerializer(period, many=True)

        hourlyTotal = 0
        if len(serializer1.data) > 0:
            for j in range(len(serializer1.data)):
                hourlyTotal += 1

            hours[i] = hourlyTotal

    return JsonResponse({'hour array': hours, 'date': payload['date']}, safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def highlightsPerDay(request):
    payload = json.loads(request.body)
    ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
    yesterday = ConvertedDate - timedelta(days=1)
    todayActivity = MotionActivity.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                        date=payload['date'])
    yesterdayActivity = MotionActivityPerDay.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                            date=yesterday)
    serializer1 = MotionActivitySerializer(todayActivity, many=True)
    serializer2 = MotionActivityPerDaySerializer(yesterdayActivity, many=True)

    if len(serializer1.data) == 0:
        today = 0
    if len(serializer2.data) == 0:
        yesterdayTime = 0
    if len(serializer2.data) != 0:
        yesterdayTime = serializer2.data[0]['timePeriod']

    dailyTotal = 0
    for i in range(len(serializer1.data)):
        dailyTotal += 1

    if dailyTotal > yesterdayTime:
        return JsonResponse(
            [{'TODAY': dailyTotal, 'YESTERDAY': yesterdayTime, 'Highlights':
                'time is higher than yesterday'}], safe=False,
            status=status.HTTP_200_OK)
    elif dailyTotal < yesterdayTime:
        return JsonResponse(
            [{'TODAY': dailyTotal, 'YESTERDAY': yesterdayTime, 'Highlights':
                'time is lower than yesterday'}], safe=False,
            status=status.HTTP_200_OK)
    elif dailyTotal == yesterdayTime:
        return JsonResponse(
            [{'TODAY': dailyTotal, 'YESTERDAY': yesterdayTime, 'Highlights':
                'time is equal to yesterday'}], safe=False,
            status=status.HTTP_200_OK)


# WEEKLY

@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getTotalMinutesPerWeek(request):
    payload = json.loads(request.body)
    ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
    week = ConvertedDate.isocalendar()[1]
    entries = MotionActivityPerDay.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                  week=week)
    serializer = MotionActivityPerDaySerializer(entries, many=True)
    totalSum = 0
    for i in range(len(serializer.data)):
        value = serializer.data[i]['timePeriod']
        totalSum += float(value)

    if len(serializer.data) > 0:
        return JsonResponse([{'week': week, 'minutes per week': totalSum}], safe=False, status=status.HTTP_200_OK)
    else:
        return JsonResponse([{'minutes per week': 0}], safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getTotalMinutesPerDayInWeek(request):
    payload = json.loads(request.body)
    ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
    week = ConvertedDate.isocalendar()[1]
    entries = MotionActivityPerDay.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                  week=week)
    entries = entries.order_by('date')
    serializer = MotionActivityPerDaySerializer(entries, many=True)
    return JsonResponse([{'week': week, 'data': serializer.data}], safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def highlightsPerWeek(request):
    payload = json.loads(request.body)
    ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
    week = ConvertedDate.isocalendar()[1]
    thisWeekEntries = MotionActivityPerDay.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                          week=week)
    previousWeek = week - 1
    lastWeekEntries = MotionActivityPerDay.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                          week=previousWeek)
    serializer1 = MotionActivityPerDaySerializer(thisWeekEntries, many=True)
    serializer2 = MotionActivityPerDaySerializer(lastWeekEntries, many=True)

    totalSum1 = 0
    for i in range(len(serializer1.data)):
        value = serializer1.data[i]['timePeriod']
        totalSum1 += float(value)

    totalSum2 = 0
    for i in range(len(serializer2.data)):
        value = serializer2.data[i]['timePeriod']
        totalSum2 += float(value)

    if totalSum1 > totalSum2:
        return JsonResponse(
            [{'this Week': totalSum1, 'last Week': totalSum2, 'Highlights':
                'greater than last Week'}], safe=False,
            status=status.HTTP_200_OK)
    elif totalSum1 < totalSum2:
        return JsonResponse(
            [{'this Week': totalSum1, 'last Week': totalSum2, 'Highlights':
                'lesser than last Week'}], safe=False,
            status=status.HTTP_200_OK)
    elif totalSum1 == totalSum2:
        return JsonResponse(
            [{'this Week': totalSum1, 'last Week': totalSum2, 'Highlights':
                'equal to last Week'}], safe=False,
            status=status.HTTP_200_OK)


# MONTHLY
@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getWeeklyDetailsInMonth(request):
    global range
    payload = json.loads(request.body)
    year = payload['year']
    month = payload['month']
    ending_day = calendar.monthrange(year, month)[1]  # get the last day of month
    initial_week = datetime(year, month, 1).isocalendar()[1]
    ending_week = datetime(year, month, ending_day).isocalendar()[1]
    weeks = []
    for i in range(initial_week, ending_week + 1):
        weeks.append(i)
    weekArray, minutes = [], []
    for i in weeks:
        weekArray.append(i)
        entries = MotionActivityPerDay.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                      week=i)

        serializer = MotionActivityPerDaySerializer(entries, many=True)
        totalSum = 0
        for j in range(len(serializer.data)):
            value = serializer.data[j]['timePeriod']
            totalSum += float(value)
        minutes.append(totalSum)

    return JsonResponse([{'month': payload['month'], 'initial week': initial_week, 'final week': ending_week,
                          'weeks': weekArray, 'minutes': minutes}], safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getTotalMinutesPerMonth(request):
    payload = json.loads(request.body)

    entries = MotionActivityPerDay.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                  month=payload['month'])
    serializer = MotionActivityPerDaySerializer(entries, many=True)
    totalSum = 0
    for i in range(len(serializer.data)):
        value = serializer.data[i]['timePeriod']
        totalSum += float(value)

    if len(serializer.data) > 0:
        return JsonResponse([{'month': payload['month'], 'minutes per month': totalSum}], safe=False,
                            status=status.HTTP_200_OK)
    else:
        return JsonResponse([{'month': payload['month'], 'minutes per month': 0}], safe=False,
                            status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def highlightsPerMonth(request):
    payload = json.loads(request.body)
    month = payload['month']
    thisMonthEntries = MotionActivityPerDay.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                           month=month)
    previousMonth = int(month) - 1
    lastMonthEntries = MotionActivityPerDay.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                           month=previousMonth)
    serializer1 = MotionActivityPerDaySerializer(thisMonthEntries, many=True)
    serializer2 = MotionActivityPerDaySerializer(lastMonthEntries, many=True)

    totalSum1 = 0
    for i in range(len(serializer1.data)):
        value = serializer1.data[i]['timePeriod']
        totalSum1 += float(value)

    totalSum2 = 0
    for i in range(len(serializer2.data)):
        value = serializer2.data[i]['timePeriod']
        totalSum2 += float(value)

    if totalSum1 > totalSum2:
        return JsonResponse(
            [{'this month': totalSum1, 'last month': totalSum2, 'Highlights':
                'greater than last month'}], safe=False,
            status=status.HTTP_200_OK)
    elif totalSum1 < totalSum2:
        return JsonResponse(
            [{'this month': totalSum1, 'last month': totalSum2, 'Highlights':
                'lesser than last month'}], safe=False,
            status=status.HTTP_200_OK)
    elif totalSum1 == totalSum2:
        return JsonResponse(
            [{'this month': totalSum1, 'last month': totalSum2, 'Highlights':
                'equal to last month'}], safe=False,
            status=status.HTTP_200_OK)


# ANNUALLY


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getTotalMinutesPerYear(request):
    payload = json.loads(request.body)
    # ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
    # year = ConvertedDate.year
    entries = MotionActivityPerDay.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                  year=payload['year'])
    serializer = MotionActivityPerDaySerializer(entries, many=True)
    totalSum = 0
    for i in range(len(serializer.data)):
        value = serializer.data[i]['timePeriod']
        totalSum += float(value)

    if len(serializer.data) > 0:
        return JsonResponse([{'year': payload['year'], 'minutes per year': totalSum}], safe=False,
                            status=status.HTTP_200_OK)
    else:
        return JsonResponse([{'year': payload['year'], 'minutes per year': 0}], safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getMonthlyDetailsInYear(request):
    global range
    payload = json.loads(request.body)
    year = payload['year']
    minutes = []
    for i in range(1, 13):
        entries = MotionActivityPerDay.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                      month=i, year=year)
        serializer = MotionActivityPerDaySerializer(entries, many=True)
        totalSum = 0
        for j in range(len(serializer.data)):
            value = serializer.data[j]['timePeriod']
            totalSum += float(value)
        minutes.append(totalSum)

    return JsonResponse([{'year': payload['year'], 'minutes': minutes}], safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def highlightsPerYear(request):
    payload = json.loads(request.body)

    thisWeekEntries = MotionActivityPerDay.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                          year=payload['year'])
    previousYear = int(payload['year']) - 1
    lastWeekEntries = MotionActivityPerDay.objects.filter(activity=payload['activity'], dog=payload['dog'],
                                                          year=previousYear)
    serializer1 = MotionActivityPerDaySerializer(thisWeekEntries, many=True)
    serializer2 = MotionActivityPerDaySerializer(lastWeekEntries, many=True)

    totalSum1 = 0
    for i in range(len(serializer1.data)):
        value = serializer1.data[i]['timePeriod']
        totalSum1 += float(value)

    totalSum2 = 0
    for i in range(len(serializer2.data)):
        value = serializer2.data[i]['timePeriod']
        totalSum2 += float(value)

    if totalSum1 > totalSum2:
        return JsonResponse(
            [{'this year': totalSum1, 'last year': totalSum2, 'Highlights':
                'greater than last year'}], safe=False,
            status=status.HTTP_200_OK)
    elif totalSum1 < totalSum2:
        return JsonResponse(
            [{'this year': totalSum1, 'last year': totalSum2, 'Highlights':
                'lesser than last year'}], safe=False,
            status=status.HTTP_200_OK)
    elif totalSum1 == totalSum2:
        return JsonResponse(
            [{'this year': totalSum1, 'last year': totalSum2, 'Highlights':
                'equal to last year'}], safe=False,
            status=status.HTTP_200_OK)


# READINGS

def readings(request):
    sched = BackgroundScheduler()
    # seconds can be replaced with minutes, hours, or days
    sched.add_job(getReadings, 'interval', seconds=2)
    sched.start()
    return JsonResponse({'data': "Data obtained"}, safe=False, status=status.HTTP_201_CREATED)


@csrf_exempt
def getReadings():
    ReadingsArray = []

    responseObtained = requests.get('http://192.168.1.7/getReadings')

    # if(responseObtained):
    #     print("Successfully Obtaining readings from ... http://192.168.1.6/getReadings")
    # else:
    #     print("Unsuccessful Connection")

    result = responseObtained.text
    Array = result.split(",")
    length = len(Array)
    i = 0
    while i < length:
        reading = Array[i]
        ReadingsArray.append(reading.split(":"))
        i = i + 1
    finalArray = obtainReadings(ReadingsArray)
    print(finalArray)

    file = open("Readings.csv")
    numline = len(file.readlines())
    if numline < 31:
        append_list_as_row('Readings.csv', finalArray)
    else:
        # trying to get the prediction
        Main()
        with open("Readings.csv", 'r') as f:
            with open("Readings.csv", 'w') as f1:
                next(f, None)
                for line in f:
                    f1.close()
        append_list_as_row('Readings.csv', ['timestamp', 'accelerometer_X', 'accelerometer_Y', 'accelerometer_Z',
                                            'gyroscope_X', 'gyroscope_Y', 'gyroscope_Z'])

    return HttpResponse(response)


def obtainReadings(array):
    newReadingArray = [datetime.now()]
    length = len(array)
    i = 0
    while i < length:
        newReadingArray.append(array[i][1])
        i = i + 1
    return newReadingArray


def append_list_as_row(file_name, list_of_elem):
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        csv_writer.writerow(list_of_elem)


class Main:

    def __init__(self):
        d = Data('Readings.csv')
        data = d.ReadData()
        i, j = 0, 0
        length = len(data)
        while i <= length:
            Index = []
            count = i + 30
            if j < length:
                while j <= count:
                    Index.append(j)
                    j = j + 1
                # print(Index)
                fIndex, lIndex = Index[0], Index[-1]
                dataset = data.iloc[fIndex: lIndex + 1]
                gd1 = GetData(dataset)
                f = FeatureExtraction(gd1)

                FeatureVector = f.getSmallTestFeatureSingle(dataset)
                append_list_as_row('FeatureVectorTest.csv', FeatureVector)
                r = Data('FeatureVectorTest.csv')
                predictingActivity = r.ReadData()
                predictedActivity = Test(predictingActivity)
            else:
                break
            i = i + 30

            # # Start a scheduler to get the activity count at the end of the day
            # end()


class Data:
    data = ''
    Read = []

    def __init__(self, data):
        self.data = data

    def ReadData(self):
        self.Read = pd.read_csv(self.data)
        return self.Read

    def append_list_as_row(self, file_name, list_of_elem):
        # Open file in append mode
        with open(file_name, 'a+', newline='') as write_obj:
            # Create a writer object from csv module
            csv_writer = writer(write_obj)
            # Add contents of list as last row in the csv file
            csv_writer.writerow(list_of_elem)


class GetData:
    data = []

    def __init__(self, data):
        self.data = data

    def getAccX(self, data):
        X = []
        for i, row in data.iterrows():
            X.append(float(data.xs(i)['accelerometer_X']))
        return X

    def getAccY(self, data):
        Y = []
        for i, row in data.iterrows():
            Y.append(float(data.xs(i)['accelerometer_Y']))
        return Y

    def getAccZ(self, data):
        Z = []
        for i, row in data.iterrows():
            Z.append(float(data.xs(i)['accelerometer_Z']))
        return Z

    def getGyrX(self, data):
        X = []
        for i, row in data.iterrows():
            X.append(float(data.xs(i)['gyroscope_X']))
        return X

    def getGyrY(self, data):
        Y = []
        for i, row in data.iterrows():
            Y.append(float(data.xs(i)['gyroscope_Y']))
        return Y

    def getGyrZ(self, data):
        Z = []
        for i, row in data.iterrows():
            Z.append(float(data.xs(i)['gyroscope_Z']))
        return Z

    def getMagnitude(self, data):
        Magnitudes = []
        for i, row in data.iterrows():
            Magnitude = ((float(data.xs(i)['accelerometer_X'])) ** 2 + (float(data.xs(i)['accelerometer_Y'])) ** 2 + (
                float(data.xs(i)['accelerometer_Z'])) ** 2) ** 0.5
            Magnitudes.append(Magnitude)
        return Magnitudes

    def getActivities(self, data):
        Activities = []
        for i, row in data.iterrows():
            Activities.append(data.xs(i)['activity'])
        return Activities

    def getStartAndEndTime(self, data):
        Times = []
        StartTime = data['timestamp'].iloc[0]
        Times.append(StartTime)
        EndTime = data['timestamp'].iloc[-1]
        Times.append(EndTime)
        return Times


class FeatureExtraction:
    list = []

    def __init__(self, list):
        self.list = list

    def MinimumPeak(self, list):
        min_value = None
        for value in list:
            if not min_value:
                min_value = value
            elif value < min_value:
                min_value = value
        return min_value

    def MaximumPeak(self, list):
        max_value = None
        for value in list:
            if not max_value:
                max_value = value
            elif value > max_value:
                max_value = value
        return max_value

    def Mean(self, list):
        return sum(list) / len(list)

    def median(self, list):
        n = len(list)
        s = sorted(list)
        return (sum(s[n // 2 - 1:n // 2 + 1]) / 2.0, s[n // 2])[n % 2] if n else None

    def Variance(self, list):
        return np.var(list)

    def StandardDeviation(self, list):
        return (np.var(list)) ** 0.5

    def Energy(self, list):
        transformed = fft(list, 4)
        array = np.array(transformed)
        return max(np.absolute(array))

    def RMS(self, list):
        RMSTotal = 0.0
        for i in list:
            RMSTotal += (i ** 2)
        return ((RMSTotal) ** 0.5)

    def getSmallTestFeatureSingle(self, list):
        d = GetData(list)

        AccX = d.getAccX(list)
        AccY = d.getAccY(list)
        AccZ = d.getAccZ(list)

        GyrX = d.getGyrX(list)
        GyrY = d.getGyrY(list)
        GyrZ = d.getGyrZ(list)

        times = d.getStartAndEndTime(list)

        fe = FeatureExtraction(list)
        feature = []

        feature.append(fe.MinimumPeak(AccX))
        feature.append(fe.MinimumPeak(AccY))
        feature.append(fe.MinimumPeak(AccZ))
        feature.append(fe.MaximumPeak(AccX))
        feature.append(fe.MaximumPeak(AccY))
        feature.append(fe.MaximumPeak(AccZ))
        feature.append(fe.Mean(AccX))
        feature.append(fe.Mean(AccY))
        feature.append(fe.Mean(AccZ))

        feature.append(fe.MinimumPeak(GyrX))
        feature.append(fe.MinimumPeak(GyrY))
        feature.append(fe.MinimumPeak(GyrZ))
        feature.append(fe.MaximumPeak(GyrX))
        feature.append(fe.MaximumPeak(GyrY))
        feature.append(fe.MaximumPeak(GyrZ))
        feature.append(fe.Mean(GyrX))
        feature.append(fe.Mean(GyrY))
        feature.append(fe.Mean(GyrZ))

        feature.append(times[0])
        feature.append(times[1])

        print("Feature Vector \n", feature, "\n\n");
        return feature

    def getFeatureSingle(self, list):
        d = GetData(list)
        X = d.getAccX(list)
        Y = d.getAccY(list)
        Z = d.getAccZ(list)
        times = d.getStartAndEndTime(list)
        fe = FeatureExtraction(list)
        feature = [fe.MinimumPeak(X), fe.MinimumPeak(Y), fe.MinimumPeak(Z), fe.MaximumPeak(X), fe.MaximumPeak(Y),
                   fe.MaximumPeak(Z), fe.Mean(X), fe.Mean(Y), fe.Mean(Z), times[0], times[1]]
        print("Small Feature Vector \n", feature, "\n\n")
        return feature


class ReadData:
    data = ''

    def __init__(self, data):

        self.data = data
        # print(data)

    def returnArray(self, data):
        finalArray = []
        i, Rest, Walk, Run = 0, 0, 0, 0

        while i < len(data):
            if data.xs(i)['Activity'] == 0:
                Rest += 1
            if data.xs(i)['Activity'] == 1:
                Walk += 1
            if data.xs(i)['Activity'] == 2:
                Run += 1
            i += 1

        finalArray.append(Rest)
        finalArray.append(Walk)
        finalArray.append(Run)
        return finalArray


class Test:
    data = ''
    activity = ''

    def __init__(self, data):
        self.data = data
        with open("FeatureVectorTest.csv", 'r') as f:
            with open("FeatureVectorTest.csv", 'w') as f1:
                for line in f:
                    f1.close()
        append_list_as_row('FeatureVectorTest.csv', ['AccXmin', 'AccYmin', 'AccZmin', 'AccXmax',
                                                     'AccYmax', 'AccZmax', 'AccXmean', 'AccYmean', 'AccZmean',
                                                     'GyrXmin', 'GyrYmin', 'GyrZmin', 'GyrXmax',
                                                     'GyrYmax', 'GyrZmax', 'GyrXmean', 'GyrYmean', 'GyrZmean',
                                                     'StartTime', 'EndTime'])
        Times = data.loc[:, ['StartTime', 'EndTime']]
        data = data.drop(['StartTime', 'EndTime'], axis=1)
        X_test = data[:]
        StartTime = Times.xs(0)['StartTime']
        EndTime = Times.xs(0)['EndTime']
        Date = Times.xs(0)['EndTime']

        ActivityArray = []
        dictionary = []

        # load the Gaussian Bayes Model from disk
        filename = 'Janadi.sav'
        model = joblib.load(filename)
        prediction = model.predict(X_test)
        activityPrediction = prediction.tolist().pop()

        if activityPrediction == 0:
            activity = 'rest'
        if activityPrediction == 1:
            activity = 'walk'
        if activityPrediction == 2:
            activity = 'run'

        print("PREDICTION ---->", activityPrediction, " ", activity, "\n\n")

        times = StartTime.split(" ")
        time_object = datetime.strptime(times[1], '%H:%M:%S.%f').time()
        hour = time_object.hour

        date = datetime.utcnow().strftime("%Y-%m-%d")
        ConvertedDate = datetime.strptime(date, "%Y-%m-%d").date()
        # ConvertedDate = datetime.now()
        motion = MotionActivity.objects.create(
            user_id=1,
            dog_id=1,
            date=ConvertedDate,
            time=StartTime,
            hour=hour,
            activity=activityPrediction
        )
        MotionActivitySerializer(motion)

        ActivityArray.append(StartTime)
        ActivityArray.append(EndTime)
        ActivityArray.append(Date)
        ActivityArray.append(activityPrediction)

        dictionary.append(Date)
        dictionary.append(activityPrediction)

        d = Data(ActivityArray)
        append_list_as_row('FeatureVectorsTest.csv', ActivityArray)

        Dictionary(dictionary)


class Dictionary:
    data = ''

    def __init__(self, data):
        self.data = data
        Dictionary = {data[0]: data[1]}
        # print(Dictionary)
        # x = Dictionary[DateTime()]
        # print("Dict activity", x)


# ACTION AT THE END OF THE DAY

@background()
def printHello():
    print("Hello")
    status = DogStatus.objects.create(
        user_id=1,
        dog_id=1,
        status='highh',

    )
    DogStatusSerializer(status)


def deleteMotionActivityTableData(request):
    try:
        activity = MotionActivity.objects.get()
        activity.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'error': 'Something went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def endOfEachDay(request):
    payload = json.loads(request.body)
    breed = payload['breed']
    dog = payload['dog_id']

    sched = BackgroundScheduler()
    sched.add_job(endOfTheDay(breed, dog), 'interval', days=1)
    sched.start()
    return JsonResponse({'data': "Comparison at the End of the Day"}, safe=False, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def endOfTheDay(breed, dog):
    print("At the End of the day...", datetime.now())
    d1 = Data('FeatureVectorsTest.csv')
    data1 = d1.ReadData()
    r = ReadData(data1)
    result = r.returnArray(data1)

    # add the data to the database here
    ConvertedDate = datetime.now()
    week = ConvertedDate.isocalendar()[1]
    month = ConvertedDate.month
    year = ConvertedDate.year

    restMinutes = result[0]
    walkMinutes = result[1]
    runMinutes = result[2]

    # Compare the Breed Data
    compareBreedData(breed, walkMinutes, runMinutes)

    # Add the final results to the Motion Activity Per Day table

    # motion1 = MotionActivityPerDay.objects.create(
    #     user_id=1,
    #     dog_id=1,
    #     date=ConvertedDate,
    #     activity=0,
    #     timePeriod=restMinutes,
    #     week=week,
    #     month=month,
    #     year=year
    # )
    # MotionActivityPerDaySerializer(motion1)
    #
    # motion2 = MotionActivityPerDay.objects.create(
    #     user_id=1,
    #     dog_id=1,
    #     date=ConvertedDate,
    #     activity=1,
    #     timePeriod=walkMinutes,
    #     week=week,
    #     month=month,
    #     year=year
    # )
    # MotionActivityPerDaySerializer(motion2)
    #
    # motion3 = MotionActivityPerDay.objects.create(
    #     user_id=1,
    #     dog_id=1,
    #     date=ConvertedDate,
    #     activity=2,
    #     timePeriod=runMinutes,
    #     week=week,
    #     month=month,
    #     year=year
    # )
    # MotionActivityPerDaySerializer(motion3)

    with open("FeatureVectorsTest.csv", 'r') as f:
        with open("FeatureVectorsTest.csv", 'w') as f1:
            next(f, None)
            for line in f:
                f1.close()
    append_list_as_row('FeatureVectorsTest.csv', ['StartTime', 'EndTime', 'Date', 'Activity'])
    return JsonResponse({'data': "Data obtained"}, safe=False, status=status.HTTP_201_CREATED)


def compareBreedData(breed, walkingMinutes, runningMinutes):
    totalActivityMinutes, breedActivityMinutes = 0, 0
    print("Now comparing " + breed)
    activityStatusOfTheDog = ''

    breedActivityMinutes = getBreedActivityData(breed)
    totalActivityMinutes = walkingMinutes + runningMinutes

    if totalActivityMinutes > breedActivityMinutes:
        print("Activity level is high")
        activityStatusOfTheDog = 'high'
    elif totalActivityMinutes < breedActivityMinutes:
        print("The actual activity level of the dog is : " + str(breedActivityMinutes) + " minutes")
        print("But the current activity level of the dog is " + str(totalActivityMinutes) + " minutes")
        print("Therefore .. Activity level is low")
        activityStatusOfTheDog = 'low'
    elif totalActivityMinutes == breedActivityMinutes:
        print("Activity level is equal")
        activityStatusOfTheDog = 'equal'

    # Add the status to the Dog Status Table
    ConvertedDate = datetime.now()

    activityStatus = DogStatus.objects.create(
        user_id=1,
        dog_id=1,
        date=ConvertedDate,
        activity=1,
        status=activityStatusOfTheDog,
    )
    DogStatusSerializer(activityStatus)


def getBreedActivityData(breed):
    name = breed
    breedData = Breed.objects.filter(name=name)
    serializer = BreedSerializer(breedData, many=True)

    for i in range(len(serializer.data)):
        value = serializer.data[i]['activityPerDay']
    return value


@api_view(["POST"])
def compare(request):
    printHello(schedule=10, repeat=Task.DAILY)
    payload = json.loads(request.body)
    breed = payload['breed']
    ActivityMinutes = payload['time']
    totalActivityMinutes, breedActivityMinutes = 0, 0
    activityStatusOfTheDog = ''
    print(breed)
    breedActivityMinutes = getBreedActivityData(breed)
    totalActivityMinutes = ActivityMinutes

    halfValue = breedActivityMinutes / 2
    if totalActivityMinutes > breedActivityMinutes:
        print("The actual activity level of the dog is : " + str(breedActivityMinutes) + " minutes")
        print("But the current activity level of the dog is " + str(totalActivityMinutes) + " minutes")
        print("Activity level is high")
        activityStatusOfTheDog = 'high'
    elif totalActivityMinutes < halfValue:
        print("The actual activity level of the dog is : " + str(breedActivityMinutes) + " minutes")
        print("But the current activity level of the dog is " + str(totalActivityMinutes) + " minutes")
        print("Therefore .. Activity level is low")
        activityStatusOfTheDog = 'low'
    elif (totalActivityMinutes <= breedActivityMinutes) and (totalActivityMinutes >= halfValue):
        print("The actual activity level of the dog is : " + str(breedActivityMinutes) + " minutes")
        print("But the current activity level of the dog is " + str(totalActivityMinutes) + " minutes")
        print("Activity level is equal")
        activityStatusOfTheDog = 'active'
    return JsonResponse({'status': activityStatusOfTheDog}, safe=False, status=status.HTTP_201_CREATED)


# TRAINING READINGS


@csrf_exempt
def getTrainingReadings():

    ReadingsArray = []

    responseObtained = requests.get('http://192.168.1.7/getReadings')
    result = responseObtained.text
    Array = result.split(",")
    length = len(Array)
    i = 0
    while i < length:
        reading = Array[i]
        ReadingsArray.append(reading.split(":"))
        i = i + 1
    finalArray = obtainReadings(ReadingsArray)
    print(finalArray)

    file = open("TrainingRestReadings.csv")
    numline = len(file.readlines())
    if numline < 31:
        append_list_as_row('TrainingRestReadings.csv', finalArray)

    else:
        # trying to get the prediction
        MainTraining()
        with open("TrainingRestReadings.csv", 'r') as f:
            with open("TrainingRestReadings.csv", 'w') as f1:
                next(f, None)
                for line in f:
                    f1.close()
        append_list_as_row('TrainingRestReadings.csv', ['timestamp', 'accelerometer_X', 'accelerometer_Y',
                                                        'accelerometer_Z', 'gyroscope_X', 'gyroscope_Y', 'gyroscope_Z'])
    return HttpResponse(response)


def trainingReadings(request):
    sched = BackgroundScheduler()
    # seconds can be replaced with minutes, hours, or days
    sched.add_job(getTrainingReadings, 'interval', seconds=2)
    sched.start()
    return JsonResponse({'data': "Training Data obtained"}, safe=False, status=status.HTTP_201_CREATED)


class MainTraining:

    def __init__(self):
        d = Data('TrainingRestReadings.csv')
        data = d.ReadData()
        i, j = 0, 0
        length = len(data)

        while i <= length:
            Index = []
            count = i + 30
            if j < length:
                while j <= count:
                    Index.append(j)
                    j = j + 1
                # print(Index)
                fIndex, lIndex = Index[0], Index[-1]
                dataset = data.iloc[fIndex: lIndex + 1]

                gd1 = GetData(dataset)
                f = FeatureExtraction(gd1)
                FeatureVector = f.getSmallTestFeatureSingle(dataset)

                d.append_list_as_row('FeatureVectorsRest2Train.csv', FeatureVector)
            else:
                break
            i = i + 30
