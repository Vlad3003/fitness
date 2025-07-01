from datetime import date, timedelta
from itertools import groupby

from django import template
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import HttpRequest

from schedule.models import Schedule, Booking

register = template.Library()
User = get_user_model()


@register.inclusion_tag("schedule/schedule-list.html")
def show_schedule(request: HttpRequest, **kwargs):
    today = date.today()
    end_date = today + timedelta(days=6)
    schedule_date_range = [today, end_date]
    booking_date_range = [today - timedelta(days=6), end_date]

    days = [today + timedelta(days=i) for i in range(7)]

    schedule_objs = (
        Schedule.objects.select_related("service", "trainer__user")
        .filter(start_time__date__range=schedule_date_range, **kwargs)
        .annotate(
            date=TruncDate("start_time"),
            not_canceled_booking_count=Count("booking", Q(booking__canceled=False)),
        )
    )

    grouped = []

    for key, group in groupby(schedule_objs, lambda item: getattr(item, "date")):
        grouped.append({"date": key, "items": list(group)})

    if request.user.is_authenticated:
        user_booked = set(
            Booking.not_canceled.filter(
                client=request.user, booked_at__date__range=booking_date_range
            ).values_list("schedule_id", flat=True)
        )
    else:
        user_booked = set()

    context = {
        "schedule": grouped,
        "days": days,
        "user_booked": user_booked,
        "request": request,
    }
    return context
