import tkinter as tk
from tkinter import messagebox
import English
import Japan
import Chinese

def open_english():
    root.withdraw()  # Ẩn cửa sổ chính
    English.english_menu(root)

def open_japan():
    root.withdraw()
    Japan.japan_menu(root)

def open_chinese():
    root.withdraw()
    Chinese.chinese_menu(root)

def exit_program():
    root.quit()  # Thoát hoàn toàn chương trình

# Tạo cửa sổ chính
root = tk.Tk()
root.title("Chương trình ôn từ vựng")
root.geometry("300x200")

# Tiêu đề
title_label = tk.Label(root, text="Chọn ngôn ngữ để ôn", font=("Arial", 14))
title_label.pack(pady=20)

# Nút chọn ngôn ngữ
btn_english = tk.Button(root, text="Tiếng Anh", command=open_english, width=20)
btn_english.pack(pady=5)

btn_japan = tk.Button(root, text="Tiếng Nhật", command=open_japan, width=20)
btn_japan.pack(pady=5)

btn_chinese = tk.Button(root, text="Tiếng Trung", command=open_chinese, width=20)
btn_chinese.pack(pady=5)

btn_exit = tk.Button(root, text="Thoát", command=exit_program, width=20)
btn_exit.pack(pady=5)

# Bind Esc để thoát hoàn toàn
root.bind("<Escape>", lambda event: root.quit())

# Chạy chương trình
root.mainloop()

# cd "C:\Project\StudyVocabulary"
# "C:\Users\12953 bao\AppData\Roaming\Python\Python312\Scripts\pyinstaller.exe" --onefile --noconsole --add-data "C:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\english_vocab.json;." --add-data "directory_treemap.png;." --add-data "tree.md;." main.py