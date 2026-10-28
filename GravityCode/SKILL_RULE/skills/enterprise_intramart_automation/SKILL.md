---
name: enterprise_intramart_automation
description: Automating enterprise web systems (Intramart, legacy portals, complex ERP) with deep nested iframes, strict CSP headers, dynamic DOM rerendering, and simulated user input events. Use when building or debugging browser extensions that must traverse multiple frame levels, bypass CSP limitations, handle batch approvals, or perform robust auto-clicks without dropping session state.
---

# Enterprise Intramart & Multi-Iframe Automation Guide

Hướng dẫn kiến trúc và kỹ thuật tự động hóa trình duyệt dành riêng cho các hệ thống doanh nghiệp (Enterprise Intranet, Intramart, ERP, Hệ thống trình ký) có cấu trúc bảo mật khắt khe và phân tầng phức tạp.

---

## 1. Thách Thức Kỹ Thuật Đặc Thù Của Hệ Thống ERP / Intramart

1. **Phân Tầng Đa Cấp Iframe Lồng Nhau (Nested Iframes)**:
   Nội dung nghiệp vụ không nằm ở `top window` mà nằm sâu trong 2-4 cấp `iframe` lồng nhau:
   `window` $\rightarrow$ `iframe#menu_frame` $\rightarrow$ `iframe#main_frame` $\rightarrow$ `iframe#content_frame`.
2. **Chính Sách Bảo Mật Khắt Khe (CSP - Content Security Policy)**:
   Chặn toàn bộ `eval()`, chặn chèn script inline (`<script>`), chặn giao tiếp cross-origin qua `postMessage` nếu không cùng domain.
3. **SPA / AJAX Re-rendering & Mất Tham Chiếu DOM (Stale Element Reference)**:
   Sau mỗi thao tác click duyệt, bảng dữ liệu bị reload toàn phần hoặc thay thế bằng DOM mới mà không đổi URL trang.
4. **Sự Kiện Chuột Phức Tạp (Synthetic Mouse Events)**:
   Hệ thống dùng các thư viện UI cũ (jQuery UI, YUI) hoặc hiện đại (React/Angular) lắng nghe chuỗi sự kiện `pointerdown` $\rightarrow$ `mousedown` $\rightarrow$ `mouseup` $\rightarrow$ `click`. Gọi đơn thuần `element.click()` thường không kích hoạt được logic nghiệp vụ.

---

## 2. Giải Pháp Duyệt Đa Tầng Iframe An Toàn

Trong Chrome/Edge Extension Manifest V3:

### Cấu hình `manifest.json`:
Bắt buộc bật `all_frames: true` và `match_about_blank: true` để Content Script tự động inject vào mọi frame:
```json
{
  "content_scripts": [
    {
      "matches": ["*://*.your-enterprise-domain.com/*"],
      "js": ["content_script.js"],
      "all_frames": true,
      "match_about_blank": true,
      "run_at": "document_idle"
    }
  ]
}
```

### Hàm Tìm Kiếm Xuyên Thấu Frame (Deep Frame Traversal):
Nếu Content Script chạy ở Top Window và cần tìm phần tử trong iframe cùng origin:
```javascript
function findInAllFrames(selector, currentDoc = document) {
  // Tìm ở document hiện tại
  const found = currentDoc.querySelector(selector);
  if (found) return found;

  // Đệ quy quét qua các frame con
  const iframes = currentDoc.querySelectorAll('iframe, frame');
  for (const iframe of iframes) {
    try {
      const frameDoc = iframe.contentDocument || iframe.contentWindow?.document;
      if (frameDoc) {
        const subFound = findInAllFrames(selector, frameDoc);
        if (subFound) return subFound;
      }
    } catch (e) {
      // Bỏ qua cross-origin iframe bị trình duyệt chặn
    }
  }
  return null;
}
```

---

## 3. Chuỗi Sự Kiện Giả Lập Chuẩn Xác (Full Synthetic Event Dispatch)

Không dùng `element.click()` đơn thuần. Hãy kích hoạt đầy đủ chuỗi sự kiện người dùng:

```javascript
function simulateUserClick(element) {
  if (!element) return false;
  
  element.scrollIntoView({ behavior: 'smooth', block: 'center' });
  
  const mouseEventInit = {
    bubbles: true,
    cancelable: true,
    view: window,
    buttons: 1
  };
  
  element.dispatchEvent(new PointerEvent('pointerdown', mouseEventInit));
  element.dispatchEvent(new MouseEvent('mousedown', mouseEventInit));
  element.dispatchEvent(new PointerEvent('pointerup', mouseEventInit));
  element.dispatchEvent(new MouseEvent('mouseup', mouseEventInit));
  element.dispatchEvent(new MouseEvent('click', mouseEventInit));
  
  return true;
}
```

---

## 4. Vòng Lặp Duyệt Hàng Loạt Tự Động (Continuous Batch Loop)

Để tự động duyệt danh sách công việc mà không làm crash trình duyệt:

1. **Tìm Nút Chọn Tất Cả (Select All Checkbox)** $\rightarrow$ Kích hoạt `simulateUserClick`.
2. **Kiểm tra trạng thái (State Validation)**: Đợi ít nhất 300ms để kiểm tra các checkbox con đã được check thật sự chưa.
3. **Click Nút Thực Hiện / Duyệt Nhanh (Process Continuously)**:
   - Ghi nhận số lượng bản ghi đang xử lý.
   - Thiết lập `MutationObserver` hoặc polling `setInterval` (mỗi 500ms) theo dõi sự xuất hiện của modal xác nhận hoặc thông báo kết thúc.
4. **Xác nhận Modal Popup Tự Động**: Bắt các dialog confirm bằng `[aria-modal="true"]` hoặc class modal đặc thù của Intramart, click nút "Đồng ý / OK".
5. **Giới hạn số vòng lặp tối đa (Max Iterations Guard)**: Luôn đặt cờ an toàn `max_rounds = 50` tránh rơi vào vòng lặp vô tận (Infinite Loop) khi server trả về lỗi.

