from django.contrib.auth.models import User, Group, Permission
from django.core.management.base import BaseCommand

from ticket.models import ProblemSource, Analytics


class Command(BaseCommand):
    help = "Creates dev admin superuser and IT & Employee Groups with proper permissions"

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            # Create Admin
            admin = User.objects.create_superuser(
                username="admin",
                password="admin",
                first_name="Admin"
            )
            admin.save()

            # Create Employee
            emp = User.objects.create(
                username="mitarbeiter",
                password="mitarbeiter123!",
                first_name="Max Mitarbeiter"
            )
            emp.save()

            # Update problem source breadcrumbs
            for source in ProblemSource.objects.all():
                source.save()

            # Create Analytics
            Analytics.update_tickets_per_problem_source()
            Analytics.update_tickets_per_day()


