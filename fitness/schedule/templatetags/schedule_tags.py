from itertools import groupby

from django import template
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from schedule.views import get_schedule

register = template.Library()
User = get_user_model()


@register.simple_tag(name="get_schedule")
def get_schedule_tag(request: HttpRequest, **kwargs):
    schedule_objs, days = get_schedule(request.user, **kwargs)

    grouped = []

    for key, group in groupby(schedule_objs, lambda item: getattr(item, "date")):
        grouped.append({"date": key, "items": list(group)})

    context = {
        "schedule": grouped,
        "days": days,
    }
    return context
