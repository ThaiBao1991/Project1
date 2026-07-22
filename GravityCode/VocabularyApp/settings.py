"""
settings.py — Quản lý cài đặt GitHub và Google Drive cho VocabularyApp
Lưu vào settings.json (local, không commit lên GitHub)
"""

import json
import os
import base64

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")

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
    if not os.path.exists(SETTINGS_PATH):
        return dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge với default để không thiếu key mới
        merged = dict(DEFAULT_SETTINGS)
        merged["github"].update(data.get("github", {}))
        merged["gdrive"].update(data.get("gdrive", {}))
        
        # Giải mã token khi load lên app
        token = merged["github"].get("token")
        if token:
            merged["github"]["token"] = decode_token(token)
            
        return merged
    except Exception:
        return dict(DEFAULT_SETTINGS)


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
