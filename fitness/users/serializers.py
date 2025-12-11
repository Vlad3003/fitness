from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users.models import User


class TokenSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "Неверное имя пользователя/адрес электронной "
        "почты или пароль. Проверьте правильность ввода."
    }


class UserSerializer(serializers.ModelSerializer):
    trainer_id = serializers.SerializerMethodField()

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
            "date_joined",
            "is_staff",
        )
        read_only_fields = (
            "id",
            "username",
            "email",
            "date_joined",
            "trainer_id",
            "is_staff",
        )

    @staticmethod
    def get_trainer_id(obj: User) -> int | None:
        if hasattr(obj, "trainer"):
            return obj.trainer.id
        return None


class UserShortSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

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
        request = self.context.get("request")
        url = obj.avatar_or_none

        if url:
            return request.build_absolute_uri(url)

        return None

    @staticmethod
    def get_full_name(obj: User) -> str:
        return obj.full_name or obj.username


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
        )
