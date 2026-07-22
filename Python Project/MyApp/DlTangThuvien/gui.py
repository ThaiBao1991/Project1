import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import json
from datetime import datetime
import webbrowser
from urllib.parse import urlparse
import time
import requests
from bs4 import BeautifulSoup
import re

# Import main downloader
from main import TruyenDownloader

class SiteConfigManager:
    """Quản lý cấu hình các site"""
    
    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.config_file = os.path.join(storage_path, 'sites_config.json')
        self.configs = self.load_configs()
    
    def load_configs(self):
        """Load cấu hình từ file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.get_default_config()
        else:
            return self.get_default_config()
    
    def get_default_config(self):
        """Cấu hình mặc định"""
        return {
            "tangthuvien": {
                "domain": "tangthuvien.net",
                "name": "Tangthuvien.net",
                "selectors": {
                    "toc": {
                        "type": "css",
                        "script": ".chapter-list a, .list-chapter a, .ds-list-chapter a"
                    },
                    "title": {
                        "type": "css", 
                        "script": ".chapter-title, h1.chapter-title, .chap-title"
                    },
                    "content": {
                        "type": "css",
                        "script": ".chapter-content, .content-chapter, #chapter-content"
                    }
                },
                "toc_page": "/doc-truyen/{story_slug}/",
                "chapter_pattern": "/doc-truyen/{story_slug}/chuong-{chapter_number}",
                "needs_login": True,
                "encoding": "utf-8",
                "use_selenium": False
            }
        }
    
    def save_configs(self):
        """Lưu cấu hình"""
        os.makedirs(self.storage_path, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.configs, f, ensure_ascii=False, indent=2)
    
    def get_site_config(self, site_name):
        """Lấy cấu hình của một site"""
        return self.configs.get(site_name, {})
    
    def update_site_config(self, site_name, config):
        """Cập nhật cấu hình site"""
        self.configs[site_name] = config
        self.save_configs()
    
    def delete_site_config(self, site_name):
        """Xóa cấu hình site"""
        if site_name in self.configs:
            del self.configs[site_name]
            self.save_configs()
    
    def get_site_by_url(self, url):
        """Xác định site dựa trên URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        
        for site_name, config in self.configs.items():
            if config.get('domain', '') in domain:
                return site_name, config
        return None, None


class SelectorTester:
    """Test các selector trên trang web với xử lý lỗi kết nối"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        
        # Thêm retry strategy
        retry_strategy = requests.adapters.Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def fetch_page(self, url, use_selenium=False, cookie_file=None):
        """Lấy nội dung trang với xử lý lỗi"""
        try:
            if use_selenium:
                return self.fetch_with_selenium(url, cookie_file)
            else:
                return self.fetch_with_requests(url)
        except Exception as e:
            print(f"Lỗi fetch_page: {str(e)}")
            return None, str(e)
    
    def fetch_with_requests(self, url):
        """Lấy nội dung bằng requests"""
        try:
            # Thử kết nối với timeout
            response = self.session.get(url, timeout=30, allow_redirects=True)
            
            if response.status_code == 200:
                # Phát hiện encoding
                if response.encoding:
                    encoding = response.encoding
                else:
                    encoding = 'utf-8'
                
                return response.text, None
            elif response.status_code == 403:
                return None, "Lỗi 403: Trang web chặn truy cập. Cần sử dụng đăng nhập."
            elif response.status_code == 404:
                return None, "Lỗi 404: Không tìm thấy trang."
            else:
                return None, f"Lỗi HTTP {response.status_code}"
                
        except requests.exceptions.ConnectionError as e:
            return None, f"Lỗi kết nối: {str(e)}"
        except requests.exceptions.Timeout as e:
            return None, "Lỗi timeout: Quá thời gian chờ kết nối"
        except requests.exceptions.RequestException as e:
            return None, f"Lỗi request: {str(e)}"
        except Exception as e:
            return None, f"Lỗi không xác định: {str(e)}"
    
    def fetch_with_selenium(self, url, cookie_file=None):
        """Lấy nội dung bằng Selenium (cho trang có Cloudflare)"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            chrome_options = Options()
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            driver = webdriver.Chrome(options=chrome_options)
            
            # Load cookies nếu có
            if cookie_file and os.path.exists(cookie_file):
                import json
                driver.get(url)
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    for cookie in cookies:
                        try:
                            driver.add_cookie(cookie)
                        except:
                            pass
                driver.refresh()
            else:
                driver.get(url)
            
            # Đợi trang load
            time.sleep(5)
            
            # Đợi content load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass
            
            html_content = driver.page_source
            driver.quit()
            
            return html_content, None
            
        except ImportError:
            return None, "Chưa cài đặt selenium. Chạy: pip install selenium"
        except Exception as e:
            return None, f"Lỗi Selenium: {str(e)}"
    
    def test_toc_selector(self, html_content, selector, selector_type='css'):
        """Test selector cho mục lục"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            if selector_type == 'css':
                elements = soup.select(selector)
            else:  # xpath
                from lxml import html
                tree = html.fromstring(html_content)
                elements = tree.xpath(selector)
            
            results = []
            for i, elem in enumerate(elements[:10]):  # Lấy 10 kết quả đầu
                if selector_type == 'css':
                    href = elem.get('href', '')
                    text = elem.get_text().strip()
                else:
                    href = elem.get('href', '') if hasattr(elem, 'get') else ''
                    text = elem.text_content().strip() if hasattr(elem, 'text_content') else str(elem)
                
                # Lọc chỉ lấy các link chapter
                if 'chuong' in href.lower() or 'chapter' in href.lower() or 'chuong' in text.lower():
                    results.append({
                        'index': i + 1,
                        'text': text[:50] + '...' if len(text) > 50 else text,
                        'href': href,
                        'full_text': text
                    })
            
            return results, None
        except Exception as e:
            return None, str(e)
    
    def test_title_selector(self, html_content, selector, selector_type='css'):
        """Test selector cho tiêu đề"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            if selector_type == 'css':
                element = soup.select_one(selector)
            else:  # xpath
                from lxml import html
                tree = html.fromstring(html_content)
                elements = tree.xpath(selector)
                element = elements[0] if elements else None
            
            if element:
                if selector_type == 'css':
                    text = element.get_text().strip()
                else:
                    text = element.text_content().strip() if hasattr(element, 'text_content') else str(element)
                
                return {
                    'text': text,
                    'html': str(element)[:200] + '...' if len(str(element)) > 200 else str(element)
                }, None
            else:
                return None, "Không tìm thấy phần tử nào"
        except Exception as e:
            return None, str(e)
    
    def test_content_selector(self, html_content, selector, selector_type='css'):
        """Test selector cho nội dung"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            if selector_type == 'css':
                element = soup.select_one(selector)
            else:  # xpath
                from lxml import html
                tree = html.fromstring(html_content)
                elements = tree.xpath(selector)
                element = elements[0] if elements else None
            
            if element:
                # Xóa script, style
                for tag in element.find_all(['script', 'style']):
                    tag.decompose()
                
                if selector_type == 'css':
                    text = element.get_text().strip()
                    html_str = str(element)
                else:
                    text = element.text_content().strip() if hasattr(element, 'text_content') else str(element)
                    html_str = html.tostring(element, encoding='unicode') if hasattr(html, 'tostring') else str(element)
                
                return {
                    'text_length': len(text),
                    'text_preview': text[:500] + '...' if len(text) > 500 else text,
                    'html_length': len(html_str),
                    'paragraphs': len(element.find_all('p'))
                }, None
            else:
                return None, "Không tìm thấy phần tử nào"
        except Exception as e:
            return None, str(e)


class TruyenDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Truyện Downloader - Quản lý cấu hình và tải truyện")
        self.root.geometry("1200x800")
        
        # Khởi tạo các manager
        self.downloader = TruyenDownloader()
        self.config_manager = SiteConfigManager(self.downloader.storage_path)
        self.selector_tester = SelectorTester()
        
        self.current_story_info = None
        self.downloading = False
        self.current_chapters = []
        self.selected_chapters = []
        self.current_site = None
        self.current_config = None
        
        # Style
        self.setup_styles()
        
        # Tạo giao diện
        self.create_widgets()
        
        # Load dữ liệu
        self.load_sites_list()
        self.load_history()
        
        # Center window
        self.center_window()
    
    def setup_styles(self):
        """Cấu hình style cho giao diện"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Màu sắc
        style.configure('Header.TLabel', font=('Arial', 16, 'bold'), foreground='#2c3e50')
        style.configure('SubHeader.TLabel', font=('Arial', 12, 'bold'), foreground='#34495e')
        style.configure('Status.TLabel', font=('Arial', 10))
        style.configure('Success.TLabel', foreground='#27ae60')
        style.configure('Error.TLabel', foreground='#c0392b')
        style.configure('Warning.TLabel', foreground='#f39c12')
        
        # Buttons
        style.configure('Action.TButton', font=('Arial', 10), padding=5)
        style.configure('Download.TButton', font=('Arial', 10, 'bold'), 
                       background='#27ae60', foreground='white')
        style.configure('Stop.TButton', font=('Arial', 10, 'bold'),
                       background='#c0392b', foreground='white')
        
        # Notebook
        style.configure('TNotebook', background='#f0f0f0')
        style.configure('TNotebook.Tab', padding=[10, 5])
    
    def create_widgets(self):
        """Tạo các widget cho giao diện"""
        
        # Main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.create_header(main_container)
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Tab 1: Tải truyện
        self.download_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.download_tab, text="📥 Tải truyện")
        self.setup_download_tab()
        
        # Tab 2: Quản lý cấu hình
        self.config_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.config_tab, text="⚙️ Quản lý cấu hình")
        self.setup_config_tab()
        
        # Tab 3: Test Selector
        self.test_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.test_tab, text="🔍 Test Selector")
        self.setup_test_tab()
        
        # Tab 4: Lịch sử
        self.history_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.history_tab, text="📋 Lịch sử")
        self.setup_history_tab()
        
        # Status bar
        self.create_status_bar(main_container)
    
    def create_header(self, parent):
        """Tạo header"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(header_frame, text="📚 Truyện Downloader", 
                 style='Header.TLabel').pack(side=tk.LEFT)
        
        # URL input nhanh
        quick_url = ttk.Frame(header_frame)
        quick_url.pack(side=tk.RIGHT)
        
        ttk.Label(quick_url, text="URL:").pack(side=tk.LEFT, padx=(0, 5))
        self.quick_url_var = tk.StringVar()
        ttk.Entry(quick_url, textvariable=self.quick_url_var, width=40).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(quick_url, text="Phân tích nhanh", 
                  command=self.quick_analyze).pack(side=tk.LEFT)
    
    def create_status_bar(self, parent):
        """Tạo status bar"""
        status_frame = ttk.Frame(parent, relief=tk.SUNKEN, padding=(5, 2))
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        self.status_text = tk.StringVar(value="Sẵn sàng")
        ttk.Label(status_frame, textvariable=self.status_text).pack(side=tk.LEFT)
        
        self.progress_bar_small = ttk.Progressbar(status_frame, mode='indeterminate', length=100)
    
    def setup_download_tab(self):
        """Thiết lập tab tải truyện"""
        # Canvas cho scroll
        canvas = tk.Canvas(self.download_tab)
        scrollbar = ttk.Scrollbar(self.download_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # URL Input
        url_frame = ttk.LabelFrame(scrollable_frame, text="🌐 Nhập URL truyện", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        url_input = ttk.Frame(url_frame)
        url_input.pack(fill=tk.X)
        
        ttk.Label(url_input, text="URL:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.url_var = tk.StringVar()
        self.url_combo = ttk.Combobox(url_input, textvariable=self.url_var)
        self.url_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.url_combo.bind('<Return>', lambda e: self.analyze_url())
        
        ttk.Button(url_input, text="🔍 Phân tích", 
                  command=self.analyze_url).pack(side=tk.LEFT, padx=2)
        ttk.Button(url_input, text="🌐 Mở browser", 
                  command=lambda: webbrowser.open(self.url_var.get())).pack(side=tk.LEFT)
        
        # Thông tin truyện
        info_frame = ttk.LabelFrame(scrollable_frame, text="📖 Thông tin truyện", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X)
        
        # Tên truyện
        ttk.Label(info_grid, text="Tên truyện:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.story_name_var = tk.StringVar(value="Chưa xác định")
        ttk.Label(info_grid, textvariable=self.story_name_var).grid(row=0, column=1, sticky=tk.W, pady=2, padx=(10, 20))
        
        # Site
        ttk.Label(info_grid, text="Site:", font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky=tk.W, pady=2, padx=(20, 0))
        self.site_name_var = tk.StringVar(value="Chưa xác định")
        ttk.Label(info_grid, textvariable=self.site_name_var).grid(row=0, column=3, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Số chapter
        ttk.Label(info_grid, text="Số chapter:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.chapters_var = tk.StringVar(value="Chưa xác định")
        ttk.Label(info_grid, textvariable=self.chapters_var).grid(row=1, column=1, sticky=tk.W, pady=2, padx=(10, 20))
        
        # Cấu hình đang dùng
        ttk.Label(info_grid, text="Cấu hình:", font=('Arial', 10, 'bold')).grid(row=1, column=2, sticky=tk.W, pady=2, padx=(20, 0))
        self.config_used_var = tk.StringVar(value="Mặc định")
        ttk.Label(info_grid, textvariable=self.config_used_var).grid(row=1, column=3, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Cấu hình tải
        config_frame = ttk.LabelFrame(scrollable_frame, text="⚙️ Cấu hình tải", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        # Login option
        self.login_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(config_frame, text="🔐 Sử dụng đăng nhập (cho Cloudflare)", 
                       variable=self.login_var).pack(anchor=tk.W, pady=2)
        
        # Range download
        range_frame = ttk.Frame(config_frame)
        range_frame.pack(anchor=tk.W, pady=5)
        
        ttk.Label(range_frame, text="Tải từ chapter:").pack(side=tk.LEFT, padx=(0, 5))
        self.start_chapter_var = tk.StringVar(value="1")
        ttk.Entry(range_frame, textvariable=self.start_chapter_var, width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(range_frame, text="đến:").pack(side=tk.LEFT, padx=5)
        self.end_chapter_var = tk.StringVar(value="0")
        ttk.Entry(range_frame, textvariable=self.end_chapter_var, width=5).pack(side=tk.LEFT, padx=2)
        
        # Options
        options_frame = ttk.Frame(config_frame)
        options_frame.pack(anchor=tk.W, pady=5)
        
        self.retry_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="🔄 Tự động thử lại khi lỗi", 
                       variable=self.retry_var).pack(side=tk.LEFT, padx=5)
        
        self.combine_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="📑 Gộp thành một file", 
                       variable=self.combine_var).pack(side=tk.LEFT, padx=5)
        
        # Danh sách chapter
        chapter_frame = ttk.LabelFrame(scrollable_frame, text="📑 Danh sách chapter", padding="10")
        chapter_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5)
        
        # Control buttons
        control_frame = ttk.Frame(chapter_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(control_frame, text="✓ Chọn tất cả", 
                  command=self.select_all_chapters).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="⬜ Bỏ chọn", 
                  command=self.deselect_all_chapters).pack(side=tk.LEFT, padx=2)
        ttk.Label(control_frame, text="(Click vào ô checkbox để chọn/bỏ chọn)").pack(side=tk.LEFT, padx=10)
        
        # Treeview for chapters
        tree_frame = ttk.Frame(chapter_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        self.chapter_tree = ttk.Treeview(tree_frame, 
                                        columns=('select', 'number', 'title', 'url'),
                                        show='headings',
                                        yscrollcommand=tree_scroll_y.set,
                                        xscrollcommand=tree_scroll_x.set,
                                        height=12)
        
        self.chapter_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure columns
        self.chapter_tree.column('select', width=40, anchor='center')
        self.chapter_tree.column('number', width=60, anchor='center')
        self.chapter_tree.column('title', width=300)
        self.chapter_tree.column('url', width=400)
        
        self.chapter_tree.heading('select', text='✓')
        self.chapter_tree.heading('number', text='Số')
        self.chapter_tree.heading('title', text='Tiêu đề')
        self.chapter_tree.heading('url', text='URL')
        
        # Bind click event
        self.chapter_tree.bind('<ButtonRelease-1>', self.on_chapter_click)
        
        # Configure scrollbars
        tree_scroll_y.config(command=self.chapter_tree.yview)
        tree_scroll_x.config(command=self.chapter_tree.xview)
        
        # Progress area
        progress_frame = ttk.LabelFrame(scrollable_frame, text="📊 Tiến trình tải", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_label = ttk.Label(progress_frame, text="Chưa bắt đầu tải")
        self.progress_label.pack()
        
        # Log area
        log_frame = ttk.LabelFrame(scrollable_frame, text="📝 Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5)
        
        log_control = ttk.Frame(log_frame)
        log_control.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(log_control, text="🗑️ Xóa log", 
                  command=self.clear_log).pack(side=tk.RIGHT)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD,
                                                  font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure log tags
        self.log_text.tag_config('error', foreground='#c0392b')
        self.log_text.tag_config('success', foreground='#27ae60')
        self.log_text.tag_config('warning', foreground='#f39c12')
        self.log_text.tag_config('info', foreground='#2980b9')
        
        # Download buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.download_btn = ttk.Button(button_frame, text="⬇️ Tải truyện", 
                                       command=self.start_download, style='Download.TButton',
                                       width=15)
        self.download_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹️ Dừng tải", 
                                   command=self.stop_download, style='Stop.TButton',
                                   width=15, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(button_frame, text="🔑 Đăng nhập", 
                  command=self.login_to_site).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(button_frame, text="📂 Mở thư mục tải", 
                  command=self.open_download_folder).pack(side=tk.RIGHT, padx=2)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_config_tab(self):
        """Thiết lập tab quản lý cấu hình"""
        # Main frame
        main_frame = ttk.Frame(self.config_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Sites list
        left_panel = ttk.LabelFrame(main_frame, text="📌 Danh sách Sites", padding="10")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Treeview for sites
        tree_frame = ttk.Frame(left_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.site_tree = ttk.Treeview(tree_frame, columns=('domain', 'status'),
                                      show='tree headings', height=15,
                                      yscrollcommand=tree_scroll.set)
        self.site_tree.pack(fill=tk.BOTH, expand=True)
        
        self.site_tree.heading('#0', text='Tên site')
        self.site_tree.heading('domain', text='Domain')
        self.site_tree.heading('status', text='Trạng thái')
        
        self.site_tree.column('#0', width=120)
        self.site_tree.column('domain', width=150)
        self.site_tree.column('status', width=80)
        
        tree_scroll.config(command=self.site_tree.yview)
        
        # Bind selection event
        self.site_tree.bind('<<TreeviewSelect>>', self.on_site_select)
        
        # Buttons for site management
        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="➕ Thêm site", 
                  command=self.add_site).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✏️ Sửa", 
                  command=self.edit_site).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="❌ Xóa", 
                  command=self.delete_site).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🔄 Làm mới", 
                  command=self.load_sites_list).pack(side=tk.LEFT, padx=2)
        
        # Right panel - Config editor
        right_panel = ttk.LabelFrame(main_frame, text="⚙️ Chi tiết cấu hình", padding="10")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Site info
        info_frame = ttk.Frame(right_panel)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text="Tên site:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.edit_site_name = ttk.Entry(info_frame, width=20)
        self.edit_site_name.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(info_frame, text="Domain:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.edit_domain = ttk.Entry(info_frame, width=30)
        self.edit_domain.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Selectors
        selector_frame = ttk.LabelFrame(right_panel, text="Selector cho các thành phần", padding="10")
        selector_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title selector
        ttk.Label(selector_frame, text="Tiêu đề (Title):", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        title_type_frame = ttk.Frame(selector_frame)
        title_type_frame.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        self.title_type = tk.StringVar(value="css")
        ttk.Radiobutton(title_type_frame, text="CSS", variable=self.title_type, 
                       value="css").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(title_type_frame, text="XPath", variable=self.title_type, 
                       value="xpath").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(title_type_frame, text="JavaScript", variable=self.title_type, 
                       value="js").pack(side=tk.LEFT, padx=2)
        
        self.title_selector = ttk.Entry(selector_frame, width=50)
        self.title_selector.grid(row=1, column=0, columnspan=2, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Content selector
        ttk.Label(selector_frame, text="Nội dung (Content):", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        content_type_frame = ttk.Frame(selector_frame)
        content_type_frame.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        self.content_type = tk.StringVar(value="css")
        ttk.Radiobutton(content_type_frame, text="CSS", variable=self.content_type, 
                       value="css").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(content_type_frame, text="XPath", variable=self.content_type, 
                       value="xpath").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(content_type_frame, text="JavaScript", variable=self.content_type, 
                       value="js").pack(side=tk.LEFT, padx=2)
        
        self.content_selector = ttk.Entry(selector_frame, width=50)
        self.content_selector.grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # TOC selector
        ttk.Label(selector_frame, text="Mục lục (TOC):", font=('Arial', 9, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=5)
        
        toc_type_frame = ttk.Frame(selector_frame)
        toc_type_frame.grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)
        
        self.toc_type = tk.StringVar(value="css")
        ttk.Radiobutton(toc_type_frame, text="CSS", variable=self.toc_type, 
                       value="css").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(toc_type_frame, text="XPath", variable=self.toc_type, 
                       value="xpath").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(toc_type_frame, text="JavaScript", variable=self.toc_type, 
                       value="js").pack(side=tk.LEFT, padx=2)
        
        self.toc_selector = ttk.Entry(selector_frame, width=50)
        self.toc_selector.grid(row=5, column=0, columnspan=2, sticky=tk.W+tk.E, pady=2, padx=5)
        
        # Advanced options
        advanced_frame = ttk.LabelFrame(right_panel, text="Tùy chọn nâng cao", padding="10")
        advanced_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.needs_login = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="Yêu cầu đăng nhập", 
                       variable=self.needs_login).pack(anchor=tk.W)
        
        self.use_selenium = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Sử dụng Selenium (cho Cloudflare)", 
                       variable=self.use_selenium).pack(anchor=tk.W)
        
        encoding_frame = ttk.Frame(advanced_frame)
        encoding_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(encoding_frame, text="Encoding:").pack(side=tk.LEFT, padx=(0, 5))
        self.encoding = ttk.Combobox(encoding_frame, values=['utf-8', 'gbk', 'gb2312', 'big5'], width=10)
        self.encoding.pack(side=tk.LEFT)
        self.encoding.set('utf-8')
        
        # Save button
        ttk.Button(right_panel, text="💾 Lưu cấu hình", 
                  command=self.save_site_config, style='Download.TButton').pack(pady=10)
    
    def setup_test_tab(self):
        """Thiết lập tab test selector"""
        # Main frame
        main_frame = ttk.Frame(self.test_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # URL input
        url_frame = ttk.LabelFrame(main_frame, text="🌐 URL cần test", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        url_input = ttk.Frame(url_frame)
        url_input.pack(fill=tk.X)
        
        ttk.Label(url_input, text="URL:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.test_url_var = tk.StringVar()
        self.test_url_var.trace('w', lambda *args: self.auto_detect_site())
        ttk.Entry(url_input, textvariable=self.test_url_var, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Site selection
        site_frame = ttk.Frame(url_frame)
        site_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(site_frame, text="Site:").pack(side=tk.LEFT, padx=(0, 5))
        self.test_site_var = tk.StringVar()
        self.test_site_combo = ttk.Combobox(site_frame, textvariable=self.test_site_var, width=20)
        self.test_site_combo.pack(side=tk.LEFT, padx=5)
        self.test_site_combo.bind('<<ComboboxSelected>>', self.load_site_selectors)
        
        ttk.Button(site_frame, text="Tải cấu hình", 
                  command=self.load_site_selectors).pack(side=tk.LEFT, padx=5)
        
        # Options
        options_frame = ttk.Frame(url_frame)
        options_frame.pack(fill=tk.X, pady=5)
        
        self.test_use_selenium = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Sử dụng Selenium (vượt Cloudflare)", 
                       variable=self.test_use_selenium).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(options_frame, text="🌐 Mở trong browser", 
                  command=lambda: webbrowser.open(self.test_url_var.get())).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(options_frame, text="🔄 Lấy HTML", 
                  command=self.fetch_test_page).pack(side=tk.RIGHT, padx=5)
        
        # Notebook for different tests
        test_notebook = ttk.Notebook(main_frame)
        test_notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Tab TOC test
        toc_test_frame = ttk.Frame(test_notebook)
        test_notebook.add(toc_test_frame, text="📑 Test Mục lục (TOC)")
        self.setup_toc_test(toc_test_frame)
        
        # Tab Title test
        title_test_frame = ttk.Frame(test_notebook)
        test_notebook.add(title_test_frame, text="📌 Test Tiêu đề")
        self.setup_title_test(title_test_frame)
        
        # Tab Content test
        content_test_frame = ttk.Frame(test_notebook)
        test_notebook.add(content_test_frame, text="📄 Test Nội dung")
        self.setup_content_test(content_test_frame)
        
        # Tab Auto detect
        auto_test_frame = ttk.Frame(test_notebook)
        test_notebook.add(auto_test_frame, text="🔍 Tự động phát hiện")
        self.setup_auto_detect(auto_test_frame)
        
        # Store HTML content for testing
        self.test_html_content = None
    
    def setup_toc_test(self, parent):
        """Thiết lập test mục lục"""
        # Selector input
        selector_frame = ttk.Frame(parent, padding="10")
        selector_frame.pack(fill=tk.X)
        
        ttk.Label(selector_frame, text="Selector TOC:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.toc_test_selector = ttk.Entry(selector_frame, width=50)
        self.toc_test_selector.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Type
        self.toc_test_type = tk.StringVar(value="css")
        ttk.Radiobutton(selector_frame, text="CSS", variable=self.toc_test_type, 
                       value="css").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(selector_frame, text="XPath", variable=self.toc_test_type, 
                       value="xpath").pack(side=tk.LEFT, padx=2)
        
        ttk.Button(selector_frame, text="Test TOC", 
                  command=self.test_toc_selector).pack(side=tk.LEFT, padx=5)
        
        # Results
        result_frame = ttk.LabelFrame(parent, text="Kết quả", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.toc_result = scrolledtext.ScrolledText(result_frame, height=15, wrap=tk.WORD,
                                                    font=('Consolas', 9))
        self.toc_result.pack(fill=tk.BOTH, expand=True)
        
        # Apply button
        ttk.Button(parent, text="📋 Áp dụng cho cấu hình", 
                  command=self.apply_toc_to_config).pack(pady=5)
    
    def setup_title_test(self, parent):
        """Thiết lập test tiêu đề"""
        # Selector input
        selector_frame = ttk.Frame(parent, padding="10")
        selector_frame.pack(fill=tk.X)
        
        ttk.Label(selector_frame, text="Selector Title:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.title_test_selector = ttk.Entry(selector_frame, width=50)
        self.title_test_selector.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Type
        self.title_test_type = tk.StringVar(value="css")
        ttk.Radiobutton(selector_frame, text="CSS", variable=self.title_test_type, 
                       value="css").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(selector_frame, text="XPath", variable=self.title_test_type, 
                       value="xpath").pack(side=tk.LEFT, padx=2)
        
        ttk.Button(selector_frame, text="Test Title", 
                  command=self.test_title_selector).pack(side=tk.LEFT, padx=5)
        
        # Results
        result_frame = ttk.LabelFrame(parent, text="Kết quả", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.title_result = scrolledtext.ScrolledText(result_frame, height=15, wrap=tk.WORD,
                                                      font=('Consolas', 9))
        self.title_result.pack(fill=tk.BOTH, expand=True)
        
        # Apply button
        ttk.Button(parent, text="📋 Áp dụng cho cấu hình", 
                  command=self.apply_title_to_config).pack(pady=5)
    
    def setup_content_test(self, parent):
        """Thiết lập test nội dung"""
        # Selector input
        selector_frame = ttk.Frame(parent, padding="10")
        selector_frame.pack(fill=tk.X)
        
        ttk.Label(selector_frame, text="Selector Content:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.content_test_selector = ttk.Entry(selector_frame, width=50)
        self.content_test_selector.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Type
        self.content_test_type = tk.StringVar(value="css")
        ttk.Radiobutton(selector_frame, text="CSS", variable=self.content_test_type, 
                       value="css").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(selector_frame, text="XPath", variable=self.content_test_type, 
                       value="xpath").pack(side=tk.LEFT, padx=2)
        
        ttk.Button(selector_frame, text="Test Content", 
                  command=self.test_content_selector).pack(side=tk.LEFT, padx=5)
        
        # Results
        result_frame = ttk.LabelFrame(parent, text="Kết quả", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.content_result = scrolledtext.ScrolledText(result_frame, height=15, wrap=tk.WORD,
                                                        font=('Consolas', 9))
        self.content_result.pack(fill=tk.BOTH, expand=True)
        
        # Apply button
        ttk.Button(parent, text="📋 Áp dụng cho cấu hình", 
                  command=self.apply_content_to_config).pack(pady=5)
    
    def setup_auto_detect(self, parent):
        """Thiết lập tự động phát hiện"""
        # Info
        info_frame = ttk.Frame(parent, padding="10")
        info_frame.pack(fill=tk.X)
        
        ttk.Label(info_frame, text="Tự động phân tích trang web và đề xuất selectors",
                 font=('Arial', 10)).pack()
        
        # Buttons
        btn_frame = ttk.Frame(parent, padding="10")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="🔍 Phát hiện selectors", 
                  command=self.auto_detect_selectors,
                  style='Download.TButton').pack(pady=5)
        
        # Results
        result_frame = ttk.LabelFrame(parent, text="Kết quả phát hiện", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.auto_result = scrolledtext.ScrolledText(result_frame, height=20, wrap=tk.WORD,
                                                     font=('Consolas', 9))
        self.auto_result.pack(fill=tk.BOTH, expand=True)
    
    def setup_history_tab(self):
        """Thiết lập tab lịch sử"""
        # Main frame
        main_frame = ttk.Frame(self.history_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for history
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.history_tree = ttk.Treeview(tree_frame, 
                                         columns=('name', 'chapters', 'date', 'file'),
                                         show='headings',
                                         yscrollcommand=tree_scroll_y.set,
                                         xscrollcommand=tree_scroll_x.set)
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        
        self.history_tree.heading('name', text='Tên truyện')
        self.history_tree.heading('chapters', text='Số chapter')
        self.history_tree.heading('date', text='Ngày tải')
        self.history_tree.heading('file', text='File')
        
        self.history_tree.column('name', width=250)
        self.history_tree.column('chapters', width=80, anchor='center')
        self.history_tree.column('date', width=150)
        self.history_tree.column('file', width=350)
        
        tree_scroll_y.config(command=self.history_tree.yview)
        tree_scroll_x.config(command=self.history_tree.xview)
        
        # Bind double click
        self.history_tree.bind('<Double-Button-1>', self.open_history_file)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="🔄 Làm mới", 
                  command=self.load_history).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📂 Mở file", 
                  command=self.open_selected_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑️ Xóa lịch sử", 
                  command=self.clear_history).pack(side=tk.RIGHT, padx=2)
    
    def center_window(self):
        """Đưa cửa sổ ra giữa màn hình"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def load_sites_list(self):
        """Load danh sách sites vào tree"""
        # Clear tree
        for item in self.site_tree.get_children():
            self.site_tree.delete(item)
        
        # Update site combo in test tab
        sites = list(self.config_manager.configs.keys())
        self.test_site_combo['values'] = sites
        
        # Add sites to tree
        for site_name, config in self.config_manager.configs.items():
            status = "✓ Active" if config.get('needs_login', False) else "○ Basic"
            self.site_tree.insert('', 'end', text=site_name, 
                                 values=(config.get('domain', ''), status))
    
    def on_site_select(self, event):
        """Xử lý khi chọn site trong tree"""
        selected = self.site_tree.selection()
        if not selected:
            return
        
        site_name = self.site_tree.item(selected[0], 'text')
        config = self.config_manager.get_site_config(site_name)
        
        # Load vào form
        self.edit_site_name.delete(0, tk.END)
        self.edit_site_name.insert(0, site_name)
        
        self.edit_domain.delete(0, tk.END)
        self.edit_domain.insert(0, config.get('domain', ''))
        
        # Load selectors
        selectors = config.get('selectors', {})
        
        # Title
        title_config = selectors.get('title', {})
        self.title_type.set(title_config.get('type', 'css'))
        self.title_selector.delete(0, tk.END)
        self.title_selector.insert(0, title_config.get('script', ''))
        
        # Content
        content_config = selectors.get('content', {})
        self.content_type.set(content_config.get('type', 'css'))
        self.content_selector.delete(0, tk.END)
        self.content_selector.insert(0, content_config.get('script', ''))
        
        # TOC
        toc_config = selectors.get('toc', {})
        self.toc_type.set(toc_config.get('type', 'css'))
        self.toc_selector.delete(0, tk.END)
        self.toc_selector.insert(0, toc_config.get('script', ''))
        
        # Options
        self.needs_login.set(config.get('needs_login', True))
        self.use_selenium.set(config.get('use_selenium', False))
        self.encoding.set(config.get('encoding', 'utf-8'))
    
    def save_site_config(self):
        """Lưu cấu hình site"""
        site_name = self.edit_site_name.get().strip()
        if not site_name:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên site")
            return
        
        config = {
            "domain": self.edit_domain.get().strip(),
            "name": site_name,
            "selectors": {
                "title": {
                    "type": self.title_type.get(),
                    "script": self.title_selector.get().strip()
                },
                "content": {
                    "type": self.content_type.get(),
                    "script": self.content_selector.get().strip()
                },
                "toc": {
                    "type": self.toc_type.get(),
                    "script": self.toc_selector.get().strip()
                }
            },
            "needs_login": self.needs_login.get(),
            "use_selenium": self.use_selenium.get(),
            "encoding": self.encoding.get(),
            "toc_page": "/doc-truyen/{story_slug}/",
            "chapter_pattern": "/doc-truyen/{story_slug}/chuong-{chapter_number}"
        }
        
        self.config_manager.update_site_config(site_name, config)
        self.load_sites_list()
        messagebox.showinfo("Thành công", f"Đã lưu cấu hình cho site {site_name}")
    
    def add_site(self):
        """Thêm site mới"""
        # Clear form
        self.edit_site_name.delete(0, tk.END)
        self.edit_domain.delete(0, tk.END)
        self.title_selector.delete(0, tk.END)
        self.content_selector.delete(0, tk.END)
        self.toc_selector.delete(0, tk.END)
        
        # Set defaults
        self.title_type.set("css")
        self.content_type.set("css")
        self.toc_type.set("css")
        self.needs_login.set(True)
        self.use_selenium.set(False)
        self.encoding.set("utf-8")
        
        # Focus on name
        self.edit_site_name.focus()
    
    def edit_site(self):
        """Sửa site - đã có khi chọn từ tree"""
        pass
    
    def delete_site(self):
        """Xóa site"""
        selected = self.site_tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn site cần xóa")
            return
        
        site_name = self.site_tree.item(selected[0], 'text')
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa site {site_name}?"):
            self.config_manager.delete_site_config(site_name)
            self.load_sites_list()
            messagebox.showinfo("Thành công", f"Đã xóa site {site_name}")
    
    def auto_detect_site(self):
        """Tự động phát hiện site từ URL"""
        url = self.test_url_var.get().strip()
        if url:
            site_name, config = self.config_manager.get_site_by_url(url)
            if site_name:
                self.test_site_var.set(site_name)
                self.load_site_selectors()
    
    def load_site_selectors(self, event=None):
        """Load selectors của site được chọn"""
        site_name = self.test_site_var.get()
        if site_name:
            config = self.config_manager.get_site_config(site_name)
            selectors = config.get('selectors', {})
            
            # Load vào các ô test
            title_config = selectors.get('title', {})
            self.title_test_selector.delete(0, tk.END)
            self.title_test_selector.insert(0, title_config.get('script', ''))
            self.title_test_type.set(title_config.get('type', 'css'))
            
            content_config = selectors.get('content', {})
            self.content_test_selector.delete(0, tk.END)
            self.content_test_selector.insert(0, content_config.get('script', ''))
            self.content_test_type.set(content_config.get('type', 'css'))
            
            toc_config = selectors.get('toc', {})
            self.toc_test_selector.delete(0, tk.END)
            self.toc_test_selector.insert(0, toc_config.get('script', ''))
            self.toc_test_type.set(toc_config.get('type', 'css'))
    
    def fetch_test_page(self):
        """Lấy HTML trang để test"""
        url = self.test_url_var.get().strip()
        if not url:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập URL")
            return
        
        self.status_text.set("Đang tải trang...")
        self.progress_bar_small.start()
        
        def fetch():
            # Xác định site để lấy cookie nếu cần
            site_name, config = self.config_manager.get_site_by_url(url)
            cookie_file = None
            use_selenium = self.test_use_selenium.get()
            
            if site_name and config and config.get('needs_login'):
                cookie_file = os.path.join(self.downloader.storage_path, 'cookies', f'{site_name}.json')
            
            html_content, error = self.selector_tester.fetch_page(url, use_selenium, cookie_file)
            
            self.root.after(0, lambda: self.process_fetched_page(html_content, error))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def process_fetched_page(self, html_content, error):
        """Xử lý kết quả fetch page"""
        self.progress_bar_small.stop()
        
        if error:
            self.status_text.set("Lỗi khi tải trang")
            messagebox.showerror("Lỗi", f"Không thể tải trang:\n{error}")
            return
        
        if html_content:
            self.test_html_content = html_content
            self.status_text.set("Đã tải trang thành công")
            messagebox.showinfo("Thành công", "Đã tải nội dung trang. Có thể test selector now.")
        else:
            self.status_text.set("Lỗi không xác định")
    
    def test_toc_selector(self):
        """Test TOC selector"""
        if not self.test_html_content:
            messagebox.showwarning("Cảnh báo", "Vui lòng tải trang trước")
            return
        
        selector = self.toc_test_selector.get().strip()
        selector_type = self.toc_test_type.get()
        
        if not selector:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập selector")
            return
        
        self.toc_result.delete(1.0, tk.END)
        self.toc_result.insert(tk.END, f"Đang test TOC selector: {selector}\n")
        self.toc_result.insert(tk.END, f"Loại: {selector_type}\n")
        self.toc_result.insert(tk.END, "-" * 50 + "\n\n")
        
        results, error = self.selector_tester.test_toc_selector(self.test_html_content, selector, selector_type)
        
        if error:
            self.toc_result.insert(tk.END, f"❌ Lỗi: {error}\n")
        elif results:
            self.toc_result.insert(tk.END, f"✅ Tìm thấy {len(results)} chapter\n\n")
            for r in results:
                self.toc_result.insert(tk.END, f"#{r['index']}: {r['text']}\n")
                self.toc_result.insert(tk.END, f"   URL: {r['href']}\n\n")
        else:
            self.toc_result.insert(tk.END, "❌ Không tìm thấy chapter nào\n")
    
    def test_title_selector(self):
        """Test Title selector"""
        if not self.test_html_content:
            messagebox.showwarning("Cảnh báo", "Vui lòng tải trang trước")
            return
        
        selector = self.title_test_selector.get().strip()
        selector_type = self.title_test_type.get()
        
        if not selector:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập selector")
            return
        
        self.title_result.delete(1.0, tk.END)
        self.title_result.insert(tk.END, f"Đang test Title selector: {selector}\n")
        self.title_result.insert(tk.END, f"Loại: {selector_type}\n")
        self.title_result.insert(tk.END, "-" * 50 + "\n\n")
        
        result, error = self.selector_tester.test_title_selector(self.test_html_content, selector, selector_type)
        
        if error:
            self.title_result.insert(tk.END, f"❌ Lỗi: {error}\n")
        elif result:
            self.title_result.insert(tk.END, f"✅ Tiêu đề tìm thấy:\n\n")
            self.title_result.insert(tk.END, f"Text: {result['text']}\n\n")
            self.title_result.insert(tk.END, f"HTML: {result['html']}\n")
        else:
            self.title_result.insert(tk.END, "❌ Không tìm thấy tiêu đề\n")
    
    def test_content_selector(self):
        """Test Content selector"""
        if not self.test_html_content:
            messagebox.showwarning("Cảnh báo", "Vui lòng tải trang trước")
            return
        
        selector = self.content_test_selector.get().strip()
        selector_type = self.content_test_type.get()
        
        if not selector:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập selector")
            return
        
        self.content_result.delete(1.0, tk.END)
        self.content_result.insert(tk.END, f"Đang test Content selector: {selector}\n")
        self.content_result.insert(tk.END, f"Loại: {selector_type}\n")
        self.content_result.insert(tk.END, "-" * 50 + "\n\n")
        
        result, error = self.selector_tester.test_content_selector(self.test_html_content, selector, selector_type)
        
        if error:
            self.content_result.insert(tk.END, f"❌ Lỗi: {error}\n")
        elif result:
            self.content_result.insert(tk.END, f"✅ Tìm thấy nội dung:\n\n")
            self.content_result.insert(tk.END, f"Độ dài text: {result['text_length']} ký tự\n")
            self.content_result.insert(tk.END, f"Số đoạn văn: {result['paragraphs']}\n\n")
            self.content_result.insert(tk.END, f"Preview:\n{result['text_preview']}\n")
        else:
            self.content_result.insert(tk.END, "❌ Không tìm thấy nội dung\n")
    
    def auto_detect_selectors(self):
        """Tự động phát hiện selectors"""
        if not self.test_html_content:
            messagebox.showwarning("Cảnh báo", "Vui lòng tải trang trước")
            return
        
        self.auto_result.delete(1.0, tk.END)
        self.auto_result.insert(tk.END, "Đang phân tích tự động...\n\n")
        
        soup = BeautifulSoup(self.test_html_content, 'html.parser')
        
        # Phát hiện TOC selectors
        self.auto_result.insert(tk.END, "📑 MỤC LỤC (TOC):\n")
        self.auto_result.insert(tk.END, "-" * 40 + "\n")
        
        toc_candidates = []
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            text = a.get_text().strip()
            if ('chuong' in href.lower() or 'chapter' in href.lower() or 
                'chuong' in text.lower() or 'chapter' in text.lower()):
                
                # Tìm parent container
                parent = a.find_parent(['div', 'ul', 'ol'])
                if parent and parent.get('class'):
                    class_str = '.'.join(parent.get('class', []))
                    selector = f"{parent.name}.{class_str} a"
                    if selector not in toc_candidates:
                        toc_candidates.append(selector)
                        self.auto_result.insert(tk.END, f"• {selector}\n")
        
        # Phát hiện Title selectors
        self.auto_result.insert(tk.END, "\n📌 TIÊU ĐỀ:\n")
        self.auto_result.insert(tk.END, "-" * 40 + "\n")
        
        title_candidates = []
        for h1 in soup.find_all(['h1', 'h2', 'h3']):
            if h1.get('class'):
                class_str = '.'.join(h1.get('class', []))
                selector = f"{h1.name}.{class_str}"
                title_candidates.append(selector)
                self.auto_result.insert(tk.END, f"• {selector}: {h1.get_text()[:50]}...\n")
        
        # Phát hiện Content selectors
        self.auto_result.insert(tk.END, "\n📄 NỘI DUNG:\n")
        self.auto_result.insert(tk.END, "-" * 40 + "\n")
        
        content_candidates = []
        for div in soup.find_all('div'):
            text_len = len(div.get_text())
            if text_len > 500 and div.get('class'):
                class_str = '.'.join(div.get('class', []))
                selector = f"div.{class_str}"
                content_candidates.append(selector)
                self.auto_result.insert(tk.END, f"• {selector} ({text_len} ký tự)\n")
        
        self.auto_result.insert(tk.END, "\n" + "=" * 50 + "\n")
        self.auto_result.insert(tk.END, "Có thể sử dụng các selector trên để cấu hình.\n")
        self.auto_result.insert(tk.END, "Test từng selector trong các tab tương ứng.\n")
    
    def apply_toc_to_config(self):
        """Áp dụng TOC selector vào cấu hình"""
        site_name = self.test_site_var.get()
        if not site_name:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn site")
            return
        
        selector = self.toc_test_selector.get().strip()
        selector_type = self.toc_test_type.get()
        
        if not selector:
            return
        
        config = self.config_manager.get_site_config(site_name)
        if 'selectors' not in config:
            config['selectors'] = {}
        
        config['selectors']['toc'] = {
            'type': selector_type,
            'script': selector
        }
        
        self.config_manager.update_site_config(site_name, config)
        messagebox.showinfo("Thành công", "Đã cập nhật TOC selector")
        
        # Cập nhật form
        self.on_site_select(None)
    
    def apply_title_to_config(self):
        """Áp dụng Title selector vào cấu hình"""
        site_name = self.test_site_var.get()
        if not site_name:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn site")
            return
        
        selector = self.title_test_selector.get().strip()
        selector_type = self.title_test_type.get()
        
        if not selector:
            return
        
        config = self.config_manager.get_site_config(site_name)
        if 'selectors' not in config:
            config['selectors'] = {}
        
        config['selectors']['title'] = {
            'type': selector_type,
            'script': selector
        }
        
        self.config_manager.update_site_config(site_name, config)
        messagebox.showinfo("Thành công", "Đã cập nhật Title selector")
        
        # Cập nhật form
        self.on_site_select(None)
    
    def apply_content_to_config(self):
        """Áp dụng Content selector vào cấu hình"""
        site_name = self.test_site_var.get()
        if not site_name:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn site")
            return
        
        selector = self.content_test_selector.get().strip()
        selector_type = self.content_test_type.get()
        
        if not selector:
            return
        
        config = self.config_manager.get_site_config(site_name)
        if 'selectors' not in config:
            config['selectors'] = {}
        
        config['selectors']['content'] = {
            'type': selector_type,
            'script': selector
        }
        
        self.config_manager.update_site_config(site_name, config)
        messagebox.showinfo("Thành công", "Đã cập nhật Content selector")
        
        # Cập nhật form
        self.on_site_select(None)
    
    def quick_analyze(self):
        """Phân tích nhanh từ URL"""
        url = self.quick_url_var.get().strip()
        if url:
            self.url_var.set(url)
            self.analyze_url()
    
    def analyze_url(self):
        """Phân tích URL để lấy thông tin truyện"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập URL")
            return
        
        self.log("Đang phân tích URL...", 'info')
        self.status_text.set("Đang phân tích...")
        
        def analyze():
            try:
                # Xác định site
                site_name, config = self.config_manager.get_site_by_url(url)
                if site_name:
                    self.current_site = site_name
                    self.current_config = config
                    self.site_name_var.set(config.get('name', site_name))
                    self.config_used_var.set(site_name)
                
                story_info = self.downloader.extract_story_info(url)
                if story_info:
                    self.current_story_info = story_info
                    self.story_name_var.set(story_info['story_name'])
                    
                    # Thêm URL vào history
                    current_urls = list(self.url_combo['values'])
                    if url not in current_urls:
                        self.url_combo['values'] = [url] + list(current_urls)[:9]
                    
                    # Lấy mục lục
                    if config:
                        toc_url = story_info['base_url'] + config.get('toc_page', '').format(story_slug=story_info['story_slug'])
                        
                        # Kiểm tra đăng nhập
                        use_selenium = config.get('use_selenium', False)
                        cookie_file = None
                        if config.get('needs_login'):
                            cookie_file = os.path.join(self.downloader.storage_path, 'cookies', f'{site_name}.json')
                        
                        html_content, error = self.selector_tester.fetch_page(toc_url, use_selenium, cookie_file)
                        
                        if error:
                            self.log(f"Lỗi khi lấy mục lục: {error}", 'error')
                        else:
                            # Test TOC selector
                            toc_selector = config['selectors']['toc']['script']
                            toc_type = config['selectors']['toc']['type']
                            
                            chapters, error = self.selector_tester.test_toc_selector(html_content, toc_selector, toc_type)
                            
                            if chapters:
                                self.current_chapters = [ch['href'] for ch in chapters]
                                self.chapters_var.set(str(len(chapters)))
                                self.display_chapters(chapters)
                                self.log(f"✓ Tìm thấy {len(chapters)} chapter", 'success')
                            else:
                                self.log("Không tìm thấy chapter nào", 'warning')
                    else:
                        self.log("Không tìm thấy cấu hình cho site này", 'warning')
                    
                    self.log(f"✓ Đã phân tích: {story_info['story_name']}", 'success')
                else:
                    self.log("✗ Không thể phân tích URL", 'error')
                    
            except Exception as e:
                self.log(f"✗ Lỗi: {str(e)}", 'error')
                import traceback
                traceback.print_exc()
            finally:
                self.status_text.set("Sẵn sàng")
        
        threading.Thread(target=analyze, daemon=True).start()
    
    def display_chapters(self, chapters):
        """Hiển thị danh sách chapter"""
        # Clear tree
        for item in self.chapter_tree.get_children():
            self.chapter_tree.delete(item)
        
        # Add chapters
        for i, ch in enumerate(chapters, 1):
            self.chapter_tree.insert('', 'end', values=('☐', str(i), ch['text'], ch['href']))
    
    def on_chapter_click(self, event):
        """Xử lý click vào chapter tree"""
        region = self.chapter_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.chapter_tree.identify_column(event.x)
            if column == '#1':  # Select column
                item = self.chapter_tree.identify_row(event.y)
                values = list(self.chapter_tree.item(item, 'values'))
                if values[0] == '☐':
                    values[0] = '✓'
                else:
                    values[0] = '☐'
                self.chapter_tree.item(item, values=values)
    
    def select_all_chapters(self):
        """Chọn tất cả chapters"""
        for item in self.chapter_tree.get_children():
            values = list(self.chapter_tree.item(item, 'values'))
            values[0] = '✓'
            self.chapter_tree.item(item, values=values)
    
    def deselect_all_chapters(self):
        """Bỏ chọn tất cả chapters"""
        for item in self.chapter_tree.get_children():
            values = list(self.chapter_tree.item(item, 'values'))
            values[0] = '☐'
            self.chapter_tree.item(item, values=values)
    
    def get_selected_chapters(self):
        """Lấy danh sách chapter được chọn"""
        selected = []
        for item in self.chapter_tree.get_children():
            values = self.chapter_tree.item(item, 'values')
            if values[0] == '✓':
                selected.append({
                    'number': values[1],
                    'title': values[2],
                    'url': values[3]
                })
        return selected
    
    def start_download(self):
        """Bắt đầu tải truyện"""
        if not self.current_story_info:
            messagebox.showwarning("Cảnh báo", "Vui lòng phân tích URL trước")
            return
        
        if self.downloading:
            messagebox.showwarning("Cảnh báo", "Đang trong quá trình tải")
            return
        
        # Get selected chapters
        selected = self.get_selected_chapters()
        if not selected:
            # If none selected, download all
            for item in self.chapter_tree.get_children():
                values = self.chapter_tree.item(item, 'values')
                selected.append({
                    'number': values[1],
                    'title': values[2],
                    'url': values[3]
                })
        
        if not selected:
            messagebox.showwarning("Cảnh báo", "Không có chapter nào để tải")
            return
        
        self.downloading = True
        self.download_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_text.set("Đang tải...")
        
        def download():
            try:
                url = self.url_var.get().strip()
                use_login = self.login_var.get() or (self.current_config and self.current_config.get('needs_login', False))
                
                # Get range
                try:
                    start = int(self.start_chapter_var.get())
                    end = int(self.end_chapter_var.get()) if self.end_chapter_var.get() else 0
                except:
                    start, end = 1, 0
                
                self.log(f"Bắt đầu tải {len(selected)} chapter...", 'info')
                
                # Filter by range
                chapters_to_download = selected
                if end > 0:
                    chapters_to_download = [ch for ch in selected if start <= int(ch['number']) <= end]
                
                self.log(f"Tải từ chapter {start} đến {end if end > 0 else 'cuối'}", 'info')
                
                # Progress callback
                def update_progress(current, total, chapter_title):
                    progress = (current / total) * 100
                    self.progress_var.set(progress)
                    self.progress_label.config(text=f"Đang tải chapter {current}/{total}: {chapter_title[:50]}...")
                    self.root.update_idletasks()
                
                # TODO: Implement actual download with config
                self.log("Tính năng đang được phát triển...", 'warning')
                
                # Simulate progress
                for i, ch in enumerate(chapters_to_download[:5], 1):
                    time.sleep(1)
                    update_progress(i, len(chapters_to_download), ch['title'])
                
                self.log("✓ Tải hoàn tất (demo)!", 'success')
                self.progress_label.config(text="Tải hoàn tất!")
                self.status_text.set("Hoàn tất")
                
            except Exception as e:
                self.log(f"✗ Lỗi khi tải: {str(e)}", 'error')
                self.status_text.set("Lỗi")
                import traceback
                traceback.print_exc()
            finally:
                self.downloading = False
                self.download_btn.config(state='normal')
                self.stop_btn.config(state='disabled')
        
        threading.Thread(target=download, daemon=True).start()
    
    def stop_download(self):
        """Dừng quá trình tải"""
        if self.downloading:
            self.downloading = False
            self.log("Đã dừng tải theo yêu cầu", 'warning')
            self.status_text.set("Đã dừng")
            self.progress_label.config(text="Đã dừng tải")
            self.download_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
    
    def login_to_site(self):
        """Đăng nhập vào site"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập URL")
            return
        
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        
        self.log(f"Đang mở trình duyệt để đăng nhập vào {domain}...", 'info')
        self.log("Vui lòng đăng nhập trong trình duyệt, sau đó đóng trình duyệt", 'warning')
        
        def login():
            try:
                site_name = domain.split('.')[0]
                self.downloader.login_to_site(site_name, f"{parsed.scheme}://{parsed.netloc}")
                self.log("✓ Đăng nhập thành công!", 'success')
                self.status_text.set("Đã đăng nhập")
            except Exception as e:
                self.log(f"✗ Lỗi đăng nhập: {str(e)}", 'error')
        
        threading.Thread(target=login, daemon=True).start()
    
    def open_download_folder(self):
        """Mở thư mục chứa file tải về"""
        download_path = self.downloader.download_path
        if os.path.exists(download_path):
            os.startfile(download_path) if os.name == 'nt' else os.system(f'xdg-open "{download_path}"')
        else:
            messagebox.showwarning("Cảnh báo", "Thư mục tải chưa được tạo")
    
    def clear_log(self):
        """Xóa log"""
        self.log_text.delete(1.0, tk.END)
    
    def log(self, message, tag='info'):
        """Ghi log vào text area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message, tag)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def load_history(self):
        """Load lịch sử tải"""
        # Clear tree
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Load from file
        history_file = os.path.join(self.downloader.storage_path, 'history.json')
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                for item in history[-50:]:  # Chỉ hiển thị 50 bản ghi gần nhất
                    self.history_tree.insert('', 'end', 
                                           values=(item.get('story_name', 'Unknown'), 
                                                  item.get('chapters', 0),
                                                  item.get('timestamp', '')[:16],
                                                  item.get('output_file', '')))
            except Exception as e:
                self.log(f"Lỗi đọc lịch sử: {str(e)}", 'error')
    
    def open_history_file(self, event):
        """Mở file từ lịch sử khi double click"""
        self.open_selected_file()
    
    def open_selected_file(self):
        """Mở file được chọn trong lịch sử"""
        selected = self.history_tree.selection()
        if selected:
            file_path = self.history_tree.item(selected[0], 'values')[3]
            if os.path.exists(file_path):
                try:
                    if os.name == 'nt':  # Windows
                        os.startfile(file_path)
                    else:  # Linux/Mac
                        import subprocess
                        subprocess.run(['xdg-open', file_path])
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể mở file:\n{str(e)}")
            else:
                messagebox.showerror("Lỗi", "File không tồn tại")
    
    def clear_history(self):
        """Xóa lịch sử"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa lịch sử?"):
            history_file = os.path.join(self.downloader.storage_path, 'history.json')
            if os.path.exists(history_file):
                try:
                    os.remove(history_file)
                    self.load_history()
                    self.log("✓ Đã xóa lịch sử", 'success')
                except Exception as e:
                    self.log(f"✗ Lỗi xóa lịch sử: {str(e)}", 'error')


def main():
    """Hàm chính để chạy GUI"""
    root = tk.Tk()
    
    # Set icon nếu có
    try:
        if os.name == 'nt':  # Windows
            root.iconbitmap(default='icon.ico')
    except:
        pass
    
    app = TruyenDownloaderGUI(root)
    
    # Handle close event
    def on_closing():
        if app.downloading:
            if messagebox.askyesno("Xác nhận", "Đang tải dở. Bạn có chắc muốn thoát?"):
                app.downloading = False
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Run
    root.mainloop()


if __name__ == "__main__":
    main()