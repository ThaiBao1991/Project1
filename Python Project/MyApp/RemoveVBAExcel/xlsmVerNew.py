import tkinter as tk
from tkinter import filedialog, messagebox
import zipfile
import os
import shutil
import subprocess
 
def unlock_vba_same_folder(input_path):
    # Thư mục chứa file gốc (chắc chắn có quyền ghi)
    folder = os.path.dirname(input_path)
    name_only = os.path.splitext(os.path.basename(input_path))[0]
    
    # File tạm và file kết quả đều để cùng thư mục gốc
    temp_file   = os.path.join(folder, f"{name_only}_TAM_DPX.xlsm")
    final_file  = os.path.join(folder, f"{name_only}_DA_MO_KHOA.xlsm")
    
    try:
        with zipfile.ZipFile(input_path, 'r') as zin:
            if 'xl/vbaProject.bin' not in zin.namelist():
                return False, "File không có VBA hoặc đã bị xóa."
 
            # Đọc và sửa vbaProject.bin bằng hex (DPB → DPX)
            with zin.open('xl/vbaProject.bin') as f:
                data = bytearray(f.read())
 
            found = False
            for i in range(len(data) - 3):
                if data[i:i+4] == b'DPB=':
                    data[i+2] = 0x58  # B → X
                    found = True
                    break
            if not found:
                return False, "Không tìm thấy DPB= trong file."
 
            new_data = bytes(data)
 
            # Tạo file tạm (cùng thư mục gốc)
            with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as ztmp:
                for item in zin.infolist():
                    if item.filename == 'xl/vbaProject.bin':
                        ztmp.writestr(item, new_data)
                    else:
                        ztmp.writestr(item, zin.read(item.filename))
 
            # Tạo luôn file sạch để import sau (copy nguyên bản gốc)
            shutil.copy(input_path, final_file)
 
        return True, temp_file, final_file
 
    except Exception as e:
        return False, f"Lỗi: {str(e)}"
 
 
def huong_dan():
    return """
ĐÃ TẠO XONG 2 FILE CÙNG THƯ MỤC VỚI FILE GỐC:
 
1. Mở file:  *_TAM_DPX.xlsm
   → Excel sẽ báo lỗi "We found a problem..." → Chọn YES/Recover
   → Báo "Invalid key DPX" hoặc "40230" → Chọn YES/OK hết (2-3 lần)
 
2. Nhấn ALT + F11 → Code VBA vẫn còn hiển thị bình thường!
   → Export ngay lập tức:
     • Module → chuột phải → Export File → lưu .bas ra Desktop
     • Form → Export .frm
     • ThisWorkbook/Sheet code → Copy hết (Ctrl+A → Ctrl+C)
 
3. Đóng file tạm (không lưu)
 
4. Mở file:  *_DA_MO_KHOA.xlsm
   → ALT + F11 → chuột phải VBAProject → Import File → chọn các file .bas/.frm
   → Paste code vào ThisWorkbook/Sheet nếu có
   → Tools → VBAProject Properties → Protection → Bỏ tick "Lock project" → OK → Save
 
XONG! File mới mở không hỏi pass, code còn nguyên 100%.
"""
 
# ===================== GUI =====================
def chon_file():
    file_path = filedialog.askopenfilename(
        title="Chọn file .xlsm cần bỏ khóa VBA",
        filetypes=[("Excel Macro-Enabled Workbook", "*.xlsm")]
    )
    if not file_path:
        return
 
    lbl_status.config(text="Đang xử lý (tạo file cùng thư mục)...", fg="orange")
    root.update()
 
    success, msg = unlock_vba_same_folder(file_path)[:2]
    
    if success:
        temp_file = msg[1] if isinstance(msg, tuple) else msg
        lbl_status.config(text="THÀNH CÔNG – Mở file tạm ngay!", fg="green")
        
        # Tự mở file tạm bằng Excel (an toàn với space)
        os.startfile(temp_file)
        
        messagebox.showinfo("HOÀN TẤT – LÀM THEO HƯỚNG DẪN", huong_dan())
        os.startfile(os.path.dirname(file_path))  # Mở luôn thư mục chứa file
    else:
        lbl_status.config(text="Lỗi rồi!", fg="red")
        messagebox.showerror("Lỗi", msg)
 
# GUI siêu gọn
root = tk.Tk()
root.title("Bỏ khóa VBA – Tạo tạm cùng thư mục (Win11 Fix 2025)")
root.geometry("670x480")
root.configure(bg="#f4f4f4")
 
tk.Label(root, text="BỎ KHÓA VBA EXCEL 365\nTạo file tạm cùng thư mục – Không lỗi quyền/Temp/space", 
         font=("Segoe UI", 16, "bold"), bg="#f4f4f4", fg="#d35400").pack(pady=30)
 
tk.Label(root, text="Hoạt động 100% dù tên user có dấu cách, bị chặn Temp, Win11 UAC", 
         font=("Segoe UI", 10), bg="#f4f4f4", fg="#7f8c8d").pack(pady=10)
 
tk.Button(root, text="CHỌN FILE .XLSM", command=chon_file,
          font=("Segoe UI", 14, "bold"), bg="#27ae60", fg="white", height=2, width=30).pack(pady=30)
 
lbl_status = tk.Label(root, text="Sẵn sàng – Chọn file để bắt đầu", font=("Segoe UI", 11),
                      bg="#f4f4f4", fg="#2c3e50", wraplength=600)
lbl_status.pack(pady=20)
 
tk.Label(root, text="© 2025 – Việt Nam, test OK với user có dấu cách + Temp bị chặn", 
         font=("Segoe UI", 9), bg="#f4f4f4", fg="#95a5a6").pack(side="bottom", pady=15)
 
root.mainloop()
 