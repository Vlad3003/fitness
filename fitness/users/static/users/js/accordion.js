$(document).ready(function () {
  $(".accordion-btn").click(function () {
    const item = $(this).closest(".accordion");
    $(this).toggleClass("closed");
    item.find(".accordion-body").slideToggle(400);
  });
});
