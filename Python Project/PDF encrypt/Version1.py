import base64
import PyPDF2
import tkinter as tk
from tkinter import filedialog
import os

def encrypt_pdf(input_file, output_file):
    # Đọc file PDF nguồn
    with open(input_file, 'rb') as file:
        pdf_reader = PyPDF2.PdfFileReader(file)
        pdf_writer = PyPDF2.PdfFileWriter()

        # Đọc từng trang trong file PDF
        for page_num in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_num)
            pdf_writer.addPage(page)

        # Mã hóa file PDF đã đọc
        encrypted_pdf = pdf_writer.encrypt('ktb1199122')

        # Tạo file mới và ghi dữ liệu mã hóa vào file
        with open(output_file, 'wb') as encrypted_file:
            pdf_writer.write(encrypted_file)

def decrypt_pdf(input_file, output_file):
    # Đọc file mã hóa
    with open(input_file, 'rb') as encrypted_file:
        pdf_reader = PyPDF2.PdfFileReader(encrypted_file)

        # Giải mã file PDF
        if pdf_reader.isEncrypted:
            pdf_reader.decrypt('password')

        # Tạo file mới và ghi dữ liệu giải mã vào file
        with open(output_file, 'wb') as decrypted_file:
            pdf_writer = PyPDF2.PdfFileWriter()

            for page_num in range(pdf_reader.numPages):
                page = pdf_reader.getPage(page_num)
                pdf_writer.addPage(page)

            pdf_writer.write(decrypted_file)

def open_file():
    file_path = filedialog.askopenfilename(filetypes=[('PDF Files', '*.pdf')])
    input_entry.delete(0, tk.END)
    input_entry.insert(tk.END, file_path)

def encrypt_file():
    input_file = input_entry.get()
    output_file = os.path.splitext(input_file)[0] + '.bkt'
    encrypt_pdf(input_file, output_file)
    result_label['text'] = 'File encrypted successfully: ' + output_file

def decrypt_file():
    input_file = input_entry.get()
    output_file = os.path.splitext(input_file)[0] + '.pdf'
    decrypt_pdf(input_file, output_file)
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

result_label = tk.Label(root, text='')
result_label.pack()

root.mainloop()