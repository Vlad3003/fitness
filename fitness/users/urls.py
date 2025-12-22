from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", views.UserCreateView.as_view(), name="register"),
    path("delete/", views.user_delete_view, name="delete"),
    path("password-reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("profile/", views.UserDetailView.as_view(), name="profile"),
    path("profile/edit/", views.UserUpdateView.as_view(), name="profile_edit"),
    path("delete-photo/", views.user_photo_delete_view, name="delete-photo"),
    path(
        "password-change/", views.PasswordChangeView.as_view(), name="password_change"
    ),
]
