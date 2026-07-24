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
                            // Tự động tải JSON sau khi cào xong
                            setTimeout(() => {
                                if (btnExport) btnExport.click();
                            }, response.count * 500 + 1500); // Chờ click hết các nút + dư 1.5s
                        } else {
                            alert("Vui lòng tải lại trang Google AI Studio và thử lại!");
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
            
            // QUY TẮC VÀNG: Thêm BOM (\uFEFF) ở đầu file để sửa lỗi font chữ khi mở bằng Excel/Notepad trên Windows
            const jsonStr = JSON.stringify(keys, null, 2);
            // Dùng Blob cho an toàn
            const blob = new Blob(['\uFEFF' + jsonStr], {type: "application/json;charset=utf-8"});
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `gemini_api_keys_${new Date().getTime()}.json`;
            a.click();
            URL.revokeObjectURL(url);
        });
    });

    updateUI();
    setInterval(updateUI, 1000);
});
