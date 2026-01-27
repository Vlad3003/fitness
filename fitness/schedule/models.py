from datetime import datetime, timedelta

from core.models import Service, Trainer
from django.contrib.auth import get_user_model
from django.db import models
from django.template.defaultfilters import date as date_filter
from django.utils import timezone

User = get_user_model()

schedule_detail_fields = (
    "service__slug",
    "service__name",
    "service__photo",
    "service__color",
    "service__max_participants",
    "service__duration",
    "trainer__slug",
    "trainer__photo",
    "trainer__user__first_name",
    "trainer__user__last_name",
    "trainer__user__middle_name",
    "start_time",
)

schedule_short_fields = (
    "service__name",
    "service__max_participants",
    "service__duration",
    "start_time",
    "trainer_id",
    "trainer__user__id",
)

trainer_schedule_fields = (
    "service__name",
    "service__color",
    "service__max_participants",
    "service__duration",
    "start_time",
)

booking_fields = (
    "schedule__service__slug",
    "schedule__service__name",
    "schedule__service__photo",
    "schedule__service__color",
    "schedule__service__max_participants",
    "schedule__service__duration",
    "schedule__trainer__slug",
    "schedule__trainer__photo",
    "schedule__trainer__user__first_name",
    "schedule__trainer__user__last_name",
    "schedule__trainer__user__middle_name",
    "schedule__start_time",
    "canceled",
)

booking_short_fields = (
    "schedule__service__name",
    "schedule__service__max_participants",
    "schedule__service__duration",
    "schedule__start_time",
    "schedule__trainer__user_id",
    "canceled",
)

client_fields = (
    "client__first_name",
    "client__last_name",
    "client__middle_name",
    "client__email",
    "client__phone_number",
    "client__photo",
    "client__trainer__photo",
    "schedule_id",
    "booked_at",
)

class NotCanceledManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(canceled=False)


class Schedule(models.Model):
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, verbose_name="Услуга"
    )
    trainer = models.ForeignKey(
        Trainer, on_delete=models.CASCADE, verbose_name="Тренер"
    )
    start_time = models.DateTimeField(verbose_name="Время начала")

    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписание"
        ordering = (
            "start_time",
            "service__name",
            "trainer__user__last_name",
            "trainer__user__first_name",
            "trainer__user__middle_name",
        )
        constraints = (
            models.UniqueConstraint(
                fields=("trainer", "start_time"),
                name="unique_trainer_start_time"
            ),
        )

    def __str__(self):
        local_time = timezone.localtime(self.start_time)
        now = timezone.localtime(timezone.now())

        if now.year == local_time.year:
            formatted = date_filter(local_time, "j E в H:i")
        else:
            formatted = date_filter(local_time, "j E Y в H:i")

        return f"{self.service.name} - {formatted}"

    @property
    def bookings_count(self) -> int:
        if hasattr(self, "not_canceled_bookings_count"):
            count = getattr(self, "not_canceled_bookings_count")
        elif hasattr(self, "not_canceled_bookings"):
            count = len(getattr(self, "not_canceled_bookings"))
        else:
            count = 0

        return count

    @property
    def count_remained_seats(self) -> int:
        return self.service.max_participants - self.bookings_count

    @property
    def end_time(self) -> datetime:
        return timezone.localtime(self.start_time + self.service.duration)

    @property
    def is_available(self) -> bool:
        return bool(self.count_remained_seats > 0 and self.in_future)

    def __time_before(self, **kwargs) -> bool:
        now = timezone.now()
        booking_end_time = timezone.localtime(self.start_time) - timedelta(**kwargs)

        return booking_end_time > timezone.localtime(now)

    @property
    def in_future(self) -> bool:
        return self.__time_before()

    @property
    def day_before(self) -> bool:
        return self.__time_before(days=1)


class Booking(models.Model):
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Клиент"
    )
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Занятие",
    )
    booked_at = models.DateTimeField(auto_now_add=True, verbose_name="Время записи")
    canceled = models.BooleanField(default=False, verbose_name="Отменено")

    objects = models.Manager()
    not_canceled = NotCanceledManager()

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        ordering = ("booked_at",)
        constraints = (
            models.UniqueConstraint(
                fields=("schedule", "client"),
                name="unique_schedule_client_booking"
            ),
        )

    def __str__(self):
        return f"{self.schedule} - {self.client}"
