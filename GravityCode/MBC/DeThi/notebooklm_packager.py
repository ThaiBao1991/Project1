# -*- coding: utf-8 -*-
"""
Module: notebooklm_packager.py
Mục đích: Đóng gói tài liệu tiêu chuẩn và prompt chuyên biệt cho Google NotebookLM.
Đảm bảo sinh ít nhất 3 câu hỏi trắc nghiệm / file, nội dung dàn trải và có đúng 1 câu chủ chốt ◎.
Hỗ trợ parse ngược kết quả từ NotebookLM về chuẩn dữ liệu hệ thống.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
from pdf_extractor import extract_pdf_content


NOTEBOOKLM_PROMPT_TEMPLATE = """Bạn là chuyên gia thẩm định và đào tạo tay nghề phòng Đảm bảo Chất lượng (BHCL) của công ty Mabuchi Motor.
Dựa CHÍNH XÁC vào nội dung tài liệu tiêu chuẩn kỹ thuật dưới đây, hãy tạo ra một bộ câu hỏi trắc nghiệm kiểm tra nhận định tư cách nhân viên/đội trưởng.

--- THÔNG TIN TÀI LIỆU NGUỒN ---
Tên tài liệu: {standard_title}
Mã số/Mã máy đo: {machine_code}
File gốc: {filename} (Thư mục: {folder_name})

--- NỘI DUNG TÀI LIỆU TIÊU CHUẨN ---
{document_text}

--- YÊU CẦU BẮT BUỘC ĐỐI VỚI BỘ CÂU HỎI ---
1. SỐ LƯỢNG CÂU HỎI: Tạo ÍT NHẤT 3 CÂU HỎI TRẮC NGHIỆM (4 lựa chọn A, B, C, D).
2. NỘI DUNG DÀN TRẢI ĐỀU:
   - Câu 1: Về ngoại quan, mục đích, tiến độ kiểm tra, thiết lập ban đầu (điểm 0, tư thế đặt, môi trường...).
   - Câu 2: Về thông số kỹ thuật chi tiết, phương pháp đo/kiểm, tiêu chuẩn phán định (dung sai, giá trị đo, tần suất...).
   - Câu 3: Về phương pháp xử lý khi có bất thường, quản lý bảo quản, chống gỉ sét, 4S hoặc ghi chép báo cáo.
3. ĐÚNG 1 CÂU CHỦ CHỐT (ĐÁNH DẤU ◎):
   - Trong các câu hỏi trên, PHẢI CHỌN ĐÚNG 1 CÂU QUAN TRỌNG NHẤT mang tính quyết định an toàn/chất lượng để đánh dấu ký hiệu ◎ vào trước nội dung câu hỏi.
   - Đây là câu hỏi trọng yếu: Người thi sai câu này sẽ bị trượt ngay lập tức theo quy chuẩn kiểm tra REV 13.
4. TÍNH CHÍNH XÁC:
   - Đáp án đúng phải trích dẫn trực tiếp từ văn bản (có căn cứ rõ ràng).
   - 3 phương án gây nhiễu phải hợp lý, sát thực tế sản xuất của Mabuchi Motor.
   - Đối tượng kiểm tra mặc định: "Đội trưởng LK, TP, HC, ĐGSP, GCCK" hoặc đối tượng phù hợp nhất trong tài liệu.

--- ĐỊNH DẠNG ĐẦU RA YÊU CẦU (JSON CHUẨN) ---
Hãy trả về DUY NHẤT một khối JSON hợp lệ theo đúng cấu trúc sau (không kèm lời chào hay giải thích ngoài JSON):
```json
{{
  "file_name": "{filename}",
  "folder_name": "{folder_name}",
  "doc_title": "{standard_title}",
  "doc_code": "{machine_code}",
  "target_audience": "Đội LK, TP, ĐGSP, HC, GCCK",
  "questions": [
    {{
      "question_number": 1,
      "is_key": false,
      "question_text": "Nội dung câu hỏi 1...?",
      "options": {{
        "A": "Nội dung lựa chọn A",
        "B": "Nội dung lựa chọn B",
        "C": "Nội dung lựa chọn C",
        "D": "Nội dung lựa chọn D"
      }},
      "correct_answer": "A",
      "reference_note": "Căn cứ theo mục 1: ..."
    }},
    {{
      "question_number": 2,
      "is_key": true,
      "question_text": "◎ Nội dung câu hỏi chủ chốt quan trọng...?",
      "options": {{
        "A": "Nội dung lựa chọn A",
        "B": "Nội dung lựa chọn B",
        "C": "Nội dung lựa chọn C",
        "D": "Nội dung lựa chọn D"
      }},
      "correct_answer": "D",
      "reference_note": "Căn cứ theo mục 4: ..."
    }},
    {{
      "question_number": 3,
      "is_key": false,
      "question_text": "Nội dung câu hỏi 3...?",
      "options": {{
        "A": "Nội dung lựa chọn A",
        "B": "Nội dung lựa chọn B",
        "C": "Nội dung lựa chọn C",
        "D": "Nội dung lựa chọn D"
      }},
      "correct_answer": "B",
      "reference_note": "Căn cứ theo mục 2: ..."
    }}
  ]
}}
```
"""


def generate_notebooklm_prompt(pdf_path: str, folder_name: str) -> str:
    """Tạo nội dung prompt đầy đủ sẵn sàng copy vào NotebookLM hoặc gọi API."""
    extracted = extract_pdf_content(pdf_path)
    meta = extracted["metadata"]
    filename = extracted["filename"]

    # Giới hạn nội dung nếu quá dài (thường các file tiêu chuẩn 2-6 trang ~ 2000-8000 ký tự)
    doc_text = extracted["full_text"]
    if len(doc_text) > 25000:
        doc_text = doc_text[:25000] + "\n...[Văn bản được rút gọn]..."

    prompt = NOTEBOOKLM_PROMPT_TEMPLATE.format(
        standard_title=meta["standard_title"],
        machine_code=meta["machine_code"],
        filename=filename,
        folder_name=folder_name,
        document_text=doc_text
    )
    return prompt


def package_pdf_to_file(pdf_path: str, folder_name: str, output_dir: str) -> str:
    """Đóng gói file PDF thành file text prompt lưu tại KetQua/prompts_for_notebooklm/."""
    prompt = generate_notebooklm_prompt(pdf_path, folder_name)
    folder_slug = folder_name.split()[0]
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    target_subfolder = os.path.join(output_dir, folder_slug)
    os.makedirs(target_subfolder, exist_ok=True)

    prompt_filepath = os.path.join(target_subfolder, f"{base_name}_prompt.txt")
    with open(prompt_filepath, "w", encoding="utf-8") as f:
        f.write(prompt)

    return prompt_filepath


def parse_notebooklm_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Phân tích phản hồi từ NotebookLM hoặc LLM để lấy đối tượng JSON chuẩn.
    Tự động lọc bỏ markdown block ```json ... ``` nếu có.
    """
    if not response_text:
        return None

    # Tìm khối JSON trong response
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response_text)
    if json_match:
        clean_json_str = json_match.group(1).strip()
    else:
        # Nếu không có block ``` thì tìm cặp ngoặc { ... } ngoài cùng
        start = response_text.find("{")
        end = response_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            clean_json_str = response_text[start:end+1]
        else:
            clean_json_str = response_text.strip()

    try:
        data = json.loads(clean_json_str)
        # Chuẩn hóa cấu trúc câu hỏi
        if "questions" in data and isinstance(data["questions"], list):
            for q in data["questions"]:
                # Đảm bảo cờ is_key đồng bộ với ký hiệu ◎
                q_text = q.get("question_text", "")
                if "◎" in q_text:
                    q["is_key"] = True
                elif q.get("is_key"):
                    if not q_text.startswith("◎"):
                        q["question_text"] = "◎ " + q_text
            return data
    except Exception as e:
        print(f"Lỗi parse JSON phản hồi: {e}")
        return None
    return None


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    sample = os.path.join("Source", "2-000 Ban V IT HOA", "000-0-V.pdf")
    if os.path.exists(sample):
        out_prompt = package_pdf_to_file(sample, "2-000 Ban V IT HOA", "KetQua/prompts_for_notebooklm")
        print(f"Đã tạo gói prompt cho NotebookLM: {out_prompt}")
    else:
        print("Không tìm thấy file mẫu.")
