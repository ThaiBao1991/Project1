# download_manager.py
import os
from file_utils import download_file_with_fallback, get_remote_file_info, get_file_size_mb, get_file_modified_date
from excel.link_parser import extract_filename_from_link
from models import FileInfo


class DownloadManager:
    def __init__(self, save_folder: str, progress_callback=None):
        self.save_folder = save_folder
        self.progress_callback = progress_callback
        os.makedirs(save_folder, exist_ok=True)
    
    def download_file_info(self, file_info: FileInfo) -> bool:
        """Tải một file và cập nhật thông tin (có fallback)"""
        filename = extract_filename_from_link(file_info.old_link)
        
        base_name, ext = os.path.splitext(filename)
        unique_filename = f"{file_info.sheet}_{file_info.row}_{base_name}{ext}"
        unique_filename = "".join(c for c in unique_filename if c.isalnum() or c in '._- ')
        
        save_path = os.path.join(self.save_folder, unique_filename)
        
        # Lấy thông tin remote (đã xử lý %20)
        size_mb, modified_date = get_remote_file_info(file_info.old_link)
        file_info.size_mb = size_mb
        file_info.modified_date = modified_date
        
        # Progress callback wrapper
        def progress_cb(downloaded_mb, total_mb, percent):
            if self.progress_callback:
                self.progress_callback(file_info.title, downloaded_mb, total_mb, percent)
        
        # Tải file với fallback (xử lý dấu , và %20)
        success = download_file_with_fallback(file_info.old_link, save_path, progress_cb)
        
        if success:
            file_info.new_link = save_path
            file_info.status = "downloaded"
            file_info.size_mb = get_file_size_mb(save_path)
            file_info.modified_date = get_file_modified_date(save_path)
            return True
        else:
            file_info.status = "failed"
            return False
    
    def download_batch(self, files: list[FileInfo], resume_mode: bool = False) -> tuple[list, list]:
        """Tải batch các file"""
        downloaded = []
        failed = []
        
        for i, file_info in enumerate(files):
            print(f"\n📥 [{i+1}/{len(files)}] Đang xử lý: {file_info.title}")
            
            if resume_mode and file_info.new_link and os.path.exists(file_info.new_link):
                current_size = get_file_size_mb(file_info.new_link)
                current_date = get_file_modified_date(file_info.new_link)
                if current_size == file_info.size_mb and current_date == file_info.modified_date:
                    file_info.status = "skipped"
                    print(f"⏭ Bỏ qua (đã tải trước đó): {file_info.title}")
                    continue
            
            if self.download_file_info(file_info):
                downloaded.append(file_info)
                print(f"✅ Đã tải: {file_info.title}")
            else:
                failed.append(file_info)
                print(f"❌ Thất bại: {file_info.title}")
        
        return downloaded, failed