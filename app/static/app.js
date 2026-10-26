(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const monthYear = (iso) => iso ? new Date(iso + "T12:00:00").toLocaleDateString("en-US", { month: "short", year: "numeric" }) : "";
  const SIGNAL = { ILLEGAL_TO_SELL: ["DANGER", "bad"], RECALLED: ["DANGER", "bad"], UNSAFE_ADVISORY: ["WARNING", "warn"], CHECK: ["CAUTION", "check"], OK_SO_FAR: ["NO KNOWN ISSUES", "good"] };
  let files = [];
  let thumbUrl = null;

  // samples
  fetch("/api/samples").then((r) => r.json()).then((list) => {
    $("#sampleRow").innerHTML = list.map((s) => `<button type="button" class="sample" data-f="${esc(s.file)}" data-u="${esc(s.url)}">
      <img src="${esc(s.url)}" alt="" loading="lazy"><b>${esc(s.title)}</b><span>${esc(s.price)}</span></button>`).join("");
    document.querySelectorAll(".sample").forEach((b) => b.addEventListener("click", () => {
      const fd = new FormData(); fd.append("sample", b.dataset.f); thumbUrl = b.dataset.u; run(fd);
    }));
  });

  const drop = $("#drop");
  ["dragenter", "dragover"].forEach((e) => drop.addEventListener(e, (ev) => { ev.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((e) => drop.addEventListener(e, () => drop.classList.remove("over")));
  drop.addEventListener("drop", (ev) => { ev.preventDefault(); setFiles([...ev.dataTransfer.files].filter((f) => f.type.startsWith("image/"))); });
  $("#fileInput").addEventListener("change", (e) => setFiles([...e.target.files]));
  function setFiles(fs) {
    files = fs; const el = $("#fileName");
    el.textContent = fs.length ? `${fs.length} image${fs.length > 1 ? "s" : ""} ready` : "Listing screenshot, or photos of the item and its labels";
    el.classList.toggle("set", fs.length > 0);
  }

  $("#checkForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const fd = new FormData();
    files.forEach((f) => fd.append("images", f));
    const url = $("#urlInput").value.trim(), text = $("#textInput").value.trim();
    if (url) fd.append("url", url);
    if (text) fd.append("text", text);
    if (!files.length && !url && !text) { $("#moreBox").open = true; $("#fileName").textContent = "Add a screenshot, a link, or the listing text"; return; }
    thumbUrl = files[0] ? URL.createObjectURL(files[0]) : null;
    run(fd);
  });

  async function run(fd) {
    $("#ask").hidden = true; $("#result").hidden = true; $("#busy").hidden = false; window.scrollTo(0, 0);
    const msgs = ["Looking at the listing", "Checking bans and safety standards", "Reading recall notices", "Writing your summary"];
    let i = 0; $("#busyText").textContent = msgs[0];
    const t = setInterval(() => { i = Math.min(i + 1, msgs.length - 1); $("#busyText").textContent = msgs[i]; }, 1600);
    try {
      const res = await fetch("/api/check", { method: "POST", body: fd });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Couldn't check that listing.");
      render(d);
    } catch (err) {
      $("#ask").hidden = false; alert(err.message);
    } finally { clearInterval(t); $("#busy").hidden = true; }
  }

  $("#againBtn").addEventListener("click", () => { $("#result").hidden = true; $("#ask").hidden = false; setFiles([]); window.scrollTo(0, 0); });

  function render(d) {
    $("#result").hidden = false; window.scrollTo(0, 0);
    const [word, tone] = SIGNAL[d.level];
    $("#signal").className = "signal " + tone;
    $("#signalWord").textContent = word;
    const th = $("#thumb");
    if (thumbUrl) { th.src = thumbUrl; th.alt = "The listing you checked"; th.hidden = false; } else th.hidden = true;
    $("#catLabel").textContent = [d.category_label, d.item.brand].filter(Boolean).join(" · ");
    $("#verdictTitle").textContent = d.label;
    $("#summary").textContent = d.writeup?.summary || d.sub;
    $("#reasons").innerHTML = d.reasons.map((r) => `<li class="${r.level}"><strong>${esc(r.title)}</strong><p>${esc(r.detail)}</p><p class="cite">${esc(r.cite)}${r.tag !== "P" ? " · secondary source" : ""}</p></li>`).join("");

    const rec = d.recalls || [];
    $("#recallSec").hidden = !rec.length;
    $("#recallList").innerHTML = rec.map((r) => {
      const img = r.images?.[0];
      const badge = r.remedied ? `<span class="badge fixed">Fix appears done</span>` : `<span class="badge ${r.match}">${r.match === "definite" ? "Matches this item" : "Possible match"}</span>`;
      return `<div class="recall">${img ? `<div><img src="${esc(img.url)}" alt="${esc(img.caption)}" loading="lazy"><p class="credit">Image: U.S. CPSC recall #${esc(r.id)}</p></div>` : "<div></div>"}
        <div>${badge}${r.deaths ? `<span class="badge deaths">${r.deaths} death${r.deaths > 1 ? "s" : ""} reported</span>` : ""}
          <p class="rt">${esc(r.title)}</p>
          <p class="meta">${esc(r.source)} ${esc(r.source === "NHTSA" ? "campaign" : "recall")} ${esc(r.id)} · ${esc(r.date)}${r.units ? " · " + esc(r.units) : ""}${r.begin ? ` · made ${esc(r.begin)} to ${esc(r.end)}` : ""}</p>
          ${r.hazard ? `<p class="rem"><b>Hazard:</b> ${esc(r.hazard.slice(0, 260))}</p>` : ""}
          ${r.remedy ? `<p class="rem"><b>Remedy:</b> ${esc(r.remedy.slice(0, 260))}</p>` : ""}
          ${r.why ? `<p class="why">${esc(r.why)}</p>` : ""}
          <p class="meta"><a href="${esc(r.url)}" target="_blank" rel="noopener">Read the official notice</a></p></div></div>`;
    }).join("");

    const cs = d.car_seat;
    $("#carSec").hidden = !cs;
    if (cs) {
      let bar = "";
      if (cs.dom && cs.expires) {
        const a = new Date(cs.dom), b = new Date(cs.expires), now = new Date();
        const pct = Math.max(0, Math.min(100, 100 * (now - a) / (b - a)));
        bar = `<div class="life-bar" role="img" aria-label="Lifespan from ${monthYear(cs.dom)} to ${monthYear(cs.expires)}"><span class="now" style="left:${pct}%"></span></div>
          <div class="life-ends"><span>Made ${monthYear(cs.dom)}</span><span>Expires ${monthYear(cs.expires)}</span></div>`;
      }
      $("#carBody").innerHTML = `<div class="life">${bar}<p>${cs.expires ? `Expiration: <b>${monthYear(cs.expires)}</b> (${esc(cs.basis)}).` : "We couldn't find a manufacture or expiration date. Ask for the label photo."}</p>
        ${cs.life_note ? `<p class="cite">${esc(cs.life_note)}${cs.life_tag !== "P" ? " (retailer sources; read the printed date)" : " (manufacturer guidance)"}</p>` : ""}</div>`;
    }

    $("#sellerMsg").textContent = d.writeup?.seller_message || "";
    $("#altText").textContent = d.writeup?.safer_alternative || "";
    $("#copyBtn").onclick = async () => { try { await navigator.clipboard.writeText($("#sellerMsg").textContent); $("#copyBtn").textContent = "Copied"; setTimeout(() => ($("#copyBtn").textContent = "Copy message"), 1500); } catch {} };
    $("#checkSec").hidden = !d.checklist?.length;
    $("#checkList").innerHTML = (d.checklist || []).concat(d.questions ? [] : []).map((c) => `<li>${esc(c)}</li>`).join("");

    const steps = d.pipeline || [];
    const calls = d.calls || [];
    $("#howBody").innerHTML = `<table><thead><tr><th>Step</th><th>Done by</th></tr></thead><tbody>
      ${steps.map((s) => `<tr><td>${esc(s.step)}${s.detail ? `<br><small>${esc(s.detail)}</small>` : ""}</td><td>${esc(s.model || "Rules engine (no AI)")}</td></tr>`).join("")}</tbody></table>
      ${calls.length ? `<p>${calls.length} model calls · ${calls.reduce((a, c) => a + c.seconds, 0).toFixed(1)}s · $${calls.reduce((a, c) => a + c.cost_usd, 0).toFixed(4)}</p>` : ""}
      ${d.news?.checked ? `<p>Recent news check (Tavily): ${d.news.new_recall ? `possible new recall: <a href="${esc(d.news.url)}" target="_blank" rel="noopener">${esc(d.news.headline)}</a>` : "nothing newer than our recall data."}</p>` : ""}
      ${d.what_i_see ? `<p>What the vision model saw: ${esc(d.what_i_see)}</p>` : ""}
      <p>Bans, standards and car seat lifespans come from a rules engine citing federal rules (16 CFR, Safe Sleep for Babies Act, FMVSS 213) and manufacturer guidance. Recalls come from a local copy of the CPSC and NHTSA databases (checked ${esc(d.rules_verified_as_of)}). AI models read the photos, read recall notices to decide if your exact model is covered, and write the summary; they don't set the verdict.</p>`;
  }
})();
