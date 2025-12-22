from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "trainers/<slug:trainer_slug>/",
        views.TrainerDetailView.as_view(),
        name="trainer",
    ),
    path("trainers/", views.TrainerListView.as_view(), name="trainers"),
    path(
        "services/<slug:service_slug>/",
        views.ServiceDetailView.as_view(),
        name="service",
    ),
    path("services/", views.ServiceListView.as_view(), name="services"),
]
