# -*- coding: utf-8 -*-
"""
Module: generate_rutgon.py
Mục đích: Lọc và xuất Đề thi rút gọn + Đáp án rút gọn cho bất kỳ thư mục nào
          (thay thế tổng quát cho generate_rutgon_1A00.py).
Hỗ trợ:
- Chọn danh sách thư mục cần xuất (mặc định = tất cả)
- Từ khóa loại trừ bổ sung tùy chỉnh (extra_exclude_keywords)
- Tiêu chí lọc cứng mặc định (ACM/SMI, ngày tháng, kgf/Newton, mã số sheet)
"""

import os
import sys
import json
import glob
import re
from typing import List, Dict, Any, Optional, Callable

try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from exam_word_merger import build_exam_doc, build_answer_doc

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BANK_BASE = os.path.join(ROOT_DIR, "KetQua", "questions_bank")
OUTPUT_DIR = os.path.join(ROOT_DIR, "KetQua")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")


def strip_vietnamese_accents(s: str) -> str:
    """Loại bỏ dấu tiếng Việt để so khớp không phân biệt có/không dấu."""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).replace('đ', 'd').replace('Đ', 'D')


def should_exclude_question(
    fname: str,
    q: Dict[str, Any],
    extra_exclude_keywords: List[str] = None,
    exclude_acm_smi: bool = True,
    exclude_dates: bool = True,
    exclude_conversions: bool = True,
    exclude_ncc_sheet: bool = True,
) -> (bool, str):
    """
    Kiểm tra câu hỏi có thuộc diện loại bỏ không.
    Hỗ trợ bật/tắt từng tiêu chí lọc và thêm từ khóa tùy chỉnh.
    """
    qt = q.get("question_text", "").strip()
    opts_str = " ".join(str(v) for v in q.get("options", {}).values())
    full_text = qt + " " + opts_str
    full_text_lower = full_text.lower()
    full_text_norm = strip_vietnamese_accents(full_text_lower)

    # 1. Phần mềm ACM / SMI
    if exclude_acm_smi:
        if fname.startswith("A09-"):
            return True, "File chuyên đề sử dụng phần mềm ACM / SMI"
        if re.search(r"\b(ACM|SMI)\b", full_text, re.IGNORECASE):
            return True, "Liên quan đến phần mềm ACM / SMI"

    # 2. Ngày tháng cố định / lịch sử cải đính / ngày ban hành
    if exclude_dates:
        if re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b", qt):
            return True, "Chứa mốc ngày tháng cố định cụ thể"
        if "ngay ban hanh dau tien" in full_text_norm or "ban hanh dau tien" in full_text_norm:
            return True, "Hỏi về ngày ban hành đầu tiên"
        if "lich su cai dinh" in full_text_norm and any(k in full_text_norm for k in ["ngay", "thang", "nam"]):
            return True, "Hỏi về ngày tháng trong lịch sử cải đính"
        if "ban hanh vao ngay thang nam nao" in full_text_norm:
            return True, "Hỏi về ngày tháng năm ban hành"
        if re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b", opts_str):
            date_count = len(re.findall(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b", opts_str))
            if date_count >= 2:
                return True, "Các phương án lựa chọn là các mốc ngày tháng cố định"

    # 3. Đổi đơn vị (kgf sang Newton, hoán đổi trọng lượng/ngẫu lực)
    if exclude_conversions:
        if re.search(r"\b(kgf|Newton|N-m|kgf-cm)\b", full_text, re.IGNORECASE) or "hoan doi trong luong" in full_text_norm:
            return True, "Hỏi về hoán đổi đơn vị đo (kgf, Newton...)"

    # 4. Đặt mã số sheet / số mẫu khi thêm nhà cung cấp
    if exclude_ncc_sheet:
        if "ma so sheet" in full_text_norm or "so mau thiet dinh" in full_text_norm or "them vao nha cung cap" in full_text_norm:
            return True, "Hỏi về quy định đặt mã số sheet / mẫu thiết định khi thêm nhà cung cấp"

    # 5. Từ khóa loại trừ bổ sung tùy chỉnh
    if extra_exclude_keywords:
        for kw in extra_exclude_keywords:
            kw_clean = kw.strip().lower()
            if not kw_clean:
                continue
            kw_norm = strip_vietnamese_accents(kw_clean)
            if kw_clean in full_text_lower or kw_norm in full_text_norm:
                return True, f"Khớp từ khóa loại trừ: '{kw_clean}'"

    return False, "OK"


def filter_and_build(
    folders: Optional[List[str]] = None,
    extra_exclude_keywords: Optional[List[str]] = None,
    exclude_acm_smi: bool = True,
    exclude_dates: bool = True,
    exclude_conversions: bool = True,
    exclude_ncc_sheet: bool = True,
    output_prefix: str = "TONG_HOP",
    custom_exam_name: Optional[str] = None,
    custom_ans_name: Optional[str] = None,
    exam_title: Optional[str] = None,
    exam_revision: Optional[str] = None,
    log_fn: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Lọc câu hỏi từ questions_bank và xuất Đề thi + Đáp án rút gọn.
    """
    log = log_fn or print
    extra_exclude_keywords = extra_exclude_keywords or []

    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Không tìm thấy file cấu hình: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Xác định danh sách thư mục cần xử lý
    all_available_folders = sorted([
        d for d in os.listdir(BANK_BASE)
        if os.path.isdir(os.path.join(BANK_BASE, d))
    ]) if os.path.isdir(BANK_BASE) else []

    if folders:
        target_folders = [f for f in folders if f in all_available_folders]
        if not target_folders:
            raise ValueError(f"Không tìm thấy thư mục nào trong questions_bank. "
                             f"Có sẵn: {all_available_folders}")
    else:
        target_folders = all_available_folders

    if not target_folders:
        raise FileNotFoundError(f"Không có thư mục câu hỏi nào trong: {BANK_BASE}")

    log(f"🔍 Đang rà soát {len(target_folders)} thư mục: {target_folders}")
    if extra_exclude_keywords:
        log(f"🚫 Từ khóa loại trừ bổ sung: {extra_exclude_keywords}")

    filtered_file_data_list = []
    total_original_q = 0
    total_excluded_q = 0
    total_kept_q = 0
    total_key_q = 0
    total_files = 0

    for folder_name in target_folders:
        bank_dir = os.path.join(BANK_BASE, folder_name)
        if not os.path.isdir(bank_dir):
            log(f"  ⚠ Không tìm thấy thư mục: {bank_dir}")
            continue

        json_files = sorted(glob.glob(os.path.join(bank_dir, "*.json")))
        log(f"  📂 [{folder_name}]: {len(json_files)} file JSON")
        total_files += len(json_files)

        for jf in json_files:
            fname = os.path.basename(jf)
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    d = json.load(f)
            except Exception as e:
                log(f"    ⚠ Lỗi đọc {fname}: {e}")
                continue

            original_questions = d.get("questions", [])
            total_original_q += len(original_questions)

            kept_questions = []
            for q in original_questions:
                exclude, reason = should_exclude_question(
                    fname, q,
                    extra_exclude_keywords=extra_exclude_keywords,
                    exclude_acm_smi=exclude_acm_smi,
                    exclude_dates=exclude_dates,
                    exclude_conversions=exclude_conversions,
                    exclude_ncc_sheet=exclude_ncc_sheet,
                )
                if exclude:
                    total_excluded_q += 1
                    log(f"    [-] Loại bỏ [{fname}] Q{q.get('question_number')}: {reason}")
                else:
                    q_clean = dict(q)
                    qt = q_clean.get("question_text", "")
                    qt_cleaned = re.sub(r"\(bản cải đính \d{4}\.\d{2}\.\d{2}\)", "", qt).strip()
                    q_clean["question_text"] = qt_cleaned
                    kept_questions.append(q_clean)
                    total_kept_q += 1
                    if q_clean.get("is_key", False) or "◎" in q_clean.get("question_text", ""):
                        total_key_q += 1

            if kept_questions:
                file_copy = dict(d)
                file_copy["questions"] = kept_questions
                filtered_file_data_list.append(file_copy)

    log("\n" + "=" * 60)
    log("📊 BÁO CÁO THỐNG KÊ LỌC CÂU HỎI:")
    log(f" - Thư mục xử lý   : {len(target_folders)} thư mục ({total_files} file)")
    log(f" - Tổng câu ban đầu: {total_original_q} câu")
    log(f" - Tổng câu bị loại: {total_excluded_q} câu")
    log(f" - Tổng câu giữ lại: {total_kept_q} câu")
    log(f" - Câu chủ chốt (◎): {total_key_q} câu")
    log("=" * 60 + "\n")

    if not filtered_file_data_list:
        raise ValueError("Không có câu hỏi nào thỏa điều kiện lọc để xuất!")

    # Tạo config cho bản rút gọn
    config_rutgon = dict(config)
    exam_settings = dict(config.get("exam_settings", {}))

    folder_label = ", ".join(target_folders) if len(target_folders) <= 3 else f"{len(target_folders)} thư mục"
    if exam_title:
        exam_settings["title"] = exam_title
    else:
        exam_settings["title"] = f"BÀI TEST NHẬN ĐỊNH TƯ CÁCH NHÂN VIÊN VÀ ĐỘI TRƯỞNG - {folder_label.upper()} (RÚT GỌN)"

    if exam_revision:
        exam_settings["revision"] = exam_revision
    else:
        exam_settings["revision"] = "BẢN RÚT GỌN CHỌN LỌC"

    config_rutgon["exam_settings"] = exam_settings

    # Xác định tên file xuất
    if custom_exam_name:
        exam_filename = custom_exam_name if custom_exam_name.endswith(".docx") else f"{custom_exam_name}.docx"
    elif output_prefix in ("TONG_HOP", "TONG_HOP_RUT_GON", "DE THI TONG HOP RUT GON"):
        exam_filename = "DE THI TONG HOP RUT GON.docx"
    else:
        exam_filename = f"{output_prefix}_RutGon_DeThi.docx"

    if custom_ans_name:
        ans_filename = custom_ans_name if custom_ans_name.endswith(".docx") else f"{custom_ans_name}.docx"
    elif output_prefix in ("TONG_HOP", "TONG_HOP_RUT_GON", "DE THI TONG HOP RUT GON"):
        ans_filename = "DAP AN TONG HOP RUT GON.docx"
    else:
        ans_filename = f"{output_prefix}_RutGon_DapAn.docx"

    # Xuất file Đề thi
    exam_path = os.path.join(OUTPUT_DIR, exam_filename)
    log(f"📝 Đang tạo file Đề thi Word: {exam_filename}...")
    exam_doc = build_exam_doc(config_rutgon, filtered_file_data_list)
    exam_doc.save(exam_path)
    log(f"✅ Đã lưu Đề thi: {exam_path}")

    # Xuất file Đáp án
    ans_path = os.path.join(OUTPUT_DIR, ans_filename)
    log(f"📋 Đang tạo file Đáp án Word: {ans_filename}...")
    ans_doc = build_answer_doc(config_rutgon, filtered_file_data_list)
    ans_doc.save(ans_path)
    log(f"✅ Đã lưu Đáp án: {ans_path}")

    # Xuất file JSON lưu bộ câu hỏi rút gọn để QuestionBrowser mở lại và chỉnh sửa nhanh
    json_filename = exam_filename.replace(".docx", "_questions.json")
    json_path = os.path.join(OUTPUT_DIR, json_filename)
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "exam_title": config_rutgon["exam_settings"].get("title"),
                "exam_revision": config_rutgon["exam_settings"].get("revision"),
                "total_questions": total_kept_q,
                "total_key": total_key_q,
                "folders_used": target_folders,
                "files": filtered_file_data_list
            }, f, ensure_ascii=False, indent=2)
        log(f"💾 Đã lưu bộ câu hỏi rút gọn JSON: {json_path}")
    except Exception as e:
        log(f"⚠ Lỗi lưu file JSON rút gọn: {e}")

    return {
        "exam_path": exam_path,
        "ans_path": ans_path,
        "json_path": json_path,
        "total_kept": total_kept_q,
        "total_excluded": total_excluded_q,
        "total_key": total_key_q,
        "folders_used": target_folders,
    }


def parse_requirements_text(text: str) -> Dict[str, Any]:
    """
    Phân tích đoạn văn bản yêu cầu tự nhiên (prompt) của người dùng để trích xuất:
    - folders: danh sách thư mục (ví dụ '1-A00')
    - exclude_acm_smi: bool
    - exclude_dates: bool
    - exclude_conversions: bool
    - exclude_ncc_sheet: bool
    - extra_exclude_keywords: list[str]
    """
    if not text:
        return {
            "folders": None,
            "exclude_acm_smi": True,
            "exclude_dates": True,
            "exclude_conversions": True,
            "exclude_ncc_sheet": True,
            "extra_exclude_keywords": [],
        }

    # 1. Nhận diện thư mục đề cập (ví dụ '1-A00', '2-000', '4-500'...)
    found_folders = []
    folder_patterns = re.findall(r"\b([1-9]-[A-Z0-9]{3})\b", text, re.IGNORECASE)
    if os.path.isdir(BANK_BASE):
        available = os.listdir(BANK_BASE)
        for fp in folder_patterns:
            fp_upper = fp.upper()
            for d in available:
                if d.upper().startswith(fp_upper):
                    if d not in found_folders:
                        found_folders.append(d)

    # 2. Nhận diện các tiêu chuẩn loại trừ
    t_lower = text.lower()
    t_norm = strip_vietnamese_accents(t_lower)
    exclude_acm_smi = bool(re.search(r"\b(acm|smi)\b", t_norm))
    exclude_dates = bool(re.search(r"ngay|thang|nam|23\.01\.2020|ban hanh|cai dinh", t_norm))
    exclude_conversions = bool(re.search(r"don vi|kgf|newton|hoan doi|trong luong|luc", t_norm))
    exclude_ncc_sheet = bool(re.search(r"nha cung cap|ma so sheet|so mau thiet dinh|mau moi", t_norm))

    # Nếu người dùng nhập yêu cầu chung chung mà không khớp cờ nào cụ thể, giữ mặc định True
    if not any([exclude_acm_smi, exclude_dates, exclude_conversions, exclude_ncc_sheet]):
        exclude_acm_smi = True
        exclude_dates = True
        exclude_conversions = True
        exclude_ncc_sheet = True

    # 3. Trích xuất từ khóa tự do
    extra_keywords = []
    for line in text.splitlines():
        line_clean = line.strip().lstrip("-*•0123456789.) ").strip()
        if not line_clean:
            continue
        m = re.search(r"(?:không đưa vào|không liên quan đến|không để|bỏ các câu liên quan đến|bỏ câu|loại bỏ)\s+(.+)", line_clean, re.IGNORECASE)
        if m:
            sub = m.group(1).strip()
            sub_short = re.split(r"như kiểu|như kiêu|như ví dụ|ví dụ", sub, flags=re.IGNORECASE)[0].strip()
            if 3 < len(sub_short) < 50:
                extra_keywords.append(sub_short)

    return {
        "folders": found_folders if found_folders else None,
        "exclude_acm_smi": exclude_acm_smi,
        "exclude_dates": exclude_dates,
        "exclude_conversions": exclude_conversions,
        "exclude_ncc_sheet": exclude_ncc_sheet,
        "extra_exclude_keywords": extra_keywords,
    }


def generate_from_prompt_requirements(prompt_text: str, output_prefix: str = "TONG_HOP",
                                      log_fn: Optional[Callable] = None) -> Dict[str, Any]:
    """Tự động phân tích prompt yêu cầu tiếng Việt của người dùng và xuất đề rút gọn."""
    parsed = parse_requirements_text(prompt_text)
    return filter_and_build(
        folders=parsed["folders"],
        extra_exclude_keywords=parsed["extra_exclude_keywords"],
        exclude_acm_smi=parsed["exclude_acm_smi"],
        exclude_dates=parsed["exclude_dates"],
        exclude_conversions=parsed["exclude_conversions"],
        exclude_ncc_sheet=parsed["exclude_ncc_sheet"],
        output_prefix=output_prefix,
        log_fn=log_fn
    )


if __name__ == "__main__":
    # Chạy thử: xuất toàn bộ
    filter_and_build()
