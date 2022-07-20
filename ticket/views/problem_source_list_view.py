from django.views.generic import ListView

from ticket.models import ProblemSource, Ticket


class ProblemSourceListView(ListView):
    model = ProblemSource
    template_name = 'ticket/select_problem_source.html'
    context_object_name = 'problem_sources'

    def get_queryset(self, *args, **kwargs):
        slug = self.kwargs.get('slug')
        if slug:
            parent = ProblemSource.objects.get(slug=slug)
            results = ProblemSource.objects.filter(parent=parent)
        else:
            results = ProblemSource.objects.filter(parent__isnull=True).exclude(slug="feature-request")
        return sorted(results, key=lambda t: t.name, reverse=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        common_problem_sources = Ticket.objects.get_common_problem_sources_for(user)

        context["common_problem_sources"] = common_problem_sources[:4]

        return context
