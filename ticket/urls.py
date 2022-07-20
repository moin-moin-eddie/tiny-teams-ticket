from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import path, include

from ticket import views
from ticket.views import IndexView
from ticket.views.ajax_views import SearchUsersView, AddUserView, PauseTicketReminders, Statistics, AutoAssignView
from ticket.views.search_view import SearchTicketsView

login_url = "/login/"

urlpatterns = [

    # The home page
    path('', login_required(IndexView.as_view(), login_url=login_url), name='home'),

    # Search results
    path('search/', login_required(SearchTicketsView.as_view(), login_url=login_url), name='search'),

    # AJAX Requests
    path('ajax/search-users/', login_required(SearchUsersView.as_view(), login_url=login_url), name='search-users'),
    path('ajax/add-user/', login_required(AddUserView.as_view(), login_url=login_url), name='add-user'),
    path('ajax/pause-reminders/', login_required(PauseTicketReminders.as_view(), login_url=login_url), name='pause-reminders'),
    path('statistics/', login_required(Statistics.as_view(), 'redirect', '/login/'), name='statistics'),
    path('statistics/autoassign/', login_required(AutoAssignView.as_view(), 'redirect', '/login/'), name='time_to_auto_assign'),

    # Problem source selection
    path('problem_sources/', login_required(views.ProblemSourceListView.as_view(), login_url=login_url),
         name='problem_sources'),
    path('problem_sources/<str:slug>/', login_required(views.ProblemSourceListView.as_view(), login_url=login_url),
         name='problem_sources'),

    # Ticket creation
    path('create_ticket/<str:slug>/', login_required(views.CreateTicketView.as_view(), login_url=login_url),
         name='create_ticket'),

    # Ticket Detail & Edit
    path('ticket/<int:id>/detail/', login_required(views.TicketDetailView.as_view(), login_url=login_url),
         name='ticket_detail'),
    path('ticket/<int:id>/edit/', login_required(views.TicketDetailView.as_view(), login_url=login_url),
         name='edit_ticket'),

    # Ticket Lists
    path('tickets/<str:type>/', login_required(views.TicketListView.as_view(), login_url=login_url),
         name='ticket_list'),
    path('tickets/<str:type>/<str:status>/', login_required(views.TicketListView.as_view(), login_url=login_url),
         name='ticket_list'),

]


if settings.DEBUG and not settings.PROD:
    import debug_toolbar
    urlpatterns.append(
        path('__debug__/', include(debug_toolbar.urls)),
    )