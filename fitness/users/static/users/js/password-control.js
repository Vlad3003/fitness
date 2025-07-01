$(document).ready(function () {
  $(".password-control").click(function () {
    const el = $(this).find("i");
    const input = $(this).closest(".form-floating").find("input");

    if (input.attr("type") == "password") {
      input.attr("type", "text");
      el.removeClass("bi-eye-fill");
      el.addClass("bi-eye-slash-fill");
    } else {
      input.attr("type", "password");
      el.removeClass("bi-eye-slash-fill");
      el.addClass("bi-eye-fill");
    }
  });
});
