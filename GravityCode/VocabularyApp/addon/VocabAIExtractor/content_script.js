/*
 * VocabAIExtractor — content script
 * Nhiệm vụ: đọc job từ bridge (127.0.0.1:5690), gửi prompt lên web AI,
 * chờ nội dung ổn định, trích HTML + ảnh (base64) rồi POST về bridge.
 *
 * Kỹ thuật mượn từ addon AskCpl (CopilotWordExportAddon):
 *  - DOM delta-extraction (đánh dấu trước khi gửi)
 *  - GIỮ block chỉ chứa <img>  (content_script.js:928-935)
 *  - Cap dung lượng IPC (MAX_HTML_BYTES = 2MB)
 *  - isErrorContent(): length guard 400 + \b503\b
 *  - validateContent(): dùng TỶ LỆ KÝ TỰ (CJK không có khoảng trắng)
 *  - Anti-stuck: 120s không đổi + không còn generating
 *  - Keepalive: silent audio + Web Locks (chống throttle tab ẩn)
 */

const BRIDGE_PORT = 5690;
const TOKEN_HEADER = "X-Vocab-Bridge";
const MAX_HTML_BYTES = 2 * 1024 * 1024;
const MIN_WAIT_MS = 8000;
const MAX_TOTAL_MS = 240000;
const STABLE_MS = 12000;
const STABLE_DELTA = 30;

/* Cấu hình chờ RIÊNG theo nền tảng.
   Grok stream Next.js chậm → cửa sổ ổn định dài hơn (20s) và hạn chờ 90_000
   (dài hơn nhiều so với STABLE_MS 12s mặc định). */
const PLATFORM_WAIT = {
  grok: { stableMs: 20000, maxWaitMs: 90000 },
  claude: { stableMs: 15000, maxWaitMs: 90000 },
  perplexity: { stableMs: 15000, maxWaitMs: 90000 },
  deepseek: { stableMs: 15000, maxWaitMs: 90000 }
};

let BRIDGE_TOKEN = "";
let isRunning = false;
let currentJob = null;
let forcedPlatform = null;   // nền tảng chọn trong popup (fallback khi không nhận diện được host)
const appLog = [];

/* ─────────── Selector theo nền tảng ─────────── */
const PLATFORMS = {
  gemini: {
    input: 'rich-textarea div[contenteditable="true"]',
    inputAlt: ".ql-editor",
    inputAlt2: 'textarea[aria-label*="Enter" i], textarea[aria-label*="Nhập" i]',
    send: 'button[aria-label*="Send" i], button[aria-label*="Gửi" i]',
    content: "message-content",
    contentAll: "user-query, model-response",
    generating: 'button[aria-label*="Stop" i], button[aria-label*="Dừng tạo" i], .typing-indicator'
  },
  chatgpt: {
    input: "#prompt-textarea",
    inputAlt: 'div[contenteditable="true"]',
    inputAlt2: "textarea",
    send: 'button[data-testid="send-button"]',
    content: "div.markdown",
    contentAll: 'article[data-testid^="conversation-turn"]',
    generating: 'button[data-testid="stop-button"], .result-streaming'
  },
  copilot: {
    input: 'div[role="textbox"][contenteditable="true"]',
    inputAlt: "textarea",
    inputAlt2: 'div[contenteditable="true"]',
    send: 'button[data-automation-id*="send" i]',
    content: ".ac-textBlock, .markdown-body",
    contentAll: "cib-chat-turn, .chat-turn, [class*='chat-turn']",
    generating: '[data-stop-button], .stop-generating-button'
  },
  /* Grok — DOM đổi rất nhanh ⇒ nhiều selector fallback */
  grok: {
    input: 'div[data-testid="grok-input"]',
    inputAlt: 'textarea[data-testid="grok-input"]',
    inputAlt2: 'div[contenteditable="true"][role="textbox"]',
    send: 'button[data-testid="submit-button"], button[aria-label*="Send" i], button[aria-label*="Gửi" i]',
    content: 'div[data-testid="grok-response"], .response-content-markdown, .prose',
    contentAll: '[data-testid="grok-response"], .response-content-markdown',
    generating: 'button[data-testid="stop-button"], button[aria-label*="Stop" i], [data-testid="grok-loading"]'
  },
  /* Claude — ô nhập là ProseMirror contenteditable */
  claude: {
    input: 'div[contenteditable="true"]',
    inputAlt: "div[ProseMirror]",
    inputAlt2: "textarea",
    send: 'button[aria-label*="Send" i], button[aria-label*="Gửi" i]',
    content: 'div[data-testid="claude-message"], .font-claude-message',
    contentAll: '[data-testid="claude-message"], .font-claude-message',
    generating: 'button[aria-label*="Stop" i], .stop-button'
  },
  /* Perplexity */
  perplexity: {
    input: 'textarea[data-testid="ask-input"]',
    inputAlt: "textarea",
    inputAlt2: 'div[contenteditable="true"]',
    send: 'button[aria-label*="Submit" i], button[aria-label*="Send" i]',
    content: ".prose, div[contentid]",
    contentAll: "div[contentid]",
    generating: 'button[aria-label*="Stop" i]'
  },
  /* DeepSeek */
  deepseek: {
    input: "textarea#dummy-input",
    inputAlt: "textarea",
    inputAlt2: 'div[contenteditable="true"]',
    send: 'button[aria-label*="Send" i], button[aria-label*="Gửi" i]',
    content: ".ds-markdown--block, .prose",
    contentAll: ".ds-markdown--block",
    generating: 'button[aria-label*="Stop" i]'
  }
};

function platformKey() {
  const h = location.hostname;
  if (h.includes("gemini.google")) return "gemini";
  if (h.includes("chatgpt") || h.includes("chat.openai")) return "chatgpt";
  if (h.includes("copilot") || h.includes("bing.com")) return "copilot";
  if (h === "grok.com" || h.endsWith(".grok.com")) return "grok";
  if (h === "claude.ai" || h.endsWith(".claude.ai")) return "claude";
  if (h === "perplexity.ai" || h.endsWith(".perplexity.ai")) return "perplexity";
  if (h === "deepseek.com" || h.endsWith(".deepseek.com")) return "deepseek";
  return null;
}

/* Nền tảng đang chạy: hostname luôn ưu tiên, lựa chọn trong popup chỉ là fallback */
function resolvePlatform() {
  const pk = platformKey();
  if (pk) return pk;
  if (forcedPlatform && PLATFORMS[forcedPlatform]) return forcedPlatform;
  return null;
}

/* ─────────── Log ─────────── */
function log(msg) {
  appLog.push({ t: Date.now(), msg: String(msg) });
  if (appLog.length > 300) appLog.shift();
  try {
    chrome.runtime.sendMessage({ action: "add_log", msg: String(msg) });
  } catch (e) { /* SW chưa sẵn sàng — bỏ qua */ }
}

async function bridgeFetch(path, options = {}) {
  const url = `http://127.0.0.1:${BRIDGE_PORT}${path}`;
  const opts = Object.assign({ headers: {} }, options);
  opts.headers = Object.assign({}, opts.headers, { "Content-Type": "application/json" });
  if (BRIDGE_TOKEN) opts.headers[TOKEN_HEADER] = BRIDGE_TOKEN;
  const res = await fetch(url, opts);
  const text = await res.text();
  try { return { status: res.status, data: JSON.parse(text) }; }
  catch (e) { return { status: res.status, data: { raw: text } }; }
}

/* ─────────── Tìm & điền ô nhập ─────────── */
function findInput(sel) {
  let el = document.querySelector(sel.input);
  if (el) return el;
  if (sel.inputAlt) {
    el = document.querySelector(sel.inputAlt);
    if (el) return el;
  }
  if (sel.inputAlt2) {
    el = document.querySelector(sel.inputAlt2);
    if (el) return el;
  }
  // fallback: contenteditable bất kỳ (bỏ qua editor lớn)
  const cds = Array.from(document.querySelectorAll('div[contenteditable="true"]'));
  const ok = cds.filter(c => !(c.scrollHeight > 500 || c.children.length > 20));
  if (ok.length) return ok[0];
  if (document.activeElement && document.activeElement.isContentEditable) {
    return document.activeElement;
  }
  return null;
}

function fillInput(el, text) {
  el.focus();
  if (el.isContentEditable) {
    el.innerHTML = "";
    const t = document.createTextNode(text);
    el.appendChild(t);
    el.dispatchEvent(new InputEvent("input", {
      bubbles: true, inputType: "insertText", data: text
    }));
  } else {
    const proto = el.tagName === "TEXTAREA"
      ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value");
    if (setter && setter.set) setter.set.call(el, text);
    else el.value = text;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }
  // Một số framework cần thêm event ở thẻ cha
  const parent = el.closest("rich-textarea, form, div");
  if (parent) {
    parent.dispatchEvent(new Event("input", { bubbles: true }));
  }
}

/* ─────────── Trích nội dung ─────────── */
/* Tìm phần tử cuối cùng theo THỨ TỰ ưu tiên của selector ("a, b" ⇒ a trước b) */
function queryLast(sel) {
  const parts = String(sel || "").split(",").map(s => s.trim()).filter(Boolean);
  for (const p of parts) {
    let g = [];
    try { g = document.querySelectorAll(p); } catch (e) { continue; }
    if (g.length) return g[g.length - 1];
  }
  return null;
}

/* Tìm phần tử ĐẦU TIÊN theo thứ tự ưu tiên của selector ("a, b" ⇒ a trước b) */
function queryFirst(sel) {
  const parts = String(sel || "").split(",").map(s => s.trim()).filter(Boolean);
  for (const p of parts) {
    let e = null;
    try { e = document.querySelector(p); } catch (err) { continue; }
    if (e) return e;
  }
  return null;
}

function snapshotBeforeSend() {
  const roots = document.querySelectorAll(
    "message-content, div.markdown, .ac-textBlock, cib-chat-turn, " +
    '[data-testid="grok-response"], .response-content-markdown, ' +
    '[data-testid="claude-message"], .font-claude-message, ' +
    ".ds-markdown--block, div[contentid]"
  );
  roots.forEach(r => r.setAttribute("data-vocab-snap", "1"));
}

function clearSnapshot() {
  document.querySelectorAll("[data-vocab-snap]").forEach(e => e.removeAttribute("data-vocab-snap"));
}

function topLevelBlocks(container) {
  const all = Array.from(container.querySelectorAll("*"));
  const set = new Set(all);
  return all.filter(el => {
    let p = el.parentElement;
    while (p) { if (set.has(p)) return false; p = p.parentElement; }
    return true;
  });
}

function extractDelta(sel) {
  const cont = queryLast(sel.content);
  if (!cont) return null;
  const blocks = topLevelBlocks(cont);
  const kept = blocks.filter(el => {
    const tag = (el.tagName || "").toLowerCase();
    if (["script", "style", "svg", "path", "button", "iframe", "nav"].includes(tag)) return false;
    const txt = (el.innerText || "").trim();
    if (txt === "") {
      // GIỮ block chỉ chứa <img> — đây là nơi giữ ảnh trong HTML
      if (!el.querySelector("img")) return false;
    }
    return true;
  });
  let html = kept.map(el => el.outerHTML).join("\n");
  if (html.length > MAX_HTML_BYTES) html = html.slice(0, MAX_HTML_BYTES);
  return { html, text: (cont.innerText || "") };
}

function isGenerating(sel) {
  try { return !!document.querySelector(sel.generating); } catch (e) { return false; }
}

function isErrorContent(text) {
  if (!text) return true;
  if (text.length > 400) return false;
  const bad = ["503", "rate limit", "quota exceeded", "try again later",
    "hết lượt", "too many requests", "429", "unavailable"];
  const low = text.toLowerCase();
  for (const b of bad) {
    if (b === "503" || b === "429") {
      if (new RegExp("\\b" + b + "\\b").test(text)) return true;
    } else if (low.includes(b)) return true;
  }
  return false;
}

function validateContent(text) {
  if (!text) return false;
  if (text.length < 60) return false;
  // TỶ LỆ KÝ TỰ (CJK không có khoảng trắng) — thay vì đếm từ
  const charCount = text.replace(/\s/g, "").length;
  if (charCount < 50) return false;
  if (isErrorContent(text)) return false;
  return true;
}

async function waitForResult(sel, pk) {
  /* Chờ nội dung ổn định: dùng cửa sổ STABLE_MS, riêng Grok (stream Next.js
     chậm) dùng PLATFORM_WAIT[pk].stableMs dài hơn + hạn chờ maxWaitMs riêng. */
  const cfg = PLATFORM_WAIT[pk] || {};
  const stableMs = cfg.stableMs || STABLE_MS;
  const maxWaitMs = cfg.maxWaitMs || 120000;   // hạn "kẹt" (không đổi bao lâu thì bỏ)
  const start = Date.now();
  let lastLen = -1;
  let stableSince = Date.now();
  while (Date.now() - start < MAX_TOTAL_MS) {
    await sleep(1500);
    const res = extractDelta(sel);
    const len = res ? res.text.length : 0;
    if (len && len !== lastLen) { lastLen = len; stableSince = Date.now(); }
    if (len && (Date.now() - stableSince) >= stableMs && !isGenerating(sel)) {
      return res;
    }
    // chống kẹt: không đổi quá lâu + không generating ⇒ coi như xong
    if (lastLen > 0 && (Date.now() - stableSince) > maxWaitMs && !isGenerating(sel)) {
      return res;
    }
  }
  return extractDelta(sel);
}

/* ─────────── Trích ảnh (base64) ─────────── */
function collectImages(sel) {
  const cont = queryLast(sel.content);
  if (!cont) return [];
  const out = [];
  const imgs = Array.from(cont.querySelectorAll("img"));
  for (let i = 0; i < imgs.length; i++) {
    const im = imgs[i];
    const raw = im.currentSrc || im.src || im.getAttribute("src") || "";
    const alt = (im.alt || "").toLowerCase();
    if (!raw) continue;
    if (["icon", "avatar", "logo", "sticker", "badge", "biểu tượng", "ảnh đại diện"]
      .some(t => alt.includes(t))) continue;
    const w = im.naturalWidth || 0, h = im.naturalHeight || 0;
    if (w && w <= 150) continue;
    if (h && h <= 150) continue;
    out.push({ index: out.length + 1, url: raw, alt: im.alt || "", w, h, b64: "" });
  }
  return out;
}

async function imageToB64(img) {
  try {
    // fetch trong PAGE-CONTEXT ⇒ browser tự gắn Referer/Origin đúng (chống hotlink)
    const resp = await fetch(img.url, { credentials: "include" });
    if (!resp.ok) return "";
    const ct = (resp.headers.get("content-type") || "").toLowerCase();
    if (!ct.startsWith("image/") || ct === "image/svg+xml") return "";
    const blob = await resp.blob();
    if (blob.size < 5 * 1024) return "";
    return await blobToB64(blob);
  } catch (e) {
    return "";
  }
}

function blobToB64(blob) {
  return new Promise(resolve => {
    const fr = new FileReader();
    fr.onloadend = () => {
      const s = String(fr.result || "");
      const i = s.indexOf(",");
      resolve(i >= 0 ? s.slice(i + 1) : "");
    };
    fr.onerror = () => resolve("");
    fr.readAsDataURL(blob);
  });
}

/* ─────────── Keepalive chống throttle ─────────── */
let keepAliveTimer = null;
let wakeLock = null;
function setupKeepAlive() {
  try {
    const audio = new Audio(
      "data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
    );
    audio.loop = true; audio.volume = 0.01;
    audio.play().catch(() => { });
    setInterval(() => { if (audio.paused) audio.play().catch(() => { }); }, 5000);
  } catch (e) { /* bỏ qua */ }
  try {
    if (navigator.locks) {
      navigator.locks.request("vocab_wakeLock", { mode: "shared" },
        () => new Promise(res => { wakeLock = res; }));
    }
  } catch (e) { /* bỏ qua */ }
  keepAliveTimer = setInterval(() => {
    try { chrome.runtime.sendMessage({ action: "ping" }); } catch (e) { }
  }, 20000);
}

function teardownKeepAlive() {
  if (keepAliveTimer) clearInterval(keepAliveTimer);
  keepAliveTimer = null;
  try { if (wakeLock) wakeLock(); } catch (e) { }
}

/* ─────────── Vòng lặp chính ─────────── */
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function runLoop() {
  if (isRunning) return;
  isRunning = true;
  setupKeepAlive();
  const pk = resolvePlatform();
  if (!pk) { log("❌ Trang này không được hỗ trợ."); isRunning = false; teardownKeepAlive(); return; }
  const sel = PLATFORMS[pk];
  log(`▶ Nền tảng: ${pk}`);

  while (isRunning) {
    let job = null;
    try {
      const r = await bridgeFetch("/api/vocab/next");
      if (r.status === 401) { log("❌ Bridge từ chối token — kiểm tra lại token."); break; }
      if (r.status === 404 || !r.data || !r.data.ok) { await sleep(4000); continue; }
      job = r.data;
      BRIDGE_TOKEN = job.bridge_token || BRIDGE_TOKEN;
      currentJob = job;
      log(`📥 Nhận job: ngày ${job.day} (${job.course})`);
    } catch (e) {
      log(`⚠ Không kết nối được bridge: ${e.message}`);
      await sleep(5000);
      continue;
    }

    try {
      const el = findInput(sel);
      if (!el) { log("⚠ Không tìm thấy ô nhập."); await postResult(job, null, "no_input"); continue; }
      snapshotBeforeSend();
      fillInput(el, job.prompt);
      await sleep(800);
      const sendBtn = queryFirst(sel.send);
      if (sendBtn) { try { sendBtn.click(); } catch (e) { } }
      else {
        el.dispatchEvent(new KeyboardEvent("keydown",
          { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true }));
      }
      log("⏳ Đã gửi — chờ AI trả lời...");
      const res = await waitForResult(sel, pk);
      clearSnapshot();
      if (!res || !validateContent(res.text)) {
        log("⚠ Nội dung không hợp lệ / bị lỗi.");
        await postResult(job, null, "invalid_content");
        continue;
      }
      const imgs = collectImages(sel);
      for (const im of imgs) { im.b64 = await imageToB64(im); }
      log(`✅ Nhận ${res.text.length} ký tự, ${imgs.filter(i => i.b64).length}/${imgs.length} ảnh.`);
      await postResult(job, { html: res.html, text: res.text, images: imgs }, "");
    } catch (e) {
      log(`⚠ Lỗi: ${e.message}`);
      await postResult(job, null, String(e.message || e));
    } finally {
      currentJob = null;
    }
  }
  isRunning = false;
  teardownKeepAlive();
}

async function postResult(job, payload, error) {
  const body = {
    job_id: job.job_id, platform: job.platform, course: job.course,
    day: job.day, status: error ? "error" : "ok",
    elapsed_ms: Date.now() - (job._t0 || Date.now()),
    html: payload ? payload.html : "",
    markdown: payload ? payload.text : "",
    images: payload ? payload.images : [],
    error: error || null
  };
  for (let attempt = 1; attempt <= 4; attempt++) {
    try {
      const r = await bridgeFetch("/api/vocab/result", {
        method: "POST", body: JSON.stringify(body)
      });
      if (r.status === 200) return true;
      log(`⚠ POST result lỗi HTTP ${r.status} (lần ${attempt})`);
    } catch (e) {
      log(`⚠ POST result thất bại (lần ${attempt}): ${e.message}`);
    }
    await sleep(1000 * attempt);
  }
  return false;
}

/* ─────────── Message handler ─────────── */
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    switch (msg.action) {
      case "start_loop":
        if (msg.platform) forcedPlatform = msg.platform;
        if (!isRunning) { runLoop(); }
        sendResponse({ ok: true, running: isRunning, platform: resolvePlatform() });
        break;
      case "set_platform":
        forcedPlatform = msg.platform || null;
        sendResponse({ ok: true, platform: resolvePlatform() });
        break;
      case "stop_loop":
        isRunning = false;
        teardownKeepAlive();
        sendResponse({ ok: true });
        break;
      case "get_status":
        sendResponse({
          ok: true, running: isRunning, platform: resolvePlatform(),
          job: currentJob ? { day: currentJob.day, course: currentJob.course } : null
        });
        break;
      case "get_log":
        sendResponse({ ok: true, log: appLog.slice(-100) });
        break;
      case "set_token":
        BRIDGE_TOKEN = msg.token || "";
        sendResponse({ ok: true });
        break;
      case "extract_current":
        {
          const pk = resolvePlatform();
          if (!pk) { sendResponse({ ok: false, error: "unsupported" }); break; }
          const res = extractDelta(PLATFORMS[pk]);
          sendResponse({ ok: !!res, html: res ? res.html : "", text: res ? res.text : "" });
        }
        break;
      default:
        sendResponse({ ok: false });
    }
  })();
  return true;
});

log("✅ VocabAIExtractor đã sẵn sàng.");
