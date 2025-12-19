$(document).ready(function () {
  $("#id_photo").on("change", function () {
    const file = this.files[0];

    if (file && file.type.startsWith("image/")) {
      $(this).removeClass("is-invalid");
      const reader = new FileReader();

      reader.onload = function (e) {
        const res = e.target.result;
        $("#img-preview").attr("src", res).show();
        $("#modalImg").attr("src", res).show();
      };

      reader.readAsDataURL(file);
    } else {
      $(this).val("");
      $(this).addClass("is-invalid");

      const error = `
      <div class="message error shadow">
        <i class="bi bi-exclamation-circle"></i>
        <span>
          Загрузите изображение. Файл, который вы загрузили, поврежден или не является изображением.
        </span>
        <button type="button" class="btn-close"></button>
      </div>
      `;

      $(".messages").append(error);

      closeMessage();
      startMessageQueue();
    }
  });
});
