# excel/link_parser.py
import re
import os

def parse_hyperlink(cell_value) -> str | None:
    """
    Parse link từ giá trị ô Excel (đơn giản, không có công thức)
    Hỗ trợ UNC, local path, http
    """
    if cell_value is None:
        return None
    
    value_str = str(cell_value).strip()
    
    if value_str == "-" or value_str == "":
        return None
    
    # UNC path
    if value_str.startswith('\\\\'):
        return value_str
    
    # Local path (C:\...)
    if re.match(r'[A-Za-z]:\\', value_str):
        return value_str
    
    # HTTP/HTTPS
    if value_str.startswith(('http://', 'https://')):
        return value_str
    
    return None


def extract_filename_from_link(link: str) -> str:
    """Lấy tên file từ đường dẫn link"""
    if not link:
        return "unknown"
    
    # Xử lý cả UNC và local path
    filename = os.path.basename(link.replace('\\', '/'))
    
    if not filename or filename == '/':
        return "unknown.bin"
    
    # Nếu không có extension, thêm .bin
    if '.' not in filename:
        filename += '.bin'
    
    # Loại bỏ ký tự không hợp lệ
    filename = "".join(c for c in filename if c.isalnum() or c in '._- ')
    
    return filename