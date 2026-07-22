# ThinkGuide.md — Cách Tư Duy & Phương Pháp Thực Hiện

> File này ghi lại **cách suy nghĩ, cách phân tích** và **phương pháp luận** để tạo ra bản `mycustomFaveTT` — một Chrome Extension độc lập, offline-ready, từ source code gốc của một extension đã có trên Store.

---

## 1. Tư Duy Cốt Lõi: "Xem Extension như một Website Đóng Gói"

Chrome Extension thực chất là một **bundle ZIP** chứa:
- `manifest.json` → Khai báo cấu hình, quyền hạn
- `*.js` → Logic chạy trên trang web hoặc nền (background)
- `*.html` → Giao diện (popup, sidebar, v.v.)
- `*.css`, `*.png` → Assets tĩnh

Khi bạn có source code này, bạn đã có toàn quyền **đọc, sửa, chạy lại** nó — giống như bạn đang đọc source một trang web tĩnh. Đây là điểm mấu chốt để tự tin thực hiện mọi thay đổi bên dưới.

---

## 2. Quy Trình 5 Bước Phân Tích Extension Bất Kỳ

### Bước 1: Lấy Source Code (Tải CRX)
- File CRX từ Chrome Web Store thực chất là một file ZIP với phần header chữ ký ở đầu.
- Dùng Python: tìm offset bắt đầu của ZIP magic bytes (`PK\x03\x04`), cắt header ra, giải nén phần còn lại.

### Bước 2: Đọc `manifest.json` Trước Tiên
- `permissions` → Extension này xin quyền gì? (Đây là "bản đồ năng lực")
- `content_scripts` → JS/CSS nào được tiêm vào trang web?
- `background.service_worker` → File nào chạy ngầm liên tục?
- `web_accessible_resources` → File nào có thể được truy cập từ ngoài extension?

### Bước 3: Lần Theo Luồng Dữ Liệu
Câu hỏi quan trọng nhất: **Dữ liệu đến từ đâu và đi về đâu?**

Với myfaveTT:
```
TikTok API (trình duyệt gửi request)
    → b.js nghe lén qua chrome.webRequest
    → Gửi qua BroadcastChannel → s.js (logic chính)
    → s.js gọi lại TikTok API (có header hợp lệ)
    → Lấy link MP4 → File System Access API → Lưu vào ổ đĩa
```

### Bước 4: Xác Định "Dây Rốn" Phụ Thuộc Ngoài
Tìm tất cả URL ngoài domain TikTok:
- Dùng `grep` / `Select-String` tìm `https://` trong tất cả file JS/HTML.
- Mỗi URL tìm được là một điểm phụ thuộc cần đánh giá: **cần thiết hay có thể cắt bỏ?**

Với myfaveTT:
| URL | Vai trò | Quyết định |
|---|---|---|
| `ui.myfavett.com` | Giao diện người dùng | Cào về local |
| `resync.myfavett.com` | Check bản quyền | Xóa bỏ hoàn toàn |
| `tiktok.com` | Tải video thực sự | Giữ lại (cần mạng để tải) |

### Bước 5: Giải Phẫu Từng Phụ Thuộc
Với mỗi điểm phụ thuộc, hỏi: **Extension sẽ làm gì nếu URL này không phản hồi?**
- Nếu treo/crash → Cần bypass hoặc thay thế.
- Nếu chỉ hiển thị lỗi nhỏ → Có thể để sau.

---

## 3. Kỹ Thuật Cốt Lõi: Cắt "Dây Rốn" Extension

### 3.1 Cào Giao Diện Web (UI Scraping)
Khi UI được load qua iframe từ một URL ngoài:
1. Tải trang chủ (`index.html`) về.
2. Dùng regex tìm tất cả asset đính kèm (`/assets/*.js`, `/assets/*.css`).
3. Tải toàn bộ asset, điều chỉnh lại đường dẫn từ `/assets/` → `assets/` (relative).
4. Cập nhật `manifest.json` cấp quyền `web_accessible_resources` cho thư mục mới.
5. Sửa code loader để dùng `chrome.runtime.getURL("ui_offline/index.html")` thay vì URL tuyệt đối.

> **Lý do phải dùng `chrome.runtime.getURL()`**: Extension ID được Chrome tạo ngẫu nhiên. Không thể dùng đường dẫn tương đối trong iframe vì iframe đang nằm trong trang TikTok (origin `tiktok.com`), không phải extension.

### 3.2 Bypass Hệ Thống Xác Thực (Auth Bypass)
Tìm biến kiểm soát trạng thái "đã xác thực":
- `grep "kt" / "isReady" / "unlocks"` trong file JS chính.
- Sửa giá trị khởi tạo từ `false` → `true`.

### 3.3 Bẻ Khóa Giới Hạn (Cap Unlock)
Tìm hàm định nghĩa giới hạn số lượng, đổi giá trị `cap` sang số rất lớn (VD: 9999999).

---

## 4. Kỹ Thuật Cốt Lõi: Chạy Song Song 2 Extension Cùng Origin

Khi fork một extension mà muốn chạy song song bản gốc:

### Vấn đề: BroadcastChannel Toàn Cục
`BroadcastChannel("tenkenh")` hoạt động trên **toàn bộ trình duyệt**, không phân biệt extension nào đang dùng. Nếu 2 extension dùng chung tên kênh → chúng sẽ nghe thấy tin nhắn của nhau → gây xung đột (thường biểu hiện là "already running in another tab").

### Giải Pháp: Đổi Tên Kênh Độc Nhất
Tìm tất cả `new BroadcastChannel("tencu")` trong toàn bộ source, đổi sang tên mới độc nhất.

### Vấn đề: Trùng Extension ID (Trường `key`)
Trường `key` trong `manifest.json` định nghĩa ID cố định cho extension. Nếu giữ nguyên → Chrome nhận dạng bản fork là "cùng extension" với bản gốc → ghi đè lên nhau.

### Giải Pháp: Xóa Trường `key`
Xóa dòng `"key": "..."` khỏi `manifest.json`. Chrome sẽ tự sinh ID mới → 2 extension tồn tại độc lập.

---

## 5. Checklist Tổng Quát Khi Fork Bất Kỳ Extension

```
[ ] 1. Tải CRX và giải nén thành công
[ ] 2. Đọc manifest.json, vẽ sơ đồ các file và vai trò
[ ] 3. Lần theo luồng dữ liệu chính (data flow)
[ ] 4. Liệt kê tất cả URL ngoài (phụ thuộc)
[ ] 5. Quyết định từng URL: Cào về / Bypass / Giữ lại
[ ] 6. Xóa trường "key" trong manifest để tránh ghi đè bản gốc
[ ] 7. Đổi tên BroadcastChannel sang tên độc nhất
[ ] 8. Cập nhật web_accessible_resources cho file mới
[ ] 9. Load unpacked và kiểm tra console (F12) cho lỗi
[ ] 10. Kiểm tra song song với bản gốc
```

---

## 6. Công Cụ Sử Dụng

| Công cụ | Mục đích |
|---|---|
| Python (`urllib.request`, `zipfile`, `re`) | Tải CRX, giải nén, cào HTML |
| PowerShell `Select-String` | Grep nhanh tìm từ khóa trong file JS minified |
| `npx prettier --write` | Format file JS minified thành dễ đọc |
| Chrome DevTools (F12) | Debug lỗi postMessage, iframe origin |
| `chrome://extensions/` → Load unpacked | Cài extension từ thư mục local |

---

*Tài liệu này được duy trì song song với `ProjectLog.md` — mỗi khi có kỹ thuật mới, hãy bổ sung vào đây.*
