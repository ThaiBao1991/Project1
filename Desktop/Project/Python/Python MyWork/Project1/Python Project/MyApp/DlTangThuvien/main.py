import os
import json
import sys
import re
from urllib.parse import urlparse
from datetime import datetime
import requests
from bs4 import BeautifulSoup

class TruyenDownloader:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.load_config()
        
    def load_config(self):
        """Load cấu hình từ file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            # Tạo cấu hình mặc định
            self.config = {
                "storage_path": "storage",
                "download_path": "downloads",
                "default_site": "tangthuvien",
                "browser": {
                    "headless": False,
                    "user_data_dir": "storage/browser_data"
                }
            }
            self.save_config()
        
        # Gán các đường dẫn
        self.storage_path = self.config['storage_path']
        self.download_path = self.config['download_path']
        
        # Tạo thư mục cần thiết
        os.makedirs(self.storage_path, exist_ok=True)
        os.makedirs(self.download_path, exist_ok=True)
        os.makedirs(os.path.join(self.storage_path, 'cookies'), exist_ok=True)
        
        # Load sites config
        self.sites_config = self.load_sites_config()
    
    def save_config(self):
        """Lưu cấu hình"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def load_sites_config(self):
        """Load cấu hình các sites từ file"""
        sites_file = os.path.join(self.storage_path, 'sites_config.json')
        if os.path.exists(sites_file):
            with open(sites_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Tạo cấu hình mặc định cho Tangthuvien
            default_config = {
                "tangthuvien": {
                    "domain": "tangthuvien.net",
                    "selectors": {
                        "title": {
                            "type": "css",
                            "selector": ".chapter-title, h1.chapter-title, .chap-title"
                        },
                        "content": {
                            "type": "css", 
                            "selector": ".chapter-content, .content, #chapter-content"
                        },
                        "toc": {
                            "type": "css",
                            "selector": ".chapter-list a, .list-chapter a, .toc a"
                        }
                    },
                    "toc_page": "https://tangthuvien.net/doc-truyen/{story_slug}/",
                    "chapter_url_pattern": "/doc-truyen/{story_slug}/chuong-{chapter_number}",
                    "needs_login": True
                }
            }
            self.save_sites_config(default_config)
            return default_config
    
    def save_sites_config(self, config):
        """Lưu cấu hình sites"""
        sites_file = os.path.join(self.storage_path, 'sites_config.json')
        with open(sites_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def get_site_parser(self, url):
        """Xác định parser dựa trên URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        
        for site_name, site_config in self.sites_config.items():
            if site_config['domain'] in domain:
                if site_name == 'tangthuvien':
                    return TangThuVienParser(site_config, self)
        
        return None
    
    def extract_story_info(self, url):
        """Trích xuất thông tin truyện từ URL"""
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        
        # Format: /doc-truyen/ten-truyen/chuong-231
        if 'doc-truyen' in path_parts:
            idx = path_parts.index('doc-truyen')
            if idx + 1 < len(path_parts):
                story_slug = path_parts[idx + 1]
                
                # Xác định chapter nếu có
                chapter = None
                for part in path_parts:
                    if 'chuong-' in part:
                        chapter = part
                        break
                
                # Tạo tên truyện từ slug
                story_name = ' '.join(word.capitalize() for word in story_slug.split('-'))
                
                return {
                    'story_slug': story_slug,
                    'story_name': story_name,
                    'chapter': chapter,
                    'base_url': f"{parsed.scheme}://{parsed.netloc}",
                    'url': url
                }
        return None
    
    def login_to_site(self, site_name, url):
        """Đăng nhập vào site sử dụng Chromium"""
        print(f"\n=== ĐĂNG NHẬP VÀO {site_name.upper()} ===")
        print("Vui lòng đăng nhập vào tài khoản của bạn trong trình duyệt")
        print("Sau khi đăng nhập xong, đóng trình duyệt để tiếp tục...")
        
        cookie_file = os.path.join(self.storage_path, 'cookies', f'{site_name}.json')
        
        try:
            from utils.browser import BrowserManager
            with BrowserManager(headless=False) as browser:
                browser.navigate(url)
                input("Nhấn Enter sau khi đã đăng nhập xong và đóng trình duyệt...")
                
                # Lưu cookies
                cookies = browser.get_cookies()
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f)
                
                print("Đã lưu thông tin đăng nhập!")
                return cookies
        except ImportError:
            print("Không thể import BrowserManager. Vui lòng cài đặt selenium.")
            return None
    
    def download_chapter(self, url, parser, use_login=False):
        """Tải một chapter"""
        print(f"Đang tải: {url}")
        
        browser = None
        try:
            if use_login:
                try:
                    from utils.browser import BrowserManager
                    cookie_file = os.path.join(self.storage_path, 'cookies', f'{parser.site_name}.json')
                    if os.path.exists(cookie_file):
                        browser = BrowserManager(headless=True, cookie_file=cookie_file)
                        browser.__enter__()
                        html_content = browser.get_page_content(url)
                    else:
                        print("Chưa đăng nhập. Đang tải bằng requests...")
                        response = requests.get(url, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        html_content = response.text
                except ImportError:
                    print("Selenium chưa được cài đặt. Đang tải bằng requests...")
                    response = requests.get(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    html_content = response.text
            else:
                # Sử dụng requests thông thường
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                html_content = response.text
            
            # Parse nội dung
            chapter_data = parser.parse_chapter(html_content, url)
            
            return chapter_data
            
        finally:
            if browser:
                browser.__exit__(None, None, None)
    
    def download_story(self, story_url, use_login=False, progress_callback=None):
        """Tải toàn bộ truyện"""
        story_info = self.extract_story_info(story_url)
        if not story_info:
            print("Không thể xác định thông tin truyện từ URL")
            return None
        
        parser = self.get_site_parser(story_url)
        if not parser:
            print("Không hỗ trợ site này")
            return None
        
        print(f"Truyện: {story_info['story_name']}")
        print(f"Slug: {story_info['story_slug']}")
        
        # Lấy mục lục
        toc_url = parser.get_toc_url(story_info)
        print(f"Đang lấy mục lục từ: {toc_url}")
        
        browser = None
        try:
            # Kiểm tra đăng nhập nếu cần
            if use_login and parser.site_config.get('needs_login', False):
                cookie_file = os.path.join(self.storage_path, 'cookies', f'{parser.site_name}.json')
                if not os.path.exists(cookie_file):
                    print("Cần đăng nhập để tải truyện này")
                    self.login_to_site(parser.site_name, story_info['base_url'])
            
            # Lấy HTML mục lục
            if use_login and os.path.exists(cookie_file):
                from utils.browser import BrowserManager
                browser = BrowserManager(headless=True, cookie_file=cookie_file)
                browser.__enter__()
                toc_html = browser.get_page_content(toc_url)
            else:
                response = requests.get(toc_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                toc_html = response.text
            
            # Parse mục lục
            chapters = parser.parse_toc(toc_html)
            
            # Lọc chỉ lấy các chapter hợp lệ
            valid_chapters = []
            for ch in chapters:
                if isinstance(ch, str) and ('chuong' in ch.lower() or 'chapter' in ch.lower()):
                    valid_chapters.append(ch)
            
            if not valid_chapters:
                print("Không tìm thấy chapter nào")
                return None
            
            print(f"Tìm thấy {len(valid_chapters)} chapter")
            
            # Tải từng chapter
            all_chapters = []
            total_chapters = len(valid_chapters)
            
            for i, chapter_url in enumerate(valid_chapters, 1):
                print(f"Đang tải chapter {i}/{total_chapters}")
                
                # Tạo URL đầy đủ
                if chapter_url.startswith('http'):
                    full_url = chapter_url
                else:
                    full_url = story_info['base_url'] + chapter_url
                
                # Tải nội dung chapter
                if use_login and browser:
                    html_content = browser.get_page_content(full_url)
                else:
                    response = requests.get(full_url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    html_content = response.text
                
                # Parse chapter
                chapter_data = parser.parse_chapter(html_content, full_url)
                all_chapters.append(chapter_data)
                
                # Cập nhật progress
                if progress_callback:
                    progress_callback(i, total_chapters, chapter_data['title'])
            
            # Tạo file HTML tổng hợp
            output_file = os.path.join(self.download_path, f"{story_info['story_slug']}.html")
            self.create_html_file(all_chapters, story_info['story_name'], output_file)
            
            # Lưu lịch sử
            self.save_history(story_info, len(all_chapters), output_file)
            
            print(f"Đã lưu tại: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"Lỗi khi tải truyện: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            if browser:
                browser.__exit__(None, None, None)
    
    def create_html_file(self, chapters, story_name, output_file):
        """Tạo file HTML từ các chapter"""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>{story_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Times New Roman', serif; 
            margin: 40px auto; 
            max-width: 800px; 
            padding: 20px;
            line-height: 1.8;
            background: #f9f9f9;
        }}
        .container {{
            background: white;
            padding: 40px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 5px;
        }}
        h1 {{ 
            color: #2c3e50; 
            text-align: center;
            font-size: 28px;
            margin-bottom: 30px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }}
        h2 {{ 
            color: #34495e; 
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 22px;
            padding-left: 10px;
            border-left: 4px solid #3498db;
        }}
        .chapter-content {{ 
            line-height: 1.8;
            font-size: 16px;
            text-align: justify;
        }}
        .chapter-content p {{
            margin-bottom: 15px;
            text-indent: 30px;
        }}
        hr {{ 
            margin: 40px 0; 
            border: none;
            border-top: 1px dashed #bdc3c7;
        }}
        .toc {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .toc ul {{
            list-style: none;
            padding-left: 20px;
        }}
        .toc li {{
            margin-bottom: 8px;
        }}
        .toc a {{
            color: #2980b9;
            text-decoration: none;
            font-size: 15px;
        }}
        .toc a:hover {{
            text-decoration: underline;
            color: #3498db;
        }}
        .chapter {{
            margin-bottom: 50px;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; padding: 0; }}
            .toc {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{story_name}</h1>
        
        <div class="toc">
            <h2>📖 Mục lục</h2>
            <ul>
"""
        
        # Thêm mục lục
        for i, chapter in enumerate(chapters, 1):
            chapter_title = chapter.get('title', f'Chapter {i}')
            # Làm sạch tiêu đề
            chapter_title = chapter_title.replace('"', '&quot;').replace("'", "&#39;")
            html_content += f'        <li><a href="#chapter-{i}">Chapter {i}: {chapter_title}</a></li>\n'
        
        html_content += "    </ul>\n    </div>\n"
        
        # Thêm nội dung các chapter
        for i, chapter in enumerate(chapters, 1):
            chapter_title = chapter.get('title', f'Chapter {i}')
            chapter_content = chapter.get('content', '<p>Không có nội dung</p>')
            
            # Xử lý nội dung
            chapter_content = chapter_content.replace('src="//', 'src="https://')
            
            html_content += f"""
    <div id="chapter-{i}" class="chapter">
        <h2>Chapter {i}: {chapter_title}</h2>
        <div class="chapter-content">
            {chapter_content}
        </div>
        <hr>
    </div>
"""
        
        html_content += """
    </div>
</body>
</html>"""
        
        # Lưu file với encoding UTF-8
        with open(output_file, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(html_content)
        
        print(f"Đã tạo file HTML: {output_file}")
    
    def save_history(self, story_info, chapters_count, output_file):
        """Lưu lịch sử tải"""
        history_file = os.path.join(self.storage_path, 'history.json')
        
        history = []
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        history.append({
            'story_name': story_info['story_name'],
            'story_slug': story_info['story_slug'],
            'chapters': chapters_count,
            'output_file': output_file,
            'timestamp': datetime.now().isoformat(),
            'url': story_info.get('url', '')
        })
        
        # Giữ 50 bản ghi gần nhất
        if len(history) > 50:
            history = history[-50:]
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)


class TangThuVienParser:
    """Parser cho trang Tangthuvien.net"""
    
    def __init__(self, site_config, downloader):
        self.site_config = site_config
        self.downloader = downloader
        self.site_name = 'tangthuvien'
    
    def get_toc_url(self, story_info):
        """Tạo URL mục lục"""
        return f"{story_info['base_url']}/doc-truyen/{story_info['story_slug']}/"
    
    def parse_toc(self, html_content):
        """Parse mục lục từ HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            chapters = []
            
            toc_config = self.site_config['selectors']['toc']
            
            if toc_config['type'] == 'css':
                # Thử nhiều selector khác nhau
                selectors = toc_config['selector'].split(',')
                for selector in selectors:
                    selector = selector.strip()
                    elements = soup.select(selector)
                    if elements:
                        for element in elements:
                            href = element.get('href')
                            if href:
                                # Chuẩn hóa URL
                                if not href.startswith('http'):
                                    chapters.append(href)
                                elif self.site_config['domain'] in href:
                                    # Lấy path từ URL đầy đủ
                                    parsed = urlparse(href)
                                    chapters.append(parsed.path)
                        break
            
            # Lọc và loại bỏ trùng lặp
            unique_chapters = []
            seen = set()
            for ch in chapters:
                if ch not in seen:
                    seen.add(ch)
                    unique_chapters.append(ch)
            
            return unique_chapters
            
        except Exception as e:
            print(f"Lỗi khi parse mục lục: {e}")
            return []
    
    def parse_chapter(self, html_content, url):
        """Parse nội dung chapter"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Lấy tiêu đề
            title = self.extract_title(soup)
            
            # Lấy nội dung
            content = self.extract_content(soup)
            
            # Xử lý nội dung
            if content:
                # Thêm class cho paragraph
                for p in content.find_all('p'):
                    if not p.get('class'):
                        p['class'] = ['chapter-paragraph']
                
                # Xử lý images
                for img in content.find_all('img'):
                    if img.get('src') and img['src'].startswith('//'):
                        img['src'] = 'https:' + img['src']
                
                content_html = str(content)
            else:
                content_html = '<p>Không thể tải nội dung chapter</p>'
            
            return {
                'title': title,
                'content': content_html,
                'url': url
            }
            
        except Exception as e:
            print(f"Lỗi khi parse chapter: {e}")
            return {
                'title': 'Lỗi tải chapter',
                'content': f'<p>Có lỗi xảy ra khi tải chapter: {str(e)}</p>',
                'url': url
            }
    
    def extract_title(self, soup):
        """Trích xuất tiêu đề chapter"""
        title_config = self.site_config['selectors']['title']
        
        if title_config['type'] == 'css':
            selectors = title_config['selector'].split(',')
            for selector in selectors:
                selector = selector.strip()
                element = soup.select_one(selector)
                if element:
                    return element.text.strip()
        
        # Fallback: tìm trong thẻ h1 hoặc title
        h1 = soup.find('h1')
        if h1:
            return h1.text.strip()
        
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.text.strip()
        
        return "Không có tiêu đề"
    
    def extract_content(self, soup):
        """Trích xuất nội dung chapter"""
        content_config = self.site_config['selectors']['content']
        
        if content_config['type'] == 'css':
            selectors = content_config['selector'].split(',')
            for selector in selectors:
                selector = selector.strip()
                element = soup.select_one(selector)
                if element:
                    # Xóa các thẻ không cần thiết
                    for tag in element.find_all(['script', 'style', 'ins', 'iframe']):
                        tag.decompose()
                    
                    # Xóa các quảng cáo
                    for ad in element.find_all(class_=re.compile(r'ad|ads|banner|quang-cao', re.I)):
                        ad.decompose()
                    
                    return element
        
        return None

def download_story_with_config(self, story_info, site_config, chapters, progress_callback=None):
    """Tải truyện sử dụng cấu hình site"""
    import requests
    from bs4 import BeautifulSoup
    import time
    
    all_chapters = []
    total = len(chapters)
    
    for i, chapter in enumerate(chapters, 1):
        if not self.downloading:  # Kiểm tra nếu bị dừng
            break
            
        try:
            # Tạo URL đầy đủ
            if chapter['url'].startswith('http'):
                url = chapter['url']
            else:
                url = story_info['base_url'] + chapter['url']
            
            # Log
            print(f"Đang tải chapter {i}/{total}: {url}")
            
            # Lấy HTML
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Parse theo cấu hình
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Lấy title
                title_config = site_config['selectors']['title']
                if title_config['type'] == 'css':
                    title_elem = soup.select_one(title_config['script'])
                    title = title_elem.text.strip() if title_elem else f"Chapter {i}"
                else:
                    title = f"Chapter {i}"
                
                # Lấy content
                content_config = site_config['selectors']['content']
                if content_config['type'] == 'css':
                    content_elem = soup.select_one(content_config['script'])
                    if content_elem:
                        # Xóa script, style
                        for tag in content_elem.find_all(['script', 'style', 'ins']):
                            tag.decompose()
                        content = str(content_elem)
                    else:
                        content = "<p>Không thể tải nội dung</p>"
                else:
                    content = "<p>Không thể tải nội dung</p>"
                
                all_chapters.append({
                    'title': title,
                    'content': content,
                    'url': url
                })
                
                # Callback progress
                if progress_callback:
                    progress_callback(i, total, title)
                
                time.sleep(1)  # Tránh spam request
            else:
                print(f"Lỗi HTTP {response.status_code} khi tải {url}")
                
        except Exception as e:
            print(f"Lỗi khi tải chapter {i}: {str(e)}")
            all_chapters.append({
                'title': f"Chapter {i} (Lỗi)",
                'content': f"<p>Có lỗi xảy ra khi tải chapter: {str(e)}</p>",
                'url': chapter['url']
            })
    
    return all_chapters

def main():
    """Hàm chính để chạy từ command line"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Tải truyện từ các trang web')
    parser.add_argument('url', help='URL của truyện cần tải')
    parser.add_argument('--login', action='store_true', help='Sử dụng đăng nhập để tải')
    parser.add_argument('--config', default='config.json', help='File cấu hình')
    
    args = parser.parse_args()
    
    downloader = TruyenDownloader(args.config)
    
    print("=" * 60)
    print("TRUYỆN DOWNLOADER")
    print("=" * 60)
    
    if 'doc-truyen' in args.url:
        result = downloader.download_story(args.url, args.login)
        if result:
            print(f"\n✅ Tải thành công! File: {result}")
        else:
            print("\n❌ Tải thất bại!")
    else:
        print("URL không hợp lệ. Vui lòng nhập URL trang truyện.")

if __name__ == '__main__':
    main()