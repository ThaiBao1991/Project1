import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import os
import subprocess
import threading
import shutil
from urllib.parse import urljoin, urlparse
from datetime import datetime
import json
import time
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_file = "hls_downloader_config.json"
        self.config = self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return self.get_default_config()
        return self.get_default_config()
    
    def get_default_config(self):
        return {
            "domains": {},  # lưu config theo domain
            "extensions": ["ts", "mp4", "m4s"],  # danh sách đuôi file đã biết
            "processing_methods": {
                "concat_copy": True,
                "concat_genpts": True,
                "concat_bsf": True,
                "concat_to_ts_then_mp4": True,
                "reencode_video": True,
                "reencode_both": True,
                "ignore_errors": True
            }
        }
    
    def save_config(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get_domain_config(self, url):
        domain = urlparse(url).netloc
        if domain not in self.config["domains"]:
            base_url = f"{urlparse(url).scheme}://{domain}/"
            self.config["domains"][domain] = {
                "base_url": base_url,
                "extensions": [],
                "last_used_ext": "ts",
                "last_processed": None
            }
            self.save_config()
        return self.config["domains"][domain]
    
    def add_extension(self, ext):
        if ext not in self.config["extensions"]:
            self.config["extensions"].append(ext)
            self.save_config()
    
    def save_domain_ext(self, url, ext):
        domain_config = self.get_domain_config(url)
        if ext not in domain_config["extensions"]:
            domain_config["extensions"].append(ext)
        domain_config["last_used_ext"] = ext
        self.save_config()


class HLSDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("HLS Downloader Pro - Đa phương pháp + Lưu config")
        self.root.geometry("1600x1000")
        self.root.configure(bg="#f5f5f5")
        
        self.config_manager = ConfigManager()
        
        style = ttk.Style()
        style.configure("Big.TButton", font=("Arial", 14, "bold"), padding=15)
        style.configure("Success.TButton", font=("Arial", 12, "bold"), padding=10, foreground="green")
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook)  # Tab quản lý config
        self.notebook.add(self.tab1, text="   TẢI MỚI từ m3u8   ")
        self.notebook.add(self.tab2, text="   GHÉP TỪ THƯ MỤC SẴN CÓ   ")
        self.notebook.add(self.tab3, text="   QUẢN LÝ CONFIG   ")
        
        self.setup_tab1()
        self.setup_tab2()
        self.setup_tab3()
    
    def _write_concat_list(self, paths, list_path):
        with open(list_path, "w", encoding="utf-8") as f:
            for p in paths:
                pp = str(Path(p).resolve().as_posix()).replace("'", r"'\''")
                f.write(f"file '{pp}'\n")
    
    def _run_ffmpeg_with_methods(self, input_file, output_file, is_concat=False, segment_files=None):
        """Thử nhiều phương pháp ffmpeg khác nhau"""
        methods = []
        
        if is_concat and segment_files:
            # Các phương pháp ghép file
            methods = [
                # Method 1: Copy trực tiếp
                lambda: self._run_ffmpeg([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", input_file,
                    "-c", "copy", output_file
                ]),
                # Method 2: Thêm genpts
                lambda: self._run_ffmpeg([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", input_file,
                    "-c", "copy", "-fflags", "+genpts", output_file
                ]),
                # Method 3: Thêm BSF audio
                lambda: self._run_ffmpeg([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", input_file,
                    "-c", "copy", "-bsf:a", "aac_adtstoasc", "-fflags", "+genpts", output_file
                ]),
                # Method 4: Ghép thành TS trước rồi sang MP4
                lambda: self._concat_to_ts_then_mp4(segment_files, output_file),
                # Method 5: Re-encode video
                lambda: self._run_ffmpeg([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", input_file,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "copy", output_file
                ]),
                # Method 6: Re-encode cả video và audio
                lambda: self._run_ffmpeg([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", input_file,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac", output_file
                ]),
                # Method 7: Bỏ qua lỗi
                lambda: self._run_ffmpeg([
                    "ffmpeg", "-y", "-err_detect", "ignore_err", "-f", "concat", "-safe", "0",
                    "-i", input_file, "-c:v", "libx264", "-preset", "fast", "-c:a", "copy", output_file
                ])
            ]
        else:
            # Các phương pháp xử lý file đơn
            methods = [
                lambda: self._run_ffmpeg([
                    "ffmpeg", "-y", "-i", input_file, "-c", "copy", output_file
                ]),
                lambda: self._run_ffmpeg([
                    "ffmpeg", "-y", "-i", input_file, "-c:v", "libx264", "-preset", "fast",
                    "-crf", "23", "-c:a", "copy", output_file
                ]),
                lambda: self._run_ffmpeg([
                    "ffmpeg", "-y", "-i", input_file, "-c:v", "libx264", "-preset", "fast",
                    "-crf", "23", "-c:a", "aac", output_file
                ]),
                lambda: self._run_ffmpeg([
                    "ffmpeg", "-y", "-err_detect", "ignore_err", "-i", input_file,
                    "-c:v", "libx264", "-preset", "fast", "-c:a", "copy", output_file
                ])
            ]
        
        for idx, method in enumerate(methods):
            try:
                rc, out, err = method()
                if rc == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 1024:
                    return True, f"Method {idx + 1} thành công"
            except:
                continue
        
        return False, "Tất cả phương pháp đều thất bại"
    
    def _concat_to_ts_then_mp4(self, segment_files, output_file):
        """Ghép thành TS trước rồi chuyển sang MP4"""
        temp_dir = os.path.dirname(output_file)
        temp_ts = os.path.join(temp_dir, f"temp_concat_{int(time.time())}.ts")
        temp_list = os.path.join(temp_dir, "temp_concat_list.txt")
        
        try:
            self._write_concat_list(segment_files, temp_list)
            rc1, _, _ = self._run_ffmpeg([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", temp_list,
                "-c", "copy", "-f", "mpegts", temp_ts
            ])
            
            if rc1 == 0 and os.path.exists(temp_ts):
                rc2, _, _ = self._run_ffmpeg([
                    "ffmpeg", "-y", "-i", temp_ts, "-c", "copy",
                    "-bsf:a", "aac_adtstoasc", output_file
                ])
                return rc2, "", ""
            return 1, "", ""
        finally:
            for f in [temp_ts, temp_list]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass
    
    def detect_file_extension(self, url):
        """Phát hiện đuôi file từ URL hoặc nội dung"""
        # Thử lấy từ URL
        parsed = urlparse(url)
        path = parsed.path
        if '.' in path:
            ext = path.split('.')[-1].split('?')[0].lower()
            if ext and len(ext) <= 4:
                return ext
        
        # Thử download 1 segment để kiểm tra
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            content_type = response.headers.get('Content-Type', '')
            if 'video/mp4' in content_type:
                return 'mp4'
            elif 'video/mp2t' in content_type:
                return 'ts'
        except:
            pass
        
        return 'ts'  # mặc định
    
    # ============================== TAB 1 ==============================
    def setup_tab1(self):
        self.segments1 = []
        self.sub_path1 = None
        self.current_domain_config = None
        
        # Frame nhập liệu chính
        main_frame = tk.Frame(self.tab1)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Nhập m3u8
        frame_m3u8 = tk.LabelFrame(main_frame, text="1. Dán link m3u8 hoặc nội dung m3u8", font=("Arial", 11, "bold"))
        frame_m3u8.pack(fill="both", expand=True, pady=(0, 10))
        self.txt_m3u8 = tk.Text(frame_m3u8, height=8, font=("Consolas", 10))
        self.txt_m3u8.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Các nút chức năng
        btn_frame1 = tk.Frame(main_frame)
        btn_frame1.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame1, text="QUÉT SEGMENT", command=self.scan_tab1).pack(side="left", padx=5)
        ttk.Button(btn_frame1, text="TẢI THỬ 1 SEGMENT", command=self.test_single_segment).pack(side="left", padx=5)
        
        tk.Label(btn_frame1, text="Lọc chứa:").pack(side="left", padx=(20, 5))
        self.filter1 = tk.StringVar(value="")
        tk.Entry(btn_frame1, textvariable=self.filter1, width=25).pack(side="left", padx=5)
        ttk.Button(btn_frame1, text="LỌC", command=self.filter_tab1).pack(side="left", padx=5)
        ttk.Button(btn_frame1, text="RESET LỌC", command=self.reset_filter_tab1).pack(side="left", padx=5)
        
        # Tùy chọn xử lý
        options_frame = tk.LabelFrame(main_frame, text="Tùy chọn xử lý", font=("Arial", 11, "bold"))
        options_frame.pack(fill="x", pady=10)
        
        # Hàng 1
        row1 = tk.Frame(options_frame)
        row1.pack(fill="x", padx=10, pady=5)
        
        tk.Label(row1, text="Chế độ:").pack(side="left", padx=5)
        self.processing_mode = tk.StringVar(value="download_and_merge")
        modes = [("Tải + Ghép", "download_and_merge"), ("Chỉ tải segment", "download_only"), ("Chỉ ghép (đã có segment)", "merge_only")]
        for text, mode in modes:
            tk.Radiobutton(row1, text=text, variable=self.processing_mode, value=mode).pack(side="left", padx=10)
        
        # Hàng 2
        row2 = tk.Frame(options_frame)
        row2.pack(fill="x", padx=10, pady=5)
        
        tk.Label(row2, text="Đuôi trung gian:").pack(side="left", padx=5)
        self.ext1 = tk.StringVar(value="ts")
        ext_combo = ttk.Combobox(row2, textvariable=self.ext1, values=self.config_manager.config["extensions"], width=10)
        ext_combo.pack(side="left", padx=5)
        ttk.Button(row2, text="Phát hiện tự động", command=self.auto_detect_ext).pack(side="left", padx=5)
        
        tk.Label(row2, text="Phụ đề:").pack(side="left", padx=(30, 5))
        ttk.Button(row2, text="Chọn .srt/.ass", command=self.choose_sub1).pack(side="left", padx=5)
        self.lbl_sub1 = tk.Label(row2, text="Không có", fg="gray")
        self.lbl_sub1.pack(side="left", padx=10)
        
        # Danh sách segment
        list_frame = tk.LabelFrame(main_frame, text="Danh sách segment")
        list_frame.pack(fill="both", expand=True, pady=10)
        
        list_header = tk.Frame(list_frame)
        list_header.pack(fill="x", padx=5, pady=5)
        tk.Label(list_header, text=f"Tổng số: 0", fg="blue", font=("Arial", 10, "bold")).pack(side="left")
        
        self.listbox1 = tk.Listbox(list_frame, font=("Consolas", 9))
        sb = tk.Scrollbar(list_frame, command=self.listbox1.yview)
        self.listbox1.config(yscrollcommand=sb.set)
        self.listbox1.pack(side="left", fill="both", expand=True, padx=5)
        sb.pack(side="right", fill="y")
        
        # Thông tin output
        output_frame = tk.Frame(main_frame)
        output_frame.pack(fill="x", pady=10)
        
        tk.Label(output_frame, text="Tên file MP4:").pack(side="left", padx=5)
        self.name1 = tk.StringVar(value="output.mp4")
        tk.Entry(output_frame, textvariable=self.name1, width=40).pack(side="left", padx=5)
        
        ttk.Button(output_frame, text="Chọn thư mục lưu", command=self.choose_folder1).pack(side="left", padx=10)
        self.lbl_folder1 = tk.Label(output_frame, text="Chưa chọn (dùng thư mục hiện tại)", fg="orange")
        self.lbl_folder1.pack(side="left", padx=10)
        
        ttk.Button(output_frame, text="LƯU CONFIG", command=self.save_current_config).pack(side="right", padx=10)
        ttk.Button(output_frame, text="TẢI CONFIG", command=self.load_config_for_url).pack(side="right", padx=10)
        
        # Nút chạy
        self.btn_run1 = ttk.Button(main_frame, text="BẮT ĐẦU XỬ LÝ", style="Big.TButton", command=self.start_tab1)
        self.btn_run1.pack(pady=20)
        
        # Progress
        self.progress1 = ttk.Progressbar(main_frame, length=1000, mode='determinate')
        self.progress1.pack(pady=10)
        self.status1 = tk.Label(main_frame, text="Sẵn sàng", fg="green", font=("Arial", 12, "bold"))
        self.status1.pack(pady=5)
    
    def scan_tab1(self):
        raw = self.txt_m3u8.get("1.0", "end-1c").strip()
        if not raw:
            return messagebox.showwarning("Lỗi", "Chưa nhập m3u8!")
        
        self.segments1.clear()
        base_url = ""
        
        if raw.startswith("http"):
            try:
                self.status1.config(text="Đang tải m3u8...", fg="blue")
                self.root.update()
                
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(raw, timeout=20, headers=headers)
                r.raise_for_status()
                content = r.text
                base_url = raw.rsplit("/", 1)[0] + "/"
                
                # Lấy config cho domain này
                self.current_domain_config = self.config_manager.get_domain_config(raw)
                self.status1.config(text=f"Domain: {urlparse(raw).netloc}", fg="green")
                
            except Exception as e:
                return messagebox.showerror("Lỗi", f"Không tải được m3u8: {e}")
        else:
            content = raw
        
        # Parse m3u8
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                if line.startswith("http"):
                    url = line
                else:
                    url = urljoin(base_url, line)
                self.segments1.append(url)
        
        self.update_listbox1()
        self.status1.config(text=f"Tìm thấy {len(self.segments1)} segment")
        
        # Tự động phát hiện đuôi file từ segment đầu tiên
        if self.segments1:
            self.auto_detect_ext()
    
    def test_single_segment(self):
        """Tải thử 1 segment để kiểm tra đuôi file và khả năng tải"""
        if not self.segments1:
            messagebox.showwarning("Lỗi", "Chưa có segment nào để test!")
            return
        
        test_url = self.segments1[0]
        ext = self.ext1.get()
        
        self.status1.config(text="Đang test segment...", fg="orange")
        self.root.update()
        
        try:
            response = requests.get(test_url, timeout=30, stream=True, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            
            # Lấy nội dung đầu tiên
            first_chunk = next(response.iter_content(1024), None)
            
            # Phát hiện magic bytes
            if first_chunk:
                if first_chunk[:4] == b'\x00\x00\x00\x01':  # MPEG-TS
                    detected_ext = 'ts'
                elif first_chunk[:8] == b'\x00\x00\x00\x18ftyp':  # MP4
                    detected_ext = 'mp4'
                else:
                    detected_ext = ext
                
                if detected_ext != ext:
                    msg = f"Phát hiện đuôi file: .{detected_ext} (khác với .{ext})\nCó muốn đổi không?"
                    if messagebox.askyesno("Phát hiện", msg):
                        self.ext1.set(detected_ext)
                        self.config_manager.add_extension(detected_ext)
                        if self.current_domain_config:
                            self.config_manager.save_domain_ext(self.txt_m3u8.get("1.0", "end-1c").strip(), detected_ext)
            
            self.status1.config(text="Test thành công!", fg="green")
            messagebox.showinfo("Thành công", f"Segment có thể tải được!\nKích thước: {len(first_chunk) if first_chunk else 0} bytes")
            
        except Exception as e:
            self.status1.config(text="Test thất bại", fg="red")
            messagebox.showerror("Lỗi", f"Không thể tải segment:\n{e}")
    
    def auto_detect_ext(self):
        """Tự động phát hiện đuôi file từ segment đầu tiên"""
        if not self.segments1:
            return
        
        test_url = self.segments1[0]
        try:
            # Thử lấy từ URL
            parsed = urlparse(test_url)
            if '.' in parsed.path:
                ext = parsed.path.split('.')[-1].split('?')[0].lower()
                if ext in ['ts', 'mp4', 'm4s', 'mpeg', 'mpg', 'avi', 'mkv']:
                    self.ext1.set(ext)
                    self.status1.config(text=f"Phát hiện đuôi file: .{ext}", fg="blue")
                    return
            
            # Thử HEAD request
            response = requests.head(test_url, timeout=10, allow_redirects=True)
            content_type = response.headers.get('Content-Type', '')
            if 'video/mp4' in content_type:
                self.ext1.set('mp4')
            elif 'video/mp2t' in content_type:
                self.ext1.set('ts')
        except:
            pass
    
    def filter_tab1(self):
        kw = self.filter1.get().lower()
        if not kw:
            return
        filtered = [u for u in self.segments1 if kw in u.lower()]
        self.segments1 = filtered
        self.update_listbox1()
        self.status1.config(text=f"Đã lọc: {len(filtered)} segment")
    
    def reset_filter_tab1(self):
        self.filter1.set("")
        self.scan_tab1()
    
    def update_listbox1(self):
        self.listbox1.delete(0, tk.END)
        for i, u in enumerate(self.segments1[:100]):
            self.listbox1.insert(tk.END, f"[{i:04d}] {u[:100]}...")
        if len(self.segments1) > 100:
            self.listbox1.insert(tk.END, f"... còn {len(self.segments1)-100} segment nữa")
    
    def choose_sub1(self):
        p = filedialog.askopenfilename(filetypes=[("Phụ đề", "*.srt *.ass")])
        if p:
            self.sub_path1 = p
            self.lbl_sub1.config(text=os.path.basename(p), fg="blue")
    
    def choose_folder1(self):
        f = filedialog.askdirectory()
        if f:
            self.output_folder1 = f
            self.lbl_folder1.config(text=f"Đã chọn: {f}", fg="green")
        else:
            self.output_folder1 = os.getcwd()
            self.lbl_folder1.config(text=f"Dùng mặc định: {os.getcwd()}", fg="orange")
    
    def save_current_config(self):
        if not self.txt_m3u8.get("1.0", "end-1c").strip():
            messagebox.showwarning("Lỗi", "Chưa có URL m3u8 để lưu config!")
            return
        
        url = self.txt_m3u8.get("1.0", "end-1c").strip()
        domain_config = self.config_manager.get_domain_config(url)
        domain_config["last_used_ext"] = self.ext1.get()
        domain_config["last_processed"] = datetime.now().isoformat()
        domain_config["filter_keyword"] = self.filter1.get()
        
        self.config_manager.save_config()
        messagebox.showinfo("Thành công", f"Đã lưu config cho domain:\n{urlparse(url).netloc}")
    
    def load_config_for_url(self):
        raw = self.txt_m3u8.get("1.0", "end-1c").strip()
        if not raw.startswith("http"):
            messagebox.showwarning("Lỗi", "Vui lòng nhập URL m3u8 hợp lệ trước!")
            return
        
        domain_config = self.config_manager.get_domain_config(raw)
        if domain_config.get("last_used_ext"):
            self.ext1.set(domain_config["last_used_ext"])
            self.status1.config(text=f"Đã tải config: đuôi file .{domain_config['last_used_ext']}", fg="green")
        else:
            self.status1.config(text="Không có config cho domain này", fg="orange")
    
    def start_tab1(self):
        mode = self.processing_mode.get()
        
        if mode == "download_and_merge" or mode == "download_only":
            if not self.segments1:
                return messagebox.showwarning("Lỗi", "Chưa quét segment!")
        
        if mode == "download_and_merge" or mode == "merge_only":
            if not hasattr(self, "output_folder1") or not self.output_folder1:
                self.output_folder1 = os.getcwd()
                self.lbl_folder1.config(text=f"Dùng mặc định: {os.getcwd()}", fg="orange")
        
        threading.Thread(target=self.run_tab1, daemon=True).start()
    
    def run_tab1(self):
        try:
            self.btn_run1.config(state="disabled")
            self.progress1["value"] = 0
            mode = self.processing_mode.get()
            
            temp_dir = os.path.join(self.output_folder1, f"temp_{int(time.time())}")
            downloaded = []
            
            if mode == "download_and_merge" or mode == "download_only":
                # Tải segments
                self.status1.config(text="Đang tải segments...")
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
                    except Exception as e:
                        print(f"Lỗi tải {url}: {e}")
                    
                    self.progress1["value"] = (i+1)/total * 50 if mode == "download_and_merge" else (i+1)/total * 100
                    self.root.update_idletasks()
                
                if not downloaded:
                    messagebox.showerror("Lỗi", "Không tải được segment nào!")
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return
                
                if mode == "download_only":
                    messagebox.showinfo("Hoàn tất", f"Đã tải {len(downloaded)} segments vào:\n{temp_dir}")
                    self.status1.config(text="Tải segments hoàn tất", fg="green")
                    return
            
            if mode == "download_and_merge" or mode == "merge_only":
                if mode == "merge_only":
                    # Chọn thư mục chứa segments
                    temp_dir = filedialog.askdirectory(title="Chọn thư mục chứa segments")
                    if not temp_dir:
                        return
                    downloaded = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) 
                                 if f.endswith(f".{self.ext1.get()}")]
                    downloaded.sort()
                
                self.progress1["value"] = 50 if mode == "download_and_merge" else 20
                
                # Bước 1: Ghép segments
                self.status1.config(text="Đang ghép segments (thử nhiều phương pháp)...")
                list_txt = os.path.join(temp_dir, "list.txt")
                self._write_concat_list(downloaded, list_txt)
                merged_ts = os.path.join(temp_dir, "merged.ts")
                
                success, msg = self._run_ffmpeg_with_methods(list_txt, merged_ts, is_concat=True, segment_files=downloaded)
                
                if not success or not os.path.exists(merged_ts) or os.path.getsize(merged_ts) < 1024:
                    messagebox.showerror("FFMPEG lỗi", f"Không thể ghép segments:\n{msg}")
                    self.btn_run1.config(state="normal")
                    return
                
                self.progress1["value"] = 70 if mode == "download_and_merge" else 50
                
                # Bước 2: Chuyển sang MP4
                self.status1.config(text="Đang chuyển sang MP4...")
                temp_mp4 = os.path.join(temp_dir, "temp.mp4")
                success, msg = self._run_ffmpeg_with_methods(merged_ts, temp_mp4)
                
                if not success or not os.path.exists(temp_mp4):
                    messagebox.showerror("FFMPEG lỗi", f"Không thể chuyển sang MP4:\n{msg}")
                    self.btn_run1.config(state="normal")
                    return
                
                self.progress1["value"] = 85 if mode == "download_and_merge" else 70
                
                # Bước 3: Burn phụ đề
                final_name = self.name1.get().strip() or "output.mp4"
                if not final_name.lower().endswith(".mp4"):
                    final_name += ".mp4"
                final_out = os.path.join(self.output_folder1, final_name)
                
                if self.sub_path1 and os.path.exists(self.sub_path1):
                    self.status1.config(text="Đang burn phụ đề...")
                    sub_ext = Path(self.sub_path1).suffix or ".srt"
                    sub_copy = os.path.join(self.output_folder1, f"temp_sub_{os.getpid()}{sub_ext}")
                    shutil.copy2(self.sub_path1, sub_copy)
                    vf_filter = f"subtitles='{Path(sub_copy).as_posix()}'"
                    
                    rc, out, err = self._run_ffmpeg([
                        "ffmpeg", "-y", "-i", temp_mp4, "-vf", vf_filter,
                        "-c:v", "libx264", "-c:a", "aac", final_out
                    ])
                    
                    try:
                        os.remove(sub_copy)
                    except:
                        pass
                    
                    if rc != 0 or not os.path.exists(final_out):
                        # Thử phương pháp khác
                        rc, out, err = self._run_ffmpeg([
                            "ffmpeg", "-y", "-i", temp_mp4, "-vf", vf_filter,
                            "-c:v", "copy", "-c:a", "copy", final_out
                        ])
                else:
                    shutil.move(temp_mp4, final_out)
                
                self.progress1["value"] = 100
                
                if os.path.exists(final_out):
                    messagebox.showinfo("HOÀN TẤT!", f"Xử lý thành công!\nVideo: {final_out}")
                    self.status1.config(text="HOÀN TẤT", fg="green")
                    
                    # Dọn dẹp nếu là mode download_and_merge
                    if mode == "download_and_merge":
                        try:
                            shutil.rmtree(temp_dir, ignore_errors=True)
                        except:
                            pass
                else:
                    messagebox.showerror("Lỗi", "Không tạo được file MP4 cuối cùng!")
                    self.status1.config(text="Lỗi", fg="red")
        
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi: {e}")
            self.status1.config(text="Lỗi", fg="red")
        finally:
            self.btn_run1.config(state="normal")
    
    # ============================== TAB 2 ==============================
    def setup_tab2(self):
        # Tương tự tab1 nhưng đơn giản hơn
        self.folder_seg2 = None
        self.folder_out2 = None
        self.sub_path2 = None
        
        main_frame = tk.Frame(self.tab2)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="GHÉP VIDEO TỪ THƯ MỤC CÓ SẴN", font=("Arial", 18, "bold"), fg="#d50000").pack(pady=15)
        
        # Chọn thư mục
        f1 = tk.Frame(main_frame)
        f1.pack(pady=10)
        ttk.Button(f1, text="1. Chọn thư mục chứa segment", command=self.choose_seg_folder2).pack(side="left", padx=20)
        self.lbl_seg2 = tk.Label(f1, text="Chưa chọn", fg="red", width=60, anchor="w")
        self.lbl_seg2.pack(side="left", padx=10)
        
        f2 = tk.Frame(main_frame)
        f2.pack(pady=8)
        ttk.Button(f2, text="2. Chọn thư mục lưu video", command=self.choose_out_folder2).pack(side="left", padx=20)
        self.lbl_out2 = tk.Label(f2, text="Chưa chọn", fg="red", width=60, anchor="w")
        self.lbl_out2.pack(side="left", padx=10)
        
        # Cấu hình
        cfg = tk.LabelFrame(main_frame, text="Cấu hình", font=("Arial", 10, "bold"))
        cfg.pack(fill="x", pady=20)
        
        tk.Label(cfg, text="Lọc đuôi:").grid(row=0, column=0, padx=20, pady=10)
        self.ext2 = tk.StringVar(value="ts")
        tk.Entry(cfg, textvariable=self.ext2, width=12).grid(row=0, column=1, padx=5)
        
        tk.Label(cfg, text="Phụ đề:").grid(row=0, column=2, padx=50)
        ttk.Button(cfg, text="Chọn .srt/.ass", command=self.choose_sub2).grid(row=0, column=3, padx=5)
        self.lbl_sub2 = tk.Label(cfg, text="Không có", fg="gray")
        self.lbl_sub2.grid(row=0, column=4, padx=10)
        
        tk.Label(cfg, text="Tên file MP4:").grid(row=1, column=0, padx=20, pady=10)
        self.name2 = tk.StringVar(value="output.mp4")
        tk.Entry(cfg, textvariable=self.name2, width=40).grid(row=1, column=1, columnspan=2, padx=5, sticky="w")
        
        # Nút chạy
        self.btn_run2 = ttk.Button(main_frame, text="GHÉP → CHUYỂN MP4 → BURN PHỤ ĐỀ", style="Big.TButton", command=self.start_tab2)
        self.btn_run2.pack(pady=30)
        
        self.progress2 = ttk.Progressbar(main_frame, length=1000, mode='determinate')
        self.progress2.pack(pady=10)
        self.status2 = tk.Label(main_frame, text="Sẵn sàng", fg="green", font=("Arial", 12, "bold"))
        self.status2.pack(pady=5)
    
    def choose_seg_folder2(self):
        f = filedialog.askdirectory()
        if f:
            self.folder_seg2 = f
            self.lbl_seg2.config(text=f"Đã chọn: {f}", fg="green")
    
    def choose_out_folder2(self):
        f = filedialog.askdirectory()
        if f:
            self.folder_out2 = f
            self.lbl_out2.config(text=f"Đã chọn: {f}", fg="green")
    
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
            
            ext = self.ext2.get().strip(" .").lower()
            files = [os.path.join(self.folder_seg2, f) for f in os.listdir(self.folder_seg2) 
                    if f.lower().endswith(ext)]
            files.sort()
            
            if not files:
                messagebox.showerror("Lỗi", "Không tìm thấy file segment!")
                return
            
            self.progress2["value"] = 20
            self.status2.config(text="Đang ghép segments...")
            
            temp_dir = os.path.join(self.folder_out2, f"temp_merge_{int(time.time())}")
            os.makedirs(temp_dir, exist_ok=True)
            
            list_txt = os.path.join(temp_dir, "list.txt")
            self._write_concat_list(files, list_txt)
            merged_ts = os.path.join(temp_dir, "merged.ts")
            
            success, msg = self._run_ffmpeg_with_methods(list_txt, merged_ts, is_concat=True, segment_files=files)
            
            if not success:
                messagebox.showerror("FFMPEG lỗi", f"Không thể ghép segments:\n{msg}")
                return
            
            self.progress2["value"] = 60
            self.status2.config(text="Đang chuyển sang MP4...")
            
            temp_mp4 = os.path.join(temp_dir, "temp.mp4")
            success, msg = self._run_ffmpeg_with_methods(merged_ts, temp_mp4)
            
            if not success:
                messagebox.showerror("FFMPEG lỗi", f"Không thể chuyển sang MP4:\n{msg}")
                return
            
            final_name = self.name2.get().strip() or "output.mp4"
            if not final_name.lower().endswith(".mp4"):
                final_name += ".mp4"
            final_out = os.path.join(self.folder_out2, final_name)
            
            if self.sub_path2 and os.path.exists(self.sub_path2):
                self.status2.config(text="Đang burn phụ đề...")
                sub_ext = Path(self.sub_path2).suffix or ".srt"
                sub_copy = os.path.join(temp_dir, f"sub{sub_ext}")
                shutil.copy2(self.sub_path2, sub_copy)
                vf_filter = f"subtitles='{Path(sub_copy).as_posix()}'"
                
                rc, out, err = self._run_ffmpeg([
                    "ffmpeg", "-y", "-i", temp_mp4, "-vf", vf_filter,
                    "-c:v", "libx264", "-c:a", "aac", final_out
                ])
            else:
                shutil.move(temp_mp4, final_out)
            
            self.progress2["value"] = 100
            
            if os.path.exists(final_out):
                # Dọn dẹp
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
                messagebox.showinfo("HOÀN TẤT!", f"Ghép thành công!\n{final_out}")
                self.status2.config(text="HOÀN TẤT", fg="green")
            else:
                messagebox.showerror("Lỗi", "Không tạo được file MP4 cuối cùng!")
                self.status2.config(text="Lỗi", fg="red")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi: {e}")
        finally:
            self.btn_run2.config(state="normal")
    
    # ============================== TAB 3 ==============================
    def setup_tab3(self):
        main_frame = tk.Frame(self.tab3)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="QUẢN LÝ CẤU HÌNH", font=("Arial", 18, "bold"), fg="#d50000").pack(pady=15)
        
        # Hiển thị config
        config_frame = tk.LabelFrame(main_frame, text="Cấu hình hiện tại", font=("Arial", 11, "bold"))
        config_frame.pack(fill="both", expand=True, pady=10)
        
        self.config_text = tk.Text(config_frame, height=20, font=("Consolas", 10))
        sb = tk.Scrollbar(config_frame, command=self.config_text.yview)
        self.config_text.config(yscrollcommand=sb.set)
        self.config_text.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        sb.pack(side="right", fill="y")
        
        # Nút chức năng
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="RELOAD CONFIG", command=self.refresh_config_display).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="XÓA CONFIG DOMAIN", command=self.delete_domain_config).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="RESET TOÀN BỘ", command=self.reset_all_config).pack(side="left", padx=10)
        
        # Phương pháp xử lý
        methods_frame = tk.LabelFrame(main_frame, text="Phương pháp xử lý (bật/tắt)", font=("Arial", 11, "bold"))
        methods_frame.pack(fill="x", pady=10)
        
        self.method_vars = {}
        methods_list = [
            ("concat_copy", "Ghép copy trực tiếp"),
            ("concat_genpts", "Ghép với genpts"),
            ("concat_bsf", "Ghép với BSF audio"),
            ("concat_to_ts_then_mp4", "Ghép TS trước rồi sang MP4"),
            ("reencode_video", "Re-encode video"),
            ("reencode_both", "Re-encode cả video và audio"),
            ("ignore_errors", "Bỏ qua lỗi")
        ]
        
        for i, (key, label) in enumerate(methods_list):
            var = tk.BooleanVar(value=self.config_manager.config["processing_methods"].get(key, True))
            self.method_vars[key] = var
            cb = tk.Checkbutton(methods_frame, text=label, variable=var,
                               command=lambda k=key: self.toggle_method(k))
            cb.grid(row=i//3, column=i%3, sticky="w", padx=20, pady=5)
        
        self.refresh_config_display()
    
    def refresh_config_display(self):
        self.config_text.delete(1.0, tk.END)
        self.config_text.insert(1.0, json.dumps(self.config_manager.config, indent=2, ensure_ascii=False))
    
    def toggle_method(self, method_key):
        self.config_manager.config["processing_methods"][method_key] = self.method_vars[method_key].get()
        self.config_manager.save_config()
        self.refresh_config_display()
    
    def delete_domain_config(self):
        domains = list(self.config_manager.config["domains"].keys())
        if not domains:
            messagebox.showinfo("Thông báo", "Không có domain nào trong config!")
            return
        
        # Tạo dialog chọn domain
        dialog = tk.Toplevel(self.root)
        dialog.title("Chọn domain để xóa")
        dialog.geometry("400x300")
        
        tk.Label(dialog, text="Chọn domain cần xóa:", font=("Arial", 10, "bold")).pack(pady=10)
        
        listbox = tk.Listbox(dialog)
        for domain in domains:
            listbox.insert(tk.END, domain)
        listbox.pack(fill="both", expand=True, padx=20, pady=10)
        
        def delete_selected():
            selection = listbox.curselection()
            if selection:
                domain = domains[selection[0]]
                if messagebox.askyesno("Xác nhận", f"Xóa config của domain:\n{domain}?"):
                    del self.config_manager.config["domains"][domain]
                    self.config_manager.save_config()
                    self.refresh_config_display()
                    dialog.destroy()
                    messagebox.showinfo("Thành công", "Đã xóa config!")
        
        ttk.Button(dialog, text="XÓA", command=delete_selected).pack(pady=10)
    
    def reset_all_config(self):
        if messagebox.askyesno("Cảnh báo", "RESET sẽ xóa TOÀN BỘ config!\nTiếp tục?"):
            self.config_manager.config = self.config_manager.get_default_config()
            self.config_manager.save_config()
            self.refresh_config_display()
            # Reset các checkbox
            for key, var in self.method_vars.items():
                var.set(True)
            messagebox.showinfo("Thành công", "Đã reset toàn bộ config!")


if __name__ == "__main__":
    root = tk.Tk()
    app = HLSDownloader(root)
    root.mainloop()