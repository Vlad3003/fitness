from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Booking, Schedule


def schedule(request: HttpRequest):
    context = {"title": "Расписание"}
    return render(request, "schedule/schedule.html", context)


def __to_book(request: HttpRequest):
    if request.user.is_anonymous:
        messages.error(
            request,
            mark_safe(
                "Для записи на занятие необходимо <strong>авторизоваться</strong>!"
            ),
        )
        return None

    try:
        schedule_id = request.POST.get("schedule_id")
        schedule_obj = (
            Schedule.objects.select_related("trainer__user", "service")
            .annotate(
                not_canceled_booking_count=Count("booking", Q(booking__canceled=False))
            )
            .get(pk=schedule_id)
        )
    except (ValueError, ObjectDoesNotExist):
        messages.error(request, f"Не удалось записаться на занятие!")
        return None

    reservation = Booking.objects.filter(
        schedule=schedule_obj, client=request.user
    ).first()

    if reservation and not reservation.canceled:
        messages.error(request, f"Вы уже записаны на '{schedule_obj}'!")
        return None

    if schedule_obj.trainer.user == request.user:
        messages.error(request, f"Вы не можете записаться на '{schedule_obj}'")
        return None

    if not schedule_obj.count_remained_seats:
        messages.error(
            request, f"Не осталось свободных мест на занятие '{schedule_obj}'!"
        )
        return None

    if not schedule_obj.in_future:
        messages.error(
            request,
            f"Записаться на '{schedule_obj}' уже нельзя!",
        )
        return None

    if reservation:
        reservation.canceled = False
        reservation.save()
    else:
        Booking.objects.create(schedule=schedule_obj, client=request.user)

    messages.success(request, f"Вы успешно записались на '{schedule_obj}'.")

    return None


def booking(request: HttpRequest):
    if request.method != "POST":
        return HttpResponse(status=405)

    redirect_url = request.POST.get("next", reverse("schedule:schedule"))
    __to_book(request)

    return redirect(redirect_url)


def __cancel(request: HttpRequest):
    if request.user.is_anonymous:
        messages.error(request, f"Не удалось отменить занятие!")
        return None

    try:
        schedule_id = request.POST.get("schedule_id")

        reservation = (
            Booking.objects.filter(schedule_id=schedule_id, client=request.user)
            .select_related("schedule", "schedule__service")
            .first()
        )
    except (ValueError, ObjectDoesNotExist):
        messages.error(request, f"Не удалось отменить занятие!")
        return None

    if reservation and reservation.canceled:
        messages.error(request, f"Не удалось отменить занятие!")
        return None

    if reservation.schedule.day_before:
        reservation.canceled = True
        reservation.save()

        messages.success(
            request, f"Вы успешно отменили запись на '{reservation.schedule}'."
        )

    else:
        messages.error(
            request, f"Отменить запись на '{reservation.schedule}' уже нельзя!"
        )

    return None


def cancel(request: HttpRequest):
    if request.method != "POST":
        return HttpResponse(status=405)

    redirect_url = request.POST.get("next", reverse("schedule:schedule"))
    __cancel(request)

    return redirect(redirect_url)
