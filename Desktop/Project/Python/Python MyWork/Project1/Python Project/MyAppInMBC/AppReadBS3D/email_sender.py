import tkinter as tk

class EmailSender:
    def __init__(self, root, back_to_menu_callback):
        self.root = root
        self.back_to_menu = back_to_menu_callback

        tk.Label(root, text="Gửi email tự động", font=("Arial", 14, "bold")).pack(pady=20)
        tk.Label(root, text="Tính năng đang phát triển...", font=("Arial", 10, "italic")).pack(pady=10)
        tk.Button(root, text="Quay lại menu", command=self.back_to_menu, font=("Arial", 10), bg="gray", fg="white").pack(pady=20)