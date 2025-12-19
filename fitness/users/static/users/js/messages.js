function startMessageQueue() {
  const interval = setInterval(function () {
    const first = $(".message").first();

    if (first.length) {
      first.fadeOut(400, function () { $(this).remove(); });
    } else {
      clearInterval(interval);
    }
  }, 5000);
}

function closeMessage() {
  $(".btn-close").click(function () {
    $(this).closest(".message").remove();
  });
}

$(document).ready(function () {
  closeMessage();
  startMessageQueue();
});
