$(document).ready(function () {
  $(".accordion.closed").each(function () {
    $(this).find(".accordion-body").hide();
  });

  $(".accordion-btn").click(function () {
    const item = $(this).closest(".accordion");
    const itemBody = item.find(".accordion-body");

    itemBody.slideToggle(400);
    item.toggleClass("closed");
  });
});
