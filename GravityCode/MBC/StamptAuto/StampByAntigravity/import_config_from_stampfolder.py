"""
import_config_from_stampfolder.py
==================================
Tiện ích: Sao chép / nhập config từ thư mục StampFolder vào StampByAntigravity.

Dùng khi: Bạn đã cấu hình con dấu bằng StamFolder01/02/03.py
          và muốn dùng lại config đó cho StampByAntigravity.

Cách dùng:
    python import_config_from_stampfolder.py
"""

import os
import json
import shutil
from pathlib import Path

# ── Đường dẫn ─────────────────────────────────────────────────────────────────
THIS_DIR         = Path(__file__).parent
TARGET_CONFIG    = THIS_DIR / "stamp_configs"

STAMPFOLDER_DIR  = THIS_DIR.parent / "StampFolder"
SOURCE_CONFIG    = STAMPFOLDER_DIR / "stamp_configs"


def import_configs():
    if not SOURCE_CONFIG.exists():
        print(f"⚠  Không tìm thấy thư mục nguồn: {SOURCE_CONFIG}")
        return

    TARGET_CONFIG.mkdir(parents=True, exist_ok=True)
    json_files = list(SOURCE_CONFIG.glob("*.json"))

    if not json_files:
        print("⚠  Không có file .json nào trong StampFolder/stamp_configs/")
        return

    print(f"\n📂 Nguồn: {SOURCE_CONFIG}")
    print(f"📂 Đích  : {TARGET_CONFIG}\n")

    imported = 0
    for src_file in json_files:
        dst_file = TARGET_CONFIG / src_file.name
        if dst_file.exists():
            choice = input(f"  '{src_file.name}' đã tồn tại. Ghi đè? (y/N): ").strip().lower()
            if choice != "y":
                print(f"  ⏭  Bỏ qua: {src_file.name}")
                continue

        shutil.copy2(src_file, dst_file)
        print(f"  ✓ Đã nhập: {src_file.name}")
        imported += 1

    print(f"\nHoàn tất! Đã nhập {imported}/{len(json_files)} cấu hình.")
    print(f"\nDanh sách config có thể dùng:")
    for f in TARGET_CONFIG.glob("*.json"):
        print(f"  • {f.stem}")


def show_config_detail(config_name: str):
    """Hiển thị chi tiết một config."""
    cfg_file = TARGET_CONFIG / f"{config_name}.json"
    if not cfg_file.exists():
        print(f"Không tìm thấy: {cfg_file}")
        return
    with open(cfg_file, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    print(f"\n{'='*50}")
    print(f"  CONFIG: {config_name}")
    print(f"{'='*50}")
    print(f"  Ảnh con dấu     : {cfg.get('stamp_image_path', '—')}")
    print(f"  Tỉ lệ (%)       : {cfg.get('scale_percent', 100)}")
    print(f"  Template Matching: {cfg.get('use_template_matching', False)}")
    print(f"  Ngưỡng (%)      : {cfg.get('match_threshold', 80)}")
    print(f"  Vị trí cố định  : {cfg.get('exact_center', '—')}")
    print(f"  Vùng bbox       : {cfg.get('stamp_bbox', '—')}")
    print(f"  Trang mẫu       : {cfg.get('page_number', 0)}")
    print(f"  Áp dụng tất cả  : {cfg.get('apply_to_all_pages', True)}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        show_config_detail(sys.argv[1])
    else:
        import_configs()
