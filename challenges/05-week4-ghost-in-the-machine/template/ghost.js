// Ghost page behavior: reveal panels on scroll, copy the address. No network, no dependencies.
(function () {
  var doc = document.documentElement;
  doc.classList.add("js");
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var panels = document.querySelectorAll(".reveal");
  function revealAll() { panels.forEach(function (p) { p.classList.add("seen"); }); }
  if (reduce || !("IntersectionObserver" in window)) {
    revealAll();
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("seen"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    panels.forEach(function (p) { io.observe(p); });
  }
  // Unconditional fallback: whatever the observer did, every panel is visible after 1.5 s
  // (full-page screenshots, print, readers, observers that never fire).
  setTimeout(revealAll, 1500);
  window.addEventListener("beforeprint", revealAll);

  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (err) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }
  document.querySelectorAll("button.copy").forEach(function (btn) {
    var label = btn.textContent;
    var status = document.getElementById(btn.getAttribute("aria-describedby") || "");
    function done(ok) {
      btn.textContent = ok ? "Copied" : "Select it";
      if (status) status.textContent = ok ? "Address copied to the clipboard." : "Copy failed; select the address by hand.";
      setTimeout(function () { btn.textContent = label; }, 1800);
    }
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy") || "";
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(fallbackCopy(text)); });
      } else {
        done(fallbackCopy(text));
      }
    });
  });
})();
