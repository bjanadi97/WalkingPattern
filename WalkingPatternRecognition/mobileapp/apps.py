from apscheduler.schedulers.background import BackgroundScheduler
from django.apps import AppConfig


class MobileappConfig(AppConfig):
    name = 'mobileapp'

    def ready(self):
        print("Starting the Server....")

        

