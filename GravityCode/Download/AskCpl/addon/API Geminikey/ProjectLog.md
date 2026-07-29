# Project Log: API Geminikey Auto Creator

Tiện ích mở rộng (addon) này được tạo ra để tự động hóa quá trình sinh API Key mới trên Google AI Studio thông qua việc tự động tạo Project mới.

## Mục tiêu
- Tự động click `Create API key`
- Chọn `Create new project` / `Create project`
- Đợi tạo xong và nhấn `Create API key`
- Lặp lại cho đến khi gặp lỗi giới hạn quota.

## Trạng thái hiện tại
- **Phiên bản 2.0**: 
  - Tách bạch 7 bước State Machine rõ ràng: `INIT` -> `WAIT_DIALOG_OPEN` -> `CLICK_DROPDOWN` -> `CLICK_CREATE_PROJECT_MENU` -> `CONFIRM_NEW_PROJECT` -> `WAIT_PROJECT_AND_CREATE_KEY` -> `EXTRACT_KEY_AND_CLOSE`.
  - Khắc phục lỗi tương tác với Dropdown.
  - Bổ sung tính năng cạo (scrape) ngầm API Key khi Dialog thứ 3 mở ra.
  - Bổ sung nút Export JSON trên popup để tải toàn bộ Keys thu thập được về máy tính.

- **Phien b?n 2.1**: 
  - C?p nh?t ham do tim ph?n t? dung textContent ?? l?c b? cac th? ?n va kho?ng tr?ng l?i.
  - B? sung Regex l?y ??a ch? email t? ??ng t? ma ngu?n.
  - L?u Key d??i d?ng object (key, email, type) thay vi ch? chu?i string.
  - C?p nh?t AskCpl.py: Them tinh n?ng Import JSON, t? ??ng x? ly ?anh s? Project ID theo Email, va them thu?c tinh type cho m?i API key.

- **Phiên bản 2.2 (Clipboard Hijack)**: 
  - Khắc phục lỗi độ trễ Dropdown: Thêm cơ chế chờ và thử lại (Retry 5 lần) nếu animation của nút Create project chưa load kịp.
  - Bổ sung nút 'Cào toàn bộ Key Cũ' trên giao diện: Tiêm mã đánh chặn Clipboard (Clipboard Hijacking) để bắt được API Key khi giả lập click hàng loạt vào các nút Copy.
  - Xác nhận chức năng Nhập JSON đã xử lý tốt việc bỏ qua Key trùng.

- **Phiên bản 2.3**:
  - Hỗ trợ trích xuất trường `project_name` (Tên Dự Án) khi cào key tự động và cào key thủ công.
  - Sửa lỗi quét thiếu key (đặc biệt là Default Gemini Project) bằng cách tối ưu hoá selector tìm kiếm nút Copy và quét `mat-tooltip`.
  - Cập nhật giao diện AskCpl hiển thị và cho phép chỉnh sửa cột Project Name.
  - **HOTFIX**: Cải tiến logic cào key cũ. Do Chrome chặn giả lập click (lỗi `isTrusted`), addon không click nút Copy nữa mà chuyển sang đọc giao diện (DOM) để quét mã Masked Key (`...klSw`) và map với Full Key do XHR chặn được. Thêm cảnh báo yêu cầu nhấn F5 nếu thiếu key do trang load trước khi bật addon.

- **Phiên bản 2.4 (Click-Dialog Scraper + UI Fix)**:
  - **Cào key cũ kiểu mới (Click-Dialog)**: Thay toàn bộ logic cào key cũ. Addon giờ tự động **click vào từng masked key link** (`...kSLw`), đọc Full Key từ dialog Angular mở ra, rồi tự đóng dialog bằng Escape. Cách này lấy được 100% key kể cả key `AQ.` (OAuth token) của Default Gemini Project — loại key không bao giờ xuất hiện trong HTML hay XHR response.
  - **Fix Auto Close khi đạt giới hạn project**: `checkLimits()` giờ tự động gọi `closeCurrentDialog()` để đóng popup lỗi và dừng state machine ngay lập tức. Bổ sung thêm text pattern `you've used all your google cloud projects`.
  - **Fix đổi Gmail**: Khi phát hiện đổi email, addon chỉ reset bộ đếm (`api_keys = []`) mà không tự động xuất JSON ra file nữa.
  - **Fix popup tự đóng sau Export**: Sau khi tải JSON xuống, popup hiện thông báo "✅ Đã xuất X key!" rồi tự đóng sau 1.5 giây.
  - **Fix AskCpl.py UI bị đè**: Dialog Add và Edit API Key được nâng cấp dùng `Canvas + Scrollbar` (cuộn nội dung) với nút hành động (Lưu/Hủy/Kiểm tra) được ghim cố định ở dưới cùng, không bị bị tràn ra ngoài màn hình dù form dài thêm. Geometry tăng từ `460x360` lên `480x580`, thêm `minsize(460, 500)` và `resizable(True, True)`. Bổ sung import `Canvas` vào header AskCpl.py.

