"""
config_generator.py
===================
Tạo file Python config tự chứa (.py) từ:
  1. Cấu hình JSON của StampFolder (stamp_configs/*.json)
  2. Ảnh con dấu (PNG/JPG) — embed base64 vào trong file .py

Kết quả: mỗi config là 1 file .py hoàn toàn độc lập,
không cần ảnh ngoài hay JSON — Access chỉ cần gọi:
    python StampByAntigravity.py "abc.pdf" "GRR"

Cách dùng:
    python config_generator.py                  # Chạy GUI chọn config
    python config_generator.py GRR              # Tạo từ tên JSON
    python config_generator.py --all            # Tạo tất cả config JSON hiện có
    python config_generator.py --list           # Liệt kê config .py đã tạo

Tác giả: Antigravity IDE
"""

import os
import sys
import json
import base64
import textwrap
from pathlib import Path
from datetime import datetime

# ── Đường dẫn ─────────────────────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).parent
CONFIG_DIR    = SCRIPT_DIR / "stamp_configs"         # chứa cả .json và .py
STAMPFOLDER   = SCRIPT_DIR.parent / "StampFolder" / "stamp_configs"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# ENCODE ẢNH → BASE64
# ─────────────────────────────────────────────────────────────────────────────

def image_to_base64(image_path: str) -> str:
    """Đọc file ảnh và trả về chuỗi base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def base64_to_image_bytes(b64_str: str) -> bytes:
    """Giải mã base64 → bytes của file ảnh."""
    return base64.b64decode(b64_str)


# ─────────────────────────────────────────────────────────────────────────────
# TẠO FILE .py CONFIG
# ─────────────────────────────────────────────────────────────────────────────

def generate_py_config(config_name: str, source_json_path: str = None) -> Path:
    """
    Tạo file Python config tự chứa từ:
      - JSON config (từ StampFolder hoặc stamp_configs/)
      - Embed ảnh con dấu thành base64

    Returns:
        Path đến file .py đã tạo.
    """
    # ── Tìm file JSON nguồn ──────────────────────────────────────────────────
    if source_json_path:
        json_path = Path(source_json_path)
    else:
        # Ưu tiên trong stamp_configs/ local, sau đó StampFolder
        paths_to_check = [
            CONFIG_DIR / "Text" / f"{config_name}.json",
            CONFIG_DIR / "Image" / f"{config_name}.json",
            CONFIG_DIR / f"{config_name}.json",
            STAMPFOLDER / f"{config_name}.json"
        ]
        
        for p in paths_to_check:
            if p.exists():
                json_path = p
                break
        else:
            raise FileNotFoundError(
                f"Không tìm thấy '{config_name}.json' trong thư mục Text, Image hoặc gốc."
            )

    print(f"  ← Đọc JSON: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    # ── Đọc ảnh → base64 ─────────────────────────────────────────────────────
    stamp_image_path = cfg.get("stamp_image_path", "")
    image_b64        = ""
    image_ext        = "png"
    image_size_kb    = 0

    if stamp_image_path and os.path.exists(stamp_image_path):
        print(f"  ← Đọc ảnh : {stamp_image_path}")
        image_b64     = image_to_base64(stamp_image_path)
        image_ext     = Path(stamp_image_path).suffix.lstrip(".").lower() or "png"
        image_size_kb = len(base64.b64decode(image_b64)) // 1024
        print(f"  ✓ Ảnh embed: {image_size_kb} KB → base64 ({len(image_b64)} chars)")
    else:
        print(f"  ⚠ Không tìm thấy ảnh: {stamp_image_path} — sẽ lưu đường dẫn gốc")

    # ── Đọc ảnh mẫu khoanh vùng → base64 ─────────────────────────────────────
    template_image_path = cfg.get("template_image_path", "")
    template_b64        = ""
    template_ext        = "png"
    template_size_kb    = 0

    if template_image_path and os.path.exists(template_image_path):
        print(f"  ← Đọc ảnh mẫu khoanh vùng : {template_image_path}")
        template_b64     = image_to_base64(template_image_path)
        template_ext     = Path(template_image_path).suffix.lstrip(".").lower() or "png"
        template_size_kb = len(base64.b64decode(template_b64)) // 1024
        print(f"  ✓ Ảnh mẫu embed: {template_size_kb} KB → base64 ({len(template_b64)} chars)")
    else:
        print(f"  ⚠ Không tìm thấy ảnh mẫu khoanh vùng (có thể đang dùng vị trí cố định)")

    # ── Chuẩn bị các giá trị ─────────────────────────────────────────────────
    scale_percent    = float(cfg.get("scale_percent", 100.0))
    use_tm           = bool(cfg.get("use_template_matching", False))
    match_threshold  = float(cfg.get("match_threshold", 80.0))
    page_number      = int(cfg.get("page_number", 0))
    apply_all        = bool(cfg.get("apply_to_all_pages", True))
    stamp_bbox       = cfg.get("stamp_bbox")
    stamp_center     = cfg.get("stamp_center")
    exact_center     = cfg.get("exact_center")
    
    use_text_anchor  = bool(cfg.get("use_text_anchor", False))
    anchor_text      = cfg.get("anchor_text", "")
    text_match_mode  = cfg.get("text_match_mode", "first")
    text_match_count = int(cfg.get("text_match_count", 1))
    text_offset_x    = float(cfg.get("text_offset_x", 0.0))
    text_offset_y    = float(cfg.get("text_offset_y", 0.0))
    
    use_annotation   = bool(cfg.get("use_annotation", False))
    file_format      = cfg.get("file_format", "pdf")
    created_at       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Tạo nội dung file .py ─────────────────────────────────────────────────
    # Base64 dài → chia dòng 80 ký tự để dễ đọc
    b64_lines = textwrap.wrap(image_b64, 76) if image_b64 else []
    b64_literal = "\n    ".join(f'"{line}"' for line in b64_lines) if b64_lines else '""'

    template_b64_lines = textwrap.wrap(template_b64, 76) if template_b64 else []
    template_b64_literal = "\n    ".join(f'"{line}"' for line in template_b64_lines) if template_b64_lines else '""'

    content = f'''\
r"""
{config_name}.py — Config đóng dấu tự chứa (Self-Contained Stamp Config)
=========================================================================
Tên config  : {config_name}
Tạo lúc     : {created_at}
Nguồn JSON  : {json_path}
Ảnh gốc     : {stamp_image_path}
Kích thước  : {image_size_kb} KB (embed base64)
Format ảnh  : {image_ext.upper()}

File này chứa toàn bộ thông số đóng dấu, bao gồm ảnh con dấu
được mã hóa base64. KHÔNG CẦN file ảnh ngoài.

Dùng với: StampByAntigravity.py
  python StampByAntigravity.py "abc.pdf" "{config_name}"
"""

import base64
import io

# ──────────────────────────────────────────────────────────────────────────────
# THÔNG SỐ ĐÓNG DẤU
# ──────────────────────────────────────────────────────────────────────────────

CONFIG_NAME          = "{config_name}"

# Tỉ lệ phóng to/thu nhỏ ảnh dấu (%) — 100 = nguyên kích thước gốc
SCALE_PERCENT        = {scale_percent}

# Template Matching: True = tìm vị trí tự động, False = vị trí cố định
USE_TEMPLATE_MATCHING = {use_tm}

# Ngưỡng độ tương đồng (%) — 70~85 là phù hợp
MATCH_THRESHOLD      = {match_threshold}

# Trang mẫu để cắt template (0-based)
PAGE_NUMBER          = {page_number}

# True = đóng dấu TẤT CẢ trang, False = chỉ trang PAGE_NUMBER
APPLY_TO_ALL_PAGES   = {apply_all}

# Vùng khoanh trên canvas preview [x1, y1, x2, y2] (pixel canvas)
STAMP_BBOX           = {stamp_bbox}

# Tâm dấu trên canvas preview [cx, cy] (pixel canvas)
STAMP_CENTER         = {stamp_center}

# Toạ độ tâm trong không gian PDF [cx_pts, cy_pts]
# (dùng khi USE_TEMPLATE_MATCHING = False và USE_TEXT_ANCHOR = False)
EXACT_CENTER         = {exact_center}

# Text Anchor: Tìm chữ và đóng dấu cạnh chữ
USE_TEXT_ANCHOR      = {use_text_anchor}
ANCHOR_TEXT          = "{anchor_text}"
TEXT_MATCH_MODE      = "{text_match_mode}"  # "first", "custom", "all"
TEXT_MATCH_COUNT     = {text_match_count}
TEXT_OFFSET_X        = {text_offset_x}
TEXT_OFFSET_Y        = {text_offset_y}

# Loại đóng dấu: False = In chết vào PDF (Hard Stamp), True = Tạo Annotation nổi (nếu hỗ trợ)
USE_ANNOTATION       = {use_annotation}

FILE_FORMAT          = "{file_format}"

# Đường dẫn ảnh gốc (fallback nếu base64 rỗng)
STAMP_IMAGE_PATH_FALLBACK = r"{stamp_image_path}"
TEMPLATE_IMAGE_PATH_FALLBACK = r"{template_image_path}"

# ──────────────────────────────────────────────────────────────────────────────
# ẢNH CON DẤU (EMBED BASE64)
# ──────────────────────────────────────────────────────────────────────────────
# Ảnh {image_ext.upper()} được mã hoá base64 — {image_size_kb} KB

STAMP_IMAGE_EXT = "{image_ext}"

STAMP_IMAGE_B64 = (
    {b64_literal}
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
        raise RuntimeError(f"Không thể tải ảnh con dấu: {{e}}")
    return None

# ──────────────────────────────────────────────────────────────────────────────
# ẢNH KHOANH VÙNG MẪU (EMBED BASE64)
# ──────────────────────────────────────────────────────────────────────────────
# Ảnh {template_ext.upper()} được mã hoá base64 — {template_size_kb} KB

TEMPLATE_IMAGE_EXT = "{template_ext}"

TEMPLATE_IMAGE_B64 = (
    {template_b64_literal}
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
        print(f"Không thể tải ảnh khoanh vùng mẫu: {{e}}")
    return None


def to_dict() -> dict:
    """Xuất toàn bộ thông số dưới dạng dict (tương thích với stamp_pdf())."""
    return {{
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
    }}


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Config: {{CONFIG_NAME}}")
    print(f"  Tỉ lệ          : {{SCALE_PERCENT}}%")
    print(f"  Template Match : {{USE_TEMPLATE_MATCHING}}")
    print(f"  Ngưỡng         : {{MATCH_THRESHOLD}}%")
    print(f"  Trang mẫu      : {{PAGE_NUMBER}}")
    print(f"  Vị trí cố định : {{EXACT_CENTER}}")
    print(f"  Ảnh embed      : {{'CÓ' if STAMP_IMAGE_B64 else 'KHÔNG (dùng file gốc)'}}")
    img = get_stamp_image_pil()
    if img:
        print(f"  Ảnh PIL        : {{img.size[0]}}x{{img.size[1]}} px, mode={{img.mode}}")
    print("\\nDict params:")
    for k, v in to_dict().items():
        if k != "_image_ext":
            val_str = str(v)[:80] + ("..." if len(str(v)) > 80 else "")
            print(f"  {{k:<28}} = {{val_str}}")
'''

    # ── Lưu file .py ─────────────────────────────────────────────────────────
    out_path = CONFIG_DIR / f"{config_name}.py"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    size_kb = out_path.stat().st_size // 1024
    print(f"  ✓ Đã tạo: {out_path} ({size_kb} KB)")
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# LIỆT KÊ
# ─────────────────────────────────────────────────────────────────────────────

def list_py_configs():
    """Liet ke tat ca file .py config da tao."""
    files = sorted(CONFIG_DIR.glob("*.py"))
    # Bỏ các file không phải config (như __init__.py)
    configs = [f for f in files if not f.name.startswith("_")]
    if not configs:
        print(f"Chua co file .py config nao trong: {CONFIG_DIR}")
    else:
        print(f"\n[PY CONFIG] ({len(configs)} file):")
        for p in configs:
            size_kb = p.stat().st_size // 1024
            print(f"   {p.stem:<30} ({size_kb:>4} KB)")
    return configs


def list_json_configs():
    """Liệt kê JSON configs có sẵn (local + StampFolder)."""
    local = sorted(CONFIG_DIR.glob("*.json"))
    sf    = sorted(STAMPFOLDER.glob("*.json")) if STAMPFOLDER.exists() else []
    seen  = set()
    all_configs = []
    for p in local + sf:
        if p.stem not in seen:
            seen.add(p.stem)
            all_configs.append(p)
    return all_configs


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Windows console UTF-8 fix
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if len(sys.argv) >= 2:
        arg = sys.argv[1]

        if arg in ("--list", "-l"):
            list_py_configs()
            return

        if arg == "--all":
            configs = list_json_configs()
            if not configs:
                print("Khong co JSON config nao de tao.")
                return
            print(f"\n[GENERATE] Tao {len(configs)} config .py...\n")
            success = 0
            for p in configs:
                print(f"[{p.stem}]")
                try:
                    generate_py_config(p.stem, str(p))
                    success += 1
                except Exception as e:
                    print(f"  Loi: {e}")
                print()
            print(f"\nHoan tat: {success}/{len(configs)} config da tao.")
            return

        # Ten config cu the
        config_name = arg
        print(f"\n[GENERATE] Tao config: {config_name}\n")
        try:
            out = generate_py_config(config_name)
            print(f"\n[OK] File tao thanh cong: {out}")
        except Exception as e:
            print(f"\n[LOI] {e}")
            sys.exit(1)
        return

    # Không có tham số → hiển thị menu
    print("""
╔══════════════════════════════════════════════════════════════╗
║        Config Generator — StampByAntigravity                 ║
╠══════════════════════════════════════════════════════════════╣
║  python config_generator.py <config_name>  Tạo 1 config    ║
║  python config_generator.py --all          Tạo tất cả      ║
║  python config_generator.py --list         Liệt kê .py     ║
╚══════════════════════════════════════════════════════════════╝
""")
    # Hiển thị JSON có sẵn
    jsons = list_json_configs()
    if jsons:
        print(f"📁 JSON configs tìm thấy ({len(jsons)}):")
        for p in jsons:
            print(f"   • {p.stem:<30} ← {p}")
        print()
        choice = input("Nhập tên config muốn tạo (hoặc 'all'): ").strip()
        if choice.lower() == "all":
            for p in jsons:
                print(f"\n[{p.stem}]")
                try:
                    generate_py_config(p.stem, str(p))
                except Exception as e:
                    print(f"  ✗ Lỗi: {e}")
        elif choice:
            try:
                out = generate_py_config(choice)
                print(f"\n✓ {out}")
            except Exception as e:
                print(f"\n✗ Lỗi: {e}")
    else:
        print("Không tìm thấy JSON config nào.")
        print(f"Thêm file .json vào: {CONFIG_DIR}")
        print(f"hoặc: {STAMPFOLDER}")


if __name__ == "__main__":
    main()
