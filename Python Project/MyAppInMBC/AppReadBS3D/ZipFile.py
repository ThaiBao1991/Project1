import tkinter as tk
from tkinter import filedialog, messagebox
import zipfile
import os
try:
    import pyzipper  # Dùng cho trường hợp có mật khẩu
except ImportError:
    pyzipper = None

class ZipApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Super Zip Compressor")
        self.root.geometry("400x300")

        # Label tiêu đề
        tk.Label(root, text="Super Zip Compressor", font=("Arial", 14, "bold")).pack(pady=10)

        # Frame cho ô nhập mật khẩu
        self.pass_frame = tk.Frame(root)
        self.pass_frame.pack(pady=5)
        tk.Label(self.pass_frame, text="Password (optional):", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.pass_entry = tk.Entry(self.pass_frame, show="*", width=20)
        self.pass_entry.pack(side=tk.LEFT, padx=5)

        # Nút nén file
        self.compress_file_button = tk.Button(root, text="Compress File", command=self.compress_file, font=("Arial", 10))
        self.compress_file_button.pack(pady=10)

        # Nút nén thư mục
        self.compress_folder_button = tk.Button(root, text="Compress Folder", command=self.compress_folder, font=("Arial", 10))
        self.compress_folder_button.pack(pady=10)

        # Nút giải nén file ZIP
        self.decompress_button = tk.Button(root, text="Decompress ZIP", command=self.decompress_file, font=("Arial", 10))
        self.decompress_button.pack(pady=10)

        # Label hiển thị kết quả với wrap text
        self.result_label = tk.Label(root, text="", font=("Arial", 10), wraplength=350, justify="center")
        self.result_label.pack(pady=10)

        # Thông báo nếu pyzipper không được cài đặt
        if not pyzipper:
            self.result_label.config(text="Note: Install 'pyzipper' for password-protected ZIPs (pip install pyzipper)")

    def compress_file(self):
        # Chọn file để nén
        source_path = filedialog.askopenfilename(title="Select file to compress")
        if not source_path:
            return

        # Chọn nơi lưu file ZIP
        zip_path = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP files", "*.zip")], title="Save ZIP as")
        if not zip_path:
            return

        # Lấy mật khẩu từ ô nhập (nếu có)
        password = self.pass_entry.get() if self.pass_entry.get() else None

        try:
            if password:
                if not pyzipper:
                    raise ImportError("pyzipper is not installed. Cannot create password-protected ZIP.")
                with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zipf:
                    zipf.pwd = password.encode('utf-8')
                    zipf.write(source_path, os.path.basename(source_path))
                self.result_label.config(text=f"File compressed to {zip_path} with password (requires 7-Zip/WinRAR)!")
            else:
                with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                    zipf.write(source_path, os.path.basename(source_path))
                self.result_label.config(text=f"File compressed to {zip_path} without password (Windows compatible)!")
        except Exception as e:
            messagebox.showerror("Error", f"Compression failed: {str(e)}")

    def compress_folder(self):
        # Chọn thư mục để nén
        source_path = filedialog.askdirectory(title="Select folder to compress")
        if not source_path:
            return

        # Chọn nơi lưu file ZIP
        zip_path = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP files", "*.zip")], title="Save ZIP as")
        if not zip_path:
            return

        # Lấy mật khẩu từ ô nhập (nếu có)
        password = self.pass_entry.get() if self.pass_entry.get() else None

        try:
            if password:
                if not pyzipper:
                    raise ImportError("pyzipper is not installed. Cannot create password-protected ZIP.")
                with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zipf:
                    zipf.pwd = password.encode('utf-8')
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, source_path)
                            zipf.write(file_path, arcname)
                self.result_label.config(text=f"Folder compressed to {zip_path} with password (requires 7-Zip/WinRAR)!")
            else:
                with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, source_path)
                            zipf.write(file_path, arcname)
                self.result_label.config(text=f"Folder compressed to {zip_path} without password (Windows compatible)!")
        except Exception as e:
            messagebox.showerror("Error", f"Compression failed: {str(e)}")

    def decompress_file(self):
        # Chọn file ZIP để giải nén
        zip_path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")], title="Select ZIP file")
        if not zip_path:
            return

        # Chọn thư mục đích để giải nén
        extract_path = filedialog.askdirectory(title="Select extract destination")
        if not extract_path:
            return

        # Lấy mật khẩu từ ô nhập (nếu có)
        password = self.pass_entry.get() if self.pass_entry.get() else None

        try:
            if pyzipper and password:
                try:
                    with pyzipper.AESZipFile(zip_path, 'r') as zipf:
                        zipf.pwd = password.encode('utf-8')
                        zipf.extractall(extract_path)
                    self.result_label.config(text=f"Decompressed successfully to {extract_path} with password!")
                    return
                except RuntimeError:
                    pass

            with zipfile.ZipFile(zip_path, 'r') as zipf:
                if password:
                    zipf.setpassword(password.encode('utf-8'))
                zipf.extractall(extract_path)
            self.result_label.config(text=f"Decompressed successfully to {extract_path}!")
        except Exception as e:
            messagebox.showerror("Error", f"Decompression failed: {str(e)} (Wrong password or corrupted file?)")

if __name__ == "__main__":
    root = tk.Tk()
    app = ZipApp(root)
    root.mainloop()