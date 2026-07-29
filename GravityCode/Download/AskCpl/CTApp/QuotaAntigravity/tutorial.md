# Hướng Dẫn Sử Dụng QuotaTracker

Hệ thống QuotaTracker bao gồm 2 thành phần hoạt động song song để giúp bạn quản lý Quota của nhiều tài khoản Google trên Antigravity IDE một cách tự động.

---

## Phần 1: Cài đặt và Chạy IDE Extension (`QuotaExt`)

Extension này cắm trực tiếp vào IDE để tự động nhận diện tài khoản bạn đang dùng và ghi nhận trạng thái khi bị lỗi Quota.

### Cách cài đặt:
1. Mở thư mục gốc chứa các extension của IDE. Tùy thuộc vào bản IDE bạn đang dùng, thư mục này thường nằm ở:
   - `C:\Users\12953 bao\.antigravity-ide\extensions`
   - Hoặc `C:\Users\12953 bao\.vscode\extensions`
2. **Copy toàn bộ thư mục `QuotaExt`** (nằm trong `CTApp\QuotaAntigravity`) dán vào thư mục extensions ở Bước 1.
3. Tắt hoàn toàn Antigravity IDE và **mở lại**.

### Thiết lập lần đầu:
1. Nhìn sang cột bên trái (Sidebar) của IDE, bạn sẽ thấy biểu tượng QuotaTracker xuất hiện.
2. Bấm phím **F1** (hoặc Ctrl+Shift+P) để mở hộp thoại lệnh.
3. Gõ chữ: `Quota: Chọn thư mục lưu file Data` và nhấn Enter.
4. Chọn đúng thư mục `CTApp\QuotaAntigravity` của dự án này. Extension sẽ tự tạo file `quota_data.json` ở đó.

---

## Phần 2: Chạy Phần Mềm Bảng Điều Khiển (`QuotaApp`)

Đây là cửa sổ nhỏ giúp bạn theo dõi đồng hồ đếm ngược trực quan. Bạn có thể mở nó bất cứ lúc nào.

### Cách chạy:
1. Mở Terminal (Command Prompt / PowerShell).
2. Chạy lệnh kích hoạt giao diện Python:
   ```bash
   python "C:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\Download\AskCpl\CTApp\QuotaAntigravity\QuotaApp\quota_app.py"
   ```
3. Lần đầu mở app, bấm nút **"Chọn"** ở góc trên cùng bên phải.
4. Trỏ đường dẫn đến file `quota_data.json` mà Extension vừa tạo ra ở Bước 1. (Mặc định nó nằm ở `CTApp\QuotaAntigravity\quota_data.json`).
5. Dữ liệu sẽ tự động đồng bộ!

---

## 🚀 Cách sử dụng thực tế (Quy trình hằng ngày)

1. Bạn dùng IDE bình thường. Nếu đổi tài khoản Google, Extension sẽ tự cập nhật dưới thanh Status Bar.
2. Bất thình lình, AI báo lỗi **"Hết Quota" / "Resource Exhausted"**.
3. Bạn dùng chuột **Click thẳng vào Tên Email** ở dưới cùng góc phải màn hình IDE (Hoặc bấm F1 > Gõ `Quota: Đánh dấu Hết Quota`).
4. Xong! Bạn không cần làm gì thêm. Phần mềm Python sẽ nhận lệnh, đổi Email đó sang trạng thái 🔴 **Hết Quota** và bắt đầu lùi thời gian đếm ngược 24 tiếng đồng hồ.
5. Bạn cứ việc đổi sang Email khác trên IDE để làm việc tiếp. Dễ như ăn kẹo!
