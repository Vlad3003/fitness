from datetime import datetime

from django.utils import timezone
from rest_framework import serializers
from users.serializers import UserShortSerializer

from .models import Booking, Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    booking_id = serializers.SerializerMethodField()
    can_book = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = (
            "id",
            "service_id",
            "trainer_id",
            "start_time",
            "end_time",
            "count_remained_seats",
            "booking_id",
            "can_book",
            "can_cancel",
        )

    @staticmethod
    def get_booking_id(obj: Schedule) -> int | None:
        return getattr(obj, "booking_id", None)

    def get_can_book(self, obj: Schedule) -> bool:
        request = self.context.get("request")

        if request:
            return (
                obj.is_available
                and not getattr(obj, "booking_id", None)
                and request.user != obj.trainer.user
            )

        return False

    @staticmethod
    def get_can_cancel(obj: Schedule) -> bool:
        return bool(getattr(obj, "booking_id", None)) and obj.day_before


class BookedScheduleSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    service_id = serializers.SerializerMethodField()
    trainer_id = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    count_remained_seats = serializers.SerializerMethodField()
    booking_id = serializers.SerializerMethodField()
    can_book = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = (
            "id",
            "service_id",
            "trainer_id",
            "start_time",
            "end_time",
            "count_remained_seats",
            "booking_id",
            "can_book",
            "can_cancel",
        )

    @staticmethod
    def get_id(obj: Booking) -> int:
        return obj.schedule.id

    @staticmethod
    def get_service_id(obj: Booking) -> int:
        return obj.schedule.service.id

    @staticmethod
    def get_trainer_id(obj: Booking) -> int:
        return obj.schedule.trainer.id

    @staticmethod
    def get_start_time(obj: Booking) -> datetime:
        return timezone.localtime(obj.schedule.start_time)

    @staticmethod
    def get_end_time(obj: Booking) -> datetime:
        return obj.schedule.end_time

    @staticmethod
    def get_count_remained_seats(obj: Booking) -> int:
        return obj.schedule.count_remained_seats

    @staticmethod
    def get_booking_id(obj: Booking) -> int | None:
        booking_id = getattr(obj, "id")
        return booking_id if not obj.canceled else None

    @staticmethod
    def get_can_book(obj: Booking) -> bool:
        return obj.schedule.is_available and obj.canceled

    @staticmethod
    def get_can_cancel(obj: Booking) -> bool:
        return not obj.canceled and obj.schedule.day_before


class CreateBookingSerializer(serializers.Serializer):
    schedule_id = serializers.IntegerField(allow_null=False)


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ("id", "schedule_id", "client_id", "booked_at")


class TrainerScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ("id", "service_id", "start_time", "end_time")


class TrainerScheduleResponseSerializer(serializers.Serializer):
    items = TrainerScheduleSerializer(many=True)
    clients = UserShortSerializer(many=True)
    bookings = BookingSerializer(many=True)
