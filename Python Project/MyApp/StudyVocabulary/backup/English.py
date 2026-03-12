import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
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
    add_window.geometry("600x400")

    tk.Label(add_window, text="Từ tiếng Anh:").pack(pady=5)
    eng_entry = tk.Entry(add_window, width=30)
    eng_entry.pack()
    eng_entry.focus_set()

    tk.Label(add_window, text="Nghĩa tiếng Việt:").pack(pady=5)
    viet_entry = tk.Entry(add_window, width=30)
    viet_entry.pack()

    vocab = load_vocab()
    count_label = tk.Label(add_window, text=f"Tổng số từ: {len(vocab)}")
    count_label.pack(pady=5)

    tree_frame = tk.Frame(add_window)
    tree_frame.pack(pady=10, fill=tk.BOTH, expand=True)
    tree = ttk.Treeview(tree_frame, columns=("English", "Vietnamese", "CorrectCount", "CompletedDate"), show="headings", height=10)
    tree.heading("English", text="Từ tiếng Anh")
    tree.heading("Vietnamese", text="Nghĩa tiếng Việt")
    tree.heading("CorrectCount", text="Số lần đúng")
    tree.heading("CompletedDate", text="Ngày hoàn thành")
    tree.column("English", width=150)
    tree.column("Vietnamese", width=150)
    tree.column("CorrectCount", width=100)
    tree.column("CompletedDate", width=150)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.configure(yscrollcommand=scrollbar.set)

    def update_tree_and_count(filter_text=""):
        for item in tree.get_children():
            tree.delete(item)
        vocab = load_vocab()
        for eng, data in vocab.items():
            if filter_text.lower() in eng.lower():
                tree.insert("", tk.END, values=(eng, data["meaning"], data["correct_count"], data["completed_date"]))
        count_label.config(text=f"Tổng số từ: {len(vocab)}")

    update_tree_and_count()

    def filter_vocab(event):
        filter_text = eng_entry.get().strip()
        update_tree_and_count(filter_text)

    eng_entry.bind("<KeyRelease>", filter_vocab)

    def save_new_word():
        eng = eng_entry.get().strip().lower()
        viet = viet_entry.get().strip()
        if not eng or not viet:
            messagebox.showwarning("Lỗi", "Vui lòng nhập đầy đủ!")
            eng_entry.focus_set()
            return
        vocab = load_vocab()
        if eng in vocab:
            messagebox.showinfo("Thông báo", "Từ này đã tồn tại!")
            eng_entry.focus_set()
        else:
            vocab[eng] = {"meaning": viet, "correct_count": 0, "completed_date": None}
            save_vocab(vocab)
            messagebox.showinfo("Thành công", f"Đã thêm: {eng} - {viet}")
            eng_entry.delete(0, tk.END)
            viet_entry.delete(0, tk.END)
            update_tree_and_count()
            eng_entry.focus_set()

    def edit_vocab(event):
        selected_item = tree.selection()
        if not selected_item:
            return
        eng = tree.item(selected_item)["values"][0]
        vocab = load_vocab()
        data = vocab[eng]

        edit_window = tk.Toplevel(add_window)
        edit_window.title(f"Sửa thông tin: {eng}")
        edit_window.geometry("300x200")

        tk.Label(edit_window, text="Nghĩa tiếng Việt:").pack(pady=5)
        viet_edit = tk.Entry(edit_window, width=30)
        viet_edit.insert(0, data["meaning"])
        viet_edit.pack()

        tk.Label(edit_window, text="Số lần đúng:").pack(pady=5)
        count_edit = tk.Entry(edit_window, width=30)
        count_edit.insert(0, data["correct_count"])
        count_edit.pack()

        tk.Label(edit_window, text="Ngày hoàn thành (YYYY-MM-DD):").pack(pady=5)
        date_edit = tk.Entry(edit_window, width=30)
        date_edit.insert(0, data["completed_date"] if data["completed_date"] else "")
        date_edit.pack()

        def save_edit():
            try:
                new_count = int(count_edit.get().strip())
                if new_count < 0 or new_count > 20:
                    raise ValueError("Số lần đúng phải từ 0 đến 20!")
                new_date = date_edit.get().strip()
                if new_date and not datetime.datetime.strptime(new_date, "%Y-%m-%d"):
                    raise ValueError("Ngày không đúng định dạng YYYY-MM-DD!")
                
                vocab[eng] = {
                    "meaning": viet_edit.get().strip(),
                    "correct_count": new_count,
                    "completed_date": new_date if new_date else None
                }
                save_vocab(vocab)
                update_tree_and_count()
                edit_window.destroy()
            except ValueError as e:
                messagebox.showerror("Lỗi", str(e))
                count_edit.focus_set()

        tk.Button(edit_window, text="Lưu", command=save_edit).pack(pady=10)
        tk.Button(edit_window, text="Hủy", command=edit_window.destroy).pack(pady=5)
        edit_window.bind("<Return>", lambda event: save_edit())
        edit_window.bind("<Escape>", lambda event: edit_window.destroy())

    tree.bind("<Double-1>", edit_vocab)

    # Tính năng 1: Thêm thư viện từ có sẵn
    def add_vocab_library():
        file_path = tk.filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                new_vocab = json.load(f)
            current_vocab = load_vocab()
            duplicates = [word for word in new_vocab if word in current_vocab]
            if duplicates:
                replace = messagebox.askyesno("Từ trùng lặp", 
                    f"Có {len(duplicates)} từ trùng lặp. Bạn có muốn thay thế từ cũ không?")
                if replace:
                    current_vocab.update(new_vocab)
                else:
                    for word, data in new_vocab.items():
                        if word not in current_vocab:
                            current_vocab[word] = data
            else:
                current_vocab.update(new_vocab)
            save_vocab(current_vocab)
            update_tree_and_count()
            messagebox.showinfo("Thành công", "Đã thêm từ thư viện!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở file: {str(e)}")

    # Tính năng 2 & 4: Xóa từ đã chọn (bao gồm chuột phải)
    def delete_selected_words():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Lỗi", "Vui lòng chọn ít nhất một từ để xóa!")
            return
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa các từ đã chọn?"):
            vocab = load_vocab()
            for item in selected_items:
                eng = tree.item(item)["values"][0]
                del vocab[eng]
            save_vocab(vocab)
            update_tree_and_count()
            messagebox.showinfo("Thành công", "Đã xóa các từ đã chọn!")

    # Tính năng 3: Xóa hết từ điển
    def delete_all_vocab():
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa hết từ điển không?"):
            vocab = {}
            save_vocab(vocab)
            update_tree_and_count()
            messagebox.showinfo("Thành công", "Đã xóa hết từ điển!")

    # Tính năng 4: Menu chuột phải
    context_menu = tk.Menu(add_window, tearoff=0)
    context_menu.add_command(label="Xóa", command=delete_selected_words)

    def show_context_menu(event):
        selected_items = tree.selection 
        if selected_items:
            context_menu.post(event.x_root, event.y_root)

    tree.bind("<Button-3>", show_context_menu)

    # Thêm các nút
    button_frame = tk.Frame(add_window)
    button_frame.pack(pady=5)
    tk.Button(button_frame, text="Lưu", command=save_new_word).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Thêm thư viện", command=add_vocab_library).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Xóa từ đã chọn", command=delete_selected_words).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Xóa hết từ điển", command=delete_all_vocab).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Quay lại", command=lambda: [add_window.destroy(), parent.deiconify()]).pack(side=tk.LEFT, padx=5)

    add_window.bind("<Return>", lambda event: save_new_word())
    add_window.bind("<Escape>", lambda event: [add_window.destroy(), parent.deiconify()])

# Kiểm tra từ vựng
def test_vocab_window(parent):
    vocab = load_vocab()
    if not vocab:
        messagebox.showinfo("Thông báo", "Chưa có từ vựng nào!")
        parent.deiconify()
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
        parent.deiconify()
        return

    current_word = random.choice(list(available_words.keys()))
    current_data = vocab[current_word]

    meaning_label = tk.Label(test_window, text=f"Nghĩa: {current_data['meaning']}", font=("Arial", 12))
    meaning_label.pack(pady=10)

    status_label = tk.Label(test_window, text=f"Số lần đúng: {current_data['correct_count']}/20")
    status_label.pack()

    answer_entry = tk.Entry(test_window, width=30)
    answer_entry.pack(pady=10)
    answer_entry.focus_set()

    def check_answer():
        nonlocal current_word, current_data, available_words
        answer = answer_entry.get().strip().lower()
        if answer == current_word:
            current_data["correct_count"] += 1
            if current_data["correct_count"] >= 20:
                current_data["completed_date"] = today.strftime("%Y-%m-%d")
                messagebox.showinfo("Hoàn thành", f"Đã hoàn thành '{current_word}'. Sẽ xuất hiện lại sau 20 ngày.")
                answer_entry.focus_set()
        else:
            if current_data["correct_count"] > 0:
                current_data["correct_count"] -= 1
            messagebox.showerror("Sai", f"Đáp án đúng: {current_word}. Số lần đúng còn: {current_data['correct_count']}")
            answer_entry.focus_set()

        vocab[current_word] = current_data
        save_vocab(vocab)

        available_words = {k: v for k, v in vocab.items() if v["correct_count"] < 20 or 
                           (v["completed_date"] and (today - datetime.datetime.strptime(v["completed_date"], "%Y-%m-%d").date()).days >= 20)}
        if not available_words:
            messagebox.showinfo("Thông báo", "Không còn từ nào để kiểm tra!")
            test_window.destroy()
            parent.deiconify()
            return

        current_word = random.choice(list(available_words.keys()))
        current_data = vocab[current_word]
        
        meaning_label.config(text=f"Nghĩa: {current_data['meaning']}")
        status_label.config(text=f"Số lần đúng: {current_data['correct_count']}/20")
        answer_entry.delete(0, tk.END)
        answer_entry.focus_set()

    tk.Button(test_window, text="Kiểm tra", command=check_answer).pack(pady=10)
    tk.Button(test_window, text="Quay lại", command=lambda: [test_window.destroy(), parent.deiconify()]).pack(pady=5)

    test_window.bind("<Return>", lambda event: check_answer())
    test_window.bind("<Escape>", lambda event: [test_window.destroy(), parent.deiconify()])

# Menu tiếng Anh
def english_menu(parent):
    root = tk.Toplevel(parent)
    root.title("Ôn tiếng Anh")
    root.geometry("300x200")

    tk.Label(root, text="Ôn tập tiếng Anh", font=("Arial", 14)).pack(pady=20)
    tk.Button(root, text="Thêm từ vựng", command=lambda: add_vocab_window(root), width=20).pack(pady=5)
    tk.Button(root, text="Kiểm tra từ vựng", command=lambda: [root.withdraw(), test_vocab_window(root)], width=20).pack(pady=5)
    tk.Button(root, text="Quay lại", command=lambda: [root.destroy(), parent.deiconify()]).pack(pady=5)

    root.bind("<Escape>", lambda event: [root.destroy(), parent.deiconify()])