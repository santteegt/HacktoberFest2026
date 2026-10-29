// Shared header behaviour (gallery and ghost pages): Lights, Animation and Effects switches, the ambient loop
// and one-shot sound effects. Exposes window.EG = { effectsOn, sfx } for the page scripts. No network beyond
// the site's own audio files; every storage access is guarded.
(function () {
  "use strict";
  var root = document.documentElement;
  var head = document.getElementById("eg-header");
  var base = (head && head.getAttribute("data-assets")) || "assets/";
  function load(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
  function save(k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* private mode: keep it in memory */ } }
  function $(id) { return document.getElementById(id); }

  // Lights and Animation: same keys as before ("ghosts.lights", "ghosts.motion"), so a choice carries
  // between the gallery and the ghost pages. Animation starts off under prefers-reduced-motion.
  var reduce = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  // First visit (no "eg-welcomed"): the browser's required first click becomes part of the story. The index
  // hunts the flying ghost (.eg-hunt), ghost pages light Doña Gwei's candle (.eg-candle); reduced motion gets
  // the candle everywhere. Automated visits (navigator.webdriver: screenshots, og, face) skip it.
  var hunt = document.querySelector(".eg-hunt"), candle = document.querySelector(".eg-candle");
  var target = (!reduce && hunt) || candle || null;
  var welcome = !!target && !navigator.webdriver && load("eg-welcomed") !== "1";
  var lights = welcome ? false : load("ghosts.lights") !== "off";
  var stored = load("ghosts.motion");
  var moving = stored ? stored === "on" : !reduce;
  var bL = $("lights"), bM = $("motion"), bE = $("effects");
  function applyView() {
    root.classList.toggle("lights-off", !lights);
    root.classList.toggle("moving", moving);
    if (bL) { bL.setAttribute("aria-pressed", String(lights)); bL.title = lights ? "Turn the lights off to see the ghost" : "Turn the lights back on"; }
    if (bM) { bM.setAttribute("aria-pressed", String(moving)); bM.title = moving ? "Stop the animation" : "Let the ghosts move"; }
    try { root.dispatchEvent(new CustomEvent("eg:view", { detail: { lights: lights, moving: moving } })); } catch (e) { /* old browser */ }
  }
  if (bL) bL.addEventListener("click", function () { lights = !lights; save("ghosts.lights", lights ? "on" : "off"); applyView(); });
  if (bM) bM.addEventListener("click", function () { moving = !moving; save("ghosts.motion", moving ? "on" : "off"); applyView(); });
  applyView();

  // Effects (default on, key "eg-effects"): the ambient loop plus one-shot effects. Browsers block audio
  // before a user gesture; then the switch shows off until the first click on it or anywhere on the page.
  var wanted = load("eg-effects") !== "off";
  var blocked = false;
  var VOL = 0.6, DUCK = 0.25, ducks = 0;
  var ambient = null;
  function amb() {
    if (!ambient && window.Audio) {
      ambient = new Audio(base + "ambient.mp3");
      ambient.loop = true;
      ambient.preload = "auto";
      ambient.volume = VOL;
      var t = parseFloat((function () { try { return window.sessionStorage.getItem("eg-ambient-t"); } catch (e) { return null; } })() || "");
      if (t > 0) { try { ambient.currentTime = t; } catch (e) { /* not seekable yet */ } }
    }
    return ambient;
  }
  function on() { return wanted && !blocked; }
  function applyFx() {
    if (!bE) return;
    bE.setAttribute("aria-pressed", String(on()));
    bE.title = on() ? "Mute the music and sound effects" : (wanted ? "Start the music and sound effects" : "Turn the music and sound effects on");
  }
  function start() {
    var a = amb();
    if (!a || !wanted) return;
    var p;
    try { p = a.play(); } catch (e) { blocked = true; applyFx(); return; }
    if (p && p.then) {
      p.then(function () { blocked = false; applyFx(); }, function () { blocked = true; applyFx(); });
    } else { blocked = false; applyFx(); }
  }
  function stop() { if (ambient) ambient.pause(); }
  if (bE) bE.addEventListener("click", function () {
    if (on()) { wanted = false; save("eg-effects", "off"); stop(); }
    else { wanted = true; blocked = false; save("eg-effects", "on"); start(); }
    applyFx();
  });
  // the first gesture anywhere starts the music when Effects is wanted but the browser said no
  var welcomeEvt = null;
  function gesture(e) {
    if (welcome || (e && e === welcomeEvt)) return;  // the welcome handles its own click
    if (bE && e && e.target && bE.contains(e.target)) return;
    if (wanted && (blocked || !ambient || ambient.paused)) { blocked = false; start(); }
  }
  document.addEventListener("click", gesture);
  document.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") gesture(e); });
  window.addEventListener("pagehide", function () {
    if (ambient) { try { window.sessionStorage.setItem("eg-ambient-t", String(ambient.currentTime || 0)); } catch (e) { /* ignore */ } }
  });
  applyFx();
  if (wanted && !welcome) start();

  // One-shot effect (name = file stem in assets/). duck: lower the ambient to DUCK while it plays.
  function sfx(name, duck, onFail, onPlay) {
    if (!wanted || !window.Audio) { if (onFail) onFail(); return false; }
    var a = new Audio(base + name + ".mp3"), done = false, ducked = !!(duck && ambient);
    function restore() {
      if (done) return;
      done = true;
      if (ducked) { ducks = Math.max(0, ducks - 1); if (!ducks) ambient.volume = VOL; }
      a.onended = a.onerror = null;
    }
    if (ducked) { ducks += 1; ambient.volume = DUCK; }
    function fail() { restore(); if (onFail) onFail(); }
    a.onended = restore; a.onerror = fail;
    try {
      var p = a.play();
      if (p && p.then) p.then(function () { if (onPlay) onPlay(); }, fail);
      else if (onPlay) onPlay();
    } catch (e) { fail(); return false; }
    return true;
  }
  // ---- the welcome ----
  var WELCOME_HINT_MS = 8000, WELCOME_GIVE_UP_MS = 20000, FADE_MS = 2000;
  var line = $("eg-line"), haunt = document.querySelector(".haunt"), timers = [];
  function say(t) { if (line && t) line.textContent = t; }
  function fadeIn(a) {
    a.volume = 0;
    var t0 = Date.now();
    var iv = setInterval(function () {
      var k = Math.min(1, (Date.now() - t0) / FADE_MS);
      if (!ducks) a.volume = VOL * k;
      if (k >= 1) clearInterval(iv);
    }, 50);
  }
  function endWelcome(lit) {
    welcome = false;
    timers.forEach(clearTimeout);
    document.removeEventListener("click", onWelcomeClick, true);
    root.classList.remove("eg-welcome");
    if (lit) { root.classList.add("eg-lit"); setTimeout(function () { root.classList.remove("eg-lit"); }, 2200); }
    if (line) { line.classList.add("eg-out"); setTimeout(function () { line.hidden = true; }, 700); }
    if (hunt) hunt.hidden = true;
    if (haunt) haunt.setAttribute("aria-hidden", "true");
    // the index's lone candle stays a moment so the flame is seen; the ghost page's button only overlays
    if (candle) setTimeout(function () { candle.hidden = true; }, candle.classList.contains("eg-candle-solo") && lit ? 1800 : 0);
  }
  function onWelcomeClick(e) {
    if (!welcome) return;
    welcomeEvt = e;  // the event is never cancelled: the click's own action (a card, a filter, a switch) still happens
    var t = e.target;
    var onFx = !!(bE && t && bE.contains(t)), onLights = !!(bL && t && bL.contains(t));
    endWelcome(true);
    save("eg-welcomed", "1");
    // a click on Lights: its own handler turns them on (and stores it)
    if (!onLights) { lights = true; save("ghosts.lights", "on"); applyView(); }
    // a click on Effects: honour it, whatever the reader chose
    if (!onFx) {
      wanted = true; blocked = false; save("eg-effects", "on");
      var a = amb();
      if (a) { fadeIn(a); start(); }
      sfx("ghost");
      applyFx();
    }
  }
  function giveUp() {
    // nobody clicked: lights back on, nothing plays, try once more on the next visit, then stop asking
    var n = (parseInt(load("eg-welcome-tries") || "0", 10) || 0) + 1;
    save("eg-welcome-tries", String(n));
    if (n >= 2) save("eg-welcomed", "1");
    endWelcome(false);
    lights = true; applyView();
    blocked = true; applyFx();
  }
  if (welcome) {
    root.classList.add("eg-welcome");
    target.hidden = false;
    if (target === hunt && haunt) haunt.removeAttribute("aria-hidden");
    if (line) {
      line.hidden = false;
      var first = line.getAttribute(target === hunt ? "data-hunt" : "data-candle");
      setTimeout(function () { say(first); }, 60);  // set after load so the live region reads it once
    }
    document.addEventListener("click", onWelcomeClick, true);
    timers.push(setTimeout(function () { say(line && line.getAttribute("data-hint")); }, WELCOME_HINT_MS));
    timers.push(setTimeout(giveUp, WELCOME_GIVE_UP_MS));
  }

  window.EG = { effectsOn: function () { return wanted; }, sfx: sfx, moving: function () { return moving; } };
})();
