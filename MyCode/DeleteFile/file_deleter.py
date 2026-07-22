"""
Xử lý logic xóa file với các ngoại lệ
"""

import os
from typing import List, Callable, Optional
from exceptions import AccessDeniedError, InvalidPathError

class FileDeleter:
    """Quản lý việc xóa file với các ngoại lệ"""
    
    def __init__(self, config_manager):
        """
        Khởi tạo FileDeleter
        
        Args:
            config_manager: Instance của ConfigManager
        """
        self.config_manager = config_manager
        self.stats = {
            "deleted_files": 0,
            "skipped_files": 0,
            "skipped_folders": 0,
            "errors": 0
        }
    
    def should_keep_folder(self, folder_path: str) -> bool:
        """
        Kiểm tra folder có nên giữ lại không
        
        Args:
            folder_path: Đường dẫn folder cần kiểm tra
            
        Returns:
            bool: True nếu nên giữ, False nếu không
        """
        normalized_path = os.path.normpath(folder_path)
        folder_name = os.path.basename(normalized_path)
        
        # Kiểm tra đường dẫn tuyệt đối
        excluded_folders = self.config_manager.get_excluded_folders()
        for excluded in excluded_folders:
            if normalized_path == os.path.normpath(excluded):
                return True
        
        # Kiểm tra keyword trong tên folder
        folder_keywords = self.config_manager.get_folder_keywords()
        for keyword in folder_keywords:
            if keyword.lower() in folder_name.lower():
                return True
        
        return False
    
    def should_keep_file(self, file_path: str) -> bool:
        """
        Kiểm tra file có nên giữ lại không
        
        Args:
            file_path: Đường dẫn file cần kiểm tra
            
        Returns:
            bool: True nếu nên giữ, False nếu không
        """
        normalized_path = os.path.normpath(file_path)
        file_name = os.path.basename(normalized_path)
        
        # Kiểm tra đường dẫn tuyệt đối
        excluded_files = self.config_manager.get_excluded_files()
        for excluded in excluded_files:
            if normalized_path == os.path.normpath(excluded):
                return True
        
        # Kiểm tra keyword trong tên file
        file_keywords = self.config_manager.get_file_keywords()
        for keyword in file_keywords:
            if keyword.lower() in file_name.lower():
                return True
        
        return False
    
    def delete_files_in_folder(self, folder_path: str, 
                              progress_callback: Optional[Callable] = None,
                              log_callback: Optional[Callable] = None) -> dict:
        """
        Xóa tất cả file trong thư mục có xét ngoại lệ
        
        Args:
            folder_path: Đường dẫn thư mục cần xóa
            progress_callback: Hàm callback để cập nhật tiến độ (nhận tham số: current, total)
            log_callback: Hàm callback để ghi log (nhận tham số: message, type)
            
        Returns:
            dict: Thống kê kết quả xóa
            
        Raises:
            InvalidPathError: Nếu đường dẫn không hợp lệ
            AccessDeniedError: Nếu không có quyền truy cập
        """
        if not os.path.exists(folder_path):
            raise InvalidPathError(f"Đường dẫn không tồn tại: {folder_path}")
        
        if not os.path.isdir(folder_path):
            raise InvalidPathError(f"Đường dẫn không phải là thư mục: {folder_path}")
        
        # Reset stats
        self.stats = {
            "deleted_files": 0,
            "skipped_files": 0,
            "skipped_folders": 0,
            "errors": 0
        }
        
        # Đếm tổng số file để hiển thị tiến độ
        total_files = 0
        for root, dirs, files in os.walk(folder_path):
            # Kiểm tra nếu folder cha bị bỏ qua thì không đếm
            if self.should_keep_folder(root):
                continue
            total_files += len(files)
        
        processed_files = 0
        
        # Duyệt và xóa file
        for root, dirs, files in os.walk(folder_path):
            # Kiểm tra nếu folder hiện tại cần giữ lại
            if self.should_keep_folder(root):
                if log_callback:
                    log_callback(f"Bỏ qua folder (theo ngoại lệ): {root}", "skip")
                self.stats["skipped_folders"] += 1
                # Xóa các thư mục con khỏi danh sách duyệt
                dirs.clear()
                continue
            
            # Xóa các file trong folder
            for file in files:
                file_path = os.path.join(root, file)
                processed_files += 1
                
                # Cập nhật tiến độ
                if progress_callback and total_files > 0:
                    progress_callback(processed_files, total_files)
                
                # Kiểm tra ngoại lệ cho file
                if self.should_keep_file(file_path):
                    if log_callback:
                        log_callback(f"Bỏ qua file (theo ngoại lệ): {file_path}", "skip")
                    self.stats["skipped_files"] += 1
                    continue
                
                # Xóa file
                try:
                    os.remove(file_path)
                    if log_callback:
                        log_callback(f"Đã xóa: {file_path}", "delete")
                    self.stats["deleted_files"] += 1
                except PermissionError:
                    error_msg = f"Không có quyền xóa: {file_path}"
                    if log_callback:
                        log_callback(error_msg, "error")
                    self.stats["errors"] += 1
                except Exception as e:
                    error_msg = f"Lỗi khi xóa {file_path}: {e}"
                    if log_callback:
                        log_callback(error_msg, "error")
                    self.stats["errors"] += 1
        
        return self.stats