import os
import sys
import site
import shutil
import importlib
import importlib.metadata
import subprocess
import json
import ast
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REQUIRED_PACKAGES = {
    "pandas": "pandas>=2.0.0",
    "pyxlsb": "pyxlsb>=1.0.10",
    "Crypto.Cipher": "pycryptodome>=3.19.0",
}

# Các gói dễ xung đột tên thư mục hoa/thường trên Windows (VD: crypto -> Crypto)
PACKAGE_CONFLICTS = {
    "Crypto": ["crypto", "pycrypto"],
}

# Gói dự phòng nếu gói chính bị khoá quyền ở thư mục hệ thống
FALLBACK_PACKAGES = {
    "Crypto.Cipher": ("Cryptodome.Cipher", "pycryptodomex>=3.19.0"),
}

EXIT_MISSING_LIB_DIALOG = 2


def _pip_base_name(pip_spec):
    for sep in ("==", ">=", "<=", "~=", "!=", ">", "<", "["):
        if sep in pip_spec:
            pip_spec = pip_spec.split(sep, 1)[0]
    return pip_spec.strip()


def _quote_pip_spec(spec):
    if any(ch in spec for ch in '<>=!~ []"'):
        return f'"{spec}"'
    return spec


def _can_import_requirement(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        fallback = FALLBACK_PACKAGES.get(module_name)
        if fallback:
            try:
                importlib.import_module(fallback[0])
                return True
            except ImportError:
                return False
        return False


def _refresh_import_paths(in_venv):
    if not in_venv:
        try:
            user_site = site.getusersitepackages()
            if user_site and os.path.isdir(user_site) and user_site not in sys.path:
                sys.path.append(user_site)
        except Exception:
            pass
    importlib.invalidate_caches()


def _collect_site_dirs():
    dirs = []
    try:
        user_site = site.getusersitepackages()
        if user_site:
            dirs.append(user_site)
    except Exception:
        pass
    try:
        dirs.extend(site.getsitepackages())
    except Exception:
        pass
    for p in sys.path:
        if p and os.path.basename(p).lower() == "site-packages":
            dirs.append(p)
    seen = set()
    result = []
    for d in dirs:
        norm = os.path.normcase(os.path.abspath(d))
        if norm not in seen and os.path.isdir(d):
            seen.add(norm)
            result.append(d)
    return result


def _heal_windows_package_conflict(module_name, pip_spec):
    """Tự phát hiện & sửa lỗi xung đột gói / sai hoa-thường thư mục trên Windows (VD: crypto vs Crypto)."""
    if sys.platform != "win32":
        return False

    top_pkg = module_name.split(".")[0]
    conflict_pkgs = list(PACKAGE_CONFLICTS.get(top_pkg, []))
    target_base = _pip_base_name(pip_spec)

    found_conflicts = []
    for pkg in conflict_pkgs:
        try:
            importlib.metadata.distribution(pkg)
            found_conflicts.append(pkg)
        except importlib.metadata.PackageNotFoundError:
            pass

    wrong_case_dirs = []
    for sp in _collect_site_dirs():
        try:
            for entry in os.listdir(sp):
                full_path = os.path.join(sp, entry)
                if os.path.isdir(full_path) and entry.lower() == top_pkg.lower() and entry != top_pkg:
                    wrong_case_dirs.append(full_path)
        except OSError:
            pass

    if not found_conflicts and not wrong_case_dirs:
        return False

    print(
        f"[*] Phát hiện xung đột gói/chữ hoa-thường cho '{top_pkg}' "
        f"(conflicts={found_conflicts}, dirs={wrong_case_dirs}). Đang tự động sửa..."
    )

    to_uninstall = []
    for pkg in found_conflicts + [target_base]:
        if pkg not in to_uninstall:
            try:
                importlib.metadata.distribution(pkg)
                to_uninstall.append(pkg)
            except importlib.metadata.PackageNotFoundError:
                pass

    if to_uninstall:
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", *to_uninstall],
            check=False,
        )

    for bad_dir in wrong_case_dirs:
        if os.path.exists(bad_dir):
            shutil.rmtree(bad_dir, ignore_errors=True)

    importlib.invalidate_caches()
    return True


def _show_manual_install_dialog(missing_packages, error_detail=""):
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    user_flag = "" if in_venv else "--user "
    quoted_pkgs = " ".join(_quote_pip_spec(p) for p in missing_packages)
    cmd = f"python -m pip install {user_flag}{quoted_pkgs}"
    try:
        root = tk.Tk()
        root.withdraw()
        err_win = tk.Toplevel(root)
        err_win.title("Lỗi Thiếu Thư Viện")
        err_win.geometry("640x360")

        def close_dialog():
            try:
                root.quit()
            except Exception:
                pass
            try:
                root.destroy()
            except Exception:
                pass

        err_win.protocol("WM_DELETE_WINDOW", close_dialog)

        tk.Label(
            err_win,
            text="Ứng dụng thiếu thư viện cần thiết và không thể tự cài đặt.",
            fg="red",
            font=("Arial", 11, "bold"),
        ).pack(pady=(12, 4))

        if error_detail:
            tk.Label(
                err_win,
                text=f"Chi tiết: {str(error_detail)[:220]}",
                fg="#555555",
                font=("Arial", 9),
                wraplength=600,
                justify="left",
            ).pack(pady=(0, 6))

        tk.Label(
            err_win,
            text="Vui lòng copy lệnh dưới đây (đã bọc ngoặc kép chuẩn) và dán vào Terminal/CMD:",
            font=("Arial", 10),
        ).pack(pady=4)

        txt = tk.Text(err_win, height=4, width=72, font=("Consolas", 10))
        txt.pack(pady=8, padx=12)
        txt.insert(tk.END, cmd)
        txt.config(state="disabled")

        btn_frame = tk.Frame(err_win)
        btn_frame.pack(pady=10)

        copy_status = tk.Label(err_win, text="", fg="green", font=("Arial", 9))
        copy_status.pack()

        def copy_cmd():
            err_win.clipboard_clear()
            err_win.clipboard_append(cmd)
            err_win.update()
            copy_status.config(text="Đã sao chép lệnh vào clipboard!")

        tk.Button(btn_frame, text="Sao chép lệnh", command=copy_cmd, width=15).pack(side=tk.LEFT, padx=8)
        tk.Button(btn_frame, text="Thoát ứng dụng", command=close_dialog, width=15).pack(side=tk.LEFT, padx=8)

        root.mainloop()
    except tk.TclError:
        print(f"[!] Không thể tự cài đặt thư viện ({error_detail}). Chạy thủ công: {cmd}", file=sys.stderr)


def check_and_install_packages():
    missing_items = [
        (mod, pip_spec)
        for mod, pip_spec in REQUIRED_PACKAGES.items()
        if not _can_import_requirement(mod)
    ]

    if not missing_items:
        return

    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    pip_base_cmd = [sys.executable, "-m", "pip", "install"]
    if not in_venv:
        pip_base_cmd.append("--user")

    missing_specs = [pip_spec for _, pip_spec in missing_items]
    print(f"[*] Đang tự động cài đặt thư viện còn thiếu: {', '.join(missing_specs)}")

    try:
        # Bước 1: Tự sửa xung đột gói / chữ hoa-thường trên Windows trước khi cài
        for mod, pip_spec in missing_items:
            _heal_windows_package_conflict(mod, pip_spec)

        # Bước 2: Cài đặt các gói còn thiếu
        subprocess.check_call(pip_base_cmd + missing_specs)
        _refresh_import_paths(in_venv)

        # Bước 3: Kiểm tra lại import; nếu gói nào vẫn lỗi do xung đột bị khoá quyền -> thử fallback
        still_missing = []
        for mod, pip_spec in missing_items:
            if _can_import_requirement(mod):
                continue
            fallback = FALLBACK_PACKAGES.get(mod)
            if fallback:
                fb_mod, fb_pip = fallback
                print(f"[*] '{mod}' vẫn chưa import được, thử gói dự phòng không xung đột: {fb_pip}")
                try:
                    subprocess.check_call(pip_base_cmd + [fb_pip])
                    _refresh_import_paths(in_venv)
                    importlib.import_module(fb_mod)
                    continue
                except Exception:
                    pass
            still_missing.append(pip_spec)

        if still_missing:
            raise ImportError(f"Đã chạy pip nhưng vẫn không thể import: {', '.join(still_missing)}")

        print("[*] Cài đặt thư viện thành công!")
    except Exception as exc:
        _show_manual_install_dialog(missing_specs, exc)
        sys.exit(EXIT_MISSING_LIB_DIALOG)


check_and_install_packages()

import pandas as pd
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    from Crypto.Random import get_random_bytes
except ImportError:
    from Cryptodome.Cipher import AES
    from Cryptodome.Util.Padding import pad, unpad
    from Cryptodome.Random import get_random_bytes

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Ứng dụng đa năng")
        self.root.geometry("500x400")
        self.show_menu()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_menu(self):
        self.clear_window()
        tk.Label(self.root, text="Chọn tính năng", font=("Arial", 14, "bold")).pack(pady=20)

        tk.Button(self.root, text="1. Đổi file .xlsb sang .csv", font=("Arial", 12), 
                  command=self.show_xlsb_to_csv, width=25).pack(pady=10)
        tk.Button(self.root, text="2. Gửi email tự động", font=("Arial", 12), 
                  command=self.show_email_sender, width=25).pack(pady=10)
        tk.Button(self.root, text="3. Mã hóa và giải mã file", font=("Arial", 12), 
                  command=self.show_file_encryption, width=25).pack(pady=10)

    def show_xlsb_to_csv(self):
        self.clear_window()
        self.xlsb_converter = XlsbToCsvConverter(self.root, self.show_menu)

    def show_email_sender(self):
        self.clear_window()
        self.email_sender = EmailSender(self.root, self.show_menu)

    def show_file_encryption(self):
        self.clear_window()
        self.file_encryption = FileEncryption(self.root, self.show_menu)

class XlsbToCsvConverter:
    def __init__(self, root, back_to_menu_callback):
        self.root = root
        self.back_to_menu = back_to_menu_callback

        self.file_xlsb = None
        self.file_csv = None
        self.header_row = tk.StringVar(value="0")

        tk.Label(root, text="Chuyển đổi .xlsb sang .csv", font=("Arial", 14, "bold")).pack(pady=10)
        frame = tk.Frame(root)
        frame.pack(pady=10)

        self.select_xlsb_button = tk.Button(frame, text="Chọn file .xlsb", command=self.select_xlsb, font=("Arial", 10))
        self.select_xlsb_button.grid(row=0, column=0, padx=5, pady=5)
        self.xlsb_label = tk.Label(frame, text="Chưa chọn file .xlsb", font=("Arial", 10))
        self.xlsb_label.grid(row=0, column=1, padx=5, pady=5)

        self.select_csv_button = tk.Button(frame, text="Chọn nơi lưu .csv", command=self.select_csv, font=("Arial", 10))
        self.select_csv_button.grid(row=1, column=0, padx=5, pady=5)
        self.csv_label = tk.Label(frame, text="Chưa chọn nơi lưu .csv", font=("Arial", 10))
        self.csv_label.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frame, text="Chọn dòng làm tiêu đề:", font=("Arial", 10)).grid(row=2, column=0, padx=5, pady=5)
        self.header_entry = tk.Entry(frame, textvariable=self.header_row, width=5, font=("Arial", 10), justify="center")
        self.header_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        tk.Label(frame, text="(0 là dòng đầu, 1 là dòng thứ hai,...)", font=("Arial", 8, "italic")).grid(row=3, column=1, padx=5, pady=0, sticky="w")

        self.start_button = tk.Button(root, text="Start", command=self.start_conversion, font=("Arial", 12, "bold"), 
                                      bg="green", fg="white", width=10, state="disabled")
        self.start_button.pack(pady=10)

        tk.Button(root, text="Quay lại menu", command=self.back_to_menu, font=("Arial", 10), bg="gray", fg="white").pack(pady=10)

        self.header_row.trace_add("write", self.validate_header_input)

    def validate_header_input(self, *args):
        value = self.header_row.get()
        if not value.isdigit() and value != "":
            self.header_row.set("0")
        self.check_start_button()

    def select_xlsb(self):
        self.file_xlsb = filedialog.askopenfilename(title="Chọn file .xlsb", filetypes=[("Excel Binary Files", "*.xlsb"), ("All Files", "*.*")])
        if self.file_xlsb:
            self.xlsb_label.config(text=f"File: {self.file_xlsb.split('/')[-1]}")
            self.check_start_button()
        else:
            self.xlsb_label.config(text="Chưa chọn file .xlsb")

    def select_csv(self):
        self.file_csv = filedialog.asksaveasfilename(title="Lưu file .csv", defaultextension=".csv", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if self.file_csv:
            self.csv_label.config(text=f"Lưu tại: {self.file_csv.split('/')[-1]}")
            self.check_start_button()
        else:
            self.csv_label.config(text="Chưa chọn nơi lưu .csv")

    def check_start_button(self):
        header_value = self.header_row.get()
        if self.file_xlsb and self.file_csv and header_value.isdigit():
            self.start_button.config(state="normal")
        else:
            self.start_button.config(state="disabled")

    def start_conversion(self):
        try:
            header_row = int(self.header_row.get())
            if header_row < 0:
                raise ValueError("Dòng tiêu đề không thể là số âm!")
            df = pd.read_excel(self.file_xlsb, engine="pyxlsb", header=header_row)
            df.to_csv(self.file_csv, index=False, encoding='utf-8-sig')
            messagebox.showinfo("Thành công", f"Đã chuyển đổi từ {self.file_xlsb.split('/')[-1]} sang {self.file_csv.split('/')[-1]} "
                                             f"với tiêu đề lấy từ dòng {header_row}")
        except ValueError as ve:
            messagebox.showerror("Lỗi", f"Giá trị dòng tiêu đề không hợp lệ: {str(ve)}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {str(e)}")

class EmailSender:
    def __init__(self, root, back_to_menu_callback):
        self.root = root
        self.back_to_menu = back_to_menu_callback

        tk.Label(root, text="Gửi email tự động", font=("Arial", 14, "bold")).pack(pady=20)
        tk.Label(root, text="Tính năng đang phát triển...", font=("Arial", 10, "italic")).pack(pady=10)
        tk.Button(root, text="Quay lại menu", command=self.back_to_menu, font=("Arial", 10), bg="gray", fg="white").pack(pady=20)

class FileEncryption:
    def __init__(self, root, back_to_menu_callback):
        self.root = root
        self.back_to_menu = back_to_menu_callback

        tk.Label(self.root, text="Mã hóa và giải mã file", font=("Arial", 14, "bold")).pack(pady=10)

        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        self.encrypt_file_button = tk.Button(frame, text="Mã hóa file", command=self.encrypt_file, font=("Arial", 10))
        self.encrypt_file_button.grid(row=0, column=0, padx=5, pady=5)

        self.decrypt_file_button = tk.Button(frame, text="Giải mã file", command=self.decrypt_file, font=("Arial", 10))
        self.decrypt_file_button.grid(row=0, column=1, padx=5, pady=5)

        self.encrypt_dir_button = tk.Button(frame, text="Mã hóa thư mục", command=self.encrypt_directory, font=("Arial", 10))
        self.encrypt_dir_button.grid(row=1, column=0, padx=5, pady=5)

        self.decrypt_dir_button = tk.Button(frame, text="Giải mã thư mục", command=self.decrypt_directory, font=("Arial", 10))
        self.decrypt_dir_button.grid(row=1, column=1, padx=5, pady=5)

        self.result_tree = ttk.Treeview(self.root, columns=("File", "Kết quả"), show="headings", height=8)
        self.result_tree.heading("File", text="File")
        self.result_tree.heading("Kết quả", text="Kết quả")
        self.result_tree.pack(fill=tk.BOTH, expand=True)

        tk.Button(self.root, text="Quay lại menu", command=self.back_to_menu, font=("Arial", 10), bg="gray", fg="white").pack(pady=10)

    def encrypt_file(self):
        try:
            file_name = filedialog.askopenfilename()
            if not file_name:
                return

            self.result_tree.delete(*self.result_tree.get_children())

            key = get_random_bytes(16)
            output_dir = os.path.dirname(file_name)
            key_path = os.path.join(output_dir, 'key.key')
            
            with open(key_path, 'wb') as key_file:
                key_file.write(key)
            
            file_dict = {}
            self.encrypt_file_helper(file_name, key, output_dir, file_dict)
            
            data_path = os.path.join(output_dir, 'data.txt')
            with open(data_path, 'w') as f:
                for original, encrypted in file_dict.items():
                    f.write(f"{original}:{encrypted}\n")
            
            file_basename = os.path.basename(file_name)
            self.result_tree.insert("", "end", values=(file_basename, "Hoàn thành"))
        
        except Exception as e:
            self.result_tree.insert("", "end", values=("Lỗi", f"Lỗi mã hóa: {str(e)}"))

    def encrypt_file_helper(self, file_name, key, output_dir, file_dict):
        cipher = AES.new(key, AES.MODE_CBC)
        with open(file_name, 'rb') as f:
            original_data = f.read()
        enc_data = cipher.encrypt(pad(original_data, AES.block_size))
        encrypted_file_name = os.path.join(output_dir, str(len(file_dict)) + '.ecrb')
        with open(encrypted_file_name, 'wb') as f:
            f.write(cipher.iv)
            f.write(enc_data)
        file_dict[os.path.basename(file_name)] = os.path.basename(encrypted_file_name)

    def decrypt_file(self):
        try:
            file_name = filedialog.askopenfilename()
            if not file_name:
                return

            self.result_tree.delete(*self.result_tree.get_children())

            output_dir = os.path.dirname(file_name)
            key_path = os.path.join(output_dir, 'key.key')
            data_path = os.path.join(output_dir, 'data.txt')
            
            with open(key_path, 'rb') as key_file:
                key = key_file.read()
            
            file_dict = self.load_file_dict(data_path)
            original_name = file_dict.get(os.path.basename(file_name))
            
            if not original_name:
                raise ValueError("Không tìm thấy tên file gốc trong data.txt")
            
            self.decrypt_file_helper(file_name, key, output_dir, original_name)
            
            self.result_tree.insert("", "end", values=(os.path.basename(file_name), "Hoàn thành"))
        
        except Exception as e:
            self.result_tree.insert("", "end", values=("Lỗi", f"Lỗi giải mã: {str(e)}"))

    def decrypt_file_helper(self, file_name, key, output_dir, original_file_name):
        with open(file_name, 'rb') as f:
            iv = f.read(16)
            enc_data = f.read()
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        original_data = unpad(cipher.decrypt(enc_data), AES.block_size)
        decrypted_path = os.path.join(output_dir, original_file_name)
        with open(decrypted_path, 'wb') as f:
            f.write(original_data)

    def load_file_dict(self, file_path):
        file_dict = {}
        with open(file_path, 'r') as f:
            data = f.read()
            if '{' in data:  # Dạng từ điển
                try:
                    file_data = ast.literal_eval(data)
                    if isinstance(file_data, dict):
                        file_dict = file_data
                except ValueError:
                    print("Lỗi: Định dạng dữ liệu không hợp lệ trong data.txt")
            else:  # Dạng key-value đơn giản
                try:
                    lines = data.split('\n')
                    for line in lines:
                        if line.strip():
                            key, value = line.split(':')
                            file_dict[value.strip()] = key.strip()
                except ValueError:
                    print("Lỗi: Định dạng dữ liệu không hợp lệ trong data.txt")
        return file_dict

    def encrypt_directory(self):
        try:
            dir_name = filedialog.askdirectory()
            if not dir_name:
                return

            self.result_tree.delete(*self.result_tree.get_children())
            key = get_random_bytes(16)
            key_path = os.path.join(dir_name, 'key.key')
            with open(key_path, 'wb') as key_file:
                key_file.write(key)

            file_dict = {}
            file_counter = 0
            for root, dirs, files in os.walk(dir_name):
                for file in files:
                    if file != 'key.key' and file != 'data.txt':
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, dir_name)
                        encrypted_file_name = f"{file_counter}.ecrb"
                        encrypted_file_path = os.path.join(dir_name, encrypted_file_name)

                        cipher = AES.new(key, AES.MODE_CBC)
                        with open(file_path, 'rb') as f:
                            original_data = f.read()
                        enc_data = cipher.encrypt(pad(original_data, AES.block_size))
                        with open(encrypted_file_path, 'wb') as f:
                            f.write(cipher.iv)
                            f.write(enc_data)

                        file_dict[relative_path] = encrypted_file_name
                        self.result_tree.insert("", "end", values=(file, "Hoàn thành"))
                        file_counter += 1

            data_path = os.path.join(dir_name, 'data.txt')
            with open(data_path, 'w') as f:
                json.dump(file_dict, f)  # Ghi dạng JSON để dễ đọc và chính xác

            self.result_tree.insert("", "end", values=("Tổng cộng", f"Đã mã hóa {file_counter} file"))
        except Exception as e:
            self.result_tree.insert("", "end", values=("Lỗi", f"Lỗi mã hóa thư mục: {str(e)}"))

    def decrypt_directory(self):
        try:
            dir_name = filedialog.askdirectory()
            if not dir_name:
                return

            self.result_tree.delete(*self.result_tree.get_children())
            key_path = os.path.join(dir_name, 'key.key')
            data_path = os.path.join(dir_name, 'data.txt')

            with open(key_path, 'rb') as key_file:
                key = key_file.read()

            with open(data_path, 'r') as f:
                file_dict = json.load(f)  # Đọc dữ liệu JSON từ data.txt

            for original_path, encrypted_file in file_dict.items():
                encrypted_file_path = os.path.join(dir_name, encrypted_file)
                if os.path.exists(encrypted_file_path):
                    with open(encrypted_file_path, 'rb') as f:
                        iv = f.read(16)
                        enc_data = f.read()
                    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
                    original_data = unpad(cipher.decrypt(enc_data), AES.block_size)

                    decrypted_file_path = os.path.join(dir_name, original_path)
                    os.makedirs(os.path.dirname(decrypted_file_path), exist_ok=True)
                    with open(decrypted_file_path, 'wb') as f:
                        f.write(original_data)
                    self.result_tree.insert("", "end", values=(encrypted_file, "Hoàn thành"))
                else:
                    self.result_tree.insert("", "end", values=(encrypted_file, "Không tìm thấy file mã hóa"))

            self.result_tree.insert("", "end", values=("Tổng cộng", f"Đã giải mã {len(file_dict)} file"))
        except Exception as e:
            self.result_tree.insert("", "end", values=("Lỗi", f"Lỗi giải mã thư mục: {str(e)}"))

def main():
    root = tk.Tk()
    app = App(root)

    def on_close():
        try:
            root.quit()
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass

    root.protocol("WM_DELETE_WINDOW", on_close)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_close()
    finally:
        try:
            if root.winfo_exists():
                root.destroy()
        except Exception:
            pass
    sys.exit(0)

if __name__ == "__main__":
    main()