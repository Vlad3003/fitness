from itertools import groupby

from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.views import PasswordResetConfirmView as PswResetConfirmView
from django.contrib.auth.views import PasswordResetView as PswResetView
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from schedule.models import Booking
from schedule.views import get_booked_schedule, get_trainer_schedule

from .forms import (
    LoginUserForm,
    PasswordResetForm,
    RegisterUserForm,
    SetPasswordForm,
    UpdateUserForm,
    UserPasswordChangeForm,
)
from .serializers import CreateUserSerializer, TokenSerializer, UserSerializer


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


def delete_user(request: HttpRequest) -> dict[str, bool | str]:
    request.user.is_active = False
    request.user.save()
    return {
        "success": True,
        "message": "Ваш аккаунт был успешно удалён. Спасибо, что были с нами!",
    }


@login_required
def delete_user_view(request: HttpRequest):
    if request.method == "POST":
        result = delete_user(request)
        logout(request)
        messages.success(request, result["message"])
        return redirect(reverse("users:login"))
    return HttpResponse(status=405)


def delete_user_photo(request: HttpRequest) -> dict[str, bool | str]:
    result: dict[str, bool | str] = {"success": False, "message": ""}

    if request.user.photo:
        request.user.photo.delete()
        request.user.save()
        result["message"] = "Ваша фотография была успешно удалена."
        result["success"] = True
    else:
        result["message"] = "У вас пока нет фотографии профиля"

    return result


@login_required
def delete_user_photo_view(request: HttpRequest):
    if request.method == "POST":
        res = delete_user_photo(request)
        message = res["message"]

        if res["success"]:
            messages.success(request, message)
        else:
            messages.error(request, message)

        return redirect(reverse("users:profile_edit"))
    return HttpResponse(status=405)


class ClassesListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = "users/classes.html"
    extra_context = {"title": "Мои занятия"}
    paginate_by = 10

    def get_queryset(self):
        return get_booked_schedule(self.request)

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

    def get_queryset(self):
        if not hasattr(self.request.user, "trainer"):
            raise PermissionDenied("У вас нет доступа к этой странице")

        return get_trainer_schedule(self.request.user.trainer)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        grouped = []

        for key, group in groupby(
            context["object_list"], lambda item: getattr(item, "date")
        ):
            grouped.append({"date": key, "items": list(group)})

        context["classes"] = grouped
        return context


class TokensObtainView(TokenObtainPairView):
    serializer_class = TokenSerializer


class UserApiView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        delete_user(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CreateUserApiView(CreateAPIView):
    serializer_class = CreateUserSerializer


class DeleteUserPhotoView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def delete(request: HttpRequest):
        result = delete_user_photo(request)
        result["user"] = UserSerializer(request.user).data

        return Response(result, status=status.HTTP_200_OK)
