import os
import re
import logging
from typing import List, Tuple, Dict, Any, Callable, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger("chapter_splitter")

# Regex nhận diện tiêu đề chương tiếng Trung & tiếng Việt
CHAPTER_TITLE_PATTERNS = [
    # Tiếng Trung: 第1章, 第一百二十章, 第 1 节, 第1回, 卷一 第1章...
    r"(?:第\s*[0-9一二三四五六七八九十百千万零]+\s*[章回节卷部][^\n\r<]{0,50})",
    # Tiếng Trung dạng số đầu dòng: 001. Tiêu đề, 1、Tiêu đề
    r"(?:^[0-9]{1,5}\s*[\.、\s\-]\s*[\u4e00-\u9fa5]{2,30})",
    # Tiếng Việt / Anh: Chương 1: ..., Hồi 1, Chapter 1...
    r"(?:(?:Chương|Hồi|Tiết|Quyển|Chapter)\s+[0-9IVXLCDM]+[^\n\r<]{0,60})",
]

COMPILED_TITLE_REGEX = re.compile(
    r"|".join(f"(?:{p})" for p in CHAPTER_TITLE_PATTERNS),
    re.IGNORECASE | re.MULTILINE
)


def read_file_safely(file_path: str) -> str:
    """Đọc file với các bảng mã phổ biến UTF-8, GB18030, GBK, Latin-1."""
    encodings = ["utf-8-sig", "utf-8", "gb18030", "gbk", "cp1252", "latin1"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
                if content:
                    return content
        except Exception:
            continue
    return ""


def clean_title_for_filename(title: str, max_len: int = 60) -> str:
    """Làm sạch tiêu đề để đặt tên file Windows an toàn."""
    clean = re.sub(r'[\\/:*?"<>|\r\n\t]', '_', title.strip())
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:max_len].strip()


class ChapterSplitter:
    """Công cụ bóc tách file HTML / TXT gộp thành các file chương lẻ."""

    def __init__(self, input_file: str, output_dir: Optional[str] = None):
        self.input_file = os.path.abspath(input_file)
        if not output_dir:
            stem = os.path.splitext(os.path.basename(self.input_file))[0]
            parent = os.path.dirname(self.input_file)
            self.output_dir = os.path.join(parent, f"{stem}_tach")
        else:
            self.output_dir = os.path.abspath(output_dir)

    def scan_chapters(self) -> List[Dict[str, Any]]:
        """
        Quét và tìm danh sách chương trong file gộp (HTML hoặc TXT).
        Trả về danh sách dict: [{'index': int, 'title': str, 'content': str}]
        """
        if not os.path.exists(self.input_file):
            return []

        raw_text = read_file_safely(self.input_file)
        if not raw_text.strip():
            return []

        ext = os.path.splitext(self.input_file)[1].lower()
        if ext in (".html", ".htm"):
            chapters = self._scan_html(raw_text)
            if chapters:
                return chapters
            # Nếu parse thẻ HTML không thấy chương thì fallback về scan theo dòng văn bản
            return self._scan_plain_text(raw_text)
        else:
            return self._scan_plain_text(raw_text)

    def _scan_html(self, raw_html: str) -> List[Dict[str, Any]]:
        """Tách chương từ HTML dựa theo cấu trúc thẻ h2, h3, anchor hoặc div chapter."""
        soup = BeautifulSoup(raw_html, "html.parser")
        
        # Bỏ qua phần mục lục (toc) nếu có
        for toc in soup.find_all(id=re.compile(r"toc|menu-chap|list-chapter", re.I)):
            toc.decompose()

        # 1. Tìm các thẻ tiêu đề h2, h3 hoặc h1
        headings = soup.find_all(["h2", "h3", "h1"])
        
        # Lọc ra các heading thực sự là tiêu đề chương
        valid_headings = []
        for h in headings:
            text = h.get_text().strip()
            if text and (COMPILED_TITLE_REGEX.search(text) or len(text) < 80):
                # Bỏ qua các tiêu đề như "Mục lục", "TOC", "Giới thiệu"
                if text.lower() not in ("mục lục", "toc", "table of contents", "thông tin ebook"):
                    valid_headings.append(h)

        if len(valid_headings) >= 2:
            chapters = []
            for i, h in enumerate(valid_headings):
                title = h.get_text().strip()
                # Thu thập nội dung giữa heading này và heading tiếp theo
                content_parts = []
                curr = h.next_sibling
                while curr and (i == len(valid_headings) - 1 or curr != valid_headings[i + 1]):
                    if hasattr(curr, "name"):
                        if curr.name in ["h1", "h2", "h3"]:
                            break
                        # Lấy text hoặc HTML
                        c_text = curr.get_text().strip()
                        if c_text:
                            content_parts.append(c_text)
                    elif isinstance(curr, str) and curr.strip():
                        content_parts.append(curr.strip())
                    curr = curr.next_sibling

                content_str = "\n\n".join(content_parts)
                chapters.append({
                    "index": i + 1,
                    "title": title or f"Chương {i + 1}",
                    "content": content_str
                })
            return chapters

        # 2. Thử tách theo regex split các thẻ tiêu đề
        # Tìm các vị trí xuất hiện của <h2[^>]*>(.*?)</h2>
        h2_pattern = re.compile(r"<h2[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL)
        matches = list(h2_pattern.finditer(raw_html))
        if len(matches) >= 2:
            chapters = []
            for i, m in enumerate(matches):
                title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                start_pos = m.end()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw_html)
                chunk_html = raw_html[start_pos:end_pos]
                
                # Trích xuất text sạch
                c_soup = BeautifulSoup(chunk_html, "html.parser")
                for br in c_soup.find_all(["br", "p"]):
                    br.replace_with("\n" + br.text)
                text = c_soup.get_text().strip()

                chapters.append({
                    "index": i + 1,
                    "title": title or f"Chương {i + 1}",
                    "content": text
                })
            return chapters

        return []

    def _scan_plain_text(self, text: str) -> List[Dict[str, Any]]:
        """Tách chương từ văn bản thuần dựa vào Regex tiêu đề chương."""
        lines = text.splitlines()
        chapters = []
        current_title = ""
        current_lines = []
        chap_idx = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_lines:
                    current_lines.append("")
                continue

            # Kiểm tra xem dòng này có phải là tiêu đề chương không
            is_title = False
            if len(stripped) <= 70 and COMPILED_TITLE_REGEX.search(stripped):
                is_title = True

            if is_title:
                # Đóng gói chương trước đó nếu đã có nội dung
                if current_title and any(l.strip() for l in current_lines):
                    chap_idx += 1
                    chapters.append({
                        "index": chap_idx,
                        "title": current_title,
                        "content": "\n".join(current_lines).strip()
                    })
                    current_lines = []

                current_title = stripped
            else:
                current_lines.append(stripped)

        # Đóng gói chương cuối cùng
        if current_title and any(l.strip() for l in current_lines):
            chap_idx += 1
            chapters.append({
                "index": chap_idx,
                "title": current_title,
                "content": "\n".join(current_lines).strip()
            })
        elif current_lines and not chapters:
            # Trường hợp cả file là 1 chương duy nhất
            chap_idx = 1
            chapters.append({
                "index": chap_idx,
                "title": os.path.splitext(os.path.basename(self.input_file))[0],
                "content": "\n".join(current_lines).strip()
            })

        return chapters

    def split_and_save(self, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> Tuple[int, str]:
        """
        Thực hiện quét, tách chương và lưu thành từng file HTML riêng biệt vào thư mục đích.
        Trả về (số chương đã tách, thư mục đích).
        """
        chapters = self.scan_chapters()
        if not chapters:
            return 0, self.output_dir

        os.makedirs(self.output_dir, exist_ok=True)
        total = len(chapters)

        for ch in chapters:
            idx = ch["index"]
            title = ch["title"]
            content = ch["content"]

            safe_title = clean_title_for_filename(title)
            out_fname = f"{idx:04d}_{safe_title}.html"
            out_fpath = os.path.join(self.output_dir, out_fname)

            # Tạo nội dung HTML chuẩn
            paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
            if paragraphs:
                body_p = "\n".join([f"<p>{p}</p>" for p in paragraphs])
            else:
                body_p = f"<p>{content}</p>"

            html_code = f"""<!DOCTYPE html>
<html lang='zh-CN'>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>{title}</title>
<style>
  body {{
    font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
    line-height: 1.8;
    padding: 24px;
    max-width: 860px;
    margin: 0 auto;
    font-size: 18px;
    color: #222;
    background-color: #fdfdfd;
  }}
  h2 {{
    text-align: center;
    margin-bottom: 24px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e2e8f0;
  }}
  .chapter-content {{
    white-space: normal;
    word-wrap: break-word;
  }}
  .chapter-content p {{
    margin-bottom: 14px;
    text-indent: 1.5em;
  }}
</style>
</head>
<body>
<h2>{title}</h2>
<div class='chapter-content'>
{body_p}
</div>
</body>
</html>
"""
            with open(out_fpath, "w", encoding="utf-8-sig") as f:
                f.write(html_code)

            if progress_callback:
                progress_callback(idx, total, title)

        return total, self.output_dir
