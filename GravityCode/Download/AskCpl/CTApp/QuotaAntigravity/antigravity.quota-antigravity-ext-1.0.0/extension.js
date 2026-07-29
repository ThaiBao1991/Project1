const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const os = require('os');
const cp = require('child_process'); // for auto-sync

let myStatusBarItem;
let currentEmail = "Unknown Account";
let dataFilePath = "";
let quotaPanel = null;
let lmWatcherInterval = null;
let lmLastAvailable = true;
let _ctx = null; // extension context reference

// ============================================================
// TOKEN MANAGER — tự chủ lưu/đọc token trong context.secrets của chính mình
// Không phụ thuộc vào Antigravity Account extension.
// ============================================================
const TokenManager = {
    _getTokenFile() {
        let dataPath = vscode.workspace.getConfiguration('quotaTracker').get('dataPath');
        if (!dataPath) {
            dataPath = path.join(require('os').homedir(), '.gemini', 'quota_data.dat');
        }
        return path.join(path.dirname(dataPath), 'quota_tokens.json');
    },

    _readAll() {
        try {
            const fs = require('fs');
            const file = this._getTokenFile();
            if (fs.existsSync(file)) {
                const raw = fs.readFileSync(file, 'utf-8');
                // Decode UTF-8 safely using Buffer
                const decoded = Buffer.from(raw, 'base64').toString('utf-8');
                return JSON.parse(decoded);
            }
        } catch (e) {
            console.error('Error reading tokens:', e);
        }
        return {};
    },

    _writeAll(data) {
        try {
            const fs = require('fs');
            const file = this._getTokenFile();
            const dir = path.dirname(file);
            if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
            
            const jsonStr = JSON.stringify(data);
            // Encode UTF-8 safely using Buffer
            const encoded = Buffer.from(jsonStr, 'utf-8').toString('base64');
            fs.writeFileSync(file, encoded, 'utf-8');
        } catch (e) {
            console.error('Error writing tokens:', e);
        }
    },

    async store(email, accessToken, refreshToken, expiresAt) {
        const all = this._readAll();
        all[email] = { accessToken, refreshToken, expiresAt: expiresAt || (Date.now() + 3600 * 1000) };
        this._writeAll(all);
    },

    async get(email) {
        const all = this._readAll();
        return all[email] || null;
    },

    async delete(email) {
        const all = this._readAll();
        if (all[email]) {
            delete all[email];
            this._writeAll(all);
        }
    },

    // Lấy access token hợp lệ, tự refresh nếu gần hết hạn
    async ensureValid(email) {
        const stored = await this.get(email);
        if (!stored) return null;
        const now = Date.now();
        // Nếu còn hơn 5 phút thì dùng luôn
        if (stored.expiresAt && stored.expiresAt - now > 5 * 60 * 1000) {
            return stored.accessToken;
        }
        // Hết hạn hoặc sắp hết: thử refresh
        if (!stored.refreshToken) return stored.accessToken; // không có refresh token thì cứ dùng
        try {
            const { AuthService } = require('./oauth.js');
            const newTokens = await AuthService.refreshAccessToken(stored.refreshToken);
            const expiresAt = newTokens.expires_in ? Date.now() + newTokens.expires_in * 1000 : Date.now() + 3600000;
            await this.store(email, newTokens.access_token, newTokens.refresh_token || stored.refreshToken, expiresAt);
            return newTokens.access_token;
        } catch (e) {
            console.error(`Token refresh lỗi cho ${email}:`, e.message);
            return stored.accessToken; // dùng token cũ nếu refresh thất bại
        }
    },

    // Quản lý danh sách email trong quota_tokens.json luôn thay vì globalState
    async listEmails() {
        const all = this._readAll();
        return Object.keys(all);
    },

    async addEmail(email) {
        // Dummy, việc add sẽ diễn ra khi gọi store()
    },

    async removeEmail(email) {
        await this.delete(email);
    }
};

// --- Compute groupStatus from raw balances (mirrors Python assess_account) ---
function computeGroupStatus(balances) {
    if (!balances || !Object.keys(balances).length) return null;
    const now = Date.now();
    const groups = {
        gemini: (m) => m.startsWith('gemini-') || m === 'gemini-pro-agent',
        claude: (m) => m.startsWith('claude-'),
        gpt: (m) => m.startsWith('gpt-'),
    };
    const groupStatus = {};
    for (const [groupName, matcher] of Object.entries(groups)) {
        const groupBalances = Object.entries(balances).filter(([m, info]) => matcher(m) && info && typeof info === 'object');
        if (!groupBalances.length) continue;
        
        let keyModel = null;
        if (groupName === 'claude') keyModel = 'claude-sonnet-4-6';
        else if (groupName === 'gemini') keyModel = 'gemini-3.1-pro-high';
        else if (groupName === 'gpt') keyModel = 'gpt-oss-120b-medium';

        let isExhausted = false;
        let resetTime = 0;
        let percent = 100;

        const keyInfo = keyModel ? groupBalances.find(([m]) => m === keyModel) : null;

        if (keyInfo) {
            const info = keyInfo[1];
            percent = info.value !== undefined ? info.value : 100;
            resetTime = info.resetTime ? new Date(info.resetTime).getTime() : 0;

            if (percent === 0 && resetTime > now) {
                isExhausted = true;
            } else if (percent === 0 && resetTime <= now) {
                isExhausted = false;
                percent = 100;
                resetTime = 0;
            }
        } else {
            const depleted = groupBalances.filter(([, info]) => (info.value === 0 || info.value === "0") && info.resetTime);
            const total = groupBalances.length;
            if (depleted.length >= Math.max(1, Math.floor(total / 2))) {
                const maxReset = Math.max(...depleted.map(([, info]) => new Date(info.resetTime).getTime()));
                if (maxReset > now) {
                    isExhausted = true;
                    resetTime = maxReset;
                    percent = 0;
                } else {
                    isExhausted = false;
                    resetTime = 0;
                    percent = 100;
                }
            } else {
                const okModels = groupBalances.filter(([, info]) => (info.value || 0) > 0);
                percent = okModels.length ? Math.min(...okModels.map(([, i]) => i.value !== undefined ? i.value : 100)) : 100;
                const depResets = depleted.map(([, i]) => i.resetTime ? new Date(i.resetTime).getTime() : 0).filter(r => r > now);
                resetTime = depResets.length ? Math.min(...depResets) : 0;
            }
        }
        
        groupStatus[groupName] = { exhausted: isExhausted, resetTime: resetTime, percent: percent };
    }
    
    if (!Object.keys(groupStatus).length) return null;
    const availableGroups = Object.entries(groupStatus).filter(([, g]) => !g.exhausted).map(([k]) => k);
    const exhaustedGroups = Object.entries(groupStatus).filter(([, g]) => g.exhausted).map(([k]) => k);
    const allExhausted = availableGroups.length === 0;

    let overallResetTime = 0;
    const keyResets = Object.values(groupStatus).map(g => g.resetTime).filter(rt => rt > now);
    if (keyResets.length > 0) {
        overallResetTime = Math.min(...keyResets);
    }
    
    // exhaustedUntil is only set if the account is FULLY exhausted
    const exhaustedUntil = allExhausted ? overallResetTime : 0;
    return { groupStatus, availableGroups, exhaustedGroups, allExhausted, exhaustedUntil, overallResetTime };
}


// --- Data File Management ---
function loadData() {
    if (!dataFilePath || !fs.existsSync(dataFilePath)) return {};
    try {
        const raw = fs.readFileSync(dataFilePath, 'utf-8').trim();
        if (!raw) return {};
        // Quy tắc VÀNG equivalent for Node.js
        return JSON.parse(Buffer.from(raw, 'base64').toString('utf-8'));
    } catch (e) {
        console.error('Error loading data:', e);
        return {};
    }
}

function saveData(data) {
    if (!dataFilePath) return;
    // Quy tắc VÀNG equivalent for Node.js
    const raw = Buffer.from(JSON.stringify(data), 'utf-8').toString('base64');
    fs.writeFileSync(dataFilePath, raw, 'utf-8');
}

// --- Script path finder helper ---
function findScriptPath(name) {
    const base = dataFilePath ? path.dirname(dataFilePath) : '';
    const candidates = [
        path.join(process.env.USERPROFILE || '', 'Desktop', 'Project', 'Python', 'Python MyWork',
            'Project1', 'GravityCode', 'Download', 'AskCpl',
            'CTApp', 'QuotaAntigravity', 'QuotaApp', name),
        base ? path.join(base, name) : '',
        base ? path.join(base, '..', 'QuotaApp', name) : '',
    ].filter(Boolean);
    return candidates.find(p => fs.existsSync(p)) || null;
}

// --- Auto-Sync from DB (runs Python sync_antigravity.py) ---
function autoSyncFromDB(quotaProvider, onDone, emailFilter) {
    if (!dataFilePath) {
        onDone && onDone({ status: 'error', message: 'Chưa thiết lập đường dẫn Data.' });
        return;
    }

    const scriptPath = findScriptPath('sync_antigravity.py');
    if (!scriptPath) {
        onDone && onDone({ status: 'error', message: 'Không tìm thấy sync_antigravity.py.' });
        return;
    }

    const pyArgs = [scriptPath, dataFilePath];
    if (emailFilter) { pyArgs.push('--email', emailFilter); }
    cp.execFile('python', pyArgs, { timeout: 20000, encoding: 'utf-8' }, (err, stdout, stderr) => {
        if (err) {
            onDone && onDone({ status: 'error', message: stderr || err.message });
        } else {
            onDone && onDone({ status: 'ok', message: stdout.trim() });
        }
        quotaProvider.refresh();
        updateStatusBar();
        refreshPanel();
    });
}

// --- Helpers ---
function formatCountdown(exhaustedUntil) {
    if (!exhaustedUntil || exhaustedUntil <= Date.now()) return null;
    const ms = exhaustedUntil - Date.now();
    const h = Math.floor(ms / 3600000);
    const m = Math.floor((ms % 3600000) / 60000);
    return `${h}h ${m}m`;
}

function updateStatusBar() {
    if (!myStatusBarItem) return;
    const data = loadData();
    const info = data[currentEmail];
    const countdown = info?.exhaustedUntil ? formatCountdown(info.exhaustedUntil) : null;
    if (countdown) {
        myStatusBarItem.text = `$(error) ${currentEmail} — Còn ${countdown}`;
        myStatusBarItem.tooltip = 'Email này đang hết quota! Click để mở bảng Quota Tracker';
        myStatusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
    } else if (currentEmail !== "Unknown Account") {
        myStatusBarItem.text = `$(account) ${currentEmail} | Quota OK`;
        myStatusBarItem.tooltip = 'Click để mở bảng Quota Tracker (Alt+Q để đánh dấu nhanh)';
        myStatusBarItem.backgroundColor = undefined;
    } else {
        myStatusBarItem.text = `$(database) Quota Tracker`;
        myStatusBarItem.tooltip = 'Click để mở bảng Quota Tracker';
        myStatusBarItem.backgroundColor = undefined;
    }
    myStatusBarItem.show();
}

async function updateActiveAccount() {
    try {
        const session = await vscode.authentication.getSession('google', [], { createIfNone: false });
        currentEmail = session?.account?.label || "Unknown Account";
        if (dataFilePath) {
            const activeFile = path.join(path.dirname(dataFilePath), 'active_account.txt');
            fs.writeFileSync(activeFile, currentEmail, 'utf-8');
        }
    } catch (_) {}
    updateStatusBar();
    refreshPanel();
}

// --- Tree View Provider ---
class QuotaProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    refresh() { this._onDidChangeTreeData.fire(); }
    getTreeItem(el) { return el; }
    getChildren(el) {
        if (el) return Promise.resolve([]);
        const data = loadData();
        const entries = Object.entries(data);
        if (entries.length === 0) {
            const empty = new vscode.TreeItem(
                dataFilePath ? 'Chưa có email nào.' : '⚠️ Chưa chọn file Data.',
                vscode.TreeItemCollapsibleState.None
            );
            return Promise.resolve([empty]);
        }
        entries.sort(([, a], [, b]) => {
            const aEx = a.exhaustedUntil > Date.now() ? 1 : 0;
            const bEx = b.exhaustedUntil > Date.now() ? 1 : 0;
            return bEx - aEx;
        });
        return Promise.resolve(entries.map(([email, info]) => {
            const countdown = info.exhaustedUntil ? formatCountdown(info.exhaustedUntil) : null;
            const item = new vscode.TreeItem(email, vscode.TreeItemCollapsibleState.None);
            item.description = countdown ? `🔴 Còn ${countdown}` : '✅ Sẵn sàng';
            item.iconPath = new vscode.ThemeIcon(countdown ? 'error' : 'check');
            if (email === currentEmail) item.description += ' ◀ ACTIVE';
            return item;
        }));
    }
}

// --- (markExhausted removed) ---

// --- Set Data Path ---
async function setDataPath(quotaProvider) {
    const uri = await vscode.window.showSaveDialog({
        saveLabel: 'Tạo / Chọn file Data',
        filters: { 'Data Files (Encoded)': ['dat'] },
        defaultUri: vscode.Uri.file(path.join(os.homedir(), 'Desktop', 'quota_data.dat'))
    });

    if (uri) {
        dataFilePath = uri.fsPath;
        setDataPath._ctx.globalState.update('quotaDataPath', dataFilePath);
        if (!fs.existsSync(dataFilePath)) {
            saveData({});
        }
        vscode.window.showInformationMessage('Đã cập nhật thư mục lưu File Data ngầm!');
        
        // Auto-sync sau khi chọn thư mục
        autoSyncFromDB(quotaProvider, (res) => {
            if (res.status === 'ok') {
                vscode.window.showInformationMessage('🔄 Đã tự động Sync dữ liệu từ IDE.');
            }
        });
        
        quotaProvider.refresh();
        updateStatusBar();
        refreshPanel();
    }
}

// --- vscode.lm Auto-Detect Watcher ---
async function notifyAutoRotate(quotaProvider) {
    const data = loadData();
    const now = Date.now();
    const okEmail = Object.entries(data).find(([email, info]) =>
        email !== currentEmail && (!info.exhaustedUntil || info.exhaustedUntil <= now)
    )?.[0];
    if (okEmail) {
        const action = await vscode.window.showWarningMessage(
            `⚠️ ${currentEmail} hết Quota! Account sẵn sàng: ${okEmail}`,
            'Chuyển ngay', 'Bỏ qua'
        );
        if (action === 'Chuyển ngay') {
            await vscode.commands.executeCommand('antigravity-account.switchAccount');
        }
    } else {
        vscode.window.showWarningMessage(
            `⚠️ AI có vẻ không phản hồi với email: ${currentEmail}. Quota có thể đã hết, hãy đợi 1 phút để Auto-Sync cập nhật.`
        );
    }
}

function startLmWatcher(quotaProvider) {
    if (!vscode.lm) return;
    lmWatcherInterval = setInterval(async () => {
        try {
            const models = await vscode.lm.selectChatModels({});
            const isAvailable = models && models.length > 0;
            if (lmLastAvailable && !isAvailable) {
                lmLastAvailable = false;
                await notifyAutoRotate(quotaProvider);
            } else if (!lmLastAvailable && isAvailable) {
                lmLastAvailable = true;
                vscode.window.showInformationMessage(`✅ AI đã phản hồi trở lại cho ${currentEmail}.`);
            }
        } catch (_) {}
    }, 30000);
}

async function syncTokensToDat() {
    try {
        const data = loadData();
        const emails = await TokenManager.listEmails();
        let changed = false;
        for (const email of emails) {
            const stored = await TokenManager.get(email);
            if (stored && stored.accessToken) {
                if (!data[email]) data[email] = { addedAt: Date.now(), source: 'token-manager' };
                const curTok = data[email].tokens || {};
                if (curTok.access_token !== stored.accessToken || curTok.refresh_token !== stored.refreshToken) {
                    data[email].tokens = {
                        access_token: stored.accessToken,
                        refresh_token: stored.refreshToken || null,
                        expiry_ms: stored.expiresAt || (Date.now() + 3600000)
                    };
                    changed = true;
                }
            }
        }
        if (changed) saveData(data);
    } catch (e) {
        console.error('syncTokensToDat error:', e);
    }
}

// --- WebView Panel ---
function refreshPanel() {
    if (!quotaPanel) return;
    syncTokensToDat().then(() => {
        quotaPanel.webview.postMessage({
            type: 'update',
            data: loadData(),
            currentEmail,
            dataPath: dataFilePath
        });
    });
}

function getWebviewContent() {
    return `<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Quota Tracker</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: var(--vscode-font-family, 'Segoe UI', sans-serif);
    font-size: var(--vscode-font-size, 13px);
    background: var(--vscode-editor-background);
    color: var(--vscode-foreground);
    padding: 10px;
    display: flex; flex-direction: column; height: 100vh; overflow: hidden;
  }
  .header {
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 8px; padding-bottom: 8px;
    border-bottom: 1px solid var(--vscode-panel-border);
    flex-shrink: 0;
  }
  .header h2 { font-size: 14px; flex: 1; }
  .active-badge {
    background: #0984e3; color: white;
    padding: 2px 10px; border-radius: 10px; font-size: 11px;
    max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    display: flex; align-items: center; gap: 4px;
  }
  .active-badge.unknown { background: var(--vscode-badge-background); color: var(--vscode-badge-foreground); }
  .setup-banner {
    background: var(--vscode-inputValidation-warningBackground);
    border: 1px solid var(--vscode-inputValidation-warningBorder);
    border-radius: 4px; padding: 6px 10px; margin-bottom: 8px;
    font-size: 12px; display: flex; align-items: center; gap: 8px; flex-shrink: 0;
  }
  .actions-row {
    display: flex; gap: 5px; margin-bottom: 8px; flex-wrap: wrap; flex-shrink: 0;
  }
  .btn {
    padding: 4px 10px; border-radius: 4px; border: none;
    background: var(--vscode-button-background);
    color: var(--vscode-button-foreground);
    cursor: pointer; font-size: 11px; white-space: nowrap;
  }
  .btn:hover { opacity: 0.85; }
  .btn.danger { background: #c0392b; color: #fff; }
  .btn.secondary {
    background: var(--vscode-button-secondaryBackground);
    color: var(--vscode-button-secondaryForeground);
  }
  .btn.add { background: #0984e3; color: white; }
  .btn.ide-sync { background: #6c5ce7; color: white; }
  .toolbar {
    display: flex; gap: 6px; margin-bottom: 8px; align-items: center; flex-shrink: 0;
  }
  .search-input {
    flex: 1; min-width: 100px;
    padding: 4px 8px; border-radius: 4px;
    border: 1px solid var(--vscode-input-border);
    background: var(--vscode-input-background);
    color: var(--vscode-input-foreground); font-size: 12px;
  }
  .filter-btn {
    padding: 3px 8px; border-radius: 4px; border: 1px solid var(--vscode-button-border, transparent);
    background: var(--vscode-button-secondaryBackground);
    color: var(--vscode-button-secondaryForeground);
    cursor: pointer; font-size: 11px; white-space: nowrap;
  }
  .filter-btn.active { background: var(--vscode-button-background); color: var(--vscode-button-foreground); }
  .stats { display: flex; gap: 12px; margin-bottom: 8px; font-size: 11px; opacity: 0.7; flex-shrink: 0; }
  .table-wrap { flex: 1; overflow-y: auto; }
  table { width: 100%; border-collapse: collapse; }
  th {
    text-align: left; padding: 5px 6px; font-size: 11px;
    text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.6;
    border-bottom: 1px solid var(--vscode-panel-border);
    cursor: pointer; user-select: none; position: sticky; top: 0;
    background: var(--vscode-editor-background);
  }
  th:hover { opacity: 1; }
  td { padding: 5px 6px; border-bottom: 1px solid var(--vscode-panel-border, rgba(255,255,255,0.05)); }
  tr:hover td { background: var(--vscode-list-hoverBackground); cursor: pointer; }
  tr.current td { background: rgba(9,132,227,0.15); }
  tr.current td:first-child { border-left: 3px solid #0984e3; }
  .status-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 5px; vertical-align: middle; }
  .dot-ok { background: #27ae60; }
  .dot-ex { background: #e74c3c; animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
  .progress-wrap { display: flex; align-items: center; gap: 5px; }
  .progress-bar { height: 3px; border-radius: 2px; min-width: 30px; max-width: 70px; }
  .countdown { font-weight: 600; color: #e74c3c; font-size: 11px; }
  .time-text { font-size: 11px; opacity: 0.65; }
  .row-action {
    padding: 2px 6px; font-size: 10px; border-radius: 3px;
    border: 1px solid var(--vscode-button-border, transparent);
    background: var(--vscode-button-secondaryBackground);
    color: var(--vscode-button-secondaryForeground); cursor: pointer;
  }
  .row-switch {
    padding: 2px 6px; font-size: 10px; border-radius: 3px;
    border: none; background: #0984e3; color: white; cursor: pointer;
  }
  .row-switch:hover { opacity: 0.85; }
  .empty-state { text-align: center; padding: 30px 20px; opacity: 0.5; }
  .sync-msg { font-size: 11px; padding: 4px 8px; border-radius: 4px; margin-bottom: 6px; flex-shrink: 0; display: none; }
  .sync-msg.ok { background: rgba(39,174,96,0.15); color: #27ae60; border: 1px solid rgba(39,174,96,0.3); }
  .sync-msg.err { background: rgba(192,57,43,0.15); color: #e74c3c; border: 1px solid rgba(192,57,43,0.3); }
  .syncing { opacity: 0.6; pointer-events: none; }
  .group-badge { display:inline-block; padding: 2px 5px; margin: 0 2px; border-radius: 3px; font-size: 9px; background: rgba(39,174,96,0.2); color: #27ae60; border: 1px solid rgba(39,174,96,0.3); font-weight: bold; text-transform: uppercase; }
</style>
</head>
<body>

<div class="header">
  <div>🔋</div>
  <h2>Quota Tracker</h2>
  <div class="active-badge unknown" id="current-badge">
    <span>⚡</span><span id="badge-email">...</span>
  </div>
</div>

<div id="setup-banner" class="setup-banner" style="display:none">
  ⚠️ Chưa chọn file Data.
  <button class="btn" onclick="send('setPath')">Thiết lập ngay</button>
</div>

<div id="sync-msg" class="sync-msg"></div>

<div class="actions-row">
  <button class="btn add" id="btn-add" onclick="addAccount()">➕ Đăng nhập / Thêm</button>
  <button class="btn ide-sync" id="btn-sync" onclick="doSync()">🔄 Sync từ IDE</button>
  <button class="btn secondary" onclick="send('setPath')">📁 Data</button>
  <button class="btn secondary" id="btn-check-all" onclick="doCheckAll()">✓ Check All (Live)</button>
</div>

<div class="toolbar">
  <input class="search-input" type="text" id="search" placeholder="🔍 Tìm email..." oninput="renderTable()">
  <button class="filter-btn active" id="f-all" onclick="setFilter('all')">Tất cả</button>
  <button class="filter-btn" id="f-ok" onclick="setFilter('ok')">✅ OK</button>
  <button class="filter-btn" id="f-ex" onclick="setFilter('ex')">🔴 Hết</button>
</div>

<div class="stats" id="stats"></div>

<div class="table-wrap">
<table>
  <thead>
    <tr>
      <th onclick="toggleSort('email')">Email ↕</th>
      <th onclick="toggleSort('status')">Trạng thái ↕</th>
      <th>Còn lại</th>
      <th onclick="toggleSort('reset')" title="Sort theo thời gian hồi phục">Reset ↕</th>
      <th></th>
    </tr>
  </thead>
  <tbody id="table-body"></tbody>
</table>
<div id="empty-state" class="empty-state" style="display:none">Chưa có email nào. Hãy Sync từ IDE hoặc đăng nhập.</div>
</div>

<script>
const vscode = acquireVsCodeApi();
let allData = {};
let currentEmail = '';
let dataPath = '';
let filter = 'all';
let sortKey = 'status';
let sortAsc = false;
let isSyncing = false;

function send(command, payload) {
  vscode.postMessage({ command, ...(payload||{}) });
}

function showSyncMsg(text, type) {
  const el = document.getElementById('sync-msg');
  el.textContent = text;
  el.className = 'sync-msg ' + type;
  el.style.display = 'block';
  setTimeout(() => { el.style.display = 'none'; }, 5000);
}

function addAccount() {
  send('addAccount');
}

function doCheckAll() {
  var btn = document.getElementById('btn-check-all');
  if (btn) { btn.textContent = '⏳ Checking...'; btn.disabled = true; }
  send('checkAll');
}

function renderGroupPcts(info) {
  var gs = info.groupStatus;
  if (!gs || !Object.keys(gs).length) return '<span style="color:#27ae60">✅ OK (100%)</span>';
  var parts = Object.entries(gs).map(function(e) {
    var name = e[0], g = e[1];
    if (g.exhausted) return '<span style="color:#e74c3c;font-size:10px">' + (name[0].toUpperCase()+name.slice(1)) + ': 🔴</span>';
    var color = name === 'gemini' ? '#0984e3' : name === 'claude' ? '#6c5ce7' : '#00b894';
    return '<span style="color:' + color + ';font-size:10px;font-weight:600">' + (name[0].toUpperCase()+name.slice(1)) + ': ' + (g.percent || 0) + '%</span>';
  });
  return '<span style="color:#27ae60;font-size:10px">✅ </span>' + parts.join('<span style="opacity:0.4"> | </span>');
}

function doSync() {
  if (isSyncing) return;
  isSyncing = true;
  document.getElementById('btn-sync').textContent = '⏳ Đang sync...';
  document.getElementById('btn-sync').disabled = true;
  send('syncFromDB');
}

function setFilter(f) {
  filter = f;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('f-' + f).classList.add('active');
  renderTable();
}

function toggleSort(key) {
  if (sortKey === key) sortAsc = !sortAsc;
  else { sortKey = key; sortAsc = true; }
  renderTable();
}

function formatCountdown(exhaustedUntil) {
  if (!exhaustedUntil || exhaustedUntil <= Date.now()) return null;
  const ms = exhaustedUntil - Date.now();
  const d = Math.floor(ms / 86400000);
  const h = Math.floor((ms % 86400000) / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  if (d > 0) return d + 'd ' + h + 'h ' + m + 'm';
  return h + 'h ' + m + 'm';
}

function getProgress(exhaustedUntil) {
  if (!exhaustedUntil) return 0;
  const total = 7 * 24 * 3600000;
  const elapsed = total - (exhaustedUntil - Date.now());
  return Math.min(100, Math.max(0, (elapsed / total) * 100));
}

function renderTable() {
  const search = document.getElementById('search').value.toLowerCase();
  const now = Date.now();
  let entries = Object.entries(allData);

  entries = entries.filter(([email, info]) => {
    if (search && !email.toLowerCase().includes(search)) return false;
    const isEx = info.exhaustedUntil && info.exhaustedUntil > now;
    if (filter === 'ok') return !isEx;
    if (filter === 'ex') return isEx;
    return true;
  });

  entries.sort(([ea, ia], [eb, ib]) => {
    const now2 = Date.now();
    if (sortKey === 'email') {
      return sortAsc ? ea.localeCompare(eb) : eb.localeCompare(ea);
    }
    if (sortKey === 'reset') {
      // Sort theo thời gian hồi phục (sắp hồi phục nhất lên đầu khi asc)
      const aReset = ia.overallResetTime && ia.overallResetTime > now2 ? ia.overallResetTime : (ia.exhaustedUntil || 0);
      const bReset = ib.overallResetTime && ib.overallResetTime > now2 ? ib.overallResetTime : (ib.exhaustedUntil || 0);
      if (aReset === 0 && bReset === 0) return 0;
      if (aReset === 0) return sortAsc ? 1 : -1;
      if (bReset === 0) return sortAsc ? -1 : 1;
      return sortAsc ? aReset - bReset : bReset - aReset;
    }
    // default: sort by status (exhausted first)
    const aEx = (ia.exhaustedUntil > now2) ? 1 : 0;
    const bEx = (ib.exhaustedUntil > now2) ? 1 : 0;
    return sortAsc ? aEx - bEx : bEx - aEx;
  });

  const tbody = document.getElementById('table-body');
  const empty = document.getElementById('empty-state');

  if (entries.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = 'block';
    return;
  }
  empty.style.display = 'none';

  tbody.innerHTML = entries.map(([email, info]) => {
    const isEx = info.exhaustedUntil && info.exhaustedUntil > now;
    const effResetTime = isEx ? info.exhaustedUntil : (info.overallResetTime && info.overallResetTime > now ? info.overallResetTime : null);
    const countdown = effResetTime ? formatCountdown(effResetTime) : null;
    const resetStr = effResetTime ? new Date(effResetTime).toLocaleString('vi-VN', {day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}) : '—';
    const progress = effResetTime ? getProgress(effResetTime) : 100;
    const isCurrent = email === currentEmail;
    
    // Model OK Badges logic
    let availableStr = '';
    if (isEx && info.availableGroups && info.availableGroups.length > 0) {
        availableStr = '<br/>' + info.availableGroups.map(function(g) {
            return '<span class="group-badge" title="Còn dùng được">' + g + ' \u2713</span>';
        }).join('');
    }

    var trClass = isCurrent ? 'current' : '';
    var dotClass = isEx ? 'dot-ex' : 'dot-ok';
    var activeLabel = isCurrent ? ' <b style="color:#0984e3;font-size:10px">\u25b6 ACTIVE</b>' : '';
    var statusCell;
    if (info.lastError) {
        statusCell = '<span style="background:rgba(231,76,60,0.2);color:#e74c3c;padding:2px 6px;border-radius:3px;font-size:10px;border:1px solid rgba(231,76,60,0.4)" title="' + info.lastError + '">⚠️ ' + info.lastError + '</span>';
    } else if (isEx) {
        statusCell = '<span class="countdown">\ud83d\udd34 H\u1ebft quota</span>' + availableStr;
    } else {
        statusCell = renderGroupPcts(info);
    }
    var progressCell;
    if (countdown) {
        var barW = Math.max(30, 80 - (progress * 0.8));
        var barColor = isEx ? '#e74c3c' : '#0984e3';
        var cdColor = !isEx ? ' style="color:#0984e3"' : '';
        progressCell = '<div class="progress-wrap"><span class="countdown"' + cdColor + '>' + countdown + '</span>'
            + '<div class="progress-bar" style="width:' + barW + 'px;background:' + barColor + '"></div></div>';
    } else {
        progressCell = '<span style="opacity:0.4">\u2014</span>';
    }
    var switchBtn = !isCurrent
        ? '<button class="row-switch" data-email="' + email + '" onclick="event.stopPropagation();switchTo(this.dataset.email)">\u25b6 D\u00f9ng</button>'
        : '';
    var refreshBtn = isCurrent
        ? '<button class="row-action" style="margin-left:3px;color:#27ae60" data-email="' + email + '" onclick="event.stopPropagation();send(\\\'refreshOne\\\',{email:this.dataset.email})" title="L\u00e0m m\u1edbi Quota t\u1eeb IDE">\ud83d\udd04</button>'
        : '';
    var checkBtn = '<button class="row-action" style="margin-left:3px;color:#0984e3" data-email="' + email + '" onclick="event.stopPropagation();send(\\\'checkOne\\\',{email:this.dataset.email})" title="Check API (Live)">\ud83d\udd0d</button>';
    var deleteBtn = '<button class="row-action" style="margin-left:3px;color:#e74c3c" data-email="' + email + '" onclick="event.stopPropagation();send(\\\'deleteAccount\\\',{email:this.dataset.email})" title="X\u00f3a">\ud83d\uddd1\ufe0f</button>';

    // Badge no-token
    var hasToken = info.tokens && info.tokens.access_token;
    var noTokenBadge = !hasToken ? ' <span style="background:#e74c3c;color:#fff;font-size:9px;padding:1px 4px;border-radius:3px;vertical-align:middle" title="Cần đăng nhập để Check All">NO TOKEN</span>' : '';

    return '<tr class="' + trClass + '" data-email="' + email + '" onclick="switchTo(this.dataset.email)">'
        + '<td><span class="status-dot ' + dotClass + '"></span>' + email + activeLabel + noTokenBadge + '</td>'
        + '<td>' + statusCell + '</td>'
        + '<td>' + progressCell + '</td>'
        + '<td class="time-text">' + resetStr + '</td>'
        + '<td style="white-space:nowrap">' + switchBtn + refreshBtn + checkBtn + deleteBtn + '</td>'
        + '</tr>';
  }).join('');

  const total = Object.keys(allData).length;
  const exhausted = Object.values(allData).filter(i => i.exhaustedUntil > now).length;
  const ok = total - exhausted;
  document.getElementById('stats').innerHTML =
    \`<span>📊 Tổng: <b>\${total}</b></span>
     <span>✅ OK: <b>\${ok}</b></span>
     <span>🔴 Hết: <b>\${exhausted}</b></span>\`;

  const badge = document.getElementById('current-badge');
  const badgeEmail = document.getElementById('badge-email');
  if (currentEmail && currentEmail !== 'Unknown Account') {
    badge.className = 'active-badge';
    badgeEmail.textContent = currentEmail;
  } else {
    badge.className = 'active-badge unknown';
    badgeEmail.textContent = 'Chưa xác định';
  }
  document.getElementById('setup-banner').style.display = dataPath ? 'none' : 'flex';
}

function switchTo(email) {
  send('switchAccount', { email });
}

setInterval(renderTable, 30000);

window.addEventListener('message', e => {
  const msg = e.data;
  if (msg.type === 'update') {
    allData = msg.data || {};
    currentEmail = msg.currentEmail || '';
    dataPath = msg.dataPath || '';
    renderTable();
  }
  if (msg.type === 'syncResult') {
    isSyncing = false;
    const btn = document.getElementById('btn-sync');
    btn.textContent = '\uD83D\uDD04 Sync t\u1eeb IDE';
    btn.disabled = false;
    if (msg.status === 'ok') {
      showSyncMsg('\u2705 ' + msg.message, 'ok');
    } else {
      showSyncMsg('\u274C ' + msg.message, 'err');
    }
  }
  if (msg.type === 'checkResult') {
    var cBtn = document.getElementById('btn-check-all');
    if (cBtn) { cBtn.textContent = '\u2713 Check All'; cBtn.disabled = false; }
    if (msg.status === 'ok') {
      showSyncMsg('\u2705 ' + msg.message, 'ok');
    } else {
      showSyncMsg('\u274C ' + msg.message, 'err');
    }
  }
});
</script>
</body>
</html>`;
}

function showPanel(context, quotaProvider) {
    if (quotaPanel) {
        quotaPanel.reveal(vscode.ViewColumn.Beside);
        refreshPanel();
        return;
    }
    quotaPanel = vscode.window.createWebviewPanel(
        'quotaTracker',
        '🔋 Quota Tracker',
        vscode.ViewColumn.Beside,
        { enableScripts: true, retainContextWhenHidden: true }
    );
    quotaPanel.webview.html = getWebviewContent();

    quotaPanel.webview.onDidReceiveMessage(async msg => {
        switch (msg.command) {
            case 'setPath':
                await setDataPath(quotaProvider);
                break;
            case 'refresh':
                quotaProvider.refresh();
                updateStatusBar();
                refreshPanel();
                break;
            case 'deleteAccount':
                if (!msg.email) break;
                const confirm = await vscode.window.showWarningMessage(
                    `Bạn có chắc muốn xóa ${msg.email} khỏi danh sách Quota?`, 'Xóa', 'Huỷ'
                );
                if (confirm === 'Xóa') {
                    const data = loadData();
                    delete data[msg.email];
                    saveData(data);
                    quotaProvider.refresh();
                    updateStatusBar();
                    refreshPanel();
                }
                break;
            case 'refreshOne':
                if (msg.email !== currentEmail) {
                    vscode.window.showWarningMessage('Chỉ có thể làm mới cho tài khoản đang ACTIVE. Vui lòng bấm [▶ Dùng] trước.');
                    return;
                }
                const p = quotaPanel;
                vscode.window.showInformationMessage(`Đang lấy dữ liệu mới nhất từ server cho ${msg.email}...`);
                try {
                    await vscode.commands.executeCommand('antigravity-account.refreshBalances');
                    autoSyncFromDB(quotaProvider, (res) => {
                        if (res.status === 'ok') {
                            vscode.window.showInformationMessage(`✅ Đã làm mới xong Quota cho ${msg.email}`);
                        }
                        p?.webview.postMessage({ type: 'syncResult', status: res.status, message: res.message });
                    });
                } catch (e) {
                    vscode.window.showErrorMessage('Lỗi khi làm mới: ' + e.message);
                }
                break;
            case 'checkOne':
                if (!msg.email) break;
                try {
                    const { AuthService: AuthServiceOne } = require('./oauth.js');
                    const dataOne = loadData();
                    let tokenOne = await TokenManager.ensureValid(msg.email);

                    // Fallback: lấy từ VS Code auth sessions nếu chưa có trong TokenManager
                    if (!tokenOne) {
                        try {
                            const sessions = await vscode.authentication.getSessions('google', [
                                'https://www.googleapis.com/auth/cloud-platform',
                                'https://www.googleapis.com/auth/userinfo.email'
                            ], { createIfNone: false });
                            const sess = sessions.find(s => s.account?.label === msg.email);
                            if (sess && sess.accessToken) {
                                tokenOne = sess.accessToken;
                                await TokenManager.store(msg.email, sess.accessToken, null, Date.now() + 3500 * 1000);
                                await TokenManager.addEmail(msg.email);
                            }
                        } catch (_) {}
                    }

                    if (!tokenOne) {
                        if (!dataOne[msg.email]) dataOne[msg.email] = { addedAt: Date.now() };
                        dataOne[msg.email].lastError = 'Không có token (cần ➕ Đăng nhập)';
                        saveData(dataOne);
                        refreshPanel();
                        quotaPanel?.webview.postMessage({ type: 'checkResult', status: 'error', message: `❌ ${msg.email}: Không có token. Vui lòng bấm ➕ Đăng nhập.` });
                        break;
                    }

                    vscode.window.showInformationMessage(`⏳ Đang check Quota cho ${msg.email}...`);
                    const balancesOne = await AuthServiceOne.fetchBalances(tokenOne);
                    if (Object.keys(balancesOne).length > 0) {
                        if (!dataOne[msg.email]) dataOne[msg.email] = { addedAt: Date.now(), source: 'check-one' };
                        dataOne[msg.email].balances = balancesOne;
                        dataOne[msg.email].lastChecked = Date.now();
                        delete dataOne[msg.email].lastError; // Xoá lỗi cũ nếu check thành công
                        const gsOne = computeGroupStatus(balancesOne);
                        if (gsOne) {
                            dataOne[msg.email].groupStatus = gsOne.groupStatus;
                            dataOne[msg.email].exhaustedUntil = gsOne.exhaustedUntil;
                            dataOne[msg.email].overallResetTime = gsOne.overallResetTime;
                            dataOne[msg.email].availableGroups = gsOne.availableGroups;
                            dataOne[msg.email].exhaustedGroups = gsOne.exhaustedGroups;
                        }
                        // Cập nhật token mới vào .dat
                        const stored = await TokenManager.get(msg.email);
                        if (stored) {
                            dataOne[msg.email].tokens = {
                                access_token: stored.accessToken,
                                refresh_token: stored.refreshToken || null,
                                expiry_ms: stored.expiresAt || (Date.now() + 3600000)
                            };
                        }
                        saveData(dataOne);
                        refreshPanel();
                        vscode.window.showInformationMessage(`✅ Đã check thành công cho ${msg.email}`);
                        quotaPanel?.webview.postMessage({ type: 'checkResult', status: 'ok', message: `✅ Đã check xong ${msg.email}` });
                    } else {
                        if (!dataOne[msg.email]) dataOne[msg.email] = { addedAt: Date.now() };
                        dataOne[msg.email].lastError = 'Lỗi API (Token hết hạn hoặc server lỗi)';
                        saveData(dataOne);
                        refreshPanel();
                        quotaPanel?.webview.postMessage({ type: 'checkResult', status: 'error', message: `❌ Không lấy được balance cho ${msg.email}.` });
                    }
                } catch (e) {
                    vscode.window.showErrorMessage(`Lỗi check ${msg.email}: ` + e.message);
                    quotaPanel?.webview.postMessage({ type: 'checkResult', status: 'error', message: e.message });
                }
                break;
            case 'checkAll':
                try {
                    vscode.window.showInformationMessage('⏳ Đang check toàn bộ Quota...');
                    quotaPanel?.webview.postMessage({ type: 'syncResult', status: 'info', message: '⏳ Đang lấy token và check API cho từng tài khoản...' });

                    const { AuthService } = require('./oauth.js');
                    const data = loadData();
                    let updated = 0, failed = 0;

                    // Bước 1: Tập hợp toàn bộ email cần check
                    // Nguồn 1: Token store của chính mình (thêm qua OAuth hoặc tay)
                    const ownEmails = await TokenManager.listEmails();

                    // Nguồn 2: Email đã có trong .dat file
                    const datEmails = Object.keys(data);

                    // Nguồn 3: VS Code auth session (chỉ lấy active account - không phụ thuộc ext khác)
                    const sessionEmails = [];
                    try {
                        const sessions = await vscode.authentication.getSessions('google', [
                            'https://www.googleapis.com/auth/cloud-platform',
                            'https://www.googleapis.com/auth/userinfo.email'
                        ], { createIfNone: false });
                        for (const s of sessions) {
                            const email = s.account?.label;
                            if (email && s.accessToken) {
                                // Lưu token này vào store của mình luôn
                                await TokenManager.store(email, s.accessToken, null, Date.now() + 3500 * 1000);
                                await TokenManager.addEmail(email);
                                sessionEmails.push(email);
                            }
                        }
                    } catch (_) {}

                    // Gộp tất cả, loại trùng
                    const allEmails = [...new Set([...ownEmails, ...sessionEmails, ...datEmails])];

                    if (allEmails.length === 0) {
                        quotaPanel?.webview.postMessage({ type: 'checkResult', status: 'error', message: '❌ Không có tài khoản nào. Hãy thêm tài khoản trước (nút ➕ Đăng nhập).' });
                        break;
                    }

                    // Bước 2: Check từng email
                    const noTokenEmails = [];
                    for (let i = 0; i < allEmails.length; i++) {
                        const email = allEmails[i];
                        quotaPanel?.webview.postMessage({ type: 'syncResult', status: 'info', message: `⏳ [${i+1}/${allEmails.length}] Đang check ${email}...` });

                        try {
                            let accessToken = await TokenManager.ensureValid(email);
                            if (!accessToken) {
                                // Không có token → hiển thị rõ ràng, không check
                                noTokenEmails.push(email);
                                if (!data[email]) data[email] = { addedAt: Date.now() };
                                data[email].lastError = 'Không có token (cần ➕ Đăng nhập)';
                                quotaPanel?.webview.postMessage({ type: 'syncResult', status: 'warn', message: `⚠️ [${i+1}/${allEmails.length}] ${email} — Không có token, cần đăng nhập lại (nút ➕)` });
                                failed++;
                                continue;
                            }

                            const balances = await AuthService.fetchBalances(accessToken);

                            if (Object.keys(balances).length > 0) {
                                if (!data[email]) data[email] = { addedAt: Date.now(), source: 'check-all' };
                                data[email].balances = balances;
                                data[email].lastChecked = Date.now();
                                delete data[email].lastError; // Xoá lỗi cũ nếu check thành công
                                const gs = computeGroupStatus(balances);
                                if (gs) {
                                    data[email].groupStatus = gs.groupStatus;
                                    data[email].exhaustedUntil = gs.exhaustedUntil;
                                    data[email].overallResetTime = gs.overallResetTime;
                                    data[email].availableGroups = gs.availableGroups;
                                    data[email].exhaustedGroups = gs.exhaustedGroups;
                                }
                                // === CẬP NHẬT TOKEN MỚI NHẤT VÀO .dat (Cross-Machine portability) ===
                                const stored = await TokenManager.get(email);
                                if (stored) {
                                    data[email].tokens = {
                                        access_token: stored.accessToken,
                                        refresh_token: stored.refreshToken || null,
                                        expiry_ms: stored.expiresAt || (Date.now() + 3600000)
                                    };
                                }
                                updated++;
                            } else {
                                if (!data[email]) data[email] = { addedAt: Date.now() };
                                data[email].lastError = 'Lỗi API Quota (Token hết hạn)';
                                failed++;
                            }
                        } catch (fetchErr) {
                            console.error(`checkAll lỗi cho ${email}:`, fetchErr.message);
                            if (!data[email]) data[email] = { addedAt: Date.now() };
                            data[email].lastError = fetchErr.message || 'Lỗi kết nối';
                            failed++;
                        }
                    }

                    // Bước 3: Lưu và hiển thị kết quả ngay lập tức
                    saveData(data);
                    quotaProvider.refresh();
                    refreshPanel();

                    // Bước 4: Chạy Python sync để cập nhật groupStatus từ DB
                    autoSyncFromDB(quotaProvider, (res) => {
                        const finalData = loadData();
                        const total = Object.keys(finalData).length;
                        const exhausted = Object.values(finalData).filter(i => i.exhaustedUntil && i.exhaustedUntil > Date.now()).length;
                        let msg = `✅ Check xong! ${updated} tài khoản cập nhật`;
                        if (noTokenEmails.length > 0) {
                            msg += ` | ⚠️ ${noTokenEmails.length} cần đăng nhập: ${noTokenEmails.map(e => e.split('@')[0]).join(', ')}`;
                        }
                        msg += ` | Tổng: ${total} (${exhausted} hết quota, ${total - exhausted} OK)`;
                        quotaPanel?.webview.postMessage({ type: 'checkResult', status: 'ok', message: msg });
                        refreshPanel();
                    });

                } catch (e) {
                    vscode.window.showErrorMessage('Lỗi khi checkAll: ' + e.message);
                    quotaPanel?.webview.postMessage({ type: 'checkResult', status: 'error', message: e.message });
                }
                break;
            case 'syncFromDB':
                autoSyncFromDB(quotaProvider, (res) => {
                    quotaPanel?.webview.postMessage({ type: 'syncResult', status: res.status, message: res.message });
                });
                break;
            case 'addAccount':
                try {
                    // Primary: dùng Local OAuth của chính mình (tự chủ, không phụ thuộc Antigravity Account)
                    const { AuthService } = require('./oauth.js');
                    vscode.window.showInformationMessage('Đang mở trình duyệt để đăng nhập Google...');
                    const { tokens, profile } = await AuthService.login();

                    vscode.window.showInformationMessage(`✅ Đăng nhập thành công! Đang cập nhật trạng thái Quota cho ${profile.email}...`);
                    const balances = await AuthService.fetchBalances(tokens.access_token);

                    const email = profile.email;
                    const data = loadData();
                    if (!data[email]) data[email] = { addedAt: Date.now(), source: 'local-oauth' };
                    data[email].balances = balances || {};
                    data[email].lastChecked = Date.now();
                    delete data[email].lastError; // Xoá bỏ thẻ lỗi/NO TOKEN ngay lập tức khi đăng nhập thành công
                    const gsNew = computeGroupStatus(balances || {});
                    if (gsNew) {
                        data[email].groupStatus = gsNew.groupStatus;
                        data[email].exhaustedUntil = gsNew.exhaustedUntil;
                        data[email].overallResetTime = gsNew.overallResetTime;
                        data[email].availableGroups = gsNew.availableGroups;
                        data[email].exhaustedGroups = gsNew.exhaustedGroups;
                    }

                    // === LƯU TOKEN VÀO .dat ĐỂ PORTABLE CROSS-MACHINE ===
                    const expiresAt = tokens.expires_in ? Date.now() + tokens.expires_in * 1000 : Date.now() + 3600000;
                    data[email].tokens = {
                        access_token: tokens.access_token,
                        refresh_token: tokens.refresh_token || null,
                        expiry_ms: expiresAt
                    };
                    saveData(data);

                    // Lưu token vào TokenManager (context.secrets) — tự chủ hoàn toàn
                    await TokenManager.store(email, tokens.access_token, tokens.refresh_token, expiresAt);
                    await TokenManager.addEmail(email);

                    // Cập nhật giao diện lập tức
                    quotaProvider.refresh();
                    refreshPanel();

                    // Tự động chạy Python sync để hợp nhất dữ liệu IDE DB và Live API ngay cho email này
                    autoSyncFromDB(quotaProvider, (res) => {
                        const refreshedData = loadData();
                        if (refreshedData[email]) delete refreshedData[email].lastError;
                        saveData(refreshedData);
                        refreshPanel();
                        quotaPanel?.webview.postMessage({ type: 'syncResult', status: 'ok', message: `✅ Đã đăng nhập & tự động cập nhật trạng thái cho ${email}` });
                    }, email);
                } catch (e) {
                    vscode.window.showErrorMessage('Lỗi đăng nhập OAuth: ' + e.message);
                }
                break;
            case 'switchAccount':
                if (!msg.email) break;
                try {
                    const targetEmail = msg.email;

                    // === Ghi trực tiếp vào state.vscdb qua Python script ===
                    // Cách này can thiệp đúng vào DB mà Antigravity Account đọc,
                    // thay vì ghi vào globalState của chính Quota Tracker (sai context)
                    const switchScript = findScriptPath('switch_account.py');
                    if (!switchScript) {
                        vscode.window.showErrorMessage('Không tìm thấy switch_account.py. Hãy kiểm tra thư mục QuotaApp.');
                        break;
                    }

                    const switchResult = await new Promise((resolve) => {
                        cp.execFile('python', [switchScript, targetEmail], { timeout: 10000, encoding: 'utf-8' }, (err, stdout) => {
                            try { resolve(JSON.parse(stdout.trim())); } catch (_) { resolve({ success: false, message: err?.message || stdout }); }
                        });
                    });

                    if (!switchResult.success) {
                        // Fallback: dùng lệnh switchAccount của Antigravity Account extension
                        try {
                            await vscode.commands.executeCommand('antigravity-account.switchAccount');
                            vscode.window.showInformationMessage(`⚠️ Python script lỗi (${switchResult.message}). Đã mở hộp chọn tài khoản của IDE.`);
                        } catch (_) {
                            vscode.window.showErrorMessage(`Lỗi chuyển tài khoản: ${switchResult.message}`);
                        }
                        break;
                    }

                    // Cập nhật UI ngay lập tức
                    currentEmail = targetEmail;
                    if (dataFilePath) {
                        const activeFile = path.join(path.dirname(dataFilePath), 'active_account.txt');
                        try { fs.writeFileSync(activeFile, currentEmail, 'utf-8'); } catch (_) {}
                    }
                    updateStatusBar();
                    refreshPanel();

                    vscode.window.showInformationMessage(`✅ Đã chuyển sang ${targetEmail}. Hãy bấm Reload Window (Ctrl+Shift+P → Reload Window) để IDE nhận tài khoản mới.`);
                } catch (e) {
                    vscode.window.showErrorMessage('Lỗi khi chuyển tài khoản: ' + e.message);
                }
                break;
        }
    }, undefined, context.subscriptions);

    quotaPanel.onDidDispose(() => { quotaPanel = null; }, null, context.subscriptions);
    setTimeout(() => refreshPanel(), 200);
}

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('Quota Antigravity Ext activated!');
    _ctx = context; // Khởi tạo TokenManager context

    dataFilePath = context.globalState.get('quotaDataPath', '');
    
    // Migrate to .dat encoded file if .json is found
    if (dataFilePath && dataFilePath.endsWith('.json')) {
        const oldPath = dataFilePath;
        dataFilePath = dataFilePath.replace('.json', '.dat');
        context.globalState.update('quotaDataPath', dataFilePath);
        
        // Convert old JSON to new DAT format
        if (fs.existsSync(oldPath) && !fs.existsSync(dataFilePath)) {
            try {
                const oldContent = fs.readFileSync(oldPath, 'utf-8');
                const oldData = JSON.parse(oldContent);
                saveData(oldData);
            } catch(e) {
                console.error('Migration error:', e);
            }
        }
    }
    
    setDataPath._ctx = context;

    // === AUTO-IMPORT TOKENS TỪ .dat VÀO TokenManager (Cross-Machine) ===
    // Khi copy .dat từ Machine A sang Machine B, tokens được bảo tồn trong .dat.
    // Startup: tự động import vào TokenManager để Check All hoạt động ngay.
    (async () => {
        try {
            const dat = loadData();
            const existingEmails = await TokenManager.listEmails();
            let imported = 0;
            for (const [email, entry] of Object.entries(dat)) {
                if (!entry || !entry.tokens) continue;
                const { access_token, refresh_token, expiry_ms } = entry.tokens;
                if (!access_token) continue;
                // Chỉ import nếu chưa có trong TokenManager (tránh ghi đè token mới hơn)
                if (!existingEmails.includes(email)) {
                    await TokenManager.store(email, access_token, refresh_token || null, expiry_ms || (Date.now() + 3600000));
                    await TokenManager.addEmail(email);
                    imported++;
                }
            }
            if (imported > 0) {
                console.log(`[QuotaTracker] Auto-imported ${imported} tokens from .dat into TokenManager.`);
            }
        } catch (e) {
            console.error('[QuotaTracker] Auto-import tokens from .dat failed:', e.message);
        }
    })();

    // 1. Status Bar
    myStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    myStatusBarItem.command = 'quotaTracker.showPanel';
    context.subscriptions.push(myStatusBarItem);

    updateActiveAccount();
    context.subscriptions.push(
        vscode.authentication.onDidChangeSessions(e => {
            if (e.provider.id === 'google') updateActiveAccount();
        })
    );

    // 2. TreeView sidebar
    const quotaProvider = new QuotaProvider();
    vscode.window.registerTreeDataProvider('quotaTrackerView', quotaProvider);

    // 3. Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('quotaTracker.showPanel', () => showPanel(context, quotaProvider)),
        vscode.commands.registerCommand('quotaTracker.showMenu', () => showPanel(context, quotaProvider)),
        vscode.commands.registerCommand('quotaTracker.setDataPath', () => setDataPath(quotaProvider)),
        vscode.commands.registerCommand('quotaTracker.refresh', () => {
            quotaProvider.refresh();
            updateActiveAccount();
            refreshPanel();
        })
    );

    // 4. vscode.lm watcher
    startLmWatcher(quotaProvider);

    // 5. UI refresh every 60s
    setInterval(() => {
        quotaProvider.refresh();
        updateStatusBar();
        refreshPanel();
    }, 60000);

    // 6. Background Auto-Sync từ DB mỗi 5 phút
    setInterval(() => {
        autoSyncFromDB(quotaProvider, (res) => {
            if (res.status === 'ok') {
                updateStatusBar();
                refreshPanel();
            }
        });
    }, 5 * 60 * 1000);
}

function deactivate() {
    if (lmWatcherInterval) clearInterval(lmWatcherInterval);
}

module.exports = { activate, deactivate };
