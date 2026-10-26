r"""
HIEUCHINH_(xacnhan).py — Config đóng dấu tự chứa (Self-Contained Stamp Config)
=========================================================================
Tên config  : HIEUCHINH_(xacnhan)
Tạo lúc     : 2026-07-06 16:11:37
Nguồn JSON  : c:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\MBC\StamptAuto\StampByAntigravity\stamp_configs\Text\HIEUCHINH_(xacnhan).json
Ảnh gốc     : C:/Users/12953 bao/Desktop/CodingTest/Test/Con dau/condauBao.png
Kích thước  : 5 KB (embed base64)
Format ảnh  : PNG

File này chứa toàn bộ thông số đóng dấu, bao gồm ảnh con dấu
được mã hóa base64. KHÔNG CẦN file ảnh ngoài.

Dùng với: StampByAntigravity.py
  python StampByAntigravity.py "abc.pdf" "HIEUCHINH_(xacnhan)"
"""

import base64
import io

# ──────────────────────────────────────────────────────────────────────────────
# THÔNG SỐ ĐÓNG DẤU
# ──────────────────────────────────────────────────────────────────────────────

CONFIG_NAME          = "HIEUCHINH_(xacnhan)"

# Tỉ lệ phóng to/thu nhỏ ảnh dấu (%) — 100 = nguyên kích thước gốc
SCALE_PERCENT        = 15.0

# Template Matching: True = tìm vị trí tự động, False = vị trí cố định
USE_TEMPLATE_MATCHING = True

# Ngưỡng độ tương đồng (%) — 70~85 là phù hợp
MATCH_THRESHOLD      = 80.0

# Trang mẫu để cắt template (0-based)
PAGE_NUMBER          = 0

# True = đóng dấu TẤT CẢ trang, False = chỉ trang PAGE_NUMBER
APPLY_TO_ALL_PAGES   = True

# Vùng khoanh trên canvas preview [x1, y1, x2, y2] (pixel canvas)
STAMP_BBOX           = None

# Tâm dấu trên canvas preview [cx, cy] (pixel canvas)
STAMP_CENTER         = [902.0, 217.0]

# Toạ độ tâm trong không gian PDF [cx_pts, cy_pts]
# (dùng khi USE_TEMPLATE_MATCHING = False và USE_TEXT_ANCHOR = False)
EXACT_CENTER         = [460.02, 110.66580811332904]

# Text Anchor: Tìm chữ và đóng dấu cạnh chữ
USE_TEXT_ANCHOR      = True
ANCHOR_TEXT          = "Xác nhận"
TEXT_MATCH_MODE      = "first"  # "first", "custom", "all"
TEXT_MATCH_COUNT     = 1
TEXT_OFFSET_X        = -20.0
TEXT_OFFSET_Y        = 15.0

# Loại đóng dấu: False = In chết vào PDF (Hard Stamp), True = Tạo Annotation nổi (nếu hỗ trợ)
USE_ANNOTATION       = False

FILE_FORMAT          = "pdf"

# Đường dẫn ảnh gốc (fallback nếu base64 rỗng)
STAMP_IMAGE_PATH_FALLBACK = r"C:/Users/12953 bao/Desktop/CodingTest/Test/Con dau/condauBao.png"
TEMPLATE_IMAGE_PATH_FALLBACK = r""

# ──────────────────────────────────────────────────────────────────────────────
# ẢNH CON DẤU (EMBED BASE64)
# ──────────────────────────────────────────────────────────────────────────────
# Ảnh PNG được mã hoá base64 — 5 KB

STAMP_IMAGE_EXT = "png"

STAMP_IMAGE_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAL4AAACSCAMAAAG7w7B0AAAAAXNSR0IArs4c6QAAAARnQU1BAACx"
    "jwv8YQUAAAIBUExURQAAAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8A"
    "AP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8A"
    "AP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8A"
    "AP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8A"
    "AP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8A"
    "AP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8A"
    "AP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8A"
    "AP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8A"
    "AP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8A"
    "AP8AAP8AAP8AAP8AAI1kLIkAAACqdFJOUwACAwQGBwkLDA0PERITFBcZGhscHR4fICEmJygpKy0u"
    "LzEyMzU2ODk6Ozw9Pj9AQ0RFRkhJSktNT1BSU1VZWltcX2JkZmhpam1vcHFzdHZ4ent8fn+BgoWG"
    "iYuMjo+RkpOVlpeZmpucnZ6foKOlp6ipqqutrrCys7S1t7i6vb/AxMXGyMnKzM/Q0dLT1NXX2Nne"
    "3+Lj5ebn6Onq6+zt7/Hy8/T19/j5+/3+BHKURgAAAAlwSFlzAAAXEQAAFxEByibzPwAAESNJREFU"
    "aEPNm4u/TcUXwEeUlMrl1E+U6lCi6KASh3AjdYg8Qp08u+mFS4/7y/2JU4TqFnWSR3SIPNZf+fus"
    "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"
    "WmoAAAAASUVORK5CYII="
)


def get_stamp_image_bytes() -> bytes:
    """Giải mã base64 → bytes của file ảnh con dấu."""
    if STAMP_IMAGE_B64:
        return base64.b64decode(STAMP_IMAGE_B64)
    return b""


def get_stamp_image_pil():
    """Trả về PIL Image của con dấu (từ base64 hoặc file gốc)."""
    try:
        from PIL import Image
        data = get_stamp_image_bytes()
        if data:
            return Image.open(io.BytesIO(data))
        # Fallback sang đường dẫn file gốc
        import os
        if STAMP_IMAGE_PATH_FALLBACK and os.path.exists(STAMP_IMAGE_PATH_FALLBACK):
            return Image.open(STAMP_IMAGE_PATH_FALLBACK)
    except Exception as e:
        raise RuntimeError(f"Không thể tải ảnh con dấu: {e}")
    return None

# ──────────────────────────────────────────────────────────────────────────────
# ẢNH KHOANH VÙNG MẪU (EMBED BASE64)
# ──────────────────────────────────────────────────────────────────────────────
# Ảnh PNG được mã hoá base64 — 0 KB

TEMPLATE_IMAGE_EXT = "png"

TEMPLATE_IMAGE_B64 = (
    ""
)

def get_template_image_bytes() -> bytes:
    """Giải mã base64 → bytes của file ảnh khoanh vùng mẫu."""
    if TEMPLATE_IMAGE_B64:
        return base64.b64decode(TEMPLATE_IMAGE_B64)
    return b""

def get_template_image_pil():
    """Trả về PIL Image của ảnh khoanh vùng mẫu (từ base64 hoặc file gốc)."""
    try:
        from PIL import Image
        data = get_template_image_bytes()
        if data:
            return Image.open(io.BytesIO(data))
        import os
        if TEMPLATE_IMAGE_PATH_FALLBACK and os.path.exists(TEMPLATE_IMAGE_PATH_FALLBACK):
            return Image.open(TEMPLATE_IMAGE_PATH_FALLBACK)
    except Exception as e:
        print(f"Không thể tải ảnh khoanh vùng mẫu: {e}")
    return None


def to_dict() -> dict:
    """Xuất toàn bộ thông số dưới dạng dict (tương thích với stamp_pdf())."""
    return {
        "config_name":           CONFIG_NAME,
        "stamp_image_path":      STAMP_IMAGE_PATH_FALLBACK,
        "template_image_path":   TEMPLATE_IMAGE_PATH_FALLBACK,
        "scale_percent":         SCALE_PERCENT,
        "use_template_matching": USE_TEMPLATE_MATCHING,
        "match_threshold":       MATCH_THRESHOLD,
        "page_number":           PAGE_NUMBER,
        "apply_to_all_pages":    APPLY_TO_ALL_PAGES,
        "stamp_bbox":            STAMP_BBOX,
        "stamp_center":          STAMP_CENTER,
        "exact_center":          EXACT_CENTER,
        
        "use_text_anchor":       USE_TEXT_ANCHOR,
        "anchor_text":           ANCHOR_TEXT,
        "text_match_mode":       TEXT_MATCH_MODE,
        "text_match_count":      TEXT_MATCH_COUNT,
        "text_offset_x":         TEXT_OFFSET_X,
        "text_offset_y":         TEXT_OFFSET_Y,
        
        "use_annotation":        USE_ANNOTATION,
        
        "file_format":           FILE_FORMAT,
        "_has_embedded_image":   bool(STAMP_IMAGE_B64),
        "_image_ext":            STAMP_IMAGE_EXT,
    }


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Config: {CONFIG_NAME}")
    print(f"  Tỉ lệ          : {SCALE_PERCENT}%")
    print(f"  Template Match : {USE_TEMPLATE_MATCHING}")
    print(f"  Ngưỡng         : {MATCH_THRESHOLD}%")
    print(f"  Trang mẫu      : {PAGE_NUMBER}")
    print(f"  Vị trí cố định : {EXACT_CENTER}")
    print(f"  Ảnh embed      : {'CÓ' if STAMP_IMAGE_B64 else 'KHÔNG (dùng file gốc)'}")
    img = get_stamp_image_pil()
    if img:
        print(f"  Ảnh PIL        : {img.size[0]}x{img.size[1]} px, mode={img.mode}")
    print("\nDict params:")
    for k, v in to_dict().items():
        if k != "_image_ext":
            val_str = str(v)[:80] + ("..." if len(str(v)) > 80 else "")
            print(f"  {k:<28} = {val_str}")
