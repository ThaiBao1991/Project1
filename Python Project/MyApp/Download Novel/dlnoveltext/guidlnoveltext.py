import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from dlnoveltext.functiondlnoveltext import NovelScraperFunctions
import webbrowser
import os
import json

class NovelScraperGUI:
    def __init__(self, master, url_entry):
        self.master = master
        self.url_entry = url_entry
        self.top_level = None
        self.functions = NovelScraperFunctions(self)
        
        # Khởi tạo các biến cần thiết
        self.chapter_list_css = None
        self.title_css = None
        self.content_css = None
        self.use_css_chapters = tk.BooleanVar(value=True)
        self.use_css_title = tk.BooleanVar(value=True)
        self.use_css_content = tk.BooleanVar(value=True)
        
        self.create_main_window()

    def create_main_window(self):
        if self.top_level is not None and self.top_level.winfo_exists():
            self.top_level.deiconify()
            self.top_level.lift()
            return

        self.top_level = tk.Toplevel(self.master)
        self.top_level.title("Tải Truyện Chữ")
        self.top_level.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.top_level.minsize(800, 600)
        
        self.notebook = ttk.Notebook(self.top_level)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.create_basic_settings_tab()
        self.create_script_test_tab()
        self.create_progress_tab()

        self.functions.load_config()

    def create_basic_settings_tab(self):
        basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(basic_frame, text="Cài đặt cơ bản")

        input_frame = tk.LabelFrame(basic_frame, text="Cài đặt trang web", padx=5, pady=5)
        input_frame.pack(padx=10, pady=5, fill=tk.X)

        tk.Label(input_frame, text="URL danh sách chương:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.url_entry_widget = tk.Entry(input_frame, width=50, textvariable=self.url_entry)
        self.url_entry_widget.grid(row=0, column=1, padx=5, pady=2)

        open_btn = tk.Button(input_frame, text="Mở trình duyệt", command=self.open_browser)
        open_btn.grid(row=0, column=2, padx=5, pady=2)

        tk.Label(input_frame, text="Tên người dùng:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.username_entry = tk.Entry(input_frame, width=50)
        self.username_entry.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(input_frame, text="Mật khẩu:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.password_entry = tk.Entry(input_frame, width=50, show="*")
        self.password_entry.grid(row=2, column=1, padx=5, pady=2)

        save_cookie_btn = tk.Button(input_frame, text="Lưu Cookie", command=self.functions.save_cookies)
        save_cookie_btn.grid(row=3, column=1, padx=5, pady=2, sticky=tk.E)

        tk.Label(input_frame, text="File lưu:").grid(row=4, column=0, padx=5, pady=2, sticky=tk.W)
        self.output_entry = tk.Entry(input_frame, width=50)
        self.output_entry.grid(row=4, column=1, padx=5, pady=2)
        self.output_entry.insert(0, "output.html")

        browse_btn = tk.Button(input_frame, text="Duyệt...", command=self.browse_output)
        browse_btn.grid(row=4, column=2, padx=5, pady=2)

        button_frame = tk.Frame(basic_frame, padx=5, pady=5)
        button_frame.pack(padx=10, pady=5, fill=tk.X)

        save_config_btn = tk.Button(button_frame, text="Lưu cấu hình", command=self.functions.save_config)
        save_config_btn.pack(side=tk.LEFT, padx=5)

        close_btn = tk.Button(button_frame, text="Đóng", command=self.hide_window)
        close_btn.pack(side=tk.LEFT, padx=5)

    def create_script_test_tab(self):
        script_frame = ttk.Frame(self.notebook)
        self.notebook.add(script_frame, text="Script & Test")

        # Phần danh sách chương
        chapter_frame = tk.LabelFrame(script_frame, text="Danh sách chương", padx=5, pady=5)
        chapter_frame.pack(fill=tk.X, padx=5, pady=5)

        self.chapter_method = tk.StringVar(value="css")
        tk.Radiobutton(chapter_frame, text="Dùng CSS Selector", variable=self.chapter_method, value="css", 
                      command=lambda: self.toggle_method('chapter')).grid(row=0, column=0, padx=5, sticky=tk.W)
        tk.Radiobutton(chapter_frame, text="Dùng JavaScript", variable=self.chapter_method, value="js",
                      command=lambda: self.toggle_method('chapter')).grid(row=0, column=1, padx=5, sticky=tk.W)

        tk.Label(chapter_frame, text="CSS Selector:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.chapter_list_css = tk.Entry(chapter_frame, width=70)
        self.chapter_list_css.grid(row=1, column=1, columnspan=2, padx=5, pady=2)
        self.chapter_list_css.insert(0, "a.chapter-title")

        tk.Label(chapter_frame, text="JavaScript:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.chapter_list_script = scrolledtext.ScrolledText(chapter_frame, width=70, height=3)
        self.chapter_list_script.grid(row=2, column=1, columnspan=2, padx=5, pady=2)
        self.chapter_list_script.insert(tk.END, "return Array.from(document.querySelectorAll('a.chapter-title')).map(a => a.href);")

        test_chapter_btn = tk.Button(chapter_frame, text="Test", command=lambda: self.test_script('chapter'))
        test_chapter_btn.grid(row=3, column=2, padx=5, pady=2, sticky=tk.E)

        self.chapter_result = scrolledtext.ScrolledText(chapter_frame, width=70, height=3, state='disabled')
        self.chapter_result.grid(row=4, column=0, columnspan=3, padx=5, pady=2)

        # Phần tiêu đề chương
        title_frame = tk.LabelFrame(script_frame, text="Tiêu đề chương", padx=5, pady=5)
        title_frame.pack(fill=tk.X, padx=5, pady=5)

        self.title_method = tk.StringVar(value="css")
        tk.Radiobutton(title_frame, text="Dùng CSS Selector", variable=self.title_method, value="css",
                      command=lambda: self.toggle_method('title')).grid(row=0, column=0, padx=5, sticky=tk.W)
        tk.Radiobutton(title_frame, text="Dùng JavaScript", variable=self.title_method, value="js",
                      command=lambda: self.toggle_method('title')).grid(row=0, column=1, padx=5, sticky=tk.W)

        tk.Label(title_frame, text="URL chương test:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.test_chapter_url = tk.Entry(title_frame, width=70)
        self.test_chapter_url.grid(row=1, column=1, columnspan=2, padx=5, pady=2)

        tk.Label(title_frame, text="CSS Selector:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.title_css = tk.Entry(title_frame, width=70)
        self.title_css.grid(row=2, column=1, columnspan=2, padx=5, pady=2)
        self.title_css.insert(0, "h1")

        tk.Label(title_frame, text="JavaScript:").grid(row=3, column=0, padx=5, pady=2, sticky=tk.W)
        self.title_script = scrolledtext.ScrolledText(title_frame, width=70, height=2)
        self.title_script.grid(row=3, column=1, columnspan=2, padx=5, pady=2)
        self.title_script.insert(tk.END, "return document.querySelector('h1').innerText;")

        test_title_btn = tk.Button(title_frame, text="Test", command=lambda: self.test_script('title'))
        test_title_btn.grid(row=4, column=2, padx=5, pady=2, sticky=tk.E)

        self.title_result = scrolledtext.ScrolledText(title_frame, width=70, height=2, state='disabled')
        self.title_result.grid(row=5, column=0, columnspan=3, padx=5, pady=2)

        # Phần nội dung chương
        content_frame = tk.LabelFrame(script_frame, text="Nội dung chương", padx=5, pady=5)
        content_frame.pack(fill=tk.X, padx=5, pady=5)

        self.content_method = tk.StringVar(value="css")
        tk.Radiobutton(content_frame, text="Dùng CSS Selector", variable=self.content_method, value="css",
                      command=lambda: self.toggle_method('content')).grid(row=0, column=0, padx=5, sticky=tk.W)
        tk.Radiobutton(content_frame, text="Dùng JavaScript", variable=self.content_method, value="js",
                      command=lambda: self.toggle_method('content')).grid(row=0, column=1, padx=5, sticky=tk.W)

        tk.Label(content_frame, text="CSS Selector:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.content_css = tk.Entry(content_frame, width=70)
        self.content_css.grid(row=1, column=1, columnspan=2, padx=5, pady=2)
        self.content_css.insert(0, "div#chapter-content")

        tk.Label(content_frame, text="JavaScript:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.content_script = scrolledtext.ScrolledText(content_frame, width=70, height=3)
        self.content_script.grid(row=2, column=1, columnspan=2, padx=5, pady=2)
        self.content_script.insert(tk.END, "return document.querySelector('div#chapter-content').innerHTML;")

        test_content_btn = tk.Button(content_frame, text="Test", command=lambda: self.test_script('content'))
        test_content_btn.grid(row=3, column=2, padx=5, pady=2, sticky=tk.E)

        self.content_result = scrolledtext.ScrolledText(content_frame, width=70, height=3, state='disabled')
        self.content_result.grid(row=4, column=0, columnspan=3, padx=5, pady=2)

        # Kích hoạt trạng thái ban đầu
        self.toggle_method('chapter')
        self.toggle_method('title')
        self.toggle_method('content')

    def create_progress_tab(self):
        progress_frame = ttk.Frame(self.notebook)
        self.notebook.add(progress_frame, text="Tiến trình")

        self.progress_label = tk.Label(progress_frame, text="Sẵn sàng...")
        self.progress_label.pack(pady=10)

        self.progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.progress_bar.pack(pady=5)

        start_btn = tk.Button(progress_frame, text="Bắt đầu tải truyện", command=self.start_scraping)
        start_btn.pack(pady=20)

    def toggle_method(self, element_type):
        if element_type == 'chapter':
            use_css = self.chapter_method.get() == "css"
            self.chapter_list_css.config(state=tk.NORMAL if use_css else tk.DISABLED)
            self.chapter_list_script.config(state=tk.NORMAL if not use_css else tk.DISABLED)
        elif element_type == 'title':
            use_css = self.title_method.get() == "css"
            self.title_css.config(state=tk.NORMAL if use_css else tk.DISABLED)
            self.title_script.config(state=tk.NORMAL if not use_css else tk.DISABLED)
        elif element_type == 'content':
            use_css = self.content_method.get() == "css"
            self.content_css.config(state=tk.NORMAL if use_css else tk.DISABLED)
            self.content_script.config(state=tk.NORMAL if not use_css else tk.DISABLED)

    def test_script(self, script_type):
        url = self.url_entry.get() if script_type == 'chapter' else self.test_chapter_url.get()
        if not url:
            messagebox.showerror("Lỗi", "Vui lòng nhập URL!")
            return

        try:
            if script_type == 'chapter':
                if self.chapter_method.get() == "css":
                    selector = self.chapter_list_css.get()
                    result = self.functions.test_css_selector(url, selector, mode="chapter")
                else:
                    script = self.chapter_list_script.get("1.0", tk.END).strip()
                    result = self.functions.test_js_selector(url, script, mode="chapter")
                result_box = self.chapter_result
            elif script_type == 'title':
                if self.title_method.get() == "css":
                    selector = self.title_css.get()
                    result = self.functions.test_css_selector(url, selector, mode="title")
                else:
                    script = self.title_script.get("1.0", tk.END).strip()
                    result = self.functions.test_js_selector(url, script, mode="title")
                result_box = self.title_result
            else:  # content
                if self.content_method.get() == "css":
                    selector = self.content_css.get()
                    result = self.functions.test_css_selector(url, selector, mode="content")
                else:
                    script = self.content_script.get("1.0", tk.END).strip()
                    result = self.functions.test_js_selector(url, script, mode="content")
                result_box = self.content_result

            result_box.config(state='normal')
            result_box.delete('1.0', tk.END)
            result_box.insert(tk.END, result)
            result_box.config(state='disabled')
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi test script: {str(e)}")
    def hide_window(self):
        if self.top_level:
            self.top_level.withdraw()

    def open_browser(self):
        url = self.url_entry.get()
        if url:
            webbrowser.open(url, new=2)
        else:
            messagebox.showerror("Lỗi", "Vui lòng nhập URL!")

    def browse_output(self):
        file_path = filedialog.asksaveasfilename(
            title="Chọn nơi lưu file",
            defaultextension=".html",
            filetypes=(("HTML Files", "*.html"), ("All Files", "*.*"))
        )
        if file_path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, file_path)

    def start_scraping(self):
        if not self.url_entry.get() or not self.output_entry.get():
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ URL và file lưu!")
            return
        self.functions.scrape_chapters()