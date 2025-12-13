from django.urls import path

from . import views

app_name = "schedule"

urlpatterns = [
    path("", views.schedule_view, name="schedule"),
    path("booking/", views.booking_view, name="booking"),
    path("bookings/<int:booking_id>/cancel/", views.booking_cancel_view, name="cancel"),
]
