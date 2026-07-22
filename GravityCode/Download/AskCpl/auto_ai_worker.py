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
    """Trả về timestamp hiện tại dạng [HH:MM:SS]"""
    return datetime.now().strftime("[%H:%M:%S]")

def run_auto_ai(api_keys_list, roadmap_path, doc_dir, out_dir, log_callback, force=False, update_keys_cb=None):
    def log(msg):
        log_callback(f"{_ts()} {msg}")
        
    def get_active_key():
        now = int(time.time())
        for k in api_keys_list:
            if k.get("status") == "exhausted" and k.get("reset_time", 0) > 0 and now > k.get("reset_time", 0):
                k["status"] = "active"
                k["reset_time"] = 0
                if update_keys_cb: update_keys_cb(api_keys_list)
                
            if k.get("status") == "active":
                return k
        return None
        
    def mark_key_exhausted(k):
        k["status"] = "exhausted"
        k["reset_time"] = int(time.time()) + 86400
        if update_keys_cb: update_keys_cb(api_keys_list)
        
    def mark_key_invalid(k):
        k["status"] = "invalid"
        if update_keys_cb: update_keys_cb(api_keys_list)


    try:
        import fitz  # PyMuPDF
    except ImportError:
        log_callback("❌ Lỗi: Thư viện PyMuPDF chưa được cài đặt. Vui lòng restart app để tự cài.")
        return
        
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    log("Đang đọc file roadmap...")
    try:
        with open(roadmap_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        log(f"❌ Lỗi đọc roadmap: {e}")
        return
        
    # Tách theo Day X
    days_blocks = re.split(r'\n## (Day \d+.*?)\n', "\n" + content)
    days_parsed = []
    
    for i in range(1, len(days_blocks), 2):
        day_title = days_blocks[i].strip()
        day_content = days_blocks[i+1]
        
        # Tìm file PDF (url kết thúc bằng .pdf)
        pdf_filename = None
        url_match = re.search(r'\(http.*?/([^/]+\.pdf)\)', day_content, re.IGNORECASE)
        if url_match:
            pdf_filename = url_match.group(1)
            
        # Trích xuất page range từ metadata (do roadmap mở rộng tạo ra)
        page_start = 0  # 0-indexed
        page_end = None  # None = lấy tối đa 10 trang
        pages_match = re.search(r'<!--\s*pages:\s*(\d+)-(\d+)\s*-->', day_content)
        if pages_match:
            page_start = int(pages_match.group(1)) - 1  # chuyển sang 0-indexed
            page_end = int(pages_match.group(2))        # exclusive end cho range()
            
        # Trích xuất Prompt
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
            
    log(f"✅ Đã tìm thấy {len(days_parsed)} Days trong roadmap.")
    
    # === AUTO-RESUME ===
    completed_days = set()
    session_data = []
    session_file = os.path.join(out_dir, "session.json")
    
    if os.path.exists(session_file) and force:
        log("🗑️ Force Restart: Xóa session cũ và chạy lại từ Day 1...")
        if os.path.exists(session_file):
            os.remove(session_file)
    elif os.path.exists(session_file):
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    if content.startswith('"') and content.endswith('"'):
                        import base64
                        content = content[1:-1]
                        decoded_str = base64.b64decode(content).decode('utf-8')
                        session_data = json.loads(decoded_str)
                    else:
                        session_data = json.loads(content)
                        
                    for item in session_data:
                        if item.get("completed"):
                            completed_days.add(item["day"].strip())
            log(f"🔄 Auto-Resume: Đã khôi phục {len(completed_days)} Days đã hoàn thành từ trước.")
            # Tạo lại index.html ngay nếu đã có dữ liệu
            if session_data:
                create_viewer(out_dir, session_data)
                log(f"📄 Đã tạo lại index.html với {len(session_data)} Days hiện có.")
        except Exception as e:
            log(f"⚠️ Không thể đọc session.json cũ, sẽ chạy lại từ đầu: {e}")
            session_data = []
    
    for idx, day in enumerate(days_parsed):
        day_clean_title = day['title'].replace("## ", "").strip()
        if day_clean_title in completed_days:
            log(f"⏭️ Bỏ qua [{idx+1}/{len(days_parsed)}]: {day_clean_title} (Đã hoàn thành)")
            continue
            
        log(f"\n--- Đang xử lý [{idx+1}/{len(days_parsed)}]: {day['title']} ---")
        prompt = day['prompt']
        
        pdf_text = ""
        if day['pdf']:
            pdf_path = find_file(doc_dir, day['pdf'])
            if pdf_path:
                log(f"📄 Đang đọc PDF: {day['pdf']} ...")
                try:
                    doc = fitz.open(pdf_path)
                    
                    # Dùng page range từ metadata nếu có (roadmap mở rộng)
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
                    log(f"Trích xuất trang {p_start+1}–{p_end} / {total_pages} ({p_end - p_start} trang).")
                except Exception as e:
                    log(f"⚠️ Lỗi đọc PDF: {e}")
            else:
                log(f"⚠️ KHÔNG tìm thấy file '{day['pdf']}' trong thư mục!")
        
        # Gắn text vào prompt
        day_clean_title = day['title'].replace("## ", "").strip()
        full_prompt = f"LƯU Ý: Đây là nội dung cho '{day_clean_title}'.\n\n{prompt}"
        if pdf_text:
            full_prompt = f"Dưới đây là toàn bộ văn bản được trích xuất trực tiếp từ file PDF cho '{day_clean_title}'.\nBẠN ĐÃ ĐỌC ĐƯỢC NỘI DUNG NÀY, DO ĐÓ KHÔNG ĐƯỢC nói rằng 'tôi không thể truy cập' hay 'tôi chưa thể truy cập'. Hãy trả lời trực tiếp dựa trên nội dung sau:\n\n{pdf_text[:120000]}\n\n---\n\n{prompt}"
            
        max_retries = 3
        daily_quota_hit = False
        day_success = False
        
        while True:
            current_key_obj = get_active_key()
            if not current_key_obj:
                log("🚫 ĐÃ HẾT KEY KHẢ DỤNG! Tất cả các API Key đều bị hết Quota ngày hoặc hỏng.")
                log(f"   → Đã xử lý xong {len(session_data)} Days. Hãy thêm Key mới vào quản lý hoặc chờ qua ngày.")
                daily_quota_hit = True
                break
                
            api_key = current_key_obj.get("key")
            key_email = current_key_obj.get("email")
            log(f"🤖 Đang gửi request lên Gemini bằng Key: {key_email}...")
            
            key_failed = False
            for attempt in range(max_retries):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                    headers = {'Content-Type': 'application/json'}
                    payload = {
                        "contents": [{"parts": [{"text": full_prompt}]}],
                        "generationConfig": {
                            "maxOutputTokens": 8192,
                            "temperature": 0.7
                        }
                    }
                    
                    log(f"⏳ Đang xử lý khoảng {len(pdf_text)} ký tự. AI bắt đầu suy nghĩ...")
                    start_time = time.time()
                    
                    # Vòng lặp song song in log mỗi 10s
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(requests.post, url, headers=headers, json=payload, timeout=180)
                        last_printed = 0
                        while not future.done():
                            elapsed = int(time.time() - start_time)
                            if elapsed > 0 and elapsed % 10 == 0 and elapsed != last_printed:
                                log(f"   ... Vẫn đang chờ AI viết kết quả ({elapsed}s trôi qua) ...")
                                last_printed = elapsed
                            time.sleep(1)
                            
                    resp = future.result()
                    elapsed_total = time.time() - start_time
                    resp_json = resp.json()
                    
                    if resp.status_code != 200:
                        error_msg = json.dumps(resp_json.get('error', {}), ensure_ascii=False)
                        raise Exception(f"HTTP {resp.status_code} - {error_msg}")
                        
                    # Extract text
                    generated_text = resp_json['candidates'][0]['content']['parts'][0]['text']
                    html_res = markdown_to_html(generated_text)
                        
                    log(f"✅ Nhận kết quả thành công! ({elapsed_total:.1f}s)")
                    
                    session_data.append({
                        "day": day['title'].replace("## ", ""),
                        "html": html_res,
                        "timestamp": int(time.time() * 1000),
                        "completed": True
                    })
                    day_success = True
                    break # Thành công thì thoát khỏi vòng lặp retry
                    
                except requests.exceptions.Timeout:
                    log("⚠️ Lỗi Timeout: Máy chủ Google phản hồi quá lâu (>180s).")
                    if attempt < max_retries - 1:
                        log(f"⏳ Đang thử lại (Lần thử {attempt + 2}/{max_retries})...")
                    else:
                        log("❌ Đã thử lại nhiều lần nhưng Google vẫn Timeout.")
                        break
                except Exception as e:
                    error_msg = str(e)
                    if any(x in error_msg for x in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"]):
                        # Kiểm tra xem có phải giới hạn theo NGÀY không
                        if "PerDay" in error_msg:
                            log(f"🚫 QUOTA NGÀY của Key {key_email} đã cạn. Đang tự động đổi Key...")
                            mark_key_exhausted(current_key_obj)
                            key_failed = True
                            break
                        
                        # Parse retryDelay từ response để chờ đúng thời gian
                        import re as _re
                        delay_match = _re.search(r'"retryDelay":\s*"(\d+)s"', error_msg)
                        wait_sec = int(delay_match.group(1)) + 5 if delay_match else 65
                        
                        if attempt < max_retries - 1:
                            log(f"⏳ Quá tải API (Per Minute/Temp). Tạm nghỉ {wait_sec}s rồi thử lại (Lần thử {attempt + 2}/{max_retries})...")
                            time.sleep(wait_sec)
                        else:
                            log(f"❌ Đã thử lại {max_retries} lần nhưng vẫn bị quá tải API.")
                            break
                    else:
                        log(f"❌ Lỗi gọi Gemini: {error_msg}")
                        if any(x in error_msg for x in ["API_KEY_INVALID", "400", "403", "PERMISSION_DENIED"]):
                            log(f"🚫 Key {key_email} bị lỗi/từ chối truy cập (403/Invalid). Đang tự động đổi Key...")
                            mark_key_invalid(current_key_obj)
                            key_failed = True
                        break
            
            if key_failed:
                continue
                
            break # Thành công thì thoát khỏi vòng lặp đổi key
            
        if daily_quota_hit:
            break
            
        if not day_success:
            log(f"❌ Quá trình xử lý {day_clean_title} thất bại và không thể phục hồi. Dừng toàn bộ tiến trình!")
            break
            
        # Lưu đè file session.json mỗi vòng lặp để an toàn
        save_session(session_data, out_dir)
        # Cập nhật luôn index.html sau mỗi Day để xem trước được ngay
        create_viewer(out_dir, session_data)
        
        # Chờ 3s giữa các request
        time.sleep(3)
        
    log(f"\n✅ Hoàn tất! Đã xử lý {len(session_data)} Days.")
    save_session(session_data, out_dir)
    create_viewer(out_dir, session_data)
    log(f"✅ index.html đã được tạo tại {out_dir}")

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
        return md_text # Fallback

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
    .navbar { display: flex; justify-content: space-between; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; }
    .nav-btn { background: #0078d4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: 500; text-align: center; flex: 1; margin: 0 10px; transition: 0.2s; }
    .nav-btn:hover { background: #005a9e; }
    .nav-btn.home { background: #475569; }
    .nav-btn.home:hover { background: #334155; }
    .nav-btn.disabled { background: #cbd5e1; color: #94a3b8; cursor: not-allowed; pointer-events: none; }
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
        
    # Pass 1: Tạo tên file trước để làm navigation
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
        
        # Parse day_num for visual listing
        day_num_match = re.search(r'Day\s*([\w]+)', day_title)
        day_num_str = day_num_match.group(1) if day_num_match else str(idx+1)
        
        # Tạo NavBar
        prev_html = f'<a href="{session_data[idx-1]["file_name"]}" class="nav-btn">⬅ Bài trước</a>' if idx > 0 else '<span class="nav-btn disabled">⬅ Bài trước</span>'
        next_html = f'<a href="{session_data[idx+1]["file_name"]}" class="nav-btn">Bài tiếp ➡</a>' if idx < len(session_data)-1 else '<span class="nav-btn disabled">Bài tiếp ➡</span>'
        nav_bar = f'<div class="navbar">\n{prev_html}\n<a href="index.html" class="nav-btn home">🏠 Mục Lục</a>\n{next_html}\n</div>'
        
        # Sinh HTML từng ngày
        day_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{day_title}</title>
  <style>{day_css}</style>
</head>
<body>
  <header>
    <h1>{day_title}</h1>
    <p>Tóm tắt & Dịch tự động bởi AI — Ngày sinh: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
  </header>
  <div class="content">{item.get('html', '')}</div>
  {nav_bar}
</body>
</html>"""
        
        with open(os.path.join(out_dir, file_name), 'w', encoding='utf-8') as f:
            f.write(day_html)
            
        # Add to index list
        safe_title = day_title.replace('<', '&lt;').replace('>', '&gt;')
        items_html += (
            f'    <a class="day-item" id="day-{day_num_str}" href="{file_name}">\n'
            f'      <span class="day-num">Day {day_num_str}</span>\n'
            f'      <span class="day-title">{safe_title}</span>\n'
            f'    </a>\n'
        )

    # Sinh index.html
    folder_name = os.path.basename(os.path.abspath(out_dir)) or "Tài liệu Sinh bởi AI"
    total_days = len(session_data)
    
    index_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>&#128218; {folder_name} &#8212; M&#7909;c L&#7909;c</title>
  <style>{index_css}</style>
</head>
<body>
  <div class="header">
    <h1>&#128218; {folder_name}</h1>
    <p>T&#7893;ng c&#7897;ng {total_days} ph&#7847;n \u0111\u00e3 x\u1eed l\u00fd</p>
  </div>
  <div class="container">
    <div class="stats">
      <span>T&#7893;ng s&#7889; Day: <b>{total_days}</b></span>
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
