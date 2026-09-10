import os
import sys
import json
import re
import time
import base64
import urllib.parse
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import requests
import concurrent.futures
from adaptive_learning import (
    LESSON_RESPONSE_SCHEMA,
    build_day_context,
    lesson_to_markdown,
    load_profile,
    load_state,
    parse_lesson_response,
    profile_questions,
    record_generated_lesson,
    save_state,
    validate_lesson,
)
from gemini_image_pipeline import generate_visual_assets
from chunk_merge import split_text, dedup_merge, PartStore
from verified_knowledge import (
    build_fact_context,
    evidence_for_claims,
    load_pack,
    pack_path_for_course,
    validate_fact_claims,
    validate_pack,
)

STOP_REQUESTED = False

def _ts():
    """Trở về timestamp hiện tại dạng [HH:MM:SS]"""
    return datetime.now().strftime("[%H:%M:%S]")

def run_auto_ai(api_keys_list, roadmap_path, doc_dir, out_dir, log_callback, 
                force=False, update_keys_cb=None, enable_followup=True, max_followup=3, start_day=0,
                adaptive_mode=True, generate_visuals=False, image_model="gemini-2.5-flash-image"):
    """
    Chạy tự động phân tích lộ trình học bằng Gemini API.
    Tham số mới:
      - enable_followup: Bật/tắt hỏi bổ sung (YC5)
    """
    global STOP_REQUESTED
    def log(msg):
        log_callback(f"{_ts()} {msg}")
        
    def update_key_on_disk(k_obj):
        try:
            from settings import load_settings, update_gemini_settings
            st = load_settings()
            disk_keys = st.get("gemini", {}).get("api_keys", [])
            target_acct = (k_obj.get("email") or "").strip().lower()
            cd_until = k_obj.get("cooldown_until", 0)
            for dk in disk_keys:
                if dk.get("key") == k_obj.get("key"):
                    dk["status"] = k_obj.get("status", "active")
                    dk["reset_time"] = k_obj.get("reset_time", 0)
                    dk["next_check_time"] = k_obj.get("next_check_time", 0)
                    if "cooldown_until" in k_obj:
                        dk["cooldown_until"] = k_obj["cooldown_until"]
                    if "today_calls" in k_obj:
                        dk["today_calls"] = k_obj["today_calls"]
                    if "today_account_calls" in k_obj:
                        dk["today_account_calls"] = k_obj["today_account_calls"]
                    if "call_date" in k_obj:
                        dk["call_date"] = k_obj["call_date"]
                elif target_acct and (dk.get("email") or "").strip().lower() == target_acct:
                    if cd_until > 0:
                        dk["cooldown_until"] = cd_until
                    if "today_account_calls" in k_obj:
                        dk["today_account_calls"] = k_obj["today_account_calls"]
                    if "call_date" in k_obj:
                        dk["call_date"] = k_obj["call_date"]
            update_gemini_settings(api_keys=disk_keys)
            if update_keys_cb:
                update_keys_cb(disk_keys)
        except Exception as e:
            log(f"Lỗi đồng bộ key: {e}")

    def get_active_key():
        try:
            from settings import load_settings
            st = load_settings()
            current_keys = st.get("gemini", {}).get("api_keys", [])
        except Exception:
            current_keys = api_keys_list
            
        now = int(time.time())
        for k in current_keys:
            status = k.get("status", "active")
            reset_time = k.get("reset_time", 0)
            next_check = k.get("next_check_time", 0)
            
            # YC3: Xử lý key đang bị cạn hạn ngạch (exhausted)
            if status == "exhausted":
                # Nếu đã đến kỳ hạn hồi phục hoàn toàn (24h)
                if reset_time > 0 and now > reset_time:
                    k["status"] = "active"
                    k["reset_time"] = 0
                    k["next_check_time"] = 0
                    update_key_on_disk(k)
                    return k
                
                # Nếu chưa đến kỳ hạn check lại (3 tiếng) -> Bỏ qua
                if next_check > 0 and now < next_check:
                    continue
                
                # Nếu đã quá 3 tiếng -> Cho phép thử lại 1 lần
                return k
                
            if status == "invalid":
                continue
                
            if status == "active":
                return k
        return None
        
    def mark_key_exhausted(k):
        now = int(time.time())
        k["status"] = "exhausted"
        k["reset_time"] = now + 86400          # Thời hạn hồi phục hoàn toàn là 24h sau
        k["next_check_time"] = now + 10800     # 3 tiếng sau mới check lại (3h * 3600 = 10800s)
        k["last_check_time"] = now
        log(f"⚠ Key {k.get('email')} (Project: {k.get('project_id', 'N/A')}) bị đánh dấu Exhausted. Sẽ check lại sau 3 tiếng.")
        update_key_on_disk(k)
        
    def mark_key_invalid(k):
        now = int(time.time())
        k["status"] = "invalid"
        k["last_check_time"] = now
        log(f"✗ Key {k.get('email')} (Project: {k.get('project_id', 'N/A')}) bị đánh dấu Invalid.")
        update_key_on_disk(k)

    def call_gemini_api(prompt_text, log_prefix="", response_schema=None):
        """Gọi Gemini REST API qua gemini_safe (pacing toàn cục, xoay key theo account, phân loại lỗi chuẩn)."""
        from gemini_safe import GeminiCoordinator, ErrorKind

        def _status_cb(key_obj, status, error_msg):
            try:
                now = int(time.time())
                key_obj["status"] = status
                key_obj["error_msg"] = error_msg
                key_obj["last_check_time"] = now
                if status == "exhausted":
                    key_obj["reset_time"] = now + 86400
                    key_obj["next_check_time"] = now + 10800
                elif status in ("active", "invalid"):
                    key_obj["reset_time"] = 0
                    key_obj["next_check_time"] = 0
                update_key_on_disk(key_obj)
            except Exception as e:
                log(f"{log_prefix}⚠ Lỗi đồng bộ key: {e}")

        def _loader():
            try:
                from settings import load_settings
                return load_settings().get("gemini", {}).get("api_keys", [])
            except Exception:
                return api_keys_list

        coord = GeminiCoordinator(
            log_fn=lambda m: log(f"{log_prefix}{m}"),
            on_key_status=_status_cb,
            key_loader=_loader,
            stop_check=lambda: STOP_REQUESTED,
            temperature=0.7,
            max_output_tokens=8192,
            timeout=60,
            lock_after_success=False,
        )

        result = coord.request(prompt_text, response_schema=response_schema)
        if result.get("ok"):
            return result["text"], True, False

        error = result.get("error", {})
        kind = error.get("kind")
        if kind == ErrorKind.ALL_BUDGET_EXHAUSTED:
            log(f"{log_prefix}🛑 Tất cả các tài khoản Google đã đạt ngân sách an toàn hôm nay! Dừng tiến trình để bảo vệ 100% tài khoản.")
            return None, False, True  # Dừng pipeline an toàn
        if kind == ErrorKind.NO_KEY:
            log(f"{log_prefix}⚠ KHÔNG tìm thấy API Key nào khả dụng! Tất cả account đang trong cooldown 60 phút.")
            return None, False, True  # Dừng pipeline — không có key để xử lý tiếp
        if kind == ErrorKind.STOPPED:
            log(f"{log_prefix}🛑 Nhận lệnh dừng khi đang chờ API...")
            return None, False, False
        if response_schema and kind == ErrorKind.REQUEST_BAD:
            log(f"{log_prefix}⚠ Model không nhận structured output; chuyển sang render text tương thích, không vô hiệu hóa key.")
            return call_gemini_api(prompt_text, log_prefix=log_prefix, response_schema=None)
        log(f"{log_prefix}⚠ Lỗi Gemini ({kind}): {error.get('message', '')[:120]}")
        return None, False, False
    try:
        import fitz  # PyMuPDF
    except ImportError:
        log_callback("⚠ Lỗi: Thư viện PyMuPDF chưa được cài đặt.")
        return
        
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    profile = load_profile(out_dir) if adaptive_mode else {}
    learner_state = load_state(out_dir) if adaptive_mode else {}
    knowledge_pack = load_pack(pack_path_for_course(out_dir, profile)) if adaptive_mode else {}
    knowledge_errors = validate_pack(knowledge_pack) if adaptive_mode and knowledge_pack.get("sources") else []
    missing_profile = profile_questions(profile) if adaptive_mode else []
    adaptive_ready = adaptive_mode and not missing_profile
    if adaptive_mode and not adaptive_ready:
        log("ℹ Hồ sơ học chưa đủ; chạy tương thích legacy. Cần bổ sung: " + "; ".join(item["field"] for item in missing_profile))
    elif adaptive_ready:
        log(f"🧠 Adaptive mode: đã nạp hồ sơ '{profile.get('domain')}' và trạng thái người học.")
        if knowledge_errors:
            log("⚠ Knowledge Pack không hợp lệ; không dùng fact từ pack: " + "; ".join(knowledge_errors[:3]))
        elif knowledge_pack.get("sources"):
            log(f"📚 Knowledge Pack: {len(knowledge_pack.get('sources', []))} nguồn đã nạp; fact phải có entity/source hợp lệ.")
        else:
            log("⚠ Chưa có Knowledge Pack: AI chỉ được tạo quy trình học, không được coi chi tiết game là fact đã kiểm chứng.")

    log("Đang đọc file roadmap...")
    try:
        with open(roadmap_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        log(f"⚠ Lỗi đọc roadmap: {e}")
        return
        
    # Tách theo Day X
    # Only accept a real top-level roadmap heading.  Generated prompt content
    # may itself mention "## Day" as an example; treating that as a new lesson
    # created phantom days (45 real days were parsed as 55).
    days_blocks = re.split(r'\n## (Day \d+[a-zA-Z]?\s*[—–-]\s*[^\n]+)\n', "\n" + content)
    days_parsed = []
    
    for i in range(1, len(days_blocks), 2):
        day_title = days_blocks[i].strip()
        day_content = days_blocks[i+1]
        
        pdf_filename = None
        url_match = re.search(r'\(http.*?/([^/]+\.pdf)\)', day_content, re.IGNORECASE)
        if url_match:
            pdf_filename = url_match.group(1)
        else:
            # Roadmaps generated from local reference files store the relevant
            # PDF name as metadata; this keeps the Markdown readable while the
            # loader can still extract the matching source document.
            source_match = re.search(r'<!--\s*sources:\s*([^>]+)\s*-->', day_content, re.IGNORECASE)
            if source_match:
                candidates = [part.strip() for part in source_match.group(1).split(',')]
                pdf_filename = next((part for part in candidates if part.lower().endswith('.pdf')), None)
            
        page_start = 0
        page_end = None
        pages_match = re.search(r'<!--\s*pages:\s*(\d+)-(\d+)\s*-->', day_content)
        if pages_match:
            page_start = int(pages_match.group(1)) - 1
            page_end = int(pages_match.group(2))
            
        prompt_text = ""
        prompt_match = re.search(r'\*\*Prompt:\*\*(.*?)(?=\*\*Bài tập:\*\*|\*\*Tags:\*\*|\Z)', day_content, re.DOTALL)
        if prompt_match:
            prompt_text = prompt_match.group(1).strip()
            
        if prompt_text:
            days_parsed.append({
                "title": f"## {day_title}",
                "pdf": pdf_filename,
                "prompt": prompt_text,
                "page_start": page_start,
                "page_end": page_end
            })
            
    log(f"✓ Đã tìm thấy {len(days_parsed)} Days trong roadmap.")
    
    # === AUTO-RESUME ===
    def get_day_num(title_str):
        import re as _re
        m = _re.search(r'Day\s+(\d+)', title_str, _re.IGNORECASE)
        if m: return int(m.group(1))
        return -1

    completed_days = set()
    incomplete_days_refs = {}
    session_data = []
    session_file = os.path.join(out_dir, "session.json")
    
    if os.path.exists(session_file) and force:
        log("🗑 Force Restart: Xóa session cũ và chạy lại từ Day 1...")
        os.remove(session_file)
    elif os.path.exists(session_file):
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    if content.startswith('"') and content.endswith('"'):
                        content = content[1:-1]
                        import urllib.parse as _urlparse
                        decoded_bytes = base64.b64decode(content)
                        json_str = _urlparse.unquote(decoded_bytes.decode('latin-1'))
                        session_data = json.loads(json_str)
                    else:
                        session_data = json.loads(content)
                        
                    if start_day > 0:
                        session_data = [item for item in session_data if get_day_num(item.get("day", "")) < start_day]
                        log(f"⏭ Đã lọc bỏ các Day >= {start_day} trong session do bạn chọn Bắt đầu từ Day {start_day}")

                    for item in session_data:
                        if item.get("completed"):
                            if enable_followup and not item.get("followup_complete", True):
                                if item.get("raw_responses"):
                                    incomplete_days_refs[item["day"].strip()] = item
                                    continue
                            completed_days.add(item["day"].strip())
            log(f"↩ Auto-Resume: Đã khôi phục {len(completed_days)} Days đã hoàn thành từ trước.")
            if session_data:
                create_viewer(out_dir, session_data)
                log(f"✓ Đã tạo lại index.html với {len(session_data)} Days hiện có.")
        except Exception as e:
            log(f"⚠ Không thể đọc session.json cũ, sẽ chạy lại từ đầu: {e}")
            session_data = []
    
    daily_quota_hit = False

    # Helper xử lý 1 Day đơn lẻ (dùng chung cho vòng chính và vòng tải bù)
    def process_single_day(day, idx, total_count, is_sweep=False):
        nonlocal daily_quota_hit
        day_clean_title = day['title'].replace("## ", "").strip()
        prefix = f"🔍 [TẢI BÙ {idx+1}/{total_count}]" if is_sweep else f"[{idx+1}/{total_count}]"
        log(f"\n--- Đang xử lý {prefix}: {day['title']} ---")
        prompt = day['prompt']
        is_resume_followup = day_clean_title in incomplete_days_refs
        
        pdf_text = ""
        if day['pdf'] and not is_resume_followup:
            pdf_path = find_file(doc_dir, day['pdf'])
            if pdf_path:
                log(f"📖 Đang đọc PDF: {day['pdf']} ...")
                try:
                    doc = fitz.open(pdf_path)
                    p_start = day.get('page_start', 0)
                    p_end_meta = day.get('page_end', None)
                    total_pages = len(doc)
                    if p_end_meta is not None:
                        p_end = min(p_end_meta, total_pages)
                    else:
                        p_end = min(p_start + 10, total_pages)
                    
                    for i in range(p_start, p_end):
                        pdf_text += doc[i].get_text() + "\n"
                    doc.close()
                    log(f"Trích xuất trang {p_start+1}-{p_end} / {total_pages} ({p_end - p_start} trang).")
                except Exception as e:
                    log(f"⚠ Lỗi đọc PDF: {e}")
            else:
                log(f"⚠ KHÔNG tìm thấy file '{day['pdf']}' trong thư mục!")
        
        # Gắn text vào prompt chính
        if adaptive_ready:
            base_prompt = build_day_context(profile, learner_state, day_clean_title, prompt, [day['pdf']] if day['pdf'] else [])
            if knowledge_pack.get("sources") and not knowledge_errors:
                fact_context, coverage = build_fact_context(knowledge_pack, prompt)
                base_prompt += "\n\n" + fact_context
            else:
                coverage = None
        else:
            base_prompt = f"LƯU Ý: Đây là nội dung cho '{day_clean_title}'.\n\n{prompt}"

        # Chia nhỏ input lớn để tránh lỗi 503/UNAVAILABLE
        MAX_INPUT = 30000
        pdf_parts = []
        if pdf_text:
            if adaptive_ready:
                pdf_text = pdf_text[:MAX_INPUT]
                pdf_parts = [pdf_text]
            elif len(pdf_text) > MAX_INPUT:
                pdf_parts = split_text(pdf_text, max_chars=MAX_INPUT)
            else:
                pdf_parts = [pdf_text]

        # Lượt 1: Gửi câu hỏi chính
        all_responses = []
        got_complete = False
        lesson_result = None

        if day_clean_title in incomplete_days_refs:
            session_item = incomplete_days_refs[day_clean_title]
            all_responses = list(session_item.get("raw_responses", []))
            log(f"↪ Tiếp tục hỏi bổ sung cho {day_clean_title} (từ lượt {len(all_responses) + 1})...")
        elif len(pdf_parts) > 1:
            store = PartStore(os.path.join(out_dir, "lesson_parts.json"))
            part_texts = []
            total_parts = len(pdf_parts)
            for pi, part_txt in enumerate(pdf_parts):
                if STOP_REQUESTED:
                    log("🛑 Đã dừng tiến trình theo yêu cầu (Stop) khi đang gửi phần nội dung.")
                    return False
                saved = store.get(day_clean_title, pi)
                if saved:
                    part_texts.append(saved)
                    log(f"  [Lượt 1 • Phần {pi+1}/{total_parts}] Dùng checkpoint đã lưu ({len(saved)} ký tự).")
                    continue
                if pi == 0:
                    part_prompt = (
                        f"## {day_clean_title}\n\n{base_prompt}\n\n"
                        f"NGUỒN CỤC BỘ ĐÃ TRÍCH XUẤT (phần 1/{total_parts}; chỉ dùng phần liên quan, không bịa trích dẫn):\n"
                        f"{part_txt}"
                    )
                else:
                    part_prompt = (
                        f"Tiếp tục nội dung cho '{day_clean_title}' (phần {pi+1}/{total_parts}). "
                        f"TUYỆT ĐỐI không viết lại heading '## ...', không lặp lại nội dung đã trả lời ở các phần trước, "
                        f"chỉ tiếp tục bổ sung nội dung còn thiếu từ tài liệu sau:\n\n{part_txt}"
                    )
                log(f"💬 [Lượt 1 • Phần {pi+1}/{total_parts}] Gửi câu hỏi ({len(part_prompt)} ký tự)...")
                text_p, ok_p, quota_hit_p = call_gemini_api(
                    part_prompt, log_prefix=f"  [Lượt 1 • Phần {pi+1}/{total_parts}] "
                )
                if quota_hit_p:
                    daily_quota_hit = True
                    return False
                if not ok_p or not text_p:
                    log(f"✗ Phần {pi+1}/{total_parts} thất bại. Các phần đã lưu sẽ resume ở lần chạy sau.")
                    return False
                store.save_part(day_clean_title, pi, text_p)
                part_texts.append(text_p)
            if STOP_REQUESTED or daily_quota_hit or not part_texts:
                return False
            text1 = dedup_merge(part_texts, heading_pattern=r"^##\s+Day\s+\d+")
            store.clear(day_clean_title)
            all_responses = [text1]
            log(f"🧩 Đã nối {len(part_texts)} phần thành bài học ({len(text1)} ký tự).")
        else:
            full_prompt = base_prompt
            if pdf_parts:
                full_prompt = f"{full_prompt}\n\nNGUỒN CỤC BỘ ĐÃ TRÍCH XUẤT (chỉ dùng phần liên quan, không bịa trích dẫn):\n{pdf_parts[0]}"
            
            MAX_DAY_ATTEMPTS = 3
            text1, ok1, quota_hit = None, False, False
            for day_attempt in range(1, MAX_DAY_ATTEMPTS + 1):
                if STOP_REQUESTED:
                    return False
                if day_attempt > 1:
                    log(f"🔄 [Lượt 1] Thử lại {day_clean_title} (lần {day_attempt}/{MAX_DAY_ATTEMPTS})...")
                else:
                    log(f"💬 [Lượt 1] Gửi câu hỏi chính ({len(full_prompt)} ký tự)...")
                
                text1, ok1, quota_hit = call_gemini_api(
                    full_prompt,
                    log_prefix="  [Lượt 1] ",
                    response_schema=LESSON_RESPONSE_SCHEMA if adaptive_ready else None,
                )
                if STOP_REQUESTED or quota_hit or ok1:
                    break
                if day_attempt < MAX_DAY_ATTEMPTS:
                    log(f"  ⏳ Chờ 10s để ổn định mạng rồi thử lại...")
                    time.sleep(10)
            
            if STOP_REQUESTED:
                return False
            if quota_hit:
                daily_quota_hit = True
                return False
            if not ok1 or not text1:
                log(f"⚠ Tạm thời không thể tải {day_clean_title} sau {MAX_DAY_ATTEMPTS} lần thử. Bỏ qua Day này, tiếp tục Day sau...")
                return False
                
            if adaptive_ready:
                lesson_result = parse_lesson_response(text1)
                errors = validate_lesson(lesson_result) if lesson_result else ["JSON bài học"]
                if not errors and knowledge_pack.get("sources") and not knowledge_errors:
                    if "factual_claims" not in lesson_result:
                        errors.append("factual_claims bắt buộc khi dùng Knowledge Pack")
                    else:
                        errors.extend(validate_fact_claims(lesson_result, knowledge_pack))
                if errors:
                    log("⚠ Gemini trả bài adaptive chưa đạt schema: " + ", ".join(errors) + ". Dùng nội dung thô và không cập nhật state.")
                    if knowledge_pack.get("sources") and not knowledge_errors:
                        all_responses = [
                            "## Bài học bị chặn để bảo vệ độ chính xác\n\n"
                            "Gemini không trả được tham chiếu entity/source hợp lệ từ Knowledge Pack. "
                            "Hệ thống không hiển thị nội dung thô để tránh đưa thông tin game chưa kiểm chứng. "
                            "Hãy bổ sung nguồn hoặc chạy lại Day này."
                        ]
                        lesson_result = None
                    else:
                        all_responses = [text1]
                else:
                    if knowledge_pack.get("sources") and not knowledge_errors:
                        lesson_result["verified_evidence"] = evidence_for_claims(lesson_result, knowledge_pack)
                        lesson_result["coverage_report"] = coverage
                    if generate_visuals and lesson_result.get("visual_plan", {}).get("needed"):
                        visual_prompts = lesson_result["visual_plan"].get("prompts", [])
                        key_object = get_active_key()
                        try:
                            assets = generate_visual_assets(
                                key_object.get("key", "") if key_object else "", image_model,
                                visual_prompts, out_dir, day_clean_title,
                            )
                            lesson_result["visual_assets"] = assets
                            log(f"🖼 Đã lưu {len(assets)} ảnh minh họa cho {day_clean_title}.")
                        except Exception as exc:
                            lesson_result["visual_assets"] = []
                            log(f"⚠ Không tạo được ảnh minh họa: {str(exc)[:180]}. Bài học văn bản vẫn được lưu.")
                    all_responses = [lesson_to_markdown(lesson_result)]
                    record_generated_lesson(learner_state, day_clean_title, lesson_result)
                    save_state(out_dir, learner_state)
                    log("✅ Bài học có schema hợp lệ; đã lưu đầu ra và câu hỏi cần xác nhận (nếu có).")
            else:
                all_responses = [text1]
            
        # YC5: Vòng lặp bổ sung (Multi-turn follow-up)
        if adaptive_ready:
            got_complete = True
        elif enable_followup:
            FOLLOWUP_PROMPT = (
                "Bạn có thấy còn điều gì cần bổ sung thêm để tôi hiểu rõ và đầy đủ hơn không?\n"
                "→ Nếu CÓ: hãy bổ sung ngay bên dưới.\n"
                "→ Nếu KHÔNG còn gì cần thêm: hãy chỉ trả lời đúng 1 dòng ở CUỐI phản hồi của bạn là:\n"
                "Đã đầy đủ"
            )
            for turn in range(max_followup):
                if STOP_REQUESTED:
                    log("🛑 Đã dừng tiến trình theo yêu cầu (Stop) khi đang follow-up.")
                    break
                log(f"💬 [Lượt {turn + 2}] Hỏi bổ sung ({turn + 1}/{max_followup})...")
                context_prompt = ""
                for idx_resp, resp_t in enumerate(all_responses):
                    context_prompt += f"--- [Phản hồi lượt {idx_resp+1}] ---\n{resp_t}\n\n"
                context_prompt += f"Dựa trên các nội dung bạn đã trả lời ở trên:\n{FOLLOWUP_PROMPT}"
                
                text_n, ok_n, quota_hit_n = call_gemini_api(context_prompt, log_prefix=f"  [Lượt {turn + 2}] ")
                if quota_hit_n:
                    log("⚠ Hết quota khi đang hỏi follow-up. Lưu nội dung hiện có.")
                    daily_quota_hit = True
                    break
                if not ok_n or not text_n:
                    log(f"⚠ Lượt {turn + 2} thất bại. Lưu nội dung hiện có.")
                    break
                all_responses.append(text_n)
                last_line = text_n.strip().split("\n")[-1].strip()
                if "Đã đầy đủ" in last_line or text_n.strip().endswith("Đã đầy đủ"):
                    log(f"  ✅ AI xác nhận đầy đủ ở lượt {turn + 2}. Dừng hỏi bổ sung.")
                    got_complete = True
                    break
                else:
                    log("  ➕ AI vẫn bổ sung nội dung mới, hỏi tiếp ở lượt sau...")
                    time.sleep(2)
            if not got_complete and not daily_quota_hit:
                log(f"  ⚠ Đã hỏi tối đa {max_followup} lần mà AI chưa xác nhận 'Đã đầy đủ'. Vẫn lưu file.")
        else:
            got_complete = True
            
        # Gộp tất cả phản hồi thành HTML
        section_labels = ["📖 Nội dung chính"] + [f"➕ Bổ sung lần {i}" for i in range(1, len(all_responses))]
        combined_html_parts = []
        for i, (resp_text, label) in enumerate(zip(all_responses, section_labels)):
            html_part = markdown_to_html(resp_text)
            section_class = "main-section" if i == 0 else "supplement-section"
            combined_html_parts.append(
                f'<div class="{section_class}">\n'
                f'  <div class="section-label">{label}</div>\n'
                f'  {html_part}\n'
                f'</div>'
            )
        html_res = "\n".join(combined_html_parts)
        
        if day_clean_title in incomplete_days_refs:
            session_item = incomplete_days_refs[day_clean_title]
            session_item["html"] = html_res
            session_item["timestamp"] = int(time.time() * 1000)
            session_item["followup_turns"] = len(all_responses) - 1
            session_item["followup_complete"] = got_complete
            session_item["raw_responses"] = all_responses
            session_item["_needs_disk_write"] = True
            if adaptive_ready and lesson_result:
                session_item["adaptive_lesson"] = lesson_result
        else:
            existing_entry = next((item for item in session_data if item.get("day", "").strip() == day_clean_title), None)
            if existing_entry:
                existing_entry["html"] = html_res
                existing_entry["timestamp"] = int(time.time() * 1000)
                existing_entry["completed"] = True
                existing_entry["followup_turns"] = len(all_responses) - 1
                existing_entry["followup_complete"] = got_complete
                existing_entry["raw_responses"] = all_responses
                existing_entry["_needs_disk_write"] = True
                if adaptive_ready and lesson_result:
                    existing_entry["adaptive_lesson"] = lesson_result
            else:
                new_entry = {
                    "day": day['title'].replace("## ", ""),
                    "html": html_res,
                    "timestamp": int(time.time() * 1000),
                    "completed": True,
                    "followup_turns": len(all_responses) - 1,
                    "followup_complete": got_complete,
                    "raw_responses": all_responses,
                    "_needs_disk_write": True,
                }
                if adaptive_ready and lesson_result:
                    new_entry["adaptive_lesson"] = lesson_result
                session_data.append(new_entry)
                # Tự động đánh dấu Day liền kề trước đó (N-1) cần cập nhật thanh điều hướng
                if len(session_data) >= 2:
                    session_data[-2]["_needs_disk_write"] = True
        
        save_session(session_data, out_dir)
        try:
            create_viewer(out_dir, session_data, total_expected_days=total_count)
        except Exception as e:
            log(f"⚠ Lỗi cập nhật index.html: {e}. Vẫn tiếp tục tải bài tiếp theo...")
        time.sleep(3)
        return True

    # ── VÒNG LẶP CHÍNH ──
    for idx, day in enumerate(days_parsed):
        if STOP_REQUESTED or daily_quota_hit:
            if STOP_REQUESTED:
                log("🛑 Đã dừng tiến trình theo yêu cầu (Stop).")
            break
            
        day_clean_title = day['title'].replace("## ", "").strip()
        
        if start_day > 0 and get_day_num(day['title']) > 0 and get_day_num(day['title']) < start_day:
            continue
            
        if day_clean_title in completed_days and day_clean_title not in incomplete_days_refs:
            log(f"⏭ Bỏ qua [{idx+1}/{len(days_parsed)}]: {day_clean_title} (Đã hoàn thành)")
            continue
            
        process_single_day(day, idx, len(days_parsed), is_sweep=False)

    # ── VÒNG QUÉT TẢI BÙ CÁC NGÀY BỊ THIẾU (MISSING DAYS AUTO-SWEEP PASS) ──
    if not STOP_REQUESTED and not daily_quota_hit:
        target_days = days_parsed if start_day <= 0 else [d for d in days_parsed if get_day_num(d['title']) >= start_day]
        for sweep_round in range(1, 4):
            existing_days_set = {item.get("day", "").strip() for item in session_data if item.get("completed")}
            missing_days = [d for d in target_days if d['title'].replace("## ", "").strip() not in existing_days_set]
            if not missing_days:
                break
            log(f"\n🔍 [QUÉT THIẾU VÒNG {sweep_round}/3] Phát hiện {len(missing_days)} Day bị thiếu/bỏ qua: {', '.join([d['title'].replace('## ', '').strip() for d in missing_days[:5]])}{'...' if len(missing_days) > 5 else ''}. Bắt đầu tự động tải bù (Sweep Pass)...")
            for s_idx, s_day in enumerate(missing_days):
                if STOP_REQUESTED or daily_quota_hit:
                    break
                process_single_day(s_day, s_idx, len(missing_days), is_sweep=True)

    # Kiểm tra tổng kết cuối cùng
    final_existing = {item.get("day", "").strip() for item in session_data if item.get("completed")}
    target_days = days_parsed if start_day <= 0 else [d for d in days_parsed if get_day_num(d['title']) >= start_day]
    final_missing = [d for d in target_days if d['title'].replace("## ", "").strip() not in final_existing]
    
    if not final_missing:
        log(f"\n🎉 HOÀN TẤT 100%! Toàn bộ {len(target_days)}/{len(target_days)} Day đều đã có đầy đủ bài học HTML.")
    else:
        log(f"\n✓ Đã lưu tiến độ hiện có ({len(session_data)} Days). Còn thiếu {len(final_missing)} Day.")
        
    save_session(session_data, out_dir)
    create_viewer(out_dir, session_data, total_expected_days=len(target_days))
    log(f"📁 index.html đã được cập nhật tại {out_dir}")

def find_file(root_dir, filename):
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if f.lower() == filename.lower():
                return os.path.join(dirpath, f)
    return None

def markdown_to_html(md_text):
    try:
        import markdown
        return markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
    except ImportError:
        return md_text
    except Exception:
        return md_text

def save_session(data_list, out_dir):
    # Rule 3.5: Không lưu trường "html" hoặc "raw_responses" của các bài đã hoàn thành
    # vào session.json để chống phình RAM/file phình hàng trăm MB khi lộ trình có hàng nghìn ngày.
    clean_list = []
    for item in data_list:
        clean_item = {}
        for k, v in item.items():
            if k in ("html", "_needs_disk_write"):
                continue
            if k == "raw_responses" and item.get("followup_complete", True):
                continue
            clean_item[k] = v
        clean_list.append(clean_item)
    json_str = json.dumps(clean_list, ensure_ascii=False)
    out_file = os.path.join(out_dir, "session.json")
    bak_file = os.path.join(out_dir, "session.bak.json")
    tmp_file = out_file + ".tmp"
    try:
        with open(tmp_file, 'w', encoding='utf-8') as f:
            f.write(json_str)
        if os.path.exists(out_file):
            try:
                import shutil
                shutil.copyfile(out_file, bak_file)
            except Exception:
                pass
            os.remove(out_file)
        os.rename(tmp_file, out_file)
    except Exception:
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(json_str)

def create_viewer(out_dir, session_data=None, total_expected_days=None):
    if session_data is None:
        return
        
    day_css = """
    body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 860px; margin: 40px auto; padding: 0 20px; background: #f9f9f9; color: #1a1a1a; transition: background 0.3s, color 0.3s; }
    header { background: #0078d4; color: #fff; padding: 16px 24px; border-radius: 8px; margin-bottom: 24px; }
    header h1 { margin: 0; font-size: 1.4em; }
    header p { margin: 4px 0 0; font-size: 0.85em; opacity: 0.85; }
    .content { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 24px; line-height: 1.7; transition: background 0.3s; }
    a.back { display: inline-block; margin-top: 20px; color: #0078d4; text-decoration: none; font-size: 0.9em; }
    a.back:hover { text-decoration: underline; }
    h2, h3 { color: #005a9e; margin-top: 1.5em; }
    code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
    pre { background: #f0f0f0; padding: 12px; border-radius: 6px; overflow-x: auto; position: relative; }
    table { border-collapse: collapse; width: 100%; margin: 15px 0; }
    th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
    th { background: #0078d4; color: #fff; }
    tr:nth-child(even) { background: #f5f5f5; }
    body { padding-top: 52px !important; }

    /* Copy code button */
    .copy-code-btn {
      position: absolute; top: 6px; right: 6px;
      background: rgba(30, 41, 59, 0.85); color: #e2e8f0; border: 1px solid rgba(255,255,255,0.2);
      border-radius: 4px; padding: 3px 8px; font-size: 11px; cursor: pointer;
      opacity: 0.7; transition: opacity 0.2s, background 0.2s; z-index: 10;
      font-family: inherit;
    }
    pre:hover .copy-code-btn { opacity: 1; }
    .copy-code-btn:hover { background: #2563eb; border-color: #3b82f6; color: #fff; }
    .copy-code-btn.copied { background: #16a34a !important; border-color: #22c55e !important; color: #fff !important; opacity: 1; }

    /* Dark mode support */
    body.dark-mode { background: #121218 !important; color: #e2e8f0 !important; }
    body.dark-mode header { background: linear-gradient(135deg, #1e3a8a, #3b82f6) !important; }
    body.dark-mode .content { background: #1a1a24 !important; border-color: #2e2e3e !important; color: #e2e8f0 !important; }
    body.dark-mode h2, body.dark-mode h3 { color: #60a5fa !important; }
    body.dark-mode code { background: #252535 !important; color: #93c5fd !important; }
    body.dark-mode pre { background: #252535 !important; color: #f8fafc !important; border: 1px solid #3b3b4f; }
    body.dark-mode table th { background: #1e40af !important; border-color: #374151 !important; }
    body.dark-mode table td { border-color: #374151 !important; color: #e2e8f0 !important; }
    body.dark-mode table tr:nth-child(even) { background: #20202e !important; }
    body.dark-mode .section-label { background: #1e293b !important; color: #60a5fa !important; border: 1px solid #334155; }
    body.dark-mode .supplement-section { border-left-color: #8b5cf6 !important; }
    body.dark-mode .verified-facts { background: #064e3b !important; border-left-color: #10b981 !important; color: #d1fae5 !important; }
    body.dark-mode .coverage-warning { background: #451a03 !important; border-left-color: #f97316 !important; color: #ffedd5 !important; }
    """
    
    index_css = """
    * { box-sizing: border-box; }
    body { margin:0; font-family:'Segoe UI',Arial,sans-serif; background:#f4f7fb; color:#162033; transition: background 0.3s, color 0.3s; }
    .header { background:linear-gradient(135deg,#14213d,#345995); color:#fff; padding:18px 24px; display:flex; justify-content:space-between; align-items:center; }
    .header h1 { margin:0 0 5px; font-size:1.35rem; } .header p { margin:0; color:#dbeafe; }
    .header-right { display:flex; gap:12px; align-items:center; }
    .theme-btn { background:rgba(255,255,255,0.2); border:1px solid rgba(255,255,255,0.4); color:#fff; padding:6px 12px; border-radius:6px; cursor:pointer; font-size:0.9rem; }
    .theme-btn:hover { background:rgba(255,255,255,0.35); }
    .progress-bar-container { background:rgba(0,0,0,0.2); border-radius:10px; height:8px; width:160px; overflow:hidden; margin-top:5px; }
    .progress-bar-fill { background:#10b981; height:100%; border-radius:10px; transition:width 0.3s; }
    .dashboard { display:grid; grid-template-columns:minmax(280px,350px) minmax(0,1fr); min-height:calc(100vh - 85px); }
    .sidebar { padding:16px; background:#101827; color:#e5e7eb; border-right:1px solid #263247; }
    .search-box { width:100%; padding:10px 12px; border:1px solid #46536b; border-radius:8px; background:#182235; color:#fff; margin:0 0 12px; }
    .course-note { color:#aab8d3; font-size:.82rem; margin:0 0 12px; line-height:1.45; }
    .day-list { display:flex; flex-direction:column; gap:6px; max-height:calc(100vh - 185px); overflow:auto; padding-right:3px; }
    .day-item { width:100%; text-align:left; border:1px solid #263247; border-radius:8px; background:#182235; color:#e5e7eb; padding:10px; cursor:pointer; transition:background 0.15s, border-color 0.15s; position:relative; }
    .day-item:hover,.day-item.active { background:#263d69; border-color:#78a6ff; }
    .day-num { display:inline-block; color:#93c5fd; font-weight:700; font-size:.8rem; margin-bottom:3px; }
    .day-check-badge { float:right; color:#10b981; font-weight:bold; font-size:0.85rem; }
    .day-title { display:block; font-size:.88rem; line-height:1.3; }
    .main { padding:24px; max-width:1050px; width:100%; margin:0 auto; }
    .lesson-card { background:#fff; border:1px solid #d9e1ee; border-radius:12px; padding:24px; box-shadow:0 3px 12px rgba(15,23,42,.06); line-height:1.7; transition:background 0.3s; position:relative; }
    .lesson-card h1,.lesson-card h2,.lesson-card h3 { color:#153e75; } .lesson-card pre { overflow:auto; background:#f1f5f9; padding:12px; border-radius:7px; position:relative; }
    .lesson-card table { border-collapse:collapse; width:100%; } .lesson-card th,.lesson-card td { border:1px solid #cbd5e1; padding:8px; text-align:left; }
    .lesson-card img { max-width:100%; border-radius:8px; border:1px solid #d9e1ee; }
    .lesson-meta { display:flex; flex-wrap:wrap; gap:8px; margin:12px 0 18px; } .badge { padding:4px 9px; border-radius:999px; font-size:.8rem; }
    .badge.ok { background:#dcfce7; color:#166534; } .badge.warn { background:#fef3c7; color:#92400e; } .badge.info { background:#dbeafe; color:#1d4ed8; }
    .source-box,.question-box { border-left:4px solid #f59e0b; background:#fffbeb; padding:10px 14px; margin:16px 0; } .source-box ul,.question-box ul { margin:6px 0 0; padding-left:20px; }
    .top-actions { float:right; display:flex; gap:8px; align-items:center; }
    .act-btn { padding:5px 11px; font-size:.84rem; border-radius:6px; text-decoration:none; cursor:pointer; border:1px solid transparent; transition:all .2s; }
    .act-btn-read { background:#ecfdf5; color:#065f46; border-color:#a7f3d0; font-weight:600; }
    .act-btn-read:hover { background:#d1fae5; }
    .act-btn-read.done { background:#10b981; color:#fff; border-color:#059669; }
    .act-btn-print { background:#f1f5f9; color:#334155; border-color:#cbd5e1; }
    .act-btn-print:hover { background:#e2e8f0; }
    .act-btn-open { background:#eff6ff; color:#1d4ed8; border-color:#bfdbfe; }
    .act-btn-open:hover { background:#dbeafe; }
    
    /* Copy button in index.html */
    .copy-code-btn {
      position: absolute; top: 6px; right: 6px;
      background: rgba(30, 41, 59, 0.85); color: #e2e8f0; border: 1px solid rgba(255,255,255,0.2);
      border-radius: 4px; padding: 3px 8px; font-size: 11px; cursor: pointer;
      opacity: 0.7; transition: opacity 0.2s; z-index: 10;
    }
    pre:hover .copy-code-btn { opacity: 1; }
    .copy-code-btn:hover { background: #2563eb; color: #fff; }
    .copy-code-btn.copied { background: #16a34a !important; color: #fff !important; opacity: 1; }

    /* Dark mode for dashboard */
    body.dark-mode { background:#0f172a; color:#e2e8f0; }
    body.dark-mode .lesson-card { background:#1e293b; border-color:#334155; color:#e2e8f0; box-shadow:0 3px 12px rgba(0,0,0,0.3); }
    body.dark-mode .lesson-card h1, body.dark-mode .lesson-card h2, body.dark-mode .lesson-card h3 { color:#93c5fd; }
    body.dark-mode .lesson-card pre { background:#0f172a; border:1px solid #334155; color:#f8fafc; }
    body.dark-mode .lesson-card table th { background:#1e3a8a; border-color:#334155; }
    body.dark-mode .lesson-card table td { border-color:#334155; color:#e2e8f0; }
    body.dark-mode .source-box, body.dark-mode .question-box { background:#3b290c; border-left-color:#f59e0b; color:#fed7aa; }
    body.dark-mode .act-btn-print { background:#334155; color:#f1f5f9; border-color:#475569; }
    body.dark-mode .act-btn-open { background:#1e3a8a; color:#93c5fd; border-color:#2563eb; }

    @media print {
      .header, .sidebar, .top-actions, #searchInput, .course-note { display: none !important; }
      .dashboard { display: block !important; }
      .main { max-width: 100% !important; padding: 0 !important; }
      .lesson-card { border: none !important; box-shadow: none !important; padding: 0 !important; }
      body { background: #fff !important; color: #000 !important; }
    }
    @media (max-width:800px) { .dashboard { grid-template-columns:1fr; } .sidebar { border-right:0; } .day-list { max-height:220px; } .main { padding:14px; } }
    """
    
    import re
    from html import escape as html_escape
    def safe_filename(name):
        return re.sub(r'[\\/*?:"<>|]', "", name).strip()
        
    for idx, item in enumerate(session_data):
        day_title = item.get("day", f"Day {idx+1}")
        safe_title_file = safe_filename(day_title)
        if len(safe_title_file) > 50:
            safe_title_file = safe_title_file[:50]
        item['file_name'] = f"{idx+1:03d}_{safe_title_file}.html"
        item['day_title'] = day_title
        
    items_html = ""
    dashboard_items = []
    for idx, item in enumerate(session_data):
        day_title = item['day_title']
        file_name = item['file_name']
        
        day_num_match = re.search(r'Day\s*([\w]+)', day_title)
        day_num_str = day_num_match.group(1) if day_num_match else str(idx+1)
        
        total_days_num = max(len(session_data), total_expected_days or len(session_data))
        nav_bar = f"""<!-- NAV-BAR-V2 -->
<style>
#askcpl-nav{{position:fixed;top:0;left:0;right:0;z-index:9999;display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);color:#fff;padding:8px 16px;box-shadow:0 2px 12px rgba(0,0,0,.5);font-family:'Segoe UI',Arial,sans-serif;font-size:14px;box-sizing:border-box;height:48px;}}
#askcpl-nav button{{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:14px;transition:background .2s;flex-shrink:0;}}
#askcpl-nav button:hover:not([disabled]){{background:rgba(255,255,255,.3);}}
#askcpl-nav button[disabled]{{opacity:.3;cursor:default;}}
#askcpl-nav-title{{flex:1;text-align:center;cursor:pointer;padding:4px 12px;border-radius:6px;transition:background .2s;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600;color:#e0d0ff;}}
#askcpl-nav-title:hover{{background:rgba(255,255,255,.15);}}
#askcpl-nav-home{{background:rgba(46,160,67,0.3);text-decoration:none;border:1px solid rgba(46,160,67,0.5);color:#fff;padding:6px 12px;border-radius:6px;font-size:14px;transition:background .2s;display:flex;align-items:center;}}
#askcpl-nav-home:hover{{background:rgba(46,160,67,0.5);}}
#askcpl-toc{{display:none;position:fixed;top:52px;left:50%;transform:translateX(-50%);background:#1e1e2e;border:1px solid rgba(167,139,250,.3);border-radius:10px;padding:8px 4px;min-width:320px;max-height:400px;overflow-y:auto;z-index:9998;box-shadow:0 8px 32px rgba(0,0,0,.7);}}
#askcpl-toc a{{display:block;padding:7px 16px;color:#a0a0c0;text-decoration:none;border-radius:6px;margin:1px 4px;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
#askcpl-toc a:hover{{background:rgba(167,139,250,.15);color:#e0d0ff;}}
#askcpl-toc a.cur{{background:linear-gradient(90deg,#7c3aed,#4f46e5)!important;color:#fff!important;font-weight:bold;}}
.nav-actions{{display:flex;gap:8px;align-items:center;}}
</style>
<div id="askcpl-nav">
  <button id="nav-prev" onclick="askcplNav(-1)">◀ Prev</button>
  <a id="askcpl-nav-home" href="index.html" title="Quay lại Menu Tổng">🏠 Menu</a>
  <span id="askcpl-nav-title" onclick="askcplToggleToc()" title="Click xem Mục Lục">Day ... ▼</span>
  <div class="nav-actions">
    <button id="nav-dark-toggle" onclick="askcplToggleDark()" title="Đổi giao diện Tối/Sáng">🌓</button>
    <button id="nav-next" onclick="askcplNav(1)">Next ▶</button>
  </div>
</div>
<div id="askcpl-toc"></div>
<script>
(function(){{
  var MAX_DAYS = {total_days_num};
  var m = window.location.pathname.match(/(\d+)_.*\.html/i)
       || window.location.pathname.match(/[\/\\]day_(\d+)[a-z]?\.html/i)
       || window.location.href.match(/(\d+)_.*\.html/i)
       || window.location.href.match(/[\/\\]day_(\d+)[a-z]?\.html/i);
  var cur = m ? parseInt(m[1]) : {idx + 1};
  
  document.getElementById('askcpl-nav-title').textContent = 'Day ' + cur + ' ▼';
  document.getElementById('askcpl-nav-home').href = 'index.html#day-' + cur;

  if(cur <= 1) document.getElementById('nav-prev').disabled = true;
  if(MAX_DAYS && MAX_DAYS < 9000 && cur >= MAX_DAYS) document.getElementById('nav-next').disabled = true;

  function showToast(msg) {{
    var t = document.getElementById('askcpl-toast');
    if (!t) {{
      t = document.createElement('div');
      t.id = 'askcpl-toast';
      t.style.cssText = 'position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:linear-gradient(135deg,#1e1b4b,#312e81);color:#e0e7ff;padding:12px 24px;border-radius:8px;border:1px solid #6366f1;box-shadow:0 10px 25px rgba(0,0,0,0.6);font-size:14px;font-family:sans-serif;z-index:999999;transition:opacity 0.3s;text-align:center;';
      document.body.appendChild(t);
    }}
    t.innerHTML = msg;
    t.style.opacity = '1';
    clearTimeout(t._timer);
    t._timer = setTimeout(function(){{ t.style.opacity = '0'; }}, 3500);
  }}

  var _lastNextAttempt = 0;
  window.askcplNav = function(d){{
    var n = cur + d;
    if(n < 1) return;
    if(MAX_DAYS && MAX_DAYS < 9000 && n > MAX_DAYS) {{
      showToast('Bạn đã ở chương cuối cùng (Day ' + cur + ')');
      return;
    }}
    var allFiles = {json.dumps([s["file_name"] for s in session_data])};
    if (n-1 >= 0 && n-1 < allFiles.length) {{
        window.location.href = allFiles[n-1];
    }} else {{
        var now = Date.now();
        var cand = ('000' + n).slice(-3) + '_Day ' + n + '.html';
        if (now - _lastNextAttempt < 4000) {{
          window.location.href = cand;
        }} else {{
          _lastNextAttempt = now;
          showToast('⏳ Day ' + n + ' đang được AI xử lý tải về. Nếu đã tải xong, nhấp Next lần nữa để mở hoặc F5 tải lại trang!');
        }}
    }}
  }};

  var toc = document.getElementById('askcpl-toc');
  window.askcplToggleToc = function(){{
    if(toc.style.display === 'block'){{ toc.style.display='none'; return; }}
    if(!toc.innerHTML){{
      var html = '';
      var lo = Math.max(1, cur-10), hi = Math.min(MAX_DAYS, cur+10);
      var allFiles = {json.dumps([s["file_name"] for s in session_data])};
      for(var i=lo; i<=hi; i++){{
        var cls = (i===cur) ? 'cur' : '';
        var mark = (i===cur) ? ' ← Hôm nay' : '';
        var link = allFiles[i-1];
        html += '<a class="'+cls+'" href="'+link+'">Day '+i+mark+'</a>';
      }}
      toc.innerHTML = html;
    }}
    toc.style.display = 'block';
    var c = toc.querySelector('.cur');
    if(c) c.scrollIntoView({{block:'center'}});
  }};

  window.askcplToggleDark = function(){{
    document.body.classList.toggle('dark-mode');
    var isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('askcpl_theme', isDark ? 'dark' : 'light');
  }};
  if(localStorage.getItem('askcpl_theme') === 'dark'){{
    document.body.classList.add('dark-mode');
  }}

  // Auto attach copy code buttons
  document.querySelectorAll('pre').forEach(function(pre){{
    if(pre.querySelector('.copy-code-btn')) return;
    var btn = document.createElement('button');
    btn.className = 'copy-code-btn';
    btn.textContent = '📋 Copy';
    btn.onclick = function(){{
      var code = pre.querySelector('code') ? pre.querySelector('code').innerText : pre.innerText;
      navigator.clipboard.writeText(code).then(function(){{
        btn.textContent = '✅ Đã chép';
        btn.classList.add('copied');
        setTimeout(function(){{
          btn.textContent = '📋 Copy';
          btn.classList.remove('copied');
        }}, 2000);
      }});
    }};
    pre.appendChild(btn);
  }});

  document.addEventListener('click', function(e){{
    var nav=document.getElementById('askcpl-nav');
    if(!nav.contains(e.target) && !toc.contains(e.target)){{
      toc.style.display='none';
    }}
  }});
  document.addEventListener('keydown', function(e){{
    if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA') return;
    if(e.key==='ArrowLeft') askcplNav(-1);
    if(e.key==='ArrowRight') askcplNav(1);
    if(e.key==='Escape') toc.style.display='none';
  }});
}})();
</script>
<!-- END-NAV-BAR-V2 -->"""
        
        followup_turns = item.get('followup_turns', 0)
        lesson = item.get("adaptive_lesson") if isinstance(item.get("adaptive_lesson"), dict) else {}
        verified_evidence = lesson.get("verified_evidence", []) if isinstance(lesson.get("verified_evidence", []), list) else []
        evidence_html = ""
        if verified_evidence:
            cards = []
            for evidence in verified_evidence:
                entity = evidence.get("entity", {}) if isinstance(evidence, dict) else {}
                sources = evidence.get("sources", []) if isinstance(evidence, dict) else []
                label = html_escape(str(entity.get("name") or entity.get("id") or "Dữ kiện"))
                claim = html_escape(str(evidence.get("claim", "")))
                links = " ".join(
                    f'<a href="{html_escape(str(src.get("url", "")), quote=True)}" target="_blank" rel="noreferrer">{html_escape(str(src.get("title") or src.get("id") or "Nguồn"))}</a>'
                    for src in sources if isinstance(src, dict) and src.get("url")
                ) or "Nguồn cục bộ đã đính kèm"
                cards.append(f"<li><b>{label}</b>: {claim}<br><small>{links}</small></li>")
            evidence_html = '<section class="verified-facts"><h2>Dữ kiện đã kiểm chứng</h2><ul>' + "".join(cards) + "</ul></section>"
        coverage = lesson.get("coverage_report", {}) if isinstance(lesson.get("coverage_report"), dict) else {}
        if coverage.get("requested_all") and not coverage.get("complete"):
            evidence_html = '<section class="coverage-warning"><b>Chưa đủ dữ liệu để khẳng định “toàn bộ”.</b> Bài này chỉ hiển thị quy trình và các dữ kiện đã có bằng chứng.</section>' + evidence_html
        out_filepath = os.path.join(out_dir, file_name)
        content_html = item.get('html', '')
        file_exists = os.path.exists(out_filepath)
        
        # Chỉ đọc từ đĩa nếu trong RAM chưa có VÀ file đã tồn tại trên đĩa (để phục hồi khi resume)
        if not content_html and file_exists:
            try:
                with open(out_filepath, 'r', encoding='utf-8') as f_in:
                    existing_c = f_in.read()
                    m = re.search(r'<div class="content">(.*?)</div>\s*<!-- NAV-BAR', existing_c, re.DOTALL)
                    if not m:
                        m = re.search(r'<div class="content">(.*?)</div>', existing_c, re.DOTALL)
                    if m and m.group(1).strip():
                        content_html = m.group(1).strip()
                        item['html'] = content_html  # Cache vào RAM để không bao giờ phải đọc lại ở các Day sau
            except Exception:
                pass

        # CHỈ GHI FILE KHI:
        # 1. File chưa tồn tại trên đĩa (not file_exists)
        # 2. HOẶC item này vừa được hoàn thành mới (_needs_disk_write)
        needs_write = bool(item.pop('_needs_disk_write', False))
        should_write = (not file_exists) or needs_write
        if should_write and content_html.strip():
            full_day_content = content_html + evidence_html
            followup_badge = (
                f'<span class="followup-badge">✓ Đã đầy đủ ({followup_turns} lượt bổ sung)</span>'
                if item.get('followup_complete') else
                (f'<span class="followup-badge incomplete">⚠ {followup_turns} lượt bổ sung (chưa xác nhận)</span>'
                 if followup_turns > 0 else '')
            )
            day_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{day_title}</title>
  <style>
  {day_css}
  .main-section {{ margin-bottom: 24px; }}
  .supplement-section {{ margin-bottom: 24px; border-left: 4px solid #a78bfa; padding-left: 16px; }}
  .section-label {{ font-weight: bold; font-size: 0.95em; color: #005a9e; margin-bottom: 10px;
                    padding: 4px 10px; background: #e8f0fe; border-radius: 4px; display: inline-block; }}
  .followup-badge {{ display: inline-block; margin-top: 6px; padding: 3px 10px;
                     border-radius: 12px; font-size: 0.82em; background: #d1fae5; color: #065f46; }}
  .followup-badge.incomplete {{ background: #fef3c7; color: #92400e; }}
  .verified-facts {{ margin:24px 0; padding:14px; background:#ecfdf5; border-left:4px solid #16a34a; }}
  .coverage-warning {{ margin:20px 0; padding:14px; background:#fff7ed; border-left:4px solid #ea580c; }}
  </style>
</head>
<body>
  <header>
    <h1>{day_title}</h1>
    <p>Tóm tắt &amp; Dịch tự động bởi AI · {datetime.now().strftime('%d/%m/%Y %H:%M')} {followup_badge}</p>
  </header>
  <div class="content">{full_day_content}</div>
  {nav_bar}
</body>
</html>"""
            try:
                with open(out_filepath, 'w', encoding='utf-8') as f:
                    f.write(day_html)
            except Exception:
                pass
            
        safe_title = day_title.replace('<', '&lt;').replace('>', '&gt;')
        items_html += (
            f'    <a class="day-item" id="day-{day_num_str}" href="{file_name}">\n'
            f'      <span class="day-num">Day {day_num_str}</span>\n'
            f'      <span class="day-title">{safe_title}</span>\n'
            f'    </a>\n'
        )
        raw_html = content_html
        safe_lesson_html = re.sub(r"(?is)<script[^>]*>.*?</script>", "", raw_html)
        plain_summary = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", safe_lesson_html)).strip()
        dashboard_items.append({
            "day": day_num_str,
            "title": day_title,
            "file": file_name,
            "html": safe_lesson_html,
            "summary": plain_summary[:220],
            "sources": [str(src.get("title") or src.get("id")) for row in verified_evidence for src in row.get("sources", []) if isinstance(src, dict)],
            "questions": lesson.get("clarifying_questions", []) if isinstance(lesson.get("clarifying_questions", []), list) else [],
            "visual_assets": lesson.get("visual_assets", []) if isinstance(lesson.get("visual_assets", []), list) else [],
            "structured": bool(lesson),
        })

    folder_name = os.path.basename(os.path.abspath(out_dir)) or "Tài liệu Sinh bởi AI"
    total_days = len(session_data)
    dashboard_json = json.dumps(dashboard_items, ensure_ascii=False).replace("</", "<\\/")
    
    index_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>📚 {folder_name} ─ Mục Lục</title>
  <style>{index_css}</style>
</head>
<body>
  <div class="header">
    <div>
      <h1>📚 {folder_name}</h1>
      <p>Tổng cộng {total_days} ngày học đã được tạo</p>
    </div>
    <div class="header-right">
      <div>
        <div style="font-size:0.8rem; text-align:right; color:#dbeafe;" id="headerProgressText">Đã học: 0/{total_days} (0%)</div>
        <div class="progress-bar-container"><div class="progress-bar-fill" id="headerProgressFill" style="width:0%;"></div></div>
      </div>
      <button class="theme-btn" onclick="toggleTheme()" title="Đổi giao diện Tối/Sáng">🌓 Theme</button>
    </div>
  </div>
  <div class="dashboard">
    <aside class="sidebar">
      <input class="search-box" type="text" id="searchInput" placeholder="🔍 Tìm Day hoặc từ khóa..." oninput="filterDays()">
      <p class="course-note">Chọn Day bên dưới để đọc trực tiếp. Dùng phím ◀ / ▶ trên bàn phím để chuyển ngày nhanh.</p>
      <div class="day-list" id="dayList"></div>
    </aside>
    <main class="main"><div id="lesson" class="lesson-card"></div></main>
  </div>
  <script>
    const lessons = {dashboard_json};
    const escapeHtml = (text) => String(text || '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
    
    function getLearnedDays() {{
      try {{
        return new Set(JSON.parse(localStorage.getItem('askcpl_learned_' + encodeURIComponent(location.pathname)) || '[]'));
      }} catch(e) {{
        return new Set();
      }}
    }}
    function saveLearnedDays(set) {{
      try {{
        localStorage.setItem('askcpl_learned_' + encodeURIComponent(location.pathname), JSON.stringify(Array.from(set)));
      }} catch(e) {{}}
    }}

    function toggleTheme() {{
      document.body.classList.toggle('dark-mode');
      localStorage.setItem('askcpl_theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
    }}
    if (localStorage.getItem('askcpl_theme') === 'dark') {{
      document.body.classList.add('dark-mode');
    }}

    function updateProgressUI() {{
      const learned = getLearnedDays();
      const total = lessons.length;
      const count = learned.size;
      const pct = total > 0 ? Math.round((count / total) * 100) : 0;
      
      const txt = document.getElementById('headerProgressText');
      if (txt) txt.textContent = 'Đã học: ' + count + '/' + total + ' (' + pct + '%)';
      const fill = document.getElementById('headerProgressFill');
      if (fill) fill.style.width = pct + '%';

      lessons.forEach(item => {{
        const b = document.getElementById('badge-day-' + item.day);
        if (b) {{
          b.textContent = learned.has(String(item.day)) ? '✅' : '';
        }}
      }});
    }}

    function toggleLearned(dayNum) {{
      const learned = getLearnedDays();
      const sNum = String(dayNum);
      if (learned.has(sNum)) {{
        learned.delete(sNum);
      }} else {{
        learned.add(sNum);
      }}
      saveLearnedDays(learned);
      updateProgressUI();
      
      const btn = document.getElementById('btnLearned');
      if (btn) {{
        const isDone = learned.has(sNum);
        btn.className = 'act-btn act-btn-read' + (isDone ? ' done' : '');
        btn.textContent = isDone ? '✅ Đã học xong' : '☑ Đánh dấu đã học';
      }}
    }}

    function renderDay(index) {{
      const item = lessons[index]; if (!item) return;
      document.querySelectorAll('.day-item').forEach((node, i) => node.classList.toggle('active', i === index));
      const sources = item.sources.length ? '<div class="source-box"><b>Nguồn AI khai báo:</b><ul>' + item.sources.map(x => '<li>' + escapeHtml(x) + '</li>').join('') + '</ul></div>' : '<div class="source-box"><b>Chưa có nguồn kiểm chứng đính kèm.</b> Nội dung này chỉ dùng làm khung học, không nên coi là thông số/sự thật đầy đủ.</div>';
      const questions = item.questions.length ? '<div class="question-box"><b>Cần bạn xác nhận trước Day tiếp theo:</b><ul>' + item.questions.map(x => '<li>' + escapeHtml(x) + '</li>').join('') + '</ul></div>' : '';
      const evidence = item.sources.length ? '<span class="badge info">Có khai báo nguồn</span>' : '<span class="badge warn">Cần dữ liệu nguồn</span>';
      const visual = item.visual_assets.length ? '<span class="badge ok">' + item.visual_assets.length + ' ảnh đã lưu</span>' : '<span class="badge warn">Chưa có ảnh thật</span>';
      
      const learned = getLearnedDays();
      const isDone = learned.has(String(item.day));
      const readBtnClass = 'act-btn act-btn-read' + (isDone ? ' done' : '');
      const readBtnText = isDone ? '✅ Đã học xong' : '☑ Đánh dấu đã học';

      const topActions = '<div class="top-actions">' +
        '<button class="' + readBtnClass + '" id="btnLearned" onclick="toggleLearned(\\'' + escapeHtml(item.day) + '\\')">' + readBtnText + '</button>' +
        '<button class="act-btn act-btn-print" onclick="window.print()" title="In hoặc lưu dạng PDF">🖨️ In / PDF</button>' +
        '<a class="act-btn act-btn-open" href="' + encodeURI(item.file) + '" title="Mở file HTML độc lập">Mở trang riêng ↗</a>' +
      '</div>';

      var bodyHtml = item.html ? item.html : '<div style="margin-top:16px;"><iframe src="' + encodeURI(item.file) + '" style="width:100%;height:80vh;border:1px solid #cbd5e1;border-radius:8px;background:#fff;" onload="try{{var nav=this.contentDocument.getElementById(&quot;askcpl-nav&quot;);if(nav)nav.style.display=&quot;none&quot;;}}catch(e){{}}"></iframe></div>';
      document.getElementById('lesson').innerHTML = topActions + '<h1>Day ' + escapeHtml(item.day) + ' — ' + escapeHtml(item.title.replace(/^Day\\s+[^—]+—\\s*/, '')) + '</h1><div class="lesson-meta">' + evidence + visual + (item.structured ? '<span class="badge ok">Bài học có cấu trúc</span>' : '<span class="badge warn">Bản legacy</span>') + '</div>' + sources + questions + bodyHtml;
      
      // Auto attach copy code buttons to newly rendered lesson
      document.querySelectorAll('#lesson pre').forEach(function(pre){{
        if(pre.querySelector('.copy-code-btn')) return;
        var btn = document.createElement('button');
        btn.className = 'copy-code-btn';
        btn.textContent = '📋 Copy';
        btn.onclick = function(){{
          var code = pre.querySelector('code') ? pre.querySelector('code').innerText : pre.innerText;
          navigator.clipboard.writeText(code).then(function(){{
            btn.textContent = '✅ Đã chép';
            btn.classList.add('copied');
            setTimeout(function(){{
              btn.textContent = '📋 Copy';
              btn.classList.remove('copied');
            }}, 2000);
          }});
        }};
        pre.appendChild(btn);
      }});

      history.replaceState(null, '', '#day-' + item.day);
    }}
    function buildList() {{
      const list = document.getElementById('dayList');
      const learned = getLearnedDays();
      list.innerHTML = lessons.map((item, i) => {{
        const isDone = learned.has(String(item.day));
        const checkIcon = isDone ? '✅' : '';
        return '<button class="day-item" id="btn-day-' + item.day + '" onclick="renderDay(' + i + ')">' +
          '<span class="day-num">Day ' + escapeHtml(item.day) + '</span>' +
          '<span class="day-check-badge" id="badge-day-' + item.day + '">' + checkIcon + '</span>' +
          '<span class="day-title">' + escapeHtml(item.title.replace(/^Day\\s+[^—]+—\\s*/, '')) + '</span>' +
        '</button>';
      }}).join('');
    }}
    function filterDays() {{
      var q = document.getElementById('searchInput').value.toLowerCase();
      document.querySelectorAll('.day-item').forEach(function(item, index) {{
        var data = lessons[index];
        item.style.display = (data.title + ' ' + data.summary).toLowerCase().includes(q) ? 'block' : 'none';
      }});
    }}
    buildList();
    updateProgressUI();
    const requested = (location.hash.match(/#day-([^&]+)/) || [])[1];
    const initial = Math.max(0, lessons.findIndex(x => String(x.day) === String(requested)));
    if (lessons.length) renderDay(initial);
  </script>
</body>
</html>"""

    with open(os.path.join(out_dir, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_html)
