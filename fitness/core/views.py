from dateutil.relativedelta import relativedelta
from django.db.models import Count, Prefetch, Q
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import DetailView, ListView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import (
    Service,
    Trainer,
    service_detail_fields,
    service_short_fields,
    trainer_detail_fields,
    trainer_short_fields,
)
from .serializers import ServiceSerializer, TrainerSerializer


def home(request):
    start_date = timezone.localdate(timezone.now()).replace(day=1)
    end_date = start_date + relativedelta(months=1)
    date_range = (start_date, end_date)

    popular_trainers = (
        Trainer.objects.annotate(
            count_distinct_clients=Count(
                "schedule__bookings__client",
                filter=Q(schedule__bookings__canceled=False)
                & Q(schedule__start_time__date__range=date_range),
                distinct=True,
            ),
            count_clients=Count(
                "schedule__bookings__client",
                filter=Q(schedule__bookings__canceled=False)
                & Q(schedule__start_time__date__range=date_range),
            ),
        )
        .filter(count_distinct_clients__gt=0, count_clients__gt=0)
        .select_related("user")
        .only("slug", *trainer_short_fields)
        .order_by(
            "-count_distinct_clients",
            "-count_clients",
            "user__last_name",
            "user__first_name",
            "user__middle_name",
        )
    )[:3]

    popular_services = (
        Service.objects.annotate(
            count_distinct_clients=Count(
                "schedule__bookings__client",
                filter=Q(schedule__bookings__canceled=False)
                & Q(schedule__start_time__date__range=date_range),
                distinct=True,
            ),
            count_clients=Count(
                "schedule__bookings__client",
                filter=Q(schedule__bookings__canceled=False)
                & Q(schedule__start_time__date__range=date_range),
            ),
        )
        .filter(count_distinct_clients__gt=0, count_clients__gt=0)
        .only("slug", *service_short_fields)
        .order_by("-count_distinct_clients", "-count_clients", "name")
    )[:3]

    context = {
        "title": "Главная",
        "trainers": popular_trainers,
        "services": popular_services,
    }
    return render(request, "core/index.html", context)


class TrainerDetailView(DetailView):
    queryset = (
        Trainer.objects.select_related("user")
        .prefetch_related(
            Prefetch(
                "services",
                queryset=Service.objects.only("slug", *service_short_fields)
            )
        )
        .only(*trainer_detail_fields)
    )
    template_name = "core/trainer.html"
    slug_url_kwarg = "trainer_slug"
    context_object_name = "trainer"


class TrainerListView(ListView):
    queryset = Trainer.objects.select_related("user").only(
        "slug", *trainer_short_fields
    )
    template_name = "core/trainers.html"
    context_object_name = "trainers"
    extra_context = {"title": "Наша команда"}


class ServiceDetailView(DetailView):
    queryset = Service.objects.prefetch_related(
        Prefetch(
            "trainers",
            queryset=Trainer.objects.select_related("user").only(
                "slug", *trainer_short_fields
            ),
        )
    ).only(*service_detail_fields)
    template_name = "core/service.html"
    slug_url_kwarg = "service_slug"
    context_object_name = "service"


class ServiceListView(ListView):
    queryset = Service.objects.only("slug", *service_short_fields)
    template_name = "core/services.html"
    context_object_name = "services"
    extra_context = {"title": "Занятия"}


class TrainerListAPIView(ListAPIView):
    queryset = (
        Trainer.objects.select_related("user")
        .only(*trainer_detail_fields)
        .order_by("id")
    )
    serializer_class = TrainerSerializer
    permission_classes = (IsAuthenticated,)


class ServiceListAPIView(ListAPIView):
    queryset = Service.objects.prefetch_related(
        Prefetch("trainers", queryset=Trainer.objects.only("id"))
    ).order_by("id")
    serializer_class = ServiceSerializer
    permission_classes = (IsAuthenticated,)
