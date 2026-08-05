# Project Log - Copilot Word Export Addon

## Mô tả chung
Addon (Extension Manifest V3) được thiết kế để tự động hóa quá trình hỏi đáp và tải tài liệu (Markdown/HTML) từ các trình duyệt AI. Đọc lộ trình (Roadmap) và chạy vòng lặp hỏi đáp ngầm.

## Tính năng đã triển khai
1. **Auto Save & Auto Resume**: Tự động lưu trạng thái vào session.json.
2. **Quản lý DOM Fingerprint**: Hỗ trợ tìm kiếm ô input/send linh hoạt.
3. **Advanced Hierarchy Extractor**: Bóc tách dữ liệu phân tầng.
4. **Trích xuất Delta**: Lọc nội dung HTML, bỏ markdown.
5. **Keep Alive**: Chống ngủ đông (Throttling) bằng Audio rỗng.
6. **Follow-up tự động (Hỏi bồi)**: Tự động gửi lệnh tiếp tục giảng bài cho đến khi nhận được cờ `[HOÀN TẤT NGÀY X]` hoặc `[HOÀN TẤT BÀI HỌC]` từ AI, để đảm bảo không bị cắt cụt bài do token limit. Số lượt hỏi bồi tối đa có thể tuỳ chỉnh (mặc định 999).
7. **Tab Trích Xuất HTML (Mới - 2026-08-05)**: Thêm tab thứ 2 trong popup, cho phép người dùng:
   - Chọn nền tảng AI (Copilot, Gemini, ChatGPT)
   - Đặt tên file tùy ý hoặc nhấn nút Auto để tự sinh tên từ tiêu đề trang + ngày
   - Click "Trích xuất & Lưu File HTML" → trình duyệt hiện hộp thoại chọn nơi lưu (saveAs)
   - File được build dạng HTML đầy đủ (CSS + nav bar) như các file Day xuất tự động.

## Tính năng đang triển khai
- (Trống)

## Lịch sử cập nhật
- Yêu cầu tích hợp Follow-up Logic. Khởi tạo ProjectLog.md.
- Đã triển khai xong tính năng Follow-up tự động với tham số tuỳ chỉnh `maxFollowUp` ở popup.
- 2026-08-05: Thêm tab "Trích Xuất" vào popup — cho phép xuất trang đang hỏi thành file HTML. Các file sửa: `popup.html`, `popup.js`, `content_script.js`, `background.js`.
