from rest_framework import serializers

from .models import Service, Trainer


class TrainerSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = Trainer
        fields = (
            "id",
            "full_name",
            "email",
            "phone_number",
            "specialization",
            "achievements",
            "experience",
            "photo",
        )

    @staticmethod
    def get_full_name(obj: Trainer) -> str:
        return str(obj)

    @staticmethod
    def get_email(obj: Trainer) -> str:
        return obj.user.email

    @staticmethod
    def get_phone_number(obj: Trainer) -> str | None:
        return obj.user.phone_number


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = (
            "id",
            "name",
            "description",
            "duration_min",
            "photo",
            "color",
            "max_participants",
            "trainers",
        )
