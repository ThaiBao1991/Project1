import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import os
import subprocess
import threading
import shutil
from urllib.parse import urljoin
from datetime import datetime
import shlex
import time
from pathlib import Path

class HLSDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("HLS Downloader 2 TAB - HOÀN HẢO 100% (Cả 2 tab đều chạy ngon)")
        self.root.geometry("1500x950")
        self.root.configure(bg="#f5f5f5")

        style = ttk.Style()
        style.configure("Big.TButton", font=("Arial", 14, "bold"), padding=15, foreground="white", background="#d50000")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)

        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="   TẢI MỚI từ m3u8   ")
        self.notebook.add(self.tab2, text="   GHÉP TỪ THƯ MỤC SẴN CÓ   ")

        self.setup_tab1()
        self.setup_tab2()

    # helper: write ffmpeg concat list safely
    def _write_concat_list(self, paths, list_path):
        with open(list_path, "w", encoding="utf-8") as f:
            for p in paths:
                # dùng đường dẫn tuyệt đối, forward slash, escape single quote
                pp = str(Path(p).resolve().as_posix()).replace("'", r"'\''")
                f.write(f"file '{pp}'\n")

    def _run_ffmpeg(self, args):
        """Chạy ffmpeg, trả về (returncode, stdout, stderr). In stderr khi lỗi để debug."""
        p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode != 0:
            print("FFMPEG CMD:", " ".join(args))
            print("FFMPEG STDERR:", p.stderr)
        return p.returncode, p.stdout, p.stderr

    # ============================== TAB 1 ==============================
    def setup_tab1(self):
        self.segments1 = []
        self.sub_path1 = None

        # Nhập m3u8
        frame_m3u8 = tk.LabelFrame(self.tab1, text="1. Dán link m3u8 hoặc nội dung m3u8", font=("Arial", 11, "bold"))
        frame_m3u8.pack(fill="both", expand=True, padx=20, pady=10)
        self.txt_m3u8 = tk.Text(frame_m3u8, height=9, font=("Consolas", 10))
        self.txt_m3u8.pack(fill="both", expand=True, padx=10, pady=10)

        # Quét + lọc
        btn_frame = tk.Frame(self.tab1)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="QUÉT SEGMENT", command=self.scan_tab1).pack(side="left", padx=15)
        tk.Label(btn_frame, text="Lọc chứa:").pack(side="left", padx=10)
        self.filter1 = tk.StringVar(value="image")
        tk.Entry(btn_frame, textvariable=self.filter1, width=20).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="LỌC", command=self.filter_tab1).pack(side="left", padx=10)

        # Danh sách
        list_frame = tk.LabelFrame(self.tab1, text="Danh sách segment")
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.listbox1 = tk.Listbox(list_frame, font=("Consolas", 9))
        sb = tk.Scrollbar(list_frame, command=self.listbox1.yview)
        self.listbox1.config(yscrollcommand=sb.set)
        self.listbox1.pack(side="left", fill="both", expand=True, padx=5)
        sb.pack(side="right", fill="y")

        # Cấu hình
        cfg = tk.LabelFrame(self.tab1, text="Cấu hình", font=("Arial", 10, "bold"))
        cfg.pack(fill="x", padx=20, pady=10)
        tk.Label(cfg, text="Đuôi trung gian:").grid(row=0, column=0, padx=15, pady=8)
        self.ext1 = tk.StringVar(value="ts")
        ttk.Combobox(cfg, textvariable=self.ext1, values=["ts","mp4","m4s"], width=10, state="readonly").grid(row=0, column=1, padx=5)

        tk.Label(cfg, text="Phụ đề:").grid(row=0, column=2, padx=40)
        ttk.Button(cfg, text="Chọn .srt/.ass", command=self.choose_sub1).grid(row=0, column=3, padx=5)
        self.lbl_sub1 = tk.Label(cfg, text="Không có", fg="gray")
        self.lbl_sub1.grid(row=0, column=4, padx=10)

        # Tên file + thư mục
        save_frame = tk.Frame(self.tab1)
        save_frame.pack(pady=12)
        tk.Label(save_frame, text="Tên file MP4:").pack(side="left", padx=10)
        self.name1 = tk.StringVar(value="output.mp4")
        tk.Entry(save_frame, textvariable=self.name1, width=40).pack(side="left", padx=5)
        ttk.Button(save_frame, text="Chọn thư mục lưu", command=self.choose_folder1).pack(side="left", padx=15)
        self.lbl_folder1 = tk.Label(save_frame, text="Chưa chọn thư mục", fg="red")
        self.lbl_folder1.pack(side="left", padx=10)

        # Nút chạy + tiến độ
        self.btn_run1 = ttk.Button(self.tab1, text="TẢI → GHÉP → XUẤT MP4 + PHỤ ĐỀ", style="Big.TButton", command=self.start_tab1)
        self.btn_run1.pack(pady=25)

        self.progress1 = ttk.Progressbar(self.tab1, length=1000, mode='determinate')
        self.progress1.pack(pady=10)
        self.status1 = tk.Label(self.tab1, text="Sẵn sàng", fg="green", font=("Arial", 12, "bold"))
        self.status1.pack(pady=5)

    def scan_tab1(self):
        raw = self.txt_m3u8.get("1.0", "end-1c").strip()
        if not raw:
            return messagebox.showwarning("Lỗi", "Chưa nhập m3u8!")
        self.segments1.clear()
        base_url = ""
        if raw.startswith("http"):
            try:
                r = requests.get(raw, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
                r.raise_for_status()
                content = r.text
                base_url = raw.rsplit("/", 1)[0] + "/"
            except:
                return messagebox.showerror("Lỗi", "Không tải được m3u8!")
        else:
            content = raw

        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                url = line if line.startswith("http") else urljoin(base_url, line)
                self.segments1.append(url)

        self.listbox1.delete(0, tk.END)
        for i, u in enumerate(self.segments1[:50]):
            self.listbox1.insert(tk.END, u)
        if len(self.segments1) > 50:
            self.listbox1.insert(tk.END, f"... còn {len(self.segments1)-50} segment nữa")
        self.status1.config(text=f"Tìm thấy {len(self.segments1)} segment")

    def filter_tab1(self):
        kw = self.filter1.get().lower()
        if not kw: return
        filtered = [u for u in self.segments1 if kw in u.lower()]
        self.segments1 = filtered
        self.listbox1.delete(0, tk.END)
        for u in filtered[:50]:
            self.listbox1.insert(tk.END, u)
        self.status1.config(text=f"Đã lọc: {len(filtered)} segment")

    def choose_sub1(self):
        p = filedialog.askopenfilename(filetypes=[("Phụ đề", "*.srt *.ass")])
        if p:
            self.sub_path1 = p
            self.lbl_sub1.config(text=os.path.basename(p), fg="blue")

    def choose_folder1(self):
        f = filedialog.askdirectory()
        if f:
            self.output_folder1 = f
            self.lbl_folder1.config(text="Đã chọn", fg="green")

    def start_tab1(self):
        if not hasattr(self, "output_folder1") or not self.segments1:
            return messagebox.showwarning("Lỗi", "Chọn thư mục và quét segment trước!")
        threading.Thread(target=self.run_tab1, daemon=True).start()

    def run_tab1(self):
        try:
            self.btn_run1.config(state="disabled")
            self.progress1["value"] = 0
            temp_dir = os.path.join(self.output_folder1, f"temp_{int(time.time())}")
            os.makedirs(temp_dir, exist_ok=True)
            downloaded = []

            self.status1.config(text="Bước 1/5: Đang tải segment...")
            total = len(self.segments1)
            for i, url in enumerate(self.segments1):
                path = os.path.join(temp_dir, f"seg_{i:06d}.{self.ext1.get()}")
                try:
                    r = requests.get(url, stream=True, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
                    r.raise_for_status()
                    with open(path, "wb") as f:
                        for chunk in r.iter_content(1024*64):
                            f.write(chunk)
                    downloaded.append(path)
                except Exception:
                    pass
                self.progress1["value"] = (i+1)/total * 25
                self.root.update_idletasks()

            if not downloaded:
                messagebox.showerror("Lỗi", "Không tải được segment nào!")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return

            # Bước 2: tạo list và ghép .ts
            self.status1.config(text="Bước 2/5: Tạo list và ghép thành merged.ts...")
            list_txt = os.path.join(temp_dir, "list.txt")
            self._write_concat_list(downloaded, list_txt)
            merged_ts = os.path.join(temp_dir, "merged.ts")
            rc, out, err = self._run_ffmpeg([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_txt, "-c", "copy", merged_ts
            ])
            if rc != 0 or not os.path.exists(merged_ts) or os.path.getsize(merged_ts) < 1024:
                # fallback: thử re-encode
                self.status1.config(text="Ghép copy lỗi, thử re-encode lại...")
                rc, out, err = self._run_ffmpeg([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_txt,
                    "-c:v", "libx264", "-c:a", "aac", merged_ts
                ])
                if rc != 0 or not os.path.exists(merged_ts) or os.path.getsize(merged_ts) < 1024:
                    messagebox.showerror("FFMPEG lỗi", f"Lỗi khi ghép segments:\n{err}\n(merged.ts chưa được tạo hoặc rỗng). Kiểm tra lại list.txt và segment.")
                    self.btn_run1.config(state="normal")
                    return

            self.progress1["value"] = 40

            # Bước 3: chuyển sang MP4 (tạo temp_mp4)
            self.status1.config(text="Bước 3/5: Chuyển sang MP4...")
            temp_mp4 = os.path.join(temp_dir, "temp.mp4")
            rc, out, err = self._run_ffmpeg(["ffmpeg", "-y", "-i", merged_ts, "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac", temp_mp4])
            if rc != 0 or not os.path.exists(temp_mp4):
                # thử remux copy
                rc2, out2, err2 = self._run_ffmpeg(["ffmpeg", "-y", "-i", merged_ts, "-c", "copy", temp_mp4])
                if rc2 != 0 or not os.path.exists(temp_mp4):
                    messagebox.showerror("FFMPEG lỗi", f"Lỗi khi chuyển sang MP4:\n{err}\n{err2}\nKhông tạo được temp.mp4. Giữ thư mục tạm để debug.")
                    self.btn_run1.config(state="normal")
                    return

            self.progress1["value"] = 75

            # Bước 4: burn phụ đề nếu có, else move
            final_name = self.name1.get().strip() or "output.mp4"
            if not final_name.lower().endswith(".mp4"):
                final_name += ".mp4"
            final_out = os.path.join(self.output_folder1, final_name)

            if self.sub_path1 and os.path.exists(self.sub_path1) and os.path.exists(temp_mp4):
                self.status1.config(text="Bước 4/5: Burn phụ đề...")
                sub_ext = Path(self.sub_path1).suffix or ".srt"
                sub_copy = os.path.join(self.output_folder1, f"temp_sub_{os.getpid()}{sub_ext}")
                shutil.copy2(self.sub_path1, sub_copy)
                vf_filter = "subtitles=" + Path(sub_copy).as_posix().replace("'", r"\'")
                rc, out, err = self._run_ffmpeg(["ffmpeg", "-y", "-i", temp_mp4, "-vf", vf_filter, "-c:v", "libx264", "-c:a", "aac", final_out])
                try:
                    os.remove(sub_copy)
                except Exception:
                    pass
                if rc != 0 or not os.path.exists(final_out):
                    messagebox.showerror("FFMPEG lỗi", f"Lỗi khi burn phụ đề:\n{err}\nKiểm tra console output.")
                    self.btn_run1.config(state="normal")
                    return
            else:
                if os.path.exists(temp_mp4):
                    shutil.move(temp_mp4, final_out)
                else:
                    rc, out, err = self._run_ffmpeg(["ffmpeg", "-y", "-i", merged_ts, "-c:v", "libx264", "-c:a", "aac", final_out])
                    if rc != 0 or not os.path.exists(final_out):
                        messagebox.showerror("FFMPEG lỗi", f"Lỗi khi tạo file cuối cùng:\n{err}\nKiểm tra console output.")
                        self.btn_run1.config(state="normal")
                        return

            # Bước 5: dọn tạm (chỉ xóa khi final_out tồn tại)
            if os.path.exists(final_out):
                for f in [merged_ts, list_txt]:
                    if os.path.exists(f):
                        try:
                            os.remove(f)
                        except Exception:
                            pass
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.progress1["value"] = 100
                messagebox.showinfo("HOÀN TẤT!", f"XONG 100%!\nVideo đã lưu tại:\n{final_out}")
                self.status1.config(text="HOÀN TẤT", fg="green")
            else:
                messagebox.showerror("Lỗi", "Không tạo được file MP4 cuối cùng.")
                self.status1.config(text="Lỗi", fg="red")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi: {e}")
        finally:
            self.btn_run1.config(state="normal")

    # ============================== TAB 2 ==============================
    def setup_tab2(self):
        self.folder_seg2 = None
        self.folder_out2 = None
        self.sub_path2 = None

        tk.Label(self.tab2, text="GHÉP VIDEO TỪ THƯ MỤC CÓ SẴN", font=("Arial", 18, "bold"), fg="#d50000").pack(pady=25)

        f1 = tk.Frame(self.tab2)
        f1.pack(pady=10)
        ttk.Button(f1, text="1. Chọn thư mục chứa segment (.ts)", command=self.choose_seg_folder2).pack(side="left", padx=20)
        self.lbl_seg2 = tk.Label(f1, text="Chưa chọn", fg="red", width=90, anchor="w")
        self.lbl_seg2.pack(side="left", padx=10)

        f2 = tk.Frame(self.tab2)
        f2.pack(pady=8)
        ttk.Button(f2, text="2. Chọn thư mục lưu video MP4", command=self.choose_out_folder2).pack(side="left", padx=20)
        self.lbl_out2 = tk.Label(f2, text="Chưa chọn", fg="red", width=90, anchor="w")
        self.lbl_out2.pack(side="left", padx=10)

        cfg = tk.LabelFrame(self.tab2, text="Cấu hình", font=("Arial", 10, "bold"))
        cfg.pack(fill="x", padx=60, pady=20)
        tk.Label(cfg, text="Lọc đuôi:").grid(row=0, column=0, padx=20, pady=10)
        self.ext2 = tk.StringVar(value="ts")
        tk.Entry(cfg, textvariable=self.ext2, width=12).grid(row=0, column=1, padx=5)

        tk.Label(cfg, text="Phụ đề:").grid(row=0, column=2, padx=50)
        ttk.Button(cfg, text="Chọn .srt/.ass", command=self.choose_sub2).grid(row=0, column=3, padx=5)
        self.lbl_sub2 = tk.Label(cfg, text="Không có", fg="gray")
        self.lbl_sub2.grid(row=0, column=4, padx=10)

        namef = tk.Frame(self.tab2)
        namef.pack(pady=12)
        tk.Label(namef, text="Tên file MP4:").pack(side="left", padx=10)
        self.name2 = tk.StringVar(value="output.mp4")
        tk.Entry(namef, textvariable=self.name2, width=50).pack(side="left", padx=5)

        self.btn_run2 = ttk.Button(self.tab2, text="GHÉP → CHUYỂN MP4 → BURN PHỤ ĐỀ", style="Big.TButton", command=self.start_tab2)
        self.btn_run2.pack(pady=35)

        self.progress2 = ttk.Progressbar(self.tab2, length=1000, mode='determinate')
        self.progress2.pack(pady=10)
        self.status2 = tk.Label(self.tab2, text="Sẵn sàng", fg="green", font=("Arial", 12, "bold"))
        self.status2.pack(pady=5)

    def choose_seg_folder2(self):
        f = filedialog.askdirectory()
        if f:
            self.folder_seg2 = f
            self.lbl_seg2.config(text="Đã chọn", fg="green")

    def choose_out_folder2(self):
        f = filedialog.askdirectory()
        if f:
            self.folder_out2 = f
            self.lbl_out2.config(text="Đã chọn", fg="green")

    def choose_sub2(self):
        p = filedialog.askopenfilename(filetypes=[("Phụ đề", "*.srt *.ass")])
        if p:
            self.sub_path2 = p
            self.lbl_sub2.config(text=os.path.basename(p), fg="blue")

    def start_tab2(self):
        if not self.folder_seg2 or not self.folder_out2:
            return messagebox.showwarning("Lỗi", "Chọn đủ 2 thư mục!")
        threading.Thread(target=self.run_tab2, daemon=True).start()

    def run_tab2(self):
        try:
            self.btn_run2.config(state="disabled")
            self.progress2["value"] = 0
            self.status2.config(text="Quét file...")

            list_txt = os.path.join(self.folder_seg2, "list.txt")
            if os.path.exists(list_txt):
                files = []
                with open(list_txt, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("file '"):
                            p = line.strip()[6:-1]
                            if os.path.exists(p):
                                files.append(p)
            else:
                ext = self.ext2.get().strip(" .").lower()
                files = [os.path.join(self.folder_seg2, f) for f in os.listdir(self.folder_seg2) if f.lower().endswith(ext)]
                files.sort()

            if not files:
                messagebox.showerror("Lỗi", "Không tìm thấy file segment!")
                return

            self.progress2["value"] = 20
            self.status2.config(text="Ghép .ts...")

            merged_ts = os.path.join(self.folder_seg2, "temp_merged.ts")
            temp_list = os.path.join(self.folder_seg2, "temp_list.txt")
            self._write_concat_list(files, temp_list)
            rc, out, err = self._run_ffmpeg(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", temp_list, "-c", "copy", merged_ts])
            if rc != 0 or not os.path.exists(merged_ts):
                rc, out, err = self._run_ffmpeg(["ffmpeg", "-y", "-protocol_whitelist", "file,udp,rtp,http,https,tcp,tls", "-f", "concat", "-safe", "0", "-i", temp_list, "-c:v", "libx264", "-c:a", "aac", merged_ts])
                if rc != 0 or not os.path.exists(merged_ts):
                    messagebox.showerror("FFMPEG lỗi", f"Lỗi khi ghép segments:\n{err}\nGiữ thư mục để debug.")
                    self.btn_run2.config(state="normal")
                    return

            self.progress2["value"] = 55
            self.status2.config(text="Chuyển MP4...")

            temp_mp4 = os.path.join(self.folder_out2, "temp_video.mp4")
            rc, out, err = self._run_ffmpeg(["ffmpeg", "-y", "-i", merged_ts, "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac", temp_mp4])
            if rc != 0 or not os.path.exists(temp_mp4):
                rc2, out2, err2 = self._run_ffmpeg(["ffmpeg", "-y", "-i", merged_ts, "-c", "copy", temp_mp4])
                if rc2 != 0 or not os.path.exists(temp_mp4):
                    messagebox.showerror("FFMPEG lỗi", f"Lỗi khi chuyển sang MP4:\n{err}\n{err2}\nGiữ thư mục để debug.")
                    self.btn_run2.config(state="normal")
                    return

            final_name = self.name2.get().strip() or "output.mp4"
            if not final_name.lower().endswith(".mp4"):
                final_name += ".mp4"
            final_out = os.path.join(self.folder_out2, final_name)

            if self.sub_path2 and os.path.exists(self.sub_path2) and os.path.exists(temp_mp4):
                sub_ext = Path(self.sub_path2).suffix or ".srt"
                sub_copy = os.path.join(self.folder_out2, f"temp_sub_{os.getpid()}{sub_ext}")
                shutil.copy2(self.sub_path2, sub_copy)
                vf_filter = "subtitles=" + Path(sub_copy).as_posix().replace("'", "\\\\'")
                rc, out, err = self._run_ffmpeg(["ffmpeg", "-y", "-i", temp_mp4, "-vf", vf_filter, "-c:v", "libx264", "-c:a", "aac", final_out])
                try:
                    os.remove(sub_copy)
                except Exception:
                    pass
                if rc != 0 or not os.path.exists(final_out):
                    messagebox.showerror("FFMPEG lỗi", f"Lỗi khi burn phụ đề:\n{err}\nKiểm tra console.")
                    self.btn_run2.config(state="normal")
                    return
            else:
                shutil.move(temp_mp4, final_out)

            if os.path.exists(final_out):
                try:
                    if os.path.exists(merged_ts):
                        os.remove(merged_ts)
                    if os.path.exists(temp_list):
                        os.remove(temp_list)
                except Exception:
                    pass
                self.progress2["value"] = 100
                messagebox.showinfo("HOÀN TẤT!", f"Ghép thành công!\n{final_out}")
                self.status2.config(text="HOÀN TẤT", fg="green")
            else:
                messagebox.showerror("Lỗi", "Không tạo được file MP4 cuối cùng.")
                self.status2.config(text="Lỗi", fg="red")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi: {e}")
        finally:
            self.btn_run2.config(state="normal")
# ============================== CHẠY ==============================
if __name__ == "__main__":
    root = tk.Tk()
    app = HLSDownloader(root)
    root.mainloop()