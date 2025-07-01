from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.template.defaultfilters import date as date_filter
from django.utils import timezone

from core.models import Trainer, Service

User = get_user_model()


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
    start_time = models.DateTimeField(
        blank=False, null=False, verbose_name="Время начала"
    )

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
        unique_together = ("trainer", "start_time")

    def __str__(self):
        local_time = timezone.localtime(self.start_time)
        now = timezone.localtime(timezone.now())

        if now.year == local_time.year:
            formatted = date_filter(local_time, "j E H:i")
        else:
            formatted = date_filter(local_time, "j E Y H:i")

        return f"{self.service.name} - {formatted}"

    @property
    def booking_count(self) -> int:
        return getattr(self, "not_canceled_booking_count", 0)

    @property
    def count_remained_seats(self) -> int:
        return self.service.max_participants - self.booking_count

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
    client = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Клиент")
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name="booking",
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
        unique_together = ("schedule", "client")

    def __str__(self):
        return f"{self.schedule} - {self.client}"
