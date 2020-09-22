from django.urls import include, path
from . import views
from .views import UserRecordView

app_name = 'api'
urlpatterns = [

  path('', views.index, name='index'),
  path('register', views.register, name='register'),
  path('user/', UserRecordView.as_view(), name='users'),

  path('dogs/', views.DogList.as_view()),
  path('addDogProfile', views.add_DogProfile),
  path('updateDogProfile/<int:dog_id>', views.update_DogProfile),
  path('deleteDogProfile', views.delete_DogProfile),

  path('addMotionActivityPerDay', views.add_motionActivityPerDay),
  path('updateMotionActivityPerDay/<int:id>', views.update_MotionActivityPerDay),
  path('motionActivityPerDay', views.MotionActivityPerDayList.as_view()),
  path('deleteMotionActivityPerDay/<int:motion_id>', views.delete_motionActivityPerDay),

  path('addActivity', views.add_Activity),
  path('getActivityData/<int:activity_id>', views.DataBasedOnActivity),
  path('getActivityNameById', views.getActivityNameById),

  # Daily
  path('getTotalMinutesPerDay', views.getTotalMinutesPerDay),
  path('getTotalMinutesPerHour', views.getTotalMinutesPerHour),
  path('highlightsPerDay', views.highlightsPerDay),

  # Weekly
  path('getTotalMinutesPerWeek', views.getTotalMinutesPerWeek),
  path('getTotalMinutesPerDayInWeek', views.getTotalMinutesPerDayInWeek),
  path('highlightsPerWeek', views.highlightsPerWeek),

  # Monthly
  path('getTotalMinutesPerMonth', views.getTotalMinutesPerMonth),
  path('getWeeklyDetailsInMonth', views.getWeeklyDetailsInMonth),
  path('highlightsPerMonth', views.highlightsPerMonth),

  # Annually
  path('getTotalMinutesPerYear', views.getTotalMinutesPerYear),
  path('getMonthlyDetailsInYear', views.getMonthlyDetailsInYear),
  path('highlightsPerYear', views.highlightsPerYear),

  # getting the readings
  path('readings', views.readings),
  path('trainingReadings', views.trainingReadings)

]
