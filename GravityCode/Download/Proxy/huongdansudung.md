# Hướng Dẫn Sử Dụng Anti-Block Proxy

## 1. Giới thiệu
Anti-Block Proxy là một ứng dụng Local Proxy chạy cục bộ trên máy tính, giúp vượt qua các giới hạn mạng (như chặn trang web, chặn tải extension VSCode) bằng 2 phương pháp:
- **DPI Bypass:** Lách hệ thống quét gói tin của nhà mạng bằng cách băm nhỏ dữ liệu (chia nhỏ gói ClientHello).
- **Free Proxy:** Sử dụng các proxy miễn phí trên mạng làm trạm trung chuyển.

> [!IMPORTANT]
> Ứng dụng này **CHỈ hỗ trợ các trang web bảo mật HTTPS** (có biểu tượng ổ khóa). Các kết nối đến trang web HTTP (không mã hóa) sẽ bị từ chối kết nối ngay lập tức.

## 2. Cách khởi động ứng dụng
1. Mở Terminal (Command Prompt hoặc PowerShell) tại thư mục chứa mã nguồn.
2. Cài đặt thư viện yêu cầu (nếu chưa cài): 
   ```bash
   pip install requests
   ```
3. Chạy lệnh để mở giao diện: 
   ```bash
   python main.py
   ```
4. Trên giao diện hiện ra:
   - Điền cổng (Port) muốn dùng, mặc định: `8888`.
   - Chọn chế độ (Khuyên dùng: **DPI Bypass**).
   - Bấm **"Bật Proxy Server"**.

## 3. Cách cấu hình mạng để sử dụng Proxy

### A. Đối với Trình duyệt (Chrome, Edge, Cốc Cốc)
Khuyên dùng tiện ích mở rộng như **Proxy SwitchyOmega** để tránh ảnh hưởng đến toàn hệ thống:
- **Giao thức (Protocol):** HTTP hoặc HTTPS
- **IP / Server:** `127.0.0.1` (hoặc `localhost`)
- **Port:** `8888` (trùng với port trên ứng dụng)

### B. Đối với VSCode (Khi không tải được Extension)
1. Mở VSCode, bấm tổ hợp phím `Ctrl + ,` để mở Cài đặt (Settings).
2. Gõ `proxy` vào ô tìm kiếm.
3. Tại mục **Http: Proxy**, điền vào: `http://127.0.0.1:8888`
4. Tại mục **Http: Proxy Strict SSL**, **BỎ TÍCH** tùy chọn này (giúp tránh lỗi chứng chỉ khi dùng DPI Bypass).
5. Khởi động lại VSCode.

> [!WARNING]
> Khi bạn đóng phần mềm Anti-Block Proxy, hãy nhớ xóa trắng ô `http.proxy` trong cài đặt của VSCode. Nếu quên, VSCode sẽ bị mất kết nối mạng hoàn toàn.

## 4. Xử lý các lỗi thường gặp

- **Bấm "Bật Proxy Server" báo lỗi `WinError 10048`:** 
  Cổng 8888 đã bị một phần mềm khác sử dụng. Hãy thử đổi thành `8889` hoặc `9999` trên giao diện, bấm bật lại, đồng thời đổi cài đặt bên trình duyệt/VSCode.
  
- **Vào mạng báo lỗi "Connection Reset" hoặc "Empty Response" ngay lập tức:** 
  Kiểm tra xem URL trang web có bắt đầu bằng `http://` không. Ứng dụng chỉ hoạt động với trang `https://`.

- **Dùng chế độ "Free Proxy" nhưng không vào mạng được:** 
  Đối với chế độ này, bạn **PHẢI** bấm nút *"Lấy Free Proxy và Chuyển chế độ"* và kiên nhẫn đợi cho đến khi báo chữ màu xanh lá trên giao diện rồi mới sử dụng được.
