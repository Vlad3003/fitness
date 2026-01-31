$(document).ready(function () {
  const stickyElements = $(".sticky-el");

  function updateSticky() {
    const scrollTop = Math.round($(window).scrollTop());

    stickyElements.each(function () {
      const el = $(this);
      const stickyTop = Math.round(parseFloat(el.css("top"))) || 0;
      const elTop = Math.round(el.offset().top);
      const isSticked = scrollTop + stickyTop === elTop;
      el.toggleClass("border", isSticked);
    });
  }

  updateSticky();
  $(window).on("scroll", updateSticky);
});
