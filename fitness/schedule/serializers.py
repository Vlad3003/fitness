from rest_framework import serializers
from users.serializers import UserShortSerializer

from .models import Booking, Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(allow_null=True, read_only=True)
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
        read_only_fields = ("start_time",)

    def get_can_book(self, obj: Schedule) -> bool:
        request = self.context["request"]

        return bool(
            obj.is_available
            and not getattr(obj, "booking_id", None)
            and request.user.pk != obj.trainer.user_id
        )

    @staticmethod
    def get_can_cancel(obj: Schedule) -> bool:
        return bool(getattr(obj, "booking_id", None)) and obj.day_before


class BookedScheduleSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="schedule_id", read_only=True)
    service_id = serializers.IntegerField(source="schedule.service_id", read_only=True)
    trainer_id = serializers.IntegerField(source="schedule.trainer_id", read_only=True)
    start_time = serializers.DateTimeField(source="schedule.start_time", read_only=True)
    end_time = serializers.DateTimeField(source="schedule.end_time", read_only=True)
    count_remained_seats = serializers.IntegerField(
        source="schedule.count_remained_seats", read_only=True
    )
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
