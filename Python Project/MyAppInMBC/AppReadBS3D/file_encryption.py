import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import json
import ast

class FileEncryption:
    def __init__(self, root, back_to_menu_callback):
        self.root = root
        self.back_to_menu = back_to_menu_callback

        tk.Label(self.root, text="Mã hóa và giải mã file", font=("Arial", 14, "bold")).pack(pady=10)

        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        self.encrypt_file_button = tk.Button(frame, text="Mã hóa file", command=self.encrypt_file, font=("Arial", 10))
        self.encrypt_file_button.grid(row=0, column=0, padx=5, pady=5)

        self.decrypt_file_button = tk.Button(frame, text="Giải mã file", command=self.decrypt_file, font=("Arial", 10))
        self.decrypt_file_button.grid(row=0, column=1, padx=5, pady=5)

        self.encrypt_dir_button = tk.Button(frame, text="Mã hóa thư mục", command=self.encrypt_directory, font=("Arial", 10))
        self.encrypt_dir_button.grid(row=1, column=0, padx=5, pady=5)

        self.decrypt_dir_button = tk.Button(frame, text="Giải mã thư mục", command=self.decrypt_directory, font=("Arial", 10))
        self.decrypt_dir_button.grid(row=1, column=1, padx=5, pady=5)

        self.result_tree = ttk.Treeview(self.root, columns=("File", "Kết quả"), show="headings", height=8)
        self.result_tree.heading("File", text="File")
        self.result_tree.heading("Kết quả", text="Kết quả")
        self.result_tree.pack(fill=tk.BOTH, expand=True)

        tk.Button(self.root, text="Quay lại menu", command=self.back_to_menu, font=("Arial", 10), bg="gray", fg="white").pack(pady=10)

    def encrypt_file(self):
        try:
            file_name = filedialog.askopenfilename()
            if not file_name:
                return

            self.result_tree.delete(*self.result_tree.get_children())

            key = get_random_bytes(16)
            output_dir = os.path.dirname(file_name)
            key_path = os.path.join(output_dir, 'key.key')
            
            with open(key_path, 'wb') as key_file:
                key_file.write(key)
            
            file_dict = {}
            self.encrypt_file_helper(file_name, key, output_dir, file_dict)
            
            data_path = os.path.join(output_dir, 'data.txt')
            with open(data_path, 'w') as f:
                for original, encrypted in file_dict.items():
                    f.write(f"{original}:{encrypted}\n")
            
            file_basename = os.path.basename(file_name)
            self.result_tree.insert("", "end", values=(file_basename, "Hoàn thành"))
        
        except Exception as e:
            self.result_tree.insert("", "end", values=("Lỗi", f"Lỗi mã hóa: {str(e)}"))

    def encrypt_file_helper(self, file_name, key, output_dir, file_dict):
        cipher = AES.new(key, AES.MODE_CBC)
        with open(file_name, 'rb') as f:
            original_data = f.read()
        enc_data = cipher.encrypt(pad(original_data, AES.block_size))
        encrypted_file_name = os.path.join(output_dir, str(len(file_dict)) + '.ecrb')
        with open(encrypted_file_name, 'wb') as f:
            f.write(cipher.iv)
            f.write(enc_data)
        file_dict[os.path.basename(file_name)] = os.path.basename(encrypted_file_name)

    def decrypt_file(self):
        try:
            file_name = filedialog.askopenfilename()
            if not file_name:
                return

            self.result_tree.delete(*self.result_tree.get_children())

            output_dir = os.path.dirname(file_name)
            key_path = os.path.join(output_dir, 'key.key')
            data_path = os.path.join(output_dir, 'data.txt')
            
            with open(key_path, 'rb') as key_file:
                key = key_file.read()
            
            file_dict = self.load_file_dict(data_path)
            original_name = file_dict.get(os.path.basename(file_name))
            
            if not original_name:
                raise ValueError("Không tìm thấy tên file gốc trong data.txt")
            
            self.decrypt_file_helper(file_name, key, output_dir, original_name)
            
            self.result_tree.insert("", "end", values=(os.path.basename(file_name), "Hoàn thành"))
        
        except Exception as e:
            self.result_tree.insert("", "end", values=("Lỗi", f"Lỗi giải mã: {str(e)}"))

    def decrypt_file_helper(self, file_name, key, output_dir, original_file_name):
        with open(file_name, 'rb') as f:
            iv = f.read(16)
            enc_data = f.read()
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        original_data = unpad(cipher.decrypt(enc_data), AES.block_size)
        decrypted_path = os.path.join(output_dir, original_file_name)
        with open(decrypted_path, 'wb') as f:
            f.write(original_data)

    def load_file_dict(self, file_path):
        file_dict = {}
        with open(file_path, 'r') as f:
            data = f.read()
            if '{' in data:  # Dạng từ điển
                try:
                    file_data = ast.literal_eval(data)
                    if isinstance(file_data, dict):
                        file_dict = file_data
                except ValueError:
                    print("Lỗi: Định dạng dữ liệu không hợp lệ trong data.txt")
            else:  # Dạng key-value đơn giản
                try:
                    lines = data.split('\n')
                    for line in lines:
                        if line.strip():
                            key, value = line.split(':')
                            file_dict[value.strip()] = key.strip()
                except ValueError:
                    print("Lỗi: Định dạng dữ liệu không hợp lệ trong data.txt")
        return file_dict

    def encrypt_directory(self):
        try:
            dir_name = filedialog.askdirectory()
            if not dir_name:
                return

            self.result_tree.delete(*self.result_tree.get_children())
            key = get_random_bytes(16)
            key_path = os.path.join(dir_name, 'key.key')
            with open(key_path, 'wb') as key_file:
                key_file.write(key)

            file_dict = {}
            file_counter = 0
            for root, dirs, files in os.walk(dir_name):
                for file in files:
                    if file != 'key.key' and file != 'data.txt':
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, dir_name)
                        encrypted_file_name = f"{file_counter}.ecrb"
                        encrypted_file_path = os.path.join(dir_name, encrypted_file_name)

                        cipher = AES.new(key, AES.MODE_CBC)
                        with open(file_path, 'rb') as f:
                            original_data = f.read()
                        enc_data = cipher.encrypt(pad(original_data, AES.block_size))
                        with open(encrypted_file_path, 'wb') as f:
                            f.write(cipher.iv)
                            f.write(enc_data)

                        file_dict[relative_path] = encrypted_file_name
                        self.result_tree.insert("", "end", values=(file, "Hoàn thành"))
                        file_counter += 1

            data_path = os.path.join(dir_name, 'data.txt')
            with open(data_path, 'w') as f:
                json.dump(file_dict, f)

            self.result_tree.insert("", "end", values=("Tổng cộng", f"Đã mã hóa {file_counter} file"))
        except Exception as e:
            self.result_tree.insert("", "end", values=("Lỗi", f"Lỗi mã hóa thư mục: {str(e)}"))

    def decrypt_directory(self):
        try:
            dir_name = filedialog.askdirectory()
            if not dir_name:
                return

            self.result_tree.delete(*self.result_tree.get_children())
            key_path = os.path.join(dir_name, 'key.key')
            data_path = os.path.join(dir_name, 'data.txt')

            with open(key_path, 'rb') as key_file:
                key = key_file.read()

            with open(data_path, 'r') as f:
                file_dict = json.load(f)

            for original_path, encrypted_file in file_dict.items():
                encrypted_file_path = os.path.join(dir_name, encrypted_file)
                if os.path.exists(encrypted_file_path):
                    with open(encrypted_file_path, 'rb') as f:
                        iv = f.read(16)
                        enc_data = f.read()
                    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
                    original_data = unpad(cipher.decrypt(enc_data), AES.block_size)

                    decrypted_file_path = os.path.join(dir_name, original_path)
                    os.makedirs(os.path.dirname(decrypted_file_path), exist_ok=True)
                    with open(decrypted_file_path, 'wb') as f:
                        f.write(original_data)
                    self.result_tree.insert("", "end", values=(encrypted_file, "Hoàn thành"))
                else:
                    self.result_tree.insert("", "end", values=(encrypted_file, "Không tìm thấy file mã hóa"))

            self.result_tree.insert("", "end", values=("Tổng cộng", f"Đã giải mã {len(file_dict)} file"))
        except Exception as e:
            self.result_tree.insert("", "end", values=("Lỗi", f"Lỗi giải mã thư mục: {str(e)}"))