import tkinter as tk
from tkinter import messagebox
import json
import random
import datetime
import os

VOCAB_FILE = "english_vocab.json"

# Khởi tạo file nếu chưa tồn tại
def initialize_vocab_file():
    if not os.path.exists(VOCAB_FILE):
        with open(VOCAB_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

# Đọc từ vựng
def load_vocab():
    initialize_vocab_file()
    with open(VOCAB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Lưu từ vựng
def save_vocab(vocab):
    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=4)

# Thêm từ vựng
def add_vocab_window(parent):
    add_window = tk.Toplevel(parent)
    add_window.title("Thêm từ vựng tiếng Anh")
    add_window.geometry("300x200")

    tk.Label(add_window, text="Từ tiếng Anh:").pack(pady=5)
    eng_entry = tk.Entry(add_window, width=30)
    eng_entry.pack()

    tk.Label(add_window, text="Nghĩa tiếng Việt:").pack(pady=5)
    viet_entry = tk.Entry(add_window, width=30)
    viet_entry.pack()

    def save_new_word():
        eng = eng_entry.get().strip().lower()
        viet = viet_entry.get().strip()
        if not eng or not viet:
            messagebox.showwarning("Lỗi", "Vui lòng nhập đầy đủ!")
            return
        vocab = load_vocab()
        if eng in vocab:
            messagebox.showinfo("Thông báo", "Từ này đã tồn tại!")
        else:
            vocab[eng] = {"meaning": viet, "correct_count": 0, "completed_date": None}
            save_vocab(vocab)
            messagebox.showinfo("Thành công", f"Đã thêm: {eng} - {viet}")
            eng_entry.delete(0, tk.END)
            viet_entry.delete(0, tk.END)

    tk.Button(add_window, text="Lưu", command=save_new_word).pack(pady=10)
    tk.Button(add_window, text="Quay lại", command=add_window.destroy).pack(pady=5)

    # Bind phím Enter để lưu và Esc để quay lại
    add_window.bind("<Return>", lambda event: save_new_word())
    add_window.bind("<Escape>", lambda event: add_window.destroy())

# Kiểm tra từ vựng
def test_vocab_window(parent):
    vocab = load_vocab()
    if not vocab:
        messagebox.showinfo("Thông báo", "Chưa có từ vựng nào!")
        return

    test_window = tk.Toplevel(parent)
    test_window.title("Kiểm tra từ vựng")
    test_window.geometry("300x250")

    today = datetime.datetime.now().date()
    available_words = {k: v for k, v in vocab.items() if v["correct_count"] < 20 or 
                       (v["completed_date"] and (today - datetime.datetime.strptime(v["completed_date"], "%Y-%m-%d").date()).days >= 20)}

    if not available_words:
        messagebox.showinfo("Thông báo", "Không có từ nào để kiểm tra!")
        test_window.destroy()
        return

    # Biến để lưu từ hiện tại
    current_word = random.choice(list(available_words.keys()))
    current_data = vocab[current_word]

    meaning_label = tk.Label(test_window, text=f"Nghĩa: {current_data['meaning']}", font=("Arial", 12))
    meaning_label.pack(pady=10)

    status_label = tk.Label(test_window, text=f"Số lần đúng: {current_data['correct_count']}/20")
    status_label.pack()

    answer_entry = tk.Entry(test_window, width=30)
    answer_entry.pack(pady=10)
    answer_entry.focus_set()  # Đặt con trỏ vào ô nhập ngay từ đầu

    def check_answer():
        nonlocal current_word, current_data, available_words
        answer = answer_entry.get().strip().lower()
        if answer == current_word:
            current_data["correct_count"] += 1
            if current_data["correct_count"] >= 20:
                current_data["completed_date"] = today.strftime("%Y-%m-%d")
                messagebox.showinfo("Hoàn thành", f"Đã hoàn thành '{current_word}'. Sẽ xuất hiện lại sau 20 ngày.")
                # Không thoát, tiếp tục với từ khác
        else:
            if current_data["correct_count"] > 0:
                current_data["correct_count"] -= 1
            messagebox.showerror("Sai", f"Đáp án đúng: {current_word}. Số lần đúng còn: {current_data['correct_count']}")

        # Cập nhật từ vựng
        vocab[current_word] = current_data
        save_vocab(vocab)

        # Lấy danh sách từ còn lại
        available_words = {k: v for k, v in vocab.items() if v["correct_count"] < 20 or 
                           (v["completed_date"] and (today - datetime.datetime.strptime(v["completed_date"], "%Y-%m-%d").date()).days >= 20)}
        if not available_words:
            messagebox.showinfo("Thông báo", "Không còn từ nào để kiểm tra!")
            test_window.destroy()
            return

        # Chọn từ mới ngẫu nhiên
        current_word = random.choice(list(available_words.keys()))
        current_data = vocab[current_word]
        
        # Cập nhật giao diện
        meaning_label.config(text=f"Nghĩa: {current_data['meaning']}")
        status_label.config(text=f"Số lần đúng: {current_data['correct_count']}/20")
        answer_entry.delete(0, tk.END)

    tk.Button(test_window, text="Kiểm tra", command=check_answer).pack(pady=10)
    tk.Button(test_window, text="Quay lại", command=test_window.destroy).pack(pady=5)

    # Bind phím Enter để kiểm tra và Esc để quay lại
    test_window.bind("<Return>", lambda event: check_answer())
    test_window.bind("<Escape>", lambda event: test_window.destroy())

# Menu tiếng Anh
def english_menu(parent):
    root = tk.Toplevel(parent)
    root.title("Ôn tiếng Anh")
    root.geometry("300x200")

    tk.Label(root, text="Ôn tập tiếng Anh", font=("Arial", 14)).pack(pady=20)
    tk.Button(root, text="Thêm từ vựng", command=lambda: add_vocab_window(root), width=20).pack(pady=5)
    tk.Button(root, text="Kiểm tra từ vựng", command=lambda: test_vocab_window(root), width=20).pack(pady=5)
    tk.Button(root, text="Quay lại", command=lambda: [root.destroy(), parent.deiconify()], width=20).pack(pady=5)

    # Bind Esc để quay lại trong menu chính của tiếng Anh
    root.bind("<Escape>", lambda event: [root.destroy(), parent.deiconify()])