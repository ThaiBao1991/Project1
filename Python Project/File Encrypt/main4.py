import os
import tkinter as tk
from tkinter import filedialog
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

class App:
    def __init__(self, root):
        self.root = root
        self.create_widgets()

    def create_widgets(self):
        self.encrypt_file_button = tk.Button(self.root, text="Mã hóa file", command=self.encrypt_file)
        self.encrypt_file_button.pack()

        self.decrypt_file_button = tk.Button(self.root, text="Giải mã file", command=self.decrypt_file)
        self.decrypt_file_button.pack()

        self.encrypt_dir_button = tk.Button(self.root, text="Mã hóa thư mục", command=self.encrypt_directory)
        self.encrypt_dir_button.pack()

        self.decrypt_dir_button = tk.Button(self.root, text="Giải mã thư mục", command=self.decrypt_directory)
        self.decrypt_dir_button.pack()

    def encrypt_file(self, file_name, key, output_dir, file_dict):
        cipher = AES.new(key, AES.MODE_CBC)
        with open(file_name, 'rb') as f:
            original_data = f.read()
        enc_data = cipher.encrypt(pad(original_data, AES.block_size))
        encrypted_file_name = os.path.join(output_dir, str(len(file_dict)) + '.ecrb')
        with open(encrypted_file_name, 'wb') as f:
            f.write(cipher.iv)
            f.write(enc_data)
        file_dict[encrypted_file_name] = os.path.basename(file_name)

    def decrypt_file(self, file_name, key, output_dir, file_dict):
        with open(file_name, 'rb') as f:
            iv = f.read(16)
            enc_data = f.read()
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        original_data = unpad(cipher.decrypt(enc_data), AES.block_size)
        decrypted_file_name = os.path.join(output_dir, file_dict[file_name])
        with open(decrypted_file_name, 'wb') as f:
            f.write(original_data)

    def encrypt_directory(self):
        dir_name = filedialog.askdirectory()
        key = get_random_bytes(16)
        with open(os.path.join(dir_name, 'key.key'), 'wb') as key_file:
            key_file.write(key)
        file_dict = {}
        for root, dirs, files in os.walk(dir_name):
            for file in files:
                self.encrypt_file(os.path.join(root, file), key, dir_name, file_dict)
        with open(os.path.join(dir_name, 'data.txt'), 'w') as f:
            f.write(str(file_dict))

    def decrypt_directory(self):
        dir_name = filedialog.askdirectory()
        with open(os.path.join(dir_name, 'key.key'), 'rb') as key_file:
            key = key_file.read()
        with open(os.path.join(dir_name, 'data.txt'), 'r') as f:
            file_dict = eval(f.read())
        for root, dirs, files in os.walk(dir_name):
            for file in files:
                if file.endswith('.ecrb'):
                    self.decrypt_file(os.path.join(root, file), key, dir_name, file_dict)

root = tk.Tk()
app = App(root)
root.mainloop()