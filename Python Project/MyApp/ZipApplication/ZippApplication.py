import os
import pyzipper
import tkinter as tk
from tkinter import filedialog, messagebox

def compress_file(file_path, password=None):
    zip_file_name = os.path.basename(file_path)  # Lấy tên thư mục hoặc tên file
    zip_file_path = zip_file_name + '.zip'

    with pyzipper.AESZipFile(zip_file_path, 'w', compression=pyzipper.ZIP_LZMA, encryption=None) as zip_file:
        if password:
            zip_file.setpassword(password.encode())

        if os.path.isfile(file_path):
            zip_file.write(file_path, os.path.basename(file_path))
        else:
            for folder_name, subfolders, filenames in os.walk(file_path):
                for filename in filenames:
                    file_path = os.path.join(folder_name, filename)
                    if os.path.exists(file_path):
                        arcname = os.path.relpath(file_path, file_path)
                        zip_file.write(file_path, arcname)
                        if password:
                            zip_file.setpassword(password.encode())

    return zip_file_path
 
def decompress_file(zip_file_path, password=None):
    file_path = os.path.splitext(zip_file_path)[0]
    
    with pyzipper.AESZipFile(zip_file_path, 'r') as zip_file:
        if password:
            zip_file.setpassword(password.encode())
        
        for zip_info in zip_file.infolist():
            if password:
                zip_file.setpassword(password.encode())
            zip_file.extract(zip_info, file_path, pwd=zip_file.getpassword())
    
    return file_path
 
def browse_file():
    file_path = filedialog.askopenfilename()
    file_entry.delete(0, tk.END)
    file_entry.insert(0, file_path)
 
def browse_folder():
    folder_path = filedialog.askdirectory()
    file_entry.delete(0, tk.END)
    file_entry.insert(0, folder_path)
 
def compress():
    file_path = file_entry.get()
    password = password_entry.get()
    
    if not file_path:
        messagebox.showerror("Lỗi", "Vui lòng chọn file hoặc thư mục cần nén.")
        return
    
    try:
        print("check2")
        zip_file_path = compress_file(file_path, password)
        print("check1")
        messagebox.showinfo("Thành công", f"File zip đã được tạo:\n{zip_file_path}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi nén file: {str(e)}")
 
def decompress():
    zip_file_path = file_entry.get()
    password = password_entry.get()
    
    if not zip_file_path:
        messagebox.showerror("Lỗi", "Vui lòng chọn file zip cần giải nén.")
        return
    
    try:
        decompressed_file_path = decompress_file(zip_file_path, password)

        messagebox.showinfo("Thành công", f"File đã được giải nén:\n{decompressed_file_path}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi giải nén file: {str(e)}")
 
# Tạo cửa sổ ứng dụng
window = tk.Tk()
window.title("Ứng dụng Nén/Giải nén File")
window.geometry("400x200")
 
# Tạo các thành phần trong giao diện
file_label = tk.Label(window, text="Chọn file hoặc thư mục:")
file_label.pack()
 
file_entry = tk.Entry(window, width=50)
file_entry.pack()
 
browse_file_button = tk.Button(window, text="Chọn file", command=browse_file)
browse_file_button.pack()
 
browse_folder_button = tk.Button(window, text="Chọn thư mục", command=browse_folder)
browse_folder_button.pack()
 
password_label = tk.Label(window, text="Nhập mật khẩu:")
password_label.pack()
 
password_entry = tk.Entry(window, width=50, show="*")
password_entry.pack()
 
compress_button = tk.Button(window, text="Nén", command=compress)
compress_button.pack()
 
decompress_button = tk.Button(window, text="Giải nén", command=decompress)
decompress_button.pack()
 
# Bắt đầu vòng lặp chờ sự kiện
window.mainloop()