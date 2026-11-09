# Project Log: Local AI (Portable Llama.cpp + Dolphin Uncensored + GUI Control Panel)

## 1. Thông Tin Môi Trường & Hệ Thống
- **Thiết bị**: Windows 11 Pro 64-bit, CPU Intel Core Ultra 3 205 (8 nhân, 8 luồng).
- **Tăng tốc phần cứng**: Intel(R) AI Boost (NPU) + Intel Graphics (Vulkan / AVX2).
- **Bộ nhớ RAM**: 16 GB (Khả dụng ~4.5 - 8 GB).
- **Thư mục lưu trữ**:
  - `GravityCode\MBC\LocalAI\`: Mã nguồn điều khiển (`local_ai_gui.py`, `start_ai.bat`, `test_chat.py`, `ProjectLog.md`).
  - `D:\LocalAI\bin`: Bộ chạy `llama.cpp` portable (Build 12211, hỗ trợ Vulkan và tối ưu Intel).
  - `D:\LocalAI\models`: Nơi lưu trữ các file mô hình `.gguf` nặng ~4.5 GB (giữ an toàn cho ổ C).
  - `D:\LocalAI\start_ai.bat`: File chạy đồng bộ từ ổ D.
- **Mô hình mục tiêu**: `QuantFactory/dolphin-2.9.2-qwen2-7b-GGUF` (Bản `Q4_K_M` ~4.48 GB, 100% Uncensored).

## 2. Nhật Ký Triển Khai (Changelog)
- **2026-11-09**:
  - Tải và cài đặt thành công `llama.cpp` portable Vulkan/CPU vào `D:\LocalAI\bin`.
  - Xây dựng ứng dụng **Bảng Điều Khiển Giao Diện Đồ Họa (Local AI Control Panel)**:
    - File: `local_ai_gui.py` (Tkinter Dark Mode).
    - Tính năng: Bật/Tắt Server AI 1-click, đèn báo trạng thái Xanh/Đỏ, tự động quét và chọn file `.gguf` trong `D:\LocalAI\models`.
    - Hỗ trợ nút sao chép 1-click cho: `Base URL` (`http://127.0.0.1:8080/v1`), `API Key` (`local`), `Model ID`.
    - Tích hợp nút mở Web Chat trình duyệt và mở nhanh thư mục `models`.
    - Thêm cơ chế thăm dò (Health Check polling) xác nhận Model nạp xong 100% vào RAM trước khi chuyển trạng thái "Đang chạy" để tránh lỗi mở web quá sớm.
  - Cập nhật cả 2 file `start_ai.bat` (tại thư mục dự án và tại `D:\LocalAI`) để khởi chạy giao diện GUI mượt mà không hiện màn hình đen cmd.
