# ProjectLog — AppForVinh (MISA Data Extractor)

## Trạng thái: 🔄 Đang phát triển

---

## 2026-10-05 — Khởi tạo dự án

### Mục tiêu
Trích xuất và lưu trữ dữ liệu từ MISA AMIS (actapp.misa.vn) vào database SQLite local.

### Dữ liệu cần thu thập
- **Khách hàng**: Mã KH, Tên KH, Địa chỉ, MST, Người liên hệ
- **Phiếu bán hàng**: Số CT, Ngày, Điều khoản thanh toán, NV bán hàng
- **Chi tiết phiếu**: Mã hàng, Tên hàng, ĐVT, Số lượng, Đơn giá, Thành tiền, Thuế GTGT

### Files đã tạo
| File | Mô tả |
|------|-------|
| `build_db.py` | Python script tạo và quản lý SQLite database |
| `extract_misa.js` | JavaScript để paste vào Chrome Console → extract data |
| `misa_data.db` | SQLite database (tạo tự động khi chạy build_db.py) |

### Database Schema
- `khach_hang` — Danh mục khách hàng
- `hang_hoa` — Danh mục hàng hóa
- `phieu_ban_hang` — Header phiếu bán hàng
- `chi_tiet_phieu_ban` — Dòng chi tiết từng phiếu

### Dữ liệu đã có (từ screenshot)
- **BH150178I**: CTYTH-E | CÔNG TY CP PHÒNG KHÁM ĐA KHOA TÂN THÀNH | MST: 3001748675
  - Địa chỉ: Số nhà 17, đường Lê Hữu Trác, Xã Hương Khê, Hà Tĩnh
  - TM/CK | 30 ngày | Hạn: 04/11/2026

### Việc cần làm tiếp
- [ ] Chạy `extract_misa.js` trong Console MISA để lấy đầy đủ Mã hàng, Tên hàng
- [ ] Lưu JSON vào `misa_extracted.json` → chạy `build_db.py` lại
- [ ] Nếu có nhiều phiếu → cần script tự động duyệt danh sách phiếu
- [ ] Bổ sung UI hoặc export Excel nếu cần

### Known Issues & Giải pháp
- **Lỗi MISA chặn F12 (Anti-DevTools/Debugger Loop)**: MISA AMIS có script ngầm liên tục gọi `debugger;` khi mở F12, làm đóng băng luồng tải dữ liệu API dẫn đến dữ liệu phiếu trả về rỗng/0.
  - *Giải pháp 1 (Khuyên dùng)*: Sử dụng **Bookmarklet** trên thanh dấu trang Chrome (chạy trực tiếp trong ngữ cảnh trang mà KHÔNG cần mở F12).
  - *Giải pháp 2*: Trong F12 DevTools, bấm `Ctrl + F8` (Deactivate breakpoints) để vô hiệu hóa mọi lệnh `debugger;`.
- Browser subagent gặp lỗi tải/503 từ model -> Ưu tiên dùng script chạy trực tiếp trên Chrome của người dùng.

### Các phương pháp trích xuất dữ liệu
1. **Phương pháp 1: Bookmarklet (Khuyên dùng - Zero DevTools)**:
   - Tạo Bookmark với mã JS extract trực tiếp từ Vue component instance (`__vue__`) và DOM.
   - Nhấp Bookmark trên tab MISA -> tự động tải `misa_extracted_full.json`.
2. **Phương pháp 2: Console F12 với Ctrl + F8**:
   - Nhấn F12 -> bấm ngay `Ctrl + F8` để tắt debugger block -> paste `extract_misa.js` -> chạy `readDomNow()` hoặc `downloadCapture()`.
3. **Nạp dữ liệu vào Database**:
   - Chạy `python build_db.py` để tự động parse file JSON và lưu vào `misa_data.db`.
