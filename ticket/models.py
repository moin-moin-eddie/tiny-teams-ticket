import datetime
import random

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django_currentuser.db.models import CurrentUserField
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from core.settings.common import AZURE_APP_ID, BASE_URL
from ticket.managers.event import TicketEventManager
from ticket.managers.ticket import TicketManager


def random_recent_date_time(time_in_days=180):
    now = timezone.now()
    # random time within x days in seconds (days*86400)
    return now - datetime.timedelta(seconds=random.randint(0, (time_in_days * 86400)))


class ProblemSource(MPTTModel):
    name = models.CharField(max_length=60, verbose_name="Name der Quelle")
    slug = models.SlugField(default="")
    breadcrumb = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Reihenfolge"
    )
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='problem_source',
        on_delete=models.CASCADE,
        verbose_name="Oberquelle")

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Problemquelle"
        verbose_name_plural = "Problemquellen"

    def save(self, **kwargs):
        self.breadcrumb = self.create_category_breadcrumb()
        super(ProblemSource, self).save()

    def count_tickets(self, user):
        return Ticket.objects.filter(problem_source=self, created_by=user).count()

    def count_user_tickets(self, user):
        # Recursive count of tickets for single user
        if self.has_children():
            children = self.get_children()
            count = sum([c.count_user_tickets(user) for c in children])
        else:
            count = Ticket.objects.filter(problem_source=self, created_by=user).count()
        return count

    def has_children(self):
        return True if self.get_children().count() > 0 else False

    def create_category_breadcrumb(self):
        title = self.name
        parent = self.parent
        while parent:
            title = parent.name + " > " + title
            parent = parent.parent
        return title


class Ticket(models.Model):
    title = models.CharField(max_length=100, blank=True, null=True, verbose_name='Titel')
    problem_source = models.ForeignKey(ProblemSource, on_delete=models.RESTRICT, null=True,
                                       verbose_name="Problemquelle")
    created_date = models.DateTimeField(verbose_name="Erstellt am")
    created_by = CurrentUserField(related_name="created_by", verbose_name="Erstellt von")
    due_date = models.DateField(blank=True, null=True, verbose_name="Fälligkeitsdatum")
    completed = models.BooleanField(default=False, verbose_name="Erledigt")
    completed_date = models.DateTimeField(blank=True, null=True, verbose_name="Erledigt am")
    followers = models.ManyToManyField(User, related_name="followers", verbose_name="Gefolgt von")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="ticket_assigned_to",
        on_delete=models.CASCADE,
        verbose_name="Zugewiesen an"
    )
    last_modified = models.DateTimeField(auto_now=True, verbose_name="Zuletzt bearbeitet am")
    modified_by = CurrentUserField(on_update=True, verbose_name="Zuletzt bearbeitet von")
    note = models.TextField(blank=True, null=True, verbose_name="Notiz")
    priority = models.PositiveIntegerField(blank=False, null=False, default=0, verbose_name="Priorität")
    paused_until = models.DateTimeField(blank=True, null=True, verbose_name='Pausiert bis')
    objects = TicketManager()

    @property
    def category(self):
        return self.problem_source.breadcrumb

    def teams_deep_link(self):
        base = "https://teams.microsoft.com/l/entity"
        app_id = AZURE_APP_ID
        entity_id = "ticket"
        web_url = f"{BASE_URL}/ticket/{self.id}/detail/"
        label = f"label=Ticket{self.id}"
        context = """context={"subEntityId":""" + str(self.id) + "}"
        deep_link = f"{base}/{app_id}/{entity_id}?{web_url}&{label}&{context}"

        return deep_link

    def __str__(self):
        return f"{self.id} - {self.category}"

    # Auto-set the Task creation / completed date
    def save(self, **kwargs):
        # If Task is being marked complete, set the completed_date
        if not self.created_date and not settings.RANDOM_TIMES:
            self.created_date = timezone.now()
        elif not self.created_date and settings.RANDOM_TIMES:
            self.created_date = random_recent_date_time()

        if self.completed and not self.completed_date:
            self.completed_date = timezone.now()

        if not self.completed and self.completed_date:
            self.completed_date = None

        super(Ticket, self).save()

    def get_comments(self):
        return Comment.objects.filter(ticket=self, level=0) \
            .select_related('parent', 'author') \
            .order_by('-created_date')

    def detail_page(self):
        return f"{settings.BASE_URL}/ticket/{self.id}/detail/"

    def close_ticket(self):
        self.completed = True
        self.save()

    def open_ticket(self):
        self.completed = False
        self.save()

    def was_updated(self):
        return True if self.last_modified != self.created_date else False

    def has_visible_followers(self):
        return True if self.get_visible_followers().count() > 0 else False

    def get_visible_followers(self):
        return self.followers.filter(is_staff=False)

    def get_priorities(self):
        return {'Hoch': 2, 'Mittel': 1, 'Niedrig': 0}

    def is_paused(self):
        if self.paused_until:
            if self.paused_until > timezone.now():
                return True
        else:
            return False

    def priority_color(self):
        if self.priority == 2:
            return 'danger'
        elif self.priority == 1:
            return 'warning'
        else:
            return 'info'

    def priority_text(self):
        if self.priority == 2:
            return 'Hoch'
        elif self.priority == 1:
            return 'Mittel'
        else:
            return 'Niedrig'

    class Meta:
        ordering = ["priority", "created_date"]


class Attachment(models.Model):
    name = models.CharField(max_length=100, verbose_name="Dateiname")
    file = models.FileField(upload_to='ticket/attachments/', verbose_name="Datei")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, verbose_name="Ticket")

    class Meta:
        verbose_name = 'Anhang'
        verbose_name_plural = 'Anhänge'

    def __str__(self):
        return self.name

    def extension(self):
        name, extension = self.file.name.split('.')
        return extension


class Comment(MPTTModel):
    author = CurrentUserField(related_name="creator", verbose_name="Autor")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, verbose_name="Ticket")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    text = models.TextField(blank=True)
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='parent_comment',
        on_delete=models.CASCADE,
        verbose_name="Oberkommentar",
    )

    class Meta:
        verbose_name = 'Kommentar'
        verbose_name_plural = 'Kommentare'

    def has_replies(self):
        return True if self.get_children().count() > 0 else False

    def get_replies(self):
        if self.rght > 2:
            return Comment.objects.filter(parent=self) \
                .select_related('author') \
                .order_by('created_date')
        else:
            return None

    def __str__(self):
        return f"{self.id} - {self.ticket.title} - {self.parent_id}"


class TicketEvent(models.Model):
    class EventType(models.TextChoices):
        NEW = "new"
        EDIT = "edit"
        COMMENT = "comment"
        REPLY = "reply"
        CLOSE = "close"
        REOPEN = "reopen"
        NEW_ATTACHMENT = "new_attachment"
        ASSIGNED = "assigned"
        ACCESS_ALLOWED = "access_allowed"

    author = CurrentUserField(related_name="author", verbose_name="Autor")
    type = models.CharField(max_length=20, choices=EventType.choices, verbose_name="Art")
    timestamp = models.DateTimeField(verbose_name="Zeitstempel")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    user_to_notify = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Benutzer zu benachrichtigen"
    )
    target_user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='subject_user', verbose_name="Zielbenutzer"
    )
    seen = models.BooleanField(default=False, verbose_name="Gesehen?")
    comment = models.ForeignKey(Comment, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Kommentar")
    is_internal = models.BooleanField(default=False, verbose_name="Intern?")
    is_automatic = models.BooleanField(default=False, verbose_name="Vom System erstellt?")
    objects = TicketEventManager()

    @property
    def date(self):
        return self.timestamp.date()

    @property
    def day(self):
        return self.timestamp.day

    @property
    def time(self):
        return self.timestamp.time()

    @property
    def text(self):
        return self.comment.text if self.comment else ""

    @property
    def category(self):
        return self.ticket.category

    class Meta:
        verbose_name = 'Benachrichtigung'
        verbose_name_plural = 'Benachrichtigungen'

    def save(self, **kwargs):
        if not self.timestamp:
            if settings.RANDOM_TIMES:
                self.timestamp = random_recent_date_time()
            else:
                self.timestamp = timezone.now()
        super(TicketEvent, self).save()

    def is_new(self):
        return True if self.type == self.EventType.NEW else False

    def is_edit(self):
        return True if self.type == self.EventType.EDIT else False

    def is_comment(self):
        return True if self.type == self.EventType.COMMENT else False

    def is_reply(self):
        return True if self.type == self.EventType.REPLY else False

    def is_close(self):
        return True if self.type == self.EventType.CLOSE else False

    def is_reopen(self):
        return True if self.type == self.EventType.REOPEN else False

    def is_new_attachment(self):
        return True if self.type == self.EventType.NEW_ATTACHMENT else False

    def is_assigned(self):
        return True if self.type == self.EventType.ASSIGNED else False

    def is_access_allowed(self):
        return True if self.type == self.EventType.ACCESS_ALLOWED else False

    def event_title(self):
        return f"{self.ticket.title} Ticket"

    def time_since_event(self):
        diff = timezone.now() - self.timestamp
        seconds = int(diff.total_seconds())
        minutes = int(diff.total_seconds() / 60)
        hours = int(minutes / 60)
        days = diff.days
        if days > 1:
            return f"vor {diff.days} Tage"
        elif days == 1:
            return "vor 1 Tag"
        elif hours > 1:
            return f"vor {hours} Stunden"
        elif hours == 1:
            return "vor einer Stunde"
        elif minutes > 1:
            return f"vor {minutes} Minuten"
        elif minutes == 1:
            return "vor einer Minute"
        elif seconds > 0:
            return f"vor {seconds} Sekunden"
        else:
            return ""

    def event_icon(self):
        if self.is_new():
            return "fas fa-plus-square"
        elif self.is_edit():
            return "fas fa-pen-square"
        elif self.is_comment():
            return "fas fa-comment-medical"
        elif self.is_reply():
            return "fas fa-reply"
        elif self.is_close():
            return "fas fa-lock"
        elif self.is_reopen():
            return "fas fa-lock-open"
        elif self.is_new_attachment():
            return "fas fa-link"
        elif self.is_assigned():
            return "fas fa-user-tag"
        elif self.is_access_allowed():
            return "fas fa-door-open"
        else:
            return "far fa-bell"

    def event_color(self):
        if self.is_new() or self.is_access_allowed():
            return "success"
        elif self.is_edit():
            return "purple"
        elif self.is_comment() or self.is_reply():
            return "warning"
        elif self.is_close():
            return "danger"
        elif self.is_reopen():
            return "green"
        elif self.is_new_attachment():
            return "orange"
        elif self.is_assigned():
            return "warning"
        else:
            return "warning"


class Analytics(models.Model):
    name = models.CharField(max_length=64, verbose_name="Name")
    labels = models.TextField(verbose_name="Etiketten")
    data = models.TextField(verbose_name="Daten")

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Analyse'
        verbose_name_plural = 'Analyse'

    @classmethod
    def update_tickets_per_day(cls):
        bar_labels = []
        open_data = []
        closed_data = []

        bar_chart_queryset = Ticket.objects.open_closed_per_day()

        for result in bar_chart_queryset:
            data = bar_chart_queryset[result]
            bar_labels.append(data['date'])
            open_data.append(data["total_created"])
            closed_data.append(data["total_closed"])

        Analytics.objects.update_or_create(
            name='Tickets pro Tag',
            defaults={
                'labels': bar_labels,
                'data': [open_data, closed_data]
            }
        )

    @classmethod
    def update_tickets_per_problem_source(cls):
        problem_sources = ProblemSource.objects.all()
        pie_labels = []
        pie_data = []

        pie_chart_queryset = Ticket.objects.group_by_problem_source()

        for ticket in pie_chart_queryset:
            problem_source = problem_sources.get(tree_id=ticket["problem_source__tree_id"], level=0)
            pie_labels.append(problem_source.name)
            pie_data.append(ticket["total"])

        Analytics.objects.update_or_create(
            name='Tickets pro Problemquelle',
            defaults={
                'labels': pie_labels,
                'data': pie_data
            }
        )

    @staticmethod
    def get_tickets_per_day():
        return Analytics.objects.get(name='Tickets pro Tag')

    @staticmethod
    def get_tickets_per_problem_source():
        return Analytics.objects.get(name='Tickets pro Problemquelle')
