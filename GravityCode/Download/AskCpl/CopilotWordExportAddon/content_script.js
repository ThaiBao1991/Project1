// ============================================================
// content_script.js — Giai đoạn 29: Fix Chrome Reload, Heartbeat, Error Detection
// ============================================================

let isRunning        = false;
let currentDay       = 1;
let prefixStr        = "Day ";
let currentAgentName = "";
let folderName       = "";
let dayIndex         = [];

// ── NEW: Nền tảng và Roadmap ──
let currentPlatform  = "copilot";
let roadmapData      = null;
let historySummaries = [];

// Helper: Tự động tính toán ngày cuối cùng từ Roadmap nếu người dùng không nhập
function calcAutoEndDay(rData, mode) {
    if (!rData || !Array.isArray(rData) || rData.length === 0) return null;
    try {
        if (mode === 'file_md') {
            return Math.max(...rData.map(d => d.day));
        } else if (mode === 'table_md') {
            return Math.max(...rData.flatMap(c => c.days.map(d => d.day)));
        }
    } catch (e) {
        console.error("Lỗi tính auto endDay:", e);
    }
    return null;
}

// Advanced & Config
let endDay           = null;
let promptMode       = 'basic';
let isAdvanced       = false;
let topicPromptStr   = "";
let targetCount      = 4;
let detailConfigs    = [];
let topicMemory      = {};
let currentTabId     = null;

// ── Delay helper ──────────────────────────────────────────
const delay = ms => new Promise(r => setTimeout(r, ms));

let _keepAliveInterval    = null;
let _silentAudio          = null;
let _heartbeatInterval    = null; // F6a: Heartbeat để popup biết loop còn sống
let _audioHealthInterval  = null; // GĐ47-A: Kiểm tra audio bị tắt bởi browser
let _wakeLockAbort        = null; // GĐ47-B: Web Locks API — ngăn Chrome throttle tab

function _playKeepAliveAudio() {
    if (!_silentAudio) return;
    const p = _silentAudio.play();
    if (p && typeof p.catch === 'function') {
        p.catch(() => {
            // F4: Autoplay bị block (thường sau reload) — retry sau 3s khi user có thể interact
            setTimeout(() => {
                if (_silentAudio) _silentAudio.play().catch(() => {});
            }, 3000);
        });
    }
}

function setupKeepAlive() {
    // F4: Silent audio — browser coi tab đang phát media → không sleep
    if (!_silentAudio) {
        _silentAudio = document.createElement('audio');
        _silentAudio.src = "data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA";
        _silentAudio.loop = true;
        _silentAudio.volume = 0.01;
        _playKeepAliveAudio();
    }
    // GĐ47-A: Audio Health Check — restart audio nếu browser tự tắt (autoplay policy sau reload)
    if (!_audioHealthInterval) {
        _audioHealthInterval = setInterval(() => {
            if (_silentAudio && _silentAudio.paused) {
                _silentAudio.play().catch(() => {});
                appLog('🔊 Audio keepalive tự restart (bị browser tắt)');
            }
        }, 5000);
    }
    // GĐ47-B: Web Locks API — giữ một lock chia sẻ để ngăn Chrome/Edge throttle tab khi bị ẩn
    // (Tab giữ lock sẽ không bị browser cho vào trạng thái ngủ/frozen)
    if (!_wakeLockAbort && typeof navigator !== 'undefined' && navigator.locks) {
        _wakeLockAbort = new AbortController();
        navigator.locks.request(
            'askcpl_wakeLock',
            { mode: 'shared', signal: _wakeLockAbort.signal },
            () => new Promise(resolve => {
                // Promise này chỉ resolve khi _wakeLockAbort.abort() được gọi (teardown)
                _wakeLockAbort._resolve = resolve;
            })
        ).catch(() => { _wakeLockAbort = null; });
        appLog('🔒 Web Lock acquired — Chrome sẽ không throttle tab này');
    }
    // Keepalive ping đến background Service Worker
    if (!_keepAliveInterval) {
        _keepAliveInterval = setInterval(() => {
            if (chrome.runtime && chrome.runtime.id) {
                chrome.runtime.sendMessage({ action: 'ping' }).catch(() => {});
            }
        }, 20000);
    }
    // F6a: Heartbeat — cập nhật timestamp mỗi 15s để popup phát hiện loop chết
    if (!_heartbeatInterval) {
        _heartbeatInterval = setInterval(() => {
            if (!isRunning || !currentTabId) return;
            chrome.storage.local.get(['runningStates'], (res) => {
                const states = res.runningStates || {};
                if (states[currentTabId]) {
                    states[currentTabId].lastHeartbeat = Date.now();
                    chrome.storage.local.set({ runningStates: states });
                }
            });
        }, 15000);
    }
}

function teardownKeepAlive() {
    if (_silentAudio) {
        _silentAudio.pause();
        _silentAudio.removeAttribute('src');
        _silentAudio = null;
    }
    // GĐ47-A: Dừng audio health check
    if (_audioHealthInterval) {
        clearInterval(_audioHealthInterval);
        _audioHealthInterval = null;
    }
    // GĐ47-B: Giải phóng Web Lock
    if (_wakeLockAbort) {
        if (typeof _wakeLockAbort._resolve === 'function') _wakeLockAbort._resolve();
        _wakeLockAbort.abort();
        _wakeLockAbort = null;
        appLog('🔓 Web Lock released');
    }
    if (_keepAliveInterval) {
        clearInterval(_keepAliveInterval);
        _keepAliveInterval = null;
    }
    // F6a: Dừng heartbeat
    if (_heartbeatInterval) {
        clearInterval(_heartbeatInterval);
        _heartbeatInterval = null;
    }
}

function safeSendMessage(msg) {
    if (chrome.runtime && chrome.runtime.id) {
        try { chrome.runtime.sendMessage(msg).catch(() => {}); } catch (e) {}
    }
}

let _logQueue = [];
let _logTimer = null;
function flushLogs() {
    if (!_logQueue.length) return;
    const text = _logQueue.join('\n');
    safeSendMessage({ action: "add_log", text });
    chrome.storage.local.get(['popup_logs'], (r) => {
        const prev = r.popup_logs || '';
        const combined = (prev + '\n' + text).split('\n').slice(-200).join('\n');
        chrome.storage.local.set({ popup_logs: combined });
    });
    _logQueue = []; _logTimer = null;
}
function appLog(msg) {
    const time = new Date().toLocaleTimeString('vi-VN');
    const logStr = `[${time}] ${msg}`;
    console.debug("[AutoLearner] " + logStr);
    _logQueue.push(logStr);
    if (!_logTimer) _logTimer = setTimeout(flushLogs, 500);
}
function sendStatus(text) {
    if (_logQueue.length) { clearTimeout(_logTimer); flushLogs(); }
    appLog("STATUS: " + text);
    safeSendMessage({ action: "update_status", text });
}

function autoSave() {
    const sessionObj = {
        agentName: currentAgentName, folderName, prefix: prefixStr,
        lastDay: currentDay, totalSaved: dayIndex.length,
        savedAt: new Date().toISOString(), days: dayIndex,
        topicMemory: topicMemory,
        platform: currentPlatform,
        // FIX GĐ 44: KHÔNG lưu roadmapData vào session.json — được lưu riêng ở key 'roadmap_active'
        // Việc nhúng roadmapData (3000 bài, ~50MB) vào session khiến file bị phình to
        historySummaries: historySummaries,
        promptMode: promptMode,
        isAdvanced: isAdvanced,
        topicPromptStr: topicPromptStr,
        targetCount: targetCount,
        details: detailConfigs
    };
    const sessionBase64 = btoa(unescape(encodeURIComponent(JSON.stringify(sessionObj))));
    
    chrome.storage.local.set({
        autosave_data: dayIndex, autosave_name: currentAgentName,
        autosave_day: currentDay, autosave_folder: folderName,
        autosave_session_json: sessionBase64
    });
}

// Fix 1: Save toàn bộ state ngay trước khi reload — đảm bảo autosave_session_json luôn tồn tại
// Kể cả khi chưa có Day nào hoàn thành (dayIndex.length = 0)
function saveStateForReload() {
    const agentName = currentAgentName || 'Copilot';
    const folder    = folderName || makeFolderName(agentName);
    const lastDone  = Math.max(0, currentDay - 1);
    const sessionObj = {
        agentName, folderName: folder, prefix: prefixStr,
        lastDay: lastDone, totalSaved: dayIndex.length,
        savedAt: new Date().toISOString(), days: dayIndex,
        topicMemory, platform: currentPlatform,
        // FIX GĐ 44: KHÔNG lưu roadmapData vào đây — được giữ nguyên ở key 'roadmap_active'
        historySummaries, promptMode, isAdvanced,
        topicPromptStr, targetCount, details: detailConfigs
    };
    const sessionBase64 = btoa(unescape(encodeURIComponent(JSON.stringify(sessionObj))));
    return new Promise(resolve => {
        chrome.storage.local.set({
            autosave_data: dayIndex,
            autosave_name: agentName,
            autosave_day: lastDone,
            autosave_folder: folder,
            autosave_session_json: sessionBase64
        }, resolve);
    });
}
function clearAutoSave() {
    chrome.storage.local.remove(['autosave_data', 'autosave_name', 'autosave_day', 'autosave_folder', 'autosave_session_json']);
}

// ── Running State (Popup Sync + Auto-Resume) ──────────────────
function saveRunningState(nextDay, lastSaved) {
    if (!currentTabId) return;
    chrome.storage.local.get(['runningStates'], (res) => {
        const states = res.runningStates || {};
        states[currentTabId] = {
            isRunning: true,
            tabId: currentTabId,
            currentDay: nextDay,
            endDay, promptMode, isAdvanced, topicPromptStr, targetCount, detailConfigs, topicMemory,
            agentName: currentAgentName,
            folderName,
            prefix: prefixStr,
            platform: currentPlatform,
            // FIX GĐ 44: KHÔNG lưu roadmapData vào runningStates
            // roadmapData (3000 bài) sẽ làm storage vượt giới hạn 10MB của chrome.storage.local
            historySummaries: historySummaries,
            lastSaved: lastSaved || '',
            lastHeartbeat: Date.now(),
            savedAt: new Date().toISOString()
        };
        chrome.storage.local.set({ runningStates: states });
    });
}
function clearRunningState() {
    // Luôn xóa TOÀN BỘ runningStates để tránh state cũ gây lỗi trên Edge khi restart
    chrome.storage.local.remove(['runningStates']);
}

// F2: Khai báo TRƯỚC pagehide listener để flag được set đúng
let _isIntentionalReload = false;

// ── Tự xóa state khi tab bị đóng / navigate đi (Edge fix) ─────
window.addEventListener('pagehide', () => {
    if (isRunning) {
        // Cố gắng lưu index và session trước khi thoát
        if (dayIndex.length > 0) { updateIndex(); saveSession(); }
        // F3: Chỉ xóa runningStates khi KHÔNG phải intentional reload
        // Edge: pagehide cũng fire khi navigate SPA → cần giữ state để auto-resume
        if (!_isIntentionalReload) {
            chrome.storage.local.remove(['runningStates']);
        }
        isRunning = false;
    }
});

// ── F1: Khôi phục vòng lặp nếu script cố ý reload trang ──────
// Dùng chrome.storage.local thay sessionStorage (tin cậy hơn trên Chrome)
chrome.storage.local.get(['askcpl_reload_flag'], (res) => {
    const flag = res.askcpl_reload_flag;
    // Expire sau 15s để tránh false-positive khi Edge restore tab cũ
    const isIntentional = flag && flag.active && (Date.now() - (flag.ts || 0) < 15000);
    // Xóa flag ngay lập tức để không bị dùng lại
    chrome.storage.local.remove(['askcpl_reload_flag']);

    if (isIntentional) {
        appLog('🔄 Khôi phục vòng lặp sau khi script tự reload...');
        chrome.storage.local.get(['autosave_session_json'], (res2) => {
            if (res2.autosave_session_json) {
                try {
                    const sessionStr = decodeURIComponent(escape(atob(res2.autosave_session_json)));
                    const s = JSON.parse(sessionStr);
                    chrome.runtime.sendMessage({ action: "get_tab_id" }, (response) => {
                        const tId = (response && response.tabId) ? response.tabId : Date.now();
                        // Fix 3: isFromReload=true → runNextDay(true) → không click New Chat lần đầu
                        handleResumeSessionRequest({
                            tabId: tId,
                            session: s,
                            currentDay: s.lastDay + 1,
                            isFromReload: true
                        });
                    });
                } catch (e) { appLog('❌ Lỗi parse session sau reload: ' + e); }
            } else {
                // Fix 1 đã đảm bảo luôn có session, trường hợp này chỉ xảy ra nếu storage bị xóa bời bên ngoài
                appLog('⚠️ Không có autosave_session_json sau reload. Thử tiếp tục từ đầu...');
                // Fallback: reload lần 2 sẽ không có flag nên sẽ khởi động bình thường
            }
        });
    } else {
        // F3: Phiên bình thường (hoặc flag expired) → xóa runningStates
        // Không xóa trên Edge nếu tab vừa được restore (flag sẽ không tồn tại → đây là đúng)
        chrome.storage.local.remove(['runningStates']);
    }
});

// ── Kiểm tra autosave khi script được inject ──────────────────
// Chỉ thông báo cho Popup biết có dữ liệu cũ để người dùng chủ động khôi phục.
chrome.storage.local.get(
    ['autosave_data', 'autosave_name', 'autosave_day', 'autosave_folder'],
    (result) => {
        if (result.autosave_data?.length > 0) {
            const savedName = result.autosave_name || 'Copilot';
            const count = result.autosave_data.length;
            safeSendMessage({ action: "update_status", text: `⚠️ Dữ liệu cũ: ${count} bài từ [${savedName}]. Nhấn Recover hoặc chạy mới.` });
            safeSendMessage({ action: "has_autosave", count, name: savedName, lastDay: result.autosave_day || '?' });
        }
    }
);

// ── Helpers ───────────────────────────────────────────────────
function makeFolderName(name) {
    return (name || "Copilot").replace(/[^a-zA-Z0-9_\u00C0-\u024F\u1E00-\u1EFF]/g, '_').slice(0, 50);
}
function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function detectAgentName() {
    const title = (document.title || "").replace(/[-|–—]\s*(Microsoft\s*)?Copilot\s*$/i, "").replace(/[-|–—]\s*Bing\s*$/i, "").replace(/[-|–—]\s*Microsoft\s*365\s*$/i, "").trim();
    if (title.length > 0 && title.length < 80) return title;
    const h1 = document.querySelector('h1');
    if (h1?.innerText?.trim()) return h1.innerText.trim().slice(0, 50);
    return "Copilot";
}

// ── New Chat ──────────────────────────────────────────────────
const NEW_CHAT_SELECTORS = ['[data-automation-id="newChatButton"]', '[data-testid="newChatButton"]', 'button[aria-label="New chat"]', 'button[aria-label*="new chat" i]', 'button[title*="New chat" i]'];
function clickNewChat() {
    if (currentPlatform === 'gemini') {
        const selectors = [
            'a[data-test-id="new-chat-button"]',
            'button[data-test-id="new-chat-button"]',
            'a[href="/app"]', 
            'a[href="/app/"]',
            'button[aria-label*="New chat" i]', 
            'button[aria-label*="trò chuyện mới" i]',
            'button[mattooltip*="New chat" i]',
            'button[mattooltip*="trò chuyện mới" i]'
        ];
        for (const sel of selectors) {
            const btn = document.querySelector(sel);
            if (btn && btn.offsetParent !== null && !btn.disabled) { 
                btn.click(); 
                appLog('🆕 Đã click New Chat Gemini: ' + sel); 
                return true; 
            }
        }
        // Text fallback
        const els = Array.from(document.querySelectorAll('span, div, p'));
        const newChatEl = els.find(el => {
            if (el.children.length > 0) return false;
            const txt = el.innerText?.trim().toLowerCase();
            return txt === 'new chat' || txt === 'trò chuyện mới' || txt === 'chat mới';
        });
        if (newChatEl) {
            const clickable = newChatEl.closest('button, a, [role="button"]') || newChatEl;
            clickable.click();
            appLog('🆕 Đã click New Chat Gemini (Text Fallback)');
            return true;
        }
    }
    if (currentPlatform === 'chatgpt') {
        const btn = document.querySelector('a[href="/"], button[aria-label*="New chat" i]');
        if (btn && btn.offsetParent !== null) { btn.click(); appLog('🆕 Đã click New Chat ChatGPT'); return true; }
    }
    for (const sel of NEW_CHAT_SELECTORS) {
        const btn = document.querySelector(sel);
        if (btn && btn.offsetParent !== null && !btn.disabled) {
            btn.click();
            appLog('🆕 Đã click New Chat: ' + sel);
            return true;
        }
    }
    appLog('⚠️ Không tìm thấy nút New Chat.');
    return false;
}

async function waitForNewChatReady() {
    appLog('⏳ Chờ 3s để DOM settle...');
    await delay(3000);
    const maxWaitMs = 30000; // 30 seconds max wait
    const startTime = Date.now();
    while (Date.now() - startTime < maxWaitMs) {
        _cachedInput = null;
        const input = findChatInput();
        if (!input) { await delay(1500); continue; }
        const empty = ((input.tagName === 'TEXTAREA' && input.value.trim() === '') || (input.isContentEditable && input.innerText.trim() === ''));
        if (empty) return true;
        await delay(1500);
    }
    appLog('⚠️ Quá thời gian 30s chờ New Chat. Đang lưu state và reload...');
    _isIntentionalReload = true;
    // Fix 1: Lưu toàn bộ state TRƯỚC reload — kể cả khi chưa có Day nào hoàn thành
    await saveStateForReload();
    // Ghi flag và reload trong callback để đảm bảo storage đã ghi xong
    await new Promise(resolve => {
        chrome.storage.local.set({ askcpl_reload_flag: { active: true, ts: Date.now() } }, () => {
            location.reload();
            resolve();
        });
    });
    return false;
}

// ── Gửi message tải file có cơ chế Retry (Fix lỗi SW ngủ quên) ──
async function sendDownloadMessageWithRetry(msg, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            await chrome.runtime.sendMessage(msg);
            return; // Thành công
        } catch (e) {
            if (e.message.includes("Receiving end does not exist") || e.message.includes("establish connection")) {
                appLog(`⚠️ [Retry ${attempt}/${maxRetries}] Lỗi kết nối Background (SW có thể đang ngủ). Thử lại sau 1s...`);
                await delay(1000);
            } else {
                appLog(`❌ Lỗi gửi download: ${e.message}`);
                return;
            }
        }
    }
    appLog(`❌ Thất bại sau ${maxRetries} lần gửi message download.`);
}

// ── Download senders ──────────────────────────────────────────
function downloadDayHtml(dayLabel, rawHtmlContent) {
    const filename = `${folderName}/day_${currentDay}.html`;
    sendDownloadMessageWithRetry({
        action: "download_html", rawContent: rawHtmlContent,
        dayLabel, agentName: currentAgentName, filename,
        totalDays: endDay || 9999,
        timestamp: new Date().toLocaleString('vi-VN')
    });
    return filename;
}
function updateIndex() {
    sendDownloadMessageWithRetry({
        action: "download_index", agentName: currentAgentName,
        folderName, days: dayIndex, filename: `${folderName}/index.html`,
        timestamp: new Date().toLocaleString('vi-VN')
    });
}
function saveSession() {
    sendDownloadMessageWithRetry({
        action: "download_session",
        data: JSON.stringify({
            agentName: currentAgentName, folderName, prefix: prefixStr,
            lastDay: currentDay, totalSaved: dayIndex.length,
            savedAt: new Date().toISOString(), days: dayIndex,
            topicMemory: topicMemory,
            platform: currentPlatform,
            roadmapData: roadmapData,
            historySummaries: historySummaries,
            promptMode: promptMode,
            isAdvanced: isAdvanced,
            topicPromptStr: topicPromptStr,
            targetCount: targetCount,
            details: detailConfigs
        }, null, 2),
        filename: `${folderName}/session.json`
    });
}
function finishLoop(msg) {
    isRunning = false;
    teardownKeepAlive();
    appLog("FINISHED: " + msg);
    if (dayIndex.length > 0) { updateIndex(); saveSession(); clearAutoSave(); }
    clearRunningState();
    safeSendMessage({ action: "loop_finished", text: msg });
}

function handleResumeSessionRequest(request) {
    if (request.tabId) currentTabId = request.tabId;
    if (!isRunning) {
        const s = request.session;
        isRunning = true;
        currentAgentName = s.agentName || "Copilot";
        folderName  = s.folderName || makeFolderName(currentAgentName);
        prefixStr   = s.prefix || "Day ";
        currentDay  = request.currentDay ? parseInt(request.currentDay, 10) : (s.lastDay || 0) + 1;
        
        let rawDays = s.days || [];
        dayIndex = rawDays.filter(d => {
            const match = String(d.day).match(/\d+/);
            return match ? parseInt(match[0], 10) < currentDay : true;
        });
        endDay      = request.endDay || null;
        promptMode  = request.promptMode || s.promptMode || 'basic';
        isAdvanced  = request.isAdvanced || false;
        topicPromptStr = request.topicPrompt || "";
        targetCount    = request.targetCount || 4;
        detailConfigs  = request.details || [];
        topicMemory    = s.topicMemory || {};
        currentPlatform  = request.platform || s.platform || "copilot";
        historySummaries = (s.historySummaries || []).filter(h => parseInt(h.day, 10) < currentDay);
        
        sendStatus(`Resume: ${currentAgentName} — từ ${prefixStr}${currentDay}`);
        safeSendMessage({ action: "update_agent_name", name: currentAgentName });
        
        // FIX GĐ 44: Đọc roadmapData từ key riêng trong storage thay vì nhận qua IPC
        // roadmapData lớn (3000 bài ~50MB) sẽ làm cầu IPC sendMessage bị drop im lặng
        chrome.storage.local.get(['roadmap_active'], (res) => {
            roadmapData = res.roadmap_active || null;
            if (!endDay && roadmapData) {
                endDay = calcAutoEndDay(roadmapData, promptMode);
                if (endDay) appLog(`Tự động thiết lập Ngày kết thúc (endDay) = ${endDay} từ Roadmap.`);
            }
            saveRunningState(currentDay);
            setupKeepAlive();
            const isFromReload = request.isFromReload || false;
            runNextDay(isFromReload);
        });
    }
}

// ── Message Listener ─────────────────────────────────────────
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "start_loop") {
        if (request.tabId) currentTabId = request.tabId;
        if (!isRunning) {
            isRunning = true;
            prefixStr  = request.prefix || "Day ";
            currentDay = request.currentDay || 1;
            endDay     = request.endDay || null;
            promptMode = request.promptMode || 'basic';
            isAdvanced = request.isAdvanced || false;
            topicPromptStr = request.topicPrompt || "";
            targetCount    = request.targetCount || 4;
            detailConfigs  = request.details || [];
            topicMemory    = {};
            dayIndex   = [];
            currentPlatform  = request.platform || "copilot";
            historySummaries = [];
            currentAgentName = request.agentName?.trim() || detectAgentName();
            safeSendMessage({ action: "update_agent_name", name: currentAgentName });
            folderName = makeFolderName(currentAgentName);
            sendStatus(`Bắt đầu từ ${prefixStr}${currentDay} | ${currentAgentName}`);
            
            // FIX GĐ 44: Đọc roadmapData từ key riêng trong storage
            chrome.storage.local.get(['roadmap_active'], (res) => {
                roadmapData = res.roadmap_active || null;
                if (!endDay && roadmapData) {
                    endDay = calcAutoEndDay(roadmapData, promptMode);
                    if (endDay) appLog(`Tự động thiết lập Ngày kết thúc (endDay) = ${endDay} từ Roadmap.`);
                }
                saveRunningState(currentDay);
                setupKeepAlive();
                runNextDay();
            });
        }
        sendResponse({ status: "started" });
    }
    else if (request.action === "resume_session") {
        handleResumeSessionRequest(request);
        sendResponse({ status: "resumed" });
    }
    else if (request.action === "stop_loop") {
        isRunning = false;
        teardownKeepAlive();
        if (dayIndex.length > 0) { updateIndex(); saveSession(); clearAutoSave(); }
        clearRunningState();
        sendStatus("Đã dừng.");
        sendResponse({ status: "stopped" });
    }
    return true;
});

// ── DOM: Tìm ô nhập ───────────────────────────────────────────
let _cachedInput = null;
let _inputFingerprint = null;
function saveInputFingerprint(el) {
    try {
        const fp = { tagName: el.tagName };
        const attrs = ['role', 'contenteditable', 'aria-label', 'data-automation-id', 'data-testid'];
        let ownSel = el.tagName.toLowerCase();
        for (const attr of attrs) {
            const v = el.getAttribute(attr);
            if (v) ownSel += `[${attr}="${v}"]`;
        }
        fp.ownSelector = ownSel;
        if (el.parentElement) {
            let parentSel = el.parentElement.tagName.toLowerCase();
            const pid = el.parentElement.id;
            if (pid) parentSel += `#${pid}`;
            else {
                const pcls = el.parentElement.className?.split?.(' ')?.[0];
                if (pcls && pcls.length > 2) parentSel += `.${pcls}`;
            }
            fp.parentSelector = parentSel;
        }
        _inputFingerprint = fp;
        chrome.storage.local.set({ inputFingerprint: fp });
    } catch (e) {}
}
function findByFingerprint() {
    if (!_inputFingerprint) return null;
    try {
        const el = document.querySelector(_inputFingerprint.ownSelector);
        if (el && el.offsetParent !== null) return el;
        if (_inputFingerprint.parentSelector) {
            const el2 = document.querySelector(`${_inputFingerprint.parentSelector} > ${_inputFingerprint.ownSelector}`);
            if (el2 && el2.offsetParent !== null) return el2;
        }
    } catch (e) {}
    return null;
}
function findLexicalInput() {
    const lexNode = document.querySelector('[data-lexical-text]');
    if (!lexNode) return null;
    let el = lexNode.closest('[contenteditable="true"]');
    if (el && el.offsetParent !== null) return el;
    return null;
}
function findChatInput() {
    if (_cachedInput?.isConnected) return _cachedInput;
    
    if (currentPlatform === 'gemini') {
        const parent = document.querySelector('rich-textarea');
        if (parent) {
            const editor = parent.querySelector('div[contenteditable="true"]') || parent.querySelector('.ql-editor') || parent;
            if (editor && editor.offsetParent !== null) { _cachedInput = editor; return editor; }
        }
        const el = document.querySelector('textarea[aria-label*="Nhập"], textarea[aria-label*="Enter"]');
        if (el && el.offsetParent !== null) { _cachedInput = el; return el; }
    }
    if (currentPlatform === 'chatgpt') {
        const el = document.querySelector('#prompt-textarea');
        if (el && el.offsetParent !== null) { _cachedInput = el; return el; }
    }
    
    let el = findByFingerprint();
    if (el) { _cachedInput = el; return el; }
    el = findLexicalInput();
    if (el) { _cachedInput = el; return el; }
    const candidates = ['div[role="textbox"][contenteditable="true"]', '[data-automation-id*="chat-input"]', '[data-testid*="chat-input"]', 'div[contenteditable="true"][aria-label*="chat" i]', 'div[contenteditable="true"][aria-label*="message" i]', 'div[contenteditable="true"][aria-label*="ask" i]', 'div[contenteditable="true"][aria-placeholder]', 'textarea[aria-label*="chat" i]', 'textarea[aria-label*="message" i]', 'textarea[placeholder*="Message"]', 'textarea[placeholder*="Nhập"]'];
    for (const sel of candidates) {
        el = document.querySelector(sel);
        if (el && el.offsetParent !== null) { _cachedInput = el; return el; }
    }
    const allCE = document.querySelectorAll('div[contenteditable="true"]');
    for (const ce of allCE) {
        if (ce.scrollHeight > 500 || ce.children.length > 20) continue;
        if (ce.offsetParent !== null) { _cachedInput = ce; return ce; }
    }
    const ae = document.activeElement;
    if (ae && (ae.tagName === 'TEXTAREA' || ae.isContentEditable)) { _cachedInput = ae; return ae; }
    return null;
}
chrome.storage.local.get(['inputFingerprint'], (r) => {
    if (r.inputFingerprint) _inputFingerprint = r.inputFingerprint;
});

let _cachedSendBtn = null;
function findSendButton() {
    if (_cachedSendBtn?.isConnected && !_cachedSendBtn.disabled) return _cachedSendBtn;
    _cachedSendBtn = null;
    
    if (currentPlatform === 'gemini') {
        const btn = document.querySelector('button[aria-label*="Send" i], button[aria-label*="Gửi" i]');
        if (btn && btn.offsetParent !== null && !btn.disabled) { _cachedSendBtn = btn; return btn; }
    }
    if (currentPlatform === 'chatgpt') {
        const btn = document.querySelector('button[data-testid="send-button"]');
        if (btn && btn.offsetParent !== null && !btn.disabled) { _cachedSendBtn = btn; return btn; }
    }
    
    const candidates = ['button[data-automation-id*="send" i]', 'button[data-testid*="send" i]', 'button[aria-label*="Send" i]', 'button[aria-label*="Submit" i]', 'button[aria-label*="Gửi" i]', 'button[title*="Send" i]', '[role="button"][aria-label*="Send" i]'];
    for (const sel of candidates) {
        const el = document.querySelector(sel);
        if (el && el.offsetParent !== null && !el.disabled) { _cachedSendBtn = el; return el; }
    }
    return null;
}

function fillInput(el, value) {
    el.focus();
    if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
        const proto  = Object.getPrototypeOf(el);
        const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
        if (setter) setter.call(el, value); else el.value = value;
        el.dispatchEvent(new Event('input',  { bubbles: true, composed: true }));
        el.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
    } else {
        try {
            const range = document.createRange();
            range.selectNodeContents(el);
            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        } catch (e) {
            document.execCommand('selectAll', false, null);
        }
        const ok = document.execCommand('insertText', false, value);
        if (!ok) {
            el.textContent = value;
        }
        // Bắt buộc fire event để Angular/React (như Gemini) nhận diện có text mới thay vì hiện icon Loa (Voice)
        el.dispatchEvent(new InputEvent('input', { bubbles: true, composed: true, inputType: 'insertText', data: value }));
        el.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
        el.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
        
        // Nếu là Gemini, fire event thêm ở tag cha rich-textarea nếu có
        const richText = el.closest('rich-textarea');
        if (richText) {
            richText.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
        }
    }
}

function snapshotBeforeSend() {
    const mainEl = document.querySelector('[role="main"]') || document.querySelector('main');
    const container = mainEl || document.body;
    const allEls = container.querySelectorAll('*');
    for (const el of allEls) { el.dataset.askcplSnapshot = "1"; }
    return { elementCount: allEls.length, chatLength: container.innerText?.length || 0, timestamp: Date.now() };
}

const MAX_HTML_BYTES = 2 * 1024 * 1024;
const MAX_BLOCKS     = 500;
function capHtml(html) {
    if (html.length <= MAX_HTML_BYTES) return html;
    return html.slice(0, MAX_HTML_BYTES) + '\n<!-- [TRUNCATED] -->';
}

function extractDeltaContent(snapshot) {
    if (currentPlatform === 'gemini') {
        const msgs = document.querySelectorAll('message-content');
        if (msgs.length > 0) return capHtml(msgs[msgs.length - 1].innerHTML);
        return "";
    }
    if (currentPlatform === 'chatgpt') {
        const msgs = document.querySelectorAll('div.markdown');
        if (msgs.length > 0) return capHtml(msgs[msgs.length - 1].innerHTML);
        return "";
    }

    const mainEl = document.querySelector('[role="main"]') || document.querySelector('main');
    const container = mainEl || document.body;
    const allEls = Array.from(container.querySelectorAll('*'));
    const newEls = allEls.filter(el => el.dataset.askcplSnapshot !== "1");
    if (newEls.length > 0) {
        const newElsSet = new Set(newEls);
        const topLevelBlocks = newEls.filter(el => {
            let p = el.parentElement;
            while (p && p !== container && p !== document.body) {
                if (newElsSet.has(p)) return false;
                p = p.parentElement;
            }
            return true;
        });
        const validBlocks = topLevelBlocks.filter(el => {
            const tag = el.tagName.toLowerCase();
            if (['script', 'style', 'svg', 'path', 'button', 'iframe', 'nav'].includes(tag)) return false;
            if (!el.innerText || el.innerText.trim() === '') {
                if (!el.querySelector('img')) return false;
            }
            return true;
        });
        if (validBlocks.length > 0) {
            const limited = validBlocks.slice(0, MAX_BLOCKS);
            const html = limited.map(el => el.outerHTML).join('\n');
            if (html.trim().length > 50) return capHtml(html);
        }
    }
    const mdBlocks = document.querySelectorAll('.markdown-body, .ac-textBlock, .body-content, [data-message-author="Copilot"], .step-content');
    if (mdBlocks.length > 0) {
        const limited = Array.from(mdBlocks).slice(0, MAX_BLOCKS);
        const html = limited.map(el => el.outerHTML).join('\n');
        if (html.trim().length > 100) return capHtml(html);
    }
    const bodyText = document.body?.innerText || "";
    if (bodyText.length > 200) return `<pre>${escapeHtml(bodyText.slice(-3000))}</pre>`;
    return "";
}

// F5: Kiểm tra nội dung có phải là error message của trang không
function isErrorContent(html) {
    if (!html) return false;
    const textRaw = html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
    
    // 1. Nếu nội dung rất dài (> 400 ký tự) thì chắc chắn không phải thông báo lỗi đứt mạng.
    if (textRaw.length > 400) return false;

    const text = textRaw.toLowerCase().slice(0, 1000);
    const errorKeywords = [
        'something went wrong', 'try again', 'please try again',
        'connection error', 'network error', 'lỗi kết nối', 'thử lại',
        'request failed', 'service unavailable', '503', '502', '429',
        'too many requests', 'rate limit', 'hết lượt',
        'error occurred', 'đã xảy ra lỗi', 'cannot connect'
    ];
    
    // 2. Kiểm tra từ khóa lỗi (dùng regex boundary cho số để tránh nhầm 1503 -> 503)
    return errorKeywords.some(kw => {
        if (/^\d+$/.test(kw)) {
            return new RegExp(`\\b${kw}\\b`).test(text);
        }
        return text.includes(kw);
    });
}

function validateContent(html, agentName) {
    if (!html || html.trim().length < 100) return false;
    const text = html.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
    if (text.length < 100) return false;
    // F5: Từ chối nội dung là error message
    if (isErrorContent(html)) { appLog('⚠️ Phát hiện error content, sẽ retry...'); return false; }
    if (agentName && agentName.length > 3) {
        const escaped = agentName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const matches = (text.match(new RegExp(escaped, 'gi')) || []).length;
        // FIX GĐ 46: Dùng tỷ lệ theo ký tự thay vì đếm từ (split by whitespace)
        // để không bị false-reject khi AI trả lời bằng tiếng Nhật/Trung (không có dấu cách)
        const nameCharCount = matches * agentName.length;
        if (nameCharCount > text.length * 0.4) {
            appLog('⚠️ AI spam tên Agent quá nhiều, sẽ retry...');
            return false;
        }
    }
    return true;
}

function getNewTextLength() {
    const mainEl = document.querySelector('[role="main"]') || document.querySelector('main') || document.body;
    const newEls = Array.from(mainEl.querySelectorAll('*')).filter(el => el.dataset.askcplSnapshot !== "1");
    if (newEls.length === 0) return mainEl.innerText.length;
    const newElsSet = new Set(newEls);
    let len = 0;
    for (const el of newEls) {
        let isTopLevel = true;
        let p = el.parentElement;
        while (p && p !== mainEl && p !== document.body) {
            if (newElsSet.has(p)) { isTopLevel = false; break; }
            p = p.parentElement;
        }
        if (isTopLevel) len += (el.innerText ? el.innerText.length : 0);
    }
    return len;
}

function isAIGenerating() {
    const btns = document.querySelectorAll('button');
    for (const b of btns) {
        const label = (b.getAttribute('aria-label') || b.getAttribute('title') || '').toLowerCase();
        if (label.includes('stop generating') || label.includes('dừng tạo') || label.includes('stop responding') || label.includes('dừng phản hồi')) {
            if (b.offsetParent !== null) return true;
        }
    }
    if (document.querySelector('div.loading-indicator, div.typing-indicator, [class*="streaming"], [class*="generating"]')) {
        return true;
    }
    return false;
}

async function checkStable15s() {
    const CHECK     = 2000;
    let lastLen     = getNewTextLength();
    let stableStart = Date.now();
    let textChangeStart = Date.now(); // Theo dõi lần cuối cùng chữ tăng thêm
    const funcStart = Date.now();

    while (true) {
        await delay(CHECK);
        if (!isRunning) return true;
        
        // Cập nhật STABLE_MS tùy thuộc vào việc tab có đang bị ẩn hay không
        // (Chrome có thể đóng băng việc render giao diện khi tab bị ẩn)
        const STABLE_MS = document.hidden ? 45000 : 15000;
        
        const len = getNewTextLength();
        if (Math.abs(len - lastLen) <= 30) {
            // Chữ KHÔNG tăng thêm đáng kể
            if (Date.now() - stableStart >= STABLE_MS) {
                // Nếu không có dấu hiệu generating từ UI, thì coi là đã xong (stable = true)
                if (!isAIGenerating()) return true;
            }
            
            // Fix kẹt vô tận: Nếu chữ KHÔNG tăng thêm tẹo nào trong 60s (dù UI có báo generating đi chăng nữa)
            // -> Ép buộc trả về false (timeout/lỗi) để kích hoạt cơ chế Retry mở Chat Mới của hệ thống
            if (Date.now() - textChangeStart >= 60000) {
                appLog(`⚠️ Chữ không thay đổi trong 60s. Dấu hiệu kẹt mạng/lỗi AI. Hủy chờ.`);
                return false; 
            }
        } else {
            // Chữ CÓ tăng thêm
            lastLen = len;
            stableStart = Date.now();
            textChangeStart = Date.now(); // Reset bộ đếm kẹt
        }
    }
}

async function waitForResponseComplete(promptLabel) {
    const MIN_WAIT  = 15000;
    const MAX_TOTAL = 600000;
    const POLL      = 10000;

    sendStatus(`"${promptLabel}" — Chờ AI phản hồi...`);
    const startTime = Date.now();
    await delay(MIN_WAIT);
    if (!isRunning) return;

    while (Date.now() - startTime < MAX_TOTAL) {
        const stable = await checkStable15s();
        if (stable) return;
        await delay(POLL);
        if (!isRunning) return;
    }
}

// ── ADVANCED MEMORY BUILDER ──────────────────────────────────
function buildMemoryPrompt() {
    if (!isAdvanced || Object.keys(topicMemory).length === 0) return "";
    let lines = ["\n\nNội dung đã học:"];
    for (const [topic, data] of Object.entries(topicMemory)) {
        if (data.count >= targetCount) {
            lines.push(`Chủ đề: ${topic} (Hoàn tất)`);
        } else {
            lines.push(`Chủ đề: ${topic} ${data.count}/${targetCount}`);
            if (data.details && detailConfigs.length > 0) {
                for (const detail of detailConfigs) {
                    if (data.details[detail.name]) {
                        lines.push(`${detail.name} đã học:`);
                        lines.push(data.details[detail.name]);
                    }
                }
            }
            lines.push("");
        }
    }
    return lines.join("\n");
}

// Helper: Hỏi thêm AI sau bài chính
async function askSecondaryPrompt(promptText) {
    appLog(`Secondary prompt: "${promptText}"`);
    let inputEl = null;
    for (let attempt = 1; attempt <= 10; attempt++) {
        _cachedInput   = null;
        _cachedSendBtn = null;
        inputEl = findChatInput();
        if (inputEl) break;
        await delay(2000);
        if (!isRunning) return null;
    }
    if (!inputEl) {
        appLog(`❌ Không tìm thấy ô nhập cho secondary prompt.`);
        return null;
    }
    const snapshot = snapshotBeforeSend();
    try { fillInput(inputEl, promptText); } catch (e) {}

    await delay(1500);
    _cachedSendBtn = null;
    const sendBtn = findSendButton();
    if (sendBtn) {
        sendBtn.click();
    } else {
        const opts = { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true, cancelable: true, composed: true };
        inputEl.dispatchEvent(new KeyboardEvent('keydown', opts));
        await delay(100);
        inputEl.dispatchEvent(new KeyboardEvent('keyup', opts));
    }
    await waitForResponseComplete("Secondary prompt");
    if (!isRunning) return null;
    return extractDeltaContent(snapshot);
}

// ── HIERARCHICAL PROMPT INJECTOR ────────────────────────────────
function buildPromptWithMemory(day) {
    if (promptMode === 'basic') return `${prefixStr}${day}`;
    if (promptMode === 'advanced') return `${prefixStr}${day}` + buildMemoryPrompt();

    if (promptMode === 'file_md' && roadmapData) {
        const found = roadmapData.find(d => d.day === day);
        if (found && found.prompt) {
            return found.prompt;
        }
        return `${prefixStr}${day}`; // Fallback
    }

    if (promptMode === 'table_md' && roadmapData) {
        let currentChapter = null;
        let dayData = null;
        for (const chapter of roadmapData) {
            const found = chapter.days.find(d => d.day === day);
            if (found) {
                currentChapter = chapter;
                dayData = found;
                break;
            }
        }

        if (!dayData) return `${prefixStr}${day}` + buildMemoryPrompt();

        let prompt = "";
        const isFirstDayOfChapter = (currentChapter.days[0].day === day);
        
        if (isFirstDayOfChapter) {
            prompt += `[BỐI CẢNH]\nChúng ta đang bắt đầu học chủ đề mới: ${currentChapter.main_topic}.\n`;
            prompt += `Tuyệt đối không nhắc lại hay bám vào các chi tiết của các chủ đề cũ (nếu có).\n\n`;
        } else {
            prompt += `[BỐI CẢNH]\nChúng ta đang học chủ đề: ${currentChapter.main_topic}.\n`;
            prompt += `Tóm tắt siêu ngắn các bài đã học trong chủ đề này để bạn nắm mạch học:\n`;
            for (const d of currentChapter.days) {
                if (d.day < day) {
                    const summary = historySummaries.find(s => s.day === d.day);
                    if (summary) prompt += `- Ngày ${d.day} (${d.title}): ${summary.text}\n`;
                }
            }
            prompt += `\n`;
        }

        prompt += `[BÀI HỌC HÔM NAY]\nHôm nay là Ngày ${day}: ${dayData.title}\n`;
        prompt += `Yêu cầu chi tiết: ${dayData.detail}\n`;
        prompt += buildMemoryPrompt();
        
        return prompt;
    }

    return `${prefixStr}${day}`;
}

// ── Vòng lặp chính ───────────────────────────────────────────
async function runNextDay(isAutoResumed = false) {
    let retry = 0;
    while (isRunning) {
        const result = await _runNextDayAttempt(retry, isAutoResumed);
        if (result === 'ok' || result === 'stop') return;
        
        retry++;
        sendStatus(`Lỗi tải. Thử lại ${prefixStr}${currentDay} trong Chat Mới sau 15s (lần ${retry + 1})...`);
        await delay(15000);
    }
}

async function _runNextDayAttempt(retryCount, isAutoResumed = false) {
    if (!isRunning) return 'stop';
    
    // Gắn thêm Memory vào Prompt nếu bật Advanced hoặc có Roadmap
    const promptText = buildPromptWithMemory(currentDay);

    // needNewChat: cần mở chat mới nếu đã có data hoặc đang retry,
    // TRUẮN NHẮN khi là lần đầu sau resume/reload (isAutoResumed=true, retryCount=0)
    const needNewChat = (dayIndex.length > 0 || retryCount > 0) && !(isAutoResumed && retryCount === 0);
    if (needNewChat) {
        sendStatus(`Mở chat mới...`);
        clickNewChat();
        await waitForNewChatReady();
    } else if (isAutoResumed) {
        // Sau reload/resume: trang đã mới, chỉ cần chờ input sẵn sàng
        await waitForNewChatReady();
    }

    sendStatus(`Đang nhập: Day ${currentDay}`);
    let inputEl = null;
    for (let attempt = 1; attempt <= 10; attempt++) {
        _cachedInput   = null;
        _cachedSendBtn = null;
        inputEl = findChatInput();
        if (inputEl) { saveInputFingerprint(inputEl); break; }
        await delay(2000);
        if (!isRunning) return 'stop';
    }
    if (!inputEl) return 'retry';

    const snapshot = snapshotBeforeSend();
    try { fillInput(inputEl, promptText); } catch (e) {}

    await delay(1500);
    _cachedSendBtn = null;
    const sendBtn = findSendButton();
    if (sendBtn) {
        sendBtn.click();
    } else {
        const opts = { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true, cancelable: true, composed: true };
        inputEl.dispatchEvent(new KeyboardEvent('keydown', opts));
        await delay(100);
        inputEl.dispatchEvent(new KeyboardEvent('keyup', opts));
    }

    sendStatus(`Đã gửi Day ${currentDay}. Chờ AI...`);
    await waitForResponseComplete(`Day ${currentDay}`);
    if (!isRunning) return 'stop';

    let responseHtml = extractDeltaContent(snapshot);
    if (!validateContent(responseHtml, currentAgentName)) {
        await delay(15000);
        if (!isRunning) return 'stop';
        responseHtml = extractDeltaContent(snapshot);
        if (!validateContent(responseHtml, currentAgentName)) return 'retry';
    }

    // ── BƯỚC 1.5: AUTO SUMMARIZER FOR HIERARCHICAL ROADMAP ──
    if (promptMode === 'table_md' && roadmapData) {
        appLog(`📝 Đang lấy tóm tắt của Ngày ${currentDay}...`);
        let summaryHtml = await askSecondaryPrompt("Hãy tóm tắt cực kỳ ngắn gọn (dưới 20 từ) những kiến thức cốt lõi bạn vừa dạy ở trên.");
        if (summaryHtml) {
            let text = summaryHtml.replace(/<[^>]+>/g, '').trim();
            if (text) {
                historySummaries.push({ day: currentDay, text: text });
                appLog(`📝 Tóm tắt lưu lại: ${text.substring(0, 30)}...`);
            }
        }
    }

    // ── BƯỚC 2: ADVANCED MULTI-STEP INTERROGATION ──
    if (isAdvanced && topicPromptStr) {
        appLog(`🧠 Bắt đầu hỏi Advanced Memory...`);
        let topicHtml = await askSecondaryPrompt(topicPromptStr);
        if (topicHtml) {
            let topicName = topicHtml.replace(/<[^>]+>/g, '').trim().replace(/^\*\*|\*\*$/g, '').replace(/[:"]+/g, '').trim();
            if (topicName.length > 0 && topicName.length < 100) {
                if (!topicMemory[topicName]) {
                    topicMemory[topicName] = { count: 0, details: {} };
                }
                topicMemory[topicName].count += 1;
                appLog(`🧠 Chủ đề mới/cập nhật: ${topicName} (${topicMemory[topicName].count}/${targetCount})`);

                if (topicMemory[topicName].count < targetCount && detailConfigs.length > 0) {
                    for (const detail of detailConfigs) {
                        if (!isRunning) return 'stop';
                        let detailHtml = await askSecondaryPrompt(detail.prompt);
                        if (detailHtml) {
                            let detailText = detailHtml.replace(/<[^>]+>/g, '').trim();
                            if (detailText.length > 0) {
                                if (!topicMemory[topicName].details[detail.name]) {
                                    topicMemory[topicName].details[detail.name] = detailText;
                                } else {
                                    topicMemory[topicName].details[detail.name] += "\n" + detailText;
                                }
                                appLog(`🧠 Đã lưu chi tiết: ${detail.name}`);
                            }
                        }
                    }
                }
            }
        }
    }

    await processExtractedContent(`Day ${currentDay}`, responseHtml);
    return 'ok';
}

const SAVE_EVERY = 5;
async function processExtractedContent(promptLabel, responseHtml) {
    const savedFilename = downloadDayHtml(promptLabel, responseHtml);
    dayIndex.push({ day: promptLabel, filename: savedFilename, timestamp: new Date().toISOString() });
    autoSave();
    safeSendMessage({ action: "day_saved", dayLabel: promptLabel, totalSaved: dayIndex.length });

    if (dayIndex.length % SAVE_EVERY === 0) {
        updateIndex();
        saveSession();
    }

    if (endDay && currentDay >= endDay) {
        finishLoop(`Hoàn tất: Đạt đến Ngày kết thúc (${endDay}).`);
        return;
    }

    currentDay++;
    saveRunningState(currentDay, promptLabel);
    sendStatus(`Chuẩn bị hỏi Day ${currentDay}...`);
    setTimeout(() => runNextDay(), 0);
}
