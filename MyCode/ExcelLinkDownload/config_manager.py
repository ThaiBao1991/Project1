# config_manager.py
import json
import os
from config import DEFAULT_SAVE_FOLDER

CONFIG_FILE = "app_config.json"

def load_config():
    """Đọc cấu hình từ file"""
    default_config = {
        "last_save_folder": DEFAULT_SAVE_FOLDER,
        "last_excel_file": "",
        "base_path": "",
        "last_data_column": "C",
        "last_title_column": "A"
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge với default
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        except Exception as e:
            print(f"Lỗi đọc config: {e}")
            return default_config
    return default_config

def save_config(config):
    """Lưu cấu hình vào file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi lưu config: {e}")

def update_save_folder(folder):
    """Cập nhật thư mục lưu và lưu config"""
    config = load_config()
    config["last_save_folder"] = folder
    save_config(config)

def update_base_path(base_path):
    """Cập nhật base path và lưu config"""
    config = load_config()
    config["base_path"] = base_path
    save_config(config)