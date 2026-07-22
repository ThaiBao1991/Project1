// b.js — background service worker (mycustomFaveTT)
// Lưu ý: chrome.action.onClicked KHÔNG còn dùng (đã có default_popup)

// Mở trang web store khi cài lần đầu
chrome.runtime.onInstalled.addListener(({ reason }) => {
  if ("install" === reason) chrome.tabs.create({ url: "https://ui.myfavett.com?route=on-install" });
});

// --- Nghe lén TikTok API để bắt header xác thực ---
chrome.webRequest.onSendHeaders.addListener(
  function (details) {
    const { initiator, method, requestHeaders, url } = details;
    if ("GET" !== method) return;
    if (initiator.startsWith("chrome-extension://")) return;
    const acceptHeader = requestHeaders.find(h => "accept" === h.name.toLowerCase());
    if (!acceptHeader) return;
    if (acceptHeader.value.includes("csv")) return;
    const ch = new BroadcastChannel("mycustomFaveTT");
    ch.postMessage({ direction: 0, type: 13, payload: { requestHeaders, url: url.split("?")[0], urlWithParams: url } });
    ch.close();
  },
  { urls: ["https://*.tiktok.com/api/post/item_list/*"] },
  ["requestHeaders"]
);

// --- Xử lý message từ popup ---
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "update_ui") {
    _scrapeAndUpdateUI(sendResponse);
    return true; // async response
  }
});

// --- Scrape ui.myfavett.com về ui_offline/ ---
async function _scrapeAndUpdateUI(sendResponse) {
  try {
    const baseUrl = "https://ui.myfavett.com";

    // Bước 1: Tải index.html
    const htmlResp = await fetch(baseUrl, { cache: "no-cache" });
    if (!htmlResp.ok) throw new Error(`HTTP ${htmlResp.status} khi tải index.html`);
    let html = await htmlResp.text();

    // Bước 2: Tìm tất cả asset (/assets/*.js, /assets/*.css)
    const assetPattern = /(?:src|href)="\/assets\/([^"]+)"/g;
    const assets = [];
    let match;
    while ((match = assetPattern.exec(html)) !== null) {
      assets.push(match[1]);
    }

    // Bước 3: Tải từng asset và chuyển thành object URL lưu vào storage
    // Vì extension không thể ghi file vào thư mục của chính nó khi runtime,
    // ta lưu nội dung vào chrome.storage.local với key đặc biệt để popup thông báo
    // rằng cần chạy lại scrape_ui.py hoặc reload extension.

    // Ghi log mô tả kết quả tải
    const assetResults = [];
    for (const asset of assets) {
      try {
        const resp = await fetch(`${baseUrl}/assets/${asset}`, { cache: "no-cache" });
        const size = parseInt(resp.headers.get("Content-Length") || "0");
        assetResults.push({ name: asset, status: resp.ok ? "ok" : resp.status, size });
      } catch (e) {
        assetResults.push({ name: asset, status: "error", error: e.message });
      }
    }

    // Lưu thông tin phiên bản mới vào storage để popup hiển thị
    await chrome.storage.local.set({
      "customFaveTT_lastUpdateCheck": {
        ts: Date.now(),
        assets: assetResults,
        note: "Để áp dụng cập nhật mới: chạy lại scrape_ui.py rồi Reload extension."
      }
    });

    // LOG KHÔNG BỊ XÓA — chỉ key "customFaveTT_lastUpdateCheck" được set,
    // key "customFaveTT_log" hoàn toàn không bị đụng vào.
    sendResponse({ success: true, assetCount: assets.length });

  } catch (err) {
    sendResponse({ success: false, error: err.message });
  }
}
