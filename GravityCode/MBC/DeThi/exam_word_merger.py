# -*- coding: utf-8 -*-
"""
Module: exam_word_merger.py
Mục đích: Ghép nối toàn bộ câu hỏi đã được duyệt OK từ tất cả các thư mục nguồn
theo thứ tự ưu tiên: 2-000 → 3-400 → 4-500 → 5-600 → 6-900 → 7-S00 → 8-T00 → 9-Z00.
Xuất 2 file Word chuẩn (DE THI MOI TONG HOP.docx và DAP AN TONG HOP.docx) theo format REV 13.
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional

try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pdf_extractor import scan_all_sources


FONT_NAME = "Arial"


def _set_paragraph_font(para, font_name: str, font_size_pt: float, bold: bool = False, color: Optional[tuple] = None):
    """Áp dụng font + cỡ chữ + in đậm + màu sắc cho toàn paragraph qua format run."""
    for run in para.runs:
        run.font.name = font_name
        run.font.size = Pt(font_size_pt)
        run.font.bold = bold
        if color:
            run.font.color.rgb = RGBColor(*color)
        run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)


def _add_styled_run(para, text: str, font_name: str = FONT_NAME, font_size_pt: float = 11.0, bold: bool = False, color: Optional[tuple] = None):
    """Thêm run có style đầy đủ vào paragraph."""
    run = para.add_run(text)
    run.font.name = font_name
    run.font.size = Pt(font_size_pt)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    try:
        run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
    except Exception:
        pass
    return run


def _add_cover_and_header(doc: Document, config: Dict[str, Any]):
    """Thêm phần bìa/tiêu đề đề thi theo chuẩn REV 13."""
    es = config.get("exam_settings", {})

    # Tiêu đề lớn
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_styled_run(p_title, es.get("title", "BÀI TEST NHẬN ĐỊNH TƯ CÁCH NHÂN VIÊN VÀ ĐỘI TRƯỞNG PHÒNG KIỂM TRA"), font_size_pt=12.0, bold=True)

    # Mã số
    p_code = doc.add_paragraph()
    p_code.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _add_styled_run(p_code, es.get("doc_code", "MSPH:VDMBH-GDNĐKT-007-BTNĐTC"), font_size_pt=11.0, bold=True)

    # Tiêu chuẩn phán định
    doc.add_paragraph()
    p_std = doc.add_paragraph()
    _add_styled_run(p_std, "Tiêu chuẩn phán định:", font_size_pt=8.0, bold=True)

    # Nhân viên
    p_nv = doc.add_paragraph()
    _add_styled_run(p_nv, "Nhân viên kiểm tra: LK, TP, HC, ĐGSP, Kiểm tra hàng gia công", font_size_pt=8.0, bold=True)
    p_nv2 = doc.add_paragraph()
    _add_styled_run(p_nv2, "Tiêu chuẩn nhận định:", font_size_pt=8.0)
    p_nv3 = doc.add_paragraph()
    _add_styled_run(p_nv3, es.get("pass_score_staff", "Đạt: 80% trở lên và không bị sai ở câu hỏi quan trọng (có dấu ◎)"), font_size_pt=8.0)
    p_nv4 = doc.add_paragraph()
    _add_styled_run(p_nv4, es.get("fail_score_staff", "Không đạt: dưới 80% hoặc trên 80% nhưng bị sai ở câu hỏi quan trọng (có dấu ◎)"), font_size_pt=8.0)

    # Đội trưởng
    p_dt = doc.add_paragraph()
    _add_styled_run(p_dt, "Đội trưởng: Linh Kiện, Thành Phẩm", font_size_pt=8.0, bold=True)
    p_dt2 = doc.add_paragraph()
    _add_styled_run(p_dt2, "Tiêu chuẩn nhận định:", font_size_pt=8.0)
    p_dt3 = doc.add_paragraph()
    _add_styled_run(p_dt3, es.get("pass_score_leader", "Đạt: 90% trở lên và không bị sai ở câu hỏi quan trọng (có dấu ◎)"), font_size_pt=8.0)
    p_dt4 = doc.add_paragraph()
    _add_styled_run(p_dt4, es.get("fail_score_leader", "Không đạt: dưới 90% hoặc trên 90% nhưng bị sai ở câu hỏi quan trọng (có dấu ◎)"), font_size_pt=8.0)

    p_schedule = doc.add_paragraph()
    _add_styled_run(p_schedule, "Tiến độ đánh giá: Định kỳ 2 năm/1 lần", font_size_pt=8.0)

    doc.add_paragraph()
    p_instruct = doc.add_paragraph()
    _add_styled_run(p_instruct, "Hãy khoanh tròn vào câu trả lời đúng nhất trong biểu trả lời câu hỏi:", font_size_pt=10.0)


def _write_question_block(doc: Document, q_data: Dict[str, Any], seq_num: int, section_header_written: bool):
    """Viết 1 block câu hỏi trắc nghiệm vào file Word Đề thi."""
    q_text = q_data.get("question_text", "").strip()
    is_key = q_data.get("is_key", False) or "◎" in q_text
    options = q_data.get("options", {})

    # In số câu + nội dung câu hỏi
    prefix = f"◎ " if is_key else ""
    full_q_text = f"Câu {seq_num:03d}: {prefix}{q_text.lstrip('◎').strip()}"

    p_q = doc.add_paragraph()
    _add_styled_run(p_q, full_q_text, font_size_pt=10.0, bold=is_key)

    # In các lựa chọn A, B, C, D
    for opt_key in ["A", "B", "C", "D"]:
        opt_text = options.get(opt_key, "")
        if opt_text:
            p_opt = doc.add_paragraph()
            p_opt.paragraph_format.left_indent = Cm(0.8)
            _add_styled_run(p_opt, f"{opt_key}. {opt_text}", font_size_pt=10.0)

    # Đường ngăn cách nhỏ
    doc.add_paragraph()


def _set_cell_bg_color(cell, hex_color: str):
    """Đặt màu nền (shading) cho ô bảng Word."""
    try:
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), hex_color)
        # Xoá shd cũ nếu có
        for old_shd in tcPr.findall(qn('w:shd')):
            tcPr.remove(old_shd)
        tcPr.append(shd)
    except Exception:
        pass


def _write_answer_row(doc: Document, q_data: Dict[str, Any], seq_num: int, table, row_idx: int, col_per_row: int = 3):
    """Thêm 1 ô đáp án vào bảng đáp án — câu chủ chốt ◎ được highlight màu nền đỏ nhạt."""
    is_key = q_data.get("is_key", False) or "◎" in q_data.get("question_text", "")
    correct = q_data.get("correct_answer", "?").upper()

    col_idx = (seq_num - 1) % col_per_row
    row_idx_actual = (seq_num - 1) // col_per_row

    try:
        cell = table.cell(row_idx_actual, col_idx)
        # Xóa text cũ
        for p in cell.paragraphs:
            for run in p.runs:
                run.text = ""

        # Dòng 1: Câu số + ký hiệu ◎ nếu là câu chủ chốt
        p1 = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.clear()
        q_label = f"◎ Câu {seq_num:03d}" if is_key else f"Câu {seq_num:03d}"
        r1 = p1.add_run(q_label)
        r1.font.name = FONT_NAME
        r1.font.size = Pt(9.0)
        r1.font.bold = True
        if is_key:
            r1.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)  # Đỏ đậm cho câu ◎

        # Dòng 2: Đáp án đúng (in đậm, lớn hơn)
        p2 = cell.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r2 = p2.add_run(correct)
        r2.font.name = FONT_NAME
        r2.font.size = Pt(11.0)
        r2.font.bold = True
        if is_key:
            r2.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)

        # Màu nền: Vàng nhạt cho câu ◎, trắng cho câu thường
        if is_key:
            _set_cell_bg_color(cell, "FFF2CC")  # Vàng nhạt
        else:
            _set_cell_bg_color(cell, "FFFFFF")  # Trắng

    except (IndexError, Exception):
        pass


def load_questions_by_priority(bank_dir: str, folder_order: List[str]) -> List[Dict[str, Any]]:
    """Đọc toàn bộ câu hỏi OK theo thứ tự ưu tiên thư mục."""
    all_questions_data = []
    for folder_name in folder_order:
        folder_slug = folder_name.split()[0]
        subfolder = os.path.join(bank_dir, folder_slug)
        if not os.path.exists(subfolder):
            continue

        json_files = sorted([f for f in os.listdir(subfolder) if f.endswith(".json")])
        for jf in json_files:
            jf_path = os.path.join(subfolder, jf)
            try:
                with open(jf_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                status = data.get("status", "MISSING")
                if status == "OK":
                    all_questions_data.append(data)
            except Exception as e:
                print(f"[WARN] Bỏ qua {jf}: {e}")

    return all_questions_data


def build_exam_doc(config: Dict[str, Any], all_questions_data: List[Dict[str, Any]]) -> Document:
    """Tạo file Word Đề thi từ toàn bộ câu hỏi OK theo thứ tự."""
    doc = Document()

    # Thiết lập lề chuẩn giống REV 13 (đơn vị: Cm)
    section = doc.sections[0]
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.3)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(1.2)

    _add_cover_and_header(doc, config)

    seq_num = 1
    prev_folder = None

    for file_data in all_questions_data:
        folder_name = file_data.get("folder_name", "")
        doc_title = file_data.get("doc_title", "Tài liệu tiêu chuẩn kỹ thuật")
        doc_code = file_data.get("doc_code", "")
        target = file_data.get("target_audience", "Đội trưởng và nhân viên LK, TP, HC, ĐGSP, GCCK")

        # Tiêu đề phần nếu chuyển thư mục
        if folder_name != prev_folder:
            p_section_header = doc.add_paragraph()
            _add_styled_run(p_section_header, f"=== {folder_name} ===", font_size_pt=9.0, bold=True)
            prev_folder = folder_name

        # Tiêu đề từng file tài liệu
        part_label = f"Phần {doc_code}: Liên quan tài liệu: {doc_title}"
        p_part = doc.add_paragraph()
        _add_styled_run(p_part, part_label, font_size_pt=9.0, bold=True)
        p_target = doc.add_paragraph()
        _add_styled_run(p_target, f"Đối tượng test: {target}", font_size_pt=9.0)

        questions = file_data.get("questions", [])
        for q in questions:
            _write_question_block(doc, q, seq_num, section_header_written=True)
            seq_num += 1

    return doc


def build_answer_doc(config: Dict[str, Any], all_questions_data: List[Dict[str, Any]]) -> Document:
    """Tạo file Word Đáp án từ toàn bộ câu hỏi OK theo thứ tự."""
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.3)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(1.2)

    es = config.get("exam_settings", {})
    # Tiêu đề file đáp án
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_styled_run(p_title, "ĐÁP ÁN NHẬN ĐỊNH TƯ CÁCH NHÂN VIÊN VÀ ĐỘI TRƯỞNG PHÒNG KIỂM TRA", font_size_pt=12.0, bold=True)
    p_rev = doc.add_paragraph()
    p_rev.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_styled_run(p_rev, es.get("revision", "REV 14 (2026)"), font_size_pt=10.0, bold=False)
    doc.add_paragraph()

    # Đếm tổng câu để tạo bảng đáp án
    total_q = sum(len(fd.get("questions", [])) for fd in all_questions_data)
    col_per_row = 3
    import math
    total_rows = math.ceil(total_q / col_per_row)

    # Tạo bảng đáp án
    table = doc.add_table(rows=total_rows, cols=col_per_row)
    table.style = "Table Grid"

    seq_num = 1
    for file_data in all_questions_data:
        questions = file_data.get("questions", [])
        for q in questions:
            _write_answer_row(doc, q, seq_num, table, None, col_per_row)
            seq_num += 1

    # Thêm bảng chú giải phía dưới
    total_key_q = sum(
        1 for fd in all_questions_data
        for q in fd.get("questions", [])
        if q.get("is_key", False) or "◎" in q.get("question_text", "")
    )
    doc.add_paragraph()
    # Bảng legend ký hiệu
    legend_table = doc.add_table(rows=1, cols=2)
    legend_table.style = "Table Grid"
    lc0 = legend_table.cell(0, 0)
    lc0.text = ""
    p_lc0 = lc0.paragraphs[0]
    p_lc0.clear()
    r_lc0 = p_lc0.add_run("  ◎ Câu Chủ Chốt  ")
    r_lc0.font.name = FONT_NAME
    r_lc0.font.size = Pt(9.0)
    r_lc0.font.bold = True
    r_lc0.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    _set_cell_bg_color(lc0, "FFF2CC")
    p_lc0.alignment = WD_ALIGN_PARAGRAPH.CENTER

    lc1 = legend_table.cell(0, 1)
    p_lc1 = lc1.paragraphs[0]
    p_lc1.clear()
    r_lc1 = p_lc1.add_run(
        f"Tổng {total_key_q} câu chủ chốt (◎) — Sai câu này không đạt ngay, dù điểm tổng đạt yêu cầu."
    )
    r_lc1.font.name = FONT_NAME
    r_lc1.font.size = Pt(9.0)
    r_lc1.font.bold = True

    doc.add_paragraph()
    p_src = doc.add_paragraph()
    _add_styled_run(p_src, "Căn cứ: Hệ thống tài liệu tiêu chuẩn kỹ thuật BHCL Mabuchi Motor (Source 2-000 ~ 9-Z00).", font_size_pt=8.0)

    return doc


def export_single_file_exam_and_answer(file_data: Dict[str, Any], config_path: str = "config.json", output_base_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Xuất file Đề thi và Đáp án riêng biệt cho ĐÚNG 1 bản tiêu chuẩn kỹ thuật (1 file PDF).
    Ví dụ: 000-0-V.pdf -> KetQua/2-000/tung_ban/DE_THI_000-0-V.docx và DAP_AN_000-0-V.docx
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    output_dir = output_base_dir or config.get("output_dir", "KetQua")
    folder_name = file_data.get("folder_name", "")
    folder_slug = folder_name.split()[0] if folder_name else "common"
    file_name = file_data.get("file_name", "standard")
    base_name = os.path.splitext(file_name)[0]

    # Thư mục chứa các file Word của từng bản riêng lẻ
    target_dir = os.path.join(output_dir, folder_slug, "tung_ban")
    os.makedirs(target_dir, exist_ok=True)

    exam_path = os.path.join(target_dir, f"DE_THI_{base_name}.docx")
    exam_doc = build_exam_doc(config, [file_data])
    exam_doc.save(exam_path)

    ans_path = os.path.join(target_dir, f"DAP_AN_{base_name}.docx")
    ans_doc = build_answer_doc(config, [file_data])
    ans_doc.save(ans_path)

    return {"file_name": file_name, "exam": exam_path, "answer": ans_path, "total_questions": len(file_data.get("questions", []))}


def export_all_single_files_by_folder(folder_name: str, config_path: str = "config.json", output_base_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Xuất file Word riêng biệt cho từng bản tiêu chuẩn trong 1 thư mục cụ thể."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    bank_dir = config.get("questions_bank_dir", "KetQua/questions_bank")
    folder_questions = load_questions_by_priority(bank_dir, [folder_name])

    exported = []
    for file_data in folder_questions:
        res = export_single_file_exam_and_answer(file_data, config_path, output_base_dir)
        exported.append(res)
    return exported


def export_all_single_files_all_folders(config_path: str = "config.json", output_base_dir: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Xuất file Word riêng biệt cho từng bản tiêu chuẩn trong TẤT CẢ các thư mục."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    folder_order = config.get("folder_order", [])
    results = {}
    for folder in folder_order:
        results[folder] = export_all_single_files_by_folder(folder, config_path, output_base_dir)
    return results


def export_folder_exam_and_answer(folder_name: str, config_path: str = "config.json", output_base_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Xuất file Đề thi và Đáp án riêng biệt cho 1 thư mục tiêu chuẩn cụ thể.
    Ví dụ: folder_name = "2-000 Ban V IT HOA" -> xuất KetQua/2-000/DE_THI_2-000.docx và DAP_AN_2-000.docx
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    bank_dir = config.get("questions_bank_dir", "KetQua/questions_bank")
    output_dir = output_base_dir or config.get("output_dir", "KetQua")

    folder_slug = folder_name.split()[0]
    folder_questions = load_questions_by_priority(bank_dir, [folder_name])
    total_q = sum(len(fd.get("questions", [])) for fd in folder_questions)

    if total_q == 0:
        return {"error": f"Thư mục {folder_slug} chưa có câu hỏi nào đạt trạng thái OK."}

    # Thư mục đích riêng cho từng nhóm tiêu chuẩn
    folder_out_dir = os.path.join(output_dir, folder_slug)
    os.makedirs(folder_out_dir, exist_ok=True)

    exam_path = os.path.join(folder_out_dir, f"DE_THI_{folder_slug}.docx")
    exam_doc = build_exam_doc(config, folder_questions)
    exam_doc.save(exam_path)

    ans_path = os.path.join(folder_out_dir, f"DAP_AN_{folder_slug}.docx")
    ans_doc = build_answer_doc(config, folder_questions)
    ans_doc.save(ans_path)

    return {"exam": exam_path, "answer": ans_path, "total_questions": total_q}


def export_all_individual_folders(config_path: str = "config.json", output_base_dir: Optional[str] = None) -> Dict[str, Any]:
    """Xuất đề thi và đáp án riêng cho từng thư mục con."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    folder_order = config.get("folder_order", [])
    results = {}

    for folder in folder_order:
        res = export_folder_exam_and_answer(folder, config_path, output_base_dir)
        results[folder] = res

    return results


def merge_and_export(config_path: str = "config.json", output_base_dir: Optional[str] = None) -> Dict[str, str]:
    """Pipeline chính: Đọc config, load câu hỏi OK toàn bộ, xuất 2 file Word tổng hợp."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    bank_dir = config.get("questions_bank_dir", "KetQua/questions_bank")
    output_dir = output_base_dir or config.get("output_dir", "KetQua")
    folder_order = config.get("folder_order", [])
    os.makedirs(output_dir, exist_ok=True)

    print("📚 Đang load câu hỏi OK theo thứ tự ưu tiên...")
    all_questions_data = load_questions_by_priority(bank_dir, folder_order)
    total_q = sum(len(fd.get("questions", [])) for fd in all_questions_data)
    print(f"✅ Đã load {len(all_questions_data)} file tài liệu, tổng {total_q} câu hỏi hợp lệ.")

    if total_q == 0:
        print("⚠️ Chưa có câu hỏi nào đạt trạng thái OK. Hãy nhập và kiểm định câu hỏi trước.")
        return {}

    # Xuất Đề thi
    exam_path = os.path.join(output_dir, "DE THI MOI TONG HOP.docx")
    print("📝 Đang tạo file Đề thi tổng hợp...")
    exam_doc = build_exam_doc(config, all_questions_data)
    exam_doc.save(exam_path)
    print(f"✅ File Đề thi: {exam_path}")

    # Xuất Đáp án
    ans_path = os.path.join(output_dir, "DAP AN TONG HOP.docx")
    print("📋 Đang tạo file Đáp án tổng hợp...")
    ans_doc = build_answer_doc(config, all_questions_data)
    ans_doc.save(ans_path)
    print(f"✅ File Đáp án: {ans_path}")

    return {"exam": exam_path, "answer": ans_path, "total_questions": total_q}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    merge_and_export()

