from django.test import SimpleTestCase
from django.urls import reverse, resolve

from ticket.views import IndexView, ProblemSourceListView
from ticket.views.search_view import SearchUsersView, AddUserView


class TestUrls(SimpleTestCase):

    def test_home_resolves(self):
        url = reverse('home')
        self.assertEquals(resolve(url).func.view_class, IndexView)

    def test_search_users_resolves(self):
        url = reverse('search-users')
        self.assertEquals(resolve(url).func.view_class, SearchUsersView)

    def test_add_user_resolves(self):
        url = reverse('add-user')
        self.assertEquals(resolve(url).func.view_class, AddUserView)

    def test_problem_source_list_resolves(self):
        url = reverse('problem_sources')
        self.assertEquals(resolve(url).func.view_class, ProblemSourceListView)
