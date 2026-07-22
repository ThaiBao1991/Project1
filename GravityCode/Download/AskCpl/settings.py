import json
import os
import base64
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "github": {
        "username": "",
        "token": "",
        "repo_name": "",
        "pages_url": ""
    },
    "editor": {
        "ex_dir": "",
        "ex_file": "",
        "note_dir": "",
        "note_file": ""
    },
    "server": {
        "host": get_local_ip(),
        "port": 5678
    },
    "gemini": {
        "api_key": "",
        "api_keys": [],
        "last_roadmap": "",
        "last_doc_dir": "",
        "last_out_dir": ""
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
        
        merged = dict(DEFAULT_SETTINGS)
        if "github" in data:
            merged["github"].update(data["github"])
        if "editor" in data:
            merged["editor"].update(data["editor"])
        if "server" in data:
            merged["server"].update(data["server"])
            
            # Tự động ghi đè IP nếu đang là 127.0.0.1 để tránh bị chặn
            if merged["server"].get("host") == "127.0.0.1":
                merged["server"]["host"] = get_local_ip()
                
        if "gemini" in data:
            merged["gemini"].update(data["gemini"])
        
        # Giải mã token khi load lên app
        token = merged["github"].get("token")
        if token:
            merged["github"]["token"] = decode_token(token)
            
        gemini_api = merged["gemini"].get("api_key")
        if gemini_api:
            merged["gemini"]["api_key"] = decode_token(gemini_api)
            
        # Đảm bảo mảng api_keys có tồn tại
        if "api_keys" not in merged["gemini"]:
            merged["gemini"]["api_keys"] = []
            
        # Tự động di chuyển api_key cũ vào danh sách nếu danh sách trống
        if merged["gemini"]["api_key"] and len(merged["gemini"]["api_keys"]) == 0:
            merged["gemini"]["api_keys"].append({
                "key": merged["gemini"]["api_key"],
                "email": "Chưa đặt tên",
                "status": "active",
                "reset_time": 0
            })
            
        # Giải mã từng key trong danh sách
        for item in merged["gemini"]["api_keys"]:
            if item.get("key"):
                item["key"] = decode_token(item["key"])
            
        return merged
    except Exception:
        return dict(DEFAULT_SETTINGS)

def save_settings(settings: dict):
    # Deep copy để không làm thay đổi state trên RAM của app
    data_to_save = json.loads(json.dumps(settings))
    token = data_to_save.get("github", {}).get("token")
    if token:
        data_to_save["github"]["token"] = encode_token(token)
        
    gemini_api = data_to_save.get("gemini", {}).get("api_key")
    if gemini_api:
        data_to_save["gemini"]["api_key"] = encode_token(gemini_api)
        
    # Mã hóa từng key trong api_keys trước khi lưu
    if "gemini" in data_to_save and "api_keys" in data_to_save["gemini"]:
        for item in data_to_save["gemini"]["api_keys"]:
            if item.get("key"):
                item["key"] = encode_token(item["key"])
        
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)

def get_github_settings() -> dict:
    return load_settings()["github"]

def update_github_settings(**kwargs):
    s = load_settings()
    s["github"].update(kwargs)
    save_settings(s)

def update_editor_settings(**kwargs):
    s = load_settings()
    if "editor" not in s:
        s["editor"] = dict(DEFAULT_SETTINGS["editor"])
    s["editor"].update(kwargs)
    save_settings(s)

def update_gemini_settings(**kwargs):
    s = load_settings()
    if "gemini" not in s:
        s["gemini"] = dict(DEFAULT_SETTINGS["gemini"])
    s["gemini"].update(kwargs)
    save_settings(s)
