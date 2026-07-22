// Content script - chạy trên TOP frame để điều khiển IM_MAIN
// Cách này mô phỏng y hệt việc bạn dán code vào F12 Console của trang web

if (window === window.top) {
    console.log("[Intramart Tool] Content script injected on top frame.");

    let currentTabId = null;

    // Lắng nghe message từ MAIN world (script được inject)
    window.addEventListener('message', (event) => {
        if (event.source !== window) return;
        
        if (event.data && event.data.type === 'INTRAMART_LOG') {
            chrome.runtime.sendMessage({
                type: 'log',
                message: event.data.message,
                logType: event.data.logType
            }).catch(() => {});
        } else if (event.data && event.data.type === 'INTRAMART_STATS') {
            chrome.runtime.sendMessage({
                type: 'updateStats',
                totalProcessed: event.data.totalProcessed,
                loopCount: event.data.loopCount
            }).catch(() => {});
        } else if (event.data && event.data.type === 'INTRAMART_DONE') {
            chrome.runtime.sendMessage({
                type: 'updateStats',
                totalProcessed: event.data.totalProcessed,
                loopCount: event.data.loopCount,
                isRunning: false
            }).catch(() => {});
        }
    });

// Lắng nghe lệnh từ Popup
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === 'start') {
            currentTabId = request.tabId;
            
            // Gọi background bơm script vào MAIN world để lách CSP
            chrome.runtime.sendMessage({
                action: 'startMainScript',
                tabId: currentTabId,
                delaySeconds: request.delaySeconds || 5
            }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error("Lỗi gửi tin nhắn cho background:", chrome.runtime.lastError);
                } else if (response && !response.success) {
                    console.error("Lỗi khi bơm script MAIN:", response.error);
                    // Báo ngược lại popup
                    chrome.runtime.sendMessage({
                        type: 'log',
                        message: '❌ Lỗi chạy code gốc: ' + response.error,
                        logType: 'error'
                    }).catch(() => {});
                }
            });
            
            sendResponse({status: 'started'});
        } else if (request.action === 'stop') {
            // Gọi background dừng script
            chrome.runtime.sendMessage({
                action: 'stopMainScript',
                tabId: request.tabId || currentTabId
            });
            sendResponse({status: 'stopped'});
        }
        return true;
    });
}