from datetime import timedelta

from django.db import models
from django.db.models import Count, Q, F, Avg, Max, Min
from django.utils import timezone


class TicketQueryset(models.QuerySet):

    def get_common_problem_sources_for(self, user):
        return self.filter(created_by=user). \
            values('problem_source__breadcrumb', 'problem_source__slug'). \
            annotate(total=Count('problem_source__breadcrumb')). \
            order_by('-total')

    def open_and_created_by(self, user):
        return self.filter(created_by=user, completed=False)

    def closed_and_created_by(self, user):
        return self.filter(created_by=user, completed=True)

    def created_by(self, user):
        return self.filter(created_by=user)

    def open_and_assigned_to(self, user):
        return self.filter(assigned_to=user, completed=False)

    def closed_and_assigned_to(self, user):
        return self.filter(assigned_to=user, completed=True)

    def assigned_to(self, user):
        return self.filter(assigned_to=user)

    def all_open(self):
        return self.filter(completed=False)

    def all_closed(self):
        return self.filter(completed=True)

    def all_tickets_containing(self, query):
        query_title = Q(title__icontains=query)
        query_ticket_author = Q(created_by__first_name__icontains=query)
        query_problem_source = Q(problem_source__name__icontains=query)
        query_ticket_id = Q(id__icontains=query)

        return self.filter(query_title | query_ticket_author | query_problem_source | query_ticket_id) \
               | self.search_notes(query)

    def all_user_tickets_containing(self, query, user):
        created_by_user = Q(created_by=user)
        followed_by_user = Q(followers__in=[user])
        users_tickets = (created_by_user | followed_by_user)

        return self.all_tickets_containing(query) & self.filter(users_tickets)

    def search_tickets(self, query, created_or_followed_by=None):
        if created_or_followed_by:
            queryset = self.all_user_tickets_containing(query, created_or_followed_by)
        else:
            queryset = self.all_tickets_containing(query)

        return queryset

    def search_notes(self, query):
        ticket_ids_containing_query = self.raw(
            f"SELECT id FROM ticket_ticket WHERE lower(note) LIKE lower('%{query}%');", None
        )
        return self.filter(id__in=[x.id for x in list(ticket_ids_containing_query)])

    def group_by_created_date(self):
        return self.all() \
            .values('created_date__date') \
            .annotate(total_created=Count('created_date__date'), date=F('created_date__date'))\
            .order_by('date')

    def group_by_completed_date(self):
        return self.all() \
            .values('completed_date__date') \
            .annotate(total_closed=Count('completed_date__date'), date=F('completed_date__date'))\
            .order_by('date')

    def open_closed_per_day(self):
        open = self.group_by_created_date()
        closed = self.group_by_completed_date()
        results = dict()
        for i in open:
            date = i["date"]
            results[date] = {
                "date": date.strftime('%d.%m.%Y'),
                "total_created": i["total_created"],
                "total_closed": 0
            }
        for i in closed:
            date = i["date"]
            if date in results.keys():
                results[date]["total_closed"] = i["total_closed"]
        return results

    def group_by_problem_source(self):
        return self.all() \
            .values('problem_source__tree_id') \
            .annotate(total=Count('problem_source__tree_id')) \
            .order_by('total')

    def not_paused(self):
        return self.filter(paused_until__lt=timezone.now()) | self.filter(paused_until__isnull=True)

    def open_and_inactive(self, hours=4):
        time_threshold = timezone.now() - timedelta(hours=hours)
        return self.filter(completed=False, last_modified__lt=time_threshold) & self.not_paused()

    def open_and_inactive_assigned_to(self, user):
        return self.open_and_inactive() & self.open_and_assigned_to(user)

    def tickets_closed_per_user(self):
        return self.filter(completed=True) \
            .values('modified_by__first_name') \
            .annotate(total=Count('modified_by__first_name')) \
            .order_by('total')

    def processing_time(self):
        return self.filter(completed=True) \
            .annotate(processing_time=F('last_modified') - F('created_date')) \
            .order_by('-processing_time')

    def average_processing_time(self):
        return self.processing_time().aggregate(Avg('processing_time'))

    def average_processing_time_per_user(self):
        return self.filter(completed=True) \
            .values('modified_by__first_name') \
            .annotate(average_processing_time=Avg(F('last_modified') - F('created_date'))) \
            .order_by('-average_processing_time')

    def statistics_per_user(self):
        return self.filter(completed=True) \
            .values('modified_by__first_name') \
            .annotate(total_tickets_closed=Count('modified_by__first_name')) \
            .annotate(average_processing_time=Avg(F('last_modified') - F('created_date'))) \
            .annotate(max_processing_time=Max(F('last_modified') - F('created_date'))) \
            .annotate(min_processing_time=Min(F('last_modified') - F('created_date'))) \
            .order_by('-total_tickets_closed')


class TicketManager(models.Manager):
    related = 'created_by', 'assigned_to', 'modified_by', 'problem_source'
    order_by = 'completed', '-priority', '-created_date'

    def get_queryset(self):
        return TicketQueryset(self.model, using=self._db)

    def get_common_problem_sources_for(self, user):
        return self.get_queryset().get_common_problem_sources_for(user)

    def open_and_created_by(self, user):
        return self.get_queryset().open_and_created_by(user) \
            .order_by(*self.order_by).select_related(*self.related)

    def closed_and_created_by(self, user):
        return self.get_queryset().closed_and_created_by(user) \
            .order_by(*self.order_by).select_related(*self.related)

    def created_by(self, user):
        return self.get_queryset().created_by(user) \
            .order_by(*self.order_by).select_related(*self.related)

    def open_and_assigned_to(self, user):
        return self.get_queryset().open_and_assigned_to(user) \
            .order_by(*self.order_by).select_related(*self.related)

    def closed_and_assigned_to(self, user):
        return self.get_queryset().closed_and_assigned_to(user) \
            .order_by(*self.order_by).select_related(*self.related)

    def assigned_to(self, user):
        return self.get_queryset().assigned_to(user) \
            .order_by(*self.order_by).select_related(*self.related)

    def all_open(self):
        return self.get_queryset().all_open() \
            .order_by(*self.order_by).select_related(*self.related)

    def all_closed(self):
        return self.get_queryset().all_closed() \
            .order_by(*self.order_by).select_related(*self.related)

    def search_tickets(self, query, created_or_followed_by=None):
        return self.get_queryset().search_tickets(query, created_or_followed_by) \
            .select_related(*self.related) \
            .distinct() \
            .order_by('-created_date')

    def search_notes(self, query):
        return self.get_queryset().search_notes(query) \
            .order_by(*self.order_by).select_related(*self.related)

    def group_by_created_date(self):
        return self.get_queryset().group_by_created_date()

    def group_by_completed_date(self):
        return self.get_queryset().group_by_completed_date()

    def open_closed_per_day(self):
        return self.get_queryset().open_closed_per_day()

    def group_by_problem_source(self):
        return self.get_queryset().group_by_problem_source()

    def open_and_inactive_users(self):
        return self.get_queryset().open_and_inactive() \
            .values('created_by__microsoftprofile') \
            .select_related('created_by__microsoftprofile')

    def open_and_inactive_assigned_to(self, user):
        return self.get_queryset().open_and_inactive_assigned_to(user) \
            .order_by(*self.order_by).select_related(*self.related)

    def tickets_closed_per_user(self):
        return self.get_queryset().tickets_closed_per_user()

    def processing_time(self):
        return self.get_queryset().processing_time()

    def average_processing_time(self):
        return self.get_queryset().average_processing_time()

    def average_processing_time_per_user(self):
        return self.get_queryset().average_processing_time_per_user()

    def statistics_per_user(self):
        return self.get_queryset().statistics_per_user()
