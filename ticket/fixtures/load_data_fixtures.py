import json

from django.contrib.auth.models import Group

from ticket.models import ProblemSource

with open('ticket/fixtures/data_fixtures.json') as json_file:
    data = json.load(json_file)
    for i in data:
        name = i["fields"]["name"]
        slug = i["fields"]["slug"]
        group = i["fields"]["group"]
        p = ProblemSource(
            name=name,
            slug=slug,
            group=Group.objects.get(name='Employee')
        )
        if "parent" in i["fields"].keys():
            parent = i["fields"]["parent"]
            p.parent = ProblemSource.objects.get(name=parent)
        p.save()
