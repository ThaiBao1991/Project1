# dlnoveltext/functiondlnoveltext.py
import json
import tkinter as tk
import os
from urllib.parse import urlparse, urljoin
import http.cookiejar as cookiejar
import cloudscraper
from bs4 import BeautifulSoup
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tkinter import filedialog, messagebox, ttk, scrolledtext
import requests
from urllib.parse import urlparse


class NovelScraperFunctions:
    def __init__(self, gui):
        self.gui = gui
        self.config_dir = "data_DlNovel"
        self.config_file = os.path.join(self.config_dir, "config_dlnovel.json")
        self.cookies_file = os.path.join(self.config_dir, "cookies_{}.txt")
        self.scraper = cloudscraper.create_scraper()
        os.makedirs(self.config_dir, exist_ok=True)
        self.load_cookies()

    def load_cookies(self):
        try:
            base_url = self.get_base_url(self.gui.url_entry.get())
            cookie_path = self.cookies_file.format(base_url.replace('://', '_').replace('/', '_'))
            self.scraper.cookies = cookiejar.MozillaCookieJar(cookie_path)
            if os.path.exists(cookie_path):
                self.scraper.cookies.load(ignore_discard=True, ignore_expires=True)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải cookies: {e}")

    def save_cookies(self):
        try:
            base_url = self.get_base_url(self.gui.url_entry.get())
            cookie_path = self.cookies_file.format(base_url.replace('://', '_').replace('/', '_'))
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(base_url)
            cookies = driver.get_cookies()
            driver.quit()
            
            for cookie in cookies:
                c = cookiejar.Cookie(
                    version=0,
                    name=cookie['name'],
                    value=cookie['value'],
                    port=None,
                    port_specified=False,
                    domain=cookie.get('domain', ''),
                    domain_specified=bool(cookie.get('domain')),
                    domain_initial_dot=cookie.get('domain', '').startswith('.'),
                    path=cookie.get('path', '/'),
                    path_specified=bool(cookie.get('path')),
                    secure=cookie.get('secure', False),
                    expires=cookie.get('expiry', None),
                    discard=False,
                    comment=None,
                    comment_url=None,
                    rest={'HttpOnly': cookie.get('httpOnly', False)},
                    rfc2109=False
                )
                self.scraper.cookies.set_cookie(c)
            
            self.scraper.cookies.save(ignore_discard=True, ignore_expires=True)
            messagebox.showinfo("Thành công", f"Đã lưu cookies cho {base_url} từ trình duyệt!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu cookies: {e}")

    def get_base_url(self, url):
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    base_url = self.get_base_url(self.gui.url_entry.get())
                    if base_url in config:
                        site_config = config[base_url]
                        self.gui.url_entry.set(site_config.get('url', ''))
                        self.gui.username_entry.delete(0, tk.END)
                        self.gui.username_entry.insert(0, site_config.get('username', ''))
                        self.gui.password_entry.delete(0, tk.END)
                        self.gui.password_entry.insert(0, site_config.get('password', ''))
                        
                        # Load phương pháp và selector/script
                        self.gui.chapter_method.set(site_config.get('chapter_method', 'css'))
                        self.gui.chapter_list_css.delete(0, tk.END)
                        self.gui.chapter_list_css.insert(0, site_config.get('chapter_list_css', 'a.chapter-title'))
                        self.gui.chapter_list_script.delete('1.0', tk.END)
                        self.gui.chapter_list_script.insert(tk.END, site_config.get('chapter_list_script', "return Array.from(document.querySelectorAll('a.chapter-title')).map(a => a.href);"))
                        
                        self.gui.title_method.set(site_config.get('title_method', 'css'))
                        self.gui.title_css.delete(0, tk.END)
                        self.gui.title_css.insert(0, site_config.get('title_css', 'h1'))
                        self.gui.title_script.delete('1.0', tk.END)
                        self.gui.title_script.insert(tk.END, site_config.get('title_script', "return document.querySelector('h1').innerText;"))
                        
                        self.gui.content_method.set(site_config.get('content_method', 'css'))
                        self.gui.content_css.delete(0, tk.END)
                        self.gui.content_css.insert(0, site_config.get('content_css', 'div#chapter-content'))
                        self.gui.content_script.delete('1.0', tk.END)
                        self.gui.content_script.insert(tk.END, site_config.get('content_script', "return document.querySelector('div#chapter-content').innerHTML;"))
                        
                        self.gui.output_entry.delete(0, tk.END)
                        self.gui.output_entry.insert(0, site_config.get('output_file', 'output.html'))
                        
                        # Cập nhật trạng thái các widget
                        self.gui.toggle_method('chapter')
                        self.gui.toggle_method('title')
                        self.gui.toggle_method('content')
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải cấu hình: {e}")

    def save_config(self):
        try:
            base_url = self.get_base_url(self.gui.url_entry.get())
            config_data = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            
            config_data[base_url] = {
                'url': self.gui.url_entry.get(),
                'username': self.gui.username_entry.get(),
                'password': self.gui.password_entry.get(),
                
                # Lưu phương pháp và selector/script
                'chapter_method': self.gui.chapter_method.get(),
                'chapter_list_css': self.gui.chapter_list_css.get(),
                'chapter_list_script': self.gui.chapter_list_script.get("1.0", tk.END).strip(),
                
                'title_method': self.gui.title_method.get(),
                'title_css': self.gui.title_css.get(),
                'title_script': self.gui.title_script.get("1.0", tk.END).strip(),
                
                'content_method': self.gui.content_method.get(),
                'content_css': self.gui.content_css.get(),
                'content_script': self.gui.content_script.get("1.0", tk.END).strip(),
                
                'output_file': self.gui.output_entry.get()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Thành công", "Đã lưu cấu hình!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu cấu hình: {e}")
    def test_css_selector(self, url, selector, mode="chapter"):
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        if mode == "chapter":
            items = soup.select(selector)
            return "\n".join([f"{a.get_text(strip=True)} - {a.get('href')}" for a in items]) or "Không tìm thấy!"
        elif mode == "title":
            item = soup.select_one(selector)
            return item.get_text(strip=True) if item else "Không tìm thấy!"
        elif mode == "content":
            item = soup.select_one(selector)
            return item.get_text("\n", strip=True) if item else "Không tìm thấy!"
        return "Không xác định mode!"

    def test_js_selector(self, url, script, mode="chapter"):
        # Nếu bạn dùng Selenium, thực thi JS ở đây
        return "Chưa hỗ trợ test JS thực tế, chỉ test CSS selector."
    async def scrape_chapters(self):
        base_url = self.gui.url_entry.get()
        output_file = self.gui.output_entry.get()

        try:
            response = self.scraper.get(base_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Lấy danh sách chương
            if self.gui.chapter_method.get() == "css":
                chapter_links = soup.select(self.gui.chapter_list_css.get())
            else:
                # Sử dụng Selenium để chạy JS
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                driver = webdriver.Chrome(options=chrome_options)
                driver.get(base_url)
                chapter_links = driver.execute_script(self.gui.chapter_list_script.get("1.0", tk.END).strip())
                driver.quit()
            
            if not chapter_links:
                messagebox.showerror("Lỗi", "Không tìm thấy chương nào!")
                return

            total_chapters = len(chapter_links)
            self.gui.progress_bar['maximum'] = total_chapters
            html_content = [
                "<!DOCTYPE html>",
                "<html><head>",
                "<meta charset='UTF-8'>",
                "<title>Web Novel</title>",
                "<style>body { font-family: Arial, sans-serif; } .toc { margin: 20px; } .chapter { margin: 20px; padding: 10px; border: 1px solid #ccc; }</style>",
                "</head><body>",
                "<div class='toc'><h1>Mục lục</h1><ul>"
            ]

            for i, link in enumerate(chapter_links[:5]):  # Giới hạn 5 chương để test
                chapter_url = urljoin(base_url, link.get('href', '')) if self.gui.chapter_method.get() == "css" else link
                self.gui.progress_label.config(text=f"Đang tải chương {i + 1}/{total_chapters}: {chapter_url}")
                self.gui.progress_bar['value'] = i + 1
                self.gui.master.update()

                response = self.scraper.get(chapter_url)
                chapter_soup = BeautifulSoup(response.text, 'html.parser')
                
                # Lấy tiêu đề chương
                if self.gui.title_method.get() == "css":
                    title = chapter_soup.select_one(self.gui.title_css.get())
                    title_text = title.get_text(strip=True) if title else f"Chương {i + 1}"
                else:
                    chrome_options = Options()
                    chrome_options.add_argument("--headless")
                    driver = webdriver.Chrome(options=chrome_options)
                    driver.get(chapter_url)
                    title_text = driver.execute_script(self.gui.title_script.get("1.0", tk.END).strip())
                    driver.quit()

                # Lấy nội dung chương
                if self.gui.content_method.get() == "css":
                    content = chapter_soup.select_one(self.gui.content_css.get())
                    content_text = content.decode_contents() if content else "Không có nội dung"
                else:
                    chrome_options = Options()
                    chrome_options.add_argument("--headless")
                    driver = webdriver.Chrome(options=chrome_options)
                    driver.get(chapter_url)
                    content_text = driver.execute_script(self.gui.content_script.get("1.0", tk.END).strip())
                    driver.quit()

                html_content.append(f"<li><a href='#chapter{i + 1}'>{title_text}</a></li>")
                html_content.append(f"</ul></div><div class='chapter' id='chapter{i + 1}'>")
                html_content.append(f"<h2>{title_text}</h2>")
                html_content.append(content_text)
                html_content.append("</div>")

                await asyncio.sleep(0.1)

            html_content.append("</body></html>")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(html_content))
            self.gui.progress_label.config(text=f"Hoàn tất! File đã lưu tại {output_file}")
            messagebox.showinfo("Thành công", "Đã tạo file HTML thành công!")
        except Exception as e:
            self.gui.progress_label.config(text="Lỗi xảy ra!")
            messagebox.showerror("Lỗi", f"Lỗi khi tải: {e}")

def test_scrape(url, username=None, password=None, timeout=15):
    """
    Thử kết nối / fetch trang để kiểm tra:
    - trả về (True, 'OK') nếu fetch được
    - hoặc (False, error_message)
    Lưu ý: đây là hàm mẫu, bạn thay bằng logic lấy danh sách chương thực tế.
    """
    try:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        headers = {"User-Agent": "Mozilla/5.0 (compatible)"}
        sess = requests.Session()
        if username and password:
            # ví dụ login (tùy site) - placeholder: set auth or cookie
            sess.auth = (username, password)
        r = sess.get(url, headers=headers, timeout=timeout)
        if r.status_code == 200 and r.text:
            # Có thể kiểm tra xem r.text có chứa list chương, ví dụ bằng selector hoặc keyword
            return True, f"Fetched {len(r.text)} chars from {base}"
        else:
            return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)