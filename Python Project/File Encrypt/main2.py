import os
import tkinter as tk
from tkinter import filedialog
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

class App:
    def __init__(self, root):
        self.root = root
        self.key = get_random_bytes(16)
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

    def encrypt_file(self):
        file_name = filedialog.askopenfilename()
        cipher = AES.new(self.key, AES.MODE_CBC)
        with open(file_name, 'rb') as f:
            original_data = f.read()
        enc_data = cipher.encrypt(pad(original_data, AES.block_size))
        with open(file_name + '.ecrb', 'wb') as f:
            f.write(cipher.iv)
            f.write(enc_data)

    def decrypt_file(self):
        file_name = filedialog.askopenfilename()
        with open(file_name, 'rb') as f:
            iv = f.read(16)
            enc_data = f.read()
        cipher = AES.new(self.key, AES.MODE_CBC, iv=iv)
        original_data = unpad(cipher.decrypt(enc_data), AES.block_size)
        with open(file_name.replace('.ecrb', ''), 'wb') as f:
            f.write(original_data)

    def encrypt_directory(self):
        dir_name = filedialog.askdirectory()
        for root, dirs, files in os.walk(dir_name):
            for file in files:
                self.encrypt_file(os.path.join(root, file))

    def decrypt_directory(self):
        dir_name = filedialog.askdirectory()
        for root, dirs, files in os.walk(dir_name):
            for file in files:
                if file.endswith('.ecrb'):
                    self.decrypt_file(os.path.join(root, file))

root = tk.Tk()
app = App(root)
root.mainloop()