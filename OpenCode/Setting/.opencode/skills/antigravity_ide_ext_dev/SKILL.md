---
name: "antigravity-ide-extension-dev"
description: "Use this skill for building, installing, or maintaining VSCode-based extensions for Antigravity IDE. Covers: correct folder naming convention (publisher.name-version), extensions.json cache corruption (undefined_publisher ID bug), package.json required fields (publisher, activationEvents), WebView panel development, keybindings registration, vscode.lm API for AI model availability polling, vscode.authentication.getSession for Google account detection, TreeDataProvider for sidebar views, StatusBarItem with dynamic background color, and extension not appearing in Extensions panel after manual folder copy. Trigger on: extension not showing in installed list, undefined_publisher in extensions.json, extension loads but command not found, Alt+Q or keybinding not working, WebView panel not receiving messages, vscode.lm not available, StatusBar not updating, or needing to package/install a local extension without marketplace."
---

# Hướng dẫn phát triển Extension cho Antigravity IDE

Áp dụng quy tắc làm việc chung từ `AI_RULES.md` / `AGENTS.md` khi chúng có trong workspace. Skill này chỉ bổ sung kiến thức kỹ thuật riêng cho Antigravity IDE.

Skill này ghi lại kiến thức từ dự án **QuotaAntigravity Tracker** — một VSCode Extension chạy trong Antigravity IDE. Áp dụng cho mọi extension local (không qua marketplace) cần cài thủ công vào Antigravity IDE.

---

## 1. Kiến trúc Extension (VSCode Manifest V3-like)

| File | Vai trò |
|---|---|
| `package.json` | Khai báo metadata, commands, keybindings, views, activationEvents |
| `extension.js` | Entry point — hàm `activate(context)` và `deactivate()` |
| `media/icon.svg` | Icon cho Activity Bar (bắt buộc nếu khai báo `viewsContainers`) |
| `README.md` | Bắt buộc nếu dùng `vsce package` để đóng gói VSIX |

---

## 2. ⚠️ QUY TẮC BẮT BUỘC — Cài Extension Thủ Công

### Tên thư mục phải đúng format:
```
<publisher>.<name>-<version>
```
Ví dụ: `antigravity.quota-antigravity-ext-1.0.0`

**Hậu quả nếu sai format:** IDE ghi ID là `undefined_publisher.<name>` vào `extensions.json`, extension không load dù file tồn tại.

### `package.json` bắt buộc có trường `publisher`:
```json
{
  "name": "my-ext",
  "publisher": "antigravity",
  "version": "1.0.0",
  "engines": { "vscode": "^1.74.0" },
  "activationEvents": ["onStartupFinished"],
  "main": "./extension.js"
}
```

**Không có `publisher`** → IDE gán `undefined_publisher` → extension bị bỏ qua.

---

## 3. ⚠️ LỖI extensions.json Cache

File `C:\Users\<user>\.antigravity-ide\extensions\extensions.json` là cache IDE dùng để track extension đã cài.

### Triệu chứng:
- Extension không hiện trong danh sách Installed dù folder đã có
- ID trong extensions.json là `undefined_publisher.xxx`

### Fix:
1. **Xóa hoặc đổi tên** `extensions.json` để IDE quét lại:
   ```powershell
   mv extensions.json extensions.json.bak
   ```
2. **Tắt hẳn IDE** (không dùng Reload Window) → Mở lại
3. IDE tự tạo lại `extensions.json` mới với metadata đúng

### Cấu trúc `extensions.json` đúng chuẩn:
```json
[{
  "identifier": { "id": "antigravity.quota-antigravity-ext" },
  "version": "1.0.0",
  "location": {
    "$mid": 1,
    "fsPath": "c:\\Users\\...\\extensions\\antigravity.quota-antigravity-ext-1.0.0",
    "_sep": 1,
    "path": "/c:/Users/.../extensions/antigravity.quota-antigravity-ext-1.0.0",
    "scheme": "file"
  },
  "relativeLocation": "antigravity.quota-antigravity-ext-1.0.0",
  "metadata": {
    "isApplicationScoped": false,
    "isMachineScoped": false,
    "isBuiltin": false,
    "installedTimestamp": 1753757000000,
    "targetPlatform": "universal",
    "private": true
  }
}]
```

**Thiếu `metadata`** → IDE coi extension là "chưa cài đúng" và không load.

---

## 4. Log Files của Antigravity IDE

```
C:\Users\<user>\AppData\Roaming\Antigravity IDE\logs\<session>\window1\exthost\
  google.antigravity\Antigravity IDE.log     ← Log chính (server, auth, API calls)
  google.antigravity\Antigravity Crash Logs.log
  exthost.log                                 ← Extension host errors
  output_logging_*\                           ← Output channels per extension
```

**Quan trọng:**
- Log ghi URL API calls (`https://daily-cloudcode-pa.googleapis.com/...`) nhưng **không ghi response body**
- Lỗi quota (`429 Resource Exhausted`) **không** xuất hiện trong log → không thể watch file để auto-detect
- Để detect quota, phải dùng `vscode.lm.selectChatModels()` và poll định kỳ

---

## 5. Phát hiện Email Đăng Nhập

```javascript
async function getGoogleEmail() {
    try {
        const session = await vscode.authentication.getSession(
            'google', [], { createIfNone: false }
        );
        return session?.account?.label || null;
    } catch (_) {
        return null;
    }
}

// Lắng nghe thay đổi đăng nhập
context.subscriptions.push(
    vscode.authentication.onDidChangeSessions(e => {
        if (e.provider.id === 'google') getGoogleEmail().then(updateUI);
    })
);
```

**Giới hạn:** Chỉ detect được nếu user đăng nhập Google chính thức qua IDE. Tài khoản đăng nhập qua cách khác sẽ trả về `null`.

---

## 6. vscode.lm API — Poll AI Model Availability

```javascript
function startLmWatcher(onQuotaDetected) {
    if (!vscode.lm) return; // API không có ở IDE cũ (< 1.90)
    
    let lastAvailable = true;
    setInterval(async () => {
        try {
            const models = await vscode.lm.selectChatModels({});
            const isAvailable = models && models.length > 0;
            if (lastAvailable && !isAvailable) {
                lastAvailable = false;
                onQuotaDetected(); // Gọi callback
            } else if (!lastAvailable && isAvailable) {
                lastAvailable = true;
                // Models khôi phục
            }
        } catch (_) {}
    }, 30000);
}
```

**Lưu ý:** Đây là heuristic — models có thể biến mất vì lý do khác (network, server). Luôn hỏi xác nhận user trước khi auto-mark.

---

## 7. WebView Panel

```javascript
function showPanel(context) {
    const panel = vscode.window.createWebviewPanel(
        'myPanel',          // viewType (unique ID)
        'Panel Title',      // Tab title
        vscode.ViewColumn.Beside,
        {
            enableScripts: true,
            retainContextWhenHidden: true  // Giữ state khi panel bị ẩn
        }
    );
    panel.webview.html = getHtml();

    // Extension → WebView
    panel.webview.postMessage({ type: 'update', data: myData });

    // WebView → Extension
    panel.webview.onDidReceiveMessage(msg => {
        if (msg.command === 'doSomething') { /* ... */ }
    }, undefined, context.subscriptions);

    panel.onDidDispose(() => { /* cleanup */ });
}
```

**Trong HTML của WebView:**
```javascript
const vscode = acquireVsCodeApi();
// Gửi message lên Extension:
vscode.postMessage({ command: 'doSomething', payload: '...' });
// Nhận message từ Extension:
window.addEventListener('message', e => {
    const msg = e.data; // { type: 'update', data: ... }
});
```

**Lưu ý CSP:** WebView mặc định chặn `eval()` và external resources. Dùng `nonce` nếu cần inline script phức tạp.

---

## 8. Keybindings

Trong `package.json`:
```json
{
  "contributes": {
    "keybindings": [
      {
        "command": "myExt.doAction",
        "key": "alt+q",
        "mac": "alt+q",
        "when": "editorFocus || !editorFocus"
      }
    ]
  }
}
```

**Lưu ý:** `"when": "editorFocus || !editorFocus"` = luôn active (mọi ngữ cảnh). Bỏ `when` nếu chỉ muốn active khi editor focus.

---

## 9. StatusBar với màu động

```javascript
const item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
item.command = 'myExt.openPanel';

// Bình thường
item.text = '$(account) user@gmail.com | OK';
item.backgroundColor = undefined;

// Cảnh báo (màu vàng/cam)
item.text = '$(error) user@gmail.com — Còn 5h 10m';
item.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');

item.show();
context.subscriptions.push(item);
```

---

## 10. Pattern TreeDataProvider (Sidebar View)

```javascript
class MyProvider {
    constructor() {
        this._onChange = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onChange.event;
    }
    refresh() { this._onChange.fire(); }
    getTreeItem(el) { return el; }
    getChildren() {
        const items = [/* your data */].map(d => {
            const item = new vscode.TreeItem(d.label, vscode.TreeItemCollapsibleState.None);
            item.description = d.desc;
            item.iconPath = new vscode.ThemeIcon('check'); // hoặc 'error', 'warning'...
            return item;
        });
        return Promise.resolve(items);
    }
}
// Đăng ký:
vscode.window.registerTreeDataProvider('myViewId', new MyProvider());
```

---

## 11. Checklist trước khi cài Extension thủ công

- [ ] `publisher` field có trong `package.json`
- [ ] Tên thư mục = `<publisher>.<name>-<version>`
- [ ] `media/icon.svg` tồn tại nếu dùng `viewsContainers`
- [ ] Xóa `extensions.json` cũ nếu có ID rác `undefined_publisher`
- [ ] **Tắt hẳn IDE và mở lại** (không chỉ Reload Window) để IDE quét lại cache

---

## 12. Pattern: Đọc Dữ Liệu globalState Từ Extension Khác Bằng SQLite

Các extension lưu globalState vào file SQLite state.vscdb của VS Code.
Nếu bạn cần tự động hóa hoặc "học" (sync) dữ liệu từ một extension khác (ví dụ: davissss2.antigravity-account) mà không thông qua API:

### Hạn chế:
File state.vscdb luôn bị **lock** (khóa) bởi tiến trình của IDE.

### Giải pháp (Dùng Python script làm cầu nối):
1. Copy file state.vscdb (từ thư mục globalStorage của User hoặc Profile) ra thư mục Temp.
2. Dùng thư viện sqlite3 truy vấn bảng ItemTable với key là tên của extension.
3. Giá trị trả về là 1 chuỗi JSON chứa toàn bộ state của extension đó.
4. Kỹ thuật này cho phép các máy tính/AI khác dễ dàng đọc được state cấu hình của IDE từ bên ngoài.

**Ví dụ Code (Python):**
`python
import sqlite3, json, os, shutil

db_path = r'C:\Users\<user>\AppData\Roaming\Antigravity IDE\User\globalStorage\state.vscdb'
temp_db = os.path.join(os.environ['TEMP'], 'temp_state.vscdb')

# 1. Copy để tránh lỗi File Locked
shutil.copy2(db_path, temp_db)

# 2. Query data
conn = sqlite3.connect(temp_db)
c = conn.cursor()
c.execute("SELECT value FROM ItemTable WHERE key = 'Davissss2.antigravity-account'")
row = c.fetchone()
if row:
    state_json = json.loads(row[0])
    print(state_json)
conn.close()
`

---

## 13. So sánh QuotaTracker vs Antigravity Account — Gap Analysis

Phân tích từ đọc source thực tế `davissss2.antigravity-account-0.2.4-universal/dist/extension.js`.

### 13.1 Antigravity Account có, QuotaTracker CHƯA có

| Tính năng | Antigravity Account | QuotaTracker | Ưu tiên |
|---|---|---|---|
| **Card layout + Avatar** | Avatar tròn, gradient border khi active, animation pulse | Table rows đơn giản | Thẩm mỹ |
| **Glassmorphism CSS** | Premium gradient, toast notification, cardRefreshPulse | VS Code native colors | Medium |
| **Xóa tài khoản** | `deleteAccount` command | Chưa có | **High** |
| **Refresh từng account** | Nút refresh riêng trên mỗi card | Chỉ refresh tất cả | Medium |
| **Auto-Rotate** | Tự switch account khi hết quota | Không có | **High** |
| **Low Credit Notifications** | Native OS notification khi balance thấp | Chỉ cảnh báo trong IDE | Medium |
| **Auto-Refresh interval** | Tự động refresh balance theo N phút | Chỉ manual | Medium |
| **Settings Tab** | Tab riêng cấu hình toggles, intervals | Không có | Medium |
| **Status chi tiết** | `token_expired`, `ineligible`, `depleted` | Chỉ OK/Exhausted | Medium |
| **Sort nhiều tiêu chí** | date-added, quota, quota-regen, name | Chỉ email/status | Low |
| **Custom OAuth Client ID** | User tự cấu hình để tránh expire 7 ngày | Không liên quan | Medium |
| **Đa ngôn ngữ i18n** | EN / AR / ES | Chỉ tiếng Việt | Low |

### 13.2 QuotaTracker làm tốt hơn hoặc khác biệt

| Tính năng | QuotaTracker | Antigravity Account |
|---|---|---|
| **Đồng hồ đếm ngược** | Hiển thị còn bao nhiêu giờ:phút | Chỉ show "Depleted" |
| **Reset timestamp** | "Reset lúc DD/MM HH:MM" | Không rõ |
| **Alt+Q hotkey** | Đánh dấu hết quota tức thì | Không có hotkey tương tự |
| **Python App đồng bộ** | GUI Tkinter đọc cùng file data | Chỉ trong IDE |
| **Auto-sync từ SQLite DB** | Đọc DB ngay trong extension | Tự quản lý data |
| **Filter OK/Hết** | Lọc nhanh theo trạng thái | Không có filter |

### 13.3 Tính năng nên thêm vào QuotaTracker (theo độ ưu tiên)

```
[HIGH]   1. Xóa account: nút 🗑️ trên mỗi dòng, xóa khỏi quota_data.json
[HIGH]   2. Auto-Rotate: khi active account hết → notify để switch sang account OK
[MEDIUM] 3. Auto-Sync định kỳ (background setInterval mỗi 5 phút gọi Python sync)
[MEDIUM] 4. Status: phân biệt token_expired / ineligible từ DB
[MEDIUM] 5. Settings Tab trong WebView: cấu hình interval, ngưỡng cảnh báo
[LOW]    6. Nâng cấp CSS: Card layout với initials avatar thay table rows
```

### 13.4 Pattern: Xóa Account

```javascript
// onDidReceiveMessage:
case 'deleteAccount':
    const confirm = await vscode.window.showWarningMessage(
        `Xóa ${msg.email} khỏi danh sách Quota?`, 'Xóa', 'Huỷ'
    );
    if (confirm === 'Xóa') {
        const data = loadData();
        delete data[msg.email];
        saveData(data);
        quotaProvider.refresh();
        refreshPanel();
    }
    break;
```

### 13.5 Pattern: Auto-Rotate Notification (không thể fully-auto vì switchAccount cần user chọn)

```javascript
// Khi phát hiện active account hết quota:
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
    }
}
// Lưu ý: switchAccount mở QuickPick — user vẫn phải bấm chọn trong menu.
```

### 13.6 Pattern: Auto-Sync Background trong activate()

```javascript
// Thêm vào activate():
setInterval(() => {
    autoSyncFromDB(quotaProvider, (res) => {
        if (res.status === 'ok') { updateStatusBar(); refreshPanel(); }
    });
}, 5 * 60 * 1000); // 5 phút
```

> [!WARNING]
> `child_process.execFile('python', ...)` sẽ fail nếu Python không có trong PATH. Luôn wrap try-catch trong background sync, không throw lỗi cho user.

### 13.7 Pattern: Trích xuất Phần trăm (%) và Nhóm Models từ SQLite
Mỗi email trong `state.vscdb` (key: `Davissss2.antigravity-account`) lưu số dư dạng `balances: { "model-name": { "value": 76, "resetTime": "ISO" } }`.
- Value thường là 0-100 (tương đương phần trăm).
- Nên nhóm model theo prefix (`gemini-`, `claude-`, `gpt-`).
- Lấy `percent` bằng cách tính trung bình cộng `value` của các model > 0.
- Lấy `overallResetTime` = MAX(`resetTime`) của toàn bộ models (để hiện đếm ngược khi chưa hết quota).

### 13.8 Pattern: Đồng bộ trạng thái ACTIVE ra Python App
Python App không thể đọc `vscode.authentication`. Cách giải quyết:
- Trong Extension `activate()` hoặc `onDidChangeSessions`, gọi `vscode.authentication.getSession('google')`.
- Ghi tên email active vào một file trung gian: `active_account.txt` (nằm chung thư mục với `quota_data.json`).
- Python GUI dùng `after(1000)` loop để đọc file txt này, từ đó gắn tag `(ACTIVE)` và highlight giao diện tương ứng.

### 13.9 Pattern: Refresh Quota thủ công cho 1 account
Extension gốc chỉ cho phép gọi lệnh `antigravity-account.refreshBalances` đối với tài khoản ĐANG ACTIVE.
- UI: Chỉ hiện nút `🔄` (Refresh riêng lẻ) trên dòng của tài khoản đang Active.
- Khi người dùng click `🔄`:
  ```javascript
  await vscode.commands.executeCommand('antigravity-account.refreshBalances');
  // Sau đó gọi hàm đọc lại SQLite db (sync_antigravity.py) để lấy số dư mới cập nhật
  autoSyncFromDB();
  ```

## 14. Pattern: Local OAuth Server for VS Code Extensions (Without Built-in Provider)

Khi viết Extension cần xác thực OAuth (như Google) nhưng IDE không có sẵn Auth Provider tương ứng, bạn có thể tự mở một Local HTTP Server siêu nhẹ để nhận OAuth Callback.

**Quy trình (tham khảo từ antigravity-account):**
1. **Tạo Local Server**: Dùng http.createServer() lắng nghe ở một cổng trống (thử từ mảng cổng định sẵn).
2. **Mở Trình Duyệt**: Gọi scode.env.openExternal(Uri.parse(authUrl)) với edirect_uri chỉ về http://localhost:<port>/oauth-callback. Đừng quên thêm prompt=consent và ccess_type=offline nếu cần Refresh Token.
2. **Mở Trình Duyệt**: Gọi  scode.env.openExternal(Uri.parse(authUrl)) với edirect_uri chỉ về http://localhost:<port>/oauth-callback. Đừng quên thêm prompt=consent và  ccess_type=offline nếu cần Refresh Token.
3. **Đón Mã Code**: Server nhận Request tại /oauth-callback, trích xuất code từ URL query.
4. **Phản hồi UI cho người dùng**: Server trả về một file HTML đẹp mắt thông báo thành công kèm theo đoạn script <script>window.close();</script> để tự động đóng tab. Sau đó đóng (close) server.
5. **Exchange Token**: Gọi API bằng https hoặc 
ode-fetch để đổi Code lấy Access Token / Refresh Token và lưu trữ vào globalState (hoặc SecretStorage).

Đây là một pattern độc lập, an toàn và cực kỳ mượt mà, giúp extension của bạn không phụ thuộc vào các tiện ích mở rộng xác thực bên thứ 3.

---

## 15. ⚡ Kiến Trúc Dữ Liệu — AG = Nguồn Sự Thật, .dat = Cache Tạm

> [!IMPORTANT]
> Đây là quy tắc cốt lưi của toàn bộ hệ thống QuotaAntigravity. Vi phạm sẽ dẫn đến dữ liệu hiển thị sai.

### 15.1 Luồng dữ liệu chính thức

```
state.vscdb (Antigravity Account IDE DB — ground truth)
        ↓  sync_antigravity.py --json
quota_data.dat  (cache tạm — ghi đè hoàn toàn sau mỗi sync)
        ↓  loadData() / _load_dat()
UI (extension WebView hoặc quota_db.py GUI)
```

### 15.2 Nguyên tắc bất biến

| Nguồn | Vai trò | Được ghi bởi | Được đọc bởi |
|---|---|---|---|
| `state.vscdb` | Ground truth — quota %, resetTime, groups | Antigravity Account extension | `sync_antigravity.py` |
| `quota_data.dat` | Cache tạm — kết quả cũ + track email thiếu | `sync_antigravity.py` | Extension JS / Python GUI |
| `active_account.txt` | Email đang active trong IDE | `switch_account.py` / extension | Python GUI (status bar) |

**Quy tắc ưu tiên:**
1. **AG DB luôn thắng** — Sau `sync_antigravity.py`, `.dat` được ghi đè bằng data từ AG. Không bao giờ giữ `.dat` cũ khi AG có data mới hơn.
2. **`.dat` chỉ có 2 mục đích:**
   - Hiện kết quả cũ khi đang chờ sync (offline cache)
   - Detect email nào **không có trong AG** → cảnh báo `lastError = 'Chưa có trong Antigravity Account'`
3. **Email không trong AG:** Không thể có quota data thực — luôn hiển thị `⚠️` và hướng dẫn thêm vào AG.

### 15.3 Pattern: "Check All" đúng chuẩn

```javascript
// extension.js — case 'checkAll'
const syncResult = await runPython(['sync_antigravity.py', dataFilePath, '--json']);
// syncResult = { status, synced, ag_emails: [...] }

const data = loadData();  // đọc .dat vừa được sync_antigravity.py cập nhật từ AG
const agEmails = new Set(syncResult.ag_emails || []);

for (const [email, entry] of Object.entries(data)) {
    if (!agEmails.has(email)) {
        entry.lastError = 'Chưa có trong Antigravity Account — bấm ➕ Thêm để thêm vào';
    } else if (entry.lastError?.includes('Antigravity Account')) {
        delete entry.lastError;  // email đã được thêm vào AG → xóa warning
    }
}
saveData(data);
```

```python
# quota_db.py GUI — _on_sync_done()
def _on_sync_done(self, res):
    self._ag_emails = set(res.get('ag_emails') or [])
    self._data = _load_dat(self._dat_path)  # .dat đã được sync_antigravity.py cập nhật từ AG

    for email, entry in self._data.items():
        if email not in self._ag_emails:
            entry['lastError'] = 'Chưa có trong Antigravity Account — bấm ➕ Thêm'
        elif 'Antigravity Account' in entry.get('lastError', ''):
            del entry['lastError']
    _save_dat(self._dat_path, self._data)
    self._render()
```

### 15.4 Pattern: Hiển thị "Renews ↻ HH:MM" (giống Antigravity Account)

Antigravity Account hiển thị thời gian phục hồi quota bên cạnh đếm ngược.
Nguồn: `overallResetTime` (timestamp ms epoch) trong `.dat`.

```python
def _fmt_cd(exh_until, reset_ms=0):
    """Trả về '2h 30m  ↻ 15:30' hoặc '↻ 31/07 04:00'."""
    import datetime, time
    now_ms = time.time() * 1000
    parts = []

    if exh_until and exh_until > now_ms:
        rem = exh_until - now_ms
        parts.append(f'{int(rem//3_600_000)}h {int((rem%3_600_000)//60_000):02d}m')

    rt = reset_ms or exh_until or 0
    if rt and rt > now_ms:
        dt = datetime.datetime.fromtimestamp(rt / 1000)
        fmt = '↻ %H:%M' if dt.date() == datetime.date.today() else '↻ %d/%m %H:%M'
        renews_str = dt.strftime(fmt)
        if renews_str not in parts:
            parts.append(renews_str)

    return '  '.join(parts)
```

**Trong `_render()`:**
```python
reset_ms = info.get('overallResetTime') or 0
cd = _fmt_cd(exh_until, reset_ms) if (exh_until > now_ms or reset_ms > now_ms) else ''
```

### 15.5 Pattern: Row màu sắc trong Treeview GUI

```python
# Thứ tự ưu tiên xác định tag:
not_in_ag = self._ag_emails and email not in self._ag_emails
ag_err    = 'Antigravity Account' in last_err

if not_in_ag or ag_err:  tag = 'noag'    # 💜 Chưa trong AG — cần thêm
elif not gs:              tag = 'nodata'  # ⬛ Chưa sync
elif not avail:           tag = 'exh'    # 🔴 Tất cả groups hết quota
elif exh_grps:            tag = 'part'   # 🟡 Một số groups hết
else:                     tag = 'ok'     # 🟢 Tất cả OK
```
