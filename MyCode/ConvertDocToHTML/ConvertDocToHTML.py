import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
import threading
import time
import win32com.client
import pythoncom
import shutil
import zipfile
from datetime import datetime

class WordToVideoConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Chuyển đổi Word sang HTML/PDF (Giữ video) - Hỗ trợ DOC, DOCX, DOCM, DOTX, DOTM, RTF")
        self.root.geometry("850x650")
        
        # Style
        style = ttk.Style()
        style.configure('Warning.TLabel', foreground='red')
        style.configure('Success.TLabel', foreground='green')
        style.configure('Info.TLabel', foreground='blue')
        
        # Danh sách định dạng Word được hỗ trợ
        self.word_formats = [
            ("Word Documents", "*.docx;*.doc;*.docm;*.dotx;*.dotm;*.rtf"),
            ("All Word Files", "*.doc;*.docx;*.docm;*.dotx;*.dotm;*.rtf"),
            ("DOCX Files", "*.docx"),
            ("DOC Files", "*.doc"),
            ("DOCM Files (Macro-enabled)", "*.docm"),
            ("DOTX Templates", "*.dotx"),
            ("DOTM Templates (Macro-enabled)", "*.dotm"),
            ("RTF Files", "*.rtf"),
            ("All Files", "*.*")
        ]
        
        # Tạo notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Tạo tabs
        self.single_file_tab = ttk.Frame(self.notebook)
        self.folder_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.single_file_tab, text="📄 Single File")
        self.notebook.add(self.folder_tab, text="📁 Multiple Files")
        
        # Khởi tạo các tab
        self.setup_single_file_tab()
        self.setup_folder_tab()
        
        # Progress bar
        self.progress = ttk.Progressbar(root, orient='horizontal', length=600, mode='determinate')
        self.progress.pack(pady=10)
        
        # Status frame
        status_frame = ttk.Frame(root)
        status_frame.pack(fill='x', padx=10)
        
        self.status_label = tk.Label(status_frame, text="✅ Sẵn sàng", fg="green", font=('Arial', 10))
        self.status_label.pack(side='left')
        
        self.time_label = tk.Label(status_frame, text="", fg="gray")
        self.time_label.pack(side='right')
        
        # Log text với scrollbar
        log_frame = ttk.Frame(root)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        log_header = ttk.Frame(log_frame)
        log_header.pack(fill='x')
        
        ttk.Label(log_header, text="📋 Nhật ký xử lý:", font=('Arial', 10, 'bold')).pack(side='left')
        
        # Nút clear log
        ttk.Button(log_header, text="🗑️ Xóa log", command=self.clear_log).pack(side='right')
        
        # Text log với scrollbar
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill='both', expand=True)
        
        self.log_text = tk.Text(text_frame, height=12, width=80, font=('Consolas', 9), wrap='word')
        self.log_text.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Thông tin Android
        android_info = ttk.LabelFrame(root, text="📱 Hướng dẫn xem trên Android", padding="5")
        android_info.pack(fill='x', padx=10, pady=5)
        
        android_text = """
        • 🌐 HTML: Copy NGUYÊN FOLDER (HTML + folder _files) vào Android, mở bằng Chrome
        • 🗜️ ZIP: Giải nén trên Android, mở file HTML trong folder đã giải nén
        • 📄 PDF: Chỉ xem được văn bản, KHÔNG xem được video trên Android
        • 📱 Cài VLC for Android từ CH Play để xem video mọi định dạng
        """
        ttk.Label(android_info, text=android_text, foreground='blue').pack(anchor='w')
        
        self.is_converting = False
        self.start_time = None
        
    def clear_log(self):
        """Xóa nội dung log"""
        self.log_text.delete(1.0, tk.END)
        
    def log(self, message, level='info'):
        """Ghi log với màu sắc"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Màu sắc cho các level
        colors = {
            'info': 'black',
            'success': 'green',
            'warning': 'orange',
            'error': 'red',
            'android': 'blue',
            'format': 'purple'
        }
        
        color = colors.get(level, 'black')
        icon = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'android': '📱',
            'format': '📄'
        }.get(level, '')
        
        self.log_text.insert(tk.END, f"[{timestamp}] {icon} {message}\n")
        self.log_text.tag_add(level, f"end-2l linestart", f"end-1l lineend")
        self.log_text.tag_config(level, foreground=color)
        self.log_text.see(tk.END)
        self.root.update()
        
    def update_time(self):
        """Cập nhật thời gian chạy"""
        if self.start_time and self.is_converting:
            elapsed = time.time() - self.start_time
            self.time_label.config(text=f"⏱️ {elapsed:.1f}s")
            self.root.after(100, self.update_time)
        
    def update_progress(self, value, status_text, level='info'):
        """Cập nhật progress và status"""
        self.progress['value'] = value
        self.status_label.config(text=status_text)
        if "Đang xử lý" not in status_text:  # Tránh log quá nhiều
            self.log(status_text, level)
        self.root.update()
        
    def setup_single_file_tab(self):
        main_frame = ttk.Frame(self.single_file_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # File Word
        file_frame = ttk.LabelFrame(main_frame, text="📄 Chọn file Word", padding="5")
        file_frame.grid(row=0, column=0, columnspan=3, sticky='ew', pady=5)
        
        self.word_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.word_file_var, width=70).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(file_frame, text="📂 Chọn file...", command=self.browse_word_file).pack(side='left', padx=2)
        
        # Hiển thị định dạng được hỗ trợ
        format_label = ttk.Label(file_frame, text="Hỗ trợ: DOC, DOCX, DOCM, DOTX, DOTM, RTF", 
                                foreground='green', font=('Arial', 8))
        format_label.pack(side='left', padx=10)
        
        # Thư mục lưu
        output_frame = ttk.LabelFrame(main_frame, text="📁 Thư mục lưu", padding="5")
        output_frame.grid(row=1, column=0, columnspan=3, sticky='ew', pady=5)
        
        self.output_folder_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_folder_var, width=70).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(output_frame, text="📂 Chọn thư mục...", command=self.browse_output_folder).pack(side='left', padx=2)
        ttk.Button(output_frame, text="🔄 Mặc định", command=self.set_default_output_folder).pack(side='left', padx=2)
        
        # Tên file
        name_frame = ttk.LabelFrame(main_frame, text="📝 Tên file đầu ra", padding="5")
        name_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=5)
        
        self.output_name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.output_name_var, width=50).pack(side='left', padx=5)
        ttk.Label(name_frame, text="(Không cần nhập phần mở rộng)").pack(side='left', padx=5)
        
        # Định dạng đầu ra
        format_frame = ttk.LabelFrame(main_frame, text="🎯 Định dạng đầu ra", padding="5")
        format_frame.grid(row=3, column=0, columnspan=3, sticky='ew', pady=5)
        
        self.output_format = tk.StringVar(value="html")
        
        # Frame cho các radio button
        radio_frame = ttk.Frame(format_frame)
        radio_frame.pack(fill='x')
        
        # Cột 1
        col1 = ttk.Frame(radio_frame)
        col1.pack(side='left', fill='y', padx=10)
        
        html_radio = ttk.Radiobutton(col1, text="🌐 HTML (Khuyên dùng - xem được video trên Android)", 
                                     variable=self.output_format, value="html")
        html_radio.pack(anchor='w', pady=2)
        
        pdf_radio = ttk.Radiobutton(col1, text="📄 PDF (Chỉ văn bản, KHÔNG xem video trên Android)", 
                                    variable=self.output_format, value="pdf_link")
        pdf_radio.pack(anchor='w', pady=2)
        
        # Cột 2
        col2 = ttk.Frame(radio_frame)
        col2.pack(side='left', fill='y', padx=10)
        
        zip_radio = ttk.Radiobutton(col2, text="🗜️ ZIP (Đóng gói HTML + video, dễ chia sẻ)", 
                                    variable=self.output_format, value="zip")
        zip_radio.pack(anchor='w', pady=2)
        
        # Android options
        android_frame = ttk.LabelFrame(main_frame, text="📱 Tùy chọn cho Android", padding="5")
        android_frame.grid(row=4, column=0, columnspan=3, sticky='ew', pady=5)
        
        self.android_optimize = tk.BooleanVar(value=True)
        ttk.Checkbutton(android_frame, text="Tối ưu cho Android (sửa đường dẫn, thêm meta tags)", 
                       variable=self.android_optimize).pack(anchor='w')
        
        self.create_readme = tk.BooleanVar(value=True)
        ttk.Checkbutton(android_frame, text="Tạo file README.txt hướng dẫn xem trên Android", 
                       variable=self.create_readme).pack(anchor='w')
        
        # Nút Start
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        self.single_start_btn = ttk.Button(button_frame, text="🚀 BẮT ĐẦU CHUYỂN ĐỔI", 
                                          command=self.start_single_conversion, width=30)
        self.single_start_btn.pack()
        
    def setup_folder_tab(self):
        main_frame = ttk.Frame(self.folder_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Folder Word
        folder_frame = ttk.LabelFrame(main_frame, text="📁 Chọn folder chứa file Word", padding="5")
        folder_frame.grid(row=0, column=0, columnspan=3, sticky='ew', pady=5)
        
        self.word_folder_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.word_folder_var, width=70).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(folder_frame, text="📂 Chọn folder...", command=self.browse_word_folder).pack(side='left', padx=2)
        
        # Hiển thị định dạng được hỗ trợ
        format_label = ttk.Label(folder_frame, text="Hỗ trợ: DOC, DOCX, DOCM, DOTX, DOTM, RTF", 
                                foreground='green', font=('Arial', 8))
        format_label.pack(side='left', padx=10)
        
        # Thư mục lưu
        output_frame = ttk.LabelFrame(main_frame, text="📁 Thư mục lưu kết quả", padding="5")
        output_frame.grid(row=1, column=0, columnspan=3, sticky='ew', pady=5)
        
        self.folder_output_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.folder_output_var, width=70).pack(side='left', padx=5, fill='x', expand=True)
        ttk.Button(output_frame, text="📂 Chọn thư mục...", command=self.browse_folder_output).pack(side='left', padx=2)
        ttk.Button(output_frame, text="🔄 Mặc định", command=self.set_default_folder_output).pack(side='left', padx=2)
        
        # Định dạng đầu ra (tương tự)
        format_frame = ttk.LabelFrame(main_frame, text="🎯 Định dạng đầu ra", padding="5")
        format_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=5)
        
        self.folder_format = tk.StringVar(value="html")
        
        radio_frame = ttk.Frame(format_frame)
        radio_frame.pack(fill='x')
        
        col1 = ttk.Frame(radio_frame)
        col1.pack(side='left', fill='y', padx=10)
        
        ttk.Radiobutton(col1, text="🌐 HTML (Khuyên dùng - xem được video trên Android)", 
                       variable=self.folder_format, value="html").pack(anchor='w', pady=2)
        ttk.Radiobutton(col1, text="📄 PDF (Chỉ văn bản, KHÔNG xem video trên Android)", 
                       variable=self.folder_format, value="pdf_link").pack(anchor='w', pady=2)
        
        col2 = ttk.Frame(radio_frame)
        col2.pack(side='left', fill='y', padx=10)
        
        ttk.Radiobutton(col2, text="🗜️ ZIP (Đóng gói HTML + video, dễ chia sẻ)", 
                       variable=self.folder_format, value="zip").pack(anchor='w', pady=2)
        
        # Android options
        android_frame = ttk.LabelFrame(main_frame, text="📱 Tùy chọn cho Android", padding="5")
        android_frame.grid(row=3, column=0, columnspan=3, sticky='ew', pady=5)
        
        self.folder_android_optimize = tk.BooleanVar(value=True)
        ttk.Checkbutton(android_frame, text="Tối ưu cho Android", 
                       variable=self.folder_android_optimize).pack(anchor='w')
        
        self.folder_create_readme = tk.BooleanVar(value=True)
        ttk.Checkbutton(android_frame, text="Tạo file README.txt", 
                       variable=self.folder_create_readme).pack(anchor='w')
        
        # Nút Start
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.folder_start_btn = ttk.Button(button_frame, text="🚀 BẮT ĐẦU XỬ LÝ HÀNG LOẠT", 
                                          command=self.start_folder_conversion, width=30)
        self.folder_start_btn.pack()
        
    def browse_word_file(self):
        filename = filedialog.askopenfilename(
            title="Chọn file Word",
            filetypes=self.word_formats
        )
        if filename:
            self.word_file_var.set(filename)
            base_name = os.path.splitext(os.path.basename(filename))[0]
            self.output_name_var.set(base_name)
            self.set_default_output_folder()
            
            # Log định dạng file
            ext = os.path.splitext(filename)[1].lower()
            self.log(f"Đã chọn file: {os.path.basename(filename)}", 'format')
            self.log(f"Định dạng: {ext.upper()}", 'format')
            
    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục lưu kết quả")
        if folder:
            self.output_folder_var.set(folder)
            
    def browse_word_folder(self):
        folder = filedialog.askdirectory(title="Chọn folder chứa file Word")
        if folder:
            self.word_folder_var.set(folder)
            self.set_default_folder_output()
            
            # Đếm số file Word trong folder
            word_files = self.get_word_files(folder)
            self.log(f"Đã chọn folder: {folder}", 'format')
            self.log(f"Tìm thấy {len(word_files)} file Word", 'format')
            
    def get_word_files(self, folder):
        """Lấy tất cả file Word trong folder"""
        word_files = []
        extensions = ['*.docx', '*.doc', '*.docm', '*.dotx', '*.dotm', '*.rtf']
        for ext in extensions:
            word_files.extend(Path(folder).glob(ext))
        return sorted(word_files)
            
    def browse_folder_output(self):
        folder = filedialog.askdirectory(title="Chọn thư mục lưu kết quả")
        if folder:
            self.folder_output_var.set(folder)
            
    def set_default_output_folder(self):
        word_file = self.word_file_var.get()
        if word_file:
            default_folder = os.path.dirname(word_file)
            self.output_folder_var.set(default_folder)
            
    def set_default_folder_output(self):
        word_folder = self.word_folder_var.get()
        if word_folder:
            self.folder_output_var.set(word_folder)
    
    def optimize_for_android(self, html_path, base_name):
        """Tối ưu file HTML để xem trên Android"""
        try:
            self.log("Đang tối ưu file HTML cho Android...", 'android')
            
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Thêm meta tags cho mobile
            if '<head>' in content:
                meta_tags = '''
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
    <meta name="theme-color" content="#4285f4">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta charset="UTF-8">
    '''
                content = content.replace('<head>', f'<head>{meta_tags}')
            
            # Sửa đường dẫn video thành đường dẫn tương đối
            content = content.replace('file:///C:', '').replace('file:///D:', '')
            content = content.replace('C:\\', '').replace('D:\\', '')
            content = content.replace('\\', '/')
            
            # Thêm CSS cho mobile
            css = '''
    <style>
        * {
            box-sizing: border-box;
        }
        body { 
            font-family: 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif; 
            margin: 0; 
            padding: 15px; 
            background: #f5f5f5;
            line-height: 1.6;
        }
        video { 
            max-width: 100%; 
            height: auto; 
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            background: #000;
        }
        img { 
            max-width: 100%; 
            height: auto; 
            border-radius: 8px;
        }
        .android-note {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 12px;
            margin: 15px 0;
            border-left: 5px solid #2196F3;
            font-size: 14px;
        }
        .android-note strong {
            color: #1976D2;
            font-size: 16px;
        }
        .video-container {
            position: relative;
            width: 100%;
            margin: 15px 0;
        }
        @media (prefers-color-scheme: dark) {
            body { background: #121212; color: #fff; }
            .android-note { background: #1e3a5f; }
        }
    </style>
            '''
            
            if '</head>' in content:
                content = content.replace('</head>', f'{css}</head>')
            
            # Thêm hướng dẫn Android (chỉ nếu chưa có)
            if 'android-note' not in content:
                android_note = f'''
    <div class="android-note">
        <strong>📱 Xem trên Android:</strong>
        <ul style="margin:5px 0 0 20px; padding:0;">
            <li>Chạm vào video để phát</li>
            <li>Vuốt để cuộn trang</li>
            <li>Nếu video không chạy, cài VLC từ CH Play</li>
        </ul>
        <small style="color:#666;">📁 Folder video: <b>{base_name}_files</b> (phải nằm cùng folder với file HTML này)</small>
    </div>
                '''
                
                if '<body>' in content:
                    content = content.replace('<body>', f'<body>{android_note}')
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log("✅ Đã tối ưu HTML cho Android", 'success')
            return True
            
        except Exception as e:
            self.log(f"❌ Lỗi tối ưu HTML: {str(e)}", 'error')
            return False
    
    def create_android_readme(self, output_dir, base_name, output_format):
        """Tạo file README hướng dẫn cho Android"""
        try:
            readme_path = os.path.join(output_dir, f"{base_name}_README.txt")
            
            if output_format == 'html':
                content = f"""HƯỚNG DẪN XEM FILE TRÊN ANDROID
================================

Tên file: {base_name}.html
Ngày tạo: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Định dạng gốc: Hỗ trợ DOC, DOCX, DOCM, DOTX, DOTM, RTF

📱 CÁCH XEM TRÊN ANDROID:

1. Copy NGUYÊN FOLDER này vào Android (qua USB, Bluetooth, Cloud...):
   - File HTML: {base_name}.html
   - Folder media: {base_name}_files/ (chứa video, ảnh)
   
2. Trên Android, dùng trình quản lý file (File Manager):
   - Tìm đến file {base_name}.html
   - Chạm vào file, chọn "Mở bằng Chrome" hoặc "Open with Chrome"
   
3. Video sẽ hiển thị trong trang web, chạm để phát

📁 CẤU TRÚC FOLDER BẮT BUỘC:
   {base_name}.html
   {base_name}_files/
       ├── video1.mp4
       ├── video2.mp4
       ├── image1.jpg
       └── ...

⚠️ LƯU Ý QUAN TRỌNG:
- Giữ nguyên tên folder {base_name}_files
- Không di chuyển file HTML ra khỏi folder này
- Nếu gặp lỗi, hãy thử:
  * Cài VLC for Android từ CH Play
  * Dùng app "HTML Viewer" từ CH Play
  * Giải nén lại từ file ZIP gốc

📱 ỨNG DỤNG CẦN CÀI:
- Google Chrome (có sẵn)
- VLC for Android (miễn phí) - để xem video mọi định dạng
- HTML Viewer (dự phòng)

---
Phần mềm chuyển đổi Word to Video Converter
Hỗ trợ: DOC, DOCX, DOCM, DOTX, DOTM, RTF
"""
            elif output_format == 'zip':
                content = f"""HƯỚNG DẪN SỬ DỤNG FILE ZIP TRÊN ANDROID
======================================

Tên file: {base_name}.zip
Ngày tạo: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Định dạng gốc: Hỗ trợ DOC, DOCX, DOCM, DOTX, DOTM, RTF

📱 CÁCH SỬ DỤNG TRÊN ANDROID:

1. Cài app giải nén (nếu chưa có):
   - ZArchiver (khuyên dùng) từ CH Play
   - Hoặc RAR từ CH Play

2. Giải nén file ZIP:
   - Mở app ZArchiver
   - Tìm đến file {base_name}.zip
   - Chọn "Extract" (Giải nén)
   - Chọn thư mục đích (ví dụ: Downloads)

3. Sau khi giải nén, bạn sẽ thấy:
   - File HTML: {base_name}.html
   - Folder media: {base_name}_files/ (chứa video)

4. Mở file HTML:
   - Dùng trình quản lý file, tìm đến {base_name}.html
   - Chạm vào file, chọn "Mở bằng Chrome"

📁 CẤU TRÚC SAU KHI GIẢI NÉN:
   {base_name}.html
   {base_name}_files/
       ├── video1.mp4
       ├── video2.mp4
       └── ...

⚠️ LƯU Ý:
- Giữ nguyên cấu trúc folder sau khi giải nén
- Không di chuyển file HTML ra khỏi folder chứa media

---
Phần mềm chuyển đổi Word to Video Converter
Hỗ trợ: DOC, DOCX, DOCM, DOTX, DOTM, RTF
"""
            else:  # pdf_link
                content = f"""LƯU Ý VỀ FILE PDF TRÊN ANDROID
============================

Tên file: {base_name}.pdf
Ngày tạo: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Định dạng gốc: Hỗ trợ DOC, DOCX, DOCM, DOTX, DOTM, RTF

⚠️ QUAN TRỌNG:

File PDF này CHỈ chứa liên kết đến video, 
KHÔNG chứa video thật trong file.

📱 ĐỂ XEM VIDEO TRÊN ANDROID:

1. Mở folder: {base_name}_videos/
2. Xem trực tiếp các file video:
   - Dùng VLC for Android
   - Hoặc Google Photos

📁 CẤU TRÚC FOLDER:
   {base_name}.pdf (chỉ văn bản, KHÔNG có video)
   {base_name}_videos/
       ├── video1.mp4
       ├── video2.mp4
       └── ...

✅ KHUYẾN NGHỊ:
- Nên dùng định dạng HTML thay vì PDF để xem video
- Cài VLC for Android từ CH Play

---
Phần mềm chuyển đổi Word to Video Converter
Hỗ trợ: DOC, DOCX, DOCM, DOTX, DOTM, RTF
"""
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log(f"✅ Đã tạo file README: {os.path.basename(readme_path)}", 'success')
            return True
            
        except Exception as e:
            self.log(f"❌ Lỗi tạo README: {str(e)}", 'error')
            return False
    
    def word_to_html(self, word_path, html_path, optimize=True, create_readme=True):
        """Chuyển Word sang HTML giữ nguyên video - Hỗ trợ mọi định dạng Word"""
        try:
            file_ext = os.path.splitext(word_path)[1].lower()
            self.log(f"Đang chuyển đổi: {os.path.basename(word_path)} ({file_ext.upper()}) → HTML", 'info')
            
            pythoncom.CoInitialize()
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = False  # Tắt cảnh báo
            
            # Mở file Word (hỗ trợ mọi định dạng)
            doc = word.Documents.Open(word_path)
            
            # Lưu dưới dạng HTML
            doc.SaveAs(html_path, FileFormat=10)  # 10 = wdFormatHTML
            doc.Close()
            word.Quit()
            
            # Tìm và rename folder media
            html_dir = os.path.dirname(html_path)
            base_name = os.path.splitext(os.path.basename(html_path))[0]
            
            # Word thường tạo folder với tên file.html_files
            possible_media_folders = [
                os.path.join(html_dir, f"{base_name}.html_files"),
                os.path.join(html_dir, f"{base_name}_files"),
                os.path.join(html_dir, f"{base_name}.files")
            ]
            
            target_media_dir = os.path.join(html_dir, f"{base_name}_files")
            
            for media_folder in possible_media_folders:
                if os.path.exists(media_folder):
                    if os.path.exists(target_media_dir):
                        shutil.rmtree(target_media_dir)
                    shutil.move(media_folder, target_media_dir)
                    self.log(f"✅ Đã lưu media vào: {os.path.basename(target_media_dir)}", 'success')
                    break
            
            # Tối ưu cho Android
            if optimize:
                self.optimize_for_android(html_path, base_name)
            
            # Tạo README
            if create_readme:
                self.create_android_readme(html_dir, base_name, 'html')
            
            return True
            
        except Exception as e:
            self.log(f"❌ Lỗi: {str(e)}", 'error')
            return False
        finally:
            pythoncom.CoUninitialize()
    
    def create_pdf_with_links(self, word_path, pdf_path, create_readme=True):
        """Tạo PDF với liên kết video - Hỗ trợ mọi định dạng Word"""
        try:
            file_ext = os.path.splitext(word_path)[1].lower()
            self.log(f"Đang chuyển đổi: {os.path.basename(word_path)} ({file_ext.upper()}) → PDF", 'info')
            
            pythoncom.CoInitialize()
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = False
            
            doc = word.Documents.Open(word_path)
            doc.SaveAs(pdf_path, FileFormat=17)  # 17 = wdFormatPDF
            doc.Close()
            word.Quit()
            
            # Xử lý media
            pdf_dir = os.path.dirname(pdf_path)
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            
            # Kiểm tra và rename media folder
            possible_media_folders = [
                os.path.join(pdf_dir, f"{base_name}.html_files"),
                os.path.join(pdf_dir, f"{base_name}_files"),
                os.path.join(pdf_dir, f"{base_name}.files")
            ]
            
            target_media_dir = os.path.join(pdf_dir, f"{base_name}_videos")
            
            for media_folder in possible_media_folders:
                if os.path.exists(media_folder):
                    if os.path.exists(target_media_dir):
                        shutil.rmtree(target_media_dir)
                    shutil.move(media_folder, target_media_dir)
                    self.log(f"✅ Đã lưu video vào: {os.path.basename(target_media_dir)}", 'success')
                    break
            
            # Cảnh báo cho Android
            self.log("⚠️ PDF KHÔNG xem được video trên Android!", 'warning')
            
            # Tạo README
            if create_readme:
                self.create_android_readme(pdf_dir, base_name, 'pdf_link')
            
            return True
            
        except Exception as e:
            self.log(f"❌ Lỗi: {str(e)}", 'error')
            return False
        finally:
            pythoncom.CoUninitialize()
    
    def create_zip_package(self, word_path, zip_path, optimize=True, create_readme=True):
        """Tạo file ZIP chứa HTML và video - Hỗ trợ mọi định dạng Word"""
        try:
            file_ext = os.path.splitext(word_path)[1].lower()
            self.log(f"Đang tạo file ZIP từ: {os.path.basename(word_path)} ({file_ext.upper()})", 'info')
            
            # Tạo thư mục tạm
            temp_dir = os.path.join(os.path.dirname(zip_path), f"temp_{int(time.time())}")
            os.makedirs(temp_dir, exist_ok=True)
            
            base_name = os.path.splitext(os.path.basename(zip_path))[0]
            temp_html = os.path.join(temp_dir, f"{base_name}.html")
            
            # Chuyển Word sang HTML
            self.word_to_html(word_path, temp_html, optimize=optimize, create_readme=False)
            
            # Tìm folder media
            media_dir = os.path.join(temp_dir, f"{base_name}_files")
            if not os.path.exists(media_dir):
                # Thử tìm folder khác
                old_media = os.path.join(temp_dir, f"{base_name}.html_files")
                if os.path.exists(old_media):
                    shutil.move(old_media, media_dir)
            
            # Tạo README
            if create_readme:
                self.create_android_readme(temp_dir, base_name, 'zip')
            
            # Tạo file ZIP
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arc_path)
            
            # Xóa thư mục tạm
            shutil.rmtree(temp_dir)
            
            # Tính dung lượng file ZIP
            size_mb = os.path.getsize(zip_path) / (1024 * 1024)
            self.log(f"✅ Đã tạo file ZIP: {size_mb:.1f} MB", 'success')
            
            return True
            
        except Exception as e:
            self.log(f"❌ Lỗi: {str(e)}", 'error')
            return False
    
    def start_single_conversion(self):
        if self.is_converting:
            messagebox.showwarning("Đang xử lý", "Vui lòng đợi quá trình hiện tại hoàn tất!")
            return
            
        word_file = self.word_file_var.get()
        output_folder = self.output_folder_var.get()
        base_name = self.output_name_var.get()
        output_format = self.output_format.get()
        android_optimize = self.android_optimize.get()
        create_readme = self.create_readme.get()
        
        # Kiểm tra đầu vào
        if not word_file:
            messagebox.showerror("Lỗi", "Vui lòng chọn file Word!")
            return
            
        if not output_folder:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục lưu!")
            return
            
        if not base_name:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên file đầu ra!")
            return
            
        if not os.path.exists(word_file):
            messagebox.showerror("Lỗi", "File Word không tồn tại!")
            return
        
        # Kiểm tra định dạng file Word
        valid_extensions = ['.docx', '.doc', '.docm', '.dotx', '.dotm', '.rtf']
        file_ext = os.path.splitext(word_file)[1].lower()
        
        if file_ext not in valid_extensions:
            result = messagebox.askyesno("Cảnh báo định dạng", 
                                       f"File có định dạng {file_ext} không nằm trong danh sách hỗ trợ.\n\n"
                                       f"Danh sách hỗ trợ: DOC, DOCX, DOCM, DOTX, DOTM, RTF\n\n"
                                       f"Bạn vẫn muốn tiếp tục?")
            if not result:
                return
        
        # Xác định file đầu ra
        if output_format == "html":
            output_path = os.path.join(output_folder, f"{base_name}.html")
        elif output_format == "pdf_link":
            output_path = os.path.join(output_folder, f"{base_name}.pdf")
        else:  # zip
            output_path = os.path.join(output_folder, f"{base_name}.zip")
        
        # Cảnh báo cho PDF
        if output_format == "pdf_link":
            result = messagebox.askyesno("Cảnh báo PDF", 
                                       "PDF sẽ KHÔNG xem được video trên Android!\n\n"
                                       "Bạn có muốn tiếp tục không?\n\n"
                                       "(Chọn 'No' để quay lại chọn HTML hoặc ZIP)")
            if not result:
                return
        
        # Disable nút
        self.single_start_btn.config(state='disabled')
        self.is_converting = True
        self.start_time = time.time()
        
        # Xóa log cũ
        self.log_text.delete(1.0, tk.END)
        self.log("🚀 BẮT ĐẦU XỬ LÝ", 'info')
        self.log(f"📄 File Word: {os.path.basename(word_file)}", 'info')
        self.log(f"📁 Thư mục lưu: {output_folder}", 'info')
        self.log(f"🎯 Định dạng: {output_format.upper()}", 'info')
        self.log(f"📱 Tối ưu Android: {'Có' if android_optimize else 'Không'}", 'android')
        
        # Cập nhật thời gian
        self.update_time()
        
        # Chạy trong thread riêng
        thread = threading.Thread(target=self.single_conversion_thread, 
                                 args=(word_file, output_path, output_format, 
                                      android_optimize, create_readme))
        thread.daemon = True
        thread.start()
        
    def single_conversion_thread(self, word_file, output_path, output_format, 
                                 android_optimize, create_readme):
        try:
            self.update_progress(30, "🔄 Đang xử lý...")
            
            success = False
            if output_format == "html":
                success = self.word_to_html(word_file, output_path, 
                                           optimize=android_optimize, 
                                           create_readme=create_readme)
            elif output_format == "pdf_link":
                success = self.create_pdf_with_links(word_file, output_path, 
                                                     create_readme=create_readme)
            else:  # zip
                success = self.create_zip_package(word_file, output_path, 
                                                  optimize=android_optimize, 
                                                  create_readme=create_readme)
            
            if success:
                elapsed = time.time() - self.start_time
                self.update_progress(100, f"✅ Hoàn thành! ({elapsed:.1f}s)", 'success')
                
                # Thông báo kết quả
                if output_format == "html":
                    msg = (f"✅ ĐÃ TẠO FILE HTML THÀNH CÔNG!\n\n"
                          f"📁 File HTML: {os.path.basename(output_path)}\n"
                          f"📁 Folder media: {os.path.splitext(os.path.basename(output_path))[0]}_files\n"
                          f"📁 File README: {os.path.splitext(os.path.basename(output_path))[0]}_README.txt\n\n"
                          f"📱 CÁCH XEM TRÊN ANDROID:\n"
                          f"1. Copy NGUYÊN FOLDER này vào Android\n"
                          f"2. Mở file .html bằng Chrome\n"
                          f"3. Video sẽ hiển thị và chạy được\n\n"
                          f"⚠️ Xem file README để biết chi tiết")
                elif output_format == "pdf_link":
                    msg = (f"✅ ĐÃ TẠO FILE PDF THÀNH CÔNG!\n\n"
                          f"📁 File PDF: {os.path.basename(output_path)}\n"
                          f"📁 Folder video: {os.path.splitext(os.path.basename(output_path))[0]}_videos\n"
                          f"📁 File README: {os.path.splitext(os.path.basename(output_path))[0]}_README.txt\n\n"
                          f"⚠️ LƯU Ý QUAN TRỌNG:\n"
                          f"PDF KHÔNG xem được video trên Android!\n\n"
                          f"📱 ĐỂ XEM VIDEO:\n"
                          f"- Mở folder _videos\n"
                          f"- Xem trực tiếp file video bằng VLC")
                else:  # zip
                    size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    msg = (f"✅ ĐÃ TẠO FILE ZIP THÀNH CÔNG!\n\n"
                          f"📁 File ZIP: {os.path.basename(output_path)}\n"
                          f"📦 Dung lượng: {size_mb:.1f} MB\n\n"
                          f"📱 CÁCH DÙNG TRÊN ANDROID:\n"
                          f"1. Giải nén file ZIP (dùng ZArchiver)\n"
                          f"2. Mở file .html trong folder đã giải nén bằng Chrome\n"
                          f"3. Video sẽ hiển thị và chạy được\n\n"
                          f"⚠️ Xem file README.txt trong ZIP để biết chi tiết")
                
                messagebox.showinfo("✅ Thành công", msg)
            else:
                self.update_progress(0, "❌ Thất bại!", 'error')
                messagebox.showerror("❌ Lỗi", "Không thể tạo file đầu ra!\n\nKiểm tra log để biết chi tiết.")
                
        except Exception as e:
            self.log(f"❌ Lỗi: {str(e)}", 'error')
            self.update_progress(0, "❌ Lỗi!", 'error')
            messagebox.showerror("❌ Lỗi", str(e))
        finally:
            self.single_start_btn.config(state='normal')
            self.is_converting = False
            self.start_time = None
            self.time_label.config(text="")
    
    def start_folder_conversion(self):
        if self.is_converting:
            messagebox.showwarning("Đang xử lý", "Vui lòng đợi quá trình hiện tại hoàn tất!")
            return
            
        word_folder = self.word_folder_var.get()
        output_folder = self.folder_output_var.get()
        output_format = self.folder_format.get()
        android_optimize = self.folder_android_optimize.get()
        create_readme = self.folder_create_readme.get()
        
        if not word_folder:
            messagebox.showerror("Lỗi", "Vui lòng chọn folder chứa file Word!")
            return
            
        if not output_folder:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục lưu kết quả!")
            return
            
        if not os.path.exists(word_folder):
            messagebox.showerror("Lỗi", "Folder Word không tồn tại!")
            return
            
        # Lấy danh sách file Word
        word_files = self.get_word_files(word_folder)
            
        if not word_files:
            messagebox.showerror("Lỗi", 
                               "Không tìm thấy file Word trong folder!\n\n"
                               "Các định dạng hỗ trợ:\n"
                               "- DOCX, DOC, DOCM\n"
                               "- DOTX, DOTM\n"
                               "- RTF")
            return
        
        # Hiển thị thống kê định dạng
        formats = {}
        for f in word_files:
            ext = f.suffix.lower()
            formats[ext] = formats.get(ext, 0) + 1
        
        format_stats = "\n".join([f"  {ext}: {count} file" for ext, count in formats.items()])
        
        # Cảnh báo cho PDF
        if output_format == "pdf_link":
            result = messagebox.askyesno("Cảnh báo PDF", 
                                       f"Sắp xử lý {len(word_files)} file sang PDF.\n\n"
                                       f"Thống kê định dạng:\n{format_stats}\n\n"
                                       f"Các file PDF sẽ KHÔNG xem được video trên Android!\n\n"
                                       f"Bạn có muốn tiếp tục không?")
            if not result:
                return
        
        # Disable nút
        self.folder_start_btn.config(state='disabled')
        self.is_converting = True
        self.start_time = time.time()
        
        # Xóa log cũ
        self.log_text.delete(1.0, tk.END)
        self.log("🚀 BẮT ĐẦU XỬ LÝ HÀNG LOẠT", 'info')
        self.log(f"📁 Folder Word: {word_folder}", 'info')
        self.log(f"📁 Thư mục lưu: {output_folder}", 'info')
        self.log(f"🎯 Định dạng: {output_format.upper()}", 'info')
        self.log(f"📊 Tổng số file: {len(word_files)}", 'info')
        self.log("📊 Thống kê định dạng:", 'info')
        for ext, count in formats.items():
            self.log(f"   {ext}: {count} file", 'format')
        
        # Cập nhật thời gian
        self.update_time()
        
        # Chạy trong thread riêng
        thread = threading.Thread(target=self.folder_conversion_thread, 
                                 args=(word_files, output_folder, output_format,
                                      android_optimize, create_readme))
        thread.daemon = True
        thread.start()
        
    def folder_conversion_thread(self, word_files, output_folder, output_format,
                                android_optimize, create_readme):
        total_files = len(word_files)
        success_count = 0
        error_files = []
        
        for i, word_file in enumerate(word_files):
            try:
                base_name = word_file.stem
                
                # Cập nhật progress
                progress = int((i / total_files) * 100)
                self.update_progress(progress, f"🔄 Đang xử lý {i+1}/{total_files}: {word_file.name}")
                
                if output_format == "html":
                    output_path = os.path.join(output_folder, f"{base_name}.html")
                    success = self.word_to_html(str(word_file), output_path, 
                                               optimize=android_optimize,
                                               create_readme=create_readme)
                elif output_format == "pdf_link":
                    output_path = os.path.join(output_folder, f"{base_name}.pdf")
                    success = self.create_pdf_with_links(str(word_file), output_path,
                                                        create_readme=create_readme)
                else:  # zip
                    output_path = os.path.join(output_folder, f"{base_name}.zip")
                    success = self.create_zip_package(str(word_file), output_path,
                                                     optimize=android_optimize,
                                                     create_readme=create_readme)
                
                if success:
                    success_count += 1
                    self.log(f"✅ {i+1}/{total_files}: {word_file.name}", 'success')
                else:
                    error_files.append(word_file.name)
                    self.log(f"❌ {i+1}/{total_files}: {word_file.name}", 'error')
                    
            except Exception as e:
                error_files.append(f"{word_file.name} - {str(e)}")
                self.log(f"❌ {i+1}/{total_files}: {word_file.name} - {str(e)}", 'error')
        
        # Hoàn thành
        elapsed = time.time() - self.start_time
        self.update_progress(100, f"✅ Hoàn thành! ({success_count}/{total_files} file - {elapsed:.1f}s)", 'success')
        
        # Thông báo kết quả
        if error_files:
            error_msg = "\n".join(error_files[:10])
            if len(error_files) > 10:
                error_msg += f"\n... và {len(error_files) - 10} lỗi khác"
            
            messagebox.showwarning("Kết quả xử lý", 
                                 f"✅ Thành công: {success_count}/{total_files} file\n"
                                 f"❌ Thất bại: {len(error_files)} file\n\n"
                                 f"Chi tiết lỗi:\n{error_msg}")
        else:
            messagebox.showinfo("✅ Thành công", 
                              f"Đã xử lý thành công {success_count}/{total_files} file!\n"
                              f"⏱️ Thời gian: {elapsed:.1f}s")
        
        self.folder_start_btn.config(state='normal')
        self.is_converting = False
        self.start_time = None
        self.time_label.config(text="")

def main():
    root = tk.Tk()
    app = WordToVideoConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()