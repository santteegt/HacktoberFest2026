// Ghost page behavior: reveal panels and story balloons on scroll, the scream, copy the address.
// No network beyond the site's own audio (template/header.js), no dependencies.
(function () {
  var doc = document.documentElement;
  doc.classList.add("js");
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var still = function () { return !!(window.EG && !window.EG.moving()); };
  var panels = document.querySelectorAll(".reveal");
  var balloons = document.querySelectorAll(".reveal .balloon");
  function showBalloons() { balloons.forEach(function (b) { b.style.transitionDelay = ""; b.classList.add("shown"); }); }
  function revealAll() { panels.forEach(function (p) { p.classList.add("seen"); }); showBalloons(); }
  // Automation (headless screenshots), reduced motion, Animation off or no observer: show everything now.
  var instant = reduce || still() || navigator.webdriver || !("IntersectionObserver" in window);
  var io = null, bo = null;
  if (instant) {
    revealAll();
  } else {
    io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("seen"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    panels.forEach(function (p) { io.observe(p); });
    // Each balloon pops in as it enters the view, 120 ms after the previous one of the same panel.
    var alive = false;
    bo = new IntersectionObserver(function (entries) {
      alive = true;
      var perPanel = new Map();
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var panel = e.target.closest(".reveal");
        var n = perPanel.get(panel) || 0;
        perPanel.set(panel, n + 1);
        if (panel) panel.classList.add("seen");
        e.target.style.transitionDelay = (n * 120) + "ms";
        e.target.classList.add("shown");
        bo.unobserve(e.target);
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.2 });
    balloons.forEach(function (b) { bo.observe(b); });
    // an observer that never reports at all is treated as broken
    setTimeout(function () { if (!alive) showBalloons(); }, 1500);
  }
  // Unconditional fallback: whatever the observer did, every panel is visible after 1.5 s
  // (full-page screenshots, print, readers, observers that never fire). Balloons keep waiting for the
  // scroll unless the balloon observer never reported (above) or the page is automated (instant).
  function revealPanels() { panels.forEach(function (p) { p.classList.add("seen"); }); }
  setTimeout(instant ? revealAll : revealPanels, 1500);
  window.addEventListener("beforeprint", revealAll);
  // Animation switched off mid-read: stop waiting for the scroll and show the rest.
  doc.addEventListener("eg:view", function (ev) { if (ev.detail && !ev.detail.moving) revealAll(); });

  // The scream: a bad ghost's vulnerable snippet (.code-card that is not the fix), the first time it enters the view, if Effects is on.
  var guilty = document.body.getAttribute("data-kind") === "bad" &&
    (document.querySelector(".code-card:not(.fix)") || document.querySelector(".wounds"));
  if (guilty && "IntersectionObserver" in window) {
    var screamed = false;
    var so = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting || screamed) return;
        if (window.EG && window.EG.effectsOn()) {
          // once per page load; if the browser refuses (no click yet), try again next time it enters the view
          screamed = true;
          window.EG.sfx("scream", true, function () { screamed = false; }, function () { so.disconnect(); });
        }
      });
    }, { threshold: 0.35 });
    so.observe(guilty);
  }

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
