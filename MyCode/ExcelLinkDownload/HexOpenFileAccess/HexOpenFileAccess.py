import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os

class VBAUnlocker:
    def __init__(self, root):
        self.root = root
        self.root.title("VBA Unlocker — Access .mdb / .accdb")
        self.root.geometry("900x620")
        self.root.resizable(True, True)

        self.filepath = None
        self.data = None
        self.dpb_offset = -1

        self._build_ui()

    def _build_ui(self):
        # --- Toolbar ---
        toolbar = tk.Frame(self.root, bg="#f0f0f0", pady=6, padx=10)
        toolbar.pack(fill="x", side="top")

        tk.Button(toolbar, text="Chọn file", command=self.open_file,
                  bg="#4a90d9", fg="white", padx=10).pack(side="left", padx=4)

        self.path_var = tk.StringVar(value="Chưa chọn file...")
        tk.Entry(toolbar, textvariable=self.path_var, state="readonly",
                 width=55, font=("Courier", 10)).pack(side="left", padx=4)

        tk.Button(toolbar, text="Unlock VBA", command=self.do_unlock,
                  bg="#e07b00", fg="white", padx=10).pack(side="left", padx=4)

        tk.Button(toolbar, text="Lưu file", command=self.save_file,
                  bg="#c0392b", fg="white", padx=10).pack(side="left", padx=4)

        # --- Status bar ---
        self.status_var = tk.StringVar(value="Chưa mở file.")
        status_bar = tk.Label(self.root, textvariable=self.status_var,
                              anchor="w", bg="#ddeeff", padx=10, pady=3,
                              font=("Arial", 9))
        status_bar.pack(fill="x", side="top")

        # --- Main panels ---
        paned = tk.PanedWindow(self.root, orient="horizontal", sashrelief="raised")
        paned.pack(fill="both", expand=True)

        # Hex viewer panel (trái)
        hex_frame = tk.LabelFrame(paned, text=" Hex Viewer ", padx=4, pady=4)
        paned.add(hex_frame, minsize=500)

        self.hex_text = scrolledtext.ScrolledText(
            hex_frame, font=("Courier", 10), bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="white", state="disabled", wrap="none"
        )
        self.hex_text.pack(fill="both", expand=True)
        self.hex_text.tag_config("highlight", background="#5a3e00", foreground="#ffd580")
        self.hex_text.tag_config("header", foreground="#888888")

        # Log panel (phải)
        log_frame = tk.LabelFrame(paned, text=" Log ", padx=4, pady=4)
        paned.add(log_frame, minsize=250)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, font=("Courier", 9), bg="#0d0d0d", fg="#aaaaaa",
            state="disabled", wrap="word"
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_config("info",    foreground="#5af")
        self.log_text.tag_config("success", foreground="#5c5")
        self.log_text.tag_config("warn",    foreground="#fa0")
        self.log_text.tag_config("error",   foreground="#f55")

    # ── helpers ──────────────────────────────────────────────

    def log(self, msg, tag=""):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def set_status(self, msg):
        self.status_var.set(msg)

    def render_hex(self, highlight_offset=-1):
        """Hiển thị toàn bộ data dưới dạng hex, tô màu dòng chứa DPB=."""
        self.hex_text.config(state="normal")
        self.hex_text.delete("1.0", "end")

        header = f"{'Offset':<12} {'00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F':<51}  ASCII\n"
        header += "─" * 75 + "\n"
        self.hex_text.insert("end", header, "header")

        for i in range(0, len(self.data), 16):
            chunk = self.data[i:i + 16]
            hex_bytes = " ".join(f"{b:02X}" for j, b in enumerate(chunk))
            # thêm khoảng cách giữa nhóm 8
            parts = [f"{b:02X}" for b in chunk]
            hex_str = " ".join(parts[:8]) + "  " + " ".join(parts[8:])
            ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            line = f"0x{i:08X}   {hex_str:<51}  {ascii_str}\n"

            tag = ""
            if highlight_offset != -1:
                row_start = (highlight_offset // 16) * 16
                if i == row_start or i == row_start + 16:
                    tag = "highlight"

            self.hex_text.insert("end", line, tag)

        # cuộn đến dòng highlight
        if highlight_offset != -1:
            row = highlight_offset // 16
            self.hex_text.see(f"{row + 3}.0")

        self.hex_text.config(state="disabled")

    # ── actions ──────────────────────────────────────────────

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Chọn file Access",
            filetypes=[("Access files", "*.mdb *.accdb"), ("All files", "*.*")]
        )
        if not path:
            return

        self.filepath = path
        self.path_var.set(path)
        self.log("─" * 40)
        self.log(f"Đọc file: {os.path.basename(path)}", "info")

        with open(path, "rb") as f:
            self.data = f.read()

        ext = os.path.splitext(path)[1].lower()
        size_kb = len(self.data) // 1024
        self.log(f"Kích thước: {size_kb} KB  |  Định dạng: {ext.upper()}")

        # Tìm DPB=
        self.dpb_offset = self.data.find(b"DPB=")
        if self.dpb_offset == -1:
            self.log("Không tìm thấy DPB= → file chưa có pass VBA!", "warn")
            self.set_status(f"Đã mở: {os.path.basename(path)} — Không có password VBA.")
        else:
            self.log(f"Tìm thấy DPB= tại offset: 0x{self.dpb_offset:08X}", "warn")
            self.log("File đang bị KHÓA VBA.", "warn")
            self.set_status(
                f"Đã mở: {os.path.basename(path)} — "
                f"DPB= tại 0x{self.dpb_offset:08X} — Nhấn [Unlock VBA] để xóa khóa."
            )

        self.render_hex(self.dpb_offset)

    def do_unlock(self):
        if self.data is None:
            messagebox.showwarning("Chưa mở file", "Hãy chọn file trước!")
            return
        if self.dpb_offset == -1:
            messagebox.showinfo("Không cần unlock", "File này không có password VBA.")
            return

        self.log("─" * 40)
        self.log("Bắt đầu patch...", "info")
        self.log(f"Thay byte tại 0x{self.dpb_offset:08X}: 'D' → 'x'")

        # Thay D (0x44) → x (0x78)
        patched = bytearray(self.data)
        patched[self.dpb_offset] = ord('x')
        self.data = bytes(patched)

        self.log("Patch thành công!", "success")
        self.log("Hãy mở lại file bằng Access → Access sẽ hỏi reset password → chọn Yes.", "info")
        self.set_status("Đã patch! Nhấn [Lưu file] để ghi ra đĩa.")
        self.render_hex(self.dpb_offset)

    def save_file(self):
        if self.data is None:
            messagebox.showwarning("Chưa có dữ liệu", "Hãy mở và unlock file trước!")
            return

        base, ext = os.path.splitext(self.filepath)
        default_name = os.path.basename(base) + "_unlocked" + ext

        out_path = filedialog.asksaveasfilename(
            title="Lưu file đã unlock",
            initialfile=default_name,
            defaultextension=ext,
            filetypes=[("Access files", "*.mdb *.accdb")]
        )
        if not out_path:
            return

        with open(out_path, "wb") as f:
            f.write(self.data)

        self.log("─" * 40)
        self.log(f"Đã lưu: {out_path}", "success")
        self.set_status(f"Lưu thành công: {os.path.basename(out_path)}")
        messagebox.showinfo("Xong!", f"File đã lưu tại:\n{out_path}\n\nBây giờ mở bằng Access, vào VBA Editor → Access sẽ hỏi reset password → chọn Yes.")

if __name__ == "__main__":
    root = tk.Tk()
    app = VBAUnlocker(root)
    root.mainloop()