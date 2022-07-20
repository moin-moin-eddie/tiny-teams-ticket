import ast
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import ListView

from authentication.models import MicrosoftProfile
from ticket.forms import SearchUsersForm
from ticket.models import TicketEvent, Ticket, ProblemSource, Analytics
from ticket.services import TicketEventService


class IndexView(ListView):
    model = TicketEvent
    context_object_name = 'timeline_events'
    paginate_by = 5  # Number of days to show activity for
    template_name = 'home.html'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            start_time = timezone.now()
            end_time = start_time - timedelta(days=10)
            user_events = TicketEvent.objects \
                .filter(user_to_notify__isnull=True, timestamp__lt=start_time, timestamp__gt=end_time) \
                .select_related("author", "ticket__problem_source", "target_user", "comment")
        else:
            user_events = TicketEvent.objects \
                .filter(user_to_notify=self.request.user) \
                .select_related("author", "ticket__problem_source", "target_user", "comment")
        return TicketEventService(current_user=user).group_timeline_events_by_date(user_events, add_text=True)

    def get_paginate_by(self, queryset):
        return 1 if self.request.user.is_staff else 5

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        tickets = Ticket.objects.select_related('problem_source', 'created_by').all()
        user = self.request.user

        if user.is_staff:
            open_inactive_tickets = Ticket.objects.open_and_inactive_assigned_to(user)
            context['tickets'] = open_inactive_tickets
            analytics = Analytics.objects.all()
            timeline_events = context["timeline_events"]
            page_date = context["timeline_events"][0][0].date if timeline_events else date.today()
            next_page_date = page_date + timedelta(days=1)

            # FIXME: Refactor the fuck out of this mess
            pie_chart = analytics.get(name='Tickets pro Problemquelle')
            bar_chart = analytics.get(name='Tickets pro Tag')
            bar_data = ast.literal_eval(bar_chart.data)
            context['pie_labels'] = pie_chart.labels
            context['pie_data'] = pie_chart.data
            context['bar_labels'] = bar_chart.labels
            context['bar_open_data'] = bar_data[0]
            context['bar_closed_data'] = bar_data[1]
            context['tickets_opened_today'] = tickets.filter(
                created_date__gt=page_date,
                created_date__lt=next_page_date
            ).count()
            context['tickets_closed_today'] = tickets.filter(
                completed_date__gt=page_date,
                completed_date__lt=next_page_date,
                completed=True
            ).count()
            context['all_open_ticket_count'] = tickets.filter(completed=False).count()
            context['all_closed_ticket_count'] = tickets.filter(completed=True).count()
            context['all_open_ticket_with_high_prio_count'] = tickets.filter(priority=2, completed=False).count()
            context['search_user_form'] = SearchUsersForm()
        else:
            context['open_ticket_count'] = tickets.filter(created_by=user, completed=False).count()
            context['closed_ticket_count'] = tickets.filter(created_by=user, completed=True).count()
        return context

    def get(self, request, *args, **kwargs):
        dark_mode_toggle = request.GET.get("dark_mode_toggle")
        mark_as_seen = request.GET.get("mark_as_seen")
        user = request.user

        if dark_mode_toggle:
            ref = request.META["HTTP_REFERER"]
            ms_profile, created = MicrosoftProfile.objects.update_or_create(user=user)
            dark_mode_active = ms_profile.dark_mode_active
            ms_profile.dark_mode_active = not dark_mode_active
            ms_profile.save()
            return redirect(ref) if ref else redirect('/')

        if mark_as_seen:
            ref = request.META["HTTP_REFERER"]
            TicketEvent.objects.filter(user_to_notify=user).update(seen=True)
            return redirect(ref) if ref else redirect('/')

        return super(IndexView, self).get(request, *args, **kwargs)

    def post(self, request):
        feature_request = request.POST.get('feature_request')
        problem_source = ProblemSource.objects.get(slug='feature-request')
        new_ticket = Ticket.objects.create(note=feature_request, problem_source=problem_source)
        new_ticket.followers.add(*User.objects.filter(is_staff=True))
        new_ticket.followers.add(request.user)
        new_ticket.save()
        TicketEventService(current_user=request.user, ticket=new_ticket).create_new_ticket_events()
        return redirect('home')

    def set_pagination(self):
        return 1 if self.request.user.is_staff else 5
