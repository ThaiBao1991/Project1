import tkinter as tk
from tkinter import messagebox

def japan_menu(parent):
    root = tk.Toplevel(parent)
    root.title("Ôn tiếng Nhật")
    root.geometry("300x200")

    tk.Label(root, text="Ôn tập tiếng Nhật", font=("Arial", 14)).pack(pady=20)
    tk.Label(root, text="Chức năng đang phát triển!").pack(pady=10)
    tk.Button(root, text="Quay lại", command=lambda: [root.destroy(), parent.deiconify()], width=20).pack(pady=5)

    root.bind("<Escape>", lambda event: [root.destroy(), parent.deiconify()])