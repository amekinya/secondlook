const api = document.getElementById("api");
chrome.storage.sync.get({ api: "" }, (v) => (api.value = v.api));
api.addEventListener("change", () => chrome.storage.sync.set({ api: api.value.trim() }));

document.getElementById("scan").addEventListener("click", async () => {
  const base = api.value.trim();
  if (!base) { api.focus(); api.placeholder = "Enter your SecondLook server first"; return; }
  chrome.storage.sync.set({ api: base });
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["sl-overlay.js", "adapters.js"] });
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: (base) => {
      if (!window.__slStarted) {
        window.__slStarted = true;
        window.SecondLook.init({ api: base, demo: false, autostart: true, findCards: window.SecondLookFindCards });
      } else {
        document.querySelector(".sl-btn")?.click();
      }
    },
    args: [base],
  });
  window.close();
});
