import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Start app with docker including Huey BG worker and PG database"

    def handle(self, *args, **options):
        os.system('docker-compose up --build')
