from dataclasses import dataclass
from enum import Enum

class OverMaxSizePageCountState(Enum):
    EMPTY_PAGE = 0
    MOVE_TO_FIRST = 1
    MOVE_TO_LAST = 2
    MOVE_TO_PAGE_WITHOUT_CHAPTER_LIST = 3

@dataclass
class PageConfig:
    page_code: str = ""
    paging_pattern: str = ""
    css_query_get_list_chapter: str = ""
    css_query_get_chapter_title: str = ""
    css_query_get_chapter_content: str = ""
    url_page_test: str = ""
    text_guide: str = ""
    css_filter: str = ""
    
    is_manual_get: bool = False
    is_chapter_link_absolute: bool = True
    is_enable_chapter_sign: bool = False
    is_revert_chapter_list: bool = False
    is_forum_type: bool = False
    is_use_jsoup_get: bool = True
    is_vietnamese_host: bool = False
    by_pass_cloudflare: bool = False
    use_brute_force_method: bool = False
    
    over_max_size_page_count_state: OverMaxSizePageCountState = OverMaxSizePageCountState.EMPTY_PAGE
    script_js: str = ""
    main_host: str = ""
    # AJAX pagination fields (dùng khi danh sách chương load qua API JS, ví dụ truyennet.org)
    ajax_list_chap_url: str = ""   # URL mẫu API, ví dụ: "/get/listchap/{id}?page={page}"
    ajax_list_chap_id: str = ""    # Book ID cần truyền vào URL trên

    def __eq__(self, other):
        if not isinstance(other, PageConfig):
            return False
            
        p1 = self.page_code
        p2 = other.page_code
        
        if not p1 or not p2:
            return p1 == p2
            
        if "*" in p1 or "*" in p2:
            if "*" in p1 and p1.replace("*", "") not in p2:
                return False
            if "*" in p2 and p2.replace("*", "") not in p1:
                return False
            return True
            
        from utils.url_handler import normalize_host
        return normalize_host(p1) == normalize_host(p2)

    def __hash__(self):
        return hash(self.page_code)
