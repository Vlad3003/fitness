from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from fitness.settings import DEFAULT_USER_IMAGE

phone_validator = RegexValidator(
    regex=r"^\+7 \(\d{3}\) \d{3} \d{2}-\d{2}$",
    message="Телефон должен быть в формате '+7 (777) 777 77-77'",
)


class User(AbstractUser):
    photo = models.ImageField(
        upload_to="users/%Y/%m/%d/", blank=True, null=True, verbose_name="Фотография"
    )
    middle_name = models.CharField(blank=True, null=True, verbose_name="Отчество")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Дата рождения")
    phone_number = models.CharField(
        blank=True,
        null=True,
        verbose_name="Номер телефона",
        max_length=18,
        validators=(phone_validator,),
        unique=True,
        error_messages={
            "unique": "Пользователь с таким номером телефона уже существует."
        },
    )
    gender = models.CharField(
        blank=True,
        null=True,
        verbose_name="Пол",
        max_length=1,
        choices=[
            ("М", "Мужской"),
            ("Ж", "Женский"),
        ],
    )

    @property
    def avatar(self) -> str:
        return self.avatar_or_none or DEFAULT_USER_IMAGE

    @property
    def avatar_or_none(self) -> str | None:
        if self.photo and hasattr(self.photo, "url"):
            return self.photo.url
        if (
            hasattr(self, "trainer")
            and self.trainer.photo
            and hasattr(self.trainer.photo, "url")
        ):
            return self.trainer.photo.url
        return None

    @property
    def full_name(self) -> str:
        _full_name = f"{self.last_name} {self.first_name} {self.middle_name}"
        return _full_name.replace("None", "").strip()

    def __str__(self) -> str:
        return self.full_name or self.username
