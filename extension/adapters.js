/* Find listing cards on common marketplace layouts, with a generic fallback.
   Each card: { el, stampHost, id, title, text, image }. Runs in the page (content script). */
(() => {
  const PRICE = /(\$|£|€)\s?\d/;
  const text = (el) => (el?.innerText || "").replace(/\s+/g, " ").trim();
  const imgOf = (el) => {
    const im = [...el.querySelectorAll("img")].find((i) => i.naturalWidth >= 100 || i.width >= 100) || el.querySelector("img");
    return im ? (im.currentSrc || im.src) : "";
  };
  const host = (el) => el.querySelector("img")?.parentElement || el;

  const SITES = [
    { test: () => /facebook\.com$/.test(location.hostname), sel: 'a[href*="/marketplace/item/"]' },
    { test: () => /craigslist\.org$/.test(location.hostname), sel: "li.cl-search-result, li.result-row, .gallery-card" },
    { test: () => /ebay\./.test(location.hostname), sel: "li.s-item, li.s-card" },
    { test: () => /offerup\.com$/.test(location.hostname), sel: 'a[href*="/item/detail/"]' },
    { test: () => /mercari\.com$/.test(location.hostname), sel: '[data-testid="ItemContainer"], a[href*="/item/"]' },
  ];

  function generic() {
    // A listing card: smallest element containing one sizable image and a price.
    const out = new Set();
    document.querySelectorAll("img").forEach((img) => {
      if ((img.naturalWidth || img.width) < 100) return;
      let el = img.parentElement;
      for (let i = 0; i < 6 && el && el !== document.body; i++, el = el.parentElement) {
        if (PRICE.test(text(el)) && el.querySelectorAll("img").length <= 3) { out.add(el); break; }
      }
    });
    return [...out];
  }

  window.SecondLookFindCards = () => {
    const site = SITES.find((s) => s.test());
    let els = site ? [...document.querySelectorAll(site.sel)] : [];
    if (!els.length) els = generic();
    const seen = new Set();
    return els.map((el, i) => {
      const image = imgOf(el);
      const t = text(el);
      if (!image || !t || seen.has(image)) return null;
      seen.add(image);
      const lines = t.split(/(?<=\S)\s{2,}|\n/);
      return { el, stampHost: host(el), id: "c" + i, title: t.slice(0, 140), text: t.slice(0, 600), image };
    }).filter(Boolean).slice(0, 60);
  };
})();
