# QmhWebsite — Project Rules

## 1. Luôn đọc PROJECT_MEMORY.md trước

Trước khi làm bất kỳ thay đổi nào, **bắt buộc** đọc `PROJECT_MEMORY.md` để nắm:
- Kiến trúc dự án hiện tại
- Các lỗi đã biết và cách fix
- Trạng thái tính năng (đã xong / đang làm)
- Kỹ thuật tải video (pipeline, strategies, CDN)

## 2. Đề xuất phương án trước khi code

Với mọi yêu cầu không trivial:
1. **Phân tích** code liên quan trước
2. **Viết phương án rõ ràng** (sẽ sửa file nào, thay đổi gì, tại sao)
3. **Chờ user xác nhận** ("ok", "tiếp tục") trước khi viết code
4. Không tự ý code khi chưa có xác nhận

## 3. Review và kiểm tra lỗi sau khi code xong

Sau mỗi thay đổi code:
1. **Đọc lại đoạn vừa sửa** để xác nhận đúng
2. **Chạy thử** nếu có thể (import test, syntax check)
3. **Kiểm tra side effects** — những nơi khác gọi hàm vừa sửa
4. **Cập nhật PROJECT_MEMORY.md** nếu có thay đổi kiến trúc hoặc fix bug quan trọng

## 4. Cấu trúc dự án

- Entry point: `python qmhdowload.py`
- Python: `C:/Python311/python.exe`
- Browser: Chrome (không có CocCoc)
- Config: `config.json` (cùng thư mục gốc)
- Skill chi tiết: xem `.agents/skills/qmh_download_pipeline/SKILL.md`
