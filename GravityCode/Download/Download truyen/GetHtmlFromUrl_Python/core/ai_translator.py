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
    "gemini-3.8-flash",        # 🥇 Mới nhất — thế hệ 3.8
    "gemini-3.5-flash-lite",   # ⚡ Siêu tốc & nhẹ — 3.5 lite
    "gemini-3.5-flash",        # 🔴 Mạnh mẽ — 3.5 flash
    "gemini-3-flash-preview",  # 🥈 Rất tốt — preview
    "gemini-flash-latest",     # 🥉 Ổn định — flash latest
    "gemini-flash-lite-latest",# 🔵 Nhanh nhẹ — flash lite
    "gemini-3.1-flash-lite",   # 🔵 3.1 lite
    "gemini-3.7-flash"         # 🟣 Dự phòng — thế hệ 3.7
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

def load_configured_models() -> List[str]:
    """Tự động tải danh sách model ưu tiên:
    1. Ưu tiên đọc từ config/model_priority.json của dự án.
    2. Nếu chưa có -> đọc từ AskCpl settings.json.
    3. Nếu không có -> dùng DEFAULT_MODELS.
    """
    try:
        from core.model_manager import get_active_models
        models = get_active_models()
        if models:
            return models
    except Exception:
        pass
    return load_askcpl_models()

def load_configured_key_objects() -> List[Dict[str, Any]]:
    """Tự động tải danh sách Gemini API Key:
    1. Ưu tiên đọc từ config/gemini_keys.json (kho riêng của GetHtmlFromUrl).
    2. Nếu chưa có -> đọc từ AskCpl settings.json.
    """
    try:
        from core.key_manager import get_active_raw_keys
        local_keys = get_active_raw_keys()
        if local_keys:
            return local_keys
    except Exception:
        pass
    return load_askcpl_key_objects()

def load_askcpl_models() -> List[str]:
    """Tự động tải danh sách model ưu tiên từ AskCpl settings.json nếu có."""
    if os.path.exists(ASKCPL_SETTINGS_PATH):
        try:
            with open(ASKCPL_SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            priority = data.get("gemini", {}).get("model_priority", [])
            active = [m["name"] for m in priority if m.get("enabled", True) and m.get("name")]
            if active:
                return active
        except Exception:
            pass
    return list(DEFAULT_MODELS)


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
        
        # 1. Ưu tiên nạp từ list keys (api_keys) — chứa đầy đủ account thực tế
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
                    
        # 2. Chỉ nạp single key nếu list_keys rỗng
        if not key_objects:
            single_key = gem.get("api_key", "")
            if single_key:
                dec = decode_token(single_key)
                if dec and dec not in seen_keys:
                    seen_keys.add(dec)
                    key_objects.append({
                        "key": dec,
                        "email": "askcpl_primary",
                        "project_id": "1",
                        "status": "active"
                    })
    except Exception as e:
        logger.warning(f"Lỗi đọc keys từ AskCpl settings: {e}")
    return key_objects

def load_askcpl_keys() -> List[str]:
    """Tự động tải danh sách Gemini API Key (dạng chuỗi trần) từ AskCpl settings.json nếu có."""
    return [k["key"] for k in load_askcpl_key_objects() if k.get("key")]

def probe_active_models(api_keys: List[Any], candidate_models: Optional[List[str]] = None, 
                        timeout: float = 6.0, log_callback=None) -> List[str]:
    """
    Kiểm tra nhanh (ping 1-token) các model trong danh sách để chọn ra các model
    thực sự đang online và phản hồi nhanh, loại bỏ các model quá tải (503), lỗi (404/400) hoặc timeout.
    """
    def _log(msg: str):
        logger.info(msg)
        if log_callback:
            try:
                log_callback(msg)
            except Exception:
                pass

    if not api_keys:
        return list(candidate_models or DEFAULT_MODELS)

    # Lấy key active đầu tiên để test
    first_key = ""
    for k in api_keys:
        if isinstance(k, dict) and k.get("key") and k.get("status", "active") == "active":
            first_key = k["key"]
            break
        elif isinstance(k, str) and k.strip():
            first_key = k.strip()
            break

    if not first_key:
        return list(candidate_models or DEFAULT_MODELS)

    cands = list(candidate_models or load_configured_models())
    _log(f"🔍 [Model Probe] Đang kiểm tra phản hồi {len(cands)} model Gemini...")

    alive_models: List[Tuple[str, int]] = []

    payload = {
        "contents": [{"parts": [{"text": "1"}]}],
        "generationConfig": {"maxOutputTokens": 1}
    }
    headers = {"Content-Type": "application/json"}

    for model in cands:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={first_key}"
        t0 = time.time()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            latency = int((time.time() - t0) * 1000)
            if resp.status_code == 200:
                alive_models.append((model, latency))
                _log(f"  ✅ {model}: {latency}ms (Sẵn sàng)")
            elif resp.status_code in (500, 503):
                _log(f"  ⚠ {model}: Quá tải server ({resp.status_code}) -> Tạm loại khỏi danh sách.")
            elif resp.status_code == 404 or is_model_restriction(resp.text):
                _log(f"  ✗ {model}: Không hỗ trợ / Bị giới hạn ({resp.status_code}) -> Loại bỏ.")
            elif resp.status_code == 429:
                _log(f"  ⚡ {model}: Bị rate limit 429 tạm thời.")
            else:
                _log(f"  ⚠ {model}: HTTP {resp.status_code}")
        except requests.exceptions.Timeout:
            _log(f"  ⏱ {model}: Timeout (> {timeout}s) -> Loại bỏ.")
        except Exception as e:
            _log(f"  ✗ {model}: Lỗi kết nối ({type(e).__name__}) -> Bỏ qua.")

    if alive_models:
        alive_models.sort(key=lambda x: x[1])
        result = [m[0] for m in alive_models]
        _log(f"🎯 [Model Probe] Đã chọn {len(result)} model tối ưu: {', '.join(result)}")
        return result

    _log("⚠ [Model Probe] Không test được model nào qua mạng; sử dụng cấu hình mặc định.")
    return cands


def enrich_key_objects(keys: List[Any]) -> List[Dict[str, Any]]:
    """
    Bổ sung metadata (email, account) cho danh sách key.
    Nếu key truyền vào dạng chuỗi trần, tra cứu trong kho riêng của dự án hoặc AskCpl để lấy email thật.
    Nếu không tìm thấy, phân phối cụm account giả lập để duy trì luân phiên và giãn cách.
    """
    known_map = {}
    for obj in load_configured_key_objects():
        k_val = obj.get("key")
        if k_val:
            known_map[k_val] = obj

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
                if k_val in known_map:
                    enriched.append(dict(known_map[k_val]))
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


RE_CJK = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]')

def has_cjk(text: str) -> bool:
    """Kiểm tra chuỗi có chứa ký tự chữ Hán (CJK) hay không."""
    return bool(RE_CJK.search(text)) if text else False


# ─── MỎ NEO ÂM HÁN-VIỆT & CHỐNG ẢO GIÁC PHIÊN ÂM (SINO-VIETNAMESE DISAMBIGUATION) ───
SINO_VIETNAMESE_ANCHORS = {
    "祟": "Toái",    # Pinyin suì: AI hay đọc nhầm thành Súy (nhầm với 帅 shuài) hoặc Sùng (nhầm với 崇)
    "崇": "Sùng",    # Pinyin chóng: hay bị nhầm sang Chung (钟)
    "帅": "Soái",
    "砼": "Đồng",
    "怼": "Đỗi",
    "魃": "Bạt",
    "魑": "Ly",
    "魅": "Mị",
    "魍": "Vọng",
    "魉": "Lượng",
    "饕": "Thao",
    "餮": "Thiết",
    "弑": "Thí",
    "戮": "Lục",
    "枭": "Kiêu",
    "傀": "Khôi",
    "儡": "Lỗi",
    "蛊": "Cổ",
    "冥": "Minh",
    "煞": "Sát",
}

# Bảng tra cứu các biến thể lệch phổ biến cho từng danh xưng để phục vụ tự động đồng bộ (Auto-Reconciliation)
DISAMBIGUATION_ALIASES: Dict[str, List[str]] = {
    "司祟": ["Tư Súy", "Tư Sùng", "Tư Chung", "Tư Tụy", "Tư Tuế"],
    "司天祟": ["Tư Thiên Súy", "Tư Thiên Sùng", "Tư Thiên Chung"],
    "祟": ["Súy", "Sùng", "Chung"]
}


def normalize_han_viet_term(zh: str, vi: str) -> str:
    """
    Chuẩn hóa các âm Hán-Việt bị AI đọc nhầm bính âm Pinyin hoặc nhìn nhầm mặt chữ.
    Ví dụ: 司祟 bị nhầm thành Tư Súy / Tư Chung -> sửa thành Tư Toái.
    """
    normalized_vi = vi.strip()
    if "祟" in zh:
        # Nếu AI dịch thành Súy hoặc Chung do nhầm pinyin hoặc mặt chữ -> sửa thành Toái
        normalized_vi = re.sub(r'\bSúy\b', 'Toái', normalized_vi, flags=re.IGNORECASE)
        normalized_vi = re.sub(r'\bChung\b', 'Toái', normalized_vi, flags=re.IGNORECASE)
    return normalized_vi


def reconcile_text_with_terms(text: str, terms_map: Dict[str, str]) -> str:
    """
    Tự động rà soát và đồng bộ các biến thể tên bị lệch trong đoạn văn bản dịch
    theo danh sách thuật ngữ chuẩn đã chốt.
    """
    if not text or not terms_map:
        return text

    modified_text = text
    for zh, vi in terms_map.items():
        if not zh or not vi:
            continue
        aliases = []
        if zh in DISAMBIGUATION_ALIASES:
            aliases.extend(DISAMBIGUATION_ALIASES[zh])

        for alias in aliases:
            if alias.lower() != vi.lower() and alias in modified_text:
                pattern = r'\b' + re.escape(alias) + r'\b'
                modified_text = re.sub(pattern, vi, modified_text)

    return modified_text


def reconcile_chapter_files(dich_dir: str, glossary: 'GlossaryManager', log_callback=None) -> Dict[str, int]:
    """
    Quét và đồng bộ nhất quán toàn bộ các file HTML chương trong thư mục dịch
    theo từ điển thuật ngữ chuẩn (xóa bỏ toàn bộ các biến thể lệch tên).
    Trả về dict: {"modified_files": int, "total_replacements": int}
    """
    if not os.path.exists(dich_dir):
        return {"modified_files": 0, "total_replacements": 0}

    alias_to_canonical: Dict[str, str] = {}
    for cat in ["characters", "sects", "weapons", "locations", "others"]:
        for zh, vi in glossary.data.get(cat, {}).items():
            if zh in DISAMBIGUATION_ALIASES:
                for alias in DISAMBIGUATION_ALIASES[zh]:
                    if alias.lower() != vi.lower():
                        alias_to_canonical[alias] = vi

    if not alias_to_canonical:
        return {"modified_files": 0, "total_replacements": 0}

    modified_files = 0
    total_replacements = 0

    search_dirs = [dich_dir, os.path.dirname(dich_dir)]
    processed_paths = set()

    for s_dir in search_dirs:
        if not os.path.exists(s_dir):
            continue
        try:
            for fname in os.listdir(s_dir):
                if not (fname.endswith('.html') or fname.endswith('.htm')):
                    continue
                fpath = os.path.join(s_dir, fname)
                if fpath in processed_paths:
                    continue
                processed_paths.add(fpath)

                with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()

                orig_content = content
                file_replacements = 0
                for alias, canonical in alias_to_canonical.items():
                    if alias in content:
                        pattern = r'\b' + re.escape(alias) + r'\b'
                        matches = len(re.findall(pattern, content))
                        if matches > 0:
                            content = re.sub(pattern, canonical, content)
                            file_replacements += matches

                if content != orig_content:
                    with open(fpath, 'w', encoding='utf-8') as fp:
                        fp.write(content)
                    modified_files += 1
                    total_replacements += file_replacements
                    if log_callback:
                        log_callback(f"  ✨ Đồng bộ {fname}: thay thế {file_replacements} vị trí.")
        except Exception as e:
            logger.error(f"Lỗi khi đồng bộ file trong {s_dir}: {e}")

    return {"modified_files": modified_files, "total_replacements": total_replacements}


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

    @staticmethod
    def clean_term(zh: Any, vi: Any) -> Optional[Tuple[str, str]]:
        """
        Làm sạch, chuẩn hóa và tự động sửa lỗi đảo ngược (Auto-Swap) cho cặp thuật ngữ.
        Đảm bảo:
        - Key (zh) BẮT BUỘC chứa chữ Hán (CJK).
        - Value (vi) BẮT BUỘC là tiếng Việt (không được chứa chữ Hán).
        - Tự động chuẩn hóa các âm Hán-Việt bị AI đọc nhầm bính âm Pinyin.
        """
        zh_str = str(zh or "").strip(" \t\r\n'\"{}[]")
        vi_str = str(vi or "").strip(" \t\r\n'\"{}[]")
        if not zh_str or not vi_str or zh_str == vi_str:
            return None

        # Tự động sửa lỗi bị đảo ngược cột: zh không có chữ Hán nhưng vi lại có chữ Hán
        if not has_cjk(zh_str) and has_cjk(vi_str):
            zh_str, vi_str = vi_str, zh_str

        # Sau khi swap, zh bắt buộc phải có chữ Hán
        if not has_cjk(zh_str):
            return None

        # vi không được chứa chữ Hán (nếu vẫn chứa chữ Hán nghĩa là chưa dịch sang tiếng Việt)
        if has_cjk(vi_str):
            return None

        # Tự động chuẩn hóa âm Hán-Việt theo bảng mỏ neo
        vi_str = normalize_han_viet_term(zh_str, vi_str)

        return zh_str, vi_str

    def load(self):
        if os.path.exists(self.glossary_file):
            try:
                with open(self.glossary_file, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, dict):
                        healed = False
                        for cat in ["characters", "sects", "weapons", "locations", "others"]:
                            if cat in content and isinstance(content[cat], dict):
                                cleaned_dict = {}
                                for k, v in content[cat].items():
                                    cleaned = self.clean_term(k, v)
                                    if cleaned:
                                        czh, cvi = cleaned
                                        cleaned_dict[czh] = cvi
                                        if czh != str(k) or cvi != str(v):
                                            healed = True
                                    else:
                                        # Loại bỏ item rác / không hợp lệ
                                        healed = True
                                self.data[cat] = cleaned_dict
                        if healed:
                            logger.info(f"Đã tự động sửa lỗi đảo chiều & chuẩn hóa glossary: {self.glossary_file}")
                            self.save()
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
        """Cập nhật các thuật ngữ mới vào từ điển (có tự động phát hiện đảo ngược và chuẩn hóa)."""
        if not isinstance(new_terms, dict):
            return
        updated = False
        for cat in ["characters", "sects", "weapons", "locations", "others"]:
            terms = new_terms.get(cat, {})
            if isinstance(terms, dict):
                for zh, vi in terms.items():
                    cleaned = self.clean_term(zh, vi)
                    if not cleaned:
                        continue
                    czh, cvi = cleaned
                    if czh not in self.data[cat]:
                        self.data[cat][czh] = cvi
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


# ─── BỘ PHONG CÁCH VĂN PHONG DỊCH THUẬT (TRANSLATION STYLES) ────────────────────
TRANSLATION_STYLES: Dict[str, Dict[str, Any]] = {
    "fluent": {
        "name": "Mượt mà thuần Việt (Đề xuất)",
        "temperature": 0.65,
        "top_p": 0.95,
        "description": "Thoát ý, câu từ uyển chuyển, giàu cảm xúc, xóa bỏ triệt để cấu trúc câu tiếng Trung thô cứng.",
        "system_instruction": """Bạn là dịch giả văn học và biên tập viên tiểu thuyết mạng tiếng Trung sang tiếng Việt chuyên nghiệp hàng đầu.
Nhiệm vụ của bạn là chuyển ngữ tác phẩm sang tiếng Việt với văn phong mượt mà, thuần Việt, chuẩn mực như sách xuất bản, giàu nhạc điệu và cảm xúc.

[BỘ QUY TẮC BÚT PHÁP VĂN HỌC BẮT BUỘC]:
1. TUYỆT ĐỐI KHÔNG DỊCH WORD-BY-WORD (CHỐNG CONVERT):
   - Thoát ly triệt để cấu trúc câu bị động và trật tự ngược của tiếng Trung.
     * Tránh: "Bị hắn một quyền đánh lui..." -> Dịch mượt: "Một quyền của hắn đánh bật đối phương lùi lại..."
     * Tránh: "Được nàng ánh mắt nhìn tới..." -> Dịch mượt: "Chạm phải ánh mắt của nàng..."
   - Lược bỏ từ đệm rườm rà tiếng Trung: "trong lòng không khỏi có chút kinh ngạc" -> "thầm giật mình"; "hướng về phía trước đi đến" -> "bước về phía trước"; "phát sinh biến hóa" -> "biến chuyển".
   - Sử dụng từ láy, từ tượng thanh, tượng hình thuần Việt để miêu tả hành động, biểu cảm, khí thế và cảnh vật.

2. CHỌN LỌC HÁN-VIỆT VÀ THUẦN VIỆT HỢP LÝ:
   - Danh từ riêng, tên nhân vật, môn phái, địa danh, tên chiêu thức, cảnh giới tu luyện: BẮT BUỘC giữ âm Hán-Việt chuẩn mực theo sách vở tự điển (Sino-Vietnamese).
   - TUYỆT ĐỐI KHÔNG dùng bính âm Pinyin tiếng Trung để phiên âm trại âm (Ví dụ: chữ 祟 là Toái/Tụy, cấm phiên âm theo pinyin suì thành Súy; 帅 mới là Soái/Súy; 崇 là Sùng; 钟 là Chung).
   - Tên nhân vật phải nhất quán, biểu đạt đúng tính cách nhân vật (tà phái, chính phái, cao nhân).
   - Từ ngữ miêu tả hành động, trạng thái, tâm lý, đồ vật thường ngày: ƯU TIÊN dùng từ thuần Việt tự nhiên (ví dụ: "sắc mặt âm trầm" -> "vẻ mặt sa sầm", "thân hình khẽ động" -> "khẽ nhích người", "tiến vào gian phòng" -> "bước vào phòng").

3. ĐẠI TỪ XƯNG HÔ LINH HOẠT THEO BỐI CẢNH & THỂ LOẠI:
   - Tuyệt đối không dịch máy móc mọi nhân vật đều xưng "ngươi - ta".
   - Biến hóa đại từ xưng hô phù hợp với địa vị, tuổi tác, quan hệ và thể loại tác phẩm:
     * Tiên hiệp/kiếm hiệp: sư đồ (sư phụ - đồ nhi), đồng môn (huynh - đệ, sư tỷ - sư muội), kẻ thù (ngươi - ta, gã, hắn, y, lão tặc, tiểu tử).
     * Khoa huyễn/học viện/đô thị (như Tu Chân Tứ Vạn Niên): thầy - trò, cậu - tôi, anh - em, mình - bạn, gã - cậu.
   - Lời thoại phải tự nhiên, mang khẩu khí đời thường, thể hiện rõ cá tính nhân vật (ngạo mạn, hài hước, trêu chọc, lạnh lùng, uy nghiêm).

4. XỬ LÝ THÀNH NGỮ VÀ QUÁN NGỮ:
   - Dịch thoát ý hoặc dùng thành ngữ/tục ngữ tiếng Việt tương đương (ví dụ: "hổ khu nhất chấn" -> "người run lên / bừng bừng khí thế", "phách đầu cái não" -> "mắng xối xả", "cẩu huyết" -> "máu chó / tức nghẹn", "trang bức" -> "lên mặt / làm bộ").

5. NGUYÊN TẮC BẢO TOÀN DỮ LIỆU:
   - Dịch trọn vẹn 100% nội dung, không tóm tắt, không tự tiện cắt xén bất kỳ câu đoạn nào.
   - Giữ nguyên cấu trúc phân đoạn văn bản."""
    },
    "classic_xianxia": {
        "name": "Tiên hiệp cổ phong (Nhiều Hán-Việt)",
        "temperature": 0.55,
        "top_p": 0.95,
        "description": "Giữ âm hưởng hùng tráng, sử thi, dùng nhiều từ Hán-Việt cổ phong trong xưng hô, chiêu thức.",
        "system_instruction": """Bạn là một dịch giả tiểu thuyết tiên hiệp, kiếm hiệp cổ điển uyên thâm.
Nhiệm vụ của bạn là chuyển ngữ tác phẩm sang tiếng Việt với văn phong cổ kính, hùng tráng, hào sảng và đậm chất tiên hiệp, kiếm hiệp cổ phong.

[QUY TẮC BÚT PHÁP]:
1. Giữ gìn hệ thống từ ngữ Hán-Việt trang trọng, cổ phong trong miêu tả khí thế, chiêu thức, pháp bảo, cảnh giới, đạo hạnh.
2. Xưng hô chuẩn mực cổ phong: bản tọa, các hạ, đạo hữu, tiền bối, vãn bối, sư huynh, sư đệ, lão phu, tiểu bối.
3. Câu văn uy nghiêm, nhịp điệu dứt khoát, giữ được không khí huyền bí, thâm sâu của giới tu chân.
4. Dịch đầy đủ 100% nội dung, không cắt bớt hay tóm tắt."""
    },
    "literal": {
        "name": "Bám sát nguyên tác (Trung tính)",
        "temperature": 0.35,
        "top_p": 0.90,
        "description": "Dịch sát nghĩa từng câu chữ, trung tính, bảo toàn trật tự câu gốc.",
        "system_instruction": """Bạn là dịch giả trung thực, dịch sát nghĩa văn bản tiểu thuyết tiếng Trung sang tiếng Việt.
Nhiệm vụ của bạn là bám sát cấu trúc ngữ pháp và câu từ của nguyên tác, dịch chính xác, khách quan, không phóng tác thêm thắt, đảm bảo phản ánh đúng 100% từng câu chữ của tác giả."""
    }
}


class GeminiTranslator:
    """Engine dịch thuật sử dụng Google Gemini API với Account-Cluster Rotation, Pacing Jitter, Glossary & Context chuẩn AskCpl."""

    def __init__(self, api_keys: List[Any], models: Optional[List[str]] = None, 
                 pace_seconds: float = 3.5, style: str = "fluent", log_callback=None):
        self.raw_keys = api_keys
        self.key_objects = enrich_key_objects(api_keys)
        self.pool = get_shared_account_pool(self.key_objects)
        self.models = list(models or load_configured_models())
        self._original_models = list(self.models)  # Bản gốc để có thể restore thứ tự
        self.pace_seconds = max(2.0, pace_seconds)
        self.style = style if style in TRANSLATION_STYLES else "fluent"
        style_info = TRANSLATION_STYLES[self.style]
        self.style_name = style_info["name"]
        self.temperature = style_info["temperature"]
        self.top_p = style_info.get("top_p", 0.95)
        self.system_instruction = style_info["system_instruction"]
        self.log_callback = log_callback
        self._last_call_time = 0.0
        self.is_stopped = False
        # Theo dõi model bị giới hạn theo từng account (không xóa khỏi global list)
        self._account_restricted_models: Dict[str, Set[str]] = {}
        # Đếm số lần phản hồi rỗng liên tiếp theo từng model
        self._model_consecutive_empty: Dict[str, int] = {}

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

    def _call_api_with_retry(self, prompt: str, system_instruction: Optional[str] = None, timeout: int = 60) -> Tuple[bool, str, str]:
        """
        Gọi Gemini REST API với Account-Cluster Rotation, Cooldown hàng đợi và Pacing Jitter chuẩn AskCpl.
        Trả về (success, raw_text, error_message)
        """
        if not self.key_objects:
            return False, "", "Không có API Key nào được cấu hình."

        exclude: Set[str] = set()
        account_attempts = 0
        all_empty_rounds = 0      # Đếm số lần toàn bộ models của một account đều rỗng/lỗi nhẹ
        MAX_EMPTY_ROUNDS = 3      # Tối đa 3 account khác nhau đều thất bại thì báo lỗi hẳn

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

            # Lọc model: bỏ qua model bị giới hạn với account này (per-account restriction)
            restricted_for_acct = self._account_restricted_models.get(email, set())
            models_to_try = [m for m in self.models if m not in restricted_for_acct]
            if not models_to_try:
                self._log(f"  ⚠ Tất cả model đều bị giới hạn với account '{email}'. Chuyển account khác...")
                # Thêm tất cả key của account này vào exclude để không bị pick lại trong lượt này
                for k in self.pool._keys:
                    if self.pool.account_of(k) == email:
                        k_val = k.get("key", "")
                        if k_val:
                            exclude.add(k_val)
                account_attempts += 1

                # Kiểm tra nếu toàn bộ account trong pool đều đã bị giới hạn hết model
                has_any_viable_account = any(
                    any(m not in self._account_restricted_models.get(self.pool.account_of(k), set()) for m in self.models)
                    for k in self.pool._keys if k.get("status") != "invalid" and k.get("key") not in exclude
                )
                if not has_any_viable_account and len(exclude) >= len(self.pool._keys):
                    return False, "", "Tất cả tài khoản Google đều đã bị giới hạn toàn bộ danh sách model."

                if account_attempts >= MAX_ACCOUNT_ATTEMPTS:
                    self._log(f"  ⚠ Đã thử {MAX_ACCOUNT_ATTEMPTS} account, nghỉ 15s trước khi tiếp tục...")
                    for _ in range(15):
                        if self.is_stopped:
                            return False, "", "Đã dừng bởi người dùng."
                        time.sleep(1.0)
                    account_attempts = 0
                    exclude.clear()
                continue

            had_real_response = False  # True nếu ít nhất 1 model nhận được HTTP 200 thực sự
            for model in models_to_try:
                if self.is_stopped:
                    return False, "", "Đã dừng bởi người dùng."

                self._wait_pacing()
                url = (f"https://generativelanguage.googleapis.com/v1beta/"
                       f"models/{model}:generateContent?key={api_key}")

                headers = {"Content-Type": "application/json"}
                body: Dict[str, Any] = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": self.temperature,
                        "topP": self.top_p,
                        "maxOutputTokens": 8192
                    },
                    # Tắt toàn bộ safety filter để dịch trọn vẹn văn học cổ điển (tiểu thuyết tu tiên)
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",  "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH",          "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT",    "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HARASSMENT",           "threshold": "BLOCK_NONE"},
                    ]
                }
                sys_inst = system_instruction or self.system_instruction
                if sys_inst:
                    body["systemInstruction"] = {
                        "parts": [{"text": sys_inst}]
                    }

                try:
                    resp = requests.post(url, headers=headers, json=body, timeout=timeout)
                    status = resp.status_code
                    resp_text = resp.text

                    if status == 200:
                        had_real_response = True  # Đã nhận phản hồi thực từ Gemini (dù rỗng)
                        try:
                            data = resp.json()
                        except Exception:
                            data = {}
                        candidates = data.get("candidates", [])
                        if candidates:
                            cand0 = candidates[0]
                            finish_reason = cand0.get("finishReason", "")
                            parts = cand0.get("content", {}).get("parts", [])
                            text = "".join(p.get("text", "") for p in parts)
                            if text.strip():
                                self.pool.mark_success(key_obj)
                                # Reset bộ đếm empty cho model vừa thành công
                                self._model_consecutive_empty[model] = 0
                                self._log(f"  ✨ [{email} | P{project_id}] Model '{model}' phản hồi thành công!")
                                return True, text, ""
                            # Nội dung bị safety filter chặn
                            if finish_reason == "SAFETY":
                                self._log(
                                    f"  🚫 [{email}] Model '{model}' bị Gemini SAFETY FILTER chặn "
                                    f"(finishReason=SAFETY). Chuyển model khác..."
                                )
                                # Safety block: không đếm vào empty_count (lý do khác)
                                continue
                        # Phản hồi rỗng: đếm số lần liên tiếp
                        empty_count = self._model_consecutive_empty.get(model, 0) + 1
                        self._model_consecutive_empty[model] = empty_count
                        if empty_count >= 2 and model in self.models and len(self.models) > 1:
                            self._log(f"  ⚠ Model '{model}' phản hồi rỗng {empty_count} lần liên tiếp → đẩy xuống cuối hàng đợi (sẽ thử lại sau khi qua account khác)...")
                            self.models.remove(model)
                            self.models.append(model)
                        else:
                            self._log(f"  ⚠ Model '{model}' phản hồi rỗng; chuyển model fallback...")
                        continue

                    # 500/503: Quá tải server Google (theo model) → đẩy model xuống cuối danh sách
                    if status in (500, 503):
                        self._log(f"  ⚠ [{email}] Model '{model}' lỗi server {status} (quá tải). Đẩy xuống cuối queue, chờ 10s...")
                        if model in self.models and len(self.models) > 1:
                            self.models.remove(model)
                            self.models.append(model)
                        # Chờ 10s để server bớt tải trước khi thử model tiếp
                        for _ in range(10):
                            if self.is_stopped:
                                return False, "", "Đã dừng bởi người dùng."
                            time.sleep(1.0)
                        continue


                    # 404 hoặc model restriction: ghi nhận per-account, KHÔNG xóa khỏi global list
                    # (Account khác có thể dùng model này tốt bình thường)
                    if status == 404 or is_model_restriction(resp_text):
                        self._log(f"  ⚠ Model '{model}' không hỗ trợ hoặc bị giới hạn ({status}) với account '{email}'. Ghi nhớ per-account, chuyển model khác...")
                        if email not in self._account_restricted_models:
                            self._account_restricted_models[email] = set()
                        self._account_restricted_models[email].add(model)
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
                    self._log(f"  ⏱ Timeout khi gọi model '{model}' (> {timeout}s). Đẩy model xuống cuối hàng đợi fallback...")
                    if model in self.models and len(self.models) > 1:
                        self.models.remove(model)
                        self.models.append(model)
                    continue
                except requests.exceptions.RequestException as e:
                    self._log(f"  🌐 Lỗi kết nối mạng ({type(e).__name__}) trên '{model}'. Thử lại...")
                    time.sleep(1.5)
                    continue

            # Sau khi thử hết toàn bộ models_to_try mà không thành công
            if had_real_response:
                # Ít nhất 1 model nhận được HTTP 200 nhưng nội dung rỗng → đếm empty round thực
                all_empty_rounds += 1
                if all_empty_rounds >= MAX_EMPTY_ROUNDS:
                    return False, "", (
                        f"Tất cả models đều phản hồi rỗng sau {all_empty_rounds} lần thử các account khác nhau. "
                        f"Nội dung có thể bị Gemini safety filter lọc bỏ."
                    )
                self._log(
                    f"  ⚠ Models phản hồi rỗng với account '{email}' (lần {all_empty_rounds}/{MAX_EMPTY_ROUNDS}). "
                    f"Chuyển account khác, thử lại..."
                )
            else:
                # Toàn bộ là 403/restriction/503 — không phải empty thật, không tăng counter
                self._log(
                    f"  ⚠ Không model nào khả dụng với account '{email}' (403/503 restriction). "
                    f"Chuyển account khác..."
                )
            exclude.add(api_key)
            account_attempts += 1
            if account_attempts >= MAX_ACCOUNT_ATTEMPTS:
                self._log(f"  ⚠ Đã thử {MAX_ACCOUNT_ATTEMPTS} account, nghỉ 15s trước khi tiếp tục...")
                for _ in range(15):
                    if self.is_stopped:
                        return False, "", "Đã dừng bởi người dùng."
                    time.sleep(1.0)
                account_attempts = 0
                exclude.clear()

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
            return self._translate_single_chunk(title_zh, content_zh, glossary, glossary_text, prev_summary_text)

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

            prompt = f"""Dịch phần {part_num}/{len(chunks)} của chương "{title_zh}" sang tiếng Việt với văn phong mượt mà, thuần Việt, giàu cảm xúc, xóa bỏ lối dịch convert thô sượng.

[QUY TẮC BẮT BUỘC]:
1. TUÂN THỦ TỪ ĐIỂN THUẬT NGỮ CỐ ĐỊNH: Bắt buộc dùng đúng danh từ riêng dưới đây:
{glossary_text}

2. BỐI CẢNH CÁC CHƯƠNG TRƯỚC (Dùng để định hình đại từ xưng hô):
{prev_summary_text}

3. CHẤT LƯỢNG VĂN PHONG DỊCH:
- Dịch thoát ý, mượt mà, câu văn tự nhiên, tránh cấu trúc câu bị động ngược và từ đệm thừa của tiếng Trung.
- Xưng hô linh hoạt, ăn khớp với thể loại và bối cảnh (thầy - trò, sư tỷ - đệ, cậu - tôi, gã - hắn).
- Ví dụ đối chiếu chất lượng:
  * ❌ Thô cứng (Convert): "Lý Diệu trong lòng chấn động, hướng về phía trước nhìn lại, chỉ thấy một cái to lớn vô cùng hình cầu..."
  * ✅ Mượt mà thuần Việt: "Lý Diệu thầm kinh hãi. Phóng mắt nhìn về phía trước, đập vào mắt hắn là một khối cầu khổng lồ vô song..."

4. DỊCH ĐẦY ĐỦ 100%: Dịch trọn vẹn từng câu từng đoạn của phần này, tuyệt đối không tóm tắt, không cắt bớt, ngắt đoạn rõ ràng.

5. ĐỊNH DẠNG ĐẦU RA JSON & QUY CHUẨN THUẬT NGỮ MỚI:
- Bảng "new_terms": Phát hiện bất kỳ tên nhân vật mới, môn phái mới, vũ khí/pháp bảo mới, địa danh mới xuất hiện trong phần này.
- QUY TẮC BẮT BUỘC CHO THUẬT NGỮ MỚI (new_terms):
  * CẤU TRÚC KEY - VALUE: Khóa (Key) BẮT BUỘC là CHỮ HÁN GỐC trong truyện, Giá trị (Value) là TÊN TIẾNG VIỆT tương ứng. TUYỆT ĐỐI KHÔNG ĐẢO NGƯỢC (Ví dụ đúng: {{"葛强": "Cát Cường"}}, cấm viết ngược: {{"Cát Cường": "葛强"}}).
  * Tên người / Địa danh / Tông môn: Phiên âm Hán-Việt chuẩn xác, viết hoa đúng chính tả (Ví dụ: "楚休红" -> "Sở Hưu Hồng").
  * Chức danh / Nghề nghiệp / Xưng hô đi kèm tên: Dịch nghĩa sang tiếng Việt và đảo trật tự tự nhiên (Ví dụ: "毛校长" -> "Hiệu trưởng Mao", không để thô cứng "Mao hiệu trưởng"; "小李师傅" -> "Bác thợ Lý" hoặc "Sư phụ Lý" tùy ngữ cảnh, cấm dịch thô "Tiểu Lý sư phó").
  * Biệt danh / Pháp hiệu: Giữ âm Hán-Việt hùng tráng nếu là ngoại hiệu tu tiên (Ví dụ: "黑面神" -> "Hắc Diện Thần", "末日战狂" -> "Mạt Nhật Chiến Cuồng").
Trả về duy nhất JSON:
```json
{{
  "title_vi": "Tiêu đề tiếng Việt của chương",
  "content_vi": "Nội dung dịch tiếng Việt đầy đủ của phần này...",
  "new_terms": {{
    "characters": {{ "chữ Hán gốc": "Tên tiếng Việt Hán-Việt" }},
    "sects": {{ "chữ Hán gốc": "Tên tiếng Việt Hán-Việt" }},
    "weapons": {{ "chữ Hán gốc": "Tên tiếng Việt Hán-Việt" }},
    "locations": {{ "chữ Hán gốc": "Tên tiếng Việt Hán-Việt" }},
    "others": {{ "chữ Hán gốc": "Tên tiếng Việt Hán-Việt" }}
  }},
  "summary": "Tóm tắt 1-2 câu diễn biến nếu đây là phần cuối của chương, nếu chưa hết để trống."
}}
```

[NỘI DUNG TIẾNG TRUNG PHẦN {part_num}/{len(chunks)}]:
{chunk_text}
"""
            success, raw_resp, err_msg = self._call_api_with_retry(prompt, system_instruction=self.system_instruction)
            if not success:
                raise RuntimeError(err_msg or f"Lỗi dịch phần {part_num}/{len(chunks)}.")

            parsed = self._parse_translation_response(raw_resp, title_zh, chunk_text)

            if is_first and parsed.get("title_vi"):
                chapter_title_vi = parsed["title_vi"]

            # Cập nhật thuật ngữ mới in-flight ngay lập tức cho các chunk tiếp theo
            new_chunk_terms = parsed.get("new_terms", {})
            if new_chunk_terms and isinstance(new_chunk_terms, dict):
                glossary.add_terms(new_chunk_terms)
                glossary_text = glossary.format_for_prompt()
                for cat, kvs in new_chunk_terms.items():
                    if isinstance(kvs, dict):
                        if cat not in combined_terms:
                            combined_terms[cat] = {}
                        combined_terms[cat].update(kvs)

            part_content = parsed.get("content_vi", "").strip()
            # Intra-chunk reconciliation: Đồng bộ nội bộ chunk theo danh sách terms hiện tại
            all_current_terms = {}
            for cat_data in glossary.data.values():
                all_current_terms.update(cat_data)
            part_content = reconcile_text_with_terms(part_content, all_current_terms)

            if part_content:
                translated_parts.append(part_content)

            if is_last or parsed.get("summary"):
                final_summary = parsed.get("summary", final_summary)

        # Final chapter pass reconciliation: Đảm bảo toàn bộ các phần đều đồng bộ nhất quán
        all_current_terms = {}
        for cat_data in glossary.data.values():
            all_current_terms.update(cat_data)
        full_content_vi = reconcile_text_with_terms("\n\n".join(translated_parts), all_current_terms)
        self._log(f"  ✅ Đã dịch và ghép nối thành công trọn vẹn {len(chunks)} phần! (Tổng cộng {len(full_content_vi)} ký tự tiếng Việt)")

        return {
            "title_vi": chapter_title_vi,
            "content_vi": full_content_vi,
            "new_terms": combined_terms,
            "summary": final_summary
        }

    def _translate_single_chunk(self, title_zh: str, content_zh: str,
                                glossary: GlossaryManager,
                                glossary_text: str, prev_summary_text: str) -> Dict[str, Any]:
        """Dịch 1 chương có độ dài bình thường trong 1 lần gọi duy nhất."""
        prompt = f"""Dịch chương tiểu thuyết sau đây từ tiếng Trung sang tiếng Việt với văn phong mượt mà, thuần Việt, giàu cảm xúc, xóa bỏ lối dịch convert thô sượng.

[QUY TẮC BẮT BUỘC]:
1. TUÂN THỦ TỪ ĐIỂN THUẬT NGỮ CỐ ĐỊNH: Bắt buộc dùng đúng bản dịch tiếng Việt cho các danh từ riêng đã có trong danh mục dưới đây:
{glossary_text}

2. BỐI CẢNH CÁC CHƯƠNG TRƯỚC (Dùng để định hình đại từ xưng hô và mạch truyện liền mạch):
{prev_summary_text}

3. CHẤT LƯỢNG VĂN PHONG DỊCH:
- Dịch thoát ý, mượt mà, câu văn tự nhiên, thuần Việt, tránh cấu trúc câu bị động ngược và từ đệm thừa của tiếng Trung.
- Xưng hô linh hoạt, ăn khớp với thể loại và bối cảnh (thầy - trò, sư tỷ - đệ, cậu - tôi, gã - hắn).
- Ví dụ đối chiếu chất lượng:
  * ❌ Thô cứng (Convert): "Lý Diệu trong lòng chấn động, hướng về phía trước nhìn lại, chỉ thấy một cái to lớn vô cùng hình cầu..."
  * ✅ Mượt mà thuần Việt: "Lý Diệu thầm kinh hãi. Phóng mắt nhìn về phía trước, đập vào mắt hắn là một khối cầu khổng lồ vô song..."

4. DỊCH ĐẦY ĐỦ 100% VÀ CHÍNH XÁC: Dịch trọn vẹn từng câu từng đoạn của nội dung chương, không tóm lược, không cắt xén, chia đoạn văn rõ ràng bằng các dòng trống.

5. BẢNG THUẬT NGỮ MỚI & TÓM TẮT CHƯƠNG:
- Phát hiện bất kỳ tên nhân vật mới, môn phái mới, vũ khí/pháp bảo mới, địa danh mới xuất hiện trong chương này.
- QUY TẮC BẮT BUỘC CHO THUẬT NGỮ MỚI (new_terms):
  * CẤU TRÚC KEY - VALUE: Khóa (Key) BẮT BUỘC là CHỮ HÁN GỐC trong truyện, Giá trị (Value) là TÊN TIẾNG VIỆT tương ứng. TUYỆT ĐỐI KHÔNG ĐẢO NGƯỢC (Ví dụ đúng: {{"葛强": "Cát Cường"}}, cấm viết ngược: {{"Cát Cường": "葛强"}}).
  * Tên người / Địa danh / Tông môn: Phiên âm Hán-Việt chuẩn xác, viết hoa đúng chính tả (Ví dụ: "楚休红" -> "Sở Hưu Hồng").
  * Chức danh / Nghề nghiệp / Xưng hô đi kèm tên: Dịch nghĩa sang tiếng Việt và đảo trật tự tự nhiên (Ví dụ: "毛校长" -> "Hiệu trưởng Mao", không để thô cứng "Mao hiệu trưởng"; "小李师傅" -> "Bác thợ Lý" hoặc "Sư phụ Lý" tùy ngữ cảnh, cấm dịch thô "Tiểu Lý sư phó").
  * Biệt danh / Pháp hiệu: Giữ âm Hán-Việt hùng tráng nếu là ngoại hiệu tu tiên (Ví dụ: "黑面神" -> "Hắc Diện Thần", "末日战狂" -> "Mạt Nhật Chiến Cuồng").
- Viết 2-3 câu tóm tắt diễn biến then chốt của chương này làm tư liệu cho chương tiếp theo.

6. ĐỊNH DẠNG KẾT QUẢ ĐẦU RA:
Trả về duy nhất định dạng JSON hợp lệ theo cấu trúc sau (không kèm lời chào hay giải thích ngoài JSON):
```json
{{
  "title_vi": "Tiêu đề tiếng Việt của chương",
  "content_vi": "Nội dung dịch tiếng Việt đầy đủ các đoạn văn...",
  "new_terms": {{
    "characters": {{ "chữ Hán gốc": "Tên tiếng Việt Hán-Việt" }},
    "sects": {{ "chữ Hán gốc": "Tên tiếng Việt Hán-Việt" }},
    "weapons": {{ "chữ Hán gốc": "Tên tiếng Việt Hán-Việt" }},
    "locations": {{ "chữ Hán gốc": "Tên tiếng Việt Hán-Việt" }},
    "others": {{ "chữ Hán gốc": "Tên tiếng Việt Hán-Việt" }}
  }},
  "summary": "Tóm tắt 2-3 câu cốt truyện chính của chương này."
}}
```

[NỘI DUNG CHƯƠNG TIẾNG TRUNG CẦN DỊCH]:
TIÊU ĐỀ: {title_zh}
NỘI DUNG:
{content_zh}
"""
        success, raw_resp, err_msg = self._call_api_with_retry(prompt, system_instruction=self.system_instruction)
        if not success:
            raise RuntimeError(err_msg or "Lỗi dịch chương với Gemini API.")

        parsed = self._parse_translation_response(raw_resp, title_zh, content_zh)
        new_terms = parsed.get("new_terms", {})
        if new_terms and isinstance(new_terms, dict):
            glossary.add_terms(new_terms)

        all_current_terms = {}
        for cat_data in glossary.data.values():
            all_current_terms.update(cat_data)

        content_vi = reconcile_text_with_terms(parsed.get("content_vi", ""), all_current_terms)
        parsed["content_vi"] = content_vi
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
