from django.urls import path

from . import views

app_name = "schedule"

urlpatterns = [
    path("", views.schedule, name="schedule"),
    path("booking/", views.booking, name="booking"),
    path("cancel/", views.cancel, name="cancel"),
]
