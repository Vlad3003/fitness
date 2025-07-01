$(document).ready(function () {
  $(".btn-close").click(function () {
    $(this).closest(".message").remove();
  });
});
