from rest_framework import serializers

from .models import Service, Trainer


class TrainerSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="__str__", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)

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
