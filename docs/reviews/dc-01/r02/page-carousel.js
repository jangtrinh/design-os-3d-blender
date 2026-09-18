
/* Carousel: jump buttons and prev/next scroll the snap track; the snapped slide drives the
   pressed tab, the counter and the caption. No timers, no autoplay. */
(function () {
  var track = document.getElementById("track"), slides = [].slice.call(track.children),
      tabs = [].slice.call(document.querySelectorAll(".viewer-tabs .ds-tab")),
      label = document.getElementById("carousel-label"), count = document.getElementById("carousel-count"), current = 0;
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function show(i) {
    i = Math.max(0, Math.min(slides.length - 1, i));
    if (i === current) return; current = i;
    tabs.forEach(function (t, k) { t.setAttribute("aria-pressed", k === i ? "true" : "false"); });
    label.textContent = slides[i].dataset.label; count.textContent = pad(i + 1) + " / " + pad(slides.length);
  }
  function goTo(i) { slides[Math.max(0, Math.min(slides.length - 1, i))].scrollIntoView({ block: "nearest", inline: "start" }); }
  tabs.forEach(function (t) { t.addEventListener("click", function () { goTo(+t.dataset.index); }); });
  document.querySelectorAll(".carousel-btn").forEach(function (b) { b.addEventListener("click", function () { goTo(current + (+b.dataset.dir)); }); });
  track.addEventListener("keydown", function (e) { if (e.key === "ArrowRight") { goTo(current + 1); e.preventDefault(); } if (e.key === "ArrowLeft") { goTo(current - 1); e.preventDefault(); } });
  var raf = 0;
  track.addEventListener("scroll", function () {
    if (raf) return;
    raf = requestAnimationFrame(function () { raf = 0; var w = slides[0].getBoundingClientRect().width + parseFloat(getComputedStyle(track).columnGap || 0); show(Math.round(track.scrollLeft / w)); });
  }, { passive: true });
})();
