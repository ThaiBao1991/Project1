from abc import ABC, abstractmethod
from utils.parser import HTMLParser

class BaseSiteParser(ABC):
    """Lớp cơ sở cho tất cả site parsers"""
    
    def __init__(self, site_config, downloader):
        self.site_config = site_config
        self.downloader = downloader
        self.parser = HTMLParser()
    
    @abstractmethod
    def get_toc_url(self, story_info):
        """Lấy URL của trang mục lục"""
        pass
    
    @abstractmethod
    def parse_toc(self, html_content):
        """Parse mục lục để lấy danh sách chapter URLs"""
        pass
    
    @abstractmethod
    def parse_chapter(self, html_content, url):
        """Parse nội dung chapter"""
        pass
    
    def clean_content(self, html_content):
        """Làm sạch nội dung chapter"""
        return self.parser.clean_html(html_content)
    
    def extract_title(self, html_content):
        """Trích xuất tiêu đề từ HTML"""
        title_config = self.site_config['selectors']['title']
        
        if title_config['type'] == 'css':
            return self.parser.parse_by_css(html_content, title_config['selector'])
        elif title_config['type'] == 'xpath':
            titles = self.parser.parse_by_xpath(html_content, title_config['selector'])
            return titles[0] if titles else None
        
        return None
    
    def extract_content(self, html_content):
        """Trích xuất nội dung từ HTML"""
        content_config = self.site_config['selectors']['content']
        
        if content_config['type'] == 'css':
            return self.parser.parse_by_css(html_content, content_config['selector'])
        elif content_config['type'] == 'xpath':
            contents = self.parser.parse_by_xpath(html_content, content_config['selector'])
            return ''.join(contents) if contents else None
        
        return None
    
    def extract_links(self, html_content):
        """Trích xuất links từ HTML"""
        toc_config = self.site_config['selectors']['toc']
        
        if toc_config['type'] == 'css':
            return self.parser.parse_by_css(html_content, toc_config['selector'], 
                                           multiple=True, attribute='href')
        elif toc_config['type'] == 'xpath':
            return self.parser.parse_by_xpath(html_content, toc_config['selector'])
        
        return []