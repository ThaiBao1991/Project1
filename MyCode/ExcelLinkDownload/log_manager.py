# log_manager.py
import os
import json
from datetime import datetime
from models import DownloadLog, FileInfo

def save_log(save_folder: str, log_data: DownloadLog) -> str:
    """Lưu log vào file JSON trong save_folder"""
    log_data.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = os.path.join(save_folder, "download_log.json")
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data.to_dict(), f, ensure_ascii=False, indent=2)
    
    return log_path

def load_log(save_folder: str) -> DownloadLog | None:
    """Đọc log từ file JSON"""
    log_path = os.path.join(save_folder, "download_log.json")
    
    if not os.path.exists(log_path):
        return None
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return DownloadLog.from_dict(data)
    except Exception as e:
        print(f"Lỗi đọc log: {e}")
        return None

def should_skip_file(existing_file: FileInfo, new_file: FileInfo) -> bool:
    """So sánh full key để quyết định có bỏ qua file hay không"""
    if not existing_file:
        return False
    
    if existing_file.sheet != new_file.sheet:
        return False
    if existing_file.row != new_file.row:
        return False
    if existing_file.title != new_file.title:
        return False
    if existing_file.old_link != new_file.old_link:
        return False
    if existing_file.size_mb != new_file.size_mb:
        return False
    if existing_file.modified_date != new_file.modified_date:
        return False
    
    if existing_file.new_link and os.path.exists(existing_file.new_link):
        return True
    
    return False

def merge_logs(old_log: DownloadLog, new_files: list[FileInfo], 
               save_folder: str) -> list[FileInfo]:
    """Merge log cũ với danh sách file mới, trả về danh sách file CẦN tải"""
    if not old_log:
        return new_files
    
    old_dict = {}
    for f in old_log.files:
        key = (f.sheet, f.row)
        old_dict[key] = f
    
    files_to_download = []
    for new_file in new_files:
        key = (new_file.sheet, new_file.row)
        if key in old_dict:
            if not should_skip_file(old_dict[key], new_file):
                new_file.new_link = old_dict[key].new_link
                files_to_download.append(new_file)
        else:
            files_to_download.append(new_file)
    
    return files_to_download