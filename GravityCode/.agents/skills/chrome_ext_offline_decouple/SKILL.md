---
name: chrome_ext_offline_decouple
description: Quy trình bóc tách, giải phóng phụ thuộc máy chủ từ xa, bẻ khóa xác thực/giới hạn và đóng gói Chrome/Edge Extension chạy offline độc lập 100% không lo xung đột bản quyền hay bị quét từ xa.
---

# Quy Trình Bóc Tách & Đóng Gói Chrome Extension Offline Độc Lập

Kỹ thuật chuyển đổi một extension phụ thuộc server online thành bản độc lập (standalone offline-ready).

## Quy Trình 5 Bước Phân Tích & Bóc Tách

### Bước 1: Trích Xuất Source Từ File CRX
- File CRX là file ZIP có thêm header chữ ký ở đầu. Tìm magic bytes `PK\x03\x04` để cắt header và giải nén thành source code gốc.

### Bước 2: Khảo Sát `manifest.json`
- Xem `permissions`: Bản đồ quyền hạn của extension.
- Xem `content_scripts`: Script tiêm vào trang web.
- Xem `background.service_worker`: Script chạy nền.

### Bước 3: Lần Theo Luồng Dữ Liệu & Tìm "Dây Rốn" Phụ Thuộc
- Dùng regex/grep quét tất cả URL `https://` trong source.
- Phân loại:
  - URL API dịch vụ chính (cần giữ để lấy dữ liệu).
  - URL kiểm tra license/bản quyền (cần xóa bỏ/bypass).
  - URL load giao diện web từ xa (cần cào về local).

### Bước 4: Cào Giao Diện & Điều Hướng Về Local
- Tải toàn bộ HTML, CSS, JS của web UI về thư mục `ui_offline/`.
- Sửa URL tuyệt đối sang tương đối.
- Cấp quyền `web_accessible_resources` cho thư mục `ui_offline/` trong `manifest.json`.
- Sử dụng `chrome.runtime.getURL("ui_offline/index.html")` để nạp UI vào iframe.

### Bước 5: Chống Xung Đột Khi Chạy Song Song
- **Đổi tên BroadcastChannel**: Đổi `new BroadcastChannel("old_name")` sang một tên duy nhất để tránh nghe lén hoặc va chạm sự kiện với extension gốc.
- **Xóa trường `key` trong `manifest.json`**: Cho phép trình duyệt tự cấp Extension ID mới, không bị ghi đè lên bản gốc.