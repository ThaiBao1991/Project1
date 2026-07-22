import requests
import os
from tkinter import *
from tkinter import ttk, filedialog, messagebox
import threading
import webbrowser
from datetime import datetime
import time
import re
from bs4 import BeautifulSoup
import random

class FacebookLikesManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Likes Manager - Đọc và tải media")
        self.root.geometry("1300x800")
        
        self.access_token = None
        self.all_posts = []
        self.selected_folder = ""
        self.is_loading = False
        self.stop_loading = False
        self.total_loaded = 0
        self.user_id = None
        self.user_name = None
        self.html_file_path = None
        self.unlike_count = 0
        
        # Session để tải ảnh
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="8")
        main_frame.pack(fill=BOTH, expand=True)
        
        # ========== FRAME ĐĂNG NHẬP ==========
        login_frame = ttk.LabelFrame(main_frame, text="🔐 ĐĂNG NHẬP", padding=5)
        login_frame.pack(fill="x", pady=3)
        
        ttk.Label(login_frame, text="Access Token:").grid(row=0, column=0, sticky="w", padx=2)
        self.token_entry = ttk.Entry(login_frame, width=70)
        self.token_entry.grid(row=0, column=1, padx=2, sticky="ew")
        
        btn_frame = ttk.Frame(login_frame)
        btn_frame.grid(row=0, column=2, padx=2)
        ttk.Button(btn_frame, text="🔑 Đăng nhập", command=self.login, width=12).pack(side=LEFT, padx=1)
        ttk.Button(btn_frame, text="📘 Lấy token", command=lambda: webbrowser.open("https://developers.facebook.com/tools/explorer/")).pack(side=LEFT, padx=1)
        
        self.user_info = StringVar(value="⏳ Chưa đăng nhập")
        ttk.Label(login_frame, textvariable=self.user_info, foreground="blue").grid(row=1, column=0, columnspan=3, sticky="w", pady=2)
        
        login_frame.columnconfigure(1, weight=1)
        
        # ========== FRAME THƯ MỤC LƯU ==========
        folder_frame = ttk.LabelFrame(main_frame, text="📁 THƯ MỤC LƯU TRỮ", padding=5)
        folder_frame.pack(fill="x", pady=3)
        
        self.folder_path = StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads", "FB_Likes"))
        ttk.Entry(folder_frame, textvariable=self.folder_path, width=70).pack(side=LEFT, padx=2, fill=X, expand=True)
        ttk.Button(folder_frame, text="📂 Chọn", command=self.select_folder, width=8).pack(side=LEFT, padx=1)
        ttk.Button(folder_frame, text="📁 Mở", command=self.open_folder, width=5).pack(side=LEFT)
        
        # ========== FRAME DỮ LIỆU FB ==========
        fbdata_frame = ttk.LabelFrame(main_frame, text="📥 DỮ LIỆU FACEBOOK (HTML)", padding=5)
        fbdata_frame.pack(fill="x", pady=3)
        
        ttk.Label(fbdata_frame, text="File HTML:").pack(side=LEFT, padx=2)
        self.html_path = StringVar()
        ttk.Entry(fbdata_frame, textvariable=self.html_path, width=60).pack(side=LEFT, padx=2, fill=X, expand=True)
        ttk.Button(fbdata_frame, text="📂 Chọn file HTML", command=self.select_html_file, width=18).pack(side=LEFT, padx=2)
        ttk.Button(fbdata_frame, text="🚀 Đọc dữ liệu", command=self.read_html_file, width=15).pack(side=LEFT, padx=2)
        
        # ========== FRAME TÙY CHỌN ==========
        option_frame = ttk.LabelFrame(main_frame, text="⚙️ TÙY CHỌN TẢI", padding=5)
        option_frame.pack(fill="x", pady=3)
        
        row1 = ttk.Frame(option_frame)
        row1.pack(fill="x", pady=2)
        
        ttk.Label(row1, text="Số bài muốn hiển thị:").pack(side=LEFT, padx=2)
        self.limit_var = StringVar(value="1000")
        ttk.Spinbox(row1, from_=10, to=100000, textvariable=self.limit_var, width=8).pack(side=LEFT, padx=2)
        ttk.Label(row1, text="(0 = tất cả)").pack(side=LEFT, padx=2)
        
        self.download_images = BooleanVar(value=True)
        ttk.Checkbutton(row1, text="🖼️ Tải ảnh", variable=self.download_images).pack(side=LEFT, padx=5)
        
        self.download_videos = BooleanVar(value=True)
        ttk.Checkbutton(row1, text="🎥 Tải video", variable=self.download_videos).pack(side=LEFT, padx=5)
        
        # ========== FRAME TÙY CHỌN HỦY LIKE ==========
        unlike_frame = ttk.LabelFrame(main_frame, text="❤️ TÙY CHỌN HỦY LIKE", padding=5)
        unlike_frame.pack(fill="x", pady=3)
        
        row2 = ttk.Frame(unlike_frame)
        row2.pack(fill="x", pady=2)
        
        ttk.Label(row2, text="Delay (giây):").pack(side=LEFT, padx=2)
        self.delay_var = StringVar(value="3")
        ttk.Spinbox(row2, from_=1, to=10, textvariable=self.delay_var, width=5).pack(side=LEFT, padx=2)
        
        self.random_delay = BooleanVar(value=True)
        ttk.Checkbutton(row2, text="Random delay", variable=self.random_delay).pack(side=LEFT, padx=5)
        
        # ========== FRAME NÚT CHỨC NĂNG ==========
        control_frame = ttk.LabelFrame(main_frame, text="🎮 ĐIỀU KHIỂN", padding=5)
        control_frame.pack(fill="x", pady=3)
        
        row_btn1 = ttk.Frame(control_frame)
        row_btn1.pack(fill="x", pady=2)
        
        ttk.Button(row_btn1, text="📥 TẢI MEDIA ĐÃ CHỌN", 
                  command=self.download_selected, width=20).pack(side=LEFT, padx=2)
        ttk.Button(row_btn1, text="📥 TẢI ALL MEDIA", 
                  command=self.download_all_media, width=15).pack(side=LEFT, padx=2)
        ttk.Button(row_btn1, text="❤️ HỦY LIKE ĐÃ CHỌN", 
                  command=self.unlike_selected, width=18).pack(side=LEFT, padx=2)
        ttk.Button(row_btn1, text="📊 THỐNG KÊ", 
                  command=self.show_stats, width=12).pack(side=LEFT, padx=2)
        
        # ========== THANH TIẾN TRÌNH ==========
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="x", pady=2)
        
        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress.pack(side=LEFT, fill="x", expand=True)
        
        self.count_label = ttk.Label(progress_frame, text="0 bài", width=15, font=('Arial', 10, 'bold'))
        self.count_label.pack(side=RIGHT, padx=5)
        
        # ========== FRAME DANH SÁCH ==========
        list_frame = ttk.LabelFrame(main_frame, text="📋 DANH SÁCH BÀI VIẾT ĐÃ LIKE", padding=5)
        list_frame.pack(fill="both", expand=True, pady=3)
        
        # Tạo notebook
        self.notebook = ttk.Notebook(list_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Tab 1: Tất cả
        self.all_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.all_tab, text="📄 Tất cả (0)")
        self.tree_all = self.create_treeview(self.all_tab)
        
        # Tab 2: Có ảnh
        self.img_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.img_tab, text="🖼️ Có ảnh (0)")
        self.tree_img = self.create_treeview(self.img_tab)
        
        # Tab 3: Có video
        self.vid_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.vid_tab, text="🎥 Có video (0)")
        self.tree_vid = self.create_treeview(self.vid_tab)
        
        # ========== FRAME TÌM KIẾM ==========
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill="x", pady=2)
        
        ttk.Label(search_frame, text="🔍 Tìm:").pack(side=LEFT, padx=2)
        self.search_var = StringVar()
        self.search_var.trace('w', self.filter_posts)
        ttk.Entry(search_frame, textvariable=self.search_var, width=40).pack(side=LEFT, padx=2, fill=X, expand=True)
        
        ttk.Label(search_frame, text="Chọn:").pack(side=LEFT, padx=(20,2))
        ttk.Button(search_frame, text="✅ Tất cả", command=self.select_all, width=8).pack(side=LEFT, padx=1)
        ttk.Button(search_frame, text="❌ Bỏ chọn", command=self.deselect_all, width=8).pack(side=LEFT, padx=1)
        
        self.status_var = StringVar(value="✅ Sẵn sàng")
        ttk.Label(search_frame, textvariable=self.status_var, foreground="green").pack(side=RIGHT, padx=5)
        
        # ========== DEBUG ==========
        debug_frame = ttk.LabelFrame(main_frame, text="📝 DEBUG", padding=5)
        debug_frame.pack(fill="x", pady=2)
        
        self.debug_text = Text(debug_frame, height=4, wrap=WORD, font=('Consolas', 8))
        scroll = ttk.Scrollbar(debug_frame, orient="vertical", command=self.debug_text.yview)
        self.debug_text.configure(yscrollcommand=scroll.set)
        
        self.debug_text.pack(side=LEFT, fill="x", expand=True)
        scroll.pack(side=RIGHT, fill="y")
        
        self.create_folders()
        
    def create_treeview(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        
        columns = ("STT", "ID", "NGƯỜI ĐĂNG", "NỘI DUNG", "THỜI GIAN", "LOẠI", "ẢNH", "VIDEO")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        
        tree.heading("STT", text="STT")
        tree.heading("ID", text="ID")
        tree.heading("NGƯỜI ĐĂNG", text="Người đăng")
        tree.heading("NỘI DUNG", text="Nội dung")
        tree.heading("THỜI GIAN", text="Thời gian")
        tree.heading("LOẠI", text="Loại")
        tree.heading("ẢNH", text="Ảnh")
        tree.heading("VIDEO", text="Video")
        
        tree.column("STT", width=40, anchor="center")
        tree.column("ID", width=150)
        tree.column("NGƯỜI ĐĂNG", width=120)
        tree.column("NỘI DUNG", width=350)
        tree.column("THỜI GIAN", width=130, anchor="center")
        tree.column("LOẠI", width=80, anchor="center")
        tree.column("ẢNH", width=40, anchor="center")
        tree.column("VIDEO", width=40, anchor="center")
        
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        tree.bind('<Double-1>', self.open_post_link)
        
        return tree
        
    def open_post_link(self, event):
        tree = event.widget
        selection = tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = tree.item(item)['values']
        
        if len(values) >= 2:
            post_id = values[1]
            url = f"https://facebook.com/{post_id}"
            webbrowser.open(url)
            self.log(f"Đã mở: {url}")
        
    def select_html_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file HTML từ Facebook",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        if file_path:
            self.html_path.set(file_path)
            self.html_file_path = file_path
            self.log(f"📂 Đã chọn file: {os.path.basename(file_path)}")
            
    def read_html_file(self):
        if not self.html_file_path or not os.path.exists(self.html_file_path):
            messagebox.showerror("Lỗi", "Vui lòng chọn file HTML trước!")
            return
            
        self.progress.start()
        self.status_var.set("⏳ Đang đọc file HTML...")
        
        thread = threading.Thread(target=self._read_html_thread, args=(self.html_file_path,))
        thread.daemon = True
        thread.start()
        
    def _read_html_thread(self, html_file):
        try:
            self.all_posts = []
            self.total_loaded = 0
            
            self.log(f"📖 Đang đọc file: {os.path.basename(html_file)}")
            
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.log(f"📊 Kích thước file: {len(content)} bytes")
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Tìm tất cả các section
            sections = soup.find_all('section', class_=re.compile(r'_3-95|_a6-g'))
            self.log(f"🔍 Tìm thấy {len(sections)} sections")
            
            for section in sections:
                try:
                    post_data = self._extract_from_section(section)
                    if post_data:
                        self.all_posts.append(post_data)
                        self.total_loaded += 1
                        
                        if self.total_loaded % 100 == 0:
                            self.log(f"📊 Đã đọc {self.total_loaded} bài...")
                            
                except Exception as e:
                    continue
                    
            self.root.after(0, lambda: self._display_html_data(self.total_loaded))
            
        except Exception as e:
            self.root.after(0, lambda: self._show_error(f"Lỗi đọc file: {str(e)}"))
            
    def _extract_from_section(self, section):
        try:
            # Tìm link
            link_tag = section.find('a', href=re.compile(r'facebook|fb\.com|/posts/|/videos/|/photo\.php|permalink\.php'))
            if not link_tag:
                return None
                
            href = link_tag.get('href', '')
            
            # Extract ID từ link
            post_id = self._extract_id_from_url(href)
            if not post_id:
                return None
                
            # Tìm tên người đăng
            name = self._extract_name(section)
            
            # Tìm thời gian
            time_str = self._extract_time(section)
            
            # Tìm loại cảm xúc
            emotion = self._extract_emotion(section)
            
            # Tìm nội dung
            content = self._extract_content(section)
            
            # Phát hiện ảnh/video
            has_image, has_video = self._detect_media(section, href, content)
            
            return {
                'id': post_id,
                'from_name': name,
                'content': content,
                'time': time_str,
                'emotion': emotion,
                'has_image': has_image,
                'has_video': has_video,
                'url': href,
                'downloaded': False
            }
            
        except Exception as e:
            return None
            
    def _extract_name(self, section):
        name_tag = section.find('td', string='Tên')
        if name_tag:
            next_td = name_tag.find_next('td')
            if next_td:
                return next_td.get_text(strip=True)
                
        name_div = section.find('div', class_=re.compile(r'_a6-p|_2ph'))
        if name_div:
            text = name_div.get_text(strip=True)
            if text and len(text) < 100:
                return text
                
        return "Không rõ"
        
    def _extract_time(self, section):
        footer = section.find('footer')
        if footer:
            time_div = footer.find('div', class_=re.compile(r'_a72d|_3-94'))
            if time_div:
                return time_div.get_text(strip=True)
        return "Không rõ"
        
    def _extract_emotion(self, section):
        emotion_td = section.find('td', string='Cảm xúc')
        if emotion_td:
            next_td = emotion_td.find_next('td')
            if next_td:
                return next_td.get_text(strip=True)
        return "Thích"
        
    def _extract_content(self, section):
        content_divs = section.find_all('div', class_=re.compile(r'_a6-p|_2ph|_aoa9'))
        for div in content_divs:
            text = div.get_text(strip=True)
            if text and len(text) > 20:
                return text[:300]
        return ""
        
    def _detect_media(self, section, url, content):
        has_image = False
        has_video = False
        
        content_lower = content.lower()
        url_lower = url.lower()
        
        # Kiểm tra URL
        if any(x in url_lower for x in ['/photo', 'fbid=', 'photo.php', '/photos', 'permalink.php']):
            has_image = True
            
        if any(x in url_lower for x in ['/video', '/videos', '/reel']):
            has_video = True
            
        # Kiểm tra nội dung
        if any(x in content_lower for x in ['ảnh', 'photo', 'hình ảnh', 'pic', 'image']):
            has_image = True
            
        if any(x in content_lower for x in ['video', 'clip', 'reel', 'vd']):
            has_video = True
            
        # Kiểm tra thẻ HTML
        if section.find('img'):
            has_image = True
            
        if section.find('video'):
            has_video = True
            
        return has_image, has_video
        
    def _extract_id_from_url(self, url):
        patterns = [
            r'/(\d+)_(\d+)',
            r'/posts/([^/?]+)',
            r'/videos/(\d+)',
            r'/reel/(\d+)',
            r'fbid=(\d+)',
            r'story_fbid=(\d+)',
            r'/photo\.php\?fbid=(\d+)',
            r'permalink\.php\?story_fbid=(\d+)',
            r'pfbid([a-zA-Z0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                if pattern == r'/(\d+)_(\d+)':
                    return f"{match.group(1)}_{match.group(2)}"
                elif pattern == r'pfbid([a-zA-Z0-9]+)':
                    return f"pfbid{match.group(1)}"
                else:
                    return match.group(1)
                    
        # Lấy phần cuối URL
        parts = url.split('/')
        for part in reversed(parts):
            if part and part not in ['posts', 'videos', 'permalink.php', 'photo.php', 'reel']:
                clean_part = part.split('?')[0].split('#')[0].split('&')[0]
                if clean_part:
                    return clean_part
                    
        return None
            
    def _display_html_data(self, count):
        self.progress.stop()
        
        for tree in [self.tree_all, self.tree_img, self.tree_vid]:
            for item in tree.get_children():
                tree.delete(item)
                
        limit = int(self.limit_var.get())
        if limit == 0:
            limit = len(self.all_posts)
            
        display_posts = self.all_posts[:min(limit, len(self.all_posts))]
        
        for i, post in enumerate(display_posts, 1):
            self._add_to_trees(post, i)
            
        img_count = sum(1 for p in display_posts if p['has_image'])
        vid_count = sum(1 for p in display_posts if p['has_video'])
        
        self.notebook.tab(0, text=f"📄 Tất cả ({len(display_posts)})")
        self.notebook.tab(1, text=f"🖼️ Có ảnh ({img_count})")
        self.notebook.tab(2, text=f"🎥 Có video ({vid_count})")
        
        self.status_var.set(f"✅ Đã đọc {count} bài ({img_count} ảnh, {vid_count} video)")
        self.log(f"✅ ĐÃ ĐỌC {count} BÀI")
        
    def _add_to_trees(self, post, index):
        values = (
            str(index),
            post['id'],
            post['from_name'][:50],
            post['content'][:100] + '...' if len(post['content']) > 100 else post['content'],
            post['time'],
            post['emotion'],
            '✅' if post['has_image'] else '❌',
            '✅' if post['has_video'] else '❌'
        )
        
        self.tree_all.insert('', 'end', values=values, tags=(post['id'],))
        
        if post['has_image']:
            self.tree_img.insert('', 'end', values=values, tags=(post['id'],))
            
        if post['has_video']:
            self.tree_vid.insert('', 'end', values=values, tags=(post['id'],))
            
    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.debug_text.insert(END, f"[{timestamp}] {msg}\n")
        self.debug_text.see(END)
        print(f"[DEBUG] {msg}")
        
    def create_folders(self):
        try:
            folder = self.folder_path.get()
            os.makedirs(os.path.join(folder, "images"), exist_ok=True)
            os.makedirs(os.path.join(folder, "videos"), exist_ok=True)
        except:
            pass
            
    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_path.get())
        if folder:
            self.folder_path.set(folder)
            self.create_folders()
            self.log(f"📁 Đã chọn thư mục lưu: {folder}")
            
    def open_folder(self):
        folder = self.folder_path.get()
        if os.path.exists(folder):
            os.startfile(folder)
            
    def get_current_tree(self):
        tab = self.notebook.index(self.notebook.select())
        if tab == 0:
            return self.tree_all
        elif tab == 1:
            return self.tree_img
        else:
            return self.tree_vid
            
    def select_all(self):
        tree = self.get_current_tree()
        for item in tree.get_children():
            tree.selection_add(item)
        self.log(f"✅ Đã chọn {len(tree.get_children())} bài")
        
    def deselect_all(self):
        tree = self.get_current_tree()
        tree.selection_remove(tree.selection())
        
    def login(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("Lỗi", "Nhập Access Token!")
            return
            
        self.access_token = token
        self.log("🔄 Đang đăng nhập...")
        self.progress.start()
        
        thread = threading.Thread(target=self._login_thread)
        thread.daemon = True
        thread.start()
        
    def _login_thread(self):
        try:
            url = "https://graph.facebook.com/v18.0/me"
            params = {'access_token': self.access_token, 'fields': 'id,name'}
            
            r = requests.get(url, params=params)
            data = r.json()
            
            if 'error' in data:
                self.root.after(0, lambda: self._login_error(data['error']['message']))
            else:
                self.user_id = data.get('id')
                self.user_name = data.get('name')
                self.root.after(0, lambda: self._login_success(data))
                
        except Exception as e:
            self.root.after(0, lambda: self._login_error(str(e)))
            
    def _login_success(self, data):
        self.progress.stop()
        self.user_info.set(f"✅ {data.get('name')}")
        self.status_var.set("✅ Đã đăng nhập")
        self.log(f"✅ Đăng nhập thành công: {data.get('name')}")
        
    def _login_error(self, msg):
        self.progress.stop()
        self.user_info.set(f"❌ Lỗi")
        messagebox.showerror("Lỗi", msg)
        
    def filter_posts(self, *args):
        search = self.search_var.get().lower()
        
        for tree in [self.tree_all, self.tree_img, self.tree_vid]:
            for item in tree.get_children():
                tree.delete(item)
                
        for i, post in enumerate(self.all_posts, 1):
            if search in post['content'].lower() or search in post['from_name'].lower() or not search:
                self._add_to_trees(post, i)
                
    def download_selected(self):
        """Tải media từ bài viết đã chọn"""
        tree = self.get_current_tree()
        selected = tree.selection()
        
        if not selected:
            messagebox.showwarning("Cảnh báo", "Chọn bài viết cần tải!")
            return
            
        if not self.access_token:
            messagebox.showerror("Lỗi", "Cần đăng nhập để tải media!")
            return
            
        if not os.path.exists(self.folder_path.get()):
            messagebox.showwarning("Cảnh báo", "Chọn thư mục lưu trữ!")
            return
            
        self.progress.start()
        self.status_var.set("⏳ Đang tải media...")
        
        thread = threading.Thread(target=self._download_selected_thread, args=(selected, tree))
        thread.daemon = True
        thread.start()
        
    def download_all_media(self):
        """Tải tất cả media"""
        if not self.all_posts:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu!")
            return
            
        if not self.access_token:
            messagebox.showerror("Lỗi", "Cần đăng nhập để tải media!")
            return
            
        total = sum(1 for p in self.all_posts if (p['has_image'] and self.download_images.get()) or 
                   (p['has_video'] and self.download_videos.get()))
                   
        if total == 0:
            messagebox.showinfo("Thông báo", "Không có media nào để tải!")
            return
            
        if messagebox.askyesno("Xác nhận", f"Tải {total} media từ {len(self.all_posts)} bài viết?\n\n"
                               f"Lưu ý: Quá trình này có thể chậm và một số bài đã bị xóa sẽ không tải được."):
            self.progress.start()
            self.status_var.set(f"⏳ Đang tải {total} media...")
            
            thread = threading.Thread(target=self._download_all_media_thread)
            thread.daemon = True
            thread.start()
            
    def _download_selected_thread(self, items, tree):
        """Thread tải media đã chọn"""
        success = 0
        total = 0
        
        for i, item in enumerate(items, 1):
            try:
                post_id = tree.item(item)['tags'][0] if tree.item(item)['tags'] else None
                
                if not post_id:
                    values = tree.item(item)['values']
                    if len(values) >= 2:
                        post_id = values[1]
                        
                if post_id:
                    self.log(f"[{i}/{len(items)}] 🔍 Đang xử lý: {post_id}")
                    
                    # Gọi API để lấy thông tin bài viết
                    url = f"https://graph.facebook.com/v18.0/{post_id}"
                    params = {
                        'access_token': self.access_token,
                        'fields': 'attachments{media,subattachments,type},message'
                    }
                    
                    try:
                        response = requests.get(url, params=params, timeout=10)
                        data = response.json()
                        
                        if 'error' in data:
                            error_msg = data['error'].get('message', '')
                            if '100' in error_msg and 'access token' in error_msg.lower():
                                self.log(f"⚠️ Token hết hạn hoặc không có quyền")
                            else:
                                self.log(f"❌ Lỗi API: {error_msg[:100]}")
                            continue
                            
                        # Xử lý attachments
                        attachments = data.get('attachments', {}).get('data', [])
                        downloaded = self._process_attachments(attachments, post_id)
                        
                        if downloaded > 0:
                            success += 1
                            self.log(f"✅ Đã tải {downloaded} file từ {post_id}")
                        else:
                            self.log(f"ℹ️ Không tìm thấy media trong {post_id}")
                            
                        total += 1
                        
                    except requests.exceptions.Timeout:
                        self.log(f"⏰ Timeout khi tải {post_id}")
                    except Exception as e:
                        self.log(f"❌ Lỗi: {str(e)}")
                        
                # Delay giữa các request
                time.sleep(1.5)
                
            except Exception as e:
                self.log(f"❌ Lỗi xử lý: {str(e)}")
                
        self.root.after(0, lambda: self._download_complete(success, total))
        
    def _download_all_media_thread(self):
        """Thread tải tất cả media"""
        success = 0
        total = 0
        posts_to_download = []
        
        # Lọc bài viết có media
        for post in self.all_posts:
            if (post['has_image'] and self.download_images.get()) or \
               (post['has_video'] and self.download_videos.get()):
                posts_to_download.append(post)
                
        self.log(f"📊 Sẽ xử lý {len(posts_to_download)} bài có media")
        
        for i, post in enumerate(posts_to_download, 1):
            try:
                post_id = post['id']
                self.log(f"[{i}/{len(posts_to_download)}] 🔍 Đang xử lý: {post_id}")
                
                # Gọi API
                url = f"https://graph.facebook.com/v18.0/{post_id}"
                params = {
                    'access_token': self.access_token,
                    'fields': 'attachments{media,subattachments,type},message'
                }
                
                try:
                    response = requests.get(url, params=params, timeout=10)
                    data = response.json()
                    
                    if 'error' in data:
                        self.log(f"❌ Lỗi API: {data['error'].get('message', '')[:100]}")
                        continue
                        
                    attachments = data.get('attachments', {}).get('data', [])
                    downloaded = self._process_attachments(attachments, post_id)
                    
                    if downloaded > 0:
                        success += 1
                        self.log(f"✅ Đã tải {downloaded} file")
                    else:
                        self.log(f"ℹ️ Không có media")
                        
                    total += 1
                    
                except requests.exceptions.Timeout:
                    self.log(f"⏰ Timeout")
                except Exception as e:
                    self.log(f"❌ Lỗi: {str(e)}")
                    
                # Delay
                time.sleep(1.5)
                
            except Exception as e:
                self.log(f"❌ Lỗi: {str(e)}")
                
        self.root.after(0, lambda: self._download_complete(success, total))
        
    def _process_attachments(self, attachments, post_id):
        """Xử lý attachments và tải file"""
        downloaded = 0
        
        for att in attachments:
            media_type = att.get('type', '').lower()
            media = att.get('media', {})
            
            # Xử lý ảnh
            if 'photo' in media_type or 'image' in media_type:
                if self.download_images.get():
                    if 'image' in media and 'src' in media['image']:
                        url = media['image']['src']
                        if self._download_file(url, post_id, 'image'):
                            downloaded += 1
                            
            # Xử lý video
            elif 'video' in media_type:
                if self.download_videos.get():
                    if 'source' in media:
                        url = media['source']
                        if self._download_file(url, post_id, 'video'):
                            downloaded += 1
                            
            # Xử lý subattachments
            sub = att.get('subattachments', {}).get('data', [])
            for s in sub:
                sub_type = s.get('type', '').lower()
                sub_media = s.get('media', {})
                
                if 'photo' in sub_type or 'image' in sub_type:
                    if self.download_images.get():
                        if 'image' in sub_media and 'src' in sub_media['image']:
                            url = sub_media['image']['src']
                            if self._download_file(url, post_id, 'image'):
                                downloaded += 1
                elif 'video' in sub_type:
                    if self.download_videos.get():
                        if 'source' in sub_media:
                            url = sub_media['source']
                            if self._download_file(url, post_id, 'video'):
                                downloaded += 1
                                
        return downloaded
        
    def _download_file(self, url, post_id, media_type):
        """Tải một file"""
        try:
            if media_type == 'video':
                folder = os.path.join(self.folder_path.get(), "videos")
                ext = '.mp4'
            else:
                folder = os.path.join(self.folder_path.get(), "images")
                ext = '.jpg'
                
            # Tạo tên file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"fb_{post_id}_{timestamp}{ext}"
            filename = "".join(c for c in filename if c.isalnum() or c in '._-')
            filepath = os.path.join(folder, filename)
            
            # Tải file
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.session.get(url, stream=True, timeout=30, headers=headers)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                self.log(f"✅ Đã tải: {filename}")
                return True
            else:
                self.log(f"⚠️ HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Lỗi tải: {str(e)[:50]}")
            return False
            
    def _download_complete(self, success, total):
        self.progress.stop()
        if total > 0:
            self.status_var.set(f"✅ Đã tải {success}/{total} bài thành công")
            messagebox.showinfo("Hoàn thành", f"Tải thành công {success}/{total} bài có media!")
        else:
            self.status_var.set("❌ Không tải được bài nào")
            messagebox.showwarning("Kết quả", "Không tải được media nào!\n\n"
                                  "Nguyên nhân:\n"
                                  "1. Token hết hạn hoặc thiếu quyền\n"
                                  "2. Bài viết đã bị xóa\n"
                                  "3. Bài viết ở chế độ riêng tư")
        
    def unlike_selected(self):
        tree = self.get_current_tree()
        selected = tree.selection()
        
        if not selected:
            messagebox.showwarning("Cảnh báo", "Chọn bài viết cần hủy like!")
            return
            
        if not self.access_token:
            messagebox.showerror("Lỗi", "Cần đăng nhập để hủy like!")
            return
            
        count = len(selected)
        if not messagebox.askyesno("Xác nhận", f"Hủy like {count} bài viết?"):
            return
            
        self.progress.start()
        self.status_var.set(f"⏳ Đang hủy like {count} bài...")
        
        thread = threading.Thread(target=self._unlike_thread, args=(selected, tree))
        thread.daemon = True
        thread.start()
        
    def _unlike_thread(self, items, tree):
        success = 0
        failed = 0
        
        for i, item in enumerate(items, 1):
            try:
                post_id = tree.item(item)['tags'][0] if tree.item(item)['tags'] else None
                
                if not post_id:
                    values = tree.item(item)['values']
                    if len(values) >= 2:
                        post_id = values[1]
                        
                if post_id:
                    self.log(f"[{i}/{len(items)}] 🔄 Hủy like: {post_id}")
                    
                    url = f"https://graph.facebook.com/v18.0/{post_id}/likes"
                    params = {'access_token': self.access_token}
                    
                    response = requests.delete(url, params=params)
                    result = response.json()
                    
                    if result.get('success'):
                        success += 1
                        self.unlike_count += 1
                        self.root.after(0, lambda i=item: tree.delete(i))
                        self.log(f"✅ Đã hủy like: {post_id}")
                    else:
                        failed += 1
                        self.log(f"❌ Lỗi: {result.get('error', {}).get('message', 'Unknown')}")
                        
                # Delay
                base_delay = float(self.delay_var.get())
                if self.random_delay.get():
                    delay = base_delay * random.uniform(0.8, 1.2)
                else:
                    delay = base_delay
                    
                if i < len(items):
                    time.sleep(delay)
                    
            except Exception as e:
                failed += 1
                self.log(f"❌ Lỗi: {str(e)}")
                
        self.root.after(0, lambda: self._unlike_complete(success, failed))
        
    def _unlike_complete(self, success, failed):
        self.progress.stop()
        self.status_var.set(f"✅ Đã hủy like {success} bài, thất bại {failed} bài")
        messagebox.showinfo("Kết quả", f"✅ Thành công: {success}\n❌ Thất bại: {failed}")
        
    def show_stats(self):
        if not self.all_posts:
            messagebox.showinfo("Thống kê", "Chưa có dữ liệu!")
            return
            
        total = len(self.all_posts)
        images = sum(1 for p in self.all_posts if p['has_image'])
        videos = sum(1 for p in self.all_posts if p['has_video'])
        both = sum(1 for p in self.all_posts if p['has_image'] and p['has_video'])
        
        # Đếm theo loại URL
        permalink_count = sum(1 for p in self.all_posts if 'permalink.php' in p.get('url', ''))
        
        # Đếm file đã tải
        img_folder = os.path.join(self.folder_path.get(), "images")
        vid_folder = os.path.join(self.folder_path.get(), "videos")
        
        downloaded_img = len([f for f in os.listdir(img_folder) if f.endswith('.jpg')]) if os.path.exists(img_folder) else 0
        downloaded_vid = len([f for f in os.listdir(vid_folder) if f.endswith('.mp4')]) if os.path.exists(vid_folder) else 0
        
        stats = f"""📊 THỐNG KÊ

📋 BÀI VIẾT:
• Tổng số: {total}
• Có ảnh: {images}
• Có video: {videos}
• Có cả ảnh & video: {both}
• Dạng permalink: {permalink_count}

💾 ĐÃ TẢI:
• Ảnh: {downloaded_img}
• Video: {downloaded_vid}

📁 Thư mục:
{self.folder_path.get()}"""
        
        messagebox.showinfo("Thống kê", stats)
        
    def _show_error(self, msg):
        self.progress.stop()
        self.status_var.set("❌ Lỗi")
        self.log(f"❌ {msg}")
        messagebox.showerror("Lỗi", msg)

if __name__ == "__main__":
    root = Tk()
    app = FacebookLikesManager(root)
    root.mainloop()