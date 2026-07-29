document.addEventListener('DOMContentLoaded', () => {
    const btnToggle = document.getElementById('btnToggle');
    const statusDiv = document.getElementById('status');
    const logDiv = document.getElementById('log');

    const btnExport = document.getElementById('btnExport');

    function updateUI() {
        chrome.storage.local.get(['auto_create_running', 'key_count', 'last_log', 'api_keys'], (res) => {
            const count = (res.api_keys && res.api_keys.length) || res.key_count || 0;
            if (res.auto_create_running) {
                statusDiv.innerText = `Status: Running (Keys: ${count})`;
                btnToggle.innerText = "Stop Auto Create";
                btnToggle.className = "stop";
            } else {
                statusDiv.innerText = `Status: Stopped (Keys: ${count})`;
                btnToggle.innerText = "Start Auto Create";
                btnToggle.className = "";
            }
            if (res.last_log) {
                logDiv.innerText = res.last_log;
            }
        });
    }

    btnToggle.addEventListener('click', () => {
        chrome.storage.local.get(['auto_create_running'], (res) => {
            const isRunning = !!res.auto_create_running;
            chrome.storage.local.set({ auto_create_running: !isRunning, last_log: "Toggled state..." }, () => {
                updateUI();
            });
        });
    });

    const btnScrapeOld = document.getElementById('btnScrapeOld');
    if (btnScrapeOld) {
        btnScrapeOld.addEventListener('click', () => {
            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                if (tabs[0]) {
                    chrome.tabs.sendMessage(tabs[0].id, { action: "SCRAPE_OLD_KEYS" }, (response) => {
                        if (response && response.status === "ok") {
                            chrome.storage.local.set({ last_log: "Đang cào " + response.count + " Key cũ..." });
                            // Tự động tải JSON sau khi quét xong (chờ 1 chút để storage cập nhật)
                            setTimeout(() => {
                                if (btnExport) btnExport.click();
                            }, 500);
                        } else {
                            chrome.storage.local.set({ last_log: "Không tìm thấy nút Copy nào. Hãy đảm bảo bạn đang ở trang API Keys." });
                        }
                    });
                }
            });
        });
    }

    btnExport.addEventListener('click', () => {
        chrome.storage.local.get(['api_keys'], (res) => {
            const keys = res.api_keys || [];
            if (keys.length === 0) {
                alert("Chưa có API key nào được thu thập.");
                return;
            }
            
            const jsonStr = JSON.stringify(keys, null, 2);
            const blob = new Blob(['\uFEFF' + jsonStr], {type: "application/json;charset=utf-8"});
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `gemini_api_keys_${new Date().getTime()}.json`;
            a.click();
            URL.revokeObjectURL(url);
            
            // Hiện thông báo rồi tự đóng popup sau 1.5s
            logDiv.innerText = `✅ Đã xuất ${keys.length} key! Popup đóng sau 1.5s...`;
            setTimeout(() => { window.close(); }, 1500);
        });
    });

    updateUI();
    setInterval(updateUI, 1000);
});
