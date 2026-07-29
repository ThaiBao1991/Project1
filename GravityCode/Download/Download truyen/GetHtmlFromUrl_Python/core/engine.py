import logging
import requests
import cloudscraper
from bs4 import BeautifulSoup, Tag
from typing import List, Tuple, Optional

from models.page_config import PageConfig
from models.chapter import Chapter

logger = logging.getLogger(__name__)

class GetHtmlEngine:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        # Lớp Cloudscraper dùng cho bypass Cloudflare
        self.cf_scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

    def _get_scraper(self, page_config):
        """Trả về session hoặc cf_scraper kèm theo cookies nếu có."""
        scraper = self.cf_scraper if getattr(page_config, 'by_pass_cloudflare', False) else self.session
        custom_cookies = getattr(page_config, '_custom_cookies', None)
        if custom_cookies:
            scraper.cookies.update(custom_cookies)
        return scraper
        
    def filter_html(self, soup_or_tag, css_filter: str):
        """Loại bỏ các thành phần rác khỏi BeautifulSoup Tag hoặc Document dựa trên cssFilter"""
        if not css_filter:
            return soup_or_tag
            
        str_content_filter = ""
        str_remove_content = css_filter
        
        # Xử lý đoạn text filter trong dấu ngoặc kép ("text1,text2")
        i_start = css_filter.find('"')
        i_end = css_filter.rfind('"')
        if i_start > -1 and i_end > -1 and i_end > i_start:
            str_content_filter = css_filter[i_start+1:i_end]
            str_remove_content = css_filter[:i_start] + css_filter[i_end+1:]
            
        filters = [f.strip() for f in str_remove_content.split(';') if f.strip()]
        
        for f in filters:
            try:
                # Nếu là remove attribute (vd: [style])
                if f.startswith('[') and f.endswith(']'):
                    attr_name = f[1:-1]
                    for el in soup_or_tag.find_all(attrs={attr_name: True}):
                        del el[attr_name]
                else:
                    # Remove tag completely
                    for el in soup_or_tag.select(f):
                        el.decompose()
            except Exception as e:
                logger.error(f"Lỗi filter CSS '{f}': {e}")
                
        # Nếu có text filter
        if str_content_filter:
            html_str = str(soup_or_tag)
            for text_to_remove in str_content_filter.split(','):
                html_str = html_str.replace(text_to_remove, '')
            return BeautifulSoup(html_str, 'html.parser')
            
        return soup_or_tag

    def fetch_html(self, url: str, page_config: PageConfig) -> Optional[BeautifulSoup]:
        """Tải HTML từ URL"""
        try:
            scraper = self._get_scraper(page_config)
            resp = scraper.get(url, timeout=15)
            resp.raise_for_status()
            # Tự động detect encoding
            resp.encoding = resp.apparent_encoding 
            return BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            logger.error(f"Lỗi tải {url}: {e}")
            return None

    def get_chapter_title_and_content(self, url: str, page_config: PageConfig) -> Chapter:
        """Lấy tiêu đề và nội dung của một chương truyện"""
        chapter = Chapter()
        
        soup = self.fetch_html(url, page_config.by_pass_cloudflare)
        if not soup:
            chapter.is_get_failed = True
            return chapter
            
        # Lấy tiêu đề TRƯỚC KHI filter
        if page_config.css_query_get_chapter_title:
            title_els = soup.select(page_config.css_query_get_chapter_title)
            if title_els:
                chapter.title = title_els[0].get_text(strip=True)
                
        # Lấy nội dung
        if page_config.css_query_get_chapter_content:
            content_els = soup.select(page_config.css_query_get_chapter_content)
            if content_els:
                html_parts = []
                for el in content_els:
                    # Chỉ áp dụng filter lên content block
                    filtered_el = self.filter_html(el, page_config.css_filter)
                    html_parts.append(str(filtered_el))
                    
                chapter.content = "<br/>".join(html_parts)
                
        return chapter

    def get_list_chapter_links(self, url: str, page_config: PageConfig) -> List[str]:
        """Lấy danh sách link chương từ trang mục lục.
        Hỗ trợ 2 mode:
        1. AJAX mode: dùng khi page_config.ajax_list_chap_url được cấu hình
        2. Static HTML mode: parse CSS selector trực tiếp từ HTML (kèm auto-paging)
        """
        # ── Mode 1: AJAX Pagination ──────────────────────────────────────────
        if page_config.ajax_list_chap_url:
            return self._get_links_ajax(url, page_config)

        # ── Mode 2: Static HTML (có thể có nhiều trang) ──────────────────────
        return self._get_links_static(url, page_config)

    # ------------------------------------------------------------------
    def _get_links_ajax(self, story_url: str, page_config: PageConfig) -> List[str]:
        """
        Fetch danh sách chương qua AJAX endpoint.
        Tự động detect book_id từ HTML (pattern: page(BOOK_ID, PAGE_NUM)).
        Lặp qua từng trang đến khi rỗng.
        """
        import re
        links: List[str] = []

        # Lấy book_id từ HTML trang truyện
        soup_main = self.fetch_html(story_url, page_config)
        if not soup_main:
            return links

        raw_html = str(soup_main)
        book_id = page_config.ajax_list_chap_id or ""
        if not book_id:
            # Detect từ pattern page(BOOK_ID, PAGE_NUM) trong JS
            match = re.search(r'page\((\d+),\s*\d+\)', raw_html)
            if match:
                book_id = match.group(1)
            else:
                logger.warning("Không tìm được book_id từ HTML. Fallback sang static mode.")
                return self._get_links_static(story_url, page_config)

        # Parse origin host để build API URL tuyệt đối
        from urllib.parse import urlparse
        parsed = urlparse(story_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        ajax_template = page_config.ajax_list_chap_url  # vd: "/get/listchap/{id}?page={page}"
        css_query = page_config.css_query_get_list_chapter or "a[href]"

        ajax_headers = {
            **self.session.headers,
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': story_url,
        }

        page_num = 1
        seen: set = set()
        while True:
            api_path = ajax_template.replace("{id}", book_id).replace("{page}", str(page_num))
            api_url = base_url + api_path

            try:
                if page_config.by_pass_cloudflare:
                    resp = self.cf_scraper.get(api_url, headers=ajax_headers, timeout=20)
                else:
                    resp = self.session.get(api_url, headers=ajax_headers, timeout=15)

                resp.raise_for_status()
                data = resp.json()
                html_chunk = data.get("data", "")
            except Exception as e:
                logger.error(f"Lỗi AJAX trang {page_num}: {e}")
                break

            if not html_chunk:
                logger.info(f"Trang {page_num} trống, dừng lại.")
                break

            chunk_soup = BeautifulSoup(html_chunk, "html.parser")
            page_links = []
            for el in chunk_soup.select(css_query):
                href = el.get("href", "")
                if href and href not in seen:
                    seen.add(href)
                    page_links.append(href)

            if not page_links:
                logger.info(f"Trang {page_num} không có link mới, dừng lại.")
                break

            links.extend(page_links)
            logger.info(f"AJAX page {page_num}: +{len(page_links)} chương (tổng: {len(links)})")
            page_num += 1

        return links

    # ------------------------------------------------------------------
    def _get_links_static(self, url: str, page_config: PageConfig) -> List[str]:
        """
        Lấy danh sách chương từ HTML tĩnh — có hỗ trợ auto-paging qua paging_pattern.
        """
        from urllib.parse import urlparse, urljoin
        links: List[str] = []
        seen: set = set()

        css_query = page_config.css_query_get_list_chapter
        # Xử lý cú pháp đặc biệt của Java cũ: #list-chapter ul{start=0&end=n}
        if "{" in css_query:
            css_query = css_query[:css_query.find("{")]

        current_url = url
        while current_url:
            soup = self.fetch_html(current_url, page_config.by_pass_cloudflare)
            if not soup:
                break

            page_links = []
            for el in soup.select(css_query):
                if el.name == 'a' and el.has_attr('href'):
                    href = el['href']
                else:
                    a = el.find('a', href=True)
                    href = a['href'] if a else ""

                if href and href not in seen:
                    seen.add(href)
                    page_links.append(href)

            if not page_links:
                break

            links.extend(page_links)

            # Auto-paging: tìm nút "Trang kế" theo paging_pattern
            next_url = None
            if page_config.paging_pattern:
                next_el = soup.select_one(page_config.paging_pattern)
                if next_el:
                    next_href = next_el.get('href', '')
                    if next_href:
                        next_url = urljoin(url, next_href)

            if not next_url or next_url == current_url:
                break
            current_url = next_url

        return links
