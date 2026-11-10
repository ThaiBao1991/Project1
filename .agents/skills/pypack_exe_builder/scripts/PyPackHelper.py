import os
import sys
import builtins

# Lưu lại hàm open gốc
_original_open = builtins.open

def get_data_path(filename):
    '''
    Lấy đường dẫn đúng của file data/config.
    '''
    filename_str = os.fspath(filename)
    # Không can thiệp nếu là đường dẫn tuyệt đối
    if os.path.isabs(filename_str):
        return filename
        
    if hasattr(sys, '_MEIPASS'):
        exe_dir = os.path.dirname(sys.executable)
        external_path = os.path.join(exe_dir, filename_str)
        internal_path = os.path.join(sys._MEIPASS, filename_str)
        
        # Ưu tiên tìm file ở ngoài (giải nén để sửa)
        if os.path.exists(external_path):
            return external_path
            
        # Sau đó tìm ở trong (đính kèm cứng)
        if os.path.exists(internal_path):
            return internal_path
            
    # Mặc định code python bình thường
    return filename

def _smart_open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
    if isinstance(file, (str, bytes, os.PathLike)):
        file_path = os.fspath(file)
        # Chỉ can thiệp vào file đọc ('r') và đường dẫn tương đối
        # Với file lưu/ghi mới ('w', 'a'), giữ nguyên hành vi gốc để user ghi vào thư mục hiện hành
        if 'r' in mode and not os.path.isabs(file_path):
            file = get_data_path(file)
            
    return _original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)

# Ghi đè hàm open của hệ thống bằng hàm thông minh
builtins.open = _smart_open

# Kích hoạt tự động khi import
def auto_patch():
    pass # Chỉ cần import là file này đã tự chạy việc gán builtins.open
