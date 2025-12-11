from datetime import datetime

from django.utils import timezone
from rest_framework import serializers
from users.serializers import UserShortSerializer

from .models import Booking, Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    is_user_booked = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
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
            "is_available",
            "is_user_booked",
            "can_cancel",
        )

    @staticmethod
    def get_is_user_booked(obj: Schedule) -> bool:
        return getattr(obj, "is_user_booked", False)

    def get_is_available(self, obj: Schedule) -> bool:
        request = self.context.get("request")

        if request:
            return obj.is_available and request.user.id != obj.trainer.user.id

        return False

    @staticmethod
    def get_can_cancel(obj: Schedule) -> bool:
        return getattr(obj, "is_user_booked", False) and obj.day_before


class BookedScheduleSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    service_id = serializers.SerializerMethodField()
    trainer_id = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    count_remained_seats = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    is_user_booked = serializers.SerializerMethodField()
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
            "is_available",
            "is_user_booked",
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
    def get_is_user_booked(obj: Booking) -> bool:
        return not obj.canceled

    @staticmethod
    def get_is_available(obj: Booking) -> bool:
        return obj.schedule.is_available

    @staticmethod
    def get_can_cancel(obj: Booking) -> bool:
        return not obj.canceled and obj.schedule.day_before


class ScheduleBookingSerializer(serializers.Serializer):
    schedule_id = serializers.IntegerField(allow_null=False)


class BookingSerializer(serializers.ModelSerializer):
    client = UserShortSerializer()

    class Meta:
        model = Booking
        fields = ("id", "client", "booked_at")


class TrainerScheduleSerializer(serializers.ModelSerializer):
    active_bookings = BookingSerializer(many=True)

    class Meta:
        model = Schedule
        fields = (
            "id",
            "service_id",
            "start_time",
            "end_time",
            "active_bookings",
        )
