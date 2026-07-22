import os
import tkinter as tk
from tkinter import filedialog
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Key để mã hóa/décrypt dữ liệu (256-bit = 32 bytes)
key = b'0123456789abcdef0123456789abcdef'

def encrypt_file(file_path):
    output_file = file_path + '.enc'
    cipher = AES.new(key, AES.MODE_CBC)

    with open(file_path, 'rb') as file:
        plaintext = file.read()
        ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

        with open(output_file, 'wb') as encrypted_file:
            encrypted_file.write(cipher.iv)
            encrypted_file.write(ciphertext)

    return output_file

def decrypt_file(file_path):
    output_file = os.path.splitext(file_path)[0]
    cipher = AES.new(key, AES.MODE_CBC)

    with open(file_path, 'rb') as encrypted_file:
        iv = encrypted_file.read(AES.block_size)
        ciphertext = encrypted_file.read()
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

        with open(output_file, 'wb') as decrypted_file:
            decrypted_file.write(plaintext)

    return output_file

def choose_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        # Gọi hàm giải mã tệp tin
        decrypted_file = decrypt_file(file_path)
        print(f"Tệp tin đã giải mã: {decrypted_file}")
    else:
        print("Không chọn tệp tin đầu vào")

def encrypt_folder(folder_path):
    output_folder = folder_path + '_enc'

    # Tạo thư mục đầu ra
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Lặp qua tất cả các file trong thư mục
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)

            # Mã hóa từng file
            encrypted_file = encrypt_file(file_path)

            # Di chuyển file mã hóa đến thư mục đầu ra
            output_file_path = os.path.join(output_folder, os.path.relpath(encrypted_file, folder_path))
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            os.rename(encrypted_file, output_file_path)

    return output_folder

def decrypt_folder(folder_path):
    output_folder = os.path.splitext(folder_path)[0] + '_dec'

    # Tạo thư mục đầu ra
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Lặp qua tất cả các file trong thư mục
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)

            # Giải mã từng file
            decrypted_file = decrypt_file(file_path)

            # Di chuyển file giải mã đến thư mục đầu ra
            output_file_path = os.path.join(output_folder, os.path.relpath(decrypted_file, folder_path))
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            os.rename(decrypted_file, output_file_path)

    return output_folder

def open_file():
    file_path = filedialog.askopenfilename()
    input_entry.delete(0, tk.END)
    input_entry.insert(tk.END, file_path)

def compress_file():
    input_file = input_entry.get()
    encrypted_file = encrypt_file(input_file)
    result_label['text'] = 'File compressed successfully: ' + encrypted_file

def decompress_file():
    input_file = input_entry.get()
    decrypted_file = decrypt_file(input_file)
    result_label['text'] = 'File decompressed successfully: ' + decrypted_file

def open_folder():
    folder_path = filedialog.askdirectory()
    input_entry.delete(0, tk.END)
    input_entry.insert(tk.END, folder_path)

def compress_folder():
    folder_path = input_entry.get()
    encrypted_folder = encrypt_folder(folder_path)
    result_label['text'] = 'Folder compressed successfully: ' + encrypted_folder

def decompress_folder():
    folder_path = input_entry.get()
    decrypted_folder = decrypt_folder(folder_path)
    result_label['text'] = 'Folder decompressed successfully: ' + decrypted_folder

# Tạo giao diện ứng dụng
root = tk.Tk()
root.title('File Compression App')

# Tạo các thành phần giao diện
input_label = tk.Label(root, text='Input Path:')
input_label.pack()

input_entry = tk.Entry(root, width=50)
input_entry.pack()

open_file_button = tk.Button(root, text='Open File', command=open_file)
open_file_button.pack()

open_folder_button = tk.Button(root, text='Open Folder', command=open_folder)
open_folder_button.pack()

compress_file_button = tk.Button(root, text='Compress File', command=compress_file)
compress_file_button.pack()

decompress_file_button = tk.Button(root, text='Decompress File', command=decompress_file)
decompress_file_button.pack()

compress_folder_button = tk.Button(root, text='Compress Folder', command=compress_folder)
compress_folder_button.pack()

decompress_folder_button = tk.Button(root, text='Decompress Folder', command=decompress_folder)
decompress_folder_button.pack()

result_label = tk.Label(root, text='')
result_label.pack()

# Chạy ứng dụng
root.mainloop()