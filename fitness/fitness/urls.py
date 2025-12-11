"""
URL configuration for fitness project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenBlacklistView,
)

from core.views import TrainerListAPIView, ServiceListAPIView
from schedule.views import (
    ScheduleAPIView,
    BookedScheduleAPIView,
    ScheduleBookingAPIView,
    BookingCancelAPIView,
    TrainerScheduleListAPIView,
)
from fitness import settings
from users.views import (
    TokensObtainView,
    UserApiView,
    DeleteUserPhotoView,
    CreateUserApiView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("users/", include("users.urls", namespace="users")),
    path("schedule/", include("schedule.urls", namespace="schedule")),
    path("__debug__/", include("debug_toolbar.urls")),

    path("api/trainers/", TrainerListAPIView.as_view()),
    path("api/services/", ServiceListAPIView.as_view()),
    path("api/schedule/", ScheduleAPIView.as_view()),
    path("api/schedule/booked/", BookedScheduleAPIView.as_view()),
    path("api/schedule/booked/cancel/", BookingCancelAPIView.as_view()),
    path("api/schedule/booking/", ScheduleBookingAPIView.as_view()),
    path("api/trainer/schedule/", TrainerScheduleListAPIView.as_view()),
    path("api/users/", CreateUserApiView.as_view()),
    path("api/users/me/", UserApiView.as_view()),
    path("api/users/me/photo/", DeleteUserPhotoView.as_view()),
    path("api/token/", TokensObtainView.as_view(), name="tokens_obtain"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Панель администрирования"
admin.site.index_title = "FitPro"
