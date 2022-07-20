from django.core.management.base import BaseCommand

from ticket.models import Analytics


class Command(BaseCommand):
    help = "Update Analytics data"

    def handle(self, *args, **options):
        Analytics.update_tickets_per_day()
        Analytics.update_tickets_per_problem_source()