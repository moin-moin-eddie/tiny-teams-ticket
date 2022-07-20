import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "helptext"

    def handle(self, *args, **options):
        try:
            os.remove('db.sqlite3')
            os.remove('huey.db')
        except:
            pass
        os.system('pip install -r requirements/dev-requirements.txt')
        os.system('python manage.py migrate')
        os.system('python manage.py loaddata data_fixtures')
        os.system('python manage.py devinit')
        os.system('python manage.py makedummydata')
        os.system('python manage.py runserver')
