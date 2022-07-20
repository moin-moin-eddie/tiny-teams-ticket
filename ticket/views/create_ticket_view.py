from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views import View

from ticket.forms import CreateTicketForm
from ticket.models import ProblemSource, Ticket, Attachment
from ticket.services import TicketEventService
from ticket.tasks import manual_update_analytics


class CreateTicketView(View):

    def get(self, request, *args, **kwargs):
        user = request.user
        problem_source = self.get_problem_source()

        open_tickets_same_category = Ticket.objects.filter(
            created_by=user, completed=False, problem_source=problem_source
        )

        context = {
            "category": problem_source.create_category_breadcrumb(),
            "ticket_form": CreateTicketForm(),
            "open_tickets_same_category": open_tickets_same_category
        }

        return render(
            request=request,
            template_name='ticket/create_ticket.html',
            context=context)

    def post(self, request, *args, **kwargs):
        form = CreateTicketForm(request.POST)
        if form.is_valid():
            new_ticket = Ticket.objects.create(
                title=form.data['title'],
                problem_source=self.get_problem_source(),
                note=form.data['note']
            )
            new_ticket.followers.add(*User.objects.filter(is_staff=True))
            new_ticket.followers.add(request.user)
            new_ticket.save()
            TicketEventService(current_user=request.user, ticket=new_ticket).create_new_ticket_events()
            manual_update_analytics()
            self.handle_attachments(attachments=request.FILES.getlist('files'), ticket=new_ticket)
            return redirect('ticket_detail', id=new_ticket.id)
        else:
            user = request.user
            problem_source = self.get_problem_source()

            open_tickets_same_category = Ticket.objects.filter(
                created_by=user, completed=False, problem_source=problem_source
            )

            context = {
                "category": problem_source.create_category_breadcrumb(),
                "ticket_form": form,
                "open_tickets_same_category": open_tickets_same_category
            }
            return render(
                request=request,
                template_name='ticket/create_ticket.html',
                context=context
            )

    def get_slug(self):
        return self.kwargs.get('slug')

    def get_problem_source(self):
        return ProblemSource.objects.get(slug=self.get_slug())

    def handle_attachments(self, attachments, ticket):
        if attachments:
            for attachment in attachments:
                new_attachment = Attachment(
                    name=attachment,
                    file=attachment,
                    ticket=ticket
                )
                new_attachment.save()

    def create_category(self):
        return self.get_problem_source().create_category_breadcrumb()

    def DEV_get_initial_text(self):
        problem = self.get_slug()
        initial = {
            'note': f"""<h3><u>{problem} ist einfach kaputt...</u></h3>
                              <h4>Subheading</h4>
                              <p>{problem} ärgert mich und zeigt tausende Fehlermeldungen. Bitte die folgende aufträge durchschleußen:  
                              </p>
                              <ul>
                                <li>321654987</li>
                                <li>654987321</li>
                              </ul>
                              <p>Dankeschön,</p>
                              <p>Max Mustermann</p>"""
        }
        return initial
