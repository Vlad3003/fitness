$(document).ready(function () {
  const dayBtns = $('input[name="day"]');

  dayBtns.on("change", function () {
    const date = $(this).val();
    $(".schedule__list_active").removeClass("schedule__list_active");

    if ($(`.schedule__list[data-date="${date}"]`).length) {
      $(`.schedule__list[data-date="${date}"]`).addClass("schedule__list_active");
      $("#schedule_empty").removeClass("active");
    } else {
      $("#schedule_empty").addClass("active");
    }
  });

  $("#scheduleModal").on("show.bs.modal", function (event) {
    const item = $(event.relatedTarget).closest(".schedule__item");
    const modal = $(this);

    const service = {
      name: item.find(".schedule__name").text(),
      photo: item.data("service-photo"),
      url: item.data("service-url")
    };

    const trainer = {
      name: item.find(".schedule__trainer").text(),
      photo: item.data("trainer-photo"),
      url: item.data("trainer-url")
    };

    const schedule = {
      date: item.data("date"),
      id: item.data("schedule-id"),
      available: item.data("available"),
      isBooked: item.data("is-booked"),
      canCancel: item.data("can-cancel")
    }

    modal.find("#modal-title").attr("data-color", item.data("color"))
      .find("a").text(service.name).attr("href", service.url);

    modal.find("#modal-date").text(schedule.date);
    modal.find("#modal-time-range").html(item.find(".schedule-time-range").html());
    modal.find("#modal-time-duration").html(item.find(".schedule-time-duration").html());

    modal.find("#modal-service-img")
      .attr({ src: service.photo, alt: service.name })
      .show();

    modal.find("#modal-trainer-img")
      .attr({ src: trainer.photo, alt: trainer.name })
      .show();

    modal.find("#modal-trainer-link").attr("href", trainer.url).text(trainer.name);

    modal.find("#scheduleId").val(schedule.id);

    const modalForm = modal.find("#modalForm");
    const bookingBtn = modal.find("#bookingBtn");
    const cancelBtn = modal.find("#cancelBtn");

    bookingBtn.toggle(schedule.available && !schedule.isBooked);
    cancelBtn.toggle(schedule.canCancel);

    if (schedule.canCancel) {
      modalForm.attr("action", modalForm.data("cancel-url"));
    } else if (schedule.available) {
      modalForm.attr("action", modalForm.data("booking-url"));
    }
  });
});
