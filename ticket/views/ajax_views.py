from django.contrib.auth.models import User
from django.core import serializers
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.views import View

from ticket.models import Ticket, TicketEvent
from ticket.services import TicketEventService


class SearchUsersView(View):
    def get(self, request, *args, **kwargs):
        name = request.GET.get('name')
        ticket_id = request.GET.get('ticket_id')

        if ticket_id:
            all_users = User.objects.filter(first_name__icontains=name)
            ticket = Ticket.objects.get(id=ticket_id)
            query = all_users.difference(ticket.followers.all())
        else:
            query = User.objects.filter(first_name__icontains=name, is_staff=False)

        json_results = serializers.serialize('json', query)
        data = {
            'results': json_results
        }
        return JsonResponse(data)


class AddUserView(View):
    def get(self, request):
        user_id = int(request.GET.get('user_id'))
        ticket_id = int(request.GET.get('ticket_id'))
        user = User.objects.get(id=user_id)
        ticket = Ticket.objects.get(id=ticket_id)
        ticket.followers.add(user)
        ticket.save()
        notifications = TicketEventService(ticket=ticket, current_user=request.user)
        notifications.create_add_user_event(added_user=user)
        return JsonResponse({"user_name": user.first_name})


class PauseTicketReminders(View):
    def get(self, request):
        ticket = Ticket.objects.get(id=int(request.GET.get('ticket_id')))
        pause_until = parse_datetime(request.GET.get('paused_until'))
        ticket.paused_until = pause_until
        ticket.save()
        return JsonResponse({"status": True})


class Statistics(View):
    def get(self, request):
        stats_per_user = Ticket.objects.statistics_per_user()
        data = {}
        for stats in stats_per_user:
            data[stats["modified_by__first_name"]] = {
                'summe_ticket_geschlossen': stats['total_tickets_closed'],
                'durchschnittliche_bearbeitungszeit': str(stats['average_processing_time']),
                'max_bearbeitungszeit': str(stats['max_processing_time']),
                'min_bearbeitungszeit': str(stats['min_processing_time'])

            }
        return JsonResponse(data, json_dumps_params={'indent': 4})


class AutoAssignView(View):
    def get(self, request):
        average_time_to_auto_assign = TicketEvent.objects.average_time_to_auto_assign()
        average_time_during_business_hours = TicketEvent.objects.average_time_to_auto_assign_during_business_hours()
        #time_to_auto_assign = [x for x in TicketEvent.objects.time_to_auto_assign().values()]
        data = {
            'average_time_to_auto_assign': average_time_to_auto_assign['time_to_auto_assign__avg'].__str__(),
            'average_time_to_auto_assign_mon_fri_9_16': average_time_during_business_hours['time_to_auto_assign__avg'].__str__()
            # 'time_to_auto_assign': {
            #     "query": TicketEvent.objects.time_to_auto_assign().query.__str__(),
            #     "result": time_to_auto_assign
        }
        return JsonResponse(data, json_dumps_params={'indent': 4})
