import base64
import PyPDF2
import tkinter as tk
from tkinter import filedialog
import os
import glob
#pip install PyPDF2
# pip install 'PyPDF2<3.0'
def encrypt_pdf(input_file, output_file, password):
    # Đọc file PDF nguồn
    with open(input_file, 'rb') as file:
        pdf_reader = PyPDF2.PdfFileReader(file)
        pdf_writer = PyPDF2.PdfFileWriter()

        # Đọc từng trang trong file PDF
        for page_num in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_num)
            pdf_writer.addPage(page)

        # Mã hóa file PDF đã đọc
        encrypted_pdf = pdf_writer.encrypt(password)

        # Tạo file mới và ghi dữ liệu mã hóa vào file
        with open(output_file, 'wb') as encrypted_file:
            pdf_writer.write(encrypted_file)

def decrypt_pdf(input_file, output_file, password):
    # Đọc file mã hóa
    with open(input_file, 'rb') as encrypted_file:
        pdf_reader = PyPDF2.PdfFileReader(encrypted_file)

        # Giải mã file PDF
        if pdf_reader.isEncrypted:
            pdf_reader.decrypt(password)

        # Tạo file mới và ghi dữ liệu giải mã vào file
        with open(output_file, 'wb') as decrypted_file:
            pdf_writer = PyPDF2.PdfFileWriter()

            for page_num in range(pdf_reader.numPages):
                page = pdf_reader.getPage(page_num)
                pdf_writer.addPage(page)

            pdf_writer.write(decrypted_file)

def encrypt_folder():
    folder_path = filedialog.askdirectory()
    password = 'ktb@123321!'  # Mật khẩu để mã hóa

    # Lấy danh sách tất cả các file PDF trong thư mục
    pdf_files = glob.glob(os.path.join(folder_path, '*.pdf'))

    for pdf_file in pdf_files:
        # Tạo đường dẫn đầu ra cho file mã hóa (.ktb)
        output_file = os.path.splitext(pdf_file)[0] + '.ktb'

        # Mã hóa file PDF
        encrypt_pdf(pdf_file, output_file, password)

    result_label['text'] = 'Folder encrypted successfully: ' + folder_path

def decrypt_folder():
    folder_path = filedialog.askdirectory()
    password = 'ktb@123321!'  # Mật khẩu để giải mã

    # Lấy danh sách tất cả các file mã hóa (.ktb) trong thư mục
    encrypted_files = glob.glob(os.path.join(folder_path, '*.ktb'))

    for encrypted_file in encrypted_files:
        # Tạo đường dẫn đầu ra cho file giải mã (PDF)
        output_file = os.path.splitext(encrypted_file)[0] + '.pdf'

        # Giải mã file PDF
        decrypt_pdf(encrypted_file, output_file, password)

    result_label['text'] = 'Folder decrypted successfully: ' + folder_path

def open_file():
    file_path = filedialog.askopenfilename(filetypes=[('PDF Files', '*.pdf')])
    input_entry.delete(0, tk.END)
    input_entry.insert(tk.END, file_path)

def encrypt_file():
    input_file = input_entry.get()
    output_file = os.path.splitext(input_file)[0] + '.bkt'
    password = 'ktb@123321!'  # Mật khẩu để mã hóa
    encrypt_pdf(input_file, output_file, password)
    result_label['text'] = 'File encrypted successfully: ' + output_file

def decrypt_file():
    input_file = input_entry.get()
    output_file = os.path.splitext(input_file)[0] + '.pdf'
    password = 'ktb@123321!'  # Mật khẩu để giải mã
    decrypt_pdf(input_file, output_file, password)
    result_label['text'] = 'File decrypted successfully: ' + output_file

# Tạo giao diện ứng dụng
root = tk.Tk()
root.title('PDF Encryption App')

# Tạo các thành phần giao diện
input_label = tk.Label(root, text='Input File:')
input_label.pack()

input_entry = tk.Entry(root, width=50)
input_entry.pack()

open_button = tk.Button(root, text='Open File', command=open_file)
open_button.pack()

encrypt_button = tk.Button(root, text='Encrypt File', command=encrypt_file)
encrypt_button.pack()

decrypt_button = tk.Button(root, text='Decrypt File', command=decrypt_file)
decrypt_button.pack()

encrypt_folder_button = tk.Button(root, text='Encrypt Folder', command=encrypt_folder)
encrypt_folder_button.pack()

decrypt_folder_button = tk.Button(root, text='Decrypt Folder', command=decrypt_folder)
decrypt_folder_button.pack()

result_label = tk.Label(root, text='')
result_label.pack()

root.mainloop()