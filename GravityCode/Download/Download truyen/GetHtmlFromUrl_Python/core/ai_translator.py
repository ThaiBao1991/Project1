import os
import re
import json
import time
import base64
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger("ai_translator")

# Default fallback models in priority order
DEFAULT_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-flash-latest"
]

# Path to AskCpl settings if present
ASKCPL_SETTINGS_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..", "..", "AskCpl", "settings.json"
    )
)

def decode_token(encoded: str) -> str:
    """Giải mã token kiểu AskCpl: ENC:<base64-reversed-string>"""
    if not encoded or not str(encoded).startswith("ENC:"):
        return encoded
    try:
        b64 = encoded[4:]
        return base64.b64decode(b64.encode("utf-8")).decode("utf-8")[::-1]
    except Exception:
        return ""

def load_askcpl_keys() -> List[str]:
    """Tự động tải danh sách Gemini API Key từ AskCpl settings.json nếu có."""
    keys = []
    if not os.path.exists(ASKCPL_SETTINGS_PATH):
        return keys
    try:
        with open(ASKCPL_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        gem = data.get("gemini", {})
        
        # Single key
        single_key = gem.get("api_key", "")
        if single_key:
            dec = decode_token(single_key)
            if dec and dec not in keys:
                keys.append(dec)
                
        # List keys
        list_keys = gem.get("api_keys", [])
        for item in list_keys:
            raw_k = item.get("key", "")
            if raw_k:
                dec = decode_token(raw_k)
                if dec and dec not in keys:
                    keys.append(dec)
    except Exception as e:
        logger.warning(f"Lỗi đọc keys từ AskCpl settings: {e}")
    return keys


class GlossaryManager:
    """Quản lý từ điển thuật ngữ (nhân vật, môn phái, vũ khí, địa danh) cho truyện."""
    def __init__(self, glossary_file: str):
        self.glossary_file = glossary_file
        self.data: Dict[str, Dict[str, str]] = {
            "characters": {},
            "sects": {},
            "weapons": {},
            "locations": {},
            "others": {}
        }
        self.load()

    def load(self):
        if os.path.exists(self.glossary_file):
            try:
                with open(self.glossary_file, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, dict):
                        for cat in ["characters", "sects", "weapons", "locations", "others"]:
                            if cat in content and isinstance(content[cat], dict):
                                self.data[cat] = content[cat]
            except Exception as e:
                logger.error(f"Lỗi load glossary {self.glossary_file}: {e}")

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.glossary_file), exist_ok=True)
            with open(self.glossary_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi save glossary {self.glossary_file}: {e}")

    def add_terms(self, new_terms: Dict[str, Any]):
        """Cập nhật các thuật ngữ mới vào từ điển."""
        if not isinstance(new_terms, dict):
            return
        updated = False
        for cat in ["characters", "sects", "weapons", "locations", "others"]:
            terms = new_terms.get(cat, {})
            if isinstance(terms, dict):
                for zh, vi in terms.items():
                    zh_str = str(zh).strip()
                    vi_str = str(vi).strip()
                    if zh_str and vi_str and zh_str not in self.data[cat]:
                        self.data[cat][zh_str] = vi_str
                        updated = True
        if updated:
            self.save()

    def format_for_prompt(self, max_items_per_cat: int = 100) -> str:
        """Tạo chuỗi văn bản danh mục thuật ngữ chèn vào prompt AI."""
        lines = []
        cat_names = {
            "characters": "Nhân vật",
            "sects": "Tông môn / Thế lực",
            "weapons": "Vũ khí / Pháp bảo / Công pháp",
            "locations": "Địa danh",
            "others": "Thuật ngữ khác"
        }
        has_any = False
        for cat, label in cat_names.items():
            items = self.data.get(cat, {})
            if items:
                has_any = True
                pairs = [f"{zh} -> {vi}" for zh, vi in list(items.items())[:max_items_per_cat]]
                lines.append(f"- {label}: " + ", ".join(pairs))
        if not has_any:
            return "(Chưa có thuật ngữ lưu trữ. Hãy tự động phát hiện và đề xuất các thuật ngữ mới trong chương này)."
        return "\n".join(lines)


class TranslateProgress:
    """Quản lý trạng thái tiến trình dịch truyện (resume state + rolling summary)."""
    def __init__(self, progress_file: str):
        self.progress_file = progress_file
        self.data = {
            "last_translated_file": "",
            "last_summary": "",
            "summaries": {},     # filename -> summary
            "translated_files": [] # list of filenames completed
        }
        self.load()

    def load(self):
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if isinstance(saved, dict):
                        self.data.update(saved)
            except Exception as e:
                logger.error(f"Lỗi load progress {self.progress_file}: {e}")

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi save progress {self.progress_file}: {e}")

    def mark_completed(self, filename: str, summary: str = ""):
        if filename not in self.data["translated_files"]:
            self.data["translated_files"].append(filename)
        self.data["last_translated_file"] = filename
        if summary:
            self.data["last_summary"] = summary
            self.data["summaries"][filename] = summary
        self.save()

    def is_completed(self, filename: str) -> bool:
        return filename in self.data["translated_files"]


class GeminiTranslator:
    """Engine dịch thuật sử dụng Google Gemini API với key rotation, pacing an toàn, glossary & context."""

    def __init__(self, api_keys: List[str], models: Optional[List[str]] = None, pace_seconds: float = 3.5):
        self.api_keys = [k.strip() for k in api_keys if k and k.strip()]
        self.models = models or list(DEFAULT_MODELS)
        self.pace_seconds = max(2.0, pace_seconds)
        self._current_key_idx = 0
        self._last_call_time = 0.0
        self.is_stopped = False

    def stop(self):
        self.is_stopped = True

    def _get_next_key(self) -> str:
        if not self.api_keys:
            return ""
        key = self.api_keys[self._current_key_idx % len(self.api_keys)]
        self._current_key_idx += 1
        return key

    def _wait_pacing(self):
        """Giữ khoảng cách thời gian an toàn giữa 2 request để tránh 429 Too Many Requests."""
        elapsed = time.time() - self._last_call_time
        wait = self.pace_seconds + random.uniform(0.2, 0.8) - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_call_time = time.time()

    def _call_api_with_retry(self, prompt: str, timeout: int = 45) -> Tuple[bool, str, str]:
        """
        Gọi Gemini REST API với luân phiên model và API key.
        Trả về (success, raw_text, error_message)
        """
        if not self.api_keys:
            return False, "", "Không có API Key nào được cấu hình."

        tried_keys = 0
        max_key_tries = len(self.api_keys) * 2

        while tried_keys < max_key_tries and not self.is_stopped:
            api_key = self._get_next_key()
            tried_keys += 1

            for model in self.models:
                if self.is_stopped:
                    return False, "", "Đã dừng bởi người dùng."

                self._wait_pacing()
                url = (f"https://generativelanguage.googleapis.com/v1beta/"
                       f"models/{model}:generateContent?key={api_key}")

                headers = {"Content-Type": "application/json"}
                body = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 8192
                    }
                }

                try:
                    resp = requests.post(url, headers=headers, json=body, timeout=timeout)
                    status = resp.status_code

                    if status == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            text = "".join(p.get("text", "") for p in parts)
                            if text.strip():
                                return True, text, ""
                        return False, "", "API trả về kết quả rỗng."

                    elif status == 429:
                        # Rate limit: thử key tiếp theo
                        logger.warning(f"Key ...{api_key[-6:]} gặp 429 Rate Limit trên model {model}. Đổi key...")
                        break # Break model loop to rotate key

                    elif status in (400, 403, 401):
                        err_msg = resp.text[:200]
                        logger.warning(f"Lỗi {status} với key ...{api_key[-6:]}: {err_msg}")
                        break # Key invalid or expired, try next key

                    elif status in (500, 503):
                        logger.warning(f"Model {model} lỗi server {status}. Thử model fallback...")
                        continue # Try next model

                    else:
                        logger.warning(f"Lỗi HTTP {status} từ Gemini API. {resp.text[:150]}")

                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout khi gọi model {model}. Thử model tiếp theo...")
                    continue
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Lỗi mạng khi gọi Gemini API ({model}): {e}")
                    time.sleep(1.0)
                    continue

        return False, "", "Tất cả API keys / models đều thất bại hoặc bị giới hạn lượt gọi."

    def translate_chapter(self, title_zh: str, content_zh: str,
                          glossary: GlossaryManager,
                          previous_summary: str = "") -> Dict[str, Any]:
        """
        Thực hiện dịch 1 chương truyện tiếng Trung sang tiếng Việt:
        - Sử dụng glossary hiện tại để nhất quán tên nhân vật, môn phái, vũ khí, địa danh
        - Dùng rolling summary để AI nắm bối cảnh, xưng hô phù hợp
        - Nhận về: title_vi, content_vi, new_terms, chapter_summary
        """
        glossary_text = glossary.format_for_prompt()
        prev_summary_text = previous_summary.strip() if previous_summary else "(Đây là chương bắt đầu hoặc chưa có tóm tắt chương trước)."

        prompt = f"""Bạn là dịch giả dịch tiểu thuyết tiếng Trung sang tiếng Việt chuyên nghiệp hàng đầu.
Nhiệm vụ của bạn là dịch chương truyện sau đây sang tiếng Việt với văn phong mượt mà, thuần Việt, chuẩn phong cách tiên hiệp/kiếm hiệp/huyền huyễn/đô thị, giữ đúng cách xưng hô theo ngữ cảnh (huynh đệ, sư đồ, phụ tử, tiền bối, vãn bối, v.v.).

[QUY TẮC BẮT BUỘC]:
1. TUÂN THỦ TỪ ĐIỂN THUẬT NGỮ CỐ ĐỊNH: Bắt buộc dùng đúng bản dịch tiếng Việt cho các danh từ riêng đã có trong danh mục dưới đây. Tuyệt đối không tự ý đổi tên nhân vật hay vũ khí thành từ khác.
{glossary_text}

2. BỐI CẢNH CÁC CHƯƠNG TRƯỚC (Dùng để định hình đại từ xưng hô và mạch truyện liền mạch):
{prev_summary_text}

3. DỊCH ĐẦY ĐỦ VÀ CHÍNH XÁC: Dịch trọn vẹn từng câu từng đoạn của nội dung chương, không tóm lược, không cắt xén, chia đoạn văn rõ ràng bằng các dòng trống.

4. BẢNG THUẬT NGỮ MỚI & TÓM TẮT CHƯƠNG:
- Phát hiện bất kỳ tên nhân vật mới, môn phái mới, vũ khí/pháp bảo mới, địa danh mới xuất hiện trong chương này và phiên âm Hán-Việt chuẩn xác.
- Viết 2-3 câu tóm tắt diễn biến then chốt của chương này làm tư liệu cho chương tiếp theo.

5. ĐỊNH DẠNG KẾT QUẢ ĐẦU RA:
Trả về duy nhất định dạng JSON hợp lệ theo cấu trúc sau (không kèm lời chào hay giải thích ngoài JSON):
```json
{{
  "title_vi": "Tiêu đề tiếng Việt của chương",
  "content_vi": "Nội dung dịch tiếng Việt đầy đủ các đoạn văn...",
  "new_terms": {{
    "characters": {{ "tên tiếng Trung": "Tên tiếng Việt Hán Việt" }},
    "sects": {{ "tên tiếng Trung": "Tên tiếng Việt Hán Việt" }},
    "weapons": {{ "tên tiếng Trung": "Tên tiếng Việt Hán Việt" }},
    "locations": {{ "tên tiếng Trung": "Tên tiếng Việt Hán Việt" }},
    "others": {{ "tên tiếng Trung": "Tên tiếng Việt Hán Việt" }}
  }},
  "summary": "Tóm tắt 2-3 câu cốt truyện chính của chương này."
}}
```

[NỘI DUNG CHƯƠNG TIẾNG TRUNG CẦN DỊCH]:
TIÊU ĐỀ: {title_zh}
NỘI DUNG:
{content_zh}
"""

        success, raw_resp, err_msg = self._call_api_with_retry(prompt)
        if not success:
            raise RuntimeError(err_msg or "Lỗi dịch chương với Gemini API.")

        # Parse JSON output
        parsed = self._parse_translation_response(raw_resp, title_zh, content_zh)
        return parsed

    def _parse_translation_response(self, raw_resp: str, default_title_zh: str, default_content_zh: str) -> Dict[str, Any]:
        """Trích xuất và chuẩn hóa dữ liệu JSON trả về từ Gemini."""
        text = raw_resp.strip()

        # Remove markdown code blocks if present
        if "```json" in text:
            m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if m:
                text = m.group(1).strip()
        elif "```" in text:
            m = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
            if m:
                text = m.group(1).strip()

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return {
                    "title_vi": str(data.get("title_vi", "")).strip() or default_title_zh,
                    "content_vi": str(data.get("content_vi", "")).strip(),
                    "new_terms": data.get("new_terms", {}),
                    "summary": str(data.get("summary", "")).strip()
                }
        except Exception:
            pass

        # Fallback parsing nếu model trả về JSON bị lỗi format ký tự đặc biệt
        title_vi = default_title_zh
        m_title = re.search(r'"title_vi"\s*:\s*"([^"]+)"', text)
        if m_title:
            title_vi = m_title.group(1)

        summary_vi = ""
        m_sum = re.search(r'"summary"\s*:\s*"([^"]+)"', text)
        if m_sum:
            summary_vi = m_sum.group(1)

        # Trích content_vi giữa "content_vi": "..." và ", "new_terms" hoặc "summary"
        content_vi = ""
        m_content = re.search(r'"content_vi"\s*:\s*"(.*?)"\s*,\s*"(?:new_terms|summary)"', text, re.DOTALL)
        if m_content:
            content_vi = m_content.group(1).replace("\\n", "\n").replace('\\"', '"')
        else:
            # Fallback: Lấy toàn bộ text làm nội dung
            content_vi = raw_resp

        return {
            "title_vi": title_vi,
            "content_vi": content_vi,
            "new_terms": {},
            "summary": summary_vi
        }


def extract_chapter_from_html(file_path: str) -> Tuple[str, str]:
    """
    Trích xuất tiêu đề và văn bản thuần túy của chương từ file HTML tiếng Trung.
    Đọc với encoding UTF-8 / GB18030 an toàn.
    """
    raw_html = ""
    for enc in ["utf-8-sig", "utf-8", "gb18030", "gbk", "latin1"]:
        try:
            with open(file_path, "r", encoding=enc) as f:
                raw_html = f.read()
                if raw_html:
                    break
        except Exception:
            continue

    if not raw_html:
        return "", ""

    soup = BeautifulSoup(raw_html, "html.parser")

    # Title extraction
    title = ""
    h2_tag = soup.find("h2")
    if h2_tag and h2_tag.text.strip():
        title = h2_tag.text.strip()
    elif soup.title and soup.title.text.strip():
        title = soup.title.text.strip()
    else:
        # Fallback from filename
        title = os.path.splitext(os.path.basename(file_path))[0]

    # Content extraction
    content = ""
    content_div = soup.find("div", class_=re.compile(r"chapter-content|content|read-content", re.I))
    if content_div:
        # Replace <br> with newlines
        for br in content_div.find_all(["br", "p"]):
            br.replace_with("\n" + br.text)
        content = content_div.get_text()
    else:
        # Fallback to body
        body = soup.find("body") or soup
        for br in body.find_all(["br", "p"]):
            br.replace_with("\n" + br.text)
        content = body.get_text()

    # Clean redundant whitespaces
    lines = [line.strip() for line in content.split("\n")]
    cleaned_text = "\n".join([line for line in lines if line])

    return title, cleaned_text


def save_translated_chapter(output_file: str, title_vi: str, content_vi: str):
    """Lưu chương đã dịch ra file HTML chuẩn tiếng Việt."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Format paragraphs
    paragraphs = [p.strip() for p in content_vi.split("\n") if p.strip()]
    if paragraphs:
        body_html = "\n".join([f"<p>{p}</p>" for p in paragraphs])
    else:
        body_html = f"<p>{content_vi}</p>"

    html_content = f"""<!DOCTYPE html>
<html lang='vi'>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>{title_vi}</title>
<style>
  body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.8;
    padding: 24px;
    max-width: 860px;
    margin: 0 auto;
    font-size: 18px;
    color: #222;
    background-color: #fdfdfd;
  }}
  h2 {{
    color: #1a365d;
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
<h2>{title_vi}</h2>
<div class='chapter-content'>
{body_html}
</div>
</body>
</html>
"""
    with open(output_file, "w", encoding="utf-8-sig") as f:
        f.write(html_content)
