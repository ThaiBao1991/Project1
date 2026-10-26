/*
 * VocabAIExtractor — background service worker
 * Vai trò: relay message popup ↔ content script, ping giữ SW thức, log queue.
 *
 * Lưu ý MV3: `URL.createObjectURL` KHÔNG hoạt động trong service worker →
 * khi cần download file phải dùng data-URI base64 (xem downloadByDataUri).
 */

const BRIDGE_PORT = 5690;
const TOKEN_HEADER = "X-Vocab-Bridge";
const logQueue = [];
const MAX_LOG = 200;

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({ auto_create_running: false, last_log: "" });
});

function addLog(msg) {
  logQueue.push({ t: Date.now(), msg: String(msg) });
  if (logQueue.length > MAX_LOG) logQueue.shift();
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  switch (msg.action) {
    case "add_log":
      addLog(msg.msg);
      sendResponse({ ok: true });
      break;
    case "ping":
      sendResponse({ ok: true, t: Date.now() });
      break;
    case "get_log":
      sendResponse({ ok: true, log: logQueue.slice(-80) });
      break;
    case "download_by_data_uri":
      downloadByDataUri(msg.url, msg.filename)
        .then(id => sendResponse({ ok: true, id }))
        .catch(e => sendResponse({ ok: false, error: String(e) }));
      return true;
    default:
      sendResponse({ ok: false });
  }
  return true;
});

/* Tải file bằng data-URI base64 (workaround cho MV3 service worker) */
async function downloadByDataUri(dataUri, filename) {
  pendingDownloadNames.push(filename);
  return new Promise((resolve, reject) => {
    chrome.downloads.download(
      { url: dataUri, filename: filename, saveAs: false, conflictAction: "overwrite" },
      dlId => {
        if (chrome.runtime.lastError) reject(new Error(chrome.runtime.lastError.message));
        else resolve(dlId);
      }
    );
  });
}

/* Ép tên file + thư mục (Edge bỏ qua `filename` nếu không có bước này) */
const pendingDownloadNames = [];
chrome.downloads.onDeterminingFilename.addListener((item, suggest) => {
  if (pendingDownloadNames.length) {
    suggest({ filename: pendingDownloadNames.shift(), conflictAction: "overwrite" });
  }
});

/* Đánh thức SW định kỳ (ngăn SW ngủ khi tab chạy lâu) */
setInterval(() => { /* SW tự thức khi có event; ping từ content script đủ */ }, 20000);
