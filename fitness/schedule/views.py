from datetime import date, timedelta

from core.models import Trainer
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, OuterRef, Prefetch, Q, QuerySet, Subquery
from django.db.models.fields import IntegerField
from django.db.models.functions import TruncDate
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.safestring import mark_safe
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Booking, Schedule
from .serializers import (
    BookedScheduleSerializer,
    CreateBookingSerializer,
    ScheduleSerializer,
    TrainerScheduleResponseSerializer,
)

User = get_user_model()


def get_schedule(user: User, **kwargs) -> tuple[QuerySet[Schedule], list[date]]:
    today = date.today()
    end_date = today + timedelta(days=6)
    schedule_date_range = (today, end_date)

    days = [today + timedelta(days=i) for i in range(7)]

    schedule_objs = (
        Schedule.objects.select_related("service", "trainer__user")
        .filter(start_time__date__range=schedule_date_range, **kwargs)
        .annotate(
            date=TruncDate("start_time"),
            not_canceled_bookings_count=Count("bookings", Q(bookings__canceled=False)),
            booking_id=Subquery(
                Booking.not_canceled.filter(
                    schedule=OuterRef("pk"),
                    client=user if not user.is_anonymous else 0,
                ).values("id")[:1],
                output_field=IntegerField(),
            ),
        )
        .order_by("start_time")
    )

    return schedule_objs, days


def get_booked_schedule(user: User) -> QuerySet[Booking]:
    return (
        Booking.objects.filter(client=user)
        .select_related(
            "schedule",
            "schedule__service",
            "schedule__trainer",
            "schedule__trainer__user",
        )
        .prefetch_related(
            Prefetch(
                "schedule__bookings",
                queryset=Booking.not_canceled.all(),
                to_attr="not_canceled_bookings",
            )
        )
        .annotate(date=TruncDate("schedule__start_time"))
        .order_by("-date", "schedule__start_time__time")
    )


def get_trainer_schedule(
    trainer: Trainer, include_bookings: bool = True
) -> QuerySet[Schedule]:
    res = (
        Schedule.objects.filter(trainer=trainer)
        .select_related("service")
        .annotate(date=TruncDate("start_time"))
        .order_by("-date", "start_time__time")
    )

    if include_bookings:
        res = res.prefetch_related(
            Prefetch(
                "bookings",
                Booking.not_canceled.select_related("client", "client__trainer").all(),
                to_attr="active_bookings",
            )
        )

    return res


def to_book(
    user: User, schedule_id: int | None, return_item: bool = False
) -> dict[str, str | bool | None | Schedule]:
    result: dict[str, bool | str | None | Schedule] = {
        "success": False,
        "message": "",
        "item": None,
    }

    try:
        schedule_obj = (
            Schedule.objects.select_related("trainer__user", "service")
            .annotate(
                not_canceled_bookings_count=Count(
                    "bookings", Q(bookings__canceled=False)
                )
            )
            .get(pk=schedule_id)
        )

    except (ValueError, ObjectDoesNotExist):
        result["message"] = "Занятие не найдено!"
        return result

    reservation = Booking.objects.filter(schedule=schedule_obj, client=user).first()

    if reservation and not reservation.canceled:
        result["message"] = f"Вы уже записаны на '{schedule_obj}'!"
        setattr(schedule_obj, "booking_id", reservation.pk)

    elif schedule_obj.trainer.user == user:
        result["message"] = f"Вы не можете записаться на '{schedule_obj}'"

    elif not schedule_obj.count_remained_seats:
        result["message"] = f"Не осталось свободных мест на занятие '{schedule_obj}'!"

    elif not schedule_obj.in_future:
        result["message"] = f"Записаться на '{schedule_obj}' уже нельзя!"

    else:
        if reservation:
            reservation.canceled = False
            reservation.save()
            setattr(schedule_obj, "booking_id", reservation.pk)
        else:
            new_reservation = Booking.objects.create(schedule=schedule_obj, client=user)
            setattr(schedule_obj, "booking_id", new_reservation.pk)

        result["success"] = True
        result["message"] = f"Вы успешно записались на '{schedule_obj}'"

        count = getattr(schedule_obj, "not_canceled_bookings_count") + 1
        setattr(schedule_obj, "not_canceled_bookings_count", count)

    if return_item:
        result["item"] = schedule_obj

    return result


def cancel(
    user: User, booking_id: int, return_item: bool = False
) -> dict[str, bool | str | None | Schedule]:
    result: dict[str, bool | str | None | Schedule] = {
        "success": False,
        "message": "",
        "item": None,
    }

    try:
        reservation = (
            Booking.objects.filter(id=booking_id, client=user)
            .select_related("schedule", "schedule__service", "schedule__trainer__user")
            .prefetch_related(
                Prefetch(
                    "schedule__bookings",
                    queryset=Booking.not_canceled.all(),
                    to_attr="not_canceled_bookings",
                )
            )
            .get()
        )

    except (ValueError, ObjectDoesNotExist):
        result["message"] = f"Запись не найдена!"
        return result

    if reservation.canceled:
        result["message"] = f"Запись на '{reservation.schedule}' уже отменена!"

    elif not reservation.schedule.day_before:
        result["message"] = f"Отменить запись на '{reservation.schedule}' уже нельзя!"

    else:
        reservation.canceled = True
        reservation.save()

        result["success"] = True
        result["message"] = f"Вы успешно отменили запись на '{reservation.schedule}'"

        count = len(getattr(reservation.schedule, "not_canceled_bookings")) - 1
        setattr(reservation.schedule, "not_canceled_bookings_count", count)

    if return_item:
        result["item"] = reservation.schedule

    return result


def schedule_view(request: HttpRequest):
    context = {"title": "Расписание"}
    return render(request, "schedule/schedule.html", context)


def booking_view(request: HttpRequest):
    if request.method != "POST":
        return HttpResponse(status=405)

    if request.user.is_anonymous:
        messages.error(
            request,
            mark_safe(
                "Для записи на занятие необходимо <strong>авторизоваться</strong>!"
            ),
        )
    else:
        schedule_id = request.POST.get("schedule_id")
        result = to_book(request.user, schedule_id)

        if result["success"]:
            messages.success(request, result["message"])
        else:
            messages.error(request, result["message"])

    redirect_url = request.POST.get("next", reverse("schedule:schedule"))

    return redirect(redirect_url)


def booking_cancel_view(request: HttpRequest, booking_id: int):
    if request.method != "POST":
        return HttpResponse(status=405)

    if request.user.is_anonymous:
        messages.error(request, f"Не удалось отменить занятие!")

    else:
        result = cancel(request.user, booking_id)

        if result["success"]:
            messages.success(request, result["message"])
        else:
            messages.error(request, result["message"])

    redirect_url = request.POST.get("next", reverse("schedule:schedule"))

    return redirect(redirect_url)


class ScheduleListAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ScheduleSerializer

    def get(self, request):
        schedule_objs, days = get_schedule(request.user)
        serializer = self.get_serializer(schedule_objs, many=True)

        result = {"days": days, "items": serializer.data}

        return Response(result, status=status.HTTP_200_OK)


class BookingsListCreateAPIView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return get_booked_schedule(self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateBookingSerializer
        return BookedScheduleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        schedule_id = serializer.validated_data["schedule_id"]
        result = to_book(request.user, schedule_id, return_item=True)

        if result["item"]:
            result["item"] = ScheduleSerializer(
                result["item"], context={"request": request}
            ).data

        return Response(result, status=status.HTTP_200_OK)


class BookingCancelAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ScheduleSerializer

    def post(self, request, booking_id):
        result = cancel(request.user, booking_id, return_item=True)

        if result["item"]:
            serializer = self.get_serializer(result["item"])

            result["item"] = serializer.data

        return Response(result, status=status.HTTP_200_OK)


class TrainerScheduleListAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TrainerScheduleResponseSerializer
    trainer: Trainer | None = None

    def get_queryset(self):
        if not hasattr(self.request.user, "trainer"):
            raise PermissionDenied()

        self.trainer = getattr(self.request.user, "trainer")
        return get_trainer_schedule(self.trainer, include_bookings=False)

    def get(self, _):
        schedule = self.get_queryset()
        bookings = Booking.not_canceled.filter(schedule__trainer=self.trainer)
        clients = (
            User.objects.filter(bookings__in=bookings)
            .select_related("trainer")
            .distinct()
            .only(
                "id",
                "first_name",
                "last_name",
                "middle_name",
                "email",
                "phone_number",
                "photo",
                "username",
                "trainer__photo",
            )
        )

        data = {"items": schedule, "clients": clients, "bookings": bookings}

        serializer = self.get_serializer(data)
        return Response(serializer.data)
