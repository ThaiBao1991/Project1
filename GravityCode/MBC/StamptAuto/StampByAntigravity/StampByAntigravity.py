"""
StampByAntigravity.py
=====================
Script đóng dấu dựa trên hình ảnh (Image-Based Stamp) cho Access VBA.

Cách dùng:
    python StampByAntigravity.py <pdf_path> <config_name>
    python StampByAntigravity.py <pdf_path> <config_name> [--log]

Ví dụ:
    python StampByAntigravity.py "C:/docs/abc.pdf" "GRR"
    python StampByAntigravity.py "C:/docs/abc.pdf" "GRR_IMX_MsNa"

Tác giả: Antigravity IDE
Phiên bản: 2.0 (2026-06-08)

=======================================================================
AI ASSISTANT — ĐỌC TRƯỚC KHI CHỈNH SỬA BẤT KỲ ĐIỀU GÌ:
  1. Đọc ProjectLog.md trong cùng thư mục này
  2. Chú ý mục 3 (Đơn vị tọa độ) — đây là nguồn gây lỗi phổ biến nhất
  3. stamp_bbox trong engine nhận PDF points (không phải canvas pixels)
  4. Config được lưu ở stamp_configs/Image/ hoặc stamp_configs/Text/
=======================================================================
"""

import sys
import os
import json
import traceback
import shutil
import io

from pathlib import Path
from datetime import datetime

# ── Thư viện ảnh và PDF ──────────────────────────────────────────────────────
try:
    import fitz  # PyMuPDF
except ImportError:
    print("LỖI: Thiếu thư viện PyMuPDF. Cài đặt bằng: pip install PyMuPDF")
    input("Nhấn Enter để thoát...")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("LỖI: Thiếu thư viện Pillow. Cài đặt bằng: pip install Pillow")
    input("Nhấn Enter để thoát...")
    sys.exit(1)

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# ── Cấu hình đường dẫn ───────────────────────────────────────────────────────
SCRIPT_DIR      = Path(__file__).parent
CONFIG_DIR      = SCRIPT_DIR / "stamp_configs"
LOG_FILE        = SCRIPT_DIR / "stamp_log.txt"
TEMP_DIR        = SCRIPT_DIR / "temp"

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

def write_log(message: str, level: str = "INFO"):
    """Ghi log vào file và in ra console."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{level}] {message}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
        # In ra stdout để Access/WScript có thể đọc nếu cần
        print(line.strip())
    except Exception:
        pass


def log_info(msg):  write_log(msg, "INFO")
def log_ok(msg):    write_log(f"✓ {msg}", "OK")
def log_warn(msg):  write_log(f"⚠ {msg}", "WARN")
def log_err(msg):   write_log(f"✗ {msg}", "ERROR")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG MANAGER
# ─────────────────────────────────────────────────────────────────────────────

def load_config(config_name: str) -> dict:
    if config_name.endswith(".py") or config_name.endswith(".json"):
        config_name = os.path.splitext(config_name)[0]
        
    # Uu tien dung file .py (tu chua anh embed base64) truoc
    py_path = CONFIG_DIR / f"{config_name}.py"
    if py_path.exists():
        log_info(f"Tim thay file config .py: {py_path}")
        return _load_py_config(config_name)
        
    paths_to_check = [
        CONFIG_DIR / "Text" / f"{config_name}.json",
        CONFIG_DIR / "Image" / f"{config_name}.json",
        CONFIG_DIR / f"{config_name}.json"
    ]
    
    for p in paths_to_check:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
                
    raise FileNotFoundError(f"Không tìm thấy cấu hình: {config_name}")

def list_configs() -> list:
    configs = set()
    if CONFIG_DIR.exists():
        for f in CONFIG_DIR.glob("*.json"):
            if not f.name.startswith("_"):
                configs.add(f.stem)
        for sub in ["Text", "Image"]:
            d = CONFIG_DIR / sub
            if d.exists():
                for f in d.glob("*.json"):
                    if not f.name.startswith("_"):
                        configs.add(f.stem)
    return sorted(list(configs))


def _load_py_config(config_name: str) -> dict:
    """
    Tải cấu hình từ file Python tự chứa (.py).
    File .py được tạo bởi config_generator.py và chứa ảnh base64 embed.
    """
    import importlib.util
    py_path = CONFIG_DIR / f"{config_name}.py"
    spec    = importlib.util.spec_from_file_location(config_name, str(py_path))
    mod     = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    cfg = mod.to_dict()

    # Gắn PIL Image đã giải mã sẵn (ưu tiên dùng thay vì đường dẫn file)
    try:
        pil_img = mod.get_stamp_image_pil()
        cfg["_stamp_image_pil"] = pil_img
        log_ok(f"Ảnh con dấu embed: {pil_img.size[0]}x{pil_img.size[1]} px (base64)")
    except Exception as e:
        log_warn(f"Không thể giải mã ảnh embed: {e}")
        cfg["_stamp_image_pil"] = None
        
    try:
        if hasattr(mod, "get_template_image_pil"):
            tmpl_img = mod.get_template_image_pil()
            cfg["_template_image_pil"] = tmpl_img
            if tmpl_img:
                log_ok(f"Ảnh mẫu (khoanh vùng) embed: {tmpl_img.size[0]}x{tmpl_img.size[1]} px (base64)")
    except Exception as e:
        log_warn(f"Không thể giải mã ảnh mẫu embed: {e}")
        cfg["_template_image_pil"] = None

    return cfg


def save_config(config_name: str, cfg: dict):
    """Lưu cấu hình vào file JSON."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_path = CONFIG_DIR / f"{config_name}.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
    log_ok(f"Đã lưu cấu hình '{config_name}' → {config_path}")

# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE MATCHING
# ─────────────────────────────────────────────────────────────────────────────

def find_match_position(page_img_pil: Image.Image, template_pil: Image.Image, threshold=0.8):
    """
    Dùng OpenCV để tìm template trên page, hỗ trợ multi-scale (50% -> 150%).
    """
    page_cv = cv2.cvtColor(np.array(page_img_pil), cv2.COLOR_RGB2BGR)
    tmpl_cv = cv2.cvtColor(np.array(template_pil), cv2.COLOR_RGB2BGR)

    h, w = tmpl_cv.shape[:2]
    
    # Scale rông hơn: từ 50% đến 300% theo yêu cầu
    scales = []
    # Thêm các scale chi tiết xung quanh 1.0
    for sc in [1.0, 0.95, 1.05, 0.9, 1.1, 0.85, 1.15, 0.8, 1.2]:
        scales.append(sc)
    
    # Thêm các scale từ 0.5 đến 3.0 với step 0.1 (tức 50% đến 300%)
    for sc in np.arange(0.5, 3.1, 0.1):
        sc = round(sc, 2)
        if sc not in scales:
            scales.append(sc)
            
    # Sắp xếp các scale theo độ gần với 1.0 để ưu tiên kích thước gốc
    scales.sort(key=lambda x: abs(x - 1.0))
    
    best_val = -1
    best_loc = None
    best_scale = 1.0
    
    # Do scales đã được sort ưu tiên gần 1.0, nếu tìm thấy max_val đủ tốt thì dừng sớm!
    for sc in scales:
        th, tw = int(h * sc), int(w * sc)
        if th > page_cv.shape[0] or tw > page_cv.shape[1]: continue
        resized = cv2.resize(tmpl_cv, (tw, th))
        res = cv2.matchTemplate(page_cv, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        
        if max_val > best_val:
            best_val = max_val
            best_loc = (max_loc[0] + tw // 2, max_loc[1] + th // 2)
            best_scale = sc
            
        # Early stopping: Đạt ngưỡng yêu cầu thì chốt luôn, tránh bị nhiễu do hình siêu nhỏ
        if best_val >= (threshold / 100.0):
            break

    if best_val >= (threshold / 100.0):
        log_info(f"Tìm thấy vị trí tại ({best_loc[0]}, {best_loc[1]}) với độ tương đồng {best_val*100:.1f}%, Tỷ lệ mẫu: {best_scale*100:.0f}%")
        return best_loc, best_scale
    return None, 1.0

# ─────────────────────────────────────────────────────────────────────────────
# IMAGE RESIZE HIGH QUALITY
# ─────────────────────────────────────────────────────────────────────────────

def resize_high_quality(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Thu nhỏ / phóng to ảnh với chất lượng cao (Lanczos)."""
    if target_w <= 0 or target_h <= 0:
        return img
    cw, ch = img.size
    if target_w < cw and target_h < ch:
        result = img.copy()
        result.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
        if result.size != (target_w, target_h):
            result = result.resize((target_w, target_h), Image.Resampling.LANCZOS)
    else:
        # Phóng to dần để giữ nét
        result = img.copy()
        sw, sh = cw, ch
        while sw < target_w and sh < target_h:
            sw = min(int(sw * 1.5), target_w)
            sh = min(int(sh * 1.5), target_h)
            result = result.resize((sw, sh), Image.Resampling.LANCZOS)
        if result.size != (target_w, target_h):
            result = result.resize((target_w, target_h), Image.Resampling.LANCZOS)
    return result

# ─────────────────────────────────────────────────────────────────────────────
# CORE: ĐÓng DẤU MỘT FILE PDF
# ─────────────────────────────────────────────────────────────────────────────

def stamp_pdf(pdf_path: str, cfg: dict, custom_output: str = None) -> bool:
    """
    Áp dụng đóng dấu image-based vào file PDF.
    """
    stamp_image_path = cfg.get("stamp_image_path", "")
    scale_percent    = float(cfg.get("scale_percent", 100.0))
    use_tm           = cfg.get("use_template_matching", False)
    threshold        = float(cfg.get("match_threshold", 80.0))
    exact_center     = cfg.get("exact_center")        # [cx_pdf, cy_pdf]
    stamp_bbox       = cfg.get("stamp_bbox_pdf") or cfg.get("stamp_bbox") # Luôn ưu tiên PDF points
    stamp_center     = [(stamp_bbox[0]+stamp_bbox[2])/2, (stamp_bbox[1]+stamp_bbox[3])/2] if stamp_bbox else None
    page_number      = int(cfg.get("page_number", 0)) # trang mẫu
    apply_to_all     = cfg.get("apply_to_all_pages", True)
    
    use_text_anchor = bool(cfg.get("use_text_anchor", False))
    anchor_text     = cfg.get("anchor_text", "")
    text_match_mode = cfg.get("text_match_mode", "first")
    text_match_count= int(cfg.get("text_match_count", 1))
    text_offset_x   = float(cfg.get("text_offset_x", 0.0))
    text_offset_y   = float(cfg.get("text_offset_y", 0.0))
    use_annotation  = bool(cfg.get("use_annotation", False))

    # ── Lấy ảnh con dấu ──────────────────────────────────────────────────────
    embedded_pil = cfg.get("_stamp_image_pil")
    if embedded_pil is not None:
        stamp_img_pil = embedded_pil
    elif stamp_image_path and os.path.exists(stamp_image_path):
        stamp_img_pil = Image.open(stamp_image_path)
    else:
        return False

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    temp_stamp_path = str(TEMP_DIR / "temp_stamp_antigravity.png")
    stamp_img_pil.save(temp_stamp_path, "PNG")

    doc = fitz.open(pdf_path)
    total_pages  = len(doc)
    
    # ── Chuẩn bị template ────────────────────────────────────────────────────
    template_img_pil = None
    if use_tm and CV2_AVAILABLE and stamp_bbox:
        if cfg.get("_template_image_pil"):
            template_img_pil = cfg.get("_template_image_pil")
        elif cfg.get("template_image_path") and os.path.exists(cfg.get("template_image_path")):
            template_img_pil = Image.open(cfg.get("template_image_path"))
        else:
            log_warn("KHONG co hinh anh mau! Dung Fallback: Cat tu PDF.")
            sample_page = doc[min(page_number, total_pages - 1)]
            mat         = fitz.Matrix(2.0, 2.0)
            pix         = sample_page.get_pixmap(matrix=mat)
            sample_pil  = Image.open(io.BytesIO(pix.tobytes("png")))
            x1 = max(0, min(int(stamp_bbox[0] * 2.0), sample_pil.width))
            y1 = max(0, min(int(stamp_bbox[1] * 2.0), sample_pil.height))
            x2 = max(0, min(int(stamp_bbox[2] * 2.0), sample_pil.width))
            y2 = max(0, min(int(stamp_bbox[3] * 2.0), sample_pil.height))
            if x2 > x1 and y2 > y1:
                template_img_pil = sample_pil.crop((x1, y1, x2, y2))

    # ── Offset tâm dấu so với tâm template (PDF points) ─────────────────────
    offset_x_pdf = 0.0
    offset_y_pdf = 0.0
    if use_tm and template_img_pil and exact_center and stamp_bbox:
        # stamp_bbox giờ đã lưu dạng PDF points (từ stamp_bbox_pdf trong main_gui)
        tmpl_cx_pdf = (stamp_bbox[0] + stamp_bbox[2]) / 2.0
        tmpl_cy_pdf = (stamp_bbox[1] + stamp_bbox[3]) / 2.0
        offset_x_pdf = exact_center[0] - tmpl_cx_pdf
        offset_y_pdf = exact_center[1] - tmpl_cy_pdf
        log_info(f"Offset tâm dấu: dx={offset_x_pdf:.2f}, dy={offset_y_pdf:.2f} pts")

    # ── Vòng lặp đóng dấu từng trang ─────────────────────────────────────────
    stamped_count = 0
    skipped_count = 0

    pages_to_stamp = list(range(total_pages)) if apply_to_all else [page_number]
    for page_num in pages_to_stamp:
        page = doc[page_num]
        pdf_w = page.rect.width
        pdf_h = page.rect.height

        centers_to_stamp = []

        if use_text_anchor and anchor_text:
            clip_rect = fitz.Rect(stamp_bbox) if stamp_bbox else None
            text_instances = page.search_for(anchor_text, clip=clip_rect)
            if text_instances:
                if text_match_mode == "first":
                    text_instances = [text_instances[0]]
                elif text_match_mode == "custom":
                    text_instances = text_instances[:text_match_count]
                
                for inst in text_instances:
                    x0, y0, x1, y1 = inst
                    cx = x1 + text_offset_x
                    cy = y1 + text_offset_y
                    centers_to_stamp.append((cx, cy))
            else:
                skipped_count += 1
                continue

        elif use_tm and template_img_pil and CV2_AVAILABLE:
            mat      = fitz.Matrix(2.0, 2.0)
            pix      = page.get_pixmap(matrix=mat)
            page_pil = Image.open(io.BytesIO(pix.tobytes("png")))
            
            match_res, match_scale = find_match_position(page_pil, template_img_pil, threshold)

            if match_res:
                scale_to_pdf_x = pdf_w / page_pil.width
                scale_to_pdf_y = pdf_h / page_pil.height

                # match_res = (x, y) trên ảnh có scale 2.0
                cx = match_res[0] * scale_to_pdf_x
                cy = match_res[1] * scale_to_pdf_y

                # Cộng offset tâm dấu (PDF points), nhân thêm tỷ lệ mẫu tìm được
                cx += offset_x_pdf * match_scale
                cy += offset_y_pdf * match_scale

                # Lưu match_scale vào tuple để tính toán kích thước con dấu
                centers_to_stamp.append((cx, cy, match_scale))
                log_info(f"  Trang {page_num+1}: Template match → tâm PDF ({cx:.2f}, {cy:.2f}) với scale {match_scale}")
            else:
                log_warn(f"  Trang {page_num+1}: Không match được template → bỏ qua trang này.")
                skipped_count += 1
                continue
        else:
            # Dùng vị trí cố định
            if exact_center:
                cx = float(exact_center[0])
                cy = float(exact_center[1])
                centers_to_stamp.append((cx, cy, 1.0))
                log_info(f"  Trang {page_num+1}: Vị trí cố định → tâm PDF ({cx:.2f}, {cy:.2f})")
            else:
                log_warn(f"  Trang {page_num+1}: Không có exact_center, template matching tắt, text anchor tắt → bỏ qua.")
                skipped_count += 1
                continue

        # Tiến hành đóng dấu tại các tâm đã xác định
        base_scale_percent = scale_percent / 100.0
        
        for item in centers_to_stamp:
            # item có thể là (cx, cy) hoặc (cx, cy, match_scale)
            cx = item[0]
            cy = item[1]
            match_scale = item[2] if len(item) > 2 else 1.0
            
            # Tính toán kích thước con dấu Dynamic
            scale_ratio = base_scale_percent * match_scale
            new_w = max(1, int(stamp_img_pil.width  * scale_ratio))
            new_h = max(1, int(stamp_img_pil.height * scale_ratio))
            
            img_rect = fitz.Rect(
                cx - new_w / 2,
                cy - new_h / 2,
                cx + new_w / 2,
                cy + new_h / 2,
            )
            
            if use_annotation:
                log_warn("Tính năng Đóng Dấu Nổi (Annotation) với ảnh tuỳ chỉnh chưa được PyMuPDF hỗ trợ hoàn toàn. Chuyển về In Chết.")
                # Override to False after first warning to prevent spam
                use_annotation = False
                
            page.insert_image(img_rect, filename=temp_stamp_path)
            stamped_count += 1
            log_ok(f"  Trang {page_num+1}: Đã chèn dấu tại Rect{img_rect}")

    # ── Lưu PDF ──────────────────────────────────────────────────────────────
    if stamped_count > 0:
        if custom_output:
            doc.save(custom_output)
            doc.close()
            log_ok(f"Đã lưu kết quả Test vào: {custom_output}")
        else:
            temp_pdf = str(TEMP_DIR / "temp_output_antigravity.pdf")
            doc.save(temp_pdf)
            doc.close()
            shutil.move(temp_pdf, pdf_path)
            log_ok(f"Đã lưu kết quả vào file gốc: {pdf_path}")
    else:
        doc.close()
        log_warn("Không có trang nào được đóng dấu — file gốc không thay đổi.")

    # Dọn file tạm
    try:
        if os.path.exists(temp_stamp_path):
            os.remove(temp_stamp_path)
    except Exception:
        pass

    log_info(f"Tổng kết: đóng dấu {stamped_count} trang, bỏ qua {skipped_count} trang.")
    return stamped_count > 0

# ─────────────────────────────────────────────────────────────────────────────
# CORE: GỠ DẤU KHỎI FILE PDF
# ─────────────────────────────────────────────────────────────────────────────

def remove_stamp_pdf(pdf_path: str, cfg: dict, custom_output: str = None) -> bool:
    """
    Gỡ các con dấu (image-based) khỏi file PDF dựa trên cấu hình (so khớp XObject theo kích thước gốc).
    """
    stamp_image_path = cfg.get("stamp_image_path", "")
    embedded_pil = cfg.get("_stamp_image_pil")
    
    if embedded_pil is not None:
        stamp_img_pil = embedded_pil
    elif stamp_image_path and os.path.exists(stamp_image_path):
        stamp_img_pil = Image.open(stamp_image_path)
    else:
        log_err("Không thể tải ảnh con dấu từ cấu hình để lấy kích thước!")
        return False
        
    target_w = stamp_img_pil.width
    target_h = stamp_img_pil.height
    log_info(f"Kích thước ảnh gốc cần gỡ: {target_w}x{target_h}")
    
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    removed_count = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images()
        for img in images:
            xref = img[0]
            w = img[2]
            h = img[3]
            # So khớp kích thước tuyệt đối
            if w == target_w and h == target_h:
                try:
                    page.delete_image(xref)
                    removed_count += 1
                    log_ok(f"  Trang {page_num+1}: Đã gỡ đối tượng ảnh {xref} ({w}x{h})")
                except Exception as e:
                    log_err(f"  Trang {page_num+1}: Lỗi khi gỡ đối tượng ảnh {xref}: {e}")
                    
    if removed_count > 0:
        if custom_output:
            doc.save(custom_output, garbage=3, deflate=True)
            doc.close()
            log_ok(f"Đã lưu kết quả Gỡ Dấu vào: {custom_output}")
        else:
            temp_pdf = str(TEMP_DIR / "temp_remove_antigravity.pdf")
            doc.save(temp_pdf, garbage=3, deflate=True)
            doc.close()
            shutil.move(temp_pdf, pdf_path)
            log_ok(f"Đã lưu kết quả Gỡ Dấu đè lên file gốc: {pdf_path}")
    else:
        doc.close()
        log_warn("Không tìm thấy con dấu nào để gỡ trong file PDF.")
        
    log_info(f"Tổng kết: Đã gỡ {removed_count} con dấu.")
    return removed_count > 0

# ─────────────────────────────────────────────────────────────────────────────
# GUI MODE
# ─────────────────────────────────────────────────────────────────────────────

def launch_gui():
    import main_gui
    import tkinter as tk
    
    root = tk.Tk()
    app = main_gui.StampApp(root)
    root.mainloop()

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def print_usage():
    print("""
+--------------------------------------------------------------+
|           StampByAntigravity — Image-Based Stamp             |
|           Được gọi từ Access VBA qua WScript.Shell           |
+--------------------------------------------------------------+
|  Cú pháp:                                                    |
|    python StampByAntigravity.py <pdf_path> <config_name> [mode]|
|                                                              |
|  Ví dụ Đóng dấu:                                             |
|    python StampByAntigravity.py "C:/docs/abc.pdf" "GRR"      |
|                                                              |
|  Ví dụ Gỡ dấu (nếu truyền tham số thứ 3 là --remove):        |
|    python StampByAntigravity.py "C:/docs/abc.pdf" "GRR" --remove |
|                                                              |
|  Để liệt kê config có sẵn:                                   |
|    python StampByAntigravity.py --list                       |
+--------------------------------------------------------------+
""")

def main():
    # Windows console UTF-8 fix
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if len(sys.argv) == 1:
        launch_gui()
        sys.exit(0)
        sys.exit(0)

    write_log("=" * 60)
    write_log("=== BAT DAU: StampByAntigravity ===")

    # ── Xử lý --list ─────────────────────────────────────────────────────────
    if len(sys.argv) == 2 and sys.argv[1] in ("--list", "-l", "list"):
        configs = list_configs()
        if configs:
            print("\n[DANH SACH] Cau hinh co san:")
            for c in configs:
                ext = ".py" if (CONFIG_DIR / f"{c}.py").exists() else ".json"
                print(f"   {c}  ({ext})")
        else:
            print(f"\n[WARN] Chua co cau hinh nao. Them file vao: {CONFIG_DIR}")
        sys.exit(0)

    # ── Kiểm tra tham số ─────────────────────────────────────────────────────
    if len(sys.argv) < 3:
        print_usage()
        log_err("Thiếu tham số: cần <pdf_path> và <config_name>")
        sys.exit(1)

    pdf_path    = sys.argv[1].replace("/", "\\").replace("file:///", "").replace("#", "")
    config_name = sys.argv[2].strip()

    log_info(f"File PDF  : {pdf_path}")
    log_info(f"Config    : {config_name}")
    log_info(f"cv2/numpy : {'CÓ SẴN' if CV2_AVAILABLE else 'KHÔNG CÓ — chỉ dùng vị trí cố định'}")

    # ── Kiểm tra file PDF ─────────────────────────────────────────────────────
    if not os.path.exists(pdf_path):
        log_err(f"File PDF không tồn tại: {pdf_path}")
        print(f"LỖI: File PDF không tồn tại: {pdf_path}")
        sys.exit(1)

    log_ok("File PDF tồn tại.")

    # ── Tải cấu hình ─────────────────────────────────────────────────────────
    try:
        cfg = load_config(config_name)
        log_ok(f"Đã tải cấu hình: {config_name}")
        log_info(f"Ảnh dấu      : {cfg.get('stamp_image_path')}")
        log_info(f"Tỉ lệ        : {cfg.get('scale_percent')}%")
        log_info(f"Template match: {cfg.get('use_template_matching')}")
        log_info(f"Ngưỡng       : {cfg.get('match_threshold')}%")
        log_info(f"Vị trí cố định: {cfg.get('exact_center')}")
    except FileNotFoundError as e:
        log_err(str(e))
        print(f"LỖI: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        log_err(f"File config JSON bị lỗi: {e}")
        print(f"LỖI: File config JSON bị lỗi: {e}")
        sys.exit(1)

    # ── Thực hiện đóng dấu / gỡ dấu ──────────────────────────────────────────
    is_remove = (len(sys.argv) >= 4 and sys.argv[3].strip().lower() in ("--remove", "remove", "-r"))
    
    try:
        if is_remove:
            log_info("=== CHẾ ĐỘ: GỠ DẤU (UNSTAMP) ===")
            success = remove_stamp_pdf(pdf_path, cfg)
        else:
            log_info("=== CHẾ ĐỘ: ĐÓNG DẤU ===")
            success = stamp_pdf(pdf_path, cfg)
    except Exception as e:
        log_err(f"Ngoại lệ khi thực thi: {e}")
        log_err(traceback.format_exc())
        print(f"LỖI: {e}")
        sys.exit(1)

    if success:
        action_name = "Gỡ dấu" if is_remove else "Đóng dấu"
        log_ok(f"ĐÃ {action_name.upper()} THÀNH CÔNG.")
        print(f"OK: Đã {action_name.lower()} thành công: {pdf_path}")
        sys.exit(0)
    else:
        log_warn("Hoàn thành nhưng không có trang nào được thay đổi.")
        print(f"WARN: Không có thay đổi nào trên file: {pdf_path}")
        sys.exit(2)


if __name__ == "__main__":
    main()
