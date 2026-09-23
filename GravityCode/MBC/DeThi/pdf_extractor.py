# -*- coding: utf-8 -*-
"""
Module: pdf_extractor.py
Mục đích: Trích xuất nội dung văn bản và siêu dữ liệu (metadata) từ các file tiêu chuẩn PDF của Mabuchi Motor.
Sử dụng PyMuPDF (fitz) để đọc text tầng sâu và bảo toàn tiếng Việt Unicode.
"""

import os
import re
import json
import hashlib
import time as _time
from datetime import datetime
from typing import Dict, Any, List, Optional
import fitz  # PyMuPDF

# Đường dẫn tuyệt đối đến config.json nằm cùng thư mục với file này
_DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def get_pdf_file_info(pdf_path: str) -> Dict[str, Any]:
    """
    Lấy thông tin file hệ thống của file PDF (nhanh, không cần đọc toàn bộ nội dung).
    Dùng để phát hiện khi PDF bị thay đổi/cập nhật kể từ lần sinh câu hỏi.
    Trả về:
      - file_size_bytes: kích thước file (bytes)
      - modified_time: Unix timestamp lần sửa đổi cuối
      - modified_time_iso: dạng ISO 8601 (dễ đọc)
      - file_hash_short: MD5 của 8KB đầu file (8 hex chars) — detect thay đổi nội dung
    """
    if not os.path.exists(pdf_path):
        return {}
    try:
        stat = os.stat(pdf_path)
        file_size = stat.st_size
        mtime = stat.st_mtime
        mtime_iso = datetime.fromtimestamp(mtime).isoformat(timespec="seconds")

        # Hash nhanh: chỉ đọc 8KB đầu để phát hiện thay đổi nội dung
        hash_short = ""
        try:
            hasher = hashlib.md5()
            with open(pdf_path, "rb") as fh:
                hasher.update(fh.read(8192))
            hash_short = hasher.hexdigest()[:8]
        except Exception:
            pass

        return {
            "file_size_bytes": file_size,
            "modified_time": mtime,
            "modified_time_iso": mtime_iso,
            "file_hash_short": hash_short,
        }
    except Exception:
        return {}


def clean_text(raw_text: str) -> str:
    """Làm sạch văn bản: chuẩn hóa khoảng trắng thừa, giữ lại ngắt dòng hợp lý."""
    if not raw_text:
        return ""
    lines = [line.strip() for line in raw_text.splitlines()]
    # Lọc bỏ các dòng hoàn toàn rỗng liên tiếp
    cleaned_lines = []
    empty_count = 0
    for line in lines:
        if not line:
            empty_count += 1
            if empty_count <= 1:
                cleaned_lines.append("")
        else:
            empty_count = 0
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def extract_metadata(filename: str, full_text: str) -> Dict[str, str]:
    """Trích xuất các thông tin định danh: Tên tiêu chuẩn, Mã số, Ngày ban hành/cải đính."""
    metadata = {
        "filename": filename,
        "doc_id": "",
        "standard_title": "",
        "machine_code": "",
        "issue_date": "",
        "rev_date": ""
    }

    # Lấy doc_id từ tên file (ví dụ: 000-0-V.pdf -> 000-0)
    base_name = os.path.splitext(filename)[0]
    m_id = re.search(r"(\d{3}[\-‐]\w+)", base_name)
    if m_id:
        metadata["doc_id"] = m_id.group(1).replace("‐", "-")
    else:
        metadata["doc_id"] = base_name

    lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]

    # Tìm tên tiêu chuẩn trên các dòng đầu (trang 1 thường chứa tên bản tiêu chuẩn)
    title_candidates = []
    for line in lines[:25]:
        if any(kw in line.lower() for kw in ["bản tiêu chuẩn", "bảng tiêu chuẩn", "tiêu chuẩn", "hướng dẫn"]):
            title_candidates.append(line)
        elif any(kw in line.lower() for kw in ["đồng hồ", "thước", "panme", "máy đo", "dụng cụ", "kiểm tra", "hiệu chỉnh"]):
            if len(line) < 100:
                title_candidates.append(line)

    if title_candidates:
        metadata["standard_title"] = " - ".join(title_candidates[:2])
    else:
        metadata["standard_title"] = f"Tiêu chuẩn kỹ thuật kiểm tra ({metadata['doc_id']})"

    # Tìm mã máy đo hoặc số tiêu chuẩn
    m_code = re.search(r"(?:Máy đo|Tiêu chuẩn số|Bản tiêu chuẩn số)\s*[:：]?\s*([0-9A-Za-z\s\-\–\—]+)", full_text)
    if m_code:
        lines_mc = m_code.group(1).strip().splitlines()
        metadata["machine_code"] = lines_mc[0].strip() if lines_mc else metadata["doc_id"]
    else:
        metadata["machine_code"] = metadata["doc_id"]


    # Tìm ngày ban hành
    m_banhanh = re.search(r"(?:Ban hành|Ngày ban hành)\s*[:：]?\s*(\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4})", full_text, re.IGNORECASE)
    if m_banhanh:
        metadata["issue_date"] = m_banhanh.group(1)

    # Tìm ngày cải đính / cải chính
    m_caidinh = re.search(r"(?:Cải đính|Cải chính|Ngày cải chính)\s*[:：]?\s*(\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4})", full_text, re.IGNORECASE)
    if m_caidinh:
        metadata["rev_date"] = m_caidinh.group(1)

    return metadata


def extract_pdf_content(pdf_path: str) -> Dict[str, Any]:
    """
    Đọc toàn bộ file PDF và trích xuất text từng trang kèm metadata.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Không tìm thấy file: {pdf_path}")

    filename = os.path.basename(pdf_path)
    pages_text = []

    doc = fitz.open(pdf_path)
    try:
        total_pages = len(doc)
        for page_idx in range(total_pages):
            page = doc[page_idx]
            raw_text = page.get_text()
            pages_text.append(clean_text(raw_text))
    finally:
        doc.close()

    full_text = "\n\n--- HẾT TRANG ---\n\n".join(pages_text)
    metadata = extract_metadata(filename, full_text)
    metadata["total_pages"] = str(total_pages)

    return {
        "file_path": pdf_path,
        "filename": filename,
        "metadata": metadata,
        "total_pages": total_pages,
        "pages_text": pages_text,
        "full_text": full_text
    }


def scan_all_sources(base_source_dir: Optional[str] = None, folder_order: Optional[List[str]] = None, config_path: str = None) -> List[Dict[str, Any]]:
    """
    Quét toàn bộ các file PDF trong các thư mục nguồn.

    Chiến lược tự-discover (không bao giờ bỏ sót thư mục mới):
    1. Bắt đầu bằng danh sách từ folder_order (config) — giữ đúng thứ tự ưu tiên.
    2. Tự động quét thêm tất cả thư mục con thực tế trong base_source_dir.
    3. Bất kỳ thư mục nào tồn tại trên đĩa nhưng KHÔNG có trong folder_order
       sẽ được tự động thêm vào cuối (sort theo tên).
    4. Ghi log cảnh báo cho thư mục mới chưa có trong config.
    """
    # Dùng đường dẫn tuyệt đối đến config.json để tránh lỗi relative path
    if config_path is None:
        config_path = _DEFAULT_CONFIG_PATH
    # Xử lý linh hoạt đối số truyền vào: nếu base_source_dir là None hoặc là file json -> tự load config
    if base_source_dir is None or (isinstance(base_source_dir, str) and base_source_dir.endswith(".json")):
        c_path = base_source_dir if (isinstance(base_source_dir, str) and base_source_dir.endswith(".json")) else config_path
        if os.path.exists(c_path):
            try:
                with open(c_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                base_source_dir = cfg.get("source_dir", "Source")
                if folder_order is None:
                    folder_order = cfg.get("folder_order", [])
            except Exception:
                base_source_dir = "Source"
        else:
            base_source_dir = "Source"

    if folder_order is None:
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                folder_order = cfg.get("folder_order", [])
            except Exception:
                folder_order = []
        else:
            folder_order = []

    items = []

    # Bước 1: Thu thập tất cả thư mục con thực tế trên đĩa
    real_folders: List[str] = []
    if os.path.isdir(base_source_dir):
        try:
            real_folders = sorted([
                d for d in os.listdir(base_source_dir)
                if os.path.isdir(os.path.join(base_source_dir, d))
            ])
        except Exception:
            real_folders = []

    # Bước 2: Merge — folder_order trước, sau đó các thư mục mới chưa có
    merged_order: List[str] = []
    known_set = set(folder_order)
    for fn in folder_order:
        if fn in real_folders or os.path.isdir(os.path.join(base_source_dir, fn)):
            merged_order.append(fn)

    new_discovered: List[str] = []
    for fn in real_folders:
        if fn not in known_set:
            new_discovered.append(fn)

    if new_discovered:
        # Cảnh báo — không dùng print để tránh lỗi cp932, dùng stderr an toàn
        import sys
        try:
            sys.stderr.write(
                f"[pdf_extractor] CẢNH BÁO: Phát hiện {len(new_discovered)} thư mục mới "
                f"chưa có trong config folder_order: {new_discovered}. "
                f"Vui lòng bổ sung vào config.json để cố định thứ tự ưu tiên.\n"
            )
        except Exception:
            pass
        merged_order.extend(new_discovered)

    # Bước 3: Quét PDF từng thư mục theo thứ tự đã merge
    for priority_idx, folder_name in enumerate(merged_order, start=1):
        folder_path = os.path.join(base_source_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        pdf_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')])

        for pdf_name in pdf_files:
            full_path = os.path.join(folder_path, pdf_name)
            # Unique key: "1-A00/A00-1-V"
            file_key = f"{folder_name.split()[0]}/{os.path.splitext(pdf_name)[0]}"
            items.append({
                "file_key": file_key,
                "folder_name": folder_name,
                "folder_priority": priority_idx,
                "filename": pdf_name,
                "full_path": full_path,
                "is_new_folder": folder_name in new_discovered,  # flag để GUI nhận biết
            })
    return items



if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    sample_pdf = os.path.join("Source", "2-000 Ban V IT HOA", "000-0-V.pdf")
    if os.path.exists(sample_pdf):
        res = extract_pdf_content(sample_pdf)
        print(f"Trích xuất thành công: {res['filename']}")
        print(f"Metadata: {res['metadata']}")
        print(f"Số trang: {res['total_pages']}, Độ dài text: {len(res['full_text'])} ký tự")
    else:
        print("Không tìm thấy file mẫu.")
