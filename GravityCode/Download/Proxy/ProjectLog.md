# Project Log - Anti-Block Proxy

## Goal
Tạo một ứng dụng Python Proxy cục bộ hỗ trợ 2 chế độ: DPI Bypass và Free Proxy Scraper, có giao diện GUI bằng Tkinter.

## Status: HOÀN THÀNH

### 2026-08-13
- Khởi tạo thư mục và setup cấu trúc.
- Viết module `proxy_scraper.py` (Lấy và test Free Proxy).
- Viết module `server.py` (Xử lý TCP socket, cắt TLS ClientHello lách DPI).
- Tích hợp giao diện `main.py` có chọn Port (Mặc định: 8888), hỗ trợ chuyển đổi linh hoạt qua các chế độ: DPI Bypass, Free Proxy, Direct (Không proxy).
- Ứng dụng không yêu cầu quyền Admin nhờ lắng nghe Port cao và không chỉnh sửa routing hệ thống.
