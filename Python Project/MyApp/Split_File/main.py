import os
import sys
import site
import shutil
import importlib
import importlib.metadata
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

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

# Khai bao thu vien ben ngoai neu bo sung trong tuong lai (hien chi dung stdlib)
REQUIRED_PACKAGES = {}

PACKAGE_CONFLICTS = {
    "Crypto": ["crypto", "pycrypto"],
}

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
        for mod, pip_spec in missing_items:
            _heal_windows_package_conflict(mod, pip_spec)

        subprocess.check_call(pip_base_cmd + missing_specs)
        _refresh_import_paths(in_venv)

        still_missing = []
        for mod, pip_spec in missing_items:
            if _can_import_requirement(mod):
                continue
            fallback = FALLBACK_PACKAGES.get(mod)
            if fallback:
                fb_mod, fb_pip = fallback
                print(f"[*] '{mod}' vẫn chưa import được, thử gói dự phòng: {fb_pip}")
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

def split_by_size(file_path, size_mb):
    try:
        size_bytes = int(size_mb) * 1024 * 1024
        if size_bytes <= 0:
            messagebox.showerror("Error", "Size must be greater than 0 MB")
            return False

        with open(file_path, 'rb') as f:
            data = f.read()
            total_parts = (len(data) + size_bytes - 1) // size_bytes
            base_name = file_path + ".part_"

            for i in range(total_parts):
                part_data = data[i * size_bytes:(i + 1) * size_bytes]
                part_filename = f"{base_name}{str(i + 1).zfill(3)}"
                with open(part_filename, 'wb') as part_file:
                    part_file.write(part_data)

        messagebox.showinfo("Success", f"File split into {total_parts} parts successfully!")
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error splitting file: {str(e)}")
        return False

def split_by_count(file_path, count):
    try:
        count = int(count)
        if count <= 0:
            messagebox.showerror("Error", "Count must be greater than 0")
            return False

        with open(file_path, 'rb') as f:
            data = f.read()
            total_size = len(data)
            part_size = (total_size + count - 1) // count
            base_name = file_path + ".part_"

            for i in range(count):
                part_data = data[i * part_size:(i + 1) * part_size]
                part_filename = f"{base_name}{str(i + 1).zfill(3)}"
                with open(part_filename, 'wb') as part_file:
                    part_file.write(part_data)

        messagebox.showinfo("Success", f"File split into {count} parts successfully!")
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error splitting file: {str(e)}")
        return False

def merge_files(file_path):
    temp_merged_path = None
    try:
        file_dir = os.path.dirname(os.path.abspath(file_path))
        file_name = os.path.basename(file_path)

        def _find_parts(prefix_base):
            prefix = prefix_base + ".part_"
            matched = []
            for name in os.listdir(file_dir):
                if name.startswith(prefix):
                    suffix = name[len(prefix):]
                    if suffix.isdigit():
                        matched.append(name)
            return matched

        # Tách tên file gốc (giữ nguyên phần mở rộng gốc, loại bỏ hậu tố .part_xxx cuối cùng)
        if ".part_" in file_name:
            base_name = file_name.rsplit(".part_", 1)[0]
            part_files = _find_parts(base_name)
        else:
            base_name = file_name
            part_files = _find_parts(base_name)
            if not part_files:
                stem, _ = os.path.splitext(file_name)
                if stem and stem != base_name:
                    candidate_parts = _find_parts(stem)
                    if candidate_parts:
                        base_name = stem
                        part_files = candidate_parts

        if not part_files:
            messagebox.showerror("Error", "No matching .part_xxx files found to merge!")
            return False

        # Sắp xếp theo thứ tự số phần
        prefix = base_name + ".part_"
        part_files.sort(key=lambda x: int(x[len(prefix):]))

        # Khôi phục đúng tên và phần mở rộng gốc của file (ghi qua file tạm an toàn)
        merged_filename = os.path.join(file_dir, base_name)
        temp_merged_path = merged_filename + ".merging_tmp"

        with open(temp_merged_path, 'wb') as merged_file:
            for part_filename in part_files:
                part_path = os.path.join(file_dir, part_filename)
                with open(part_path, 'rb') as part_file:
                    shutil.copyfileobj(part_file, merged_file, length=1024 * 1024)

        os.replace(temp_merged_path, merged_filename)
        temp_merged_path = None

        # Xóa các phần tệp tin đã nối sau khi đã ghi hoàn chỉnh
        for part_filename in part_files:
            part_path = os.path.join(file_dir, part_filename)
            os.remove(part_path)

        messagebox.showinfo("Success", f"Files merged successfully into:\n{base_name}")
        return True
    except Exception as e:
        if temp_merged_path and os.path.exists(temp_merged_path):
            try:
                os.remove(temp_merged_path)
            except OSError:
                pass
        messagebox.showerror("Error", f"Error merging files: {str(e)}")
        return False

def open_file_dialog():
    file_path = filedialog.askopenfilename()  # Hiển thị hộp thoại chọn tệp tin
    if file_path:
        merge_result = merge_files(file_path)
        if merge_result:
            print("Files merged successfully!")
        else:
            print("Error merging files.")

def split_by_size_dialog():
    file_path = filedialog.askopenfilename()
    if file_path:
        top = tk.Toplevel()
        top.title("Split by Size")
        top.geometry("300x100")
        entry_label = tk.Label(top, text="Enter size (MB):")
        entry_label.pack()
        size_entry = tk.Entry(top)
        size_entry.pack()
        split_button = tk.Button(top, text="Split", command=lambda: split_by_size(file_path, size_entry.get()))
        split_button.pack()

def split_by_count_dialog():
    file_path = filedialog.askopenfilename()
    if file_path:
        top = tk.Toplevel()
        top.title("Split by Count")
        top.geometry("300x100")
        entry_label = tk.Label(top, text="Enter count:")
        entry_label.pack()
        count_entry = tk.Entry(top)
        count_entry.pack()
        split_button = tk.Button(top, text="Split", command=lambda: split_by_count(file_path, count_entry.get()))
        split_button.pack()

def main():
    root = tk.Tk()
    root.title("File Splitter & Merger")
    root.geometry("300x200")

    split_by_size_button = tk.Button(root, text="Split by Size", command=split_by_size_dialog)
    split_by_size_button.pack()

    split_by_count_button = tk.Button(root, text="Split by Count", command=split_by_count_dialog)
    split_by_count_button.pack()

    merge_files_button = tk.Button(root, text="Merge Files", command=open_file_dialog)
    merge_files_button.pack()

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