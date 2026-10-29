/* Framework-free gallery: fetch ghosts/index.json (and featured.json), render the story of the day
   and the cards, filter client-side; the lights / flight toggles and the floating legend.
   Model-written text only ever goes in through textContent. */
(function () {
  "use strict";
  var KINDS = ["friendly", "lingering", "bad", "banished", "alive"];
  var GLYPH = { friendly: "👻", lingering: "🕯️", bad: "💀", banished: "⚰️", alive: "🌼", unknown: "👻" };
  var all = [];
  var state = { kind: "", age: "", q: "", sort: "new" };
  var $ = function (id) { return document.getElementById(id); };

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function fmtEth(v) {
    if (v == null) return "unknown";
    if (v === 0) return "0 ETH";
    if (v >= 100) return Math.round(v).toLocaleString("en-US") + " ETH";
    if (v >= 1) return v.toFixed(2) + " ETH";
    if (v >= 0.001) return v.toFixed(4) + " ETH";
    return "< 0.001 ETH";
  }

  function yearsSince(iso) {
    if (!iso) return null;
    var t = Date.parse(iso);
    return isNaN(t) ? null : (Date.now() - t) / 31557600000;
  }

  function ageText(g) {
    var y = yearsSince(g.born);
    return g.age ? g.age + (y != null ? " · " + Math.floor(y) + " yrs" : "") : (y != null ? Math.floor(y) + " yrs" : "unknown");
  }

  function shortAddress(a) { return a && a.length > 12 ? a.slice(0, 6) + "…" + a.slice(-4) : (a || ""); }
  // Ghosts with no name anywhere (gallery.py sets `unnamed` when the name is the address).
  function displayName(g) { return g.unnamed ? "Unknown ghost soul" : g.name; }
  function displayTitle(g) {
    var t = g.title, a = (g.address || "").toLowerCase();
    if (!t || t === g.name || t.toLowerCase() === a) return displayName(g);
    return t;
  }

  function card(g) {
    var li = el("li");
    var a = el("a", "card");
    a.href = g.path;
    a.setAttribute("aria-label", displayName(g) + (g.unnamed ? " " + shortAddress(g.address) : "") + ", " + g.kind + " ghost");

    var cover = el("div", "cover");
    if (g.cover) {
      var img = el("img");
      img.src = g.cover; img.alt = ""; img.loading = "lazy"; img.decoding = "async";
      img.addEventListener("error", function () { cover.textContent = ""; cover.appendChild(glyph(g)); });
      cover.appendChild(img);
    } else {
      cover.appendChild(glyph(g));
    }
    a.appendChild(cover);

    var body = el("div", "body");
    var badges = el("div", "row");
    badges.appendChild(el("span", "badge k-" + (KINDS.indexOf(g.kind) >= 0 ? g.kind : "unknown"), g.kind));
    badges.appendChild(el("span", "badge plain", g.historian ? "historian story" : "no historian"));
    if (g.proxy) badges.appendChild(el("span", "badge plain tag-proxy", "proxy"));
    if (g.scars > 0) badges.appendChild(el("span", "badge plain tag-scarred", "scarred"));
    if (g.never_called) badges.appendChild(el("span", "badge plain tag-never", "never called"));
    body.appendChild(badges);
    body.appendChild(el("h2", null, displayName(g)));
    if (g.unnamed) body.appendChild(el("p", "short-addr", shortAddress(g.address)));
    if (displayTitle(g) !== displayName(g)) body.appendChild(el("p", "title", displayTitle(g)));
    if (g.tagline) body.appendChild(el("p", "tagline", g.tagline));
    body.appendChild(el("span", "addr", g.address));

    var dl = el("dl", "facts");
    [["Age", ageText(g)], ["Born", g.born || "unknown"], ["Last seen", g.never_called ? "never called" : (g.last_seen || "unknown")],
     ["Balance", fmtEth(g.balance_eth)], ["Historian", g.historian ? "yes" : "no"]].forEach(function (r) {
      dl.appendChild(el("dt", null, r[0]));
      dl.appendChild(el("dd", null, r[1]));
    });
    body.appendChild(dl);
    a.appendChild(body);
    li.appendChild(a);
    return li;
  }

  function glyph(g) {
    var s = el("span", "glyph", GLYPH[g.kind] || GLYPH.unknown);
    s.setAttribute("aria-hidden", "true");
    return s;
  }

  function haystack(g) {
    return [g.name, g.address, g.title, g.tagline, g.kind, g.age].join(" ").toLowerCase();
  }

  function silentYears(g) {
    if (g.never_called) return 1e6; // never answered anyone: the quietest of all
    var y = yearsSince(g.last_seen);
    return y == null ? -1 : y;
  }

  function visible() {
    var q = state.q.trim().toLowerCase();
    var out = all.filter(function (g) {
      return (!state.kind || (state.kind === "scarred" ? g.scars > 0 : g.kind === state.kind)) &&
        (!state.age || g.age === state.age) &&
        (!q || haystack(g).indexOf(q) >= 0);
    });
    var by = {
      new: null, // index.json is already newest story first; stable sort keeps it
      oldest: function (a, b) { return (a.born || "9").localeCompare(b.born || "9"); },
      silent: function (a, b) { return (silentYears(b) - silentYears(a)) || ((a.calls || 0) - (b.calls || 0)); },
      balance: function (a, b) { return (b.balance_eth || 0) - (a.balance_eth || 0); }
    }[state.sort];
    if (by) out = out.slice().sort(by);
    return out;
  }

  function render() {
    var list = visible(), grid = $("grid");
    grid.textContent = "";
    list.forEach(function (g) { grid.appendChild(card(g)); });
    $("count").textContent = all.length
      ? "Showing " + list.length + " of " + all.length + " ghost" + (all.length === 1 ? "" : "s")
      : "";
    var empty = $("empty");
    if (!all.length) { empty.hidden = false; empty.textContent = "No ghosts have been summoned yet. Check back after the next story."; }
    else if (!list.length) { empty.hidden = false; empty.textContent = "No ghost matches these filters."; }
    else empty.hidden = true;
    Array.prototype.forEach.call(document.querySelectorAll(".chip"), function (c) {
      c.setAttribute("aria-pressed", String(c.dataset.kind === state.kind));
    });
  }


  function kindOf(g) { return KINDS.indexOf(g.kind) >= 0 ? g.kind : "unknown"; }

  // The story of the day: the newest story (featured.json, else index[0]); big picture, little text.
  function renderFeatured(g) {
    var box = $("featured");
    if (!g || !g.path) { box.hidden = true; return; }
    box.textContent = "";
    box.setAttribute("data-kind", kindOf(g));

    var stage = el("div", "f-stage" + (g.cover ? " has-cover" : ""));
    stage.setAttribute("aria-hidden", "true");
    stage.appendChild(el("div", "stars"));
    stage.appendChild(el("div", "moon"));
    if (g.cover) {
      var fig = el("figure", "f-cover");
      var img = el("img");
      img.src = g.cover; img.alt = ""; img.decoding = "async";
      img.addEventListener("error", function () { stage.removeChild(fig); stage.classList.remove("has-cover"); });
      fig.appendChild(img);
      stage.appendChild(fig);
    }
    var src = document.querySelector(".haunt svg.ghost");
    if (src) {
      var holder = el("div", "f-ghost");
      var bob = el("div", "bob");
      var svg = src.cloneNode(true);
      var tag = svg.querySelector(".ghost-tag text");
      if (tag) tag.textContent = (g.address || "0x").slice(0, 6);
      bob.appendChild(svg);
      holder.appendChild(bob);
      stage.appendChild(holder);
    }
    box.appendChild(stage);

    var copy = el("div", "f-copy");
    copy.appendChild(el("p", "kicker", "Story of the day"));
    var h = el("h2", "f-title", displayTitle(g));
    h.id = "featured-title";
    copy.appendChild(h);
    var who = el("p", "f-name", displayTitle(g) !== displayName(g) || g.unnamed ? displayName(g) + " · " : "");
    who.appendChild(el("code", null, shortAddress(g.address)));
    copy.appendChild(who);
    if (g.tagline) copy.appendChild(el("p", "f-tagline", g.tagline));

    var chips = el("ul", "f-chips");
    function chip(cls, text) { var li = el("li"); li.appendChild(el("span", cls, text)); chips.appendChild(li); }
    chip("badge k-" + kindOf(g), g.kind || "unknown");
    if (g.age) chip("badge plain", g.age);
    if (g.scars > 0) chip("badge plain tag-scarred", "scarred");
    if (g.never_called) chip("badge plain tag-never", "never called");
    if (g.proxy) chip("badge plain tag-proxy", "proxy");
    chip("badge plain", g.historian ? "historian story" : "no historian");
    copy.appendChild(chips);

    var dl = el("dl", "f-stats");
    [["Born", g.born || "unknown"],
     [g.never_called ? "Called" : "Last seen", g.never_called ? "never" : (g.last_seen || "unknown")],
     ["Calls", (g.calls || 0).toLocaleString("en-US")],
     ["Balance", fmtEth(g.balance_eth)]].forEach(function (r) {
      var d = el("div");
      d.appendChild(el("dt", null, r[0]));
      d.appendChild(el("dd", null, r[1]));
      dl.appendChild(d);
    });
    copy.appendChild(dl);

    var cta = el("a", "cta", "Learn more");
    cta.href = g.path;
    cta.appendChild(el("span", "sr-only", ": the story of " + displayName(g) + (g.unnamed ? " " + shortAddress(g.address) : "")));
    var arrow = el("span", null, "→");
    arrow.setAttribute("aria-hidden", "true");
    cta.appendChild(arrow);
    copy.appendChild(cta);
    box.appendChild(copy);
    box.hidden = false;
  }

  // Lights and flight toggles: state in localStorage (guarded), flight off by default under reduced motion.
  function load(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
  function save(k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* private mode: keep it in memory */ } }

  function setupToggles() {
    var root = document.documentElement;
    var reduce = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    var lights = load("ghosts.lights") !== "off";
    var stored = load("ghosts.motion");
    var moving = stored ? stored === "on" : !reduce;
    var bL = $("lights"), bM = $("motion");
    function apply() {
      root.classList.toggle("lights-off", !lights);
      root.classList.toggle("moving", moving);
      if (bL) { bL.setAttribute("aria-pressed", String(lights)); bL.title = lights ? "Turn the lights off to see the ghost" : "Turn the lights back on"; }
      if (bM) { bM.setAttribute("aria-pressed", String(moving)); bM.title = moving ? "Stop the ghost" : "Let the ghost fly"; }
    }
    if (bL) bL.addEventListener("click", function () { lights = !lights; save("ghosts.lights", lights ? "on" : "off"); apply(); });
    if (bM) bM.addEventListener("click", function () { moving = !moving; save("ghosts.motion", moving ? "on" : "off"); apply(); });
    apply();
  }

  // Floating legend: hover / focus expand it on desktop (CSS); the Key button toggles it (touch, keyboard).
  function setupLegend() {
    var box = $("legend"), btn = $("legend-toggle");
    if (!box || !btn) return;
    function set(open) { box.classList.toggle("open", open); btn.setAttribute("aria-expanded", String(open)); }
    btn.addEventListener("click", function () { set(!box.classList.contains("open")); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && box.classList.contains("open")) { set(false); btn.focus(); }
    });
    document.addEventListener("click", function (e) { if (!box.contains(e.target)) set(false); });
  }

  function buildControls() {
    var kinds = $("kinds");
    var counts = {};
    all.forEach(function (g) { counts[g.kind] = (counts[g.kind] || 0) + 1; });
    var present = KINDS.filter(function (k) { return counts[k]; });
    Object.keys(counts).forEach(function (k) { if (KINDS.indexOf(k) < 0) present.push(k); });
    var scarred = all.filter(function (g) { return g.scars > 0; }).length;
    var defs = [{ kind: "", label: "All", n: all.length }].concat(present.map(function (k) { return { kind: k, label: k, n: counts[k] }; }));
    if (scarred) defs.push({ kind: "scarred", label: "scarred", n: scarred });
    defs
      .forEach(function (d) {
        var b = el("button", "chip", d.label);
        b.type = "button"; b.dataset.kind = d.kind;
        b.appendChild(el("small", null, String(d.n)));
        b.addEventListener("click", function () { state.kind = d.kind; render(); });
        kinds.appendChild(b);
      });
    var ages = [];
    all.forEach(function (g) { if (g.age && ages.indexOf(g.age) < 0) ages.push(g.age); });
    var sel = $("age");
    ages.forEach(function (a) { var o = el("option", null, a); o.value = a; sel.appendChild(o); });
    sel.addEventListener("change", function () { state.age = sel.value; render(); });
    $("q").addEventListener("input", function (e) { state.q = e.target.value; render(); });
    $("sort").addEventListener("change", function (e) { state.sort = e.target.value; render(); });
  }

  setupToggles();
  setupLegend();

  function getJSON(url) {
    return fetch(url, { cache: "no-cache" }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
  }
  var featured = getJSON("ghosts/featured.json").catch(function () { return null; });

  getJSON("ghosts/index.json")
    .then(function (data) {
      all = Array.isArray(data) ? data : [];
      buildControls();
      render();
      return featured.then(function (f) {
        renderFeatured(f && typeof f === "object" && f.path ? f : all[0]);
      });
    })
    .catch(function (err) {
      var empty = $("empty");
      empty.hidden = false;
      empty.textContent = "The ghosts could not be listed (" + err.message + "). Try again in a moment.";
    });
})();
