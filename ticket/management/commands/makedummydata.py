import random

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from ticket.factories import UserFactory, TicketFactory, CommentFactory, TicketEventFactory
from ticket.models import Ticket, TicketEvent, random_recent_date_time
from ticket.tasks import manual_update_analytics

NUM_USERS = 100
NUM_TICKETS = 500
MAX_COMMENTS_PER_TICKET = 5
MAX_EVENTS_PER_TICKET = 10
OPEN_TICKET_RATIO = 0.08


class Command(BaseCommand):
    help = "Fill DB with dummy data"

    @transaction.atomic
    def handle(self, *args, **options):
        settings.RANDOM_TIMES = True
        # Create 90% Users
        for _ in range(int(NUM_USERS * 0.9)):
            UserFactory()

        # Create 10% Staff
        for _ in range(int(NUM_USERS * 0.1)):
            user = UserFactory()
            user.is_staff = True
            user.save()

        # Create open tickets
        for _ in range(int(NUM_TICKETS * OPEN_TICKET_RATIO)):
            TicketFactory()

        # Create closed tickets
        for _ in range(int(NUM_TICKETS * (1 - OPEN_TICKET_RATIO))):
            ticket = TicketFactory()
            ticket.completed = True
            ticket.completed_date = random_recent_date_time()
            ticket.save()

        # Create random number of comments in range for all tickets
        for _ in range(NUM_TICKETS):
            for _ in range(random.randrange(1, MAX_COMMENTS_PER_TICKET)):
                CommentFactory()

        # # Create random number TicketEvents in range for all Tickets
        for _ in range(NUM_TICKETS):
            for _ in range(random.randrange(1, MAX_EVENTS_PER_TICKET)):
                event = TicketEventFactory()
                TicketEvent.objects.create(
                    type=event.type,
                    ticket=event.ticket,
                    author=event.author,
                    seen=False
                )

        employees = User.objects.filter(is_staff=True).values_list('id', flat=True)
        for ticket in Ticket.objects.all():
            ticket.followers.set(list(employees))

        manual_update_analytics()

        settings.RANDOM_TIMES = False
