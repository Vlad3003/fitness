from itertools import groupby

from core.models import Trainer
from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.views import PasswordResetConfirmView as PswResetConfirmView
from django.contrib.auth.views import PasswordResetView as PswResetView
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.db.models.functions import TruncDate
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from schedule.models import Booking, Schedule

from .forms import (
    LoginUserForm,
    PasswordResetForm,
    RegisterUserForm,
    SetPasswordForm,
    UpdateUserForm,
    UserPasswordChangeForm,
)


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = "users/login.html"
    redirect_authenticated_user = True
    extra_context = {"title": "Вход в профиль"}


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")
    extra_context = {"title": "Регистрация"}

    def form_valid(self, form):
        messages.success(self.request, "Вы успешно зарегистрировались.")
        return super().form_valid(form)


class PasswordResetView(PswResetView):
    form_class = PasswordResetForm
    template_name = "users/password_reset_form.html"
    email_template_name = "users/password_reset_email.html"
    success_url = reverse_lazy("users:password_reset")
    extra_context = {"title": "Восстановление пароля"}

    def form_valid(self, form):
        messages.success(
            self.request,
            "Мы отправили вам инструкцию по установке "
            "нового пароля на указанный адрес электронной почты. "
            "Вы должны получить её в ближайшее время.",
        )
        return super().form_valid(form)


class PasswordResetConfirmView(PswResetConfirmView):
    form_class = SetPasswordForm
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("users:login")
    extra_context = {"title": "Новый пароль"}

    def form_valid(self, form):
        messages.success(
            self.request, "Поздравляем! Вы успешно изменили пароль от своего аккаунта."
        )
        return super().form_valid(form)


class UserPasswordChange(PasswordChangeView):
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy("users:login")
    template_name = "users/password_change_form.html"
    extra_context = {"title": "Изменение пароля"}

    def form_valid(self, form):
        logout(self.request)
        messages.success(self.request, "Вы успешно изменили пароль.")
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"
    extra_context = {"title": "Профиль"}


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UpdateUserForm
    template_name = "users/profile_edit.html"
    user_photo = None
    success_url = reverse_lazy("users:profile_edit")
    extra_context = {"title": "Редактирование профиля"}

    def get_object(self, queryset=None):
        self.user_photo = self.request.user.photo
        return self.request.user

    def form_valid(self, form):
        if form.has_changed():
            messages.success(
                self.request, "Ваши данные профиля были успешно обновлены."
            )

        return super().form_valid(form)

    def form_invalid(self, form):
        if "photo" in form.changed_data:
            form.instance.photo = self.user_photo
        return super().form_invalid(form)


@login_required
def delete_user(request: HttpRequest):
    if request.method == "POST":
        request.user.is_active = False
        request.user.save()
        logout(request)
        messages.success(
            request, "Ваш аккаунт был успешно удалён. Спасибо, что были с нами!"
        )
        return redirect(reverse("users:login"))
    return HttpResponse(status=405)


@login_required
def delete_user_photo(request: HttpRequest):
    if request.method == "POST":
        request.user.photo.delete()
        messages.success(request, "Ваша фотография была успешно удалена.")
        return redirect(reverse("users:profile_edit"))
    return HttpResponse(status=405)


class ClassesListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = "users/classes.html"
    extra_context = {"title": "Мои занятия"}
    paginate_by = 10

    def get_queryset(self):
        return (
            Booking.objects.filter(client=self.request.user)
            .select_related(
                "schedule",
                "schedule__service",
                "schedule__trainer",
                "schedule__trainer__user",
            )
            .prefetch_related(
                Prefetch(
                    "schedule__booking",
                    queryset=Booking.not_canceled.all(),
                    to_attr="not_canceled_booking"
                )
            )
            .annotate(date=TruncDate("schedule__start_time"))
            .order_by("-date", "schedule__start_time__time")
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        grouped = []

        for key, group in groupby(
            context["object_list"], lambda item: getattr(item, "date")
        ):
            grouped.append({"date": key, "items": list(group)})

        context["classes"] = grouped
        return context


class TrainerClassesListView(LoginRequiredMixin, ListView):
    model = Booking
    context_object_name = "classes"
    template_name = "users/trainer_classes.html"
    extra_context = {"title": "Мои тренировки"}
    paginate_by = 20
    trainer = None

    def get_queryset(self):
        self.trainer = Trainer.objects.filter(user__pk=self.request.user.pk).first()

        if not self.trainer:
            raise PermissionDenied("У вас нет доступа к этой странице")

        return (
            Schedule.objects.filter(trainer=self.trainer)
            .select_related("service")
            .prefetch_related(
                Prefetch(
                    "booking",
                    Booking.not_canceled.select_related("client").all(),
                    to_attr="active_booking",
                )
            )
            .annotate(date=TruncDate("start_time"))
            .order_by("-date", "start_time__time")
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        grouped = []

        for key, group in groupby(
            context["object_list"], lambda item: getattr(item, "date")
        ):
            grouped.append({"date": key, "items": list(group)})

        context["classes"] = grouped
        return context
