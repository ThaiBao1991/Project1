# -*- coding: utf-8 -*-
"""
Module: question_validator.py
Mục đích: Quản lý ngân hàng câu hỏi (questions_bank), kiểm định chất lượng từng file câu hỏi.
Kiểm tra các quy tắc bắt buộc:
- Đủ ít nhất 3 câu hỏi / file.
- Có đúng 1 câu chủ chốt (ký hiệu ◎).
- Đủ 4 phương án A, B, C, D và có đáp án chính xác.
- Nội dung câu hỏi dàn trải, không trùng lặp.
Cung cấp bảng báo cáo tiến độ toàn diện cho 409 file tiêu chuẩn.
"""

import os
import json
import re
from typing import Dict, Any, List, Tuple, Optional
from pdf_extractor import scan_all_sources


class QuestionValidator:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.source_dir = self.config.get("source_dir", "Source")
        self.bank_dir = self.config.get("questions_bank_dir", "KetQua/questions_bank")
        self.folder_order = self.config.get("folder_order", [])
        self.min_q = self.config.get("min_questions_per_file", 3)
        self.key_q = self.config.get("key_questions_per_file", 1)

        os.makedirs(self.bank_dir, exist_ok=True)

    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Kiểm định một bộ câu hỏi của 1 file PDF."""
        errors = []
        questions = data.get("questions", [])

        # Rule 1: Số lượng câu hỏi >= min_q
        if len(questions) < self.min_q:
            errors.append(f"Số lượng câu hỏi chưa đạt: có {len(questions)}/{self.min_q} câu.")

        # Rule 2: Đúng 1 câu chủ chốt ◎
        key_count = 0
        for idx, q in enumerate(questions, start=1):
            is_key = q.get("is_key", False)
            q_text = q.get("question_text", "")
            if is_key or "◎" in q_text:
                key_count += 1
                q["is_key"] = True
                if not q_text.startswith("◎"):
                    q["question_text"] = "◎ " + q_text.lstrip()

        if key_count != self.key_q:
            errors.append(f"Yêu cầu đúng {self.key_q} câu chủ chốt (◎), nhưng hiện có {key_count} câu.")

        # Rule 3 & 4: Từng câu hỏi phải đủ A, B, C, D và đáp án đúng
        for idx, q in enumerate(questions, start=1):
            q_text = q.get("question_text", "").strip()
            if len(q_text) < 10:
                errors.append(f"Câu {idx}: Nội dung quá ngắn ({len(q_text)} ký tự).")

            options = q.get("options", {})
            for opt_key in ["A", "B", "C", "D"]:
                if opt_key not in options or not str(options[opt_key]).strip():
                    errors.append(f"Câu {idx}: Thiếu phương án lựa chọn {opt_key}.")

            correct = q.get("correct_answer", "").strip().upper()
            if correct not in ["A", "B", "C", "D"]:
                errors.append(f"Câu {idx}: Đáp án đúng '{correct}' không hợp lệ (phải là A, B, C hoặc D).")

        # Rule 5: Kiểm tra tính dàn trải (không trùng lặp nội dung câu hỏi)
        q_texts = [re.sub(r"[^\w\s]", "", q.get("question_text", "").lower()).split() for q in questions]
        for i in range(len(q_texts)):
            for j in range(i + 1, len(q_texts)):
                set_i = set(q_texts[i])
                set_j = set(q_texts[j])
                if set_i and set_j:
                    overlap = len(set_i & set_j) / min(len(set_i), len(set_j))
                    if overlap > 0.8:
                        errors.append(f"Câu {i+1} và Câu {j+1} có độ trùng lặp quá cao ({overlap*100:.0f}%). Cần nội dung dàn trải hơn.")

        is_valid = (len(errors) == 0)
        return is_valid, errors

    def save_questions(self, data: Dict[str, Any], pdf_path: str = "") -> str:
        """Thẩm định và lưu bộ câu hỏi vào ngân hàng câu hỏi (questions_bank).
        
        Tham số mới:
          pdf_path: Đường dẫn file PDF gốc — nếu có, sẽ lưu metadata (size, mtime, hash)
                    vào JSON để hệ thống phát hiện khi PDF bị thay đổi và tái tạo câu hỏi.
        """
        import time as _t
        from pdf_extractor import get_pdf_file_info

        is_valid, errors = self.validate_data(data)
        data["status"] = "OK" if is_valid else "INVALID"
        data["validation_errors"] = errors

        # Lưu thời điểm sinh câu hỏi và phiên bản
        data["generated_at"] = _t.time()
        data["generated_at_iso"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
        data["app_version"] = "1.4"

        # Lưu metadata file PDF để phát hiện thay đổi trong tương lai
        if pdf_path and os.path.exists(pdf_path):
            data["pdf_metadata"] = get_pdf_file_info(pdf_path)
        elif "pdf_metadata" not in data:
            data["pdf_metadata"] = {}

        folder_name = data.get("folder_name", "Unknown")
        folder_slug = folder_name.split()[0]
        file_name = data.get("file_name", "unknown.pdf")
        base_name = os.path.splitext(file_name)[0]

        subfolder = os.path.join(self.bank_dir, folder_slug)
        os.makedirs(subfolder, exist_ok=True)

        json_path = os.path.join(subfolder, f"{base_name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return json_path

    def get_file_questions(self, folder_slug: str, base_name: str) -> Optional[Dict[str, Any]]:
        """Đọc câu hỏi đã lưu của 1 file cụ thể."""
        json_path = os.path.join(self.bank_dir, folder_slug, f"{base_name}.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def get_progress_report(self) -> Dict[str, Any]:
        """Tạo báo cáo tiến độ toàn diện cho 409 file trong tất cả các thư mục nguồn."""
        all_sources = scan_all_sources(self.source_dir, self.folder_order)
        report = {
            "total_files": len(all_sources),
            "total_ok": 0,
            "total_invalid": 0,
            "total_missing": 0,
            "by_folder": {}
        }

        for item in all_sources:
            folder_name = item["folder_name"]
            folder_slug = folder_name.split()[0]
            base_name = os.path.splitext(item["filename"])[0]

            if folder_slug not in report["by_folder"]:
                report["by_folder"][folder_slug] = {
                    "folder_name": folder_name,
                    "folder_priority": item["folder_priority"],
                    "total": 0,
                    "ok": 0,
                    "invalid": 0,
                    "missing": 0,
                    "files": []
                }

            f_stat = report["by_folder"][folder_slug]
            f_stat["total"] += 1

            saved_q = self.get_file_questions(folder_slug, base_name)
            if saved_q:
                status = saved_q.get("status", "INVALID")
                if status == "OK":
                    f_stat["ok"] += 1
                    report["total_ok"] += 1
                    status_display = "OK"
                else:
                    f_stat["invalid"] += 1
                    report["total_invalid"] += 1
                    status_display = "INVALID"
            else:
                f_stat["missing"] += 1
                report["total_missing"] += 1
                status_display = "MISSING"

            f_stat["files"].append({
                "filename": item["filename"],
                "base_name": base_name,
                "status": status_display
            })

        return report

    def print_progress(self):
        """In bảng tiến độ trực quan ra màn hình terminal."""
        report = self.get_progress_report()
        print("=" * 72)
        print(f"📊 BÁO CÁO TIẾN ĐỘ NGÂN HÀNG CÂU HỎI (TỔNG CỘNG: {report['total_files']} FILE)")
        print("=" * 72)
        print(f"{'ƯU TIÊN':<8} | {'THƯ MỤC':<26} | {'TỔNG':<5} | {'OK':<5} | {'LỖI':<5} | {'THIẾU':<6} | {'TIẾN ĐỘ'}")
        print("-" * 72)

        for folder_slug in sorted(report["by_folder"].keys(), key=lambda x: report["by_folder"][x]["folder_priority"]):
            st = report["by_folder"][folder_slug]
            pct = (st["ok"] / st["total"] * 100) if st["total"] > 0 else 0
            name_short = (st["folder_name"][:24] + "..") if len(st["folder_name"]) > 26 else st["folder_name"]
            print(f"Ưu tiên {st['folder_priority']:<1} | {name_short:<26} | {st['total']:<5} | {st['ok']:<5} | {st['invalid']:<5} | {st['missing']:<6} | {pct:>5.1f}%")

        print("-" * 72)
        total_pct = (report['total_ok'] / report['total_files'] * 100) if report['total_files'] > 0 else 0
        print(f"TỔNG CỘNG: {report['total_ok']} ĐẠT OK / {report['total_files']} FILE ({total_pct:.1f}%) | {report['total_invalid']} LỖI | {report['total_missing']} CHƯA LÀM")
        print("=" * 72)


def validate_questions_data(data: Dict[str, Any], config_path: str = "config.json") -> Tuple[bool, List[str]]:
    """Hàm tiện ích cấp module để kiểm định nhanh cấu trúc bộ câu hỏi."""
    validator = QuestionValidator(config_path)
    return validator.validate_data(data)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    validator = QuestionValidator()
    validator.print_progress()
