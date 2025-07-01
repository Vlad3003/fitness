from django.contrib.auth import get_user_model
from django.db import models

from datetime import date

from django.urls import reverse

User = get_user_model()


class Trainer(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    slug = models.SlugField(
        max_length=100, unique=True, db_index=True, verbose_name="Slug"
    )
    specialization = models.TextField(
        blank=True, null=True, verbose_name="Специализация"
    )
    achievements = models.TextField(blank=True, null=True, verbose_name="Достижения")
    experience_since = models.DateField(blank=True, null=True, verbose_name="Стаж с")
    photo = models.ImageField(
        upload_to="trainers/", blank=True, null=True, verbose_name="Фото"
    )

    class Meta:
        verbose_name = "Тренер"
        verbose_name_plural = "Тренеры"
        ordering = ("user__last_name", "user__first_name", "user__middle_name")

    def __str__(self) -> str:
        return str(self.user)

    @property
    def experience_years(self) -> str:
        years = (date.today() - self.experience_since).days // 365

        if not years:
            return ""

        if years % 10 == 1 and years % 100 != 11:
            word = "год"
        elif years % 10 in (2, 3, 4) and years % 100 not in (12, 13, 14):
            word = "года"
        else:
            word = "лет"

        return f"{years} {word}"

    @property
    def specialization_list(self) -> list[str]:
        return self.specialization.split("\n")

    @property
    def achievements_list(self) -> list[str]:
        if self.achievements:
            return self.achievements.split("\n")
        return []

    def get_absolute_url(self):
        return reverse("trainer", kwargs={"trainer_slug": self.slug})


class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(
        max_length=200, db_index=True, unique=True, verbose_name="Slug"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    duration = models.DurationField(
        verbose_name="Продолжительность",
        help_text="Укажите продолжительность в секундах или в формате 'ЧЧ:ММ:СС'",
    )
    price = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Стоимость"
    )
    photo = models.ImageField(
        upload_to="services/", blank=True, null=True, verbose_name="Фото"
    )
    trainers = models.ManyToManyField(
        Trainer, blank=True, related_name="services", verbose_name="Тренеры"
    )
    max_participants = models.PositiveIntegerField(
        default=10, null=False, blank=False, verbose_name="Кол-во мест"
    )

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    @property
    def duration_minutes(self) -> int:
        if self.duration:
            return int(self.duration.total_seconds()) // 60
        return 0

    def get_absolute_url(self):
        return reverse("service", kwargs={"service_slug": self.slug})
