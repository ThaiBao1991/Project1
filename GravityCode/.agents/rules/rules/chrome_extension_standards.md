# Chrome Extension Manifest V3 Standards

Áp dụng cho tất cả Extension Chrome/Edge (Manifest V3).

## 1. Tránh Xung Đột & Độc Lập Khi Chạy
- **BroadcastChannel**: Đặt tên channel duy nhất theo tên extension, không dùng tên chung chung dễ xung đột đa extension (như `"channel"` hay `"sync"`).
- **ID & Manifest Key**: Không tái sử dụng khóa `"key"` từ extension gốc khi fork hoặc clone; để Chrome tự cấp ID mới nhằm tránh ghi đè bản gốc.
- **Offline Decoupling**: Khi cào giao diện web về chạy offline trong extension, dùng `chrome.runtime.getURL("path/to/asset")` và khai báo trong `web_accessible_resources`.

## 2. Xử Lý Bộ Nhớ & Dữ Liệu
- **Bắt buộc chuẩn Base64 & Unicode đồng bộ 2 chiều**:
  - Save: `btoa(unescape(encodeURIComponent(JSON.stringify(obj))))`
  - Load: `JSON.parse(decodeURIComponent(escape(atob(str))))`
  - Hoặc dùng `TextEncoder` & `TextDecoder` (Uint8Array).
- **Tránh tràn dung lượng**: `chrome.storage.local` có giới hạn 10MB (hoặc không giới hạn nếu có quyền `unlimitedStorage`). Phải kiểm tra kích thước payload trước khi lưu.

## 3. Service Worker & IPC Reliability
- **Keep-alive khi chạy ngầm**: Service worker Manifest V3 tự động sleep sau 30 giây rảnh rỗi. Dùng cổng kết nối dài hạn (`chrome.runtime.connect`) hoặc Web Locks API / offscreen document để giữ tiến trình khi xử lý tác vụ vòng lặp lớn.