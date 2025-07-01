$(document).ready(function () {
  $("#id_photo").on("change", function () {
    const file = this.files[0];

    if (file && file.type.startsWith("image/")) {
      $(this).removeClass("is-invalid").addClass("is-valid");
      const reader = new FileReader();

      reader.onload = function (e) {
        const res = e.target.result;
        $("#img-preview").attr("src", res).show();
        $("#modalImg").attr("src", res).show();
      };

      reader.readAsDataURL(file);
    } else {
      $(this).val("");
      $(this).removeClass("is-valid").addClass("is-invalid");

      const error = `
      <div class="message error shadow">
        <i class="bi bi-exclamation-circle"></i>
        <span>
          Загрузите изображение. Файл, который вы загрузили, поврежден или не является изображением.
        </span>
        <button type="button" class="btn-close"></button>
      </div>`;

      $(".form-messages").append(error);

      $(".btn-close").click(function () {
        $(this).closest(".message").remove();
      });
    }
  });
});
