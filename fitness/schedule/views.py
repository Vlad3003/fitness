from datetime import date, timedelta

from core.models import Trainer
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import (
    BooleanField,
    Case,
    Count,
    Exists,
    OuterRef,
    Prefetch,
    Q,
    QuerySet,
    When,
)
from django.db.models.functions import TruncDate
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.safestring import mark_safe
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking, Schedule
from .serializers import (
    BookedScheduleSerializer,
    ScheduleBookingSerializer,
    ScheduleSerializer,
    TrainerScheduleSerializer,
)


def get_schedule(
    request: HttpRequest, **kwargs
) -> tuple[QuerySet[Schedule], list[date]]:
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
            is_user_booked=Case(
                When(
                    Exists(
                        Booking.not_canceled.filter(
                            schedule=OuterRef("pk"),
                            client=request.user if not request.user.is_anonymous else 0,
                        )
                    ),
                    then=True,
                ),
                default=False,
                output_field=BooleanField(),
            ),
        )
        .order_by("start_time")
    )

    return schedule_objs, days


def get_booked_schedule(request: HttpRequest) -> QuerySet[Booking]:
    return (
        Booking.objects.filter(client=request.user)
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


def get_trainer_schedule(trainer: Trainer) -> QuerySet[Schedule]:
    return (
        Schedule.objects.filter(trainer=trainer)
        .select_related("service")
        .prefetch_related(
            Prefetch(
                "bookings",
                Booking.not_canceled.select_related("client", "client__trainer").all(),
                to_attr="active_bookings",
            )
        )
        .annotate(date=TruncDate("start_time"))
        .order_by("-date", "start_time__time")
    )


def schedule(request: HttpRequest):
    context = {"title": "Расписание"}
    return render(request, "schedule/schedule.html", context)


def to_book(
    request: HttpRequest, schedule_id: int | None, return_item: bool = False
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
                not_canceled_bookings_count=Count("bookings", Q(bookings__canceled=False))
            )
            .get(pk=schedule_id)
        )

    except (ValueError, ObjectDoesNotExist):
        result["message"] = "Не удалось записаться на занятие!"
        return result

    reservation = Booking.objects.filter(
        schedule=schedule_obj, client=request.user
    ).first()

    if reservation and not reservation.canceled:
        result["message"] = f"Вы уже записаны на '{schedule_obj}'!"

    elif schedule_obj.trainer.user.id == request.user.id:
        result["message"] = f"Вы не можете записаться на '{schedule_obj}'"

    elif not schedule_obj.count_remained_seats:
        result["message"] = f"Не осталось свободных мест на занятие '{schedule_obj}'!"

    elif not schedule_obj.in_future:
        result["message"] = f"Записаться на '{schedule_obj}' уже нельзя!"

    else:
        if reservation:
            reservation.canceled = False
            reservation.save()
        else:
            Booking.objects.create(schedule=schedule_obj, client=request.user)

        result["success"] = True
        result["message"] = f"Вы успешно записались на '{schedule_obj}'."

        if return_item:
            modified_schedule_obj = (
                Schedule.objects.select_related("trainer__user", "service")
                .annotate(
                    not_canceled_bookings_count=Count(
                        "bookings", Q(bookings__canceled=False)
                    )
                )
                .get(pk=schedule_id)
            )

            setattr(modified_schedule_obj, "is_user_booked", True)
            result["item"] = modified_schedule_obj

    return result


def booking(request: HttpRequest):
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
        result = to_book(request, schedule_id)

        if result["success"]:
            messages.success(request, result["message"])
        else:
            messages.error(request, result["message"])

    redirect_url = request.POST.get("next", reverse("schedule:schedule"))

    return redirect(redirect_url)


def cancel(
    request: HttpRequest, schedule_id: int | None, return_item: bool = False
) -> dict[str, bool | str | None | Schedule]:
    result: dict[str, bool | str | None | Schedule] = {
        "success": False,
        "message": "",
        "item": None,
    }

    try:
        reservation = (
            Booking.objects.filter(schedule_id=schedule_id, client=request.user)
            .select_related("schedule", "schedule__service")
            .prefetch_related(
                Prefetch(
                    "schedule__bookings",
                    queryset=Booking.not_canceled.all(),
                    to_attr="not_canceled_bookings",
                )
            )
            .first()
        )

    except (ValueError, ObjectDoesNotExist):
        result["message"] = f"Не удалось отменить запись!"
        return result

    if not reservation or reservation.canceled:
        result["message"] = f"Не удалось отменить запись!"

    elif not reservation.schedule.day_before:
        result["message"] = f"Отменить запись на '{reservation.schedule}' уже нельзя!"

    else:
        reservation.canceled = True
        reservation.save()

        result["success"] = True
        result["message"] = f"Вы успешно отменили запись на '{reservation.schedule}'."

        if return_item:
            modified_schedule_obj = (
                Schedule.objects.select_related("trainer__user", "service")
                .annotate(
                    not_canceled_bookings_count=Count(
                        "bookings", Q(bookings__canceled=False)
                    )
                )
                .get(pk=schedule_id)
            )

            result["item"] = modified_schedule_obj

    return result


def booking_cancel(request: HttpRequest):
    if request.method != "POST":
        return HttpResponse(status=405)

    if request.user.is_anonymous:
        messages.error(request, f"Не удалось отменить занятие!")

    else:
        schedule_id = request.POST.get("schedule_id")
        result = cancel(request, schedule_id)

        if result["success"]:
            messages.success(request, result["message"])
        else:
            messages.error(request, result["message"])

    redirect_url = request.POST.get("next", reverse("schedule:schedule"))

    return redirect(redirect_url)


class ScheduleAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get(request):
        schedule_objs, days = get_schedule(request)

        result = {
            "days": days,
            "items": ScheduleSerializer(
                schedule_objs, many=True, context={"request": request}
            ).data,
        }

        return Response(result, status=status.HTTP_200_OK)


class BookedScheduleAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BookedScheduleSerializer

    def get_queryset(self):
        return get_booked_schedule(self.request)


class TrainerScheduleListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TrainerScheduleSerializer

    def get_queryset(self):
        if not hasattr(self.request.user, "trainer"):
            raise PermissionDenied()

        trainer = getattr(self.request.user, "trainer")
        return get_trainer_schedule(trainer)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)


class ScheduleBookingAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ScheduleBookingSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        schedule_id = serializer.validated_data["schedule_id"]
        result = to_book(request, schedule_id, return_item=True)

        if result["item"]:
            result["item"] = ScheduleSerializer(
                result["item"], context={"request": request}
            ).data

        return Response(result, status=status.HTTP_200_OK)


class BookingCancelAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ScheduleBookingSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        schedule_id = serializer.validated_data["schedule_id"]
        result = cancel(request, schedule_id, return_item=True)

        if result["item"]:
            result["item"] = ScheduleSerializer(
                result["item"], context={"request": request}
            ).data

        return Response(result, status=status.HTTP_200_OK)
