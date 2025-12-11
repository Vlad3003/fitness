from datetime import timedelta

from django.contrib import admin, messages
from django.db import IntegrityError
from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest

from .models import Booking, Schedule


class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    fields = ("client", "booked_at", "canceled")
    readonly_fields = ("booked_at", "client")
    can_delete = False

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("client", "schedule", "schedule__service")
        )


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    inlines = (BookingInline,)
    list_display = (
        "service",
        "trainer",
        "start_time",
        "service_duration",
        "max_participants",
        "booking_count",
        "count_remained_seats",
    )
    autocomplete_fields = ("service", "trainer")
    date_hierarchy = "start_time"
    readonly_fields = ("booking_count", "count_remained_seats")
    search_fields = ("start_time__gte",)
    list_filter = ("service", "trainer")
    actions = ("duplicate_schedule",)
    save_as = True
    save_on_top = True

    @admin.display(description="Продолжительность (мин)")
    def service_duration(self, schedule: Schedule) -> int:
        return schedule.service.duration_min

    @admin.display(description="Кол-во мест", ordering="service__max_participants")
    def max_participants(self, schedule: Schedule) -> int:
        return schedule.service.max_participants

    @admin.display(description="Записано")
    def booking_count(self, schedule: Schedule) -> int:
        return schedule.booking_count

    @admin.display(description="Свободных мест")
    def count_remained_seats(self, schedule: Schedule) -> int:
        return schedule.count_remained_seats

    def get_queryset(self, request: HttpRequest):
        return (
            super()
            .get_queryset(request)
            .select_related("service", "trainer__user")
            .annotate(
                not_canceled_booking_count=Count("booking", Q(booking__canceled=False))
            )
        )

    @admin.action(description="Создать копию на следующую неделю")
    def duplicate_schedule(self, request: HttpRequest, queryset: QuerySet):
        new_schedule = [
            Schedule(
                service_id=obj.service_id,
                trainer_id=obj.trainer_id,
                start_time=obj.start_time + timedelta(days=7),
            )
            for obj in queryset
        ]

        try:
            Schedule.objects.bulk_create(new_schedule)
            self.message_user(request, f"Добавлено записей - {len(new_schedule)}.")
        except IntegrityError:
            self.message_user(
                request,
                "Найдены дубликаты расписания! Проверьте данные и попробуйте ещё раз!",
                messages.ERROR,
            )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "client_name",
        "service_name",
        "trainer_name",
        "schedule_time",
        "booked_at",
        "canceled",
    )
    list_filter = ("canceled", "schedule__trainer", "schedule__service")
    fieldsets = (
        ("Информация о клиенте", {"fields": ("client",)}),
        ("Детали занятия", {"fields": ("schedule",)}),
        ("Статус и время", {"fields": ("canceled", "booked_at")}),
    )
    readonly_fields = ("client", "schedule", "booked_at")
    date_hierarchy = "booked_at"
    list_editable = ("canceled",)
    search_fields = (
        "client__username",
        "client__first_name",
        "client__last_name",
        "client__middle_name",
    )
    save_on_top = True
    list_per_page = 20
    list_max_show_all = 50

    @admin.display(description="Клиент", ordering="client__last_name")
    def client_name(self, booking: Booking):
        return str(booking.client)

    @admin.display(description="Занятие", ordering="schedule__service__name")
    def service_name(self, booking: Booking):
        return booking.schedule.service

    @admin.display(description="Время занятия", ordering="schedule__start_time")
    def schedule_time(self, booking: Booking):
        return booking.schedule.start_time

    @admin.display(description="Тренер", ordering="schedule__trainer__user__last_name")
    def trainer_name(self, booking: Booking):
        return booking.schedule.trainer

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("client", "schedule__service", "schedule__trainer__user")
        )
