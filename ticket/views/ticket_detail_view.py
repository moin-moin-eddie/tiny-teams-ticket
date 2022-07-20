import random

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.views import View

from ticket.forms import SearchUsersForm, CreateTicketForm, PauseTicketForm
from ticket.models import Attachment, Ticket, Comment, ProblemSource
from ticket.services import TicketEventService
from ticket.tasks import manual_update_analytics
from ticket.thanks import thanks_comments


class TicketDetailView(View):
    def get(self, request, *args, **kwargs):
        ticket = self.get_ticket()
        user = request.user
        followers = ticket.followers.all()
        if user in followers or user == ticket.created_by or user.is_staff:
            attachments = Attachment.objects.filter(ticket=ticket)
            notifications = TicketEventService(ticket=ticket, current_user=user)
            new_problem_source = request.GET.get('problem_source')
            thanks = request.GET.get('thanks')

            if thanks:
                comment = Comment.objects.create(
                    ticket=ticket,
                    text=random.choice(thanks_comments),
                )
                notifications.create_comment_events(comment=comment, reopen=False)

            context = {
                "attachments": attachments,
                "search_user_form": SearchUsersForm(),
            }

            if 'edit' in request.get_full_path().split('/'):
                context['edit'] = True
                context['ticket_form'] = CreateTicketForm(initial={'note': ticket.note})

            if user.is_staff:
                context['employees'] = User.objects.filter(is_staff=True)
                context['problem_sources'] = ProblemSource.objects.all()
                context['pause_ticket_form'] = PauseTicketForm()
                if new_problem_source:
                    ticket.problem_source_id = new_problem_source
                    ticket.save()
                if not ticket.assigned_to:
                    followers_to_remove = [
                        f for f in followers if f.is_staff and f != user
                    ]
                    ticket.followers.remove(*followers_to_remove)
                    ticket.assigned_to = user
                    ticket.save()
                    notifications.create_assign_events(is_automatic=True)

            notifications.mark_events_as_seen()
            context["timeline_events"] = notifications.get_unique_events()
            context["ticket"] = ticket
            context["followers"] = followers

            return render(
                request=request,
                template_name='ticket/ticket_detail.html',
                context=context
            )
        else:
            html_template = loader.get_template('403.html')
            return HttpResponse(html_template.render({}, request))

    def post(self, request, *args, **kwargs):
        # Necessary data for handling POST requests
        ticket = self.get_ticket()
        current_user = request.user
        post = request.POST

        # Instantiate TicketEventService for notification creation
        notifications = TicketEventService(ticket=ticket, current_user=current_user)

        # Get POST data for processing
        new_comment = post.get('new_comment')
        internal_note = post.get('internal_note')
        new_note = post.get('note')
        new_attachments = request.FILES.getlist('files')
        new_comment_reply = post.get('new_reply')
        close = post.get('close')
        open = post.get('open')
        title = post.get('title')
        assign_to = post.get('assign_to')
        priority = post.get('priority')
        pause_until = post.get('pause_until')
        unpause = post.get('unpause')

        if new_comment:
            comment = Comment.objects.create(
                ticket=ticket,
                text=new_comment,
            )
            notifications.create_comment_events(comment=comment)

        if new_comment_reply:
            comment_id = post.get('comment_id')
            reply = Comment.objects.create(
                ticket=ticket,
                text=new_comment_reply,
                parent=Comment.objects.get(id=comment_id)
            )
            notifications.create_reply_events(reply=reply)

        if new_note:
            if ticket.note != new_note:
                ticket.note = new_note
                ticket.save()
                notifications.create_edit_events()

        if title:
            if title != ticket.title:
                ticket.title = title
                ticket.save()

        if new_attachments:
            for attachment in new_attachments:
                Attachment.objects.create(
                    name=attachment,
                    file=attachment,
                    ticket=ticket
                )
            notifications.create_attachment_events()

        if close:
            if not ticket.completed:
                close_comment = Comment.objects.create(
                    ticket=ticket,
                    text=internal_note
                ) if internal_note else None
                ticket.completed = True
                ticket.save()
                notifications.create_close_events(comment=close_comment)

        if open:
            if ticket.completed:
                ticket.completed = False
                ticket.save()
                notifications.create_open_events()

        if assign_to:
            user_to_assign = User.objects.get(id=assign_to)
            followers = ticket.followers.all()
            followers_to_remove = [
                f for f in followers if f.is_staff
            ]
            ticket.followers.remove(*followers_to_remove)
            ticket.followers.add(user_to_assign)
            if not ticket.assigned_to == user_to_assign:
                comment = Comment.objects.create(
                    ticket=ticket,
                    text=internal_note
                ) if internal_note else None
                ticket.assigned_to = user_to_assign
                ticket.save()
                notifications.create_assign_events(comment=comment)

        if priority:
            ticket.priority = priority
            ticket.save()
            # Notification for priority change???

        if pause_until:
            ticket.paused_until = pause_until
            ticket.save()

        if unpause:
            ticket.paused_until = None
            ticket.save()

        manual_update_analytics()

        return redirect("ticket_detail", id=ticket.id)

    def count_open_tickets_with_same_problem_source(self):
        ticket = self.get_ticket()
        return Ticket.objects.filter(problem_source=ticket.problem_source, completed=False).exclude(
            id=ticket.id).count()

    def get_ticket(self):
        return Ticket.objects.filter(id=self.kwargs.get('id')).select_related(
            "created_by", "assigned_to", "modified_by", "problem_source"
        )[0]
