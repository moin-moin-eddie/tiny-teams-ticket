from background_task import background
from django.conf import settings
from django.contrib.auth.models import User
from huey import crontab
from huey.contrib.djhuey import periodic_task

from authentication.graph_api.base import GraphAPI
from authentication.models import MicrosoftProfile
from ticket.models import Analytics


@background(schedule=1)
def update_analytics_in_background():
    print("UPDATING ANALYTICS")
    Analytics.update_tickets_per_problem_source()
    Analytics.update_tickets_per_day()


def update_analytics_in_development():
    print("UPDATING ANALYTICS")
    Analytics.update_tickets_per_problem_source()
    Analytics.update_tickets_per_day()


def manual_update_analytics():
    if settings.DEBUG:
        update_analytics_in_development()
    else:
        update_analytics_in_background()


@periodic_task(crontab(minute=30, hour="*/12"))
def daily_user_update():
    update_users()

@periodic_task(crontab(hour='12', day_of_week='0'))
def weekly_completed_task_cleanup():
    from background_task.models import CompletedTask
    CompletedTask.objects.all().delete()


# Update analytics every 10 minutes between 5-19 Uhr Monday-Saturday
@periodic_task(crontab(minute="*/10", hour='5-19', day_of_week='1,2,3,4,5,6'))
def update_analytics():
    Analytics.update_tickets_per_day()
    Analytics.update_tickets_per_problem_source()


def update_users():
    graph_api = GraphAPI()
    users = graph_api.get_all_users()
    for user in users:
        name = user["displayName"]
        email = user["mail"] if user["mail"] else user["userPrincipalName"]
        id = user["id"]
        new_user, created = User.objects.update_or_create(
            username=email,
            defaults={
                "email": email,
            }
        )
        MicrosoftProfile.objects.update_or_create(
            user=new_user,
            defaults={"ms_id": id})
        if created:
            new_user.first_name = name
            new_user.set_password(email)
            new_user.save()
            print("NEW USER CREATED:", name)
