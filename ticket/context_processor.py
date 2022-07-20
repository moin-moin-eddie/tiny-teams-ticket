from ticket.models import TicketEvent
from ticket.services import TicketEventService


def get_notifications(request, limit=None):
    user = request.user
    notification_service = TicketEventService(current_user=user)
    notifications = TicketEvent.objects\
        .filter(user_to_notify=user,seen=False)\
        .exclude(author=user)\
        .order_by('-timestamp')\
        .select_related(
        "author", "ticket", "user_to_notify", "target_user", "comment"
    )

    count = notifications.count()

    if limit: notifications = notifications[:limit]

    for notification in notifications:
        notification.event_text = notification_service.get_event_text(
            event=notification,
            author=notification.author,
            target_user=notification.target_user
        )

    return notifications, count


def top_notifications(request):
    context = {}
    if request.user.is_authenticated:
        top_notifications, notification_count = get_notifications(request=request, limit=3)
        context['top_notifications'] = top_notifications
        context['notification_count'] = notification_count
    return context
