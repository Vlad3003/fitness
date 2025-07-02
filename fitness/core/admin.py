from django.contrib import admin
from django.utils.safestring import mark_safe

from .forms import ServiceAdminForm
from .models import Service, Trainer


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ("username", "full_name", "email", "phone_number", "photo_preview")
    autocomplete_fields = ("user",)
    readonly_fields = ("photo_preview",)
    fieldsets = (
        ("Пользователь", {"fields": ("user",)}),
        (None, {"fields": ("slug",)}),
        (
            "Основная информация",
            {
                "fields": (
                    "specialization",
                    "achievements",
                    "experience_since",
                )
            },
        ),
        ("Медиа", {"fields": ("photo", "photo_preview")}),
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__phone_number",
        "user__first_name",
        "user__last_name",
        "user__middle_name",
    )
    search_help_text = "Поиск по: логину, email, телефону, имени, фамилии, отчеству"
    save_on_top = True
    list_per_page = 20
    list_max_show_all = 50

    @admin.display(description="Имя пользователя", ordering="user__username")
    def username(self, trainer: Trainer) -> str:
        return trainer.user.username

    @admin.display(description="Адрес электронной почты", ordering="user__email")
    def email(self, trainer: Trainer) -> str:
        return trainer.user.email

    @admin.display(
        description="Номер телефона", ordering="user__phone_number", empty_value="-"
    )
    def phone_number(self, trainer: Trainer) -> str:
        return trainer.user.phone_number

    @admin.display(description="ФИО", ordering="user__last_name", empty_value="-")
    def full_name(self, trainer: Trainer) -> str:
        return trainer.user.full_name

    @admin.display(description="Фотография")
    def photo_preview(self, trainer: Trainer):
        if trainer.photo:
            return mark_safe(f'<img src="{trainer.photo.url}" width="300">')
        return "-"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    form = ServiceAdminForm
    list_display = (
        "name",
        "duration_minutes",
        "price",
        "photo_preview",
        "trainer_count",
        "max_participants",
        "color_preview",
    )
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("photo_preview",)
    fieldsets = (
        (None, {"fields": ("name", "slug", "description", "color")}),
        (
            "Стоимость, длительность, количество мест",
            {"fields": ("price", "duration", "max_participants")},
        ),
        ("Медиа", {"fields": ("photo", "photo_preview")}),
        ("Тренеры", {"fields": ("trainers",)}),
    )
    list_editable = ("price", "max_participants")
    search_fields = (
        "name",
        "price",
    )
    filter_horizontal = ("trainers",)
    save_on_top = True
    list_per_page = 20
    list_max_show_all = 50

    @admin.display(description="Фотография")
    def photo_preview(self, service: Service):
        if service.photo:
            return mark_safe(f'<img src="{service.photo.url}" width="200">')
        return "-"

    @admin.display(
        description="Продолжительность (мин)", ordering="duration", empty_value="-"
    )
    def duration_minutes(self, service: Service):
        return service.duration_minutes

    @admin.display(description="Кол-во тренеров")
    def trainer_count(self, service: Service):
        return service.trainers.count()

    @admin.display(description="Цвет", ordering="color")
    def color_preview(self, service: Service):
        return mark_safe(
            f'<div style="width: 40px; height: 20px; background-color: {service.color}"></div>'
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("trainers")
