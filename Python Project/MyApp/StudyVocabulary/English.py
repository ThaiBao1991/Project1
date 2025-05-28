import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
import json
import random
import datetime
import os
import sys
import shutil

# Xử lý sys.stdout/sys.stderr cho --noconsole
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

def resource_path(relative_path):
    """Lấy đường dẫn tuyệt đối đến tài nguyên trong thư mục tạm hoặc thư mục dự án"""
    if hasattr(sys, '_MEIPASS'):
        # Đường dẫn đến thư mục tạm khi chạy file .exe
        base_path = sys._MEIPASS
    else:
        # Đường dẫn khi chạy mã nguồn
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_vocab_file_path():
    """Lấy đường dẫn đến english_vocab.json trong thư mục chứa main.exe hoặc dự án"""
    if hasattr(sys, '_MEIPASS'):
        # Khi chạy .exe, lấy thư mục chứa main.exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Khi chạy mã nguồn, lấy thư mục chứa main.py
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "english_vocab.json")

# Đường dẫn đến file vocab
VOCAB_FILE = get_vocab_file_path()
VOCAB_FILE_PACKAGED = resource_path("english_vocab.json")

# Khởi tạo file nếu chưa tồn tại
def initialize_vocab_file():
    try:
        if not os.path.exists(VOCAB_FILE):
            # Nếu file chưa tồn tại, sao chép từ file đóng gói
            if os.path.exists(VOCAB_FILE_PACKAGED):
                shutil.copyfile(VOCAB_FILE_PACKAGED, VOCAB_FILE)
            else:
                # Nếu không có file đóng gói, tạo file rỗng
                with open(VOCAB_FILE, "w", encoding="utf-8") as f:
                    json.dump({}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể khởi tạo file từ vựng: {str(e)}")
        raise

# Đọc từ vựng
def load_vocab():
    try:
        initialize_vocab_file()
        with open(VOCAB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đọc file từ vựng: {str(e)}")
        raise

# Lưu từ vựng
def save_vocab(vocab):
    try:
        with open(VOCAB_FILE, "w", encoding="utf-8") as f:
            json.dump(vocab, f, ensure_ascii=False, indent=4)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể lưu file từ vựng: {str(e)}")
        raise

# Thêm từ vựng
def add_vocab_window(parent):
    add_window = tk.Toplevel(parent)
    add_window.title("Thêm từ vựng tiếng Anh")
    add_window.geometry("600x900")

    tk.Label(add_window, text="Từ tiếng Anh (Ctrl+V để dán):").pack(pady=5)
    eng_entry = tk.Entry(add_window, width=40)
    eng_entry.pack()
    eng_entry.focus_set()

    tk.Label(add_window, text="Nghĩa tiếng Việt (Ctrl+V để dán):").pack(pady=5)
    viet_entry = tk.Entry(add_window, width=40)
    viet_entry.pack()

    tk.Label(add_window, text="Loại từ (type, Ctrl+V để dán):").pack(pady=5)
    type_entry = tk.Entry(add_window, width=40)
    type_entry.pack()

    tk.Label(add_window, text="Phát âm (pronounce, Ctrl+V để dán):").pack(pady=5)
    pronounce_entry = tk.Entry(add_window, width=40)
    pronounce_entry.pack()

    tk.Label(add_window, text="Dán nhiều từ: 'từ - nghĩa - loại - phát âm' (dùng dấu gạch ngang)", fg="gray").pack(pady=2)

    try:
        vocab = load_vocab()
        count_label = tk.Label(add_window, text=f"Tổng số từ: {len(vocab)}")
        count_label.pack(pady=5)
    except:
        add_window.destroy()
        return

    tree_frame = tk.Frame(add_window)
    tree_frame.pack(pady=10, fill=tk.BOTH, expand=True)
    tree = ttk.Treeview(tree_frame, columns=("English", "Vietnamese", "Type", "Pronounce", "CorrectCount", "CompletedDate"), show="headings", height=10)
    tree.heading("English", text="Từ tiếng Anh")
    tree.heading("Vietnamese", text="Nghĩa tiếng Việt")
    tree.heading("Type", text="Loại từ")
    tree.heading("Pronounce", text="Phát âm")
    tree.heading("CorrectCount", text="Số lần đúng")
    tree.heading("CompletedDate", text="Ngày hoàn thành")
    tree.column("English", width=100)
    tree.column("Vietnamese", width=100)
    tree.column("Type", width=100)
    tree.column("Pronounce", width=100)
    tree.column("CorrectCount", width=80)
    tree.column("CompletedDate", width=100)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.configure(yscrollcommand=scrollbar.set)

    def update_tree_and_count(filter_text=""):
        for item in tree.get_children():
            tree.delete(item)
        try:
            vocab = load_vocab()
            for eng, data in vocab.items():
                if filter_text.lower() in eng.lower():
                    tree.insert("", tk.END, values=(eng, data["meaning"], data["type"], data["pronounce"], data["correct_count"], data["completed_date"]))
            count_label.config(text=f"Tổng số từ: {len(vocab)}")
        except:
            messagebox.showerror("Lỗi", "Không thể cập nhật danh sách từ vựng!")
            add_window.destroy()

    update_tree_and_count()

    def filter_vocab(event):
        filter_text = eng_entry.get().strip()
        update_tree_and_count(filter_text)

    eng_entry.bind("<KeyRelease>", filter_vocab)

    def save_new_word():
        eng_text = eng_entry.get().strip()
        viet = viet_entry.get().strip()
        word_type = type_entry.get().strip()
        pronounce = pronounce_entry.get().strip()

        if "-" in eng_text and not (viet or word_type or pronounce):
            parts = [p.strip() for p in eng_text.split("-")]
            if len(parts) >= 2:
                eng = parts[0].lower()
                viet = parts[1]
                word_type = parts[2] if len(parts) > 2 else "N/A"
                pronounce = parts[3] if len(parts) > 3 else "N/A"
            else:
                messagebox.showwarning("Lỗi", "Định dạng không đúng! Dùng: từ - nghĩa - loại - phát âm")
                eng_entry.focus_set()
                return
        else:
            eng = eng_text.lower()

        if not eng or not viet:
            messagebox.showwarning("Lỗi", "Vui lòng nhập ít nhất từ tiếng Anh và nghĩa tiếng Việt!")
            eng_entry.focus_set()
            return
        
        try:
            vocab = load_vocab()
            if eng in vocab:
                messagebox.showinfo("Thông báo", "Từ này đã tồn tại!")
                eng_entry.focus_set()
            else:
                vocab[eng] = {
                    "meaning": viet,
                    "type": word_type if word_type else "N/A",
                    "pronounce": pronounce if pronounce else "N/A",
                    "correct_count": 0,
                    "completed_date": None
                }
                save_vocab(vocab)
                messagebox.showinfo("Thành công", f"Đã thêm: {eng} - {viet}")
                eng_entry.delete(0, tk.END)
                viet_entry.delete(0, tk.END)
                type_entry.delete(0, tk.END)
                pronounce_entry.delete(0, tk.END)
                update_tree_and_count()
                eng_entry.focus_set()
        except:
            messagebox.showerror("Lỗi", "Không thể thêm từ mới!")
            eng_entry.focus_set()

    def edit_vocab(event):
        selected_item = tree.selection()
        if not selected_item:
            return
        eng = tree.item(selected_item)["values"][0]
        try:
            vocab = load_vocab()
            data = vocab[eng]
        except:
            messagebox.showerror("Lỗi", "Không thể tải thông tin từ vựng!")
            return

        edit_window = tk.Toplevel(add_window)
        edit_window.title(f"Sửa thông tin: {eng}")
        edit_window.geometry("300x250")

        tk.Label(edit_window, text="Nghĩa tiếng Việt:").pack(pady=5)
        viet_edit = tk.Entry(edit_window, width=30)
        viet_edit.insert(0, data["meaning"])
        viet_edit.pack()

        tk.Label(edit_window, text="Loại từ (type):").pack(pady=5)
        type_edit = tk.Entry(edit_window, width=30)
        type_edit.insert(0, data["type"])
        type_edit.pack()

        tk.Label(edit_window, text="Phát âm (pronounce):").pack(pady=5)
        pronounce_edit = tk.Entry(edit_window, width=30)
        pronounce_edit.insert(0, data["pronounce"])
        pronounce_edit.pack()

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
                    "type": type_edit.get().strip() if type_edit.get().strip() else "N/A",
                    "pronounce": pronounce_edit.get().strip() if pronounce_edit.get().strip() else "N/A",
                    "correct_count": new_count,
                    "completed_date": new_date if new_date else None
                }
                save_vocab(vocab)
                update_tree_and_count()
                edit_window.destroy()
            except ValueError as e:
                messagebox.showerror("Lỗi", str(e))
                count_edit.focus_set()
            except:
                messagebox.showerror("Lỗi", "Không thể lưu chỉnh sửa!")

        tk.Button(edit_window, text="Lưu", command=save_edit).pack(pady=10)
        tk.Button(edit_window, text="Hủy", command=edit_window.destroy).pack(pady=5)
        edit_window.bind("<Return>", lambda event: save_edit())
        edit_window.bind("<Escape>", lambda event: edit_window.destroy())

    tree.bind("<Double-1>", edit_vocab)

    def add_vocab_library():
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
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

    def delete_selected_words():
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Lỗi", "Vui lòng chọn ít nhất một từ để xóa!")
            return
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa các từ đã chọn?"):
            try:
                vocab = load_vocab()
                for item in selected_items:
                    eng = tree.item(item)["values"][0]
                    del vocab[eng]
                save_vocab(vocab)
                update_tree_and_count()
                messagebox.showinfo("Thành công", "Đã xóa các từ đã chọn!")
            except:
                messagebox.showerror("Lỗi", "Không thể xóa từ!")

    def delete_all_vocab():
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa hết từ điển không?"):
            try:
                vocab = {}
                save_vocab(vocab)
                update_tree_and_count()
                messagebox.showinfo("Thành công", "Đã xóa hết từ điển!")
            except:
                messagebox.showerror("Lỗi", "Không thể xóa từ điển!")

    context_menu = tk.Menu(add_window, tearoff=0)
    context_menu.add_command(label="Xóa", command=delete_selected_words)

    def show_context_menu(event):
        selected_items = tree.selection()
        if selected_items:
            context_menu.post(event.x_root, event.y_root)

    tree.bind("<Button-3>", show_context_menu)

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
    try:
        vocab = load_vocab()
        if not vocab:
            messagebox.showinfo("Thông báo", "Chưa có từ vựng nào!")
            parent.deiconify()
            return
    except:
        parent.deiconify()
        return

    test_window = tk.Toplevel(parent)
    test_window.title("Kiểm tra từ vựng")
    test_window.geometry("300x400")

    tk.Label(test_window, text="Ôn từ số (1 đến tổng số từ):").pack(pady=5)
    range_frame = tk.Frame(test_window)
    range_frame.pack(pady=5)
    tk.Label(range_frame, text="Từ:").pack(side=tk.LEFT)
    start_entry = tk.Entry(range_frame, width=5)
    start_entry.pack(side=tk.LEFT, padx=5)
    tk.Label(range_frame, text="Đến:").pack(side=tk.LEFT)
    end_entry = tk.Entry(range_frame, width=5)
    end_entry.pack(side=tk.LEFT, padx=5)

    today = datetime.datetime.now().date()

    def get_filtered_vocab():
        try:
            vocab_list = list(load_vocab().items())
            total_words = len(vocab_list)
            
            start_text = start_entry.get().strip()
            end_text = end_entry.get().strip()
            
            if not start_text or not end_text:
                filtered_vocab = {k: v for k, v in vocab_list if v["correct_count"] < 20 or 
                                  (v["completed_date"] and (today - datetime.datetime.strptime(v["completed_date"], "%Y-%m-%d").date()).days >= 20)}
                return filtered_vocab, total_words
            
            try:
                start = int(start_text) - 1
                end = int(end_text)
                if start < 0 or end > total_words or start >= end:
                    raise ValueError("Khoảng không hợp lệ!")
                filtered_list = vocab_list[start:end]
                filtered_vocab = {k: v for k, v in filtered_list if v["correct_count"] < 20 or 
                                  (v["completed_date"] and (today - datetime.datetime.strptime(v["completed_date"], "%Y-%m-%d").date()).days >= 20)}
                return filtered_vocab, total_words
            except ValueError as e:
                messagebox.showwarning("Lỗi", str(e) if str(e) != "Khoảng không hợp lệ!" else "Khoảng không hợp lệ! Vui lòng nhập số hợp lệ.")
                return None, total_words
        except:
            messagebox.showerror("Lỗi", "Không thể tải từ vựng!")
            return None, 0

    available_words, total_words = get_filtered_vocab()
    if not available_words:
        messagebox.showinfo("Thông báo", "Không có từ nào để kiểm tra trong khoảng này!")
        test_window.destroy()
        parent.deiconify()
        return

    current_word = random.choice(list(available_words.keys()))
    current_data = available_words[current_word]

    meaning_label = tk.Label(test_window, text=f"Nghĩa: {current_data['meaning']}", font=("Arial", 12))
    meaning_label.pack(pady=5)

    type_label = tk.Label(test_window, text=f"Loại từ: {current_data['type']}", font=("Arial", 12))
    type_label.pack(pady=5)

    pronounce_label = tk.Label(test_window, text=f"Phát âm: {current_data['pronounce']}", font=("Arial", 12))
    pronounce_label.pack(pady=5)

    status_label = tk.Label(test_window, text=f"Số lần đúng: {current_data['correct_count']}/20")
    status_label.pack(pady=5)

    tk.Label(test_window, text="Nhập từ tiếng Anh:").pack(pady=5)
    answer_entry = tk.Entry(test_window, width=30)
    answer_entry.pack(pady=5)
    answer_entry.focus_set()

    def check_answer():
        nonlocal current_word, current_data, available_words
        answer = answer_entry.get().strip().lower()
        try:
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

            vocab = load_vocab()
            vocab[current_word] = current_data
            save_vocab(vocab)

            available_words, _ = get_filtered_vocab()
            if not available_words:
                messagebox.showinfo("Thông báo", "Không còn từ nào để kiểm tra trong khoảng này!")
                test_window.destroy()
                parent.deiconify()
                return

            current_word = random.choice(list(available_words.keys()))
            current_data = available_words[current_word]
            
            meaning_label.config(text=f"Nghĩa: {current_data['meaning']}")
            type_label.config(text=f"Loại từ: {current_data['type']}")
            pronounce_label.config(text=f"Phát âm: {current_data['pronounce']}")
            status_label.config(text=f"Số lần đúng: {current_data['correct_count']}/20")
            answer_entry.delete(0, tk.END)
            answer_entry.focus_set()
        except:
            messagebox.showerror("Lỗi", "Không thể kiểm tra đáp án!")
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

# Main window
if __name__ == "__main__":
    main_window = tk.Tk()
    main_window.title("Ứng dụng học tiếng Anh")
    main_window.geometry("300x200")
    tk.Label(main_window, text="Chào mừng!", font=("Arial", 14)).pack(pady=20)
    tk.Button(main_window, text="Bắt đầu", command=lambda: english_menu(main_window), width=20).pack(pady=5)
    main_window.mainloop()