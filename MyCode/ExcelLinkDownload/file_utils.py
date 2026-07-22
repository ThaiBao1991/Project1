# file_utils.py
import os
import shutil
import requests
from datetime import datetime
from utils import clean_link, generate_link_variants


def get_file_size_mb(filepath: str) -> float:
    """Lấy dung lượng file (MB)"""
    if os.path.exists(filepath):
        size_bytes = os.path.getsize(filepath)
        return round(size_bytes / (1024 * 1024), 2)
    return 0.0


def get_file_modified_date(filepath: str) -> str:
    """Lấy ngày sửa file (YYYY-MM-DD HH:MM:SS)"""
    if os.path.exists(filepath):
        timestamp = os.path.getmtime(filepath)
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    return ""


def get_remote_file_info(url: str) -> tuple[float, str]:
    """Lấy thông tin file từ remote (hỗ trợ UNC, local path)"""
    # Làm sạch link trước
    url = clean_link(url)
    
    # Nếu là UNC hoặc local path
    if url.startswith('\\\\') or ':\\' in url:
        if os.path.exists(url):
            size_mb = get_file_size_mb(url)
            modified_date = get_file_modified_date(url)
            return size_mb, modified_date
        return 0.0, ""
    
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        size_mb = 0.0
        if 'content-length' in response.headers:
            size_bytes = int(response.headers['content-length'])
            size_mb = round(size_bytes / (1024 * 1024), 2)
        
        last_modified = ""
        if 'last-modified' in response.headers:
            last_modified = response.headers['last-modified']
        
        return size_mb, last_modified
    except:
        return 0.0, ""


def download_file(url: str, save_path: str, progress_callback=None) -> bool:
    """
    Tải file từ url về save_path (hàm gốc)
    Hỗ trợ HTTP, HTTPS, UNC path, local path
    """
    # Làm sạch link trước khi tải
    url = clean_link(url)
    
    try:
        # Kiểm tra nếu là UNC path hoặc local path
        if url.startswith('\\\\') or ':\\' in url:
            if not os.path.exists(url):
                print(f"Lỗi: File nguồn không tồn tại: {url}")
                return False
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            shutil.copy2(url, save_path)
            
            if progress_callback:
                total_mb = os.path.getsize(url) / (1024 * 1024)
                progress_callback(total_mb, total_mb, 100)
            
            return True
        
        # HTTP/HTTPS URL
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        total_mb = round(total_size / (1024 * 1024), 2)
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        downloaded = 0
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        downloaded_mb = round(downloaded / (1024 * 1024), 2)
                        percent = (downloaded / total_size) * 100
                        progress_callback(downloaded_mb, total_mb, percent)
        
        return True
        
    except Exception as e:
        print(f"Lỗi tải file {url}: {e}")
        return False


def download_file_with_fallback(link: str, save_path: str, progress_callback=None) -> bool:
    """
    Tải file với fallback: thử nhiều biến thể của link
    - Thử link gốc (đã clean)
    - Nếu fail, thử thay , bằng \
    - Nếu fail, thử thay \ bằng ,
    """
    # Làm sạch link gốc
    clean_link_original = clean_link(link)
    variants = generate_link_variants(clean_link_original)
    
    for i, variant in enumerate(variants):
        print(f"Thử tải biến thể {i+1}/{len(variants)}: {variant[:100]}...")
        
        if download_file(variant, save_path, progress_callback):
            if i > 0:
                print(f"✅ Thành công với biến thể: {variant}")
            return True
        else:
            print(f"❌ Thất bại với biến thể: {variant[:100]}...")
    
    return False