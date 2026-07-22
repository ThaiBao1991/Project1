# link_parser.py
import re
from openpyxl.cell.cell import Cell

def parse_hyperlink(cell: Cell) -> str | None:
    """
    Parse link từ ô Excel.
    Hỗ trợ:
    - Hyperlink object (openpyxl)
    - Công thức HYPERLINK("path", "text")
    - Đường dẫn UNC thuần \\server\folder\file.pdf
    """
    # Trường hợp 1: Ô trống hoặc giá trị "-"
    if cell.value is None or str(cell.value).strip() == "-" or str(cell.value).strip() == "":
        return None
    
    # Trường hợp 2: Có hyperlink object
    if cell.hyperlink and cell.hyperlink.target:
        return cell.hyperlink.target
    
    # Trường hợp 3: Công thức HYPERLINK
    if isinstance(cell.value, str):
        # Pattern cho HYPERLINK("đường_dẫn", "hiển_thị")
        pattern = r'HYPERLINK\("([^"]+)"'
        match = re.search(pattern, cell.value)
        if match:
            return match.group(1)
        
        # Pattern cho UNC path thuần
        # \\server\folder\file.pdf
        unc_pattern = r'\\\\[^\\]+\\[^"]+'
        match_unc = re.search(unc_pattern, cell.value)
        if match_unc:
            return match_unc.group(0)
        
        # Pattern cho đường dẫn local C:\folder\file.pdf
        local_pattern = r'[A-Za-z]:\\[^"]+'
        match_local = re.search(local_pattern, cell.value)
        if match_local:
            return match_local.group(0)
    
    return None


def extract_filename_from_link(link: str) -> str:
    """Lấy tên file từ đường dẫn link"""
    if not link:
        return "unknown"
    
    # Xử lý cả UNC và local path
    # Tách bằng \ hoặc /
    import os
    filename = os.path.basename(link.replace('\\', '/'))
    
    # Nếu không có extension, thêm .bin
    if '.' not in filename:
        filename += '.bin'
    
    return filename