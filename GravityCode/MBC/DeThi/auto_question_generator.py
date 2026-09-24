# -*- coding: utf-8 -*-
"""
Module: auto_question_generator.py
Mục đích: Tự động sinh câu hỏi trắc nghiệm từ các file PDF tiêu chuẩn Mabuchi Motor.
Sử dụng Gemini Files API — upload PDF trực tiếp để Gemini đọc tài liệu gốc (chất lượng cao hơn
extract text), kết hợp với GeminiCoordinator từ gemini_safe.py để xoay vòng key an toàn.
Hỗ trợ resume: bỏ qua file đã có câu hỏi OK trong ngân hàng.
"""

import os
import sys
import json
import time
import re
import requests
import random
from typing import List, Dict, Optional, Any

try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from pdf_extractor import scan_all_sources
from notebooklm_packager import NOTEBOOKLM_PROMPT_TEMPLATE
from question_validator import QuestionValidator
from settings_reader import load_gemini_keys, get_active_model_list


# ─────────────────────────────────────────────────────────────
# Gemini Files API — upload PDF và gọi với file reference
# ─────────────────────────────────────────────────────────────
GEMINI_FILES_UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files"
GEMINI_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Model mặc định nếu settings không có
DEFAULT_MODELS = [
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
]

# Prompt template cho Gemini (gọn hơn, tập trung vào yêu cầu)
GEMINI_AUTO_PROMPT = """Bạn là chuyên gia thẩm định tay nghề phòng BHCL - Mabuchi Motor Vietnam.
Dựa CHÍNH XÁC vào tài liệu tiêu chuẩn kỹ thuật đính kèm, hãy tạo BỘ CÂU HỎI TRẮC NGHIỆM để kiểm tra nhận định tư cách nhân viên/đội trưởng.

THÔNG TIN TÀI LIỆU:
- Tên file: {{filename_placeholder}}
- Thư mục: {{folder_placeholder}}

YÊU CẦU BẮT BUỘC:
1. TỐI THIỂU 3 CÂU HỎI trắc nghiệm (4 lựa chọn A, B, C, D).
2. NỘI DUNG DÀN TRẢI đều: 1 câu về ngoại quan/mục đích/tiến độ kiểm tra; 1 câu về thông số kỹ thuật chi tiết/phương pháp đo; 1 câu về xử lý bất thường/bảo quản/4S.
3. ĐÚNG 1 CÂU CHỦ CHỐT (ký hiệu ◎): Câu quan trọng nhất về an toàn hoặc chất lượng bắt buộc — sai câu này sẽ không đạt ngay dù điểm tổng đạt yêu cầu.
   CHÚ Ý QUAN TRỌNG: Vị trí câu hỏi chủ chốt (◎) PHẢI ĐƯỢC ĐẶT NGẪU NHIÊN (có thể nằm ở câu 1, câu 2, hoặc câu 3), TUYỆT ĐỐI KHÔNG cố định luôn là câu số 2!
4. Đáp án đúng PHẢI căn cứ trực tiếp từ nội dung trong tài liệu.
5. 3 phương án sai phải hợp lý, sát thực tế sản xuất Mabuchi Motor.

TRẢ VỀ DUY NHẤT một JSON hợp lệ (không có lời giải thích ngoài JSON), ví dụ cấu trúc:
{{"file_name":"<tên file>","folder_name":"<tên thư mục>","doc_title":"<Tên tiêu chuẩn>","doc_code":"<Mã số>","target_audience":"Đội LK, TP, ĐGSP, HC, GCCK","questions":[{{"question_number":1,"is_key":false,"question_text":"<Nội dung câu hỏi>","options":{{"A":"...","B":"...","C":"...","D":"..."}},"correct_answer":"A","reference_note":"<Trích dẫn>"}},{{"question_number":2,"is_key":true,"question_text":"◎ <Nội dung câu hỏi chủ chốt>","options":{{"A":"...","B":"...","C":"...","D":"..."}},"correct_answer":"C","reference_note":"<Trích dẫn>"}},{{"question_number":3,"is_key":false,"question_text":"<Nội dung câu hỏi>","options":{{"A":"...","B":"...","C":"...","D":"..."}},"correct_answer":"B","reference_note":"<Trích dẫn>"}}]}}"""


def randomize_questions_order(questions: List[Dict]) -> List[Dict]:
    """
    Xáo trộn ngẫu nhiên thứ tự các câu hỏi trong bộ câu hỏi của 1 file PDF.
    Đảm bảo câu hỏi chủ chốt (ký hiệu ◎ hoặc is_key=True) xuất hiện ngẫu nhiên
    ở bất kỳ vị trí nào (câu 1, câu 2, câu 3, ...), loại bỏ hoàn toàn quy luật 2, 5, 8.
    Đánh lại số thứ tự question_number tương ứng từ 1..N.
    """
    if not questions or len(questions) <= 1:
        return questions
    shuffled = list(questions)
    random.shuffle(shuffled)
    for idx, q in enumerate(shuffled, start=1):
        q["question_number"] = idx
    return shuffled



def _pick_key(keys: List[Dict], exclude: set) -> Optional[Dict]:
    """Chọn key active không bị cooldown và không trong exclude."""
    now = time.time()
    available = [
        k for k in keys
        if k.get("status") in ("active", "exhausted", None)
        and k.get("key") not in exclude
        and k.get("cooldown_until", 0) < now
    ]
    if not available:
        return None
    return random.choice(available)


def _upload_pdf_to_gemini(pdf_path: str, api_key: str, timeout: int = 60) -> Optional[str]:
    """
    Upload file PDF lên Gemini Files API.
    Trả về file_uri dùng cho generateContent, hoặc None nếu thất bại.
    """
    filename = os.path.basename(pdf_path)
    file_size = os.path.getsize(pdf_path)

    headers = {
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(file_size),
        "X-Goog-Upload-Header-Content-Type": "application/pdf",
        "Content-Type": "application/json"
    }
    meta_body = json.dumps({"file": {"display_name": filename}})

    try:
        resp = requests.post(
            f"{GEMINI_FILES_UPLOAD_URL}?key={api_key}",
            headers=headers,
            data=meta_body.encode("utf-8"),
            timeout=timeout
        )
        if resp.status_code not in (200, 201):
            return None

        upload_url = resp.headers.get("X-Goog-Upload-URL")
        if not upload_url:
            return None

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        upload_resp = requests.post(
            upload_url,
            headers={
                "Content-Length": str(file_size),
                "X-Goog-Upload-Offset": "0",
                "X-Goog-Upload-Command": "upload, finalize"
            },
            data=pdf_bytes,
            timeout=timeout
        )

        if upload_resp.status_code in (200, 201):
            data = upload_resp.json()
            return data.get("file", {}).get("uri")

    except Exception:
        pass

    return None


def _call_gemini_with_file(prompt: str, file_uri: str, api_key: str,
                            model: str, timeout: int = 90) -> Dict:
    """Gọi Gemini generateContent với file URI đã upload + prompt."""
    url = GEMINI_GENERATE_URL.format(model=model) + f"?key={api_key}"
    body = {
        "contents": [{
            "parts": [
                {"file_data": {"mime_type": "application/pdf", "file_uri": file_uri}},
                {"text": prompt}
            ]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json"
        }
    }
    try:
        resp = requests.post(url, json=body, headers={"Content-Type": "application/json"}, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts).strip()
                return {"ok": True, "text": text, "status_code": 200}
            return {"ok": False, "text": "", "error": "empty response", "status_code": 200}
        return {"ok": False, "text": "", "error": f"HTTP {resp.status_code}", "status_code": resp.status_code, "body": resp.text[:200]}
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "status_code": 0}


def _call_gemini_with_text(prompt: str, api_key: str, model: str, timeout: int = 90) -> Dict:
    """Fallback: Gọi Gemini generateContent chỉ với text (không dùng Files API)."""
    url = GEMINI_GENERATE_URL.format(model=model) + f"?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json"
        }
    }
    try:
        resp = requests.post(url, json=body, headers={"Content-Type": "application/json"}, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts).strip()
                return {"ok": True, "text": text, "status_code": 200}
            return {"ok": False, "text": "", "error": "empty response", "status_code": 200}
        return {"ok": False, "text": "", "error": f"HTTP {resp.status_code}", "status_code": resp.status_code, "body": resp.text[:300]}
    except Exception as e:
        return {"ok": False, "text": "", "error": str(e), "status_code": 0}


def _parse_json_response(text: str) -> Optional[Dict]:
    """Parse JSON từ phản hồi Gemini, xử lý trường hợp có markdown block."""
    if not text:
        return None
    # Loại bỏ markdown block nếu có
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end+1]
    try:
        return json.loads(text)
    except Exception:
        # Thử repair basic
        try:
            text_fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)
            return json.loads(text_fixed)
        except Exception:
            return None


class AutoQuestionGenerator:
    """Engine tự động sinh câu hỏi từ PDF bằng Gemini API."""

    def __init__(self, config_path: str = "config.json", log_fn=None):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.source_dir = self.config.get("source_dir", "Source")
        self.folder_order = self.config.get("folder_order", [])
        self.log = log_fn or print

        self.validator = QuestionValidator(config_path)
        self.keys = load_gemini_keys()
        self.models = get_active_model_list() or DEFAULT_MODELS

        if not self.keys:
            raise RuntimeError("❌ Không tìm thấy API key Gemini. Kiểm tra settings_reader.py và AskCpl/settings.json.")

        self.log(f"✅ Đã load {len(self.keys)} API key(s) từ {len(set(k['email'] for k in self.keys))} account(s).")
        self.log(f"✅ Model list: {self.models[:3]}...")

    def _build_prompt(self, filename: str, folder_name: str, extra_requirements: str = "") -> str:
        """Xây dựng prompt đầy đủ với tên file và thư mục được điền vào.
        extra_requirements: Yêu cầu bổ sung tùy chỉnh từ người dùng (ghép vào cuối prompt).
        """
        base = GEMINI_AUTO_PROMPT.replace(
            "{{filename_placeholder}}", filename
        ).replace(
            "{{folder_placeholder}}", folder_name
        )
        if extra_requirements and extra_requirements.strip():
            base += (
                "\n\nYÊu CẦU BỔ SUNG TÙY CHỈNH (do người dùng cấu hình thêm — bắt buộc tuân thủ):\n"
                + extra_requirements.strip()
            )
        return base

    def _make_text_prompt(self, filename: str, folder_name: str, full_text: str, extra_requirements: str = "") -> str:
        """Tạo prompt text khi không dùng được Files API."""
        doc_text = full_text
        if len(doc_text) > 20000:
            doc_text = doc_text[:20000] + "\n...[rút gọn]..."
        base_prompt = self._build_prompt(filename, folder_name, extra_requirements)
        return (
            f"Tài liệu: {filename} ({folder_name})\n\n"
            f"Nội dung:\n{doc_text}\n\n"
            + base_prompt
        )

    def generate_for_file(self, pdf_path: str, folder_name: str,
                          full_text: str = "", max_retries: int = 3,
                          extra_requirements: str = "") -> Optional[Dict]:
        """
        Sinh câu hỏi cho 1 file PDF. Thử Files API trước, fallback sang text prompt.
        extra_requirements: Yêu cầu tùy chỉnh bổ sung từ người dùng.
        Trả về dict data hoặc None nếu thất bại.
        """
        filename = os.path.basename(pdf_path)
        prompt_only = self._build_prompt(filename, folder_name, extra_requirements)
        exclude_keys = set()

        for attempt in range(max_retries):
            key_obj = _pick_key(self.keys, exclude_keys)
            if not key_obj:
                self.log(f"  ⚠ Không còn key khả dụng cho {filename}. Chờ 30s...")
                time.sleep(30)
                exclude_keys.clear()
                key_obj = _pick_key(self.keys, exclude_keys)
                if not key_obj:
                    return None

            api_key = key_obj["key"]
            email = key_obj.get("email", "?")
            model = self.models[attempt % len(self.models)]

            # Thử 1: Gemini Files API (chất lượng cao nhất)
            file_uri = _upload_pdf_to_gemini(pdf_path, api_key)
            if file_uri:
                result = _call_gemini_with_file(prompt_only, file_uri, api_key, model)
            else:
                # Fallback: Text prompt với nội dung đã extract
                text_prompt = self._make_text_prompt(filename, folder_name, full_text, extra_requirements)
                result = _call_gemini_with_text(text_prompt, api_key, model)

            if result.get("ok") and result.get("text"):
                data = _parse_json_response(result["text"])
                if data and "questions" in data:
                    # Điền thêm metadata nếu AI bỏ sót
                    data.setdefault("file_name", filename)
                    data.setdefault("folder_name", folder_name)
                    # Xáo trộn thứ tự câu hỏi ngẫu nhiên (chống quy luật câu 2, 5, 8...)
                    data["questions"] = randomize_questions_order(data["questions"])
                    return data
                self.log(f"  ⚠ [{filename}] JSON parse lỗi lần {attempt+1}. Thử lại...")
            else:
                status = result.get("status_code", 0)
                err = result.get("error", result.get("body", ""))[:80]
                if status in (429, 503):
                    self.log(f"  ⚠ [{filename}] Key {email} bị rate limit (HTTP {status}). Đổi key...")
                    key_obj["cooldown_until"] = time.time() + 65
                    exclude_keys.add(api_key)
                else:
                    self.log(f"  ⚠ [{filename}] Lỗi HTTP {status}: {err}. Thử lại lần {attempt+1}...")
                    if status in (400, 401, 403):
                        exclude_keys.add(api_key)

            time.sleep(3 + attempt * 2)

        return None

    def is_already_done(self, folder_slug: str, base_name: str, pdf_path: str = "") -> bool:
        """
        Kiểm tra file đã có câu hỏi OK trong ngân hàng chưa.
        Nếu có pdf_path: còn kiểm tra STALE — PDF đã thay đổi kể từ lần sinh câu hỏi trước
        (khác file_size hoặc khác file_hash_short) thì coi là chưa xong → tái tạo.
        """
        q = self.validator.get_file_questions(folder_slug, base_name)
        if q is None or q.get("status") != "OK":
            return False

        # Kiểm tra STALE: so sánh metadata file PDF hiện tại với lúc sinh
        if pdf_path and os.path.exists(pdf_path):
            from pdf_extractor import get_pdf_file_info
            saved_meta = q.get("pdf_metadata", {})
            if saved_meta:  # chỉ kiểm tra nếu đã có metadata (các file JSON cũ không có → bỏ qua)
                curr_info = get_pdf_file_info(pdf_path)
                saved_size = saved_meta.get("file_size_bytes", -1)
                saved_hash = saved_meta.get("file_hash_short", "")
                curr_size  = curr_info.get("file_size_bytes", -1)
                curr_hash  = curr_info.get("file_hash_short", "")

                if saved_size > 0 and curr_size > 0 and saved_size != curr_size:
                    self.log(f"  🔄 STALE [{base_name}]: Kích thước PDF thay đổi "
                             f"({saved_size:,} → {curr_size:,} bytes) → Tái tạo câu hỏi...")
                    return False

                if saved_hash and curr_hash and saved_hash != curr_hash:
                    self.log(f"  🔄 STALE [{base_name}]: Nội dung PDF đã thay đổi "
                             f"(hash {saved_hash} → {curr_hash}) → Tái tạo câu hỏi...")
                    return False

        return True

    def detect_new_and_missing_files(self, selected_folders: List[str] = None) -> Dict[str, Any]:
        """
        Đối chiếu thời gian thực giữa thư mục Source/ và ngân hàng câu hỏi.
        Phân loại chính xác:
        - done_count / done_files: các file đã hoàn thành đạt chuẩn OK.
        - missing_count / missing_files: các file mới bổ sung hoặc chưa hoàn thành.
        """
        folders = selected_folders or self.folder_order
        all_sources = scan_all_sources(self.source_dir, self.folder_order)
        sources = [s for s in all_sources if s["folder_name"] in folders]

        done_list = []
        missing_list = []

        for item in sources:
            folder_slug = item["folder_name"].split()[0]
            base_name = os.path.splitext(item["filename"])[0]
            pdf_path_item = item["full_path"]
            if self.is_already_done(folder_slug, base_name, pdf_path_item):
                done_list.append(item)
            else:
                missing_list.append(item)

        return {
            "total_count": len(sources),
            "done_count": len(done_list),
            "missing_count": len(missing_list),
            "done_files": done_list,
            "missing_files": missing_list
        }

    def scan_progress(self, selected_folders: List[str] = None) -> Dict[str, Any]:
        """
        Quét trạng thái hiện tại của tất cả tài liệu nguồn trong các thư mục.
        Lưu kết quả tổng hợp vào KetQua/progress_status.json để GUI hoặc các module khác đọc nhanh.
        """
        folders = selected_folders or self.folder_order
        all_sources = scan_all_sources(self.source_dir, self.folder_order)
        output_dir = self.config.get("output_dir", "KetQua")

        folder_stats = {}
        for fn in folders:
            folder_slug = fn.split()[0]
            folder_stats[fn] = {
                "folder_name": fn,
                "folder_slug": folder_slug,
                "total": 0,
                "done": 0,
                "missing": 0,
                "percent": 0.0,
                "exam_docx": os.path.exists(os.path.join(output_dir, folder_slug, f"DE_THI_{folder_slug}.docx")),
                "ans_docx": os.path.exists(os.path.join(output_dir, folder_slug, f"DAP_AN_{folder_slug}.docx"))
            }

        total_all = 0
        done_all = 0

        for item in all_sources:
            fn = item["folder_name"]
            if fn not in folder_stats:
                continue
            folder_slug = fn.split()[0]
            base_name = os.path.splitext(item["filename"])[0]

            folder_stats[fn]["total"] += 1
            total_all += 1
            if self.is_already_done(folder_slug, base_name):
                folder_stats[fn]["done"] += 1
                done_all += 1
            else:
                folder_stats[fn]["missing"] += 1

        for fn, stat in folder_stats.items():
            if stat["total"] > 0:
                stat["percent"] = round((stat["done"] / stat["total"]) * 100, 1)

        overall = {
            "total": total_all,
            "done": done_all,
            "missing": total_all - done_all,
            "percent": round((done_all / max(total_all, 1)) * 100, 1),
            "merged_exam_exists": os.path.exists(os.path.join(output_dir, "DE THI MOI TONG HOP.docx")),
            "merged_ans_exists": os.path.exists(os.path.join(output_dir, "DAP AN TONG HOP.docx")),
            "folders": folder_stats
        }

        # Lưu tóm tắt tiến độ
        try:
            status_file = os.path.join(output_dir, "progress_status.json")
            os.makedirs(output_dir, exist_ok=True)
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(overall, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"⚠ Lỗi lưu progress_status.json: {e}")

        return overall

    def run_batch(self, selected_folders: List[str] = None,
                  log_progress_every: int = 5,
                  stop_check=None,
                  pause_check=None,
                  progress_callback=None,
                  force_regenerate: bool = False,
                  extra_requirements: str = "") -> Dict:
        """
        Chạy sinh câu hỏi tự động hàng loạt cho các thư mục được chọn.
        Hỗ trợ:
        - stop_check(): callable -> bool để dừng an toàn
        - pause_check(): callable -> bool để tạm dừng
        - progress_callback(dict): thông báo tiến độ cho GUI
        - force_regenerate: True để làm lại từ đầu (bỏ qua cache OK)
        - extra_requirements: Yêu cầu tùy chỉnh bổ sung cho Gemini prompt
        """
        folders = selected_folders or self.folder_order
        all_sources = scan_all_sources(self.source_dir, self.folder_order)

        # Lọc theo folders được chọn
        sources = [s for s in all_sources if s["folder_name"] in folders]

        total = len(sources)
        done = 0
        skipped = 0
        failed = 0
        invalid_saved = 0

        mode_desc = "LÀM LẠI TỪ ĐẦU (Ghi đè)" if force_regenerate else "CHẠY BỔ SUNG / TIẾP TỤC (Bỏ qua file đã OK)"
        self.log(f"\n🚀 BẮT ĐẦU SINH ĐỀ: {total} file trong {len(folders)} thư mục")
        self.log(f"   Chế độ: {mode_desc}")
        self.log(f"   Keys hoạt động: {len(self.keys)} | Model ưu tiên: {self.models[0]}")
        self.log("=" * 65)

        t_start = time.time()

        for idx, item in enumerate(sources, start=1):
            # Kiểm tra dừng
            if stop_check and stop_check():
                self.log("\n⛔ Đã nhận tín hiệu dừng từ người dùng.")
                break

            # Kiểm tra tạm dừng
            while pause_check and pause_check():
                if stop_check and stop_check():
                    break
                time.sleep(1)

            folder_slug = item["folder_name"].split()[0]
            base_name = os.path.splitext(item["filename"])[0]
            pdf_path = item["full_path"]

            # Bỏ qua nếu đã xong (khi không chọn force_regenerate)
            if not force_regenerate and self.is_already_done(folder_slug, base_name, pdf_path):
                skipped += 1
                if progress_callback:
                    progress_callback({
                        "current_idx": idx,
                        "total": total,
                        "current_file": item["filename"],
                        "folder_name": item["folder_name"],
                        "status": "SKIP_OK",
                        "done": done,
                        "skipped": skipped,
                        "failed": failed
                    })
                if idx % log_progress_every == 0:
                    self.log(f"  [{idx}/{total}] Đã có sẵn (OK): {item['filename']}")
                continue

            # Đọc text fallback
            try:
                from pdf_extractor import extract_pdf_content
                extracted = extract_pdf_content(pdf_path)
                full_text = extracted.get("full_text", "")
            except Exception:
                full_text = ""

            self.log(f"  [{idx}/{total}] Đang xử lý: {item['filename']} ({folder_slug})")
            if progress_callback:
                progress_callback({
                    "current_idx": idx,
                    "total": total,
                    "current_file": item["filename"],
                    "folder_name": item["folder_name"],
                    "status": "PROCESSING",
                    "done": done,
                    "skipped": skipped,
                    "failed": failed
                })

            data = self.generate_for_file(pdf_path, item["folder_name"], full_text,
                                          extra_requirements=extra_requirements)

            if data:
                is_valid, errors = self.validator.validate_data(data)
                saved_path = self.validator.save_questions(data, pdf_path=pdf_path)
                if is_valid:
                    done += 1
                    file_status = "OK"
                    self.log(f"  ✅ [{idx}/{total}] OK: {item['filename']} ({len(data.get('questions', []))} câu hỏi) → {os.path.basename(saved_path)}")
                else:
                    invalid_saved += 1
                    file_status = "INVALID"
                    self.log(f"  ⚠ [{idx}/{total}] Cần bổ sung ({len(errors)} lỗi): {item['filename']}")
            else:
                failed += 1
                file_status = "FAILED"
                self.log(f"  ❌ [{idx}/{total}] Thất bại (hết lần thử): {item['filename']}")

            if progress_callback:
                progress_callback({
                    "current_idx": idx,
                    "total": total,
                    "current_file": item["filename"],
                    "folder_name": item["folder_name"],
                    "status": file_status,
                    "done": done,
                    "skipped": skipped,
                    "failed": failed
                })

            # Nghỉ ngơi nhẹ nhàng giữa các file (3.5 - 5.5s)
            time.sleep(random.uniform(3.5, 5.5))

        elapsed = time.time() - t_start
        self.log("\n" + "=" * 65)
        self.log(f"📊 KẾT QUẢ ĐỢT QUÉT")
        self.log(f"   ✅ Mới tạo OK:  {done}")
        self.log(f"   ⏭ Đã có sẵn:    {skipped}")
        self.log(f"   ⚠ Chưa đạt:     {invalid_saved}")
        self.log(f"   ❌ Thất bại:    {failed}")
        self.log(f"   ⏱ Thời gian:    {elapsed/60:.1f} phút")
        self.log("=" * 65)

        # Cập nhật lại file thống kê
        self.scan_progress(selected_folders)

        return {"ok": done, "invalid": invalid_saved, "skipped": skipped, "failed": failed}

    def run_loop_until_complete(self, selected_folders: List[str] = None,
                                max_passes: int = 10,
                                stop_check=None,
                                pause_check=None,
                                progress_callback=None,
                                force_regenerate: bool = False,
                                extra_requirements: str = "") -> Dict:
        """
        VÒNG LẶP TỰ ĐỘNG ĐẾN KHI HOÀN THÀNH (Zero-Error Loop):
        Tự động lặp lại nhiều đợt quét cho đến khi 100% các file PDF đều sinh câu hỏi hợp lệ OK.
        Nếu gặp file bị lỗi do rate limit hoặc gián đoạn, sẽ xoay vòng key và tự động thử lại ở đợt kế tiếp.
        Hỗ trợ:
        - force_regenerate=False (Chế độ Bổ sung / Tiếp tục): bỏ qua các file đã OK, chỉ làm file mới hoặc thiếu.
        - force_regenerate=True (Chế độ Làm lại từ đầu): làm mới toàn bộ.
        - extra_requirements: Chuỗi yêu cầu bổ sung (vd: "Ưu tiên an toàn lao động, không hỏi ngày tháng...")
        """
        folders = selected_folders or self.folder_order

        # Đối chiếu trạng thái hiện tại
        detect = self.detect_new_and_missing_files(folders)
        mode_str = "🔄 LÀM LẠI TỪ ĐẦU (Ghi đè)" if force_regenerate else "⚡ TIẾP TỤC / BỔ SUNG (Chỉ làm phần mới/thiếu)"
        self.log(f"\n🔄 BẮT ĐẦU VÒNG LẶP TỰ ĐỘNG (Tối đa {max_passes} đợt)")
        self.log(f"   Chế độ: {mode_str}")
        if extra_requirements:
            self.log(f"   📝 Yêu cầu thêm: {extra_requirements}")
        self.log(f"   🔍 Tổng số tài liệu: {detect['total_count']} | Đã có sẵn: {detect['done_count']} | Cần xử lý: {detect['missing_count'] if not force_regenerate else detect['total_count']}")

        pass_num = 1
        while pass_num <= max_passes:
            if stop_check and stop_check():
                self.log("⛔ Người dùng đã dừng vòng lặp.")
                break

            # Ở đợt 1 dùng force_regenerate của người dùng chọn. Các đợt sau chỉ làm các file còn sót
            current_force = force_regenerate if pass_num == 1 else False

            self.log(f"\n▶ ĐỢT QUÉT #{pass_num}/{max_passes}...")
            res = self.run_batch(
                selected_folders=folders,
                stop_check=stop_check,
                pause_check=pause_check,
                progress_callback=progress_callback,
                force_regenerate=current_force,
                extra_requirements=extra_requirements
            )

            # Kiểm tra tiến độ tổng thể
            current_stat = self.scan_progress(folders)
            missing = current_stat.get("missing", 0)
            total = current_stat.get("total", 0)

            if missing == 0:
                self.log(f"\n🎉 HOÀN THÀNH 100%! Tất cả {total}/{total} tài liệu đều đã có câu hỏi hợp lệ!")
                break

            if stop_check and stop_check():
                break

            self.log(f"\n⏳ Còn lại {missing}/{total} file chưa hoàn thành. Nghỉ 10 giây trước đợt thử lại tiếp theo...")
            for s in range(10, 0, -1):
                if stop_check and stop_check():
                    break
                time.sleep(1)

            pass_num += 1

        final_stat = self.scan_progress(folders)
        return final_stat


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    gen = AutoQuestionGenerator()
    stat = gen.scan_progress()
    print("Thống kê hiện tại:")
    print(f"Tổng: {stat['total']} | Đã xong: {stat['done']} | Còn thiếu: {stat['missing']} | {stat['percent']}%")

