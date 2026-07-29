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
        textNodes.includes("you have reached the maximum") ||
        textNodes.includes("you've used all your google cloud projects")) {
        // Tự động đóng mọi dialog/popup đang mở
        closeCurrentDialog();
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
                        
                        // Tự động kiểm tra đổi Email -> Chỉ reset đếm, không xuất JSON
                        if (keys.length > 0) {
                            let lastEmail = keys[keys.length - 1].email;
                            if (lastEmail && lastEmail !== email) {
                                log("Phát hiện đổi tài khoản email. Reset bộ đếm và bắt đầu lại...");
                                keys = []; // Xóa keys cũ để bắt đầu vòng mới
                                chrome.storage.local.set({ api_keys: [] });
                            }
                        }

                        // Lấy Project Name từ dropdown đang hiển thị
                        let currDropdown = document.querySelector('mat-select, [role="combobox"]');
                        let pname = currDropdown ? currDropdown.textContent.trim() : "";

                        let isDuplicate = keys.some(k => (typeof k === 'object' && k.key === apiKey) || k === apiKey);
                        if (!isDuplicate) {
                            keys.push({
                                key: apiKey,
                                email: email,
                                type: "GEMINI API",
                                project_name: pname,
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
            const isApiKey = (text) => text && (typeof text === 'string') && (text.trim().startsWith("AIza") || text.trim().startsWith("AQ."));
            
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
                        const matches = text.match(/(?:AIza[A-Za-z0-9_-]{30,40}|AQ\.[A-Za-z0-9_-]{30,60})/g);
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
                        const matches = this.responseText.match(/(?:AIza[A-Za-z0-9_-]{30,40}|AQ\.[A-Za-z0-9_-]{30,60})/g);
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
                    type: "GEMINI API",
                    project_name: window.__currentScrapingProjectName || "",
                    project_id: window.__currentScrapingProjectId || ""
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
        log("Bắt đầu cào toàn bộ Key cũ bằng phương pháp Click-Dialog!");
        
        const email = extractEmail();
        
        // Bước 1: Quét tất cả các row để lấy masked suffix + project info
        const rows = document.querySelectorAll('tr.mat-mdc-row, mat-row, [role="row"].mat-mdc-row, .mdc-data-table__row');
        let domKeys = [];
        
        rows.forEach(row => {
            // Lấy masked key từ button.key-string-link
            const keyBtn = row.querySelector('button.key-string-link, .key-string-link');
            if (!keyBtn) return;
            
            const maskedText = (keyBtn.textContent || "").trim();
            if (!maskedText.startsWith('...') || maskedText.length < 5) return;
            const suffix = maskedText.replace('...', '').trim();
            
            // Lấy project name + project ID từ row
            let projectName = "";
            let projectId = "";
            const projBtn = row.querySelector('button.key-table-link, .key-table-link');
            if (projBtn) projectName = projBtn.textContent.trim();
            const subTexts = row.querySelectorAll('.sub-text');
            subTexts.forEach(s => {
                const t = s.textContent.trim();
                if (t.includes('gen-lang-client-')) projectId = t;
            });
            
            domKeys.push({ suffix, projectName, projectId, keyBtn, fullKey: null });
        });
        
        if (domKeys.length === 0) {
            sendResponse({ status: "error", count: 0 });
            return;
        }
        
        log(`Tìm thấy ${domKeys.length} key trên UI. Bắt đầu click từng nút để lấy Full Key...`);
        
        // Bước 2: Click lần lượt từng nút, đọc full key từ dialog
        let currentIdx = 0;
        
        function processNext() {
            if (currentIdx >= domKeys.length) {
                // Hoàn thành! Lưu vào storage
                chrome.storage.local.get(['api_keys'], (res) => {
                    let keys = res.api_keys || [];
                    const dominantSuffixes = new Set(domKeys.map(dk => dk.suffix));
                    
                    // Cleanup phantom keys
                    keys = keys.filter(k => {
                        let kVal = typeof k === 'object' ? k.key : k;
                        let suffix4 = kVal.slice(-4);
                        let hasMatchOnUI = dominantSuffixes.has(kVal.slice(-4)) || dominantSuffixes.has(kVal.slice(-5));
                        let hasProjectId = typeof k === 'object' && k.project_id && k.project_id.trim() !== "";
                        let isAutoCreated = typeof k === 'object' && k.project_name && k.project_name.trim() !== "";
                        return hasMatchOnUI || hasProjectId || isAutoCreated;
                    });
                    
                    let addedCount = 0;
                    domKeys.forEach(dk => {
                        if (!dk.fullKey) return;
                        
                        // Tìm key đã có trong storage (match theo suffix)
                        let existing = keys.find(k => {
                            let val = typeof k === 'object' ? k.key : k;
                            return val && val.endsWith(dk.suffix);
                        });
                        
                        if (existing) {
                            // Cập nhật project info
                            if (typeof existing === 'object') {
                                existing.project_name = dk.projectName;
                                existing.project_id = dk.projectId;
                                if (dk.fullKey !== "UNKNOWN") existing.key = dk.fullKey;
                            }
                        } else {
                            // Thêm key mới
                            keys.push({
                                key: dk.fullKey,
                                email: email,
                                type: "GEMINI API",
                                project_name: dk.projectName,
                                project_id: dk.projectId
                            });
                            addedCount++;
                        }
                    });
                    
                    chrome.storage.local.set({ api_keys: keys }, () => {
                        log(`✅ Xong! Đã lưu ${keys.length} key (thêm mới: ${addedCount}).`);
                        sendResponse({ status: "ok", count: keys.length });
                    });
                });
                return;
            }
            
            const dk = domKeys[currentIdx];
            log(`[${currentIdx + 1}/${domKeys.length}] Đang lấy key có đuôi: ...${dk.suffix}`);
            
            // Click vào nút masked key để mở dialog chi tiết
            dk.keyBtn.click();
            
            // Chờ dialog mở ra và đọc full key
            let attempts = 0;
            const waitForDialog = setInterval(() => {
                attempts++;
                
                // Tìm dialog hoặc overlay chứa full key
                const dialogs = document.querySelectorAll('mat-dialog-container, [role="dialog"], .cdk-overlay-container .mat-mdc-dialog-container, ms-api-key-details');
                let fullKey = null;
                
                dialogs.forEach(dialog => {
                    const txt = dialog.innerText || "";
                    // Tìm dạng AQ.xxxx hoặc AIzaxxxx
                    const m = txt.match(/(?:AQ\.[A-Za-z0-9_/+\-]{30,80}|AIza[A-Za-z0-9_\-]{30,50})/);
                    if (m) fullKey = m[0];
                });
                
                if (fullKey || attempts > 20) {
                    clearInterval(waitForDialog);
                    
                    if (fullKey) {
                        log(`✓ Lấy được: ${fullKey.substring(0, 15)}...`);
                        dk.fullKey = fullKey;
                    } else {
                        log(`⚠ Không đọc được full key cho ...${dk.suffix} (dialog không hiện hoặc timeout)`);
                        dk.fullKey = "UNKNOWN";
                    }
                    
                    // Đóng dialog bằng Escape
                    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', keyCode: 27, bubbles: true }));
                    
                    // Chờ dialog đóng rồi xử lý key tiếp theo
                    setTimeout(() => {
                        currentIdx++;
                        processNext();
                    }, 600);
                }
            }, 200); // Kiểm tra mỗi 200ms
        }
        
        processNext();
        return true;
    }
});
log("Content script đã sẵn sàng với luồng chi tiết & tính năng Export.");
