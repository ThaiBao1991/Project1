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

## Tính năng đang triển khai
- (Trống)

## Lịch sử cập nhật
- Yêu cầu tích hợp Follow-up Logic. Khởi tạo ProjectLog.md.
- Đã triển khai xong tính năng Follow-up tự động với tham số tuỳ chỉnh `maxFollowUp` ở popup.
