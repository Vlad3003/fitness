from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as LognView
from django.contrib.auth.views import PasswordChangeView as PswChangeView
from django.contrib.auth.views import PasswordResetConfirmView as PswResetConfirmView
from django.contrib.auth.views import PasswordResetView as PswResetView
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView
from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .forms import (
    LoginForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreateForm,
    UserUpdateForm,
)
from .serializers import CreateUserSerializer, TokenSerializer, UserSerializer

User = get_user_model()


class LoginView(LognView):
    form_class = LoginForm
    template_name = "users/login.html"
    redirect_authenticated_user = True
    extra_context = {"title": "Вход в профиль"}


class UserCreateView(CreateView):
    form_class = UserCreateForm
    template_name = "users/register.html"
    success_url = reverse_lazy("home")
    extra_context = {"title": "Регистрация"}

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        messages.success(self.request, "Вы успешно зарегистрировались")
        return HttpResponseRedirect(self.get_success_url())


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


class PasswordChangeView(PswChangeView):
    form_class = PasswordChangeForm
    success_url = reverse_lazy("users:login")
    template_name = "users/password_change_form.html"
    extra_context = {"title": "Изменение пароля"}

    def form_valid(self, form):
        logout(self.request)
        messages.success(self.request, "Вы успешно изменили пароль")
        return super().form_valid(form)


class UserDetailView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"
    extra_context = {"title": "Профиль"}


class UserUpdateView(LoginRequiredMixin, UpdateView):
    form_class = UserUpdateForm
    template_name = "users/profile_edit.html"
    user_photo = None
    success_url = reverse_lazy("users:profile_edit")
    extra_context = {"title": "Редактирование профиля"}

    def get_object(self, queryset=None):
        self.user_photo = self.request.user.photo
        return self.request.user

    def form_valid(self, form):
        if form.has_changed():
            messages.success(self.request, "Ваши данные профиля были успешно обновлены")

        return super().form_valid(form)

    def form_invalid(self, form):
        if "photo" in form.changed_data:
            form.instance.photo = self.user_photo
        return super().form_invalid(form)


def delete_user(user: User) -> dict[str, bool | str]:
    user.is_active = False
    user.save()
    return {
        "success": True,
        "message": "Ваш аккаунт был успешно удалён. Спасибо, что были с нами!",
    }


@login_required
def user_delete_view(request: HttpRequest):
    if request.method == "POST":
        result = delete_user(request.user)
        logout(request)
        messages.success(request, result["message"])
        return redirect(reverse("users:login"))
    return HttpResponse(status=405)


def delete_user_photo(user: User) -> dict[str, bool | str]:
    result: dict[str, bool | str] = {"success": False, "message": ""}

    if user.photo:
        user.photo.delete()
        user.save()
        result["message"] = "Ваша фотография была успешно удалена"
        result["success"] = True
    else:
        result["message"] = "У вас пока нет фотографии профиля"

    return result


@login_required
def user_photo_delete_view(request: HttpRequest):
    if request.method == "POST":
        res = delete_user_photo(request.user)
        message = res["message"]

        if res["success"]:
            messages.success(request, message)
        else:
            messages.error(request, message)

        return redirect(reverse("users:profile_edit"))
    return HttpResponse(status=405)


class TokensObtainView(TokenObtainPairView):
    serializer_class = TokenSerializer


class UserAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        delete_user(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CreateUserAPIView(GenericAPIView):
    serializer_class = CreateUserSerializer
    permission_classes = ()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": serializer.data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class DeleteUserPhotoAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def delete(request: HttpRequest):
        result = delete_user_photo(request.user)
        result["user"] = UserSerializer(request.user).data

        return Response(result, status=status.HTTP_200_OK)
