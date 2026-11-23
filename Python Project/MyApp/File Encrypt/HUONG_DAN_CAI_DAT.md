# HƯỚNG DẪN CÀI ĐẶT & SỬ DỤNG ỨNG DỤNG FILE ENCRYPT

Ứng dụng đa năng bao gồm các tính năng:
1. **Đổi file `.xlsb` sang `.csv`** (hỗ trợ chọn dòng tiêu đề header tùy biến).
2. **Mã hóa và giải mã file / thư mục** bằng thuật toán mã hóa chuẩn quân sự **AES-CBC**.
3. **Gửi email tự động** (mô-đun đang phát triển).

---

## 🚀 1. Cách Chạy Nhanh Ứng Dụng

- **Cách 1 (Khuyên dùng)**: Click đúp vào file `run.bat`. Ứng dụng sẽ tự động khởi động. (Nếu thiếu thư viện, ứng dụng sẽ tự động tải và cài đặt nhờ cơ chế auto-install).
- **Cách 2**: Chạy qua Terminal / Command Prompt:
  ```bash
  cd "C:\Users\12953 Bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\Python Project\MyApp\File Encrypt"
  python main.py
  ```

---

## 📦 2. Danh Sách Thư Viện Cần Thiết

Ứng dụng yêu cầu các thư viện sau:

| Tên thư viện | Tên gói Pip cài đặt | Mục đích sử dụng |
|---|---|---|
| `Crypto` | **`pycryptodome`** | **BẮT BUỘC**: Cung cấp `Crypto.Cipher.AES`, `Crypto.Util.Padding`, `Crypto.Random`. *(⚠️ LƯU Ý: KHÔNG cài `pip install crypto` vì đó là gói khác gây xung đột!)* |
| `pandas` | **`pandas`** | Đọc và ghi dữ liệu bảng Excel / CSV |
| `pyxlsb` | **`pyxlsb`** | Engine đọc file Excel dạng nhị phân (`.xlsb`) |
| `tkinter` | *Có sẵn trong Python* | Thư viện giao diện người dùng Desktop (GUI) chuẩn của Python |

---

## 🛠️ 3. Cách Cài Đặt Thư Viện Khi Đổi Máy Hoặc Cài Mới

### Cách A: Click đúp file tự động
- Click đúp vào file **`CAI_DAT_THU_VIEN.bat`**. Script sẽ tự động dọn dẹp gói xung đột và cài đầy đủ các thư viện.

### Cách B: Dùng lệnh pip với file requirements.txt
```bash
cd "C:\Users\12953 Bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\Python Project\MyApp\File Encrypt"
pip uninstall -y crypto
pip install -r requirements.txt
```

### Cách C: Cài đặt trực tiếp từng gói
```bash
pip install pycryptodome pyxlsb pandas
```

---

## 🔒 4. Cơ Chế Mã Hóa & Lưu Khóa (File Encrypt)
- Khi mã hóa file hoặc thư mục:
  - Khóa AES 128-bit được sinh ngẫu nhiên và lưu tại: `key.key`.
  - Danh bạ ánh xạ tên file gốc và tên file mã hóa lưu tại: `data.txt`.
  - Các file mã hóa có đuôi: `.ecrb`.
- **Quan trọng**: Để giải mã thành công, thư mục giải mã phải chứa đầy đủ cả file mã hóa, file `key.key` và file `data.txt`.
