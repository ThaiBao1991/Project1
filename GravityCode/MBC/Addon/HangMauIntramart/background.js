// Lưu trữ trạng thái
let totalProcessed = 0;
let loopCount = 0;
let isRunning = false;
let currentTabId = null;

// Nhận message từ content script và popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'log') {
        chrome.runtime.sendMessage(request).catch(() => {});
    } 
    else if (request.type === 'updateStats') {
        totalProcessed = request.totalProcessed;
        loopCount = request.loopCount;
        chrome.storage.local.set({
            totalProcessed: totalProcessed,
            loopCount: loopCount,
            isRunning: request.isRunning !== false
        });
        chrome.runtime.sendMessage(request).catch(() => {});
    }
    else if (request.action === 'startMainScript') {
        executeMainScript(request.tabId, request.delaySeconds)
            .then(() => sendResponse({success: true}))
            .catch(e => sendResponse({success: false, error: e.message}));
        return true;
    }
    else if (request.action === 'stopMainScript') {
        executeStopScript(request.tabId);
        sendResponse({success: true});
        return true;
    }
});

async function executeMainScript(tabId, delaySeconds) {
    await chrome.scripting.executeScript({
        target: { tabId: tabId, frameIds: [0] },
        world: 'MAIN',
        func: getInjectedAutomationCode,
        args: [delaySeconds || 5]
    });
}

async function executeStopScript(tabId) {
    await chrome.scripting.executeScript({
        target: { tabId: tabId, frameIds: [0] },
        world: 'MAIN',
        func: () => { window.__intramart_stop = true; }
    });
}

// Đây là đoạn code được bơm trực tiếp vào MAIN world của Top window
function getInjectedAutomationCode(delaySeconds) {
    (async function autoIntramart() {
        const delayMs = (delaySeconds || 5) * 1000;
        
        // Bỏ qua check cờ running, luôn ép chạy mới khi ấn Start để tránh kẹt trạng thái
        window.__intramart_running = true;
        window.__intramart_stop = false;

        const log = (msg, type = 'info') => {
            console.log('%c[AUTO] ' + msg, 'color: #ff9900');
            window.postMessage({type: 'INTRAMART_LOG', message: msg, logType: type}, '*');
        };
        
        // CƠ CHẾ CHỐNG NGỦ GẬT (ANTI-THROTTLING) KHI CHUYỂN TAB HOẶC ỨNG DỤNG KHÁC
        function keepTabAwake() {
            try {
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioCtx.createOscillator();
                const gainNode = audioCtx.createGain();
                gainNode.gain.value = 0; // Mute hoàn toàn (Im lặng)
                oscillator.connect(gainNode);
                gainNode.connect(audioCtx.destination);
                oscillator.start();
                log('🔊 Đã bật khiên chống ngủ gật cho Tab (Chạy nền 100% công lực)', 'success');
            } catch(e) {
                log('ℹ️ Không thể bật chống ngủ gật: ' + e.message, 'info');
            }
        }
        
        keepTabAwake();
        
        const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));
        
        function getAllFrames() {
            const framesList = [];
            function collectFrames(win) {
                if (!win) return;
                framesList.push(win);
                try {
                    if (win.frames && win.frames.length > 0) {
                        for (let i = 0; i < win.frames.length; i++) {
                            collectFrames(win.frames[i]);
                        }
                    }
                } catch(e) {}
            }
            collectFrames(window);
            return framesList;
        }
        
        function getMainFrame() {
            for (let frame of getAllFrames()) {
                try { if (frame.name === 'IM_MAIN') return frame; } catch(e) {}
            }
            return null;
        }
        
        function hasDataRows() {
            const mainFrame = getMainFrame();
            if (!mainFrame) return false;
            try {
                const table = mainFrame.document.getElementById('list_table');
                if (!table) return false;
                return table.querySelectorAll('tr.list_data_line').length > 0;
            } catch(e) { return false; }
        }
        
        function getSelectAllCheckbox() {
            const mainFrame = getMainFrame();
            if (!mainFrame) return null;
            try {
                return mainFrame.document.querySelector('#list_table > tbody > tr:nth-child(1) > td:nth-child(1) > input[type="checkbox"]');
            } catch(e) { return null; }
        }
        
        function getProcessContinuousButton() {
            const mainFrame = getMainFrame();
            if (!mainFrame) return null;
            try {
                const links = mainFrame.document.querySelectorAll('td.toolbar_left a');
                for (let link of links) {
                    const text = link.textContent?.trim() || '';
                    if (text.includes('Process continuously') || text.includes('連続処理')) return link;
                }
                return null;
            } catch(e) { return null; }
        }
        
        function getStartContinuousButton() {
            const mainFrame = getMainFrame();
            if (!mainFrame) return null;
            try {
                const links = mainFrame.document.querySelectorAll('td.toolbar_left a');
                for (let link of links) {
                    const text = link.textContent?.trim() || '';
                    if (text.includes('Start continuous processing')) return link;
                }
                return null;
            } catch(e) { return null; }
        }
        
        function getDuyetNhanhButton() {
            const mainFrame = getMainFrame();
            if (!mainFrame) return null;
            try {
                const links = mainFrame.document.querySelectorAll('a');
                for (let link of links) {
                    const text = link.textContent?.trim() || '';
                    if (text === 'Duyệt nhanh' || text.includes('Duyệt nhanh')) return link;
                }
                return null;
            } catch(e) { return null; }
        }
        
        async function clickButton(button, name) {
            if (!button) {
                log('❌ Không tìm thấy nút: ' + name, 'error');
                return false;
            }
            try {
                button.scrollIntoView({ behavior: 'smooth', block: 'center' });
                await wait(300);
                button.style.outline = '3px solid #ff9900';
                await wait(200);
                button.style.outline = '';
                button.click();
                log('✅ Đã click: ' + name, 'success');
                return true;
            } catch(e) {
                log('❌ Lỗi click ' + name + ': ' + e.message, 'error');
                return false;
            }
        }
        
        async function clickSelectAll(checkbox) {
            if (!checkbox) return false;
            try {
                if (checkbox.checked) {
                    log('ℹ️ Select All đã được chọn', 'info');
                    return true;
                }
                checkbox.scrollIntoView({ behavior: 'smooth', block: 'center' });
                await wait(500);
                checkbox.click();
                log('✅ Đã click Select All', 'success');
                await wait(1500);
                if (!checkbox.checked) {
                    checkbox.click();
                    await wait(1000);
                    if (!checkbox.checked) checkbox.checked = true;
                    log('✅ Đã force check Select All', 'success');
                }
                return checkbox.checked;
            } catch(e) { return false; }
        }
        
        async function callDuyetNhanh(button) {
            const href = button.getAttribute('href');
            if (!href || !href.startsWith('javascript:')) return false;
            let jsCode = href.substring(11).trim();
            if (jsCode.endsWith(';')) jsCode = jsCode.slice(0, -1);
            const match = jsCode.match(/^(\w+)\(['"]?([^'"()]+)['"]?\)$/);
            if (!match) return false;
            const functionName = match[1];
            const param = match[2];
            log('🎯 Gọi function: ' + functionName + '(' + param + ')', 'step');
            
            try {
                const mainFrame = getMainFrame();
                if (mainFrame && typeof mainFrame[functionName] === 'function') {
                    mainFrame[functionName](param);
                    log('✅ Thực thi thành công!', 'success');
                    return true;
                } else {
                    log('❌ Không tìm thấy function ' + functionName, 'error');
                    return false;
                }
            } catch(e) { return false; }
        }
        
        async function processDuyetNhanh() {
            let count = 0;
            log('🔄 BẮT ĐẦU XỬ LÝ DUYỆT NHANH...', 'step');
            while (true) {
                if (window.__intramart_stop) break;
                const button = getDuyetNhanhButton();
                if (!button) {
                    if (count === 0) {
                        log('ℹ️ Không tìm thấy nút Duyệt nhanh', 'info');
                    } else {
                        log('✅ ĐÃ XỬ LÝ XONG ' + count + ' LẦN DUYỆT NHANH!', 'success');
                    }
                    break;
                }
                count++;
                log('\\n📌 LẦN THỨ ' + count + ': XỬ LÝ DUYỆT NHANH', 'step');
                
                button.scrollIntoView({ behavior: 'smooth', block: 'center' });
                await wait(300);
                button.style.outline = '3px solid #00ff00';
                await wait(200);
                button.style.outline = '';
                
                const success = await callDuyetNhanh(button);
                if (!success) {
                    log('❌ DỪNG LẠI Ở LẦN THỨ ' + count, 'error');
                    break;
                }
                
                log('⏳ Đợi ' + delaySeconds + ' giây để trang xử lý...', 'info');
                await wait(delayMs);
                
                log('⏳ Đợi frame load lại...', 'info');
                let loaded = false;
                for (let i = 0; i < 60; i++) {
                    const frame = getMainFrame();
                    if (frame && frame.document && frame.document.readyState === 'complete') {
                        log('✅ Frame đã load lại sau ' + ((i+1)*0.5) + ' giây', 'success');
                        loaded = true;
                        break;
                    }
                    await wait(500);
                }
                if (!loaded) {
                    log('⚠️ CẢNH BÁO: Frame bị kẹt loading quá 30 giây. Vui lòng F5 (Tải lại trang) để tự làm mới!', 'error');
                    break; // Thoát vòng lặp để user tự xử lý
                }
            }
            return count;
        }
        
        log('═'.repeat(60), 'step');
        log('🚀 KHỞI ĐỘNG AUTO TOOL INTRAMART', 'step');
        log('═'.repeat(60), 'step');
        
        let mainFrame = getMainFrame();
        if (!mainFrame) {
            log('❌ KHÔNG TÌM THẤY FRAME IM_MAIN!', 'error');
            window.__intramart_running = false;
            return;
        }
        
        const processBtn = getProcessContinuousButton();
        if (processBtn) {
            await clickButton(processBtn, 'Process continuously');
            log('⏳ Đợi 4 giây...', 'info');
            await wait(4000);
        }
        
        let loopCount = 0;
        let totalProcessed = 0;
        
        while (true) {
            if (window.__intramart_stop) {
                log('⏸ Đã dừng theo yêu cầu', 'error');
                break;
            }
            
            loopCount++;
            log('\\n🔄 VÒNG LẶP CHÍNH #' + loopCount, 'step');
            
            if (!hasDataRows()) {
                const dnBtn = getDuyetNhanhButton();
                if (dnBtn) {
                    log('ℹ️ Đang ở màn hình duyệt nhanh, bỏ qua list_table', 'info');
                } else {
                    log('\\n✅ HOÀN THÀNH! KHÔNG CÒN DỮ LIỆU ĐỂ XỬ LÝ', 'success');
                    break;
                }
            }
            
            const selectAllCheckbox = getSelectAllCheckbox();
            if (selectAllCheckbox) {
                const selectAllSuccess = await clickSelectAll(selectAllCheckbox);
                if (!selectAllSuccess) {
                    await wait(2000);
                    continue;
                }
                await wait(1000);
            }
            
            const startBtn = getStartContinuousButton();
            if (startBtn && startBtn.offsetParent !== null) {
                await clickButton(startBtn, 'Start continuous processing');
                await wait(3000);
            }
            
            const duyetNhanhCount = await processDuyetNhanh();
            if (duyetNhanhCount > 0) {
                totalProcessed += duyetNhanhCount;
                window.postMessage({type: 'INTRAMART_STATS', totalProcessed: totalProcessed, loopCount: loopCount}, '*');
            }
            
            log('⏳ Chờ 3 giây trước khi kiểm tra dữ liệu mới...', 'info');
            await wait(3000);
        }
        
        log('\\n🏁 KẾT THÚC XỬ LÝ', 'success');
        window.__intramart_running = false;
        window.postMessage({type: 'INTRAMART_DONE', totalProcessed: totalProcessed, loopCount: loopCount}, '*');
        
    })();
}