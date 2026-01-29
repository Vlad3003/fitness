from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    CommonPasswordValidator,
    NumericPasswordValidator,
    UserAttributeSimilarityValidator,
    validate_password,
)
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .forms import error_messages

User = get_user_model()


class TokenSerializer(TokenObtainPairSerializer):
    default_error_messages = error_messages["no_active_account"]


class _UserBaseSerializer(serializers.ModelSerializer):
    trainer_id = serializers.SerializerMethodField()
    date_joined_ms = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "middle_name",
            "photo",
            "birth_date",
            "phone_number",
            "gender",
            "trainer_id",
            "date_joined_ms",
            "is_staff",
        )
        read_only_fields = (
            "id",
            "date_joined_ms",
            "is_staff",
        )

    @staticmethod
    def get_trainer_id(obj: User) -> int | None:
        if hasattr(obj, "trainer"):
            return obj.trainer.id
        return None

    @staticmethod
    def get_date_joined_ms(obj: User) -> int:
        return int(obj.date_joined.timestamp()) * 1000


class CreateUserSerializer(_UserBaseSerializer):
    password = serializers.CharField(
        label="Пароль",
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        error_messages=error_messages["min_length"],
    )

    class Meta(_UserBaseSerializer.Meta):
        fields = _UserBaseSerializer.Meta.fields + ("password",)
        read_only_fields = _UserBaseSerializer.Meta.read_only_fields + (
            "middle_name",
            "photo",
            "birth_date",
            "phone_number",
            "gender",
        )

    def validate(self, attrs):
        temp_user = User(
            username=attrs["username"],
            email=attrs["email"],
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
        )
        validators = (
            UserAttributeSimilarityValidator(),
            CommonPasswordValidator(),
            NumericPasswordValidator(),
        )

        try:
            validate_password(attrs["password"], temp_user, validators)
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(_UserBaseSerializer):
    class Meta(_UserBaseSerializer.Meta):
        read_only_fields = _UserBaseSerializer.Meta.read_only_fields + (
            "username",
            "email",
        )


class UserShortSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()
    full_name = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "full_name",
            "email",
            "phone_number",
            "photo",
        )

    def get_photo(self, obj: User) -> str | None:
        request = self.context["request"]
        url = obj.avatar_or_none

        if url:
            return request.build_absolute_uri(url)

        return None
