from django.contrib.auth.models import User
from django.db import models

from ticket.models import TicketEvent


class MicrosoftProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Benutzer")
    ms_id = models.CharField(max_length=150, blank=True, null=True, verbose_name="Microsoft ID")
    receives_new_ticket_notifications = models.BooleanField(
        default=False, verbose_name="Neues Ticket Benachrichtigungen aktiviert?"
    )
    teams_notifications_active = models.BooleanField(
        default=True, verbose_name="Benachrichtigungen aktiviert?"
    )
    dark_mode_active = models.BooleanField(default=False, verbose_name="Dunkelmodus aktiviert?")

    def __str__(self):
        return f"Microsoftprofil von {self.user.first_name}"

    def receives_notifications(self):
        return True if self.teams_notifications_active and self.ms_id != None else False

    def should_receive_this_notification(self, type):
        result = self.receives_notifications()
        if type == TicketEvent.EventType.NEW and not self.receives_new_ticket_notifications:
            result = False

        return result
