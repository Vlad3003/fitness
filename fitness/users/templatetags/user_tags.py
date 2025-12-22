from django import template
from django.http import HttpRequest
from django.urls import reverse

register = template.Library()


@register.inclusion_tag("users/includes/user-menu.html")
def show_user_menu(request: HttpRequest):
    menu = [
        {
            "name": "Профиль",
            "icon_class": "bi-person-circle",
            "url": reverse("users:profile"),
        },
        {
            "name": "Редактировать профиль",
            "icon_class": "bi-pen",
            "url": reverse("users:profile_edit"),
        },
        {
            "name": "Мои занятия",
            "icon_class": "bi-calendar-week",
            "url": reverse("schedule:bookings"),
        },
    ]
    menu_for_trainers = (
        {
            "name": "Мои тренировки",
            "icon_class": "bi-calendar-check",
            "url": reverse("schedule:trainer_schedule"),
        },
    )
    menu_for_staff = (
        {
            "name": "Админ панель",
            "icon_class": "bi-laptop",
            "url": reverse("admin:index"),
        },
    )

    if hasattr(request.user, "trainer"):
        menu.append({})
        menu.append(*menu_for_trainers)

    if request.user.is_staff:
        menu.append({})
        menu.append(*menu_for_staff)

    context = {"menu": menu, "user": request.user, "request": request}

    return context
