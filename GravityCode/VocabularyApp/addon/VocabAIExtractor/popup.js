/* VocabAIExtractor — popup controller */
const BRIDGE_PORT = 5690;
const TOKEN_HEADER = "X-Vocab-Bridge";

const $ = id => document.getElementById(id);
let tabId = null;
let polling = null;

function setStatus(text, cls) {
  const el = $("status");
  el.textContent = text;
  el.className = "status" + (cls ? " " + cls : "");
}

function appendLog(msg) {
  const el = $("log");
  const line = document.createElement("div");
  line.textContent = msg;
  el.appendChild(line);
  while (el.childElementCount > 120) el.removeChild(el.firstChild);
  el.scrollTop = el.scrollHeight;
}

async function activeTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs && tabs.length ? tabs[0] : null;
}

async function checkBridge() {
  const token = ($("token").value || "").trim();
  try {
    const res = await fetch(`http://127.0.0.1:${BRIDGE_PORT}/api/vocab/status`);
    const data = await res.json();
    const okBridge = !!data && data.ok;
    if (!okBridge) { setStatus("❌ Bridge không phản hồi.", "err"); return false; }
    if (token && data.bridge_token && data.bridge_token !== token) {
      setStatus("⚠ Token KHÔNG khớp với bridge.", "err");
    } else {
      setStatus(`✅ Bridge OK — state: ${data.state} | đã lấy ${data.ok}/${data.requested} job`, "ok");
    }
    if (data.bridge_token && !$("token").value) {
      $("token").value = data.bridge_token;
    }
    return true;
  } catch (e) {
    setStatus("❌ Không kết nối được bridge (127.0.0.1:" + BRIDGE_PORT + ")", "err");
    return false;
  }
}

async function start() {
  const tab = await activeTab();
  if (!tab) { setStatus("❌ Không có tab nào.", "err"); return; }
  tabId = tab.id;
  const token = ($("token").value || "").trim();
  const platform = ($("platform").value || "").trim();
  try {
    await chrome.tabs.sendMessage(tabId, { action: "set_token", token });
  } catch (e) { /* content script chưa nạp — vẫn thử start */ }
  try {
    await chrome.tabs.sendMessage(tabId, { action: "start_loop", platform });
    setStatus(`▶ Đang chạy trên tab này${platform ? " (" + platform + ")" : ""}.`, "ok");
    startPolling();
  } catch (e) {
    setStatus("❌ Không gửi được lệnh tới tab: " + e.message, "err");
  }
}

async function stop() {
  if (tabId != null) {
    try { await chrome.tabs.sendMessage(tabId, { action: "stop_loop" }); } catch (e) { }
  }
  setStatus("⏹ Đã dừng.");
  if (polling) { clearInterval(polling); polling = null; }
}

function startPolling() {
  if (polling) clearInterval(polling);
  polling = setInterval(async () => {
    try {
      const r = await chrome.runtime.sendMessage({ action: "get_log" });
      if (r && r.log) {
        const last = r.log[r.log.length - 1];
        if (last) appendLog(`[${new Date(last.t).toLocaleTimeString()}] ${last.msg}`);
      }
      if (tabId != null) {
        const s = await chrome.tabs.sendMessage(tabId, { action: "get_status" });
        if (s && s.job) {
          setStatus(`▶ Đang xử lý ngày ${s.job.day} (${s.job.course})${s.platform ? " — " + s.platform : ""}`, "ok");
        }
      }
    } catch (e) { /* tab đã đóng */ }
  }, 1500);
}

$("btnStart").addEventListener("click", start);
$("btnStop").addEventListener("click", stop);
$("btnCheck").addEventListener("click", checkBridge);
$("token").addEventListener("change", async () => {
  const tab = await activeTab();
  if (!tab) return;
  try {
    await chrome.tabs.sendMessage(tab.id, { action: "set_token", token: $("token").value.trim() });
  } catch (e) { }
});
// Đổi nền tảng AI → báo cho content script biết (dùng khi hostname không nhận diện được)
$("platform").addEventListener("change", async () => {
  const tab = await activeTab();
  if (!tab) return;
  tabId = tab.id;
  try {
    await chrome.tabs.sendMessage(tab.id, { action: "set_platform", platform: $("platform").value });
  } catch (e) { }
});

checkBridge();
setInterval(checkBridge, 8000);
