# utils.py
import urllib.parse

def col_to_index(col_str: str) -> int:
    """
    Chuyển đổi ký tự cột Excel thành số (1-index)
    A -> 1, Z -> 26, AA -> 27, AB -> 28
    """
    if not col_str:
        return 1
    
    result = 0
    for c in col_str.upper().strip():
        if c.isalpha():
            result = result * 26 + (ord(c) - ord('A') + 1)
    
    return max(result, 1)


def normalize_unc_path(link: str) -> str:
    """
    Chuẩn hóa UNC path: \\server\folder (chỉ 2 dấu \ đầu)
    Xử lý trường hợp \\\server → \\server
    """
    if not link:
        return link
    
    if link.startswith('\\\\'):
        # Đếm số dấu \ ở đầu
        count = 0
        for c in link:
            if c == '\\':
                count += 1
            else:
                break
        if count > 2:
            # Thay bằng 2 dấu \
            link = '\\\\' + link[count:]
            print(f"DEBUG - Đã chuẩn hóa UNC: {count} dấu \\ → 2 dấu \\")
    
    return link


def clean_link(link: str) -> str:
    """
    Làm sạch link:
    - URL decode (%20 → space, %2C → ,, %5C → \, ...)
    - Chuẩn hóa UNC path (3 dấu \ → 2 dấu \)
    - Chuẩn hóa dấu \
    """
    if not link:
        return link
    
    # Bước 1: URL decode
    try:
        link = urllib.parse.unquote(link)
    except Exception as e:
        print(f"Warning: URL decode failed: {e}")
    
    # Bước 2: Chuẩn hóa UNC path (3 dấu \ → 2 dấu \)
    link = normalize_unc_path(link)
    
    # Bước 3: Chuẩn hóa dấu \ (không nhân đôi)
    if link.startswith('\\\\'):
        prefix = '\\\\'
        rest = link[2:]
        rest = rest.replace('\\\\', '\\')
        link = prefix + rest
    else:
        link = link.replace('\\\\', '\\')
    
    # Bước 4: Xóa dấu " thừa
    link = link.replace('"', '')
    
    # Bước 5: Loại bỏ khoảng trắng đầu cuối
    link = link.strip()
    
    return link


def generate_link_variants(link: str) -> list:
    """
    Tạo các biến thể của link để thử khi tải
    """
    if not link:
        return []
    
    variants = [link]
    
    # Biến thể 2: thay , bằng \
    if ',' in link:
        variants.append(link.replace(',', '\\'))
    
    # Biến thể 3: thay \ bằng , (ít khả năng hơn)
    if '\\' in link and ',' not in link:
        variants.append(link.replace('\\', ','))
    
    # Loại bỏ trùng lặp
    variants = list(dict.fromkeys(variants))
    
    return variants