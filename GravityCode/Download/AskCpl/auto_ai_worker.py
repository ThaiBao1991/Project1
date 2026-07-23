import os
import json
import re
import time
import base64
import urllib.parse
from datetime import datetime
import requests
import concurrent.futures

def _ts():
    """Trở về timestamp hiện tại dạng [HH:MM:SS]"""
    return datetime.now().strftime("[%H:%M:%S]")

def run_auto_ai(api_keys_list, roadmap_path, doc_dir, out_dir, log_callback, 
                force=False, update_keys_cb=None, enable_followup=True, max_followup=3, start_day=0):
    """
    Chạy tự động phân tích lộ trình học bằng Gemini API.
    Tham số mới:
      - enable_followup: Bật/tắt hỏi bổ sung (YC5)
      - max_followup: Số lượt hỏi bổ sung tối đa
    """
    def log(msg):
        log_callback(f"{_ts()} {msg}")
        
    def get_active_key():
        now = int(time.time())
        for k in api_keys_list:
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
                    if update_keys_cb: update_keys_cb(api_keys_list)
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
        log(f"⚠ Key {k.get('email')} bị đánh dấu Exhausted. Sẽ check lại sau 3 tiếng.")
        if update_keys_cb: update_keys_cb(api_keys_list)
        
    def mark_key_invalid(k):
        now = int(time.time())
        k["status"] = "invalid"
        k["last_check_time"] = now
        log(f"✗ Key {k.get('email')} bị đánh dấu Invalid.")
        if update_keys_cb: update_keys_cb(api_keys_list)

    def call_gemini_api(prompt_text, log_prefix=""):
        """Gọi Gemini REST API trực tiếp với cơ chế chọn key thông minh và tự động retry."""
        max_retries = 3
        while True:
            current_key_obj = get_active_key()
            if not current_key_obj:
                log(f"{log_prefix}⚠ KHÔNG tìm thấy API Key nào khả dụng!")
                return None, False, True  # daily_quota_hit = True

            api_key = current_key_obj.get("key")
            key_email = current_key_obj.get("email")
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
            headers = {'Content-Type': 'application/json'}
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "generationConfig": {
                    "maxOutputTokens": 8192,
                    "temperature": 0.7
                }
            }
            
            key_failed = False
            for attempt in range(max_retries):
                try:
                    start_time = time.time()
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(requests.post, url, headers=headers, json=payload, timeout=180)
                        last_printed = 0
                        while not future.done():
                            elapsed = int(time.time() - start_time)
                            if elapsed > 0 and elapsed % 10 == 0 and elapsed != last_printed:
                                log(f"{log_prefix}   ... Đang chờ AI phản hồi ({elapsed}s) ...")
                                last_printed = elapsed
                            time.sleep(1)
                            
                    resp = future.result()
                    elapsed_total = time.time() - start_time
                    resp_json = resp.json()
                    
                    if resp.status_code != 200:
                        error_msg = json.dumps(resp_json.get('error', {}), ensure_ascii=False)
                        raise Exception(f"HTTP {resp.status_code} - {error_msg}")
                        
                    generated_text = resp_json['candidates'][0]['content']['parts'][0]['text']
                    
                    # Thành công -> cập nhật last_check_time
                    current_key_obj["last_check_time"] = int(time.time())
                    # Nếu đang ở trạng thái exhausted (sau 3 tiếng thử lại thành công) -> đưa về active
                    if current_key_obj.get("status") == "exhausted":
                        current_key_obj["status"] = "active"
                        current_key_obj["reset_time"] = 0
                        current_key_obj["next_check_time"] = 0
                    
                    if update_keys_cb: update_keys_cb(api_keys_list)
                    return generated_text, True, False
                    
                except requests.exceptions.Timeout:
                    log(f"{log_prefix}⚠ Timeout khi kết nối đến Gemini (Lần {attempt+1}/{max_retries}).")
                    if attempt == max_retries - 1:
                        # Thất bại do timeout nhiều lần, đổi sang key khác cho chắc
                        key_failed = True
                        break
                except Exception as e:
                    error_msg = str(e)
                    # Quá hạn ngạch (429)
                    if any(x in error_msg for x in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"]):
                        if "PerDay" in error_msg:
                            log(f"{log_prefix}⚠ Key {key_email} Hết quota ngày. Chuyển key...")
                            mark_key_exhausted(current_key_obj)
                            key_failed = True
                            break
                        
                        # Quá hạn ngạch theo phút (Per Minute) -> Đợi rồi thử lại
                        import re as _re
                        delay_match = _re.search(r'"retryDelay":\s*"(\d+)s"', error_msg)
                        wait_sec = int(delay_match.group(1)) + 5 if delay_match else 65
                        
                        if attempt < max_retries - 1:
                            log(f"{log_prefix}⏳ API quá tải (phút). Chờ {wait_sec}s rồi thử lại...")
                            time.sleep(wait_sec)
                        else:
                            log(f"{log_prefix}⚠ Key {key_email} bị lỗi quá tải liên tục.")
                            mark_key_exhausted(current_key_obj) # Đánh dấu tạm chờ
                            key_failed = True
                            break
                    else:
                        log(f"{log_prefix} Lỗi Gemini: {error_msg}")
                        # API key hỏng/sai/403
                        if any(x in error_msg for x in ["API_KEY_INVALID", "400", "403", "PERMISSION_DENIED"]):
                            log(f"{log_prefix}⚠ Key {key_email} bị từ chối truy cập (403/Invalid). Chuyển key...")
                            mark_key_invalid(current_key_obj)
                            key_failed = True
                        else:
                            # Các lỗi vặt khác thì tạm thời đổi key
                            key_failed = True
                        break
            
            if key_failed:
                continue
            break
        return None, False, False

    try:
        import fitz  # PyMuPDF
    except ImportError:
        log_callback("⚠ Lỗi: Thư viện PyMuPDF chưa được cài đặt.")
        return
        
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    log("Đang đọc file roadmap...")
    try:
        with open(roadmap_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        log(f"⚠ Lỗi đọc roadmap: {e}")
        return
        
    # Tách theo Day X
    days_blocks = re.split(r'\n## (Day \d+.*?)\n', "\n" + content)
    days_parsed = []
    
    for i in range(1, len(days_blocks), 2):
        day_title = days_blocks[i].strip()
        day_content = days_blocks[i+1]
        
        pdf_filename = None
        url_match = re.search(r'\(http.*?/([^/]+\.pdf)\)', day_content, re.IGNORECASE)
        if url_match:
            pdf_filename = url_match.group(1)
            
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
                        decoded_str = base64.b64decode(content).decode('utf-8')
                        session_data = json.loads(decoded_str)
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
    
    for idx, day in enumerate(days_parsed):
        day_clean_title = day['title'].replace("## ", "").strip()
        
        if start_day > 0 and get_day_num(day['title']) > 0 and get_day_num(day['title']) < start_day:
            continue
            
        if day_clean_title in completed_days:
            log(f"⏭ Bỏ qua [{idx+1}/{len(days_parsed)}]: {day_clean_title} (Đã hoàn thành)")
            continue
            
        log(f"\n--- Đang xử lý [{idx+1}/{len(days_parsed)}]: {day['title']} ---")
        prompt = day['prompt']
        
        pdf_text = ""
        if day['pdf']:
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
        day_clean_title = day['title'].replace("## ", "").strip()
        full_prompt = f"LƯU Ý: Đây là nội dung cho '{day_clean_title}'.\n\n{prompt}"
        if pdf_text:
            full_prompt = f"Dưới đây là toàn bộ văn bản được trích xuất trực tiếp từ file PDF cho '{day_clean_title}'.\nBẠN ĐÃ ĐỌC ĐƯỢC NỘI DUNG NÀY, DO ĐÓ KHÔNG ĐƯỢC nói rằng 'tôi không thể truy cập' hay 'tôi chưa thể truy cập'. Hãy trả lời trực tiếp dựa trên nội dung sau:\n\n{pdf_text[:120000]}\n\n---\n\n{prompt}"
            
        # Lượt 1: Gửi câu hỏi chính
        daily_quota_hit = False
        day_success = False
        all_responses = []
        got_complete = False

        if day_clean_title in incomplete_days_refs:
            session_item = incomplete_days_refs[day_clean_title]
            all_responses = list(session_item.get("raw_responses", []))
            log(f"↪ Tiếp tục hỏi bổ sung cho {day_clean_title} (từ lượt {len(all_responses) + 1})...")
        else:
            log(f"💬 [Lượt 1] Gửi câu hỏi chính ({len(full_prompt)} ký tự)...")
            text1, ok1, quota_hit = call_gemini_api(full_prompt, log_prefix="  [Lượt 1] ")
            
            if quota_hit:
                daily_quota_hit = True
                break
            if not ok1 or not text1:
                log(f"✗ Lượt 1 thất bại cho {day_clean_title}. Dừng!")
                break
                
            all_responses = [text1]
            
        # YC5: Vòng lặp bổ sung (Multi-turn follow-up)
        
        if enable_followup:
            FOLLOWUP_PROMPT = (
                "Bạn có thấy còn điều gì cần bổ sung thêm để tôi hiểu rõ và đầy đủ hơn không?\n"
                "→ Nếu CÓ: hãy bổ sung ngay bên dưới.\n"
                "→ Nếu KHÔNG còn gì cần thêm: hãy chỉ trả lời đúng 1 dòng ở CUỐI phản hồi của bạn là:\n"
                "Đã đầy đủ"
            )
            
            for turn in range(max_followup):
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
                
                # Kiểm tra xem dòng cuối cùng của phản hồi có chứa "Đã đầy đủ" không
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
            
        # Gộp tất cả phản hồi thành HTML đẹp mắt
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
        else:
            session_data.append({
                "day": day['title'].replace("## ", ""),
                "html": html_res,
                "timestamp": int(time.time() * 1000),
                "completed": True,
                "followup_turns": len(all_responses) - 1,
                "followup_complete": got_complete,
                "raw_responses": all_responses
            })
        day_success = True
        
        if daily_quota_hit:
            break
            
        save_session(session_data, out_dir)
        create_viewer(out_dir, session_data)
        
        # Chờ 3s giữa các ngày học
        time.sleep(3)
        
    log(f"\n✓ Hoàn tất! Đã xử lý {len(session_data)} Days.")
    save_session(session_data, out_dir)
    create_viewer(out_dir, session_data)
    log(f"📁 index.html đã được tạo tại {out_dir}")

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
    except:
        return md_text

def save_session(data_list, out_dir):
    json_str = json.dumps(data_list, ensure_ascii=False)
    out_file = os.path.join(out_dir, "session.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(json_str)

def create_viewer(out_dir, session_data=None):
    if session_data is None:
        return
        
    day_css = """
    body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 860px; margin: 40px auto; padding: 0 20px; background: #f9f9f9; color: #1a1a1a; }
    header { background: #0078d4; color: #fff; padding: 16px 24px; border-radius: 8px; margin-bottom: 24px; }
    header h1 { margin: 0; font-size: 1.4em; }
    header p { margin: 4px 0 0; font-size: 0.85em; opacity: 0.85; }
    .content { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 24px; line-height: 1.7; }
    a.back { display: inline-block; margin-top: 20px; color: #0078d4; text-decoration: none; font-size: 0.9em; }
    a.back:hover { text-decoration: underline; }
    h2, h3 { color: #005a9e; margin-top: 1.5em; }
    code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
    pre { background: #f0f0f0; padding: 12px; border-radius: 6px; overflow-x: auto; }
    table { border-collapse: collapse; width: 100%; margin: 15px 0; }
    th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
    th { background: #0078d4; color: #fff; }
    tr:nth-child(even) { background: #f5f5f5; }
    /* Loại bỏ CSS navbar cũ để thay bằng css của addon */
    body { padding-top: 52px !important; }
    """
    
    index_css = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f0c29; color: #e0e0f0; min-height: 100vh; }
    .header { background: linear-gradient(135deg, #1a1a3e, #2d2b55); padding: 32px 24px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1); }
    .header h1 { font-size: 2em; color: #a78bfa; margin-bottom: 8px; }
    .header p { color: #9090b0; font-size: 0.95em; }
    .container { max-width: 820px; margin: 0 auto; padding: 24px 16px; }
    .stats { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px 20px; margin-bottom: 20px; display: flex; gap: 24px; flex-wrap: wrap; }
    .stats span { color: #a0a0c0; font-size: 0.9em; }
    .stats b { color: #a78bfa; }
    .search-box { width: 100%; padding: 10px 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.08); color: #e0e0f0; font-size: 14px; margin-bottom: 16px; outline: none; transition: border-color 0.2s; }
    .search-box:focus { border-color: rgba(167,139,250,0.6); }
    .day-list { display: flex; flex-direction: column; gap: 4px; }
    .day-item { display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-radius: 8px; text-decoration: none; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07); transition: all 0.18s; }
    .day-item:hover { background: rgba(167,139,250,0.15); border-color: rgba(167,139,250,0.4); transform: translateX(4px); }
    .day-num { font-size: 0.8em; font-weight: bold; color: #a78bfa; min-width: 64px; flex-shrink: 0; }
    .day-title { color: #c0c0e0; font-size: 0.93em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    """
    
    import re
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
    for idx, item in enumerate(session_data):
        day_title = item['day_title']
        file_name = item['file_name']
        
        day_num_match = re.search(r'Day\s*([\w]+)', day_title)
        day_num_str = day_num_match.group(1) if day_num_match else str(idx+1)
        
        # NAV-BAR giống hệt Addon Word Export
        total_days_num = len(session_data)
        nav_bar = f"""<!-- NAV-BAR-V2 -->
<style>
#askcpl-nav{{position:fixed;top:0;left:0;right:0;z-index:9999;display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);color:#fff;padding:8px 16px;box-shadow:0 2px 12px rgba(0,0,0,.5);font-family:'Segoe UI',Arial,sans-serif;font-size:14px;box-sizing:border-box;height:48px;}}
#askcpl-nav button{{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:15px;transition:background .2s;flex-shrink:0;}}
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
</style>
<div id="askcpl-nav">
  <button id="nav-prev" onclick="askcplNav(-1)">◀ Prev</button>
  <a id="askcpl-nav-home" href="index.html" title="Quay lại Menu Tổng">🏠 Menu</a>
  <span id="askcpl-nav-title" onclick="askcplToggleToc()" title="Click xem Mục Lục">Day ... ▼</span>
  <button id="nav-next" onclick="askcplNav(1)">Next ▶</button>
</div>
<div id="askcpl-toc"></div>
<script>
(function(){{
  var MAX_DAYS = {total_days_num};
  var m = window.location.pathname.match(/(\d+)_.*\.html/i) 
       || window.location.href.match(/(\d+)_.*\.html/i);
  var cur = m ? parseInt(m[1]) : {idx + 1};
  
  document.getElementById('askcpl-nav-title').textContent = 'Day ' + cur + ' ▼';
  document.getElementById('askcpl-nav-home').href = 'index.html#day-' + cur;

  if(cur <= 1) document.getElementById('nav-prev').disabled = true;
  if(cur >= MAX_DAYS) document.getElementById('nav-next').disabled = true;
  
  window.askcplNav = function(d){{
    var n = cur + d;
    if(n < 1 || n > MAX_DAYS) return;
    // Tìm file tương ứng với số n
    var allFiles = {json.dumps([s["file_name"] for s in session_data])};
    if (n-1 >= 0 && n-1 < allFiles.length) {{
        window.location.href = allFiles[n-1];
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
  </style>
</head>
<body>
  <header>
    <h1>{day_title}</h1>
    <p>Tóm tắt &amp; Dịch tự động bởi AI · {datetime.now().strftime('%d/%m/%Y %H:%M')} {followup_badge}</p>
  </header>
  <div class="content">{item.get('html', '')}</div>
  {nav_bar}
</body>
</html>"""
        
        with open(os.path.join(out_dir, file_name), 'w', encoding='utf-8') as f:
            f.write(day_html)
            
        safe_title = day_title.replace('<', '&lt;').replace('>', '&gt;')
        items_html += (
            f'    <a class="day-item" id="day-{day_num_str}" href="{file_name}">\n'
            f'      <span class="day-num">Day {day_num_str}</span>\n'
            f'      <span class="day-title">{safe_title}</span>\n'
            f'    </a>\n'
        )

    folder_name = os.path.basename(os.path.abspath(out_dir)) or "Tài liệu Sinh bởi AI"
    total_days = len(session_data)
    
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
    <h1>📚 {folder_name}</h1>
    <p>Tổng cộng {total_days} phần đã xử lý</p>
  </div>
  <div class="container">
    <div class="stats">
      <span>Tổng số Day: <b>{total_days}</b></span>
    </div>
    <input class="search-box" type="text" id="searchInput" placeholder="Tìm kiếm Day hoặc nội dung..." oninput="filterDays()">
    <div class="day-list" id="dayList">
{items_html}
    </div>
  </div>
  <script>
    function filterDays() {{
      var q = document.getElementById('searchInput').value.toLowerCase();
      document.querySelectorAll('.day-item').forEach(function(item) {{
        item.style.display = item.textContent.toLowerCase().includes(q) ? 'flex' : 'none';
      }});
    }}
  </script>
</body>
</html>"""

    with open(os.path.join(out_dir, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_html)
