let port = null;

document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    // Lấy thông tin tab hiện tại
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        if (tabs[0]) {
            document.getElementById('currentTab').textContent = tabs[0].title.substring(0, 50);
        }
    });
    
    // Lấy trạng thái từ storage
    chrome.storage.local.get(['isRunning', 'totalProcessed', 'loopCount'], (result) => {
        if (result.isRunning) {
            updateUI(true);
            document.getElementById('totalProcessed').textContent = result.totalProcessed || 0;
            document.getElementById('loopCount').textContent = result.loopCount || 0;
        } else {
            updateUI(false);
        }
    });
    
    // Start button
    startBtn.addEventListener('click', () => {
        chrome.tabs.query({active: true, currentWindow: true}, async (tabs) => {
            if (!tabs[0]) {
                addLog('❌ Không tìm thấy tab nào đang hoạt động', 'error');
                return;
            }
            
            const delayValue = parseInt(document.getElementById('delayInput').value) || 5;
            addLog('🔄 Đang khởi động tool với delay ' + delayValue + 's...', 'info');
            
            try {
                // Inject content script nếu chưa có
                await chrome.scripting.executeScript({
                    target: {tabId: tabs[0].id},
                    files: ['content.js']
                }).catch(() => {});
                
                // Gửi message start
                chrome.tabs.sendMessage(tabs[0].id, {
                    action: 'start',
                    tabId: tabs[0].id,
                    delaySeconds: delayValue
                }, (response) => {
                    if (chrome.runtime.lastError) {
                        addLog(`⚠️ Lỗi: ${chrome.runtime.lastError.message}`, 'error');
                        addLog('💡 Vui lòng tải lại trang và thử lại', 'info');
                        updateUI(false);
                    } else {
                        addLog('✅ Tool đã khởi động thành công!', 'success');
                        updateUI(true);
                        chrome.storage.local.set({isRunning: true});
                    }
                });
            } catch (error) {
                addLog(`❌ Lỗi: ${error.message}`, 'error');
            }
        });
    });
    
    // Stop button
    stopBtn.addEventListener('click', () => {
        chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
            if (tabs[0]) {
                chrome.tabs.sendMessage(tabs[0].id, {action: 'stop'}, () => {
                    if (!chrome.runtime.lastError) {
                        addLog('⏸ Đã dừng tool', 'error');
                        updateUI(false);
                        chrome.storage.local.set({isRunning: false});
                    }
                });
            }
        });
    });
    
    // Nút Lưu Log
    const exportLogBtn = document.getElementById('exportLogBtn');
    if (exportLogBtn) {
        exportLogBtn.addEventListener('click', () => {
            const logs = Array.from(document.querySelectorAll('.log-entry'))
                              .map(el => el.textContent)
                              .join('\n');
            if (!logs) {
                addLog('ℹ️ Không có log để lưu!', 'info');
                return;
            }
            const blob = new Blob([logs], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            const now = new Date();
            const timeStr = `${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}_${String(now.getHours()).padStart(2,'0')}${String(now.getMinutes()).padStart(2,'0')}`;
            a.href = url;
            a.download = `intramart_log_${timeStr}.txt`;
            a.click();
            URL.revokeObjectURL(url);
            addLog('✅ Đã lưu log thành công!', 'success');
        });
    }
});

// Lắng nghe log từ background/content script
chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === 'log') {
        addLog(msg.message, msg.logType);
    } else if (msg.type === 'updateStats') {
        document.getElementById('totalProcessed').textContent = msg.totalProcessed || 0;
        document.getElementById('loopCount').textContent = msg.loopCount || 0;
        if (msg.isRunning === false) {
            updateUI(false);
            chrome.storage.local.set({isRunning: false});
        }
    }
});

function addLog(message, type = 'info') {
    const logContainer = document.getElementById('logContainer');
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${type}`;
    
    const now = new Date();
    const timestamp = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`;
    logEntry.textContent = `[${timestamp}] ${message}`;
    
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
    
    while (logContainer.children.length > 100) {
        logContainer.removeChild(logContainer.firstChild);
    }
}

function updateUI(isRunning) {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const statusEl = document.getElementById('status');
    
    if (isRunning) {
        startBtn.disabled = true;
        stopBtn.disabled = false;
        statusEl.innerHTML = '🟢 ĐANG CHẠY...';
        statusEl.className = 'status-value running';
    } else {
        startBtn.disabled = false;
        stopBtn.disabled = true;
        statusEl.innerHTML = '⏸️ Đã dừng';
        statusEl.className = 'status-value stopped';
    }
}