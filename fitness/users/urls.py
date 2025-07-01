from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("login/", views.LoginUser.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", views.RegisterUser.as_view(), name="register"),
    path("delete/", views.delete_user, name="delete"),
    path("password-reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileEditView.as_view(), name="profile_edit"),
    path("delete-photo/", views.delete_user_photo, name="delete-photo"),
    path(
        "password-change/", views.UserPasswordChange.as_view(), name="password_change"
    ),
    path("classes/", views.ClassesListView.as_view(), name="classes"),
    path(
        "trainer/classes/",
        views.TrainerClassesListView.as_view(),
        name="trainer_classes",
    ),
]
