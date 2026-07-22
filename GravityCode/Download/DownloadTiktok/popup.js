// popup.js — mycustomFaveTT
// Log được lưu trong chrome.storage.local key "customFaveTT_log"
// HOÀN TOÀN TÁCH BIỆT với ui_offline/ — update UI không bao giờ xóa log

const LOG_KEY = "customFaveTT_log";
const MAX_LOGS = 200;

// ---- Render log ----
function formatTime(ts) {
  const d = new Date(ts);
  return `${d.getHours().toString().padStart(2,"0")}:${d.getMinutes().toString().padStart(2,"0")}:${d.getSeconds().toString().padStart(2,"0")}`;
}

function renderLogs(logs) {
  const container = document.getElementById("log-container");
  const empty = document.getElementById("log-empty");
  const count = document.getElementById("log-count");

  if (!logs || logs.length === 0) {
    empty.style.display = "block";
    count.textContent = "0";
    // Xóa các log item cũ nếu có
    [...container.querySelectorAll(".log-item")].forEach(el => el.remove());
    return;
  }

  empty.style.display = "none";
  count.textContent = logs.length;

  // Rebuild toàn bộ log (đơn giản và đáng tin cậy hơn incremental)
  [...container.querySelectorAll(".log-item")].forEach(el => el.remove());

  // Hiện theo thứ tự mới nhất ở trên
  const sorted = [...logs].reverse();
  const fragment = document.createDocumentFragment();

  for (const item of sorted) {
    const div = document.createElement("div");
    div.className = `log-item ${item.type}`;

    const icon = item.type === "downloading" ? "⏬"
               : item.type === "done"        ? "✅"
               : item.type === "error"       ? "❌"
               :                               "ℹ️";

    const idPart = item.videoId ? `<span class="log-id">#${item.videoId.slice(-6)}</span> ` : "";
    const reasonPart = item.reason ? `<br><span style="opacity:0.7">→ ${item.reason}</span>` : "";

    div.innerHTML = `<span class="log-time">${formatTime(item.ts)}</span><span class="log-icon">${icon}</span>${idPart}${item.msg}${reasonPart}`;
    fragment.appendChild(div);
  }

  // Chèn sau log-empty (không xóa nó, chỉ ẩn)
  container.appendChild(fragment);
}

// ---- Load log từ storage ----
function loadLogs() {
  chrome.storage.local.get(LOG_KEY, (result) => {
    renderLogs(result[LOG_KEY] || []);
  });
}

// ---- Lắng nghe log mới real-time ----
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes[LOG_KEY]) {
    renderLogs(changes[LOG_KEY].newValue || []);
    // Auto-scroll về đầu (mới nhất)
    document.getElementById("log-container").scrollTop = 0;
  }
});

// ---- Nút Mở TikTok ----
document.getElementById("btn-open-tiktok").addEventListener("click", () => {
  chrome.tabs.create({ url: "https://www.tiktok.com" });
  window.close();
});

// ---- Nút Xoá Log ----
document.getElementById("btn-clear-log").addEventListener("click", () => {
  chrome.storage.local.set({ [LOG_KEY]: [] }, () => {
    renderLogs([]);
  });
});

// ---- Nút Cập nhật UI từ Tác giả ----
// Gửi lệnh sang b.js để scrape lại ui.myfavett.com
document.getElementById("btn-update-ui").addEventListener("click", () => {
  const statusEl = document.getElementById("update-status");
  const btn = document.getElementById("btn-update-ui");

  btn.disabled = true;
  btn.textContent = "⏳ Đang cập nhật...";
  statusEl.style.display = "block";
  statusEl.textContent = "Đang kết nối với ui.myfavett.com...";

  chrome.runtime.sendMessage({ action: "update_ui" }, (response) => {
    btn.disabled = false;
    btn.textContent = "🔄 Cập nhật UI";

    if (chrome.runtime.lastError) {
      statusEl.style.color = "#fe2c55";
      statusEl.textContent = "❌ Lỗi: " + chrome.runtime.lastError.message;
      return;
    }

    if (response && response.success) {
      statusEl.style.color = "#4caf50";
      statusEl.textContent = "✅ Cập nhật xong! Reload extension để áp dụng.";
    } else {
      statusEl.style.color = "#fe2c55";
      statusEl.textContent = "❌ " + (response ? response.error : "Không có phản hồi");
    }

    setTimeout(() => { statusEl.style.display = "none"; }, 6000);
  });
});

// ---- Khởi tạo ----
loadLogs();
