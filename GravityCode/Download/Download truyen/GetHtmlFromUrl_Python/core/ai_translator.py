import os
import re
import json
import time
import base64
import random
import logging
import threading
from typing import List, Dict, Any, Optional, Tuple, Set
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger("ai_translator")

# Default fallback models in priority order (Khớp 100% với AskCpl gemini_safe.py)
DEFAULT_MODELS = [
    "gemini-3.5-flash",        # 🥇 Mới nhất — thế hệ 3.5
    "gemini-3-flash-preview",  # 🥈 Rất tốt — preview
    "gemini-flash-latest",     # 🥉 Ổn định — flash latest
    "gemini-3.1-flash-lite",   # 🔵 Nhanh & nhẹ — 3.1 lite
    "gemini-flash-lite-latest" # 🔵 Dự phòng cuối — flash lite
]

# Cấu hình an toàn chuẩn AskCpl (gemini_safe.py / gemini_api_key_handling skill)
PACE_MIN = 3.5
PACE_MAX = 5.0
PACE_JITTER = (0.5, 1.5)          # Jitter ngẫu nhiên phá tần số bot detection
ACCOUNT_COOLDOWN = 3600           # 60 phút nghỉ khi gặp 429 Daily
PER_ACCOUNT_MIN_GAP = 8.0         # Khoảng cách tối thiểu giữa 2 request vào cùng 1 Google account
MAX_ACCOUNT_ATTEMPTS = 3          # Thử tối đa 3 account trước khi nghỉ 15s tránh đốt dồn dập

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

def retry_delay_from(msg: str) -> int:
    """Parse retryDelay (vd: 'retryDelay: 4s' hoặc 'retry in 43.1s') từ message lỗi 429."""
    if not msg:
        return 65
    m = re.search(r'retryDelay["\s:]+([0-9]+(?:\.[0-9]+)?)s?', msg, re.IGNORECASE)
    if not m:
        m = re.search(r'retry in\s+([0-9]+(?:\.[0-9]+)?)s', msg, re.IGNORECASE)
    if m:
        try:
            return int(float(m.group(1))) + 5
        except Exception:
            pass
    return 65

def is_model_restriction(msg: str) -> bool:
    """Kiểm tra lỗi quyền hạn/hạn chế model hoặc model không còn tồn tại trên API version."""
    low = (msg or "").lower()
    markers = (
        "denied access", "has been denied", "no longer available", "is not found",
        "not found for api version", "not supported for generatecontent",
        "does not have access", "access to the model", "permission denied",
        "no longer available to new users",
    )
    return any(m in low for m in markers)

def load_askcpl_key_objects() -> List[Dict[str, Any]]:
    """Tự động tải danh sách Gemini API Key cùng metadata đầy đủ (email, project_id, status) từ AskCpl settings.json."""
    key_objects = []
    if not os.path.exists(ASKCPL_SETTINGS_PATH):
        return key_objects
    try:
        with open(ASKCPL_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        gem = data.get("gemini", {})
        
        seen_keys = set()
        
        # Single key
        single_key = gem.get("api_key", "")
        if single_key:
            dec = decode_token(single_key)
            if dec and dec not in seen_keys:
                seen_keys.add(dec)
                key_objects.append({
                    "key": dec,
                    "email": "default_account@gmail.com",
                    "project_id": "default",
                    "status": "active"
                })
                
        # List keys
        list_keys = gem.get("api_keys", [])
        for item in list_keys:
            raw_k = item.get("key", "")
            if raw_k:
                dec = decode_token(raw_k)
                if dec and dec not in seen_keys:
                    seen_keys.add(dec)
                    obj = dict(item)
                    obj["key"] = dec
                    if not obj.get("email"):
                        obj["email"] = "unknown"
                    if not obj.get("status"):
                        obj["status"] = "active"
                    key_objects.append(obj)
    except Exception as e:
        logger.warning(f"Lỗi đọc keys từ AskCpl settings: {e}")
    return key_objects

def load_askcpl_keys() -> List[str]:
    """Tự động tải danh sách Gemini API Key (dạng chuỗi trần) từ AskCpl settings.json nếu có."""
    return [k["key"] for k in load_askcpl_key_objects() if k.get("key")]

def enrich_key_objects(keys: List[Any]) -> List[Dict[str, Any]]:
    """
    Bổ sung metadata (email, account) cho danh sách key.
    Nếu key truyền vào dạng chuỗi trần, tra cứu trong AskCpl settings để lấy email thật.
    Nếu không tìm thấy, phân phối cụm account giả lập để duy trì luân phiên và giãn cách.
    """
    askcpl_map = {}
    for obj in load_askcpl_key_objects():
        k_val = obj.get("key")
        if k_val:
            askcpl_map[k_val] = obj

    enriched = []
    seen = set()
    for idx, item in enumerate(keys or []):
        if isinstance(item, dict):
            k_val = item.get("key", "").strip()
            if k_val and k_val not in seen:
                seen.add(k_val)
                enriched.append(item)
        elif isinstance(item, str):
            k_val = item.strip()
            if k_val and k_val not in seen:
                seen.add(k_val)
                if k_val in askcpl_map:
                    enriched.append(dict(askcpl_map[k_val]))
                else:
                    enriched.append({
                        "key": k_val,
                        "email": f"account_{(idx % 5) + 1}@custom",
                        "project_id": str(idx + 1),
                        "status": "active"
                    })
    return enriched

class AccountPool:
    """
    Quản lý pool API keys gom cụm theo Google Account (email).
    Chuẩn hóa 100% theo gemini_safe.py của AskCpl:
    - Xoay vòng Round-Robin theo từng Account (tránh gọi dồn vào 1 account).
    - Giữ khoảng cách an toàn PER_ACCOUNT_MIN_GAP (>= 8.0s) trên cùng 1 account.
    - Phân biệt 429 RPM (cooldown 65s) vs 429 Daily (cooldown 60 phút).
    """
    def __init__(self, key_objects: Optional[List[Dict[str, Any]]] = None):
        self._keys: List[Dict[str, Any]] = []
        self._cooldown: Dict[str, int] = {}            # account -> unlock ts
        self._last_account: Optional[str] = None
        self._acct_counters: Dict[str, int] = {}
        self._account_last_used: Dict[str, float] = {} # account -> timestamp of last call
        self._lock = threading.Lock()
        if key_objects:
            self.sync(key_objects)

    def sync(self, key_objects: List[Dict[str, Any]]):
        with self._lock:
            self._keys = list(key_objects or [])

    @staticmethod
    def account_of(key_obj: Dict[str, Any]) -> str:
        return (key_obj.get("email") or "unknown").strip().lower() or "unknown"

    def lock_account(self, key_obj: Optional[Dict[str, Any]] = None, 
                     account: Optional[str] = None, 
                     duration: int = ACCOUNT_COOLDOWN,
                     reason: str = "") -> int:
        acct = account or (self.account_of(key_obj) if key_obj else None)
        if not acct:
            return 0
        until = int(time.time() + duration)
        with self._lock:
            self._cooldown[acct] = until
            for k in self._keys:
                if self.account_of(k) == acct:
                    k["cooldown_until"] = until
                    k["error_msg"] = reason
        return until

    def mark_invalid(self, key_obj: Dict[str, Any], reason: str = "Invalid"):
        with self._lock:
            key_obj["status"] = "invalid"
            key_obj["error_msg"] = reason

    def mark_success(self, key_obj: Dict[str, Any]):
        with self._lock:
            if key_obj.get("status") == "exhausted":
                key_obj["status"] = "active"
            key_obj["last_check_time"] = int(time.time())
            key_obj["error_msg"] = ""

    def account_locked(self, account: str, now: Optional[float] = None) -> bool:
        now = now or time.time()
        with self._lock:
            return self._cooldown.get(account, 0) > now

    def _usable_keys(self, exclude: Set[str]) -> List[Dict[str, Any]]:
        now = time.time()
        usable = []
        for k in self._keys:
            if k.get("status") == "invalid":
                continue
            raw = k.get("key", "")
            if not raw or raw in exclude:
                continue
            acct = self.account_of(k)
            cd_until = max(self._cooldown.get(acct, 0), k.get("cooldown_until", 0))
            if cd_until > now:
                continue
            usable.append(k)
        return usable

    def pick(self, exclude: Optional[Set[str]] = None) -> Optional[Dict[str, Any]]:
        exclude_set = set(exclude or [])
        with self._lock:
            usable = self._usable_keys(exclude_set)
            if not usable:
                return None

            groups: Dict[str, List[Dict[str, Any]]] = {}
            for k in usable:
                groups.setdefault(self.account_of(k), []).append(k)

            names = sorted(groups.keys())
            if not names:
                return None

            # Chọn account kế tiếp (Account Round-Robin)
            if self._last_account and self._last_account in names:
                idx = (names.index(self._last_account) + 1) % len(names)
            else:
                idx = 0
            acct = names[idx]

            # Kiểm tra khoảng cách an toàn PER_ACCOUNT_MIN_GAP (>= 8.0s) trên cùng 1 account
            now = time.time()
            last_ts = self._account_last_used.get(acct, 0)
            if (now - last_ts) < PER_ACCOUNT_MIN_GAP and len(names) > 1:
                # Tìm account khác đã qua thời gian giãn cách >= 8.0s
                ready_accts = [a for a in names if (now - self._account_last_used.get(a, 0)) >= PER_ACCOUNT_MIN_GAP]
                if ready_accts:
                    acct = ready_accts[0]

            self._last_account = acct
            keys = groups[acct]
            counter = self._acct_counters.get(acct, 0)
            self._acct_counters[acct] = counter + 1
            picked = keys[counter % len(keys)]
            self._account_last_used[acct] = time.time()
            return picked

_shared_pool_instance: Optional[AccountPool] = None
_shared_pool_lock = threading.Lock()

def get_shared_account_pool(key_objects: Optional[List[Dict[str, Any]]] = None) -> AccountPool:
    global _shared_pool_instance
    with _shared_pool_lock:
        if _shared_pool_instance is None:
            _shared_pool_instance = AccountPool(key_objects)
        elif key_objects:
            _shared_pool_instance.sync(key_objects)
        return _shared_pool_instance


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


def is_model_restriction(msg: str) -> bool:
    """Kiểm tra lỗi model không tồn tại hoặc bị giới hạn theo chuẩn AskCpl."""
    low = (msg or "").lower()
    markers = (
        "denied access", "has been denied", "no longer available", "is not found",
        "not found for api version", "not supported for generatecontent",
        "does not have access", "access to the model", "permission denied",
        "no longer available to new users",
    )
    return any(m in low for m in markers)


def split_text_into_chunks(text: str, max_chars: int = 1500) -> List[str]:
    """
    Chia văn bản dài thành các khối nhỏ an toàn, bảo toàn ranh giới đoạn văn
    để AI dịch trọn vẹn 100% không bao giờ bị cắt cụt hay vượt quá token output.
    """
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n")
    chunks = []
    current_chunk = []
    current_len = 0

    for p in paragraphs:
        p_str = p.strip()
        if not p_str:
            continue

        # Nếu một đoạn đơn lẻ quá dài (> max_chars), chia theo dấu chấm câu
        if len(p_str) > max_chars:
            sentences = re.split(r'([。！？.!?]+)', p_str)
            for i in range(0, len(sentences), 2):
                sent = sentences[i]
                punct = sentences[i + 1] if i + 1 < len(sentences) else ""
                full_sent = sent + punct
                if not full_sent.strip():
                    continue
                if current_len + len(full_sent) > max_chars and current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = [full_sent]
                    current_len = len(full_sent)
                else:
                    current_chunk.append(full_sent)
                    current_len += len(full_sent)
            continue

        if current_len + len(p_str) > max_chars and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [p_str]
            current_len = len(p_str)
        else:
            current_chunk.append(p_str)
            current_len += len(p_str) + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks or [text]


class GeminiTranslator:
    """Engine dịch thuật sử dụng Google Gemini API với Account-Cluster Rotation, Pacing Jitter, Glossary & Context chuẩn AskCpl."""

    def __init__(self, api_keys: List[Any], models: Optional[List[str]] = None, 
                 pace_seconds: float = 3.5, log_callback=None):
        self.raw_keys = api_keys
        self.key_objects = enrich_key_objects(api_keys)
        self.pool = get_shared_account_pool(self.key_objects)
        self.models = list(models or DEFAULT_MODELS)
        self.pace_seconds = max(2.0, pace_seconds)
        self.log_callback = log_callback
        self._last_call_time = 0.0
        self.is_stopped = False

    def _log(self, msg: str):
        logger.info(msg)
        if self.log_callback:
            try:
                self.log_callback(msg)
            except Exception:
                pass

    def stop(self):
        self.is_stopped = True

    def _wait_pacing(self):
        """Giữ khoảng cách an toàn 3.5s - 5.0s + jitter ngẫu nhiên 0.5s - 1.5s để phá tần số bot."""
        base = random.uniform(max(PACE_MIN, self.pace_seconds), max(PACE_MAX, self.pace_seconds + 1.5))
        jitter = random.uniform(*PACE_JITTER)
        elapsed = time.time() - self._last_call_time
        wait = (base + jitter) - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_call_time = time.time()

    def _call_api_with_retry(self, prompt: str, timeout: int = 60) -> Tuple[bool, str, str]:
        """
        Gọi Gemini REST API với Account-Cluster Rotation, Cooldown hàng đợi và Pacing Jitter chuẩn AskCpl.
        Trả về (success, raw_text, error_message)
        """
        if not self.key_objects:
            return False, "", "Không có API Key nào được cấu hình."

        exclude: Set[str] = set()
        account_attempts = 0

        while not self.is_stopped:
            key_obj = self.pool.pick(exclude=exclude)
            if not key_obj:
                # Kiểm tra nếu tất cả account đang tạm thời bị cooldown (ví dụ rate limit 65s)
                if account_attempts > 0:
                    self._log("  ⏳ Các account đang trong thời gian nghỉ tốc độ (cooldown). Nghỉ 10s để hồi phục lưu lượng...")
                    for _ in range(10):
                        if self.is_stopped:
                            return False, "", "Đã dừng bởi người dùng."
                        time.sleep(1.0)
                    exclude.clear()
                    account_attempts = 0
                    continue
                return False, "", "Tất cả API keys/accounts đều bị lỗi, hết hạn hoặc đang trong thời gian khóa."

            api_key = key_obj.get("key", "")
            email = key_obj.get("email", "unknown")
            project_id = key_obj.get("project_id", "")
            short_key = f"...{api_key[-6:]}" if len(api_key) >= 6 else "key"

            for model in list(self.models):
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
                    resp_text = resp.text

                    if status == 200:
                        try:
                            data = resp.json()
                        except Exception:
                            data = {}
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            text = "".join(p.get("text", "") for p in parts)
                            if text.strip():
                                self.pool.mark_success(key_obj)
                                self._log(f"  ✨ [{email} | P{project_id}] Model '{model}' phản hồi thành công!")
                                return True, text, ""
                        self._log(f"  ⚠ Model '{model}' phản hồi rỗng; chuyển model fallback...")
                        continue

                    # 500/503: Quá tải server Google (theo model) -> thử model tiếp theo
                    if status in (500, 503):
                        self._log(f"  ⚠ [{email}] Model '{model}' lỗi server {status} (quá tải). Tự động chuyển model fallback tiếp theo...")
                        continue

                    # 404 hoặc model restriction: model không được hỗ trợ
                    if status == 404 or is_model_restriction(resp_text):
                        self._log(f"  ⚠ Model '{model}' không hỗ trợ hoặc bị giới hạn ({status}). Bỏ qua model này...")
                        if model in self.models and len(self.models) > 1:
                            self.models.remove(model)
                        continue

                    # 429: Too Many Requests
                    if status == 429:
                        low_resp = resp_text.lower()
                        if any(w in low_resp for w in ("perday", "per-day", "daily")):
                            self._log(f"  ⚠ Account '{email}' hết quota ngày (Daily). Khóa account 60 phút, chuyển account khác...")
                            self.pool.lock_account(key_obj, duration=ACCOUNT_COOLDOWN, reason="429 Daily Limit")
                        else:
                            delay = retry_delay_from(resp_text)
                            self._log(f"  ⚡ Account '{email}' chạm giới hạn tốc độ RPM/TPM ({delay}s). Cooldown {delay}s (không xóa key), chuyển account khác...")
                            self.pool.lock_account(key_obj, duration=delay, reason=f"429 RPM ({delay}s)")

                        exclude.add(api_key)
                        account_attempts += 1
                        if account_attempts >= MAX_ACCOUNT_ATTEMPTS:
                            self._log(f"  ⚠ Đã thử {MAX_ACCOUNT_ATTEMPTS} account gặp giới hạn tốc độ. Tạm dừng 15s để server Google giải tỏa lưu lượng...")
                            for _ in range(15):
                                if self.is_stopped:
                                    return False, "", "Đã dừng bởi người dùng."
                                time.sleep(1.0)
                            account_attempts = 0
                        break # Break model loop để đổi account

                    # 401/403: Key lỗi hoặc vô hiệu
                    if status in (401, 403):
                        if any(w in resp_text.lower() for w in ("api_key_invalid", "invalid authentication", "invalid key", "not valid", "not found")):
                            self._log(f"  ✗ Key {short_key} ({email}) không hợp lệ (Invalid). Đánh dấu loại bỏ key này...")
                            self.pool.mark_invalid(key_obj, reason=f"HTTP {status} Invalid Key")
                            exclude.add(api_key)
                            break
                        self._log(f"  ⚠ [{email}] HTTP {status}: {resp_text[:100]}. Thử model tiếp theo...")
                        continue

                    self._log(f"  ⚠ HTTP {status} từ '{model}' ({email}): {resp_text[:120]}. Thử model tiếp theo...")
                    continue

                except requests.exceptions.Timeout:
                    self._log(f"  ⏱ Timeout khi gọi model '{model}' (> {timeout}s). Chuyển model fallback...")
                    continue
                except requests.exceptions.RequestException as e:
                    self._log(f"  🌐 Lỗi kết nối mạng ({type(e).__name__}) trên '{model}'. Thử lại...")
                    time.sleep(1.5)
                    continue

        return False, "", "Tiến trình dịch đã bị dừng hoặc cạn kiệt API keys."

    def translate_chapter(self, title_zh: str, content_zh: str,
                          glossary: GlossaryManager,
                          previous_summary: str = "") -> Dict[str, Any]:
        """
        Thực hiện dịch 1 chương truyện tiếng Trung sang tiếng Việt:
        - Tự động chia đoạn thông minh nếu chương dài (> 1800 chữ Hán)
        - Dịch trọn vẹn từng phần và tự động nối lại thành 1 file duy nhất
        - Sử dụng glossary hiện tại để nhất quán tên nhân vật, môn phái, vũ khí, địa danh
        - Dùng rolling summary để AI nắm bối cảnh, xưng hô phù hợp
        - Nhận về: title_vi, content_vi, new_terms, chapter_summary
        """
        glossary_text = glossary.format_for_prompt()
        prev_summary_text = previous_summary.strip() if previous_summary else "(Đây là chương bắt đầu hoặc chưa có tóm tắt chương trước)."

        # Kiểm tra nếu chương dài -> Tách thành nhiều chunk nhỏ để dịch trọn vẹn
        chunks = split_text_into_chunks(content_zh, max_chars=1400)

        if len(chunks) <= 1:
            return self._translate_single_chunk(title_zh, content_zh, glossary_text, prev_summary_text)

        # Chương dài: Dịch tuần tự từng phần và ghép lại
        self._log(f"  📑 Chương dài ({len(content_zh)} chữ Hán) → Tự động chia thành {len(chunks)} phần nhỏ để dịch trọn vẹn không bị cắt cụt...")
        translated_parts = []
        combined_terms: Dict[str, Dict[str, str]] = {}
        chapter_title_vi = title_zh
        final_summary = ""

        for c_idx, chunk_text in enumerate(chunks):
            if self.is_stopped:
                break
            part_num = c_idx + 1
            self._log(f"    ⏳ Đang dịch phần {part_num}/{len(chunks)} ({len(chunk_text)} ký tự)...")

            is_first = (c_idx == 0)
            is_last = (c_idx == len(chunks) - 1)

            prompt = f"""Bạn là dịch giả dịch tiểu thuyết tiếng Trung sang tiếng Việt chuyên nghiệp.
Nhiệm vụ: Dịch phần {part_num}/{len(chunks)} của chương "{title_zh}" sang tiếng Việt với văn phong mượt mà, chuẩn phong cách tiên hiệp/đô thị.

[QUY TẮC BẮT BUỘC]:
1. TUÂN THỦ TỪ ĐIỂN THUẬT NGỮ CỐ ĐỊNH:
{glossary_text}

2. BỐI CẢNH CÁC CHƯƠNG TRƯỚC (Dùng để định hình đại từ xưng hô):
{prev_summary_text}

3. DỊCH ĐẦY ĐỦ VÀ CHÍNH XÁC: Dịch trọn vẹn từng câu từng đoạn của phần này, tuyệt đối không tóm tắt, không cắt bớt, ngắt đoạn rõ ràng.

4. ĐỊNH DẠNG ĐẦU RA JSON:
Trả về duy nhất JSON:
```json
{{
  "title_vi": "Tiêu đề tiếng Việt của chương",
  "content_vi": "Nội dung dịch tiếng Việt đầy đủ của phần này...",
  "new_terms": {{
    "characters": {{}},
    "sects": {{}},
    "weapons": {{}},
    "locations": {{}},
    "others": {{}}
  }},
  "summary": "Tóm tắt 1-2 câu diễn biến nếu đây là phần cuối của chương, nếu chưa hết để trống."
}}
```

[NỘI DUNG TIẾNG TRUNG PHẦN {part_num}/{len(chunks)}]:
{chunk_text}
"""
            success, raw_resp, err_msg = self._call_api_with_retry(prompt)
            if not success:
                raise RuntimeError(err_msg or f"Lỗi dịch phần {part_num}/{len(chunks)}.")

            parsed = self._parse_translation_response(raw_resp, title_zh, chunk_text)

            if is_first and parsed.get("title_vi"):
                chapter_title_vi = parsed["title_vi"]

            part_content = parsed.get("content_vi", "").strip()
            if part_content:
                translated_parts.append(part_content)

            # Thu thập thuật ngữ mới
            for cat, kvs in parsed.get("new_terms", {}).items():
                if isinstance(kvs, dict):
                    if cat not in combined_terms:
                        combined_terms[cat] = {}
                    combined_terms[cat].update(kvs)

            if is_last or parsed.get("summary"):
                final_summary = parsed.get("summary", final_summary)

        full_content_vi = "\n\n".join(translated_parts)
        self._log(f"  ✅ Đã dịch và ghép nối thành công trọn vẹn {len(chunks)} phần! (Tổng cộng {len(full_content_vi)} ký tự tiếng Việt)")

        return {
            "title_vi": chapter_title_vi,
            "content_vi": full_content_vi,
            "new_terms": combined_terms,
            "summary": final_summary
        }

    def _translate_single_chunk(self, title_zh: str, content_zh: str,
                                glossary_text: str, prev_summary_text: str) -> Dict[str, Any]:
        """Dịch 1 chương có độ dài bình thường trong 1 lần gọi duy nhất."""
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

        return self._parse_translation_response(raw_resp, title_zh, content_zh)

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
                content_str = str(data.get("content_vi", "")).strip()
                content_str = content_str.replace('\\n', '\n').replace('\\"', '"')
                return {
                    "title_vi": str(data.get("title_vi", "")).strip() or default_title_zh,
                    "content_vi": content_str,
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

        # Trích content_vi linh hoạt: giữa "content_vi": "..." và ", "new_terms" hoặc "summary" hoặc đóng ngoặc }
        content_vi = ""
        m_content = re.search(r'"content_vi"\s*:\s*"(.*?)(?:"\s*,\s*"(?:new_terms|summary|title_vi)"|"\s*\}\s*$)', text, re.DOTALL)
        if m_content:
            content_vi = m_content.group(1).replace("\\n", "\n").replace('\\"', '"')
        else:
            m_simple = re.search(r'"content_vi"\s*:\s*"([\s\S]*?)(?:"\s*,\s*"|"\s*\}\s*$)', text)
            if m_simple:
                content_vi = m_simple.group(1).replace("\\n", "\n").replace('\\"', '"')
            else:
                # Fallback cuối: Lấy toàn bộ text nhưng làm sạch sạch sẽ mọi cấu trúc JSON/markdown
                content_vi = raw_resp
                content_vi = re.sub(r'```(?:json)?\s*', '', content_vi)
                content_vi = re.sub(r'```', '', content_vi)
                content_vi = re.sub(r'^\s*\{\s*"title_vi"[^}]*?"content_vi"\s*:\s*"', '', content_vi, flags=re.DOTALL)
                content_vi = re.sub(r'"\s*,\s*"(?:new_terms|summary)"[\s\S]*$', '', content_vi)
                content_vi = re.sub(r'"\s*\}\s*$', '', content_vi)
                content_vi = content_vi.replace('\\n', '\n').replace('\\"', '"').strip()

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
    """
    Lưu nội dung chương đã dịch ra file HTML với template chuẩn,
    font Segoe UI thân thiện, hỗ trợ CSS hiển thị đẹp.
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Giải mã triệt để ký tự \n và \" thô
    content_vi = content_vi.replace('\\n', '\n').replace('\\"', '"')

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
