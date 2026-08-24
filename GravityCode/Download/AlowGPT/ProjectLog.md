# ProjectLog - AlowGPT

## Thông Tin Dự Án
- **Tên dự án:** AlowGPT (DPI / SNI Bypass Proxy & OpenCode/VSCode Gateway)
- **Mục tiêu:** Ứng dụng Desktop GUI giúp vượt tường lửa Trend Micro chặn AI API và ChatGPT bằng thuần Python 100%, tích hợp cấu hình 1-chạm cho OpenCode và VSCode.
- **Vị trí:** `c:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\Download\AlowGPT`

---

## Kiến Trúc & Tính Năng
1. **Core Engine (`core_engine.py`)**:
   - `AlowGPTProxyServer`: HTTP/HTTPS CONNECT Proxy đa luồng.
   - `VSCodeConfigHelper`: Tự động tìm và cập nhật `settings.json` của VSCode.
   - `SystemProxyManager`: Bật/Tắt System Proxy Windows Registry an toàn.
2. **Giao Diện Điều Khiển (`app_gui.py`)**:
   - **Tab 1: ⚡ OpenCode & VSCode**:
     - Nút 1-chạm: "⚡ Tự Động Áp Dụng Proxy Vào VSCode".
     - Nút "📋 Copy Base URL" cho OpenCode (`https://testconnectgpt.gamesvendn02.workers.dev/v1`).
     - Khung "🧪 Live API Test" kiểm tra kết nối API Key và model trực tiếp.
   - **Tab 2: ⚙️ Thiết Lập Chế Độ**: Chuyển đổi Phân mảnh SNI nội bộ hoặc Cloudflare Worker Relay + Copy mã Worker mẫu.
   - **Tab 3: 🌐 Danh Sách Tên Miền**: Quản lý các domain `api.openai.com`, `api.anthropic.com`, `api.deepseek.com`...
   - **Tab 4: 📜 Nhật Ký Hoạt Động**: Live log thời gian thực.
3. **Entry Point (`main.py`)**: Khởi chạy ứng dụng.

---

## Lịch Sử Cập Nhật
- **2026-08-24:**
  - Khởi tạo dự án và các tính năng cốt lõi.
  - Bổ sung Tab OpenCode & VSCode Helper với tính năng tự động cấu hình `settings.json` và Live API Tester.
