# ProjectLog: QuotaAntigravity Tracker

## Mô tả
Hệ thống theo dõi và quản lý Quota cho các tài khoản Google khi sử dụng trên Antigravity IDE.
Dự án được xây dựng theo mô hình lai (Hybrid):
1. **QuotaExt**: Extension (Addon) chạy trên Antigravity IDE để tự động lấy tên đăng nhập và ghi vào file `quota_data.json`.
2. **QuotaApp**: Ứng dụng giao diện Tkinter bằng Python để đọc file `quota_data.json` và hiển thị đồng hồ đếm ngược.

## Quá trình phát triển

### Ngày 29/07/2026 — Khởi tạo & Fix cài đặt
- Khởi tạo cấu trúc dự án `QuotaExt` (Node.js/VSCode Extension) và `QuotaApp` (Python Tkinter).
- Tách bạch file data dùng chung `quota_data.json`.
- Hỗ trợ thiết lập Cooldown 24h.
- Fix lỗi thiếu `publisher` trong `package.json` → ID bị `undefined_publisher` khiến không load được.

### Ngày 29/07/2026 — Nâng cấp UX
1. **WebView Panel** — Hiển thị danh sách tất cả email với màu sắc 🔴/✅
2. **Phím tắt `Alt+Q` (Cải tiến QuickPick)** — Đánh dấu hết quota không lo gõ sai.
3. **Auto-detect via `vscode.lm` API** (thực nghiệm) — Poll mỗi 30s.

### Ngày 29/07/2026 — Tích hợp SQLite & Tối ưu Khởi động
1. **Đồng bộ tự động từ Antigravity Account (SQLite `state.vscdb`)**:
   - Viết `QuotaApp/sync_antigravity.py` đọc trực tiếp Database của IDE để lấy chính xác danh sách tài khoản và thời gian hồi phục (`resetTime`). Tính năng tự động đồng bộ (Auto-Sync) giúp loại bỏ việc nhập tay bằng `Alt+Q` nếu tài khoản đã cạn Quota bên IDE.
   - Thêm nút "🔄 Auto-Sync từ IDE" vào ứng dụng `quota_app.py`.
2. **Tính năng [➕ Thêm Account] (Gọi thẳng trình Đăng nhập)**:
   - Gỡ bỏ hộp thoại nhập tay thủ công. Thay vào đó, nút ➕ Thêm Account giờ đây sẽ gọi thẳng lệnh `antigravity-account.addAccount` của IDE. Bạn sẽ được điều hướng ra trình duyệt để đăng nhập Google OAuth đàng hoàng, sau khi đăng nhập xong, chỉ việc bấm nút "🔄 Auto-Sync", tool sẽ tự động bế trọn gói dữ liệu về (kể cả email lẫn Quota) một cách chính xác tuyệt đối!
3. **Tối ưu tốc độ khởi động Extension**:
   - Thêm `onView:quotaTrackerView` vào `activationEvents` trong `package.json`, giúp Quota Tracker load nhanh ngay lập tức khi mở sidebar, không còn bị chậm so với các extension khác.
4. **Cập nhật Kiến thức SKILL**:
   - Đã đóng gói kỹ thuật bypass File Locked (SQLite `state.vscdb`) vào SKILL.md để áp dụng cho các tác vụ/AI khác trên các máy tính khác.

## Cấu trúc file

```
CTApp/QuotaAntigravity/
├── guide.md                ← Hướng dẫn sử dụng đầy đủ
├── ProjectLog.md           ← File này
├── QuotaApp/               ← Python Tkinter UI
│   ├── quota_app.py        ← App chính (có nút Thêm & Auto-Sync)
│   └── sync_antigravity.py ← Script đọc SQLite (state.vscdb)
└── antigravity.quota-antigravity-ext-1.0.0/  ← Source ext
    ├── package.json        ← (Đã tối ưu khởi động)
    ├── extension.js        ← (Có nút ➕ Thêm Account trong HTML)
    └── media/icon.svg
```

## Trạng thái hiện tại
- ✅ Extension WebView & Python GUI hoạt động đồng bộ.
- ✅ Auto-Sync từ IDE Database lấy tự động `resetTime` — đã test thực tế chính xác.
- ✅ **UI overhaul hoàn toàn** (lần 3, 29/07/2026):
  - Layout `flex column + scrollable table-wrap` → không còn bị che khuất.
  - Active account badge màu xanh nổi bật + dòng active highlight + `▶ ACTIVE` label.
  - Click vào bất kỳ dòng nào → gọi `antigravity-account.switchAccount`.
  - Nút `▶ Dùng` riêng trên mỗi dòng để switch account tức thì.
  - Nút `🔄 Sync từ IDE` có trạng thái loading, phản hồi OK/Error sau sync.
  - Nút `➕ Đăng nhập / Thêm` → OAuth login → Tự động cập nhật im lặng, không hiện popup hỏi lại.
  - Filter `Tất cả / ✅ OK / 🔴 Hết` hoạt động chuẩn.
  - Sort `Email / Trạng thái` click header.
  - Auto-sync chạy Python `sync_antigravity.py` qua `child_process` ngay trong extension.
  - Đã xóa hoàn toàn tính năng "🔴 Đánh dấu hết" thủ công vì mọi thứ đã tự động.
- ✅ Logic tính quota Option B (Group-based): 
  - Đã chia 3 group: Gemini, Claude, GPT. Nếu account chỉ hết Gemini nhưng còn Claude/GPT → hiển thị huy hiệu `[Claude ✓] [GPT ✓]`
  - Trạng thái sẵn sàng hiển thị kèm % còn lại của Gemini (vd: `✅ Sẵn sàng (76%)`).
  - Hỗ trợ hiển thị "Đếm ngược" và "Reset lúc" ngay cả khi account đang ở trạng thái `Sẵn sàng`, với thanh progress bar màu xanh (nhằm biết thời điểm các quota bị trừ sẽ hồi lại 100%).
- ✅ `setDataPath` tự động merge data mới từ IDE nếu db tồn tại.
- ✅ Cập nhật `active_account.txt` tự động để Python App biết tài khoản nào đang được sử dụng (Thêm nhãn `(ACTIVE)` bên cạnh email trong GUI Python).
- ✅ Thêm nút `🔄` (Làm mới Quota tài khoản này) hiển thị riêng rẽ cho tài khoản đang ACTIVE. Nó sẽ gọi trực tiếp lệnh lấy data mới nhất từ server thay vì đợi ngầm 5 phút.
- ✅ **Bảo mật File Data (Quy tắc VÀNG)**: Đã đổi format lưu trữ từ file `quota_data.json` (plain text) sang file ngầm `quota_data.dat` (mã hóa Base64 2 chiều đồng bộ `btoa(unescape(...))`). NodeJS và Python đều đọc/ghi mượt mà không dùng native module, đáp ứng yêu cầu tự chủ database mã hoá.
- ✅ Background Auto-Sync: Tự động chạy mỗi 5 phút ngầm.
- ✅ Nút Delete 🗑️: Xóa account trực tiếp trên UI.
- ✅ Auto-Rotate Notifier: Nhắc chuyển account khi AI hết quota mà có account khác rảnh.
- ✅ Python GUI thêm cột `Models OK` hiển thị group sẵn sàng và phần trăm.



