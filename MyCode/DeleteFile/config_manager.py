"""
Quản lý việc đọc/ghi cấu hình từ file JSON
"""

import os
import json
from typing import List, Set
from exceptions import ConfigError

class ConfigManager:
    """Quản lý cấu hình cho ứng dụng xóa file"""
    
    DEFAULT_CONFIG = {
        "excluded_folders": [],
        "excluded_files": [],
        "folder_keywords": [],
        "file_keywords": []
    }
    
    def __init__(self, config_path: str = "config.json"):
        """
        Khởi tạo ConfigManager
        
        Args:
            config_path: Đường dẫn đến file cấu hình JSON
        """
        self.config_path = config_path
        self.config = self.load()
    
    def load(self) -> dict:
        """
        Tải cấu hình từ file JSON
        
        Returns:
            dict: Cấu hình đã tải
            
        Raises:
            ConfigError: Nếu không thể đọc file cấu hình
        """
        if not os.path.exists(self.config_path):
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()
            return self.config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                
            # Đảm bảo tất cả các key đều tồn tại
            for key in self.DEFAULT_CONFIG:
                if key not in self.config:
                    self.config[key] = self.DEFAULT_CONFIG[key].copy()
            
            return self.config
            
        except Exception as e:
            raise ConfigError(f"Không thể đọc file cấu hình: {e}")
    
    def save(self):
        """Lưu cấu hình vào file JSON"""
        try:
            # Chuẩn hóa đường dẫn
            for key in ["excluded_folders", "excluded_files"]:
                if key in self.config:
                    self.config[key] = [os.path.normpath(p) for p in self.config[key]]
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise ConfigError(f"Không thể lưu file cấu hình: {e}")
    
    def get_excluded_folders(self) -> List[str]:
        """Lấy danh sách folder không xóa"""
        return self.config.get("excluded_folders", [])
    
    def get_excluded_files(self) -> List[str]:
        """Lấy danh sách file không xóa"""
        return self.config.get("excluded_files", [])
    
    def get_folder_keywords(self) -> List[str]:
        """Lấy danh sách keyword cho folder"""
        return self.config.get("folder_keywords", [])
    
    def get_file_keywords(self) -> List[str]:
        """Lấy danh sách keyword cho file"""
        return self.config.get("file_keywords", [])
    
    def add_excluded_folder(self, folder_path: str):
        """Thêm folder vào danh sách không xóa"""
        normalized_path = os.path.normpath(folder_path)
        if normalized_path not in self.config["excluded_folders"]:
            self.config["excluded_folders"].append(normalized_path)
            self.save()
    
    def remove_excluded_folder(self, folder_path: str):
        """Xóa folder khỏi danh sách không xóa"""
        normalized_path = os.path.normpath(folder_path)
        if normalized_path in self.config["excluded_folders"]:
            self.config["excluded_folders"].remove(normalized_path)
            self.save()
    
    def add_excluded_file(self, file_path: str):
        """Thêm file vào danh sách không xóa"""
        normalized_path = os.path.normpath(file_path)
        if normalized_path not in self.config["excluded_files"]:
            self.config["excluded_files"].append(normalized_path)
            self.save()
    
    def remove_excluded_file(self, file_path: str):
        """Xóa file khỏi danh sách không xóa"""
        normalized_path = os.path.normpath(file_path)
        if normalized_path in self.config["excluded_files"]:
            self.config["excluded_files"].remove(normalized_path)
            self.save()
    
    def add_folder_keyword(self, keyword: str):
        """Thêm keyword cho folder"""
        keyword = keyword.strip()
        if keyword and keyword not in self.config["folder_keywords"]:
            self.config["folder_keywords"].append(keyword)
            self.save()
    
    def remove_folder_keyword(self, keyword: str):
        """Xóa keyword cho folder"""
        keyword = keyword.strip()
        if keyword in self.config["folder_keywords"]:
            self.config["folder_keywords"].remove(keyword)
            self.save()
    
    def add_file_keyword(self, keyword: str):
        """Thêm keyword cho file"""
        keyword = keyword.strip()
        if keyword and keyword not in self.config["file_keywords"]:
            self.config["file_keywords"].append(keyword)
            self.save()
    
    def remove_file_keyword(self, keyword: str):
        """Xóa keyword cho file"""
        keyword = keyword.strip()
        if keyword in self.config["file_keywords"]:
            self.config["file_keywords"].remove(keyword)
            self.save()