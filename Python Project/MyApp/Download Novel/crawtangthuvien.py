import os
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# Config cho từng trang (dễ thêm site mới)
SITES = {
    "tangthuvien": {
        "name": "Tàng Thư Viện",
        "chapter_list_selector": "ul.list-chapter a",  # a tags trong ul.list-chapter
        "chapter_link_attr": "href",
        "chapter_title_selector": "h2.chapter-title, .chapter-title",  # heading chương
        "content_selector": "div#chapter-content, .chapter-content, div.box-content",  # nội dung chính
        "next_chapter_selector": "a.next-chapter, .next a",  # nếu crawl sequential
        "login_url": "https://tangthuvien.net/dang-nhap",  # nếu cần
        "login_fields": {"username": "input[name='email']", "password": "input[name='password']"},
        "use_js": True,  # cần chờ JS load
        "wait_time": 60,  # giây chờ load
    },
    # Thêm site khác ví dụ:
    # "truyenfull": {...}
}

class TruyenDownloader:
    def __init__(self, site_key="tangthuvien", download_dir="downloads"):
        self.site = SITES.get(site_key, {})
        self.download_dir = os.path.join(download_dir, self.site["name"])
        os.makedirs(self.download_dir, exist_ok=True)
        
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Uncomment để chạy ngầm (nhưng captcha khó hơn)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)

    def login(self, username=None, password=None):
        if not self.site.get("login_url"):
            return
        print("Đang đăng nhập...")
        self.driver.get(self.site["login_url"])
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.site["login_fields"]["username"])))
            self.driver.find_element(By.CSS_SELECTOR, self.site["login_fields"]["username"]).send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, self.site["login_fields"]["password"]).send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()  # chỉnh nếu button khác
            time.sleep(5)  # chờ redirect
            print("Đăng nhập thành công!")
        except Exception as e:
            print("Đăng nhập lỗi:", e)

    def get_chapter_list(self, novel_url):
        """Lấy list chương từ trang truyện chính (ví dụ: https://tangthuvien.net/doc-truyen/tao-thao-xuyen-viet-vo-dai-lang/)"""
        print(f"Đang lấy mục lục từ: {novel_url}")
        self.driver.get(novel_url)
        time.sleep(self.site["wait_time"])  # chờ JS load list
        
        soup = BeautifulSoup(self.driver.page_source, "lxml")
        chapter_links = []
        for a in soup.select(self.site["chapter_list_selector"]):
            href = a.get(self.site["chapter_link_attr"])
            if href:
                if not href.startswith("http"):
                    href = "https://tangthuvien.net" + href
                title = a.text.strip()
                chapter_links.append({"title": title, "url": href})
        return chapter_links

    def download_chapter(self, chapter):
        url = chapter["url"]
        title = chapter["title"].replace("/", "-").replace("\\", "-")  # an toàn filename
        filename = os.path.join(self.download_dir, f"{title}.html")
        
        if os.path.exists(filename):
            print(f"Đã tồn tại: {title}")
            return
        
        print(f"Đang tải: {title}")
        self.driver.get(url)
        time.sleep(self.site["wait_time"])
        
        # Xử lý Cloudflare captcha nếu hiện (thủ công)
        try:
            if "Checking your browser" in self.driver.page_source or "cf-browser-verification" in self.driver.page_source:
                print("Cloudflare đang kiểm tra... Hãy click 'I'm not robot' nếu hiện captcha.")
                input("Nhấn Enter sau khi qua captcha để tiếp tục...")
        except:
            pass
        
        soup = BeautifulSoup(self.driver.page_source, "lxml")
        
        # Lấy heading (tiêu đề chương)
        heading = soup.select_one(self.site["chapter_title_selector"])
        heading_html = str(heading) if heading else f"<h1>{title}</h1>"
        
        # Lấy content
        content_div = soup.select_one(self.site["content_selector"])
        content_html = str(content_div) if content_div else "<p>Không lấy được nội dung</p>"
        
        # Build HTML đầy đủ
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>{title}</title></head>
        <body>
        {heading_html}
        {content_html}
        </body>
        </html>
        """
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_html)
        print(f"Đã lưu: {filename}")

    def run(self, novel_url, username=None, password=None, max_chapters=None):
        self.login(username, password)
        chapters = self.get_chapter_list(novel_url)
        print(f"Tìm thấy {len(chapters)} chương.")
        
        if max_chapters:
            chapters = chapters[:max_chapters]
        
        for chap in chapters:
            self.download_chapter(chap)
            time.sleep(3 + random.uniform(0, 2))  # delay tránh block
        
        self.driver.quit()
        print("Hoàn tất! File HTML lưu tại:", self.download_dir)

# Sử dụng
if __name__ == "__main__":
    import random  # import random để delay ngẫu nhiên
    downloader = TruyenDownloader(site_key="tangthuvien")
    novel_url = "https://tangthuvien.net/doc-truyen/tao-thao-xuyen-viet-vo-dai-lang/"
    # Nếu cần đăng nhập (thay bằng acc thật của bạn)
    # downloader.run(novel_url, username="your_email", password="your_pass")
    downloader.run(novel_url)  # thử không login trước