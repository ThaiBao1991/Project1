import os
import json
import base64
import time
import requests
from typing import List, Dict, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
KEYS_FILE = os.path.join(CONFIG_DIR, "gemini_keys.json")

# Đường dẫn settings.json của AskCpl (nằm ở GravityCode/Download/AskCpl)
ASKCPL_SETTINGS_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..", "..", "AskCpl", "settings.json"
    )
)


def encode_token(token: str) -> str:
    """Mã hóa token bảo vệ chuỗi key: đảo ngược rồi base64 (chuẩn tương thích AskCpl)."""
    if not token:
        return ""
    if token.startswith("ENC:"):
        return token
    b64 = base64.b64encode(token[::-1].encode("utf-8")).decode("utf-8")
    return f"ENC:{b64}"


def decode_token(encoded: str) -> str:
    """Giải mã token chuỗi key (chuẩn tương thích AskCpl)."""
    if not encoded or not encoded.startswith("ENC:"):
        return encoded
    try:
        b64 = encoded[4:]
        return base64.b64decode(b64.encode("utf-8")).decode("utf-8")[::-1]
    except Exception:
        return ""


def mask_key(raw_key: str) -> str:
    """Ẩn bớt ký tự key để hiển thị an toàn trên giao diện UI: AIzaSy...xxxx."""
    if not raw_key:
        return ""
    if len(raw_key) <= 10:
        return "***"
    return f"{raw_key[:6]}...{raw_key[-4:]}"


def load_local_keys() -> List[Dict]:
    """Tải danh sách key từ file riêng của dự án: config/gemini_keys.json."""
    if not os.path.exists(KEYS_FILE):
        return []
    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def save_local_keys(keys: List[Dict]) -> bool:
    """Lưu danh sách key vào file config/gemini_keys.json."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(keys, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_active_raw_keys() -> List[Dict]:
    """Lấy danh sách các key đang active với key đã được giải mã thô."""
    items = load_local_keys()
    results = []
    for item in items:
        if item.get("status", "active") == "active":
            raw_key = decode_token(item.get("key", ""))
            if raw_key:
                results.append({
                    "id": item.get("id", ""),
                    "key": raw_key,
                    "email": item.get("email", ""),
                    "note": item.get("note", "")
                })
    return results


def sync_from_askcpl() -> Tuple[int, int]:
    """Đồng bộ nạp keys từ AskCpl settings.json vào config riêng của GetHtmlFromUrl.
    Trả về: (số_key_mới_được_thêm, tổng_số_key_hiện_tại)
    """
    if not os.path.exists(ASKCPL_SETTINGS_PATH):
        return 0, len(load_local_keys())

    try:
        with open(ASKCPL_SETTINGS_PATH, "r", encoding="utf-8") as f:
            askcpl_data = json.load(f)
        
        askcpl_keys = askcpl_data.get("gemini", {}).get("api_keys", [])
        if not askcpl_keys:
            return 0, len(load_local_keys())

        local_keys = load_local_keys()
        existing_raw_keys = {decode_token(k.get("key", "")) for k in local_keys}
        
        added_count = 0
        for ak in askcpl_keys:
            raw = decode_token(ak.get("key", ""))
            if raw and raw not in existing_raw_keys:
                new_item = {
                    "id": ak.get("id") or f"key_{int(time.time()*1000)}_{added_count}",
                    "key": encode_token(raw),
                    "email": ak.get("email", ""),
                    "status": ak.get("status", "active"),
                    "note": ak.get("note", "Nhập từ AskCpl")
                }
                local_keys.append(new_item)
                existing_raw_keys.add(raw)
                added_count += 1

        if added_count > 0:
            save_local_keys(local_keys)

        return added_count, len(local_keys)
    except Exception as e:
        print(f"Lỗi sync_from_askcpl: {e}")
        return 0, len(load_local_keys())


def sync_to_askcpl() -> Tuple[int, int]:
    """Đồng bộ xuất các key mới từ GetHtmlFromUrl sang AskCpl settings.json.
    Trả về: (số_key_mới_được_thêm_vào_askcpl, tổng_số_key_askcpl)
    """
    if not os.path.exists(ASKCPL_SETTINGS_PATH):
        return 0, 0

    try:
        with open(ASKCPL_SETTINGS_PATH, "r", encoding="utf-8") as f:
            askcpl_data = json.load(f)

        if "gemini" not in askcpl_data:
            askcpl_data["gemini"] = {}
        if "api_keys" not in askcpl_data["gemini"]:
            askcpl_data["gemini"]["api_keys"] = []

        askcpl_keys = askcpl_data["gemini"]["api_keys"]
        existing_raw_keys = {decode_token(k.get("key", "")) for k in askcpl_keys}

        local_keys = load_local_keys()
        added_count = 0
        for lk in local_keys:
            raw = decode_token(lk.get("key", ""))
            if raw and raw not in existing_raw_keys:
                askcpl_item = {
                    "id": lk.get("id") or f"key_{int(time.time()*1000)}_{added_count}",
                    "key": encode_token(raw),
                    "email": lk.get("email", ""),
                    "status": lk.get("status", "active"),
                    "note": lk.get("note", "Nhập từ GetHtmlFromUrl"),
                    "cooldown_until": 0
                }
                askcpl_keys.append(askcpl_item)
                existing_raw_keys.add(raw)
                added_count += 1

        if added_count > 0:
            with open(ASKCPL_SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(askcpl_data, f, ensure_ascii=False, indent=2)

        return added_count, len(askcpl_keys)
    except Exception as e:
        print(f"Lỗi sync_to_askcpl: {e}")
        return 0, 0


def sync_merge_two_way() -> Tuple[int, int, int]:
    """Đồng bộ hợp nhất 2 chiều giữa GetHtmlFromUrl và AskCpl.
    Gộp tất cả key của 2 bên để cả 2 ứng dụng đều sở hữu cùng 1 danh sách API keys đầy đủ nhất 100%.
    Trả về: (số_key_mới_vào_local, số_key_mới_vào_askcpl, tổng_số_key_sau_gộp)
    """
    if not os.path.exists(ASKCPL_SETTINGS_PATH):
        return 0, 0, len(load_local_keys())

    try:
        with open(ASKCPL_SETTINGS_PATH, "r", encoding="utf-8") as f:
            askcpl_data = json.load(f)

        if "gemini" not in askcpl_data:
            askcpl_data["gemini"] = {}
        if "api_keys" not in askcpl_data["gemini"]:
            askcpl_data["gemini"]["api_keys"] = []

        askcpl_keys = askcpl_data["gemini"]["api_keys"]
        local_keys = load_local_keys()

        # Map theo raw_key: raw_key -> key_dict
        merged: Dict[str, Dict] = {}

        # 1. Nạp từ AskCpl trước
        for ak in askcpl_keys:
            raw = decode_token(ak.get("key", ""))
            if raw:
                merged[raw] = {
                    "id": ak.get("id") or f"key_{int(time.time()*1000)}_{len(merged)}",
                    "key": encode_token(raw),
                    "email": ak.get("email", ""),
                    "status": ak.get("status", "active"),
                    "note": ak.get("note", ""),
                    "cooldown_until": ak.get("cooldown_until", 0)
                }

        local_raw_before = {decode_token(k.get("key", "")) for k in local_keys}
        askcpl_raw_before = set(merged.keys())

        # 2. Hợp nhất từ Local
        for lk in local_keys:
            raw = decode_token(lk.get("key", ""))
            if not raw:
                continue
            if raw in merged:
                # Cập nhật thông tin tốt hơn nếu local có email thật
                if not merged[raw]["email"] and lk.get("email"):
                    merged[raw]["email"] = lk["email"]
                if not merged[raw]["note"] and lk.get("note"):
                    merged[raw]["note"] = lk["note"]
            else:
                merged[raw] = {
                    "id": lk.get("id") or f"key_{int(time.time()*1000)}_{len(merged)}",
                    "key": encode_token(raw),
                    "email": lk.get("email", ""),
                    "status": lk.get("status", "active"),
                    "note": lk.get("note", ""),
                    "cooldown_until": 0
                }

        # Tạo danh sách hợp nhất chuẩn
        final_list = list(merged.values())

        # Tính số lượng thêm vào mỗi bên
        added_to_local = len(set(merged.keys()) - local_raw_before)
        added_to_askcpl = len(set(merged.keys()) - askcpl_raw_before)

        # Lưu lại cả 2 bên
        save_local_keys(final_list)

        askcpl_data["gemini"]["api_keys"] = final_list
        with open(ASKCPL_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(askcpl_data, f, ensure_ascii=False, indent=2)

        return added_to_local, added_to_askcpl, len(final_list)
    except Exception as e:
        print(f"Lỗi sync_merge_two_way: {e}")
        return 0, 0, len(load_local_keys())


def overwrite_from_askcpl() -> Tuple[int, int]:
    """Ghi đè 100% danh sách key từ AskCpl sang GetHtmlFromUrl.
    Trả về: (số_key_nạp_được, tổng_số_key)
    """
    if not os.path.exists(ASKCPL_SETTINGS_PATH):
        return 0, len(load_local_keys())

    try:
        with open(ASKCPL_SETTINGS_PATH, "r", encoding="utf-8") as f:
            askcpl_data = json.load(f)

        askcpl_keys = askcpl_data.get("gemini", {}).get("api_keys", [])
        if not askcpl_keys:
            return 0, 0

        new_local = []
        for ak in askcpl_keys:
            raw = decode_token(ak.get("key", ""))
            if raw:
                new_local.append({
                    "id": ak.get("id") or f"key_{int(time.time()*1000)}_{len(new_local)}",
                    "key": encode_token(raw),
                    "email": ak.get("email", ""),
                    "status": ak.get("status", "active"),
                    "note": ak.get("note", "Nhập từ AskCpl")
                })

        save_local_keys(new_local)
        return len(new_local), len(new_local)
    except Exception as e:
        print(f"Lỗi overwrite_from_askcpl: {e}")
        return 0, len(load_local_keys())


def overwrite_to_askcpl() -> Tuple[int, int]:
    """Ghi đè 100% danh sách key từ GetHtmlFromUrl sang AskCpl.
    Trả về: (số_key_xuất_được, tổng_số_key)
    """
    if not os.path.exists(ASKCPL_SETTINGS_PATH):
        return 0, 0

    try:
        with open(ASKCPL_SETTINGS_PATH, "r", encoding="utf-8") as f:
            askcpl_data = json.load(f)

        if "gemini" not in askcpl_data:
            askcpl_data["gemini"] = {}

        local_keys = load_local_keys()
        new_askcpl = []
        for lk in local_keys:
            raw = decode_token(lk.get("key", ""))
            if raw:
                new_askcpl.append({
                    "id": lk.get("id") or f"key_{int(time.time()*1000)}_{len(new_askcpl)}",
                    "key": encode_token(raw),
                    "email": lk.get("email", ""),
                    "status": lk.get("status", "active"),
                    "note": lk.get("note", ""),
                    "cooldown_until": 0
                })

        askcpl_data["gemini"]["api_keys"] = new_askcpl
        with open(ASKCPL_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(askcpl_data, f, ensure_ascii=False, indent=2)

        return len(new_askcpl), len(new_askcpl)
    except Exception as e:
        print(f"Lỗi overwrite_to_askcpl: {e}")
        return 0, 0


def remove_keys_from_askcpl(raw_keys_to_remove: List[str]) -> int:
    """Xóa danh sách các raw keys khỏi file settings.json của AskCpl.
    Trả về: số lượng key đã xóa.
    """
    if not os.path.exists(ASKCPL_SETTINGS_PATH) or not raw_keys_to_remove:
        return 0

    try:
        remove_set = set(raw_keys_to_remove)
        with open(ASKCPL_SETTINGS_PATH, "r", encoding="utf-8") as f:
            askcpl_data = json.load(f)

        askcpl_keys = askcpl_data.get("gemini", {}).get("api_keys", [])
        original_count = len(askcpl_keys)
        filtered = [k for k in askcpl_keys if decode_token(k.get("key", "")) not in remove_set]

        removed_count = original_count - len(filtered)
        if removed_count > 0:
            askcpl_data["gemini"]["api_keys"] = filtered
            with open(ASKCPL_SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(askcpl_data, f, ensure_ascii=False, indent=2)

        return removed_count
    except Exception as e:
        print(f"Lỗi remove_keys_from_askcpl: {e}")
        return 0


def validate_key(raw_key: str, timeout: float = 7.0) -> Tuple[bool, str, int]:
    """Kiểm tra xem API key có hoạt động hay không bằng prompt nhẹ 'Hi'.
    Sử dụng endpoint sinh nội dung chuẩn (Blind Fire) với model tốc độ cao gemini-3.5-flash-lite / gemini-3-flash-preview.
    Trả về: (is_valid, message, latency_ms)
    """
    if not raw_key:
        return False, "❌ Key rỗng", 0
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={raw_key}"
    fallback_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={raw_key}"
    payload = {
        "contents": [{"parts": [{"text": "Hi"}]}],
        "generationConfig": {"maxOutputTokens": 2}
    }
    t0 = time.time()
    try:
        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=timeout)
        ms = int((time.time() - t0) * 1000)
        resp_text = resp.text.lower()
        if resp.status_code == 200:
            return True, f"Hoạt động tốt ({ms}ms)", ms
        elif resp.status_code == 429:
            return True, f"⚠ Key sống (Tạm nghẽn hạn ngạch 429)", ms
        elif resp.status_code == 401:
            if "service account" in resp_text and ("deleted" in resp_text or "disabled" in resp_text):
                return False, f"❌ Service account đã bị xóa hoặc vô hiệu hóa (401)", ms
            return False, f"❌ Key không hợp lệ hoặc bị Google khóa (401)", ms
        elif resp.status_code == 400:
            if any(w in resp_text for w in ("api key not valid", "api_key_invalid", "invalid api key", "key not valid", "api_key_deleted")):
                return False, "❌ API key không hợp lệ hoặc đã bị vô hiệu hóa (400)", ms
            t1 = time.time()
            resp2 = requests.post(fallback_url, json=payload, headers={"Content-Type": "application/json"}, timeout=timeout)
            ms2 = int((time.time() - t1) * 1000)
            if resp2.status_code == 200:
                return True, f"Hoạt động tốt ({ms2}ms)", ms2
            return False, f"⚠ HTTP 400: {resp.text[:80]}", ms2
        elif resp.status_code == 403:
            if any(w in resp_text for w in ("deleted", "disabled", "service account", "permission denied", "caller does not have permission")):
                return False, f"❌ Bị từ chối quyền truy cập (403)", ms
            return False, f"❌ Lỗi quyền hạn (403)", ms
        elif resp.status_code in (404, 500, 503):
            t1 = time.time()
            resp2 = requests.post(fallback_url, json=payload, headers={"Content-Type": "application/json"}, timeout=timeout)
            ms2 = int((time.time() - t1) * 1000)
            resp2_text = resp2.text.lower()
            if resp2.status_code == 200:
                return True, f"Hoạt động tốt ({ms2}ms)", ms2
            elif resp2.status_code == 429:
                return True, f"⚠ Key sống (Tạm nghẽn hạn ngạch 429)", ms2
            elif resp2.status_code == 401:
                return False, f"❌ Key không hợp lệ hoặc bị khóa (401)", ms2
            elif resp2.status_code == 403:
                return False, f"❌ Bị từ chối quyền truy cập (403)", ms2
            else:
                return False, f"⚠ Server Google bận ({resp.status_code}) — Key vẫn sống", ms
        else:
            return False, f"⚠ Lỗi HTTP {resp.status_code}", ms
    except requests.exceptions.Timeout:
        try:
            t1 = time.time()
            resp2 = requests.post(fallback_url, json=payload, headers={"Content-Type": "application/json"}, timeout=3.5)
            ms2 = int((time.time() - t1) * 1000)
            if resp2.status_code == 200:
                return True, f"Hoạt động tốt ({ms2}ms)", ms2
        except Exception:
            pass
        return False, "⚠ Timeout > 7s (Mạng lag) — Key chưa xác định", int((time.time() - t0) * 1000)
    except Exception as e:
        return False, f"⚠ Lỗi kết nối: {e}", int((time.time() - t0) * 1000)
