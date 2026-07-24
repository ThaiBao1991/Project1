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

- **Phien b?n 2.2 (Clipboard Hijack)**: 
  - Kh?c ph?c l?i ?? tr? Dropdown: Them c? ch? ch? va th? l?i (Retry 5 l?n) n?u animation c?a nut Create project ch?a load k?p.
  - B? sung nut 'Cao toan b? Key C?' tren giao di?n: Tiem ma ?anh ch?n Clipboard (Clipboard Hijacking) ?? b?t ???c API Key khi gi? l?p click hang lo?t vao cac nut Copy.
  - Xac nh?n ch?c n?ng Nh?p JSON ?a x? ly t?t vi?c b? qua Key trung.
