"""
settings.py — Quản lý cài đặt GitHub và Google Drive cho VocabularyApp
Lưu vào settings.json (local, không commit lên GitHub)
"""

import json
import os
import copy
import base64

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")

_DEFAULT_MODEL_FALLBACKS = [
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
]

DEFAULT_SETTINGS = {
    "github": {
        "username": "",
        "token": "",
        "repo_name": "VocabularyApp",
        "branch": "main",
        "pages_url": ""
    },
    "gdrive": {
        "connected": False,
        "folder_id_mp3": "",
        "folder_id_mp4": "",
        "root_folder_id": "",
        "root_folder_name": "VocabularyApp"
    },
    "ai": {
        # Để trống = tự dò ../Download/AskCpl/settings.json (dùng chung kho API key)
        "askcpl_settings_path": "",
        "model_priority": [
            {"name": "gemini-3.5-flash",        "enabled": True,  "tier": "S", "note": "Mạnh nhất — Gemini 3.5",       "latency_ms": 0},
            {"name": "gemini-3-flash-preview",  "enabled": True,  "tier": "A", "note": "Rất tốt — Gemini 3 Preview",   "latency_ms": 0},
            {"name": "gemini-flash-latest",     "enabled": True,  "tier": "A", "note": "Ổn định — Flash Latest",       "latency_ms": 0},
            {"name": "gemini-3.1-flash-lite",   "enabled": True,  "tier": "B", "note": "Nhẹ & Nhanh — Gemini 3.1 Lite","latency_ms": 0},
            {"name": "gemini-flash-lite-latest","enabled": True,  "tier": "B", "note": "Dự phòng — Flash Lite Latest", "latency_ms": 0}
        ]
    }
}

def encode_token(token: str) -> str:
    if not token:
        return ""
    if token.startswith("ENC:"):
        return token
    # Đảo ngược chuỗi rồi mã hóa base64
    b64 = base64.b64encode(token[::-1].encode("utf-8")).decode("utf-8")
    return f"ENC:{b64}"

def decode_token(encoded: str) -> str:
    if not encoded or not encoded.startswith("ENC:"):
        return encoded
    try:
        b64 = encoded[4:]
        # Giải mã base64 rồi đảo ngược lại chuỗi ban đầu
        return base64.b64decode(b64.encode("utf-8")).decode("utf-8")[::-1]
    except Exception:
        return ""

def load_settings() -> dict:
    # deepcopy để không mutate DEFAULT_SETTINGS toàn cục khi merge
    if not os.path.exists(SETTINGS_PATH):
        return copy.deepcopy(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge với default để không thiếu key mới
        merged = copy.deepcopy(DEFAULT_SETTINGS)
        merged["github"].update(data.get("github", {}))
        merged["gdrive"].update(data.get("gdrive", {}))
        merged["ai"].update(data.get("ai", {}))
        
        # Giải mã token khi load lên app
        token = merged["github"].get("token")
        if token:
            merged["github"]["token"] = decode_token(token)
            
        return merged
    except Exception:
        return copy.deepcopy(DEFAULT_SETTINGS)


def save_settings(settings: dict):
    # Deep copy để không làm thay đổi state trên RAM của app
    data_to_save = json.loads(json.dumps(settings))
    token = data_to_save.get("github", {}).get("token")
    if token:
        data_to_save["github"]["token"] = encode_token(token)
        
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)


def get_github_settings() -> dict:
    return load_settings()["github"]


def get_gdrive_settings() -> dict:
    return load_settings()["gdrive"]


def update_github_settings(**kwargs):
    s = load_settings()
    s["github"].update(kwargs)
    save_settings(s)


def update_gdrive_settings(**kwargs):
    s = load_settings()
    s["gdrive"].update(kwargs)
    save_settings(s)


def update_ai_settings(**kwargs):
    """Cập nhật một hoặc nhiều key trong section 'ai' rồi lưu."""
    s = load_settings()
    if "ai" not in s:
        s["ai"] = copy.deepcopy(DEFAULT_SETTINGS["ai"])
    s["ai"].update(kwargs)
    save_settings(s)


# ─────────────────────────────────────────────────────────────
# Helper: lấy danh sách model đang enabled theo thứ tự ưu tiên
# ─────────────────────────────────────────────────────────────

def get_active_model_list() -> list:
    """Trả về list tên model đang enabled theo thứ tự ưu tiên.

    Thứ tự ưu tiên đọc cấu hình:
      1. settings.json của VocabularyApp (ai.model_priority)
      2. settings.json của AskCpl (gemini.model_priority) — nếu VocabApp chưa cấu hình
      3. _DEFAULT_MODEL_FALLBACKS — hardcode cứng làm phòng tuyến cuối

    Backward-compatible: nếu không tìm thấy cấu hình nào, trả về list mặc định.
    """
    try:
        s = load_settings()
        priority = s.get("ai", {}).get("model_priority", [])

        # Nếu VocabApp chưa cấu hình model_priority riêng, thử đọc từ AskCpl
        if not priority:
            try:
                askcpl_path = s.get("ai", {}).get("askcpl_settings_path", "")
                if not askcpl_path:
                    askcpl_path = os.path.normpath(
                        os.path.join(BASE_DIR, "..", "Download", "AskCpl", "settings.json")
                    )
                if os.path.exists(askcpl_path):
                    with open(askcpl_path, "r", encoding="utf-8") as f:
                        askcpl_data = json.load(f)
                    priority = askcpl_data.get("gemini", {}).get("model_priority", [])
            except Exception:
                priority = []

        if not priority:
            return list(_DEFAULT_MODEL_FALLBACKS)

        enabled = [m["name"] for m in priority if m.get("enabled", True) and m.get("name")]
        return enabled if enabled else list(_DEFAULT_MODEL_FALLBACKS)
    except Exception:
        return list(_DEFAULT_MODEL_FALLBACKS)
