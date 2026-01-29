from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from django import template
from django.utils import timezone
from django.utils.formats import date_format

register = template.Library()


@register.filter
def to_day(day: date | datetime):
    now = timezone.localtime(timezone.now()).date()

    if day == now:
        return "сегодня"
    elif day == now - relativedelta(days=1):
        return "вчера"
    elif day == now + relativedelta(days=1):
        return "завтра"
    elif day.year == now.year:
        return date_format(day, "l, j E").lower()
    else:
        return date_format(day, "j E Y")
