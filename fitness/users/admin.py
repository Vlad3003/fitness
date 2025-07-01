from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.safestring import mark_safe

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "phone_number",
        "full_name",
        "is_staff",
        "is_active",
    )
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Персональная информация",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "middle_name",
                    "email",
                    "phone_number",
                    "birth_date",
                    "gender",
                    "avatar",
                )
            },
        ),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Важные даты", {"fields": ("date_joined", "last_login")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
        (
            "Персональная информация",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "middle_name",
                    "email",
                    "phone_number",
                    "birth_date",
                    "gender",
                    "photo",
                )
            },
        ),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "gender", "groups")
    search_fields = (
        "username",
        "email",
        "phone_number",
        "first_name",
        "last_name",
        "middle_name",
    )
    readonly_fields = ("avatar", "date_joined", "last_login")
    actions = ("set_is_active", "set_is_inactive")
    save_on_top = True
    list_per_page = 20
    list_max_show_all = 50

    class Media:
        js = (
            "js/jquery-3.7.1.min.js",
            "js/jquery.inputmask.min.js",
            "users/js/phone-mask.js",
        )

    @admin.display(description="ФИО", ordering="last_name", empty_value="-")
    def full_name(self, user: User) -> str:
        return user.full_name

    @admin.display(description="Фотография")
    def avatar(self, user: User):
        if user.photo:
            return mark_safe(f'<img src="{user.photo.url}" width=300>')
        return "-"

    @admin.action(description="Сделать активными")
    def set_is_active(self, request: HttpRequest, queryset: QuerySet) -> None:
        count = queryset.update(is_active=True)
        self.message_user(request, f"Количество изменённых записей: {count}")

    @admin.action(description="Сделать неактивными")
    def set_is_inactive(self, request: HttpRequest, queryset: QuerySet) -> None:
        count = queryset.update(is_active=False)
        self.message_user(
            request, f"Количество изменённых записей: {count}", messages.WARNING
        )
