# -*- coding: utf-8 -*-
"""
Script: generate_rutgon_1A00.py
Mục đích: Lọc và xuất Đề thi rút gọn + Đáp án rút gọn riêng cho thư mục 1-A00 Ban V IT HOA.
Tiêu chí lọc nghiêm ngặt theo yêu cầu:
1. Không đưa vào câu hỏi ngày tháng cố định (ví dụ: ngày 23.01.2020, ngày ban hành đầu tiên).
2. Không đưa vào câu hỏi liên quan đến cách sử dụng phần mềm ACM, SMI (bỏ toàn bộ file A09 và câu hỏi liên quan).
3. Không để câu hỏi đổi đơn vị kgf sang N, hoán đổi trọng lượng/ngẫu lực (A17-1 Q1, Q2).
4. Không để câu hỏi quy định đặt mã số sheet / số mẫu khi thêm nhà cung cấp mới (A18-5).
"""

import os
import sys
import json
import glob
import re
from typing import List, Dict, Any

try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from exam_word_merger import build_exam_doc, build_answer_doc

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BANK_DIR = os.path.join(ROOT_DIR, "KetQua", "questions_bank", "1-A00")
OUTPUT_DIR = os.path.join(ROOT_DIR, "KetQua")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")


def should_exclude_question(fname: str, q: Dict[str, Any]) -> (bool, str):
    """Kiểm tra câu hỏi có thuộc diện cần loại bỏ hay không."""
    qt = q.get("question_text", "").strip()
    opts_str = " ".join(str(v) for v in q.get("options", {}).values())
    full_text = qt + " " + opts_str

    # 1. Toàn bộ file A09 là hướng dẫn phần mềm ACM / SMI
    if fname.startswith("A09-"):
        return True, "File chuyên đề sử dụng phần mềm ACM / SMI"

    # 2. Câu hỏi nhắc tới ACM hoặc SMI
    if re.search(r"\b(ACM|SMI)\b", full_text, re.IGNORECASE):
        return True, "Liên quan đến phần mềm ACM / SMI"

    # 3. Ngày tháng cố định / lịch sử cải đính / ngày ban hành
    if re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b", qt):
        return True, "Chứa mốc ngày tháng cố định cụ thể"
    if "ngày ban hành đầu tiên" in qt.lower() or "ban hành đầu tiên" in qt.lower():
        return True, "Hỏi về ngày ban hành đầu tiên"
    if "lịch sử cải đính" in qt.lower() and any(k in qt.lower() for k in ["ngày", "tháng", "năm"]):
        return True, "Hỏi về ngày tháng trong lịch sử cải đính"
    if "ban hành vào ngày tháng năm nào" in qt.lower():
        return True, "Hỏi về ngày tháng năm ban hành"
    if re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b", opts_str):
        # Kiểm tra nếu đáp án là danh sách các mốc ngày tháng (như A08-1 Q1)
        date_count = len(re.findall(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b", opts_str))
        if date_count >= 2:
            return True, "Các phương án lựa chọn là các mốc ngày tháng cố định"

    # 4. Đổi đơn vị (kgf sang Newton, hoán đổi trọng lượng/ngẫu lực)
    if re.search(r"\b(kgf|Newton|N-m|kgf-cm)\b", full_text, re.IGNORECASE) or "hoán đổi trọng lượng" in qt.lower():
        return True, "Hỏi về hoán đổi đơn vị đo (kgf, Newton...)"

    # 5. Đặt mã số sheet / số mẫu khi thêm nhà cung cấp (A18-5)
    if "mã số sheet" in qt.lower() or "số mẫu thiết định" in qt.lower() or "thêm vào nhà cung cấp" in qt.lower():
        return True, "Hỏi về quy định đặt mã số sheet / mẫu thiết định khi thêm nhà cung cấp"

    return False, "OK"


def filter_and_build():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Không tìm thấy file cấu hình {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    if not os.path.exists(BANK_DIR):
        raise FileNotFoundError(f"Không tìm thấy thư mục ngân hàng câu hỏi: {BANK_DIR}")

    json_files = sorted(glob.glob(os.path.join(BANK_DIR, "*.json")))
    print(f"🔍 Đang rà soát {len(json_files)} file JSON trong {BANK_DIR}...")

    filtered_file_data_list = []
    total_original_q = 0
    total_excluded_q = 0
    total_kept_q = 0
    total_key_q = 0

    for jf in json_files:
        fname = os.path.basename(jf)
        with open(jf, "r", encoding="utf-8") as f:
            d = json.load(f)

        original_questions = d.get("questions", [])
        total_original_q += len(original_questions)

        kept_questions = []
        for q in original_questions:
            exclude, reason = should_exclude_question(fname, q)
            if exclude:
                total_excluded_q += 1
                print(f"  [-] Loại bỏ [{fname}] Q{q.get('question_number')}: {reason}")
                print(f"      Chi tiết: {q.get('question_text')[:80]}...")
            else:
                # Làm sạch tiền tố ngày nếu chỉ là chú thích phiên bản trong ngoặc đơn không cần thiết
                q_clean = dict(q)
                qt = q_clean.get("question_text", "")
                # Ví dụ: "(bản cải đính 2022.03.10)" -> lược bớt để câu hỏi thuần túy nghiệp vụ
                qt_cleaned = re.sub(r"\(bản cải đính \d{4}\.\d{2}\.\d{2}\)", "", qt).strip()
                q_clean["question_text"] = qt_cleaned
                kept_questions.append(q_clean)
                total_kept_q += 1
                if q_clean.get("is_key", False) or "◎" in q_clean.get("question_text", ""):
                    total_key_q += 1

        if kept_questions:
            # Tạo bản sao file data chứa các câu hỏi đã lọc
            file_copy = dict(d)
            file_copy["questions"] = kept_questions
            filtered_file_data_list.append(file_copy)

    print("\n" + "=" * 60)
    print("📊 BÁO CÁO THỐNG KÊ LỌC CÂU HỎI 1-A00:")
    print(f" - Tổng câu ban đầu : {total_original_q} câu (từ {len(json_files)} file)")
    print(f" - Tổng câu bị loại : {total_excluded_q} câu")
    print(f" - Tổng câu giữ lại : {total_kept_q} câu (từ {len(filtered_file_data_list)} file tiêu chuẩn)")
    print(f" - Câu chủ chốt (◎) : {total_key_q} câu")
    print("=" * 60 + "\n")

    # Cập nhật thông tin tiêu đề đề thi riêng cho bản rút gọn
    config_rutgon = dict(config)
    exam_settings = dict(config.get("exam_settings", {}))
    exam_settings["title"] = "BÀI TEST NHẬN ĐỊNH TƯ CÁCH NHÂN VIÊN VÀ ĐỘI TRƯỞNG - PHẦN 1-A00 (RÚT GỌN)"
    exam_settings["revision"] = "REV 14 (2026) - BẢN RÚT GỌN CHỌN LỌC"
    config_rutgon["exam_settings"] = exam_settings

    # Xuất file Đề thi rút gọn
    exam_path = os.path.join(OUTPUT_DIR, "1-A00_RutGon_DeThi.docx")
    print("📝 Đang tạo file Đề thi rút gọn Word...")
    exam_doc = build_exam_doc(config_rutgon, filtered_file_data_list)
    exam_doc.save(exam_path)
    print(f"✅ Đã lưu Đề thi: {exam_path}")

    # Xuất file Đáp án rút gọn
    ans_path = os.path.join(OUTPUT_DIR, "1-A00_RutGon_DapAn.docx")
    print("📋 Đang tạo file Đáp án rút gọn Word...")
    ans_doc = build_answer_doc(config_rutgon, filtered_file_data_list)
    ans_doc.save(ans_path)
    print(f"✅ Đã lưu Đáp án: {ans_path}")

    return {
        "exam_path": exam_path,
        "ans_path": ans_path,
        "total_kept": total_kept_q,
        "total_excluded": total_excluded_q,
        "total_key": total_key_q
    }


if __name__ == "__main__":
    filter_and_build()
