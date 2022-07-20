from django.views.generic import ListView

from ticket.models import Ticket


class SearchTicketsView(ListView):
    model = Ticket
    template_name = 'ticket/ticket_list.html'
    context_object_name = 'tickets'

    def get_queryset(self, *args, **kwargs):
        query = self.request.GET.get('query')
        user = self.request.user

        if user.is_staff:
            return Ticket.objects.search_tickets(query=query)
        else:
            return Ticket.objects.search_tickets(query=query, created_or_followed_by=user)





