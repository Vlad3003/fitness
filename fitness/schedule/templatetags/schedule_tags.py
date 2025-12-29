from itertools import groupby

from django import template
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from schedule.views import get_schedule

register = template.Library()
User = get_user_model()


@register.simple_tag(name="get_schedule")
def get_schedule_tag(request: HttpRequest, **kwargs):
    schedule_objs, schedule_days = get_schedule(request.user, **kwargs)

    schedule = []
    days = {day: False for day in schedule_days}

    for day, items in groupby(schedule_objs, lambda item: getattr(item, "date")):
        schedule.append({"date": day, "items": list(items)})
        days[day] = True

    context = {
        "schedule": schedule,
        "days": list(days.items()),
    }
    return context
