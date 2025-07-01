from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db.models import Prefetch, Count, Q
from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .models import Trainer, Service


def home(request):
    start_date = timezone.localdate(timezone.now()).replace(day=1)
    end_date = start_date + relativedelta(months=1)
    date_range = [start_date, end_date]

    popular_trainers = (
        Trainer.objects.annotate(
            count_distinct_clients=Count(
                "schedule__booking__client",
                filter=Q(schedule__booking__canceled=False)
                & Q(schedule__start_time__date__range=date_range),
                distinct=True,
            ),
            count_clients=Count(
                "schedule__booking__client",
                filter=Q(schedule__booking__canceled=False)
                & Q(schedule__start_time__date__range=date_range),
            ),
        )
        .select_related("user")
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
                "schedule__booking__client",
                filter=Q(schedule__booking__canceled=False)
                & Q(schedule__start_time__date__range=date_range),
                distinct=True,
            ),
            count_clients=Count(
                "schedule__booking__client",
                filter=Q(schedule__booking__canceled=False)
                & Q(schedule__start_time__date__range=date_range),
            ),
        ).order_by("-count_distinct_clients", "-count_clients", "name")
    )[:3]

    context = {
        "title": "Главная",
        "trainers": popular_trainers,
        "services": popular_services,
    }
    return render(request, "core/index.html", context)


class TrainerView(DetailView):
    queryset = Trainer.objects.select_related("user").prefetch_related("services")
    template_name = "core/trainer.html"
    slug_url_kwarg = "trainer_slug"
    context_object_name = "trainer"


class TrainersView(ListView):
    queryset = Trainer.objects.select_related("user")
    template_name = "core/trainers.html"
    context_object_name = "trainers"
    extra_context = {"title": "Наша команда"}


class ServiceView(DetailView):
    queryset = Service.objects.prefetch_related(
        Prefetch("trainers", queryset=Trainer.objects.select_related("user"))
    )
    template_name = "core/service.html"
    slug_url_kwarg = "service_slug"
    context_object_name = "service"


class ServicesView(ListView):
    model = Service
    template_name = "core/services.html"
    context_object_name = "services"
    extra_context = {"title": "Занятия"}
