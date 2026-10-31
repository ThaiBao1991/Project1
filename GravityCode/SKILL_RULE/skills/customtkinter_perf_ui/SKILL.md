---
name: customtkinter-perf-ui
description: Best practices and design patterns for building lightning-fast, zero-lag Python desktop UIs with Tkinter and CustomTkinter (CTk). Eliminates UI thread freezes when rendering large lists/tables (>50 items), fixes the double-scroll empty background glitch, provides instant 60fps search filtering, and demonstrates seamless dark-mode C-engine Listbox/Treeview integration.
---

# CustomTkinter High-Performance UI & Anti-Lag Guidelines

Tài liệu quy chuẩn kỹ thuật nhằm tối ưu hóa hiệu năng, loại bỏ 100% độ trễ (Zero-Lag) cho các ứng dụng Python Desktop (CustomTkinter / Tkinter).

---

## 1. ⚠️ Quy Tắc Vàng: Tránh Quá Tải Canvas (Canvas Saturation Rule)

### Vấn đề gốc rễ
- Mỗi widget của CustomTkinter (`CTkFrame`, `CTkButton`, `CTkLabel`) đều chứa 1 hoặc nhiều đối tượng canvas nội bộ để vẽ bo góc, viền và xử lý hover events.
- Khi render một danh sách có hơn 50–100 items trong `CTkScrollableFrame`, việc tạo 200–600 widget Canvas cùng lúc sẽ **nghẽn hoàn toàn UI Thread**, làm ứng dụng bị đơ (freeze) từ 1.5s đến 4s.
- Mỗi lần người dùng gõ 1 ký tự vào ô tìm kiếm, nếu hủy và dựng lại hàng trăm canvas widget, giao diện sẽ giật lag nghiêm trọng.

### Giải pháp chuẩn mực: C-Engine Widgets
1. **Đối với Menu thả xuống / Popup danh sách chọn ngày / ComboBox tùy biến**:
   - Sử dụng `tk.Listbox` kết hợp `ttk.Scrollbar`.
   - `tk.Listbox` được viết bằng C ở tầng nhân, nạp 10.000 items chỉ mất `< 2ms` (nhanh gấp 1000 lần).
   - Tùy biến màu sắc Dark Mode sang trọng để tiệp màu 100% với CustomTkinter:
     ```python
     lb = tk.Listbox(
         parent,
         bg=C["sidebar"],
         fg=C["text"],
         selectbackground=C["accent"],
         selectforeground="#000000",
         activestyle="none",
         font=("Segoe UI", 11),
         highlightthickness=0,
         borderwidth=0,
         yscrollcommand=sb.set
     )
     ```
2. **Đối với Bảng dữ liệu nhiều cột (Lộ trình, Danh sách từ vựng, Quản lý)**:
   - Sử dụng `ttk.Treeview` với style Dark Mode tùy chỉnh (`Treeview` style).
   - Hỗ trợ phân cột, sắp xếp, click đúp chọn nhanh và render hàng nghìn dòng trong 0.005s.

---

## 2. 🛑 Quy Tắc Chống Lỗi Cuộn Lồng (Double-Scroll Glitch Prevention)

### Vấn đề
- Lồng một widget tự cuộn (`CTkTextbox`) vào bên trong một container cuộn khác (`CTkScrollableFrame`) với chiều cao cố định (`height=500`).
- **Hậu quả**:
  - Tạo ra một khoảng trống màu đen vô nghĩa phía dưới bài học khi nội dung ngắn hoặc khi phóng to cửa sổ.
  - Làm cắt lửng nửa chữ ở dòng cuối do bị tràn khung nhìn.

### Cách xử lý đúng
- **KHÔNG** bọc `CTkTextbox` trong `CTkScrollableFrame`.
- Đặt `CTkTextbox` trực tiếp vào khung cha:
  ```python
  self.lesson_text = ctk.CTkTextbox(
      cbody,
      fg_color=C["card"],
      text_color=C["text"],
      font=("Consolas", 14),
      wrap="word",
      corner_radius=10
  )
  self.lesson_text.pack(side="left", fill="both", expand=True, padx=(0, 8))
  ```

---

## 3. ⚡ Bộ Lọc Tìm Kiếm Thời Gian Thực (Live-Filter 60fps)

### Mẫu triển khai Listbox Filter tức thì:
```python
def _update_listbox(*_):
    lb.delete(0, "end")
    query = var_filter.get().strip().lower()
    filtered = []
    selected_idx = 0

    for item in all_items:
        day_num, full_label = item
        if query and query not in f"{day_num} {full_label}".lower():
            continue
        filtered.append(item)
        lb.insert("end", f"  {full_label}")
        if day_num == current_day:
            selected_idx = len(filtered) - 1

    if filtered:
        lb.selection_set(selected_idx)
        lb.see(selected_idx)
```

---

## 4. ⌨️ Bộ Phím Tắt Trải Nghiệm Người Dùng (UX Hotkeys)

Khi xây dựng Dropdown / Dialog tùy biến, luôn tích hợp:
- `▲` / `▼` (Down / Up Arrow): Di chuyển giữa các mục.
- `<Return>` / `<Double-Button-1>`: Chọn mục ngay lập tức.
- `<Escape>` / `<FocusOut>`: Đóng popup tự động khi nhấn Esc hoặc click ra ngoài.
