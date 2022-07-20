import random

import factory
from django.contrib.auth.models import User
from factory import fuzzy
from factory.django import DjangoModelFactory

from ticket.models import ProblemSource, Ticket, TicketEvent, Comment


@factory.Faker.override_default_locale('de_DE')
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    password = factory.Faker("password")
    email = factory.Faker("ascii_company_email")
    first_name = factory.Faker("name")


@factory.Faker.override_default_locale('de_DE')
class TicketFactory(DjangoModelFactory):
    class Meta:
        model = Ticket

    title = factory.Faker("sentence")
    problem_source = factory.Iterator([p for p in ProblemSource.objects.all() if p.is_leaf_node()])
    note = factory.Faker("paragraph")
    created_by = factory.Iterator(User.objects.filter(is_staff=False))
    assigned_to = factory.Iterator(User.objects.filter(is_staff=True))


@factory.Faker.override_default_locale('de_DE')
class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    author = factory.Iterator(User.objects.all())
    text = factory.Faker("paragraph")
    ticket = factory.Iterator(Ticket.objects.all())


@factory.Faker.override_default_locale('de_DE')
class TicketEventFactory(DjangoModelFactory):
    class Meta:
        model = TicketEvent

    type = factory.fuzzy.FuzzyChoice([
        TicketEvent.EventType.EDIT,
        TicketEvent.EventType.REOPEN,
        TicketEvent.EventType.CLOSE,
        TicketEvent.EventType.NEW_ATTACHMENT
    ])
    ticket = factory.Iterator(Ticket.objects.all())
    author = factory.Iterator(User.objects.all())
    user_to_notify = factory.Iterator(User.objects.all())
    seen = factory.Iterator([False, False, False, True])
