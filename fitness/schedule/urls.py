from django.urls import path

from . import views

app_name = "schedule"

urlpatterns = [
    path("", views.schedule_view, name="schedule"),
    path("bookings/", views.BookingListView.as_view(), name="bookings"),
    path(
        "my/",
        views.TrainerScheduleListView.as_view(),
        name="trainer_schedule",
    ),
    path("booking/", views.booking_create_view, name="booking"),
    path("bookings/<int:booking_id>/cancel/", views.booking_cancel_view, name="cancel"),
]
