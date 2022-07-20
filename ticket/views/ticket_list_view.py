from django.db.models import QuerySet
from django.views.generic import ListView

from ticket.models import Ticket


class TicketListView(ListView):
    model = Ticket
    template_name = 'ticket/ticket_list.html'
    context_object_name = "tickets"
    paginate_by = 25

    def get_queryset(self):
        status = self.kwargs.get('status')
        type = self.kwargs.get('type')
        user = self.request.user

        if type == "mine":
            if status == "open":
                tickets = Ticket.objects.open_and_created_by(user)
            elif status == "closed":
                tickets = Ticket.objects.closed_and_created_by(user)
            else:
                tickets = Ticket.objects.created_by(user)
        elif type == "assigned_to_me":
            if status == "open":
                tickets = Ticket.objects.open_and_assigned_to(user)
            elif status == "closed":
                tickets = Ticket.objects.closed_and_assigned_to(user)
            else:
                tickets = Ticket.objects.assigned_to(user)
        elif type == "all" and user.is_staff:
            if status == "open":
                tickets = Ticket.objects.all_open()
            elif status == "closed":
                tickets = Ticket.objects.all_closed()
            else:
                tickets = Ticket.objects.all()\
                    .select_related('created_by', 'assigned_to', 'modified_by', 'problem_source')
        else:
            tickets = QuerySet()

        return tickets.order_by('completed', '-priority', '-created_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ticket_status'] = self.kwargs.get('status')
        context['ticket_type'] = self.kwargs.get('type')
        return context
