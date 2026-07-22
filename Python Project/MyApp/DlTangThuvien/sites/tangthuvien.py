import re
from bs4 import BeautifulSoup

class TangThuVienParser:
    def __init__(self, site_config, downloader):
        self.site_config = site_config
        self.downloader = downloader
        self.site_name = 'tangthuvien'
    
    def get_toc_url(self, story_info):
        """Tạo URL mục lục"""
        return f"{story_info['base_url']}/doc-truyen/{story_info['story_slug']}/"
    
    def parse_toc(self, html_content):
        """Parse mục lục từ HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        chapters = []
        
        toc_config = self.site_config['selectors']['toc']
        
        if toc_config['type'] == 'css':
            elements = soup.select(toc_config['selector'])
            for element in elements:
                href = element.get('href')
                if href and '/chuong-' in href:
                    chapters.append(href)
        
        return chapters
    
    def parse_chapter(self, html_content, url):
        """Parse nội dung chapter"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Lấy tiêu đề
        title_config = self.site_config['selectors']['title']
        if title_config['type'] == 'css':
            title_elem = soup.select_one(title_config['selector'])
            title = title_elem.text.strip() if title_elem else 'Không có tiêu đề'
        
        # Lấy nội dung
        content_config = self.site_config['selectors']['content']
        if content_config['type'] == 'css':
            content_elem = soup.select_one(content_config['selector'])
            if content_elem:
                # Xóa các script, style
                for script in content_elem.find_all(['script', 'style']):
                    script.decompose()
                content = str(content_elem)
            else:
                content = '<p>Không có nội dung</p>'
        
        return {
            'title': title,
            'content': content,
            'url': url
        }