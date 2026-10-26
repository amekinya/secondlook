/* SecondLook page overlay. Shared by the demo marketplace and the browser extension.
   window.SecondLook.init({ api, findCards, demo }) -> adds a HUD; "Scan this page" stamps every listing live. */
(() => {
  if (window.SecondLook) return;
  const CSS = `
  .sl-hud{position:fixed;right:16px;bottom:16px;z-index:2147483000;width:min(360px,calc(100vw - 32px));background:#18322b;color:#f2f5f1;
    border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.35);font:15px/1.45 "Atkinson Hyperlegible",system-ui,sans-serif;overflow:hidden}
  .sl-hud *{box-sizing:border-box}
  .sl-hud-head{display:flex;align-items:center;gap:10px;padding:12px 14px}
  .sl-logo{width:24px;height:21px;background:#ffd100;clip-path:polygon(50% 0,100% 100%,0 100%);flex:none;position:relative}
  .sl-logo:after{content:"";position:absolute;left:8px;top:9px;width:8px;height:8px;border:2px solid #18322b;border-radius:50%}
  .sl-name{font-weight:700;font-size:17px;flex:1}
  .sl-x{background:none;border:0;color:inherit;opacity:.7;cursor:pointer;font-size:18px;padding:2px 6px}
  .sl-body{padding:0 14px 14px}
  .sl-btn{width:100%;min-height:44px;border:0;border-radius:6px;background:#ffd100;color:#18322b;font:700 16px/1 inherit;cursor:pointer}
  .sl-btn:disabled{opacity:.6;cursor:progress}
  .sl-mode{font-size:13px;opacity:.85;margin:8px 0 0}
  .sl-bar{height:6px;background:rgba(255,255,255,.18);border-radius:3px;overflow:hidden;margin:12px 0 10px}
  .sl-bar i{display:block;height:100%;width:0;background:#ffd100;transition:width .25s}
  .sl-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;text-align:center}
  .sl-stats b{display:block;font-size:20px;font-variant-numeric:tabular-nums}
  .sl-stats span{font-size:12px;opacity:.8}
  .sl-stats .sl-red b{color:#ff8a8a}
  .sl-sum{margin-top:12px;padding:10px 12px;background:rgba(255,255,255,.08);border-radius:6px;font-size:14px}
  .sl-card{position:relative !important}
  .sl-scanning:after{content:"";position:absolute;left:0;right:0;top:0;height:3px;background:#ffd100;box-shadow:0 0 12px #ffd100;
    animation:sl-sweep 1.4s ease-in-out infinite;z-index:5;pointer-events:none}
  @keyframes sl-sweep{0%{top:0}50%{top:calc(var(--sl-h,60%) - 3px)}100%{top:0}}
  @media (prefers-reduced-motion:reduce){.sl-scanning:after{animation:none;top:0}}
  .sl-stamp{position:absolute;left:8px;right:8px;top:8px;z-index:6;border-radius:6px;overflow:hidden;cursor:pointer;
    font:14px/1.35 "Atkinson Hyperlegible",system-ui,sans-serif;box-shadow:0 4px 14px rgba(0,0,0,.28);transform-origin:top center;
    animation:sl-in .35s cubic-bezier(.2,.9,.2,1.2) both;text-align:left;border:0;padding:0;background:#fff;color:#18322b}
  @keyframes sl-in{from{transform:scale(.6) rotate(-4deg);opacity:0}}
  @media (prefers-reduced-motion:reduce){.sl-stamp{animation:none}}
  .sl-band{display:flex;align-items:center;gap:8px;padding:6px 10px;font-weight:700;letter-spacing:.06em;font-size:15px}
  .sl-band:before{content:"";width:18px;height:16px;background:currentColor;clip-path:polygon(50% 0,100% 100%,0 100%)}
  .sl-msg{padding:6px 10px 8px;font-weight:700;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .sl-deaths{display:block;margin:-4px 10px 8px;font-size:13px;font-weight:700;color:#c8102e}
  .sl-bad .sl-band{background:#c8102e;color:#fff}.sl-warn .sl-band{background:#f47b20;color:#18322b}
  .sl-check .sl-band{background:#ffd100;color:#18322b}
  .sl-ok{left:auto;right:8px;width:auto;border-radius:999px;background:#00843d;color:#fff}
  .sl-ok .sl-band{padding:4px 10px;font-size:13px;letter-spacing:.02em}.sl-ok .sl-band:before{display:none}
  .sl-dim img{filter:grayscale(.5) brightness(.85)}
  .sl-drawer{position:fixed;top:0;right:0;bottom:0;z-index:2147483001;width:min(460px,100vw);background:#fff;color:#18322b;
    box-shadow:-10px 0 30px rgba(0,0,0,.3);overflow:auto;font:16px/1.5 "Atkinson Hyperlegible",system-ui,sans-serif;transform:translateX(100%);transition:transform .25s}
  .sl-drawer.sl-open{transform:none}
  .sl-drawer *{box-sizing:border-box}
  .sl-dhead{display:flex;align-items:center;gap:10px;padding:14px 16px;font-weight:700;font-size:22px;letter-spacing:.05em}
  .sl-dhead.sl-bad{background:#c8102e;color:#fff}.sl-dhead.sl-warn{background:#f47b20}.sl-dhead.sl-check{background:#ffd100}.sl-dhead.sl-good{background:#00843d;color:#fff}
  .sl-dhead:before{content:"";width:24px;height:21px;background:currentColor;clip-path:polygon(50% 0,100% 100%,0 100%)}
  .sl-dhead span{flex:1}.sl-dhead button{background:none;border:0;color:inherit;font-size:22px;cursor:pointer}
  .sl-dbody{padding:16px;display:grid;gap:14px}
  .sl-dbody h3{margin:0;font-size:22px;line-height:1.2}
  .sl-dbody p{margin:0}
  .sl-rs{list-style:none;margin:0;padding:0;border-top:2px solid #18322b}
  .sl-rs li{padding:10px 0 10px 12px;border-left:5px solid #d3ddd8;border-bottom:1px solid #d3ddd8}
  .sl-rs li.ILLEGAL_TO_SELL,.sl-rs li.RECALLED{border-left-color:#c8102e}.sl-rs li.UNSAFE_ADVISORY{border-left-color:#f47b20}.sl-rs li.CHECK{border-left-color:#ffd100}.sl-rs li.OK_SO_FAR{border-left-color:#00843d}
  .sl-rs b{display:block}.sl-rs small{color:#74867f}
  .sl-rc{display:grid;grid-template-columns:110px 1fr;gap:12px;border:1px solid #d3ddd8;border-radius:6px;padding:10px}
  .sl-rc img{width:110px;border-radius:3px}.sl-rc small{color:#74867f;display:block}
  .sl-msgbox{background:#f2f5f1;border-radius:14px 14px 14px 4px;padding:12px 14px}
  .sl-copy{margin-top:8px;border:2px solid #18322b;background:#fff;border-radius:6px;padding:6px 12px;font-weight:700;cursor:pointer}
  .sl-skel{height:12px;border-radius:3px;background:#e3e9e6;margin:8px 0}
  `;
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const TONE = { ILLEGAL_TO_SELL: "bad", RECALLED: "bad", UNSAFE_ADVISORY: "warn", CHECK: "check", OK_SO_FAR: "good" };
  const WORD = { ILLEGAL_TO_SELL: "DANGER", RECALLED: "DANGER", UNSAFE_ADVISORY: "WARNING", CHECK: "CAUTION", OK_SO_FAR: "NO KNOWN ISSUES" };

  function init(opts) {
    const api = (opts.api || "").replace(/\/$/, "");
    const st = document.createElement("style"); st.textContent = CSS; document.head.appendChild(st);
    const hud = document.createElement("section");
    hud.className = "sl-hud"; hud.setAttribute("aria-label", "SecondLook");
    hud.innerHTML = `<div class="sl-hud-head"><span class="sl-logo" aria-hidden="true"></span><span class="sl-name">SecondLook</span>
      <button class="sl-x" title="Hide" aria-label="Hide SecondLook">×</button></div>
      <div class="sl-body"><button class="sl-btn" type="button">Scan this page for unsafe baby gear</button>
      <p class="sl-mode">Checks every listing for banned products, recalls and expired car seats.</p>
      <div class="sl-live" hidden><div class="sl-bar"><i></i></div>
      <div class="sl-stats"><div><b class="sl-n">0</b><span>scanned</span></div><div class="sl-red"><b class="sl-f">0</b><span>flagged</span></div>
      <div><b class="sl-t">0.0s</b><span>time</span></div><div><b class="sl-c">$0.000</b><span>AI cost</span></div></div></div>
      <div class="sl-sum" hidden aria-live="polite"></div></div>`;
    document.body.appendChild(hud);
    hud.querySelector(".sl-x").onclick = () => hud.remove();
    const drawer = document.createElement("aside"); drawer.className = "sl-drawer"; drawer.setAttribute("aria-label", "Listing check");
    document.body.appendChild(drawer);
    const btn = hud.querySelector(".sl-btn");
    btn.onclick = () => run();
    if (opts.autostart) setTimeout(run, 400);

    async function run() {
      const cards = opts.findCards();
      if (!cards.length) { hud.querySelector(".sl-mode").textContent = "No listings found on this page."; return; }
      btn.disabled = true; btn.textContent = `Scanning ${cards.length} listings…`;
      hud.querySelector(".sl-live").hidden = false; hud.querySelector(".sl-sum").hidden = true;
      const byId = {};
      cards.forEach((c) => {
        byId[c.id] = c; c.el.classList.add("sl-card", "sl-scanning");
        c.el.querySelectorAll(".sl-stamp").forEach((s) => s.remove());
        const img = c.el.querySelector("img"); if (img) c.el.style.setProperty("--sl-h", img.offsetHeight + "px");
      });
      const t0 = performance.now();
      const tick = setInterval(() => (hud.querySelector(".sl-t").textContent = ((performance.now() - t0) / 1000).toFixed(1) + "s"), 100);
      try {
        const res = await fetch(api + "/api/scan", { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ demo: !!opts.demo, listings: cards.map((c) => ({ id: c.id, title: c.title, text: c.text, image: c.image })) }) });
        if (!res.ok || !res.body) throw new Error((await res.json().catch(() => ({}))).detail || "Scan failed");
        const reader = res.body.getReader(); const dec = new TextDecoder(); let buf = "";
        for (;;) {
          const { value, done } = await reader.read(); if (done) break;
          buf += dec.decode(value, { stream: true });
          let i; while ((i = buf.indexOf("\n\n")) >= 0) { handle(buf.slice(0, i)); buf = buf.slice(i + 2); }
        }
      } catch (e) {
        hud.querySelector(".sl-mode").textContent = "Couldn't reach SecondLook: " + e.message;
      } finally {
        clearInterval(tick); btn.disabled = false; btn.textContent = "Scan again";
        cards.forEach((c) => c.el.classList.remove("sl-scanning"));
      }

      function handle(block) {
        const ev = /event: (\w+)/.exec(block)?.[1]; const data = JSON.parse(/data: (.*)/s.exec(block)?.[1] || "{}");
        if (ev === "start") {
          const modes = { live: `Live · Nemotron 3.5 Super VL on Nebius · ${data.workers} in parallel`, recorded: "Replaying a recorded live scan (Nemotron 3.5 Super VL on Nebius)", rules: "AI offline · checking listing text with rules only" };
          hud.querySelector(".sl-mode").textContent = modes[data.mode] || "";
        } else if (ev === "stamp") {
          const c = byId[data.id]; if (!c) return;
          c.el.classList.remove("sl-scanning"); stamp(c, data);
          const p = data.progress;
          hud.querySelector(".sl-n").textContent = `${p.done}/${p.total}`; hud.querySelector(".sl-f").textContent = p.flagged;
          hud.querySelector(".sl-c").textContent = "$" + p.cost_usd.toFixed(3);
          hud.querySelector(".sl-bar i").style.width = (100 * p.done / p.total) + "%";
        } else if (ev === "done") {
          clearInterval(tick);
          hud.querySelector(".sl-t").textContent = data.elapsed.toFixed(1) + "s";
          const sum = hud.querySelector(".sl-sum"); sum.hidden = false;
          sum.innerHTML = data.flagged
            ? `<b>${data.flagged} of ${data.total} listings</b> shouldn't be bought as-is. Scanned in ${data.elapsed.toFixed(1)} s for $${data.cost_usd.toFixed(3)}. Tap a label for details.`
            : `No banned or recalled items found in ${data.total} listings. Still check labels in person.`;
        }
      }
    }

    function stamp(c, d) {
      const tone = TONE[d.level];
      const b = document.createElement("button"); b.type = "button";
      b.className = "sl-stamp sl-" + tone + (tone === "good" ? " sl-ok" : "");
      b.setAttribute("aria-label", `${WORD[d.level]}: ${d.headline}. Open details.`);
      b.innerHTML = tone === "good" ? `<span class="sl-band">✓ No known issues</span>`
        : `<span class="sl-band">${WORD[d.level]}</span><span class="sl-msg">${esc(d.headline)}</span>${d.deaths ? `<span class="sl-deaths">${d.deaths} infant death${d.deaths > 1 ? "s" : ""} reported</span>` : ""}`;
      b.onclick = (e) => { e.preventDefault(); e.stopPropagation(); open(c, d); };
      (c.stampHost || c.el).appendChild(b);
      if (tone === "bad") c.el.classList.add("sl-dim");
    }

    async function open(c, d) {
      const tone = TONE[d.level];
      drawer.innerHTML = `<div class="sl-dhead sl-${tone}"><span>${WORD[d.level]}</span><button aria-label="Close">×</button></div>
        <div class="sl-dbody"><p><small>${esc(c.title)}</small></p><div class="sl-skel"></div><div class="sl-skel" style="width:70%"></div><div class="sl-skel" style="width:85%"></div>
        <p><small>Nemotron 3 Ultra is reading the recall notices…</small></p></div>`;
      drawer.classList.add("sl-open"); drawer.querySelector("button").onclick = () => drawer.classList.remove("sl-open");
      try {
        const r = await fetch(api + "/api/listing", { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ demo: !!opts.demo, id: c.id, title: c.title, text: c.text, image: c.image }) });
        const x = await r.json();
        const t2 = TONE[x.level];
        drawer.innerHTML = `<div class="sl-dhead sl-${t2}"><span>${WORD[x.level]}</span><button aria-label="Close">×</button></div>
          <div class="sl-dbody"><p><small>${esc([x.category_label, x.item.brand].filter(Boolean).join(" · "))}</small></p>
          <h3>${esc(x.label)}</h3><p>${esc(x.writeup?.summary || "")}</p>
          <ul class="sl-rs">${x.reasons.map((r) => `<li class="${r.level}"><b>${esc(r.title)}</b>${esc(r.detail)}<br><small>${esc(r.cite)}</small></li>`).join("")}</ul>
          ${(x.recalls || []).filter((r) => r.match === "definite").map((r) => `<div class="sl-rc">${r.images?.[0] ? `<img src="${esc(r.images[0].url)}" alt="">` : "<span></span>"}
            <div><b>${esc(r.title)}</b><small>${esc(r.source)} ${esc(r.id)} · ${esc(r.date)}${r.deaths ? ` · ${r.deaths} deaths reported` : ""}</small>
            ${r.remedy ? `<small><b>Remedy:</b> ${esc(r.remedy.slice(0, 200))}</small>` : ""}${r.why ? `<small><i>${esc(r.why)}</i></small>` : ""}
            <small><a href="${esc(r.url)}" target="_blank" rel="noopener">Official notice</a></small></div></div>`).join("")}
          ${x.writeup?.seller_message ? `<div><b>Message to the seller</b><div class="sl-msgbox">${esc(x.writeup.seller_message)}</div><button class="sl-copy">Copy message</button></div>` : ""}
          <p><small>Recall data from CPSC and NHTSA (checked ${esc(x.rules_verified_as_of)}). Not legal advice; check the item in person.</small></p></div>`;
        drawer.querySelector(".sl-dhead button").onclick = () => drawer.classList.remove("sl-open");
        const cp = drawer.querySelector(".sl-copy");
        if (cp) cp.onclick = () => navigator.clipboard?.writeText(x.writeup.seller_message).then(() => (cp.textContent = "Copied"));
      } catch (e) {
        drawer.querySelector(".sl-dbody").innerHTML = `<p>Couldn't load details: ${esc(e.message)}</p>`;
      }
    }
  }
  window.SecondLook = { init };
})();
