let currentState = 'INIT';
let previousProjectName = ''; // Để so sánh xem tên project đã thay đổi chưa
let retryCount = 0;

function findButtonByText(text) {
    const elements = Array.from(document.querySelectorAll('button, div[role="button"], span[role="button"], a, mat-option, [role="option"]'));
    for (let el of elements) {
        if (el.textContent && el.textContent.trim() === text) {
            return el;
        }
    }
    for (let el of elements) {
        if (el.textContent && el.textContent.includes(text)) {
            return el;
        }
    }
    return null;
}

function findDialogByTitle(titleSnippet) {
    const dialogs = document.querySelectorAll('mat-dialog-container, [role="dialog"]');
    for (let d of dialogs) {
        if (d.textContent.includes(titleSnippet)) {
            return d;
        }
    }
    return null;
}

function log(msg) {
    console.log("[API Geminikey]", msg);
    chrome.storage.local.set({ last_log: msg });
}

function checkLimits() {
    const textNodes = document.body.textContent.toLowerCase();
    if (textNodes.includes("maximum number of projects") || 
        textNodes.includes("quota exceeded") || 
        textNodes.includes("you have reached the maximum")) {
        return true;
    }
    return false;
}

function extractEmail() {
    // Dùng regex để tìm email trong toàn bộ mã nguồn html
    const htmlContent = document.documentElement.innerHTML;
    const match = htmlContent.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
    if (match) {
        return match[0];
    }
    return "unknown@gmail.com";
}

function extractApiKey() {
    // Gemini keys thường bắt đầu bằng AIzaSy... hoặc AQ.
    // Lấy toàn bộ text node trong body
    const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
    let node;
    const regex = /^(AIzaSy|AQ\.)[A-Za-z0-9_-]{30,}$/;
    while (node = walk.nextNode()) {
        const text = node.nodeValue.trim();
        if (regex.test(text)) {
            return text;
        }
    }
    return null;
}

function extractProjectId() {
    const fieldHeaders = document.querySelectorAll('.field-header');
    for (let header of fieldHeaders) {
        if (header.textContent.includes('Project number') || header.textContent.includes('Project ID')) {
            const valEl = header.nextElementSibling ? header.nextElementSibling.querySelector('.field-value') : null;
            if (valEl) return valEl.textContent.trim();
        }
    }
    return "";
}

function closeCurrentDialog() {
    // Cách 1: Nút aria-label="close" hoặc matdialogclose
    const closeBtn = document.querySelector('button[aria-label="close" i], button[matdialogclose], button.close-button, button[aria-label="Close"], button[mat-dialog-close]');
    if (closeBtn) {
        closeBtn.click();
        return true;
    }
    // Cách 2: Thử nhấn phím Escape
    const escEvent = new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', keyCode: 27, bubbles: true });
    document.dispatchEvent(escEvent);
    return true;
}

function runStateMachine() {
    chrome.storage.local.get(['auto_create_running', 'api_keys'], (res) => {
        if (!res.auto_create_running) {
            currentState = 'INIT';
            return;
        }

        if (checkLimits()) {
            log("LIMIT REACHED! Bị chặn limit quota.");
            chrome.storage.local.set({ auto_create_running: false });
            return;
        }

        switch (currentState) {
            case 'INIT':
                log("Đang tìm nút 'Create API key' ở màn hình chính...");
                let createBtn = findButtonByText("Create API key");
                // Đảm bảo không phải đang trong dialog
                if (createBtn && !document.querySelector('[role="dialog"]')) {
                    createBtn.click();
                    currentState = 'WAIT_DIALOG_OPEN';
                }
                break;

            case 'WAIT_DIALOG_OPEN':
                log("Đang chờ Dialog 'Create a new key' mở ra...");
                if (findDialogByTitle("Create a new key")) {
                    setTimeout(() => { currentState = 'CLICK_DROPDOWN'; }, 500);
                }
                break;

            case 'CLICK_DROPDOWN':
                log("Đang tìm và click vào Dropdown chọn Project...");
                // Tìm dropdown (thường là mat-select)
                let dropdown = document.querySelector('mat-select, [role="combobox"]');
                if (dropdown) {
                    previousProjectName = dropdown.textContent.trim();
                    dropdown.click();
                    currentState = 'CLICK_CREATE_PROJECT_MENU';
                } else {
                    log("Không tìm thấy Dropdown.");
                }
                break;

            case 'CLICK_CREATE_PROJECT_MENU':
                log("Đang tìm tùy chọn '+ Create project' trong menu xổ ra...");
                let createProjOption = findButtonByText("+ Create project") || findButtonByText("Create project");
                if (createProjOption) {
                    createProjOption.click();
                    currentState = 'CONFIRM_NEW_PROJECT';
                    retryCount = 0;
                } else {
                    retryCount++;
                    if (retryCount > 5) {
                        log("Không thấy menu 'Create project', thử click lại dropdown.");
                        currentState = 'CLICK_DROPDOWN';
                        retryCount = 0;
                    }
                }
                break;

            case 'CONFIRM_NEW_PROJECT':
                log("Đang chờ Dialog 'Create a new project'...");
                let newProjDialog = findDialogByTitle("Create a new project");
                if (newProjDialog) {
                    let confirmBtn = Array.from(newProjDialog.querySelectorAll('button')).find(b => b.innerText.includes('Create project'));
                    if (confirmBtn && !confirmBtn.disabled) {
                        log("Click xác nhận 'Create project'!");
                        confirmBtn.click();
                        currentState = 'WAIT_PROJECT_AND_CREATE_KEY';
                    }
                }
                break;

            case 'WAIT_PROJECT_AND_CREATE_KEY':
                log("Chờ Project tạo xong và chọn Create Key...");
                let currDropdown = document.querySelector('mat-select, [role="combobox"]');
                let currentName = currDropdown ? currDropdown.textContent.trim() : '';
                
                let createKeyBtn = findButtonByText("Create key") || findButtonByText("Create API key in existing project");
                
                // BẮT BUỘC CHỜ tên Project trong dropdown thay đổi khác với tên cũ
                if (createKeyBtn && !createKeyBtn.disabled && currentName !== '' && currentName !== previousProjectName) {
                    log("Đã chọn xong project mới: " + currentName + ". Chờ 3s đồng bộ hệ thống...");
                    currentState = 'WAIT_SYNC';
                    setTimeout(() => {
                        let btn = findButtonByText("Create key") || findButtonByText("Create API key in existing project");
                        if (btn && !btn.disabled) {
                            btn.click();
                            log("Đã click 'Create key'!");
                        }
                        currentState = 'EXTRACT_KEY_AND_CLOSE';
                    }, 3500); // Đợi 3.5s cho an toàn
                }
                break;
                
            case 'WAIT_SYNC':
                // Đang trong thời gian chờ 3.5s, không làm gì cả
                break;

            case 'EXTRACT_KEY_AND_CLOSE':
                log("Chờ hộp thoại API key details để copy key...");
                let detailDialog = findDialogByTitle("API key details");
                if (detailDialog) {
                    // Cố gắng tìm API key
                    let apiKey = extractApiKey();
                    if (apiKey) {
                        log("Đã lấy được Key: " + apiKey.substring(0, 10) + "...");
                        let email = extractEmail();
                        let projectId = extractProjectId();
                        
                        let keys = res.api_keys || [];
                        
                        // Tự động kiểm tra đổi Email -> Lưu ngầm và reset
                        if (keys.length > 0) {
                            let lastEmail = keys[keys.length - 1].email;
                            if (lastEmail && lastEmail !== email) {
                                log("Phát hiện đổi tài khoản email. Tự động lưu JSON cũ và đếm lại...");
                                const jsonStr = JSON.stringify(keys, null, 2);
                                const blob = new Blob([jsonStr], { type: "application/json" });
                                const url = URL.createObjectURL(blob);
                                const a = document.createElement("a");
                                a.href = url;
                                let safeEmail = lastEmail.split('@')[0] || "old";
                                a.download = "gemini_api_keys_" + safeEmail + ".json";
                                document.body.appendChild(a);
                                a.click();
                                document.body.removeChild(a);
                                URL.revokeObjectURL(url);
                                keys = []; // Xóa keys cũ để bắt đầu vòng mới
                            }
                        }

                        // Check duplicate
                        let isDuplicate = keys.some(k => (typeof k === 'object' && k.key === apiKey) || k === apiKey);
                        if (!isDuplicate) {
                            keys.push({
                                key: apiKey,
                                email: email,
                                type: "GEMINI API",
                                project_id: projectId
                            });
                            chrome.storage.local.set({ api_keys: keys });
                        }
                        
                        log("Đóng dialog.");
                        closeCurrentDialog();
                        
                        // Chờ dialog đóng xong rồi quay lại INIT
                        setTimeout(() => {
                            currentState = 'INIT';
                        }, 1000);
                    }
                }
                break;
        }
    });
}

// Khởi động vòng lặp
setInterval(runStateMachine, 1500);

// ==========================================
// TÍNH NĂNG CÀO KEY CŨ (CLIPBOARD HIJACKING)
// ==========================================
function injectClipboardHijacker() {
    let script = document.createElement('script');
    script.textContent = `
        window.__hijackedKeys = [];
        if (!window.__clipboardHijacked) {
            const isApiKey = (text) => text && (typeof text === 'string') && (text.startsWith("AIza") || text.startsWith("AQ."));
            
            // 1. Chặn navigator.clipboard.writeText
            if (navigator.clipboard) {
                const originalWriteText = navigator.clipboard.writeText;
                navigator.clipboard.writeText = function(text) {
                    if (isApiKey(text)) {
                        window.postMessage({ type: "API_KEY_HIJACKED", key: text }, "*");
                    }
                    return originalWriteText.apply(this, arguments);
                };
            }
            
            // 2. Chặn document.execCommand('copy') (Dùng làm fallback trong Angular CDK)
            const originalExecCommand = document.execCommand;
            document.execCommand = function(command, showUI, value) {
                if (command.toLowerCase() === 'copy') {
                    let text = window.getSelection().toString();
                    if (!text) {
                        let activeEl = document.activeElement;
                        if (activeEl && (activeEl.tagName === 'TEXTAREA' || activeEl.tagName === 'INPUT')) {
                            text = activeEl.value.substring(activeEl.selectionStart, activeEl.selectionEnd) || activeEl.value;
                        }
                    }
                    if (isApiKey(text)) {
                        window.postMessage({ type: "API_KEY_HIJACKED", key: text }, "*");
                    }
                }
                return originalExecCommand.apply(this, arguments);
            };
            
            // 3. Chặn hàm select() của textarea (Angular CDK Clipboard dùng cái này trước khi execCommand)
            const originalSelect = HTMLTextAreaElement.prototype.select;
            HTMLTextAreaElement.prototype.select = function() {
                let text = this.value;
                if (isApiKey(text)) {
                    window.postMessage({ type: "API_KEY_HIJACKED", key: text }, "*");
                }
                return originalSelect.apply(this, arguments);
            };
            
            // 4. Mạng lưới tình báo XHR / Fetch (Bắt key trả về từ server)
            const originalFetch = window.fetch;
            window.fetch = async function() {
                try {
                    const response = await originalFetch.apply(this, arguments);
                    const clone = response.clone();
                    clone.text().then(text => {
                        const matches = text.match(/(?:AIzaSy[A-Za-z0-9_-]{33}|AQ\.[A-Za-z0-9_-]+)/g);
                        if (matches) {
                            matches.forEach(k => {
                                if (isApiKey(k)) window.postMessage({ type: "API_KEY_HIJACKED", key: k }, "*");
                            });
                        }
                    }).catch(e => {});
                    return response;
                } catch(e) {
                    throw e;
                }
            };
            
            const originalXHROpen = XMLHttpRequest.prototype.open;
            const originalXHRSend = XMLHttpRequest.prototype.send;
            XMLHttpRequest.prototype.send = function() {
                this.addEventListener('load', function() {
                    if (this.responseText) {
                        const matches = this.responseText.match(/(?:AIzaSy[A-Za-z0-9_-]{33}|AQ\.[A-Za-z0-9_-]+)/g);
                        if (matches) {
                            matches.forEach(k => {
                                if (isApiKey(k)) window.postMessage({ type: "API_KEY_HIJACKED", key: k }, "*");
                            });
                        }
                    }
                });
                return originalXHRSend.apply(this, arguments);
            };
            
            window.__clipboardHijacked = true;
            console.log("[API Geminikey] Clipboard Hijacker Injected Early! (Network Interceptor Active)");
        }
    `;
    (document.head || document.documentElement).appendChild(script);
    script.remove();
}

// Bắt buộc tiêm ngay khi Content Script load (để không bị lỡ việc Angular lưu reference của hàm)
injectClipboardHijacker();

// Lắng nghe Key bị cướp từ Clipboard
window.addEventListener("message", (event) => {
    if (event.data && event.data.type === "API_KEY_HIJACKED") {
        let apiKey = event.data.key;
        let email = extractEmail();
        chrome.storage.local.get(['api_keys'], (res) => {
            let keys = res.api_keys || [];
            let isDuplicate = keys.some(k => (typeof k === 'object' && k.key === apiKey) || k === apiKey);
            if (!isDuplicate) {
                keys.push({
                    key: apiKey,
                    email: email,
                    type: "GEMINI API"
                });
                chrome.storage.local.set({ api_keys: keys });
                log("Đã cào thành công 1 Key cũ!");
            }
        });
    }
});

// Lắng nghe lệnh từ Popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "SCRAPE_OLD_KEYS") {
        log("Bắt đầu cào toàn bộ Key cũ!");
        
        // Chờ 1 giây để script chuẩn bị, sau đó click tất cả nút copy
        setTimeout(() => {
            const allButtons = document.querySelectorAll('button, [role="button"], a');
            let count = 0;
            
            allButtons.forEach(btn => {
                const label = (btn.getAttribute('aria-label') || '').toLowerCase();
                const text = btn.textContent.trim().toLowerCase();
                
                // Nếu aria-label có chữ copy HOẶC nội dung text là icon 'content_copy'
                if (label.includes('copy') || text === 'content_copy' || text.includes('content_copy')) {
                    setTimeout(() => {
                        // Mô phỏng click cực mạnh (Khoanh vùng tương tác vật lý giả lập)
                        if (typeof btn.focus === 'function') btn.focus();
                        
                        const rect = btn.getBoundingClientRect();
                        const clientX = rect.left + rect.width / 2;
                        const clientY = rect.top + rect.height / 2;
                        const commonOpts = { bubbles: true, cancelable: true, view: window, clientX, clientY };
                        
                        btn.dispatchEvent(new PointerEvent('pointerover', commonOpts));
                        btn.dispatchEvent(new PointerEvent('pointerenter', commonOpts));
                        btn.dispatchEvent(new PointerEvent('pointerdown', commonOpts));
                        btn.dispatchEvent(new MouseEvent('mousedown', commonOpts));
                        btn.dispatchEvent(new PointerEvent('pointerup', commonOpts));
                        btn.dispatchEvent(new MouseEvent('mouseup', commonOpts));
                        btn.click();
                        
                    }, count * 500); // Click mỗi nút cách nhau 500ms
                    count++;
                }
            });
            
            log("Đã kích hoạt click " + count + " nút Copy.");
            sendResponse({ status: "ok", count: count });
        }, 1000);
        return true;
    }
});
log("Content script đã sẵn sàng với luồng chi tiết & tính năng Export.");
