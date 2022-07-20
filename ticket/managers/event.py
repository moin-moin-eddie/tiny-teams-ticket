from itertools import chain, zip_longest

from django.db import models
from django.db.models import F, Avg, Subquery, Count


class TicketEventQueryset(models.QuerySet):
    """
    A query manager for ticket events, also referred to as notifications from
    time to time.  Ticket Events are used as notifications, however, there are
    user independent ticket events as well.  This is the default_set for most
    queries that aim to calculate interaction times with tickets themselves.
    """

    def default_set(self):
        return self.filter(user_to_notify=None)

    def event_type(self, type):
        return self.default_set().filter(type=type)

    def created(self):
        return self.event_type('new')

    def assigned(self):
        return self.event_type("assigned")

    def is_automatic(self):
        return self.default_set().filter(is_automatic=True)

    def auto_assigned(self):
        return self.is_automatic() & self.assigned()

    def time_to_auto_assign(self):
        return self.auto_assigned() \
            .values('ticket', 'ticket__created_date', 'timestamp') \
            .annotate(time_to_auto_assign=F('timestamp') - F('ticket__created_date'))

    def average_time_to_auto_assign(self):
        return self.time_to_auto_assign().aggregate(Avg('time_to_auto_assign'))

    def created_during_business_hours(self):
        return self.created().filter(
            timestamp__hour__gt=9,
            timestamp__hour__lt=16,
            timestamp__week_day__lt=5,
            timestamp__week_day__gte=0
        )

    def average_time_to_auto_assign_during_business_hours(self):
        ids = self.created_during_business_hours().values('ticket__id')
        return self.time_to_auto_assign().filter(ticket__in=ids).aggregate(Avg('time_to_auto_assign'))

    def ticket(self, type):
        return self.event_type(type).values('ticket')

    def creation_time(self):
        return self.ticket('new').annotate(creation_time=F('timestamp'))

    def auto_assign_time(self):
        return self.ticket('assigned').annotate(auto_assign_time=F('timestamp'))

    def num_comments(self):
        return self.ticket('comment').annotate(num_comments=Count('ticket'))

    def num_followers_added(self):
        return self.ticket('access_allowed').annotate(num_followers_added=Count('ticket'))

    def all_ticket_stats(self):
        queries = [
            self.creation_time(),
            self.auto_assign_time(),
            self.num_comments(),
            self.num_followers_added()
        ]
        result = [{**q1, **q2} for q1, q2 in zip_longest(queries[0], queries[1], fillvalue={})]
        for i in range(2,len(queries)):
            print(queries[i])
            result = [{**q1, **q2} for q1, q2 in zip_longest(result, queries[i], fillvalue={})]

        return result


class TicketEventManager(models.Manager):

    def get_queryset(self):
        return TicketEventQueryset(self.model, using=self._db)

    def assigned(self):
        return self.get_queryset().assigned()

    def is_automatic(self):
        return self.get_queryset().is_automatic()

    def auto_assigned(self):
        return self.get_queryset().auto_assigned()

    def time_to_auto_assign(self):
        return self.get_queryset().time_to_auto_assign()

    def average_time_to_auto_assign(self):
        return self.get_queryset().average_time_to_auto_assign()

    def created(self):
        return self.get_queryset().created()

    def created_during_business_hours(self):
        return self.get_queryset().created_during_business_hours()

    def average_time_to_auto_assign_during_business_hours(self):
        return self.get_queryset().average_time_to_auto_assign_during_business_hours()

    def creation_time(self):
        return self.get_queryset().creation_time()

    def num_comments(self):
        return self.get_queryset().num_comments()

    def all_ticket_stats(self):
        return self.get_queryset().all_ticket_stats()
