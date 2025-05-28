import tkinter as tk
from tkinter import filedialog, messagebox
from pikepdf import Pdf, Permissions, Encryption

def remove_restrictions(input_pdf, output_pdf):
    try:
        # Mở file PDF với pikepdf
        pdf = Pdf.open(input_pdf)
        
        # Nếu file không bị mã hóa, chỉ cần lưu lại mà không có hạn chế
        pdf.save(output_pdf, encryption=False)
        messagebox.showinfo("Thành công", f"File đã được mở khóa và lưu tại: {output_pdf}")
        return True
    except Exception as e:
        messagebox.showerror("Lỗi", f"File có thể bị mã hóa hoặc lỗi: {str(e)}")
        return False

def brute_force_pdf(input_pdf, output_pdf):
    try:
        pdf = Pdf.open(input_pdf)
        messagebox.showinfo("Thông tin", "File không bị mã hóa, đang mở khóa...")
        pdf.save(output_pdf, encryption=False)
        return True
    except:
        # Thử dò mật khẩu đơn giản (có thể mở rộng)
        passwords = ["", "1234", "password", "admin"]  # Danh sách mật khẩu thử
        for password in passwords:
            try:
                pdf = Pdf.open(input_pdf, password=password)
                pdf.save(output_pdf, encryption=False)
                messagebox.showinfo("Thành công", f"Mật khẩu tìm thấy: {password}\nFile đã được lưu tại: {output_pdf}")
                return True
            except:
                continue
        messagebox.showerror("Thất bại", "Không tìm thấy mật khẩu trong danh sách thử.")
        return False

def choose_file():
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if file_path:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)

def start_unlock():
    input_pdf = entry_file.get()
    if not input_pdf:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn file PDF trước!")
        return
    
    output_pdf = input_pdf.replace(".pdf", "_unlocked.pdf")
    if not brute_force_pdf(input_pdf, output_pdf):
        messagebox.showinfo("Thông báo", "Thử mở khóa mà không cần mật khẩu...")
        remove_restrictions(input_pdf, output_pdf)

# Tạo giao diện GUI
root = tk.Tk()
root.title("Mở khóa PDF với pikepdf")
root.geometry("400x200")

label_file = tk.Label(root, text="Chọn file PDF:")
label_file.pack(pady=10)

entry_file = tk.Entry(root, width=40)
entry_file.pack(pady=5)

btn_choose = tk.Button(root, text="Chọn file PDF", command=choose_file)
btn_choose.pack(pady=10)

btn_unlock = tk.Button(root, text="Mở khóa copy", command=start_unlock)
btn_unlock.pack(pady=10)

root.mainloop()