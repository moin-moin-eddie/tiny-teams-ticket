import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from ticket.models import ProblemSource


class Command(BaseCommand):
    help = "helptext"

    def handle(self, *args, **options):
        # Empty database
        os.system('python manage.py flush')
        # Create Admin
        admin = User.objects.create_superuser(
            username="admin",
            password=os.getenv('ADMIN_PW', 'N8schicht#'),
            first_name="ITticket Admin"
        )
        admin.save()
        # Load Problem sources & save to generate breadcrumbs
        os.system('python manage.py loaddata data_fixtures')
        for problem in ProblemSource.objects.all():
            problem.save()
        # Create Factory Boy dummy data
        os.system('python manage.py makedummydata')
