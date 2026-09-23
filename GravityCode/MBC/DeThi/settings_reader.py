# -*- coding: utf-8 -*-
"""
Module: settings_reader.py
Mục đích: Đọc API Keys Gemini đã mã hóa từ settings.json của AskCpl.
Không phụ thuộc GUI/Tkinter. Có thể chạy độc lập trong DeThi.
"""

import json
import os
import base64
from typing import List, Dict

# Đường dẫn cố định tới settings.json của AskCpl (cùng máy)
# DeThi path: .../GravityCode/MBC/DeThi
# AskCpl path: .../GravityCode/Download/AskCpl
ASKCPL_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..",        # DeThi -> MBC -> GravityCode
    "Download", "AskCpl"
))
ASKCPL_SETTINGS_PATH = os.path.join(ASKCPL_DIR, "settings.json")


def decode_token(encoded: str) -> str:
    """Giải mã API key dạng ENC:... bằng thuật toán base64 + đảo chuỗi."""
    if not encoded or not encoded.startswith("ENC:"):
        return encoded
    try:
        b64 = encoded[4:]
        return base64.b64decode(b64.encode("utf-8")).decode("utf-8")[::-1]
    except Exception:
        return ""


def load_gemini_keys(settings_path: str = None) -> List[Dict]:
    """
    Đọc danh sách Gemini API keys từ settings.json của AskCpl.
    Tự động giải mã token ENC:...
    Trả về list các dict: [{key, email, status, ...}, ...]
    """
    path = settings_path or ASKCPL_SETTINGS_PATH
    path = os.path.normpath(path)

    if not os.path.exists(path):
        # Thử tìm trực tiếp trong cùng thư mục (nếu chạy từ AskCpl)
        fallback = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        if os.path.exists(fallback):
            path = fallback
        else:
            print(f"[settings_reader] Không tìm thấy settings.json tại: {path}")
            return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[settings_reader] Lỗi đọc settings.json: {e}")
        return []

    gemini_cfg = data.get("gemini", {})
    api_keys = gemini_cfg.get("api_keys", [])

    # Giải mã từng key
    decoded_keys = []
    for item in api_keys:
        raw = item.get("key", "")
        decoded = decode_token(raw)
        if decoded:
            entry = dict(item)
            entry["key"] = decoded
            entry.setdefault("status", "active")
            entry.setdefault("email", "unknown")
            decoded_keys.append(entry)

    # Nếu danh sách trống, thử lấy api_key đơn
    if not decoded_keys:
        single = gemini_cfg.get("api_key", "")
        decoded_single = decode_token(single)
        if decoded_single:
            decoded_keys.append({
                "key": decoded_single,
                "email": "default",
                "status": "active"
            })

    return decoded_keys


def get_active_model_list() -> List[str]:
    """Đọc danh sách model ưu tiên từ settings.json của AskCpl."""
    path = os.path.normpath(ASKCPL_SETTINGS_PATH)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        models = data.get("gemini", {}).get("model_priority", [])
        return [m["name"] for m in models if m.get("enabled", True) and m.get("name")]
    except Exception:
        return []


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    keys = load_gemini_keys()
    print(f"Đọc được {len(keys)} API key(s):")
    for k in keys:
        disp = k['key'][:12] + "..." if len(k['key']) > 12 else k['key']
        print(f"  - [{k.get('status','?')}] {k.get('email','?')}: {disp}")
    models = get_active_model_list()
    print(f"\nDanh sách model: {models}")
