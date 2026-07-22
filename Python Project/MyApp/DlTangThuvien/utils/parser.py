import re
from bs4 import BeautifulSoup
import json

class HTMLParser:
    """Lớp parser tổng quát cho các trang web"""
    
    @staticmethod
    def parse_by_css(html_content, selector, multiple=False, attribute=None):
        """Parse nội dung bằng CSS selector"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        if multiple:
            elements = soup.select(selector)
            if attribute:
                return [elem.get(attribute, '') for elem in elements if elem]
            return [elem.text.strip() for elem in elements if elem]
        else:
            element = soup.select_one(selector)
            if element:
                if attribute:
                    return element.get(attribute, '')
                return element.text.strip()
        return None if not multiple else []
    
    @staticmethod
    def parse_by_xpath(html_content, xpath):
        """Parse nội dung bằng XPath (cần lxml)"""
        try:
            from lxml import html
            tree = html.fromstring(html_content)
            elements = tree.xpath(xpath)
            return [elem.text_content().strip() for elem in elements if elem is not None]
        except:
            return []
    
    @staticmethod
    def clean_html(html_content):
        """Làm sạch HTML, loại bỏ script, style"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Xóa các thẻ không cần thiết
        for tag in soup.find_all(['script', 'style', 'iframe', 'noscript']):
            tag.decompose()
        
        # Xóa các comment
        for comment in soup.find_all(string=lambda text: isinstance(text, str) and '<!--' in text):
            comment.extract()
        
        return str(soup)
    
    @staticmethod
    def extract_links(html_content, pattern=None):
        """Trích xuất tất cả links từ HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if pattern:
                if re.search(pattern, href):
                    links.append({
                        'url': href,
                        'text': a.text.strip()
                    })
            else:
                links.append({
                    'url': href,
                    'text': a.text.strip()
                })
        
        return links
    
    @staticmethod
    def parse_json_ld(html_content):
        """Parse JSON-LD structured data"""
        soup = BeautifulSoup(html_content, 'html.parser')
        json_ld_data = []
        
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                json_ld_data.append(data)
            except:
                continue
        
        return json_ld_data
    
    @staticmethod
    def detect_encoding(html_content):
        """Phát hiện encoding của trang"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Kiểm tra meta charset
        meta = soup.find('meta', charset=True)
        if meta and meta.get('charset'):
            return meta['charset']
        
        # Kiểm tra meta http-equiv
        meta = soup.find('meta', attrs={'http-equiv': 'Content-Type'})
        if meta and meta.get('content'):
            content = meta['content']
            if 'charset=' in content:
                return content.split('charset=')[-1]
        
        return 'utf-8'