from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("trainers/<slug:trainer_slug>/", views.TrainerView.as_view(), name="trainer"),
    path("trainers/", views.TrainersView.as_view(), name="trainers"),
    path("services/<slug:service_slug>/", views.ServiceView.as_view(), name="service"),
    path("services/", views.ServicesView.as_view(), name="services"),
]
