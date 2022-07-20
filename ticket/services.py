import itertools
import operator
import urllib

from background_task import background
from django.conf import settings
from django.core.mail import send_mail

from authentication.graph_api.base import GraphAPI
from authentication.models import MicrosoftProfile
from core.settings.common import EMAIL_HOST_USER, BASE_URL, AZURE_APP_ID
from ticket.models import TicketEvent

graph_api = GraphAPI()


@background(schedule=1)
def send_background_notification(ms_id, payload):
    print(f"BACKGROUND NOTIFICATION: {payload}")
    result = graph_api.send_activity_feed_notification(
        user_id=ms_id,
        payload=payload
    )
    print(result)
    if result is not None:
        print("TOKEN INVALID, RETRYING")
        graph_api.refresh_token()
        result = graph_api.send_activity_feed_notification(
            user_id=ms_id,
            payload=payload
        )
        print("RESULT:", result)


@background(schedule=1)
def send_email_notification(subject, message, send_to):
    return send_mail(
        subject=subject,
        message=message,
        from_email=EMAIL_HOST_USER,
        recipient_list=send_to,
        fail_silently=True
    )


class TicketEventService:
    event_types = TicketEvent.EventType

    def __init__(self, ticket=None, current_user=None):
        self.ticket = ticket
        self.current_user = current_user
        if ticket:
            self.followers = ticket.followers.all()

    def mark_events_as_seen(self):
        TicketEvent.objects.filter(ticket=self.ticket, user_to_notify=self.current_user).update(seen=True)

    def create_ticket_events(self,
                             type,
                             target_user=None,
                             comment=None,
                             is_internal=False,
                             skip_teams=False,
                             is_automatic=False,
                             reopen=True):

        # Create event just for the ticket, independent of user, to be shown on detail.
        TicketEvent.objects.create(
            type=type,
            ticket=self.ticket,
            target_user=target_user,
            comment=comment,
            is_internal=is_internal,
            is_automatic=is_automatic
        )

        # Automatically reopen the ticket if closed and event isnt reopen or close
        if self.ticket.completed and type not in [self.event_types.REOPEN, self.event_types.CLOSE] and reopen:
            TicketEvent.objects.create(
                type=self.event_types.REOPEN,
                ticket=self.ticket,
                is_automatic=True
            )
            self.ticket.completed = False
            self.ticket.save()

        # Create internal notifications/timeline events for all followers.
        for user in self.followers:
            seen = False if user != self.current_user else True
            notification = TicketEvent.objects.create(
                type=type,
                ticket=self.ticket,
                target_user=target_user,
                user_to_notify=user,
                seen=seen,
                comment=comment,
                is_internal=is_internal
            )

            # FIXME: Review for generalization

            try:
                ms_profile = MicrosoftProfile.objects.get(user=user)
                if not seen and ms_profile.should_receive_this_notification(type=type) and not skip_teams:
                    send_background_notification(
                        ms_id=ms_profile.ms_id,
                        payload=self.create_notification_payload(notification=notification)
                    )
                    print(f"SENDING {type.upper()} NOTIFICATION TO: {user.first_name}")
                elif not seen \
                        and ms_profile.should_receive_this_notification(type=type) \
                        and not skip_teams:
                    print(f"NOT IN DOMAIN, SENDING EMAIL NOTIFICATION TO: {user.first_name}")
                    self.create_and_send_email_notification(notification=notification)
                else:
                    print(f"SKIPPING SENDING {type.upper()} NOTIFICATION TO: {user.first_name}")
                    pass
            except:
                if not seen and not skip_teams:
                    print(f"MSID UNAVAILABLE, SENDING EMAIL NOTIFICATION TO: {user.first_name}")
                    self.create_and_send_email_notification(notification=notification)
                pass

    def create_and_send_email_notification(self, notification):
        if not settings.DEBUG:
            topic_text = self.ticket.title if self.ticket.title else self.ticket.category
            subject = f"Ticket: TicketID - {self.ticket.id} - {topic_text}"
            author = notification.author.first_name
            if notification.target_user:
                target_user = notification.target_user.first_name
            else:
                target_user = 'jemand'

            if notification.is_new():
                event_text = f"Ein neues Ticket wurde von {author} erstellt"
            elif notification.is_edit():
                event_text = f"Das Ticket wurde von {author} bearbeitet"
            elif notification.is_comment():
                event_text = f"Das Ticket hat einen neuen Kommentar von {author}"
            elif notification.is_reply():
                event_text = f"{author} hat auf einen Kommentar geantwortet"
            elif notification.is_close():
                event_text = f"{author} hat das Ticket geschlossen"
            elif notification.is_reopen():
                event_text = f"{author} hat das Ticket wieder geöffnet"
            elif notification.is_new_attachment():
                event_text = f"{author} hat eine neue Datei hochgeladen"
            elif notification.is_assigned():
                event_text = f"{author} hat das Ticket an {target_user} zugewiesen"
            elif notification.is_access_allowed():
                event_text = f"{author} hat {target_user} zum Ticket hinzugefügt"
            else:
                event_text = "Das Ticket hat ein neues Ereignis"

            if notification.text and not notification.is_internal:
                message = f"""{event_text}:
                
                "{notification.text}"
                
                Sie können das Ticket hier anschauen: {BASE_URL}/{self.ticket.id}/detail/
        
                Bitte nicht auf diese Email antworten.
                """
            else:
                message = f"""{event_text}.
    
                Sie können das Ticket hier anschauen: {BASE_URL}/{self.ticket.id}/detail/
    
                Bitte nicht auf diese Email antworten.
                """

            recipient_list = [notification.user_to_notify.email]

            return send_email_notification(
                subject=subject,
                message='\n'.join([m.lstrip() for m in message.split('\n')]),
                send_to=recipient_list
            )

    def create_notification_payload(self, notification: TicketEvent):
        template_target = notification.target_user if notification.target_user else notification.author

        topic_text = self.ticket.title if self.ticket.title else self.ticket.category

        payload = {
            "topic": {
                "source": "text",
                "value": topic_text,
                "webUrl": self.generate_deep_link()
            },
            "activityType": notification.type,
            "previewText": {
                "content": notification.text if not notification.is_internal else ""
            },
            "templateParameters": [
                {
                    "name": "user",
                    "value": template_target.first_name
                }
            ]
        }

        return payload

    def generate_deep_link(self):
        # TODO: CHANGE THIS!
        base_url = "https://teams.microsoft.com/l/entity"
        app_id = AZURE_APP_ID
        entity_id = "domain_ticket"
        web_url = f"webUrl={BASE_URL}/ticket/{self.ticket.id}/detail/"
        label = f"label=Ticket{self.ticket.id}"
        context = urllib.parse.quote("""&context={"subEntityId": """ + str(self.ticket.id) + "}")
        deep_link = f"{base_url}/{app_id}/{entity_id}?{web_url}&{label}&{context}"

        return deep_link

    def create_new_ticket_events(self, skip_teams=False):
        self.create_ticket_events(type=TicketEvent.EventType.NEW, skip_teams=skip_teams)

    def create_comment_events(self, comment, skip_teams=False, reopen=True):
        self.create_ticket_events(
            type=TicketEvent.EventType.COMMENT, comment=comment, skip_teams=skip_teams, reopen=reopen
        )

    def create_reply_events(self, reply, skip_teams=False):
        self.create_ticket_events(type=TicketEvent.EventType.REPLY, comment=reply, skip_teams=skip_teams)

    def create_edit_events(self, skip_teams=True):
        self.create_ticket_events(type=TicketEvent.EventType.EDIT, skip_teams=skip_teams)

    def create_attachment_events(self, skip_teams=True):
        self.create_ticket_events(type=TicketEvent.EventType.NEW_ATTACHMENT, skip_teams=skip_teams)

    def create_close_events(self, comment=None, skip_teams=True):
        self.create_ticket_events(
            type=TicketEvent.EventType.CLOSE, comment=comment, is_internal=True, skip_teams=skip_teams
        )

    def create_open_events(self, skip_teams=True, is_automatic=False):
        self.create_ticket_events(type=TicketEvent.EventType.REOPEN, skip_teams=skip_teams, is_automatic=is_automatic)

    def create_assign_events(self, comment=None, skip_teams=False, is_automatic=False):
        self.create_ticket_events(
            type=TicketEvent.EventType.ASSIGNED,
            target_user=self.ticket.assigned_to,
            comment=comment,
            is_internal=True,
            skip_teams=skip_teams,
            is_automatic=is_automatic
        )

    def create_add_user_event(self, added_user, skip_teams=False):
        self.create_ticket_events(
            type=TicketEvent.EventType.ACCESS_ALLOWED, target_user=added_user, skip_teams=skip_teams
        )

    def get_unique_events(self):
        unfiltered_timeline_events = TicketEvent.objects\
            .filter(ticket=self.ticket, user_to_notify__isnull=True)\
            .select_related("author", "ticket", "target_user", "comment", "comment__parent")

        for event in unfiltered_timeline_events:
            event.event_text = self.get_event_text(
                event=event, author=event.author, target_user=event.target_user
            )
        return self.group_timeline_events_by_date(unfiltered_timeline_events)

    def group_timeline_events_by_date(self, timeline_events, add_text=False):
        if add_text:
            for event in timeline_events:
                event.event_text = self.get_event_text(
                    event=event, author=event.author, target_user=event.target_user
                )
        group_attribute = operator.attrgetter('date')
        grouped_list = [list(g) for k, g in
                        itertools.groupby(sorted(timeline_events, key=group_attribute, reverse=True), group_attribute)]
        for group in grouped_list:
            group.sort(key=lambda x: x.time, reverse=True)
        return grouped_list

    def get_event_text(self, event, author, target_user):
        author_name = author.first_name if not event.is_automatic else "Das System"
        target_user_name = target_user.first_name if target_user else None

        current_user_is_author = True if self.current_user == author else False
        current_user_is_target = True if self.current_user == target_user else False
        author_is_target = True if author_name == target_user_name else False

        beginning_text = "Du hast" if (current_user_is_author and not event.is_automatic) else f"{author_name} hat"

        if event.is_new():
            return f"{beginning_text} das ticket erstellt"
        elif event.is_edit():
            return f"{beginning_text} das Ticket bearbeitet"
        elif event.is_comment():
            return f"{beginning_text} kommentiert"
        elif event.is_reply():
            return f"{beginning_text} auf einen Kommentar geantwortet"
        elif event.is_close():
            return f"{beginning_text} das Ticket geschlossen"
        elif event.is_reopen():
            return f"{beginning_text} das Ticket wieder geöffnet"
        elif event.is_new_attachment():
            return f"{beginning_text} eine neue Datei hochgeladen"
        elif event.is_assigned():
            if author_is_target:
                return f"{beginning_text} das Ticket übernommen"
            elif current_user_is_target:
                return f"{author_name} hat dir das Ticket zugewiesen"
            elif current_user_is_author:
                return f"Du hast das Ticket an {target_user_name} zugewiesen"
            else:
                return f"{author_name} hat das Ticket an {target_user_name} zugewiesen"
        elif event.is_access_allowed():
            if current_user_is_target:
                return f"{author_name} hat dich zu diesem Ticket hinzugefügt"
            elif current_user_is_author:
                return f"Du hast {target_user_name} zu diesem Ticket hinzugefügt"
            else:
                return f"{target_user_name} wurde von {author_name} zu diesem Ticket hinzugefügt"
        else:
            return "neues Ereignis"
