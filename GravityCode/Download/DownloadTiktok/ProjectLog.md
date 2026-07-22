# ProjectLog.md - Nhat Ky Du An mycustomFaveTT

> Ban fork offline, standalone cua extension "myfaveTT".
> Moi thay doi ky thuat moi: cap nhat file nay VA bo sung phuong phap vao [ThinkGuide.md](./ThinkGuide.md).

---

## Tong quan Du an

| Thong tin | Chi tiet |
|---|---|
| Extension goc | myfaveTT (v1.12.63) |
| ID goc | gmajiifkcmjkehmngbopoobeplhoegad |
| Ten ban custom | mycustomFaveTT |
| Muc tieu | Offline UI, khong tracking, khong gioi han tai, chay song song ban goc |
| Thu muc | DownloadTiktok/ |

---

## Nhat Ky Thay Doi

### Giai doan 1 - Tai & Phan Tich Source (19/07/2026)

**Viec da lam:**
- Viet script Python tai file .crx tu Chrome Web Store bang API redirect cua Google.
- Phat hien CRX3 chua ZIP o phan cuoi, cat bo header bang magic bytes PK (ZIP).
- Giai nen thanh cong toan bo source vao thu muc DownloadTiktok/.

**Phan tich co che hoat dong:**
- b.js (background): Nghe len network request den /api/post/item_list/ de bat Header co chu ky TikTok.
- s.js (main logic): Nhan header tu b.js qua BroadcastChannel, dung header do goi TikTok API lay link MP4.
- r.js (relay): Tao iframe load UI tu ui.myfavett.com va lam cau noi postMessage.
- c.js (content script): Tiem sidebar va s.js vao DOM trang TikTok.

**Phu thuoc ngoai:**
- ui.myfavett.com -> Toan bo giao dien nguoi dung (React/Vue SPA)
- resync.myfavett.com -> Kiem tra ban quyen / unlock Premium

-> Xem cach xu ly: ThinkGuide.md - Muc 4

---

### Giai doan 2 - Standalone hoa (19/07/2026)

| File | Thay doi |
|---|---|
| manifest.json | Them "ui_offline/*" vao web_accessible_resources |
| r.js | Xoa iframe resync; Doi src iframe UI -> chrome.runtime.getURL("ui_offline/index.html") |
| s.js | Sua cap: 1e3 -> 9999999; Sua Ue={kt:!1} -> Ue={kt:!0} (bypass resync) |
| ui_offline/ | Cao toan bo HTML + assets tu ui.myfavett.com bang Python |

**Ket qua:** Extension khong phu thuoc server ngoai nao ngoai TikTok. Gioi han tai bi vo hieu hoa.

-> Ky thuat chi tiet: ThinkGuide.md - Muc 3

---

### Giai doan 3 - Doi ten & Popup Check Update (19/07/2026)

| File | Thay doi |
|---|---|
| manifest.json | Doi ten -> "mycustomFaveTT"; Them quyen "notifications"; Xoa truong "key" |
| b.js | Them chrome.notifications.create() khi click icon -> popup hoi check update |
| b.js | Them onButtonClicked -> mo link Web Store neu chon "Kiem tra ngay" |

**Ket qua:** Ten rieng, popup update, khong ghi de ban goc.

-> Ly do xoa "key": ThinkGuide.md - Muc 4

---

### Giai doan 4 - Fix Xung dot BroadcastChannel (19/07/2026)

**Trieu chung:** Sidebar hien "already running in another tab", loading mai khong hien giao dien.

**Nguyen nhan:**
1. Ca ban goc va ban custom cung dung BroadcastChannel("myfaveTT"). Ban goc phan hoi "dang chay roi" -> ban custom bi block.
2. r.js dung duong dan tuong doi "ui_offline/index.html" -> Chrome resolve thanh tiktok.com/ui_offline/... -> iframe trang.

**Fix da thuc hien:**

| File | Thay doi |
|---|---|
| s.js (dong 1) | BroadcastChannel("myfaveTT") -> BroadcastChannel("mycustomFaveTT") |
| b.js | BroadcastChannel("myfaveTT") -> BroadcastChannel("mycustomFaveTT") |
| r.js | BroadcastChannel("myfaveTT") -> BroadcastChannel("mycustomFaveTT"); src -> chrome.runtime.getURL("ui_offline/index.html") |

**Ket qua:** Ban goc va ban custom chay song song hoan toan doc lap.

-> Hieu sau: ThinkGuide.md - Muc 4

---

## Trang thai Hien Tai

| Muc | Trang thai |
|---|---|
| Tai video TikTok | OK (can mang) |
| Giao dien UI | OK - load tu local ui_offline/ |
| Tracking / Ban quyen | Da loai bo |
| Gioi han so luong tai | Da go bo (9999999) |
| Chay song song ban goc | Khong xung dot |
| Popup check update | Hien khi click icon extension |

---

## Cai dat Offline (Load Unpacked)

1. Mo chrome://extensions/ hoac edge://extensions/
2. Bat Developer mode (goc tren phai)
3. Nhan Load unpacked -> Chon thu muc DownloadTiktok
4. Extension mycustomFaveTT se xuat hien ngay
5. Moi khi sua code -> Nhan nut Reload o trang extensions

---

*Cap nhat lan cuoi: 19/07/2026 - Xem ThinkGuide.md de hieu phuong phap luan.*


### Giai doan 5 - Them Popup Log + Nut Cap nhat UI (19/07/2026)
- **popup.html**: Tao popup chinh voi 3 khu vuc: header, actions (Open TikTok + Update UI + Clear), log panel
- **popup.js**: Doc log tu chrome.storage.local["customFaveTT_log"], hien real-time qua chrome.storage.onChanged, xu ly nut Update UI
- **manifest.json**: Them "default_popup": "popup.html" va quyen "storage"
- **b.js**: Xoa chrome.action.onClicked, them message listener xu ly lenh "update_ui" (scrape ui.myfavett.com, bao cao ket qua)
- **s.js**: Them _writeLog() helper o dau file, hook vao ham ln() de log: bat dau tai, thanh cong, loi 403, loi khac
- **Dam bao log khong bi mat**: Log o chrome.storage.local["customFaveTT_log"], hoan toan tach biet voi ui_offline/. Cap nhat UI chi dung key "customFaveTT_lastUpdateCheck", KHONG bao gio xoa key log.

