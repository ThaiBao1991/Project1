import os
import shutil
import re
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from exercise_builder import save_exercise_to_html
from settings import load_settings

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # Max 50MB

def extract_inner_html(content):
    start_marker = "<!-- EXERCISE START -->"
    end_marker = "<!-- EXERCISE END -->"
    if start_marker not in content or end_marker not in content:
        return ""
    
    start_idx = content.find(start_marker) + len(start_marker)
    end_idx = content.find(end_marker)
    ex_html = content[start_idx:end_idx].strip()
    
    # Priority 1: Format cũ với class "exercise-body ql-editor"
    if '<div class="exercise-body ql-editor"' in ex_html:
        body_start = ex_html.find('<div class="exercise-body ql-editor"')
        body_start = ex_html.find('>', body_start) + 1
        body_end = ex_html.rfind('</div>')
        body_end = ex_html.rfind('</div>', 0, body_end) 
        return ex_html[body_start:body_end].strip()
    
    # Priority 2: Format từ Web Editor — class "ql-editor" thông thường
    elif '<div class="ql-editor">' in ex_html:
        marker = '<div class="ql-editor">'
        body_start = ex_html.find(marker) + len(marker)
        # Dùng depth tracking để tìm đúng thẻ </div> đóng (tránh bị nhầm bởi div lồng trong content)
        depth = 1
        pos = body_start
        body_end = len(ex_html)
        while pos < len(ex_html):
            next_open = ex_html.find('<div', pos)
            next_close = ex_html.find('</div>', pos)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                pos = next_open + 4
            else:
                depth -= 1
                if depth == 0:
                    body_end = next_close
                    break
                pos = next_close + 6
        return ex_html[body_start:body_end].strip()
    
    # Fallback: format block cũ (text/code block)
    else:
        core = re.sub(r'<div class="exercise-container"[^>]*>', '', ex_html, count=1)
        core = re.sub(r'<h2[^>]*>.*?</h2>', '', core, count=1, flags=re.DOTALL)
        core = core.rstrip()
        if core.endswith('</div>'):
            core = core[:-6]
        return core.strip()

def update_index_links(index_content, day, status_html, archival_link_html, mode):
    search_str = f'href="{day}"'
    idx = index_content.find(search_str)
    if idx == -1:
        return index_content
        
    a_end_idx = index_content.find('</a>', idx)
    if a_end_idx == -1:
        return index_content
    a_end_idx += 4
    
    chunk = index_content[a_end_idx:a_end_idx+500]
    escaped_day = re.escape(day)
    pattern = r'^(?:\s*<span class="ex-status" data-day="' + escaped_day + r'".*?</span>)?(?:\s*<a href="exercise/[^"]+" class="ex-archival-link" data-day="' + escaped_day + r'".*?</a>)?'
    
    match = re.match(pattern, chunk, flags=re.DOTALL)
    if match:
        replace_len = len(match.group(0))
        if mode == "direct":
            new_chunk = status_html
        else:
            new_chunk = status_html + archival_link_html
        return index_content[:a_end_idx] + new_chunk + index_content[a_end_idx + replace_len:]
    return index_content

@app.route('/editor')
def editor():
    day = request.args.get('day', '')
    target_dir = request.args.get('target_dir', '')
    mode = request.args.get('mode', 'direct')
    html_content = ""
    if day and target_dir:
        day_file_base = os.path.splitext(day)[0]
        archival_file_name = f"{day_file_base} exercise.html"
        archival_path = os.path.join(target_dir, "exercise", archival_file_name)
        html_path = os.path.join(target_dir, day)

        content_to_extract = ""
        EXERCISE_MARKER = "<!-- EXERCISE START -->"

        # Bước 1: Ưu tiên đọc theo mode được yêu cầu
        if mode == "standalone":
            if os.path.exists(html_path):
                with open(html_path, 'r', encoding='utf-8') as f:
                    tmp = f.read()
                if EXERCISE_MARKER in tmp:
                    content_to_extract = tmp
        elif mode == "archival" and os.path.exists(archival_path):
            with open(archival_path, 'r', encoding='utf-8') as f:
                content_to_extract = f.read()
        elif mode == "direct" and os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                tmp = f.read()
            # Chỉ dùng nếu file thực sự chứa exercise (tránh đọc nhầm bài học chính)
            if EXERCISE_MARKER in tmp:
                content_to_extract = tmp
            # Nếu không có marker → bỏ qua, chuyển sang Bước 2 fallback

        # Bước 2: Fallback thông minh — tìm ở nơi còn lại
        if not content_to_extract:
            if os.path.exists(archival_path):
                with open(archival_path, 'r', encoding='utf-8') as f:
                    content_to_extract = f.read()
            elif os.path.exists(html_path):
                with open(html_path, 'r', encoding='utf-8') as f:
                    tmp = f.read()
                if EXERCISE_MARKER in tmp:
                    content_to_extract = tmp

        if content_to_extract:
            extracted = extract_inner_html(content_to_extract)
            if extracted:
                html_content = extracted

    return render_template('editor.html', day=day, target_dir=target_dir, mode=mode, existing_content=html_content)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    target_dir = request.form.get('target_dir', '')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and target_dir:
        filename = secure_filename(file.filename)
        
        attachments_dir = os.path.join(target_dir, "attachments")
        if not os.path.exists(attachments_dir):
            os.makedirs(attachments_dir)
            
        file_path = os.path.join(attachments_dir, filename)
        file.save(file_path)
        
        file_url = f"attachments/{filename}"
        
        # Check file type for specific HTML injection if needed, 
        # but Quill will handle it or we return URL
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        file_type = 'file'
        if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']: file_type = 'image'
        elif file_ext in ['mp3', 'wav', 'ogg']: file_type = 'audio'
        elif file_ext in ['mp4', 'webm']: file_type = 'video'
        
        return jsonify({'url': file_url, 'filename': filename, 'type': file_type})
        
    return jsonify({'error': 'Missing target_dir'}), 400

@app.route('/save', methods=['POST'])
def save_content():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    day = data.get('day')
    target_dir = data.get('target_dir')
    html_content = data.get('html_content')
    is_completed = data.get('is_completed', False)
    mode = data.get('mode', 'direct')
    
    if not day or not target_dir or html_content is None:
        return jsonify({'error': 'Missing parameters'}), 400
        
    html_path = os.path.join(target_dir, day)
    
    html_snippets = ["<!-- EXERCISE START -->"]
    
    day_file_base = os.path.splitext(day)[0]
    archival_file_name = f"{day_file_base} exercise.html"
    
    if mode == "standalone":
        html_snippets.append('<!DOCTYPE html>')
        html_snippets.append('<html lang="vi">')
        html_snippets.append('<head>')
        html_snippets.append('  <meta charset="UTF-8">')
        html_snippets.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_snippets.append(f'  <title>{day_file_base}</title>')
        html_snippets.append('  <style>body { font-family: sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; }</style>')
        html_snippets.append('</head>')
        html_snippets.append('<body>')
    elif mode == "archival":
        html_snippets.append('<!DOCTYPE html>')
        html_snippets.append('<html lang="vi">')
        html_snippets.append('<head>')
        html_snippets.append('  <meta charset="UTF-8">')
        html_snippets.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_snippets.append(f'  <title>Bài tập - {day_file_base}</title>')
        html_snippets.append('  <style>body { font-family: sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; }</style>')
        html_snippets.append('</head>')
        html_snippets.append('<body>')
        html_snippets.append('  <a href="../index.html" style="display: inline-block; margin-bottom: 20px; padding: 10px 15px; background: #0078d4; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">⬅ Quay lại Index</a>')

    if mode == "standalone":
        html_snippets.append('<div class="note-container" style="margin: 0 auto; max-width: 900px; padding: 20px; background-color: #fff; font-family: sans-serif; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 8px;">')
        html_snippets.append(f'  <h1 style="color: #333; border-bottom: 2px solid #0078d4; padding-bottom: 10px; margin-top: 0;">{day_file_base}</h1>')
        html_snippets.append(f'  <div class="ql-editor">{html_content}</div>')
        html_snippets.append('</div>')
    else:
        html_snippets.append('<div class="exercise-container" style="margin-top: 20px; padding: 20px; border-top: 2px dashed #0078d4; background-color: #f9f9f9; font-family: sans-serif; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-radius: 8px;">')
        html_snippets.append('  <h2 style="color: #0078d4;">Bài Tập & Lời Giải</h2>')
        html_snippets.append(f'  <div class="ql-editor">{html_content}</div>')
        html_snippets.append('</div>')
    
    has_code = 'class="language-' in html_content or '<pre class="ql-syntax' in html_content
    if has_code:
        html_snippets.insert(1 if mode == "direct" else 10, '<link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />')
        html_snippets.append('<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>')
        html_snippets.append('<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>')

    if mode == "archival" or mode == "standalone":
        html_snippets.append('</body>')
        html_snippets.append('</html>')

    html_snippets.append("<!-- EXERCISE END -->")
    new_ex_content = "\n".join(html_snippets)
    
    try:
        import logging
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exercise_server.log')
        logging.basicConfig(filename=log_path, level=logging.DEBUG)
        logging.debug(f"Saving day {day} with mode {mode}...")
        
        import re
        if mode == "direct":
            logging.debug("Reading direct html path")
            content = ""
            if os.path.exists(html_path):
                with open(html_path, "r", encoding="utf-8") as f:
                    content = f.read()

            start_marker = "<!-- EXERCISE START -->"
            end_marker = "<!-- EXERCISE END -->"
            if start_marker in content and end_marker in content:
                start_idx = content.find(start_marker)
                end_idx = content.find(end_marker) + len(end_marker)
                content = content[:start_idx] + content[end_idx:]

            if "</body>" in content:
                content = content.replace("</body>", new_ex_content + "\n</body>")
            else:
                content += "\n" + new_ex_content

            logging.debug("Writing direct html path")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(content)
                
        elif mode == "archival":
            logging.debug("Handling archival mode")
            exercise_dir = os.path.join(target_dir, "exercise")
            if not os.path.exists(exercise_dir):
                os.makedirs(exercise_dir)
            archival_path = os.path.join(exercise_dir, archival_file_name)
            with open(archival_path, "w", encoding="utf-8") as f:
                f.write(new_ex_content)
                
        elif mode == "standalone":
            logging.debug("Handling standalone mode")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(new_ex_content)
            logging.debug("Done save successfully")
            return jsonify({'status': 'success'})

        index_path = os.path.join(target_dir, "index.html")
        logging.debug(f"Updating index.html: {index_path}")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                index_content = f.read()

            if is_completed:
                status_html = f' <span class="ex-status" data-day="{day}" style="color: white; background-color: #2ea043; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold; margin-left: 10px;">Đã hoàn thành</span>'
            else:
                status_html = f' <span class="ex-status" data-day="{day}" style="color: white; background-color: #d97706; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold; margin-left: 10px;">Đang thực hiện</span>'
                
            archival_link_html = f' <a href="exercise/{archival_file_name}" class="ex-archival-link" data-day="{day}" style="margin-left: 5px; color: #0078d4; text-decoration: none; font-weight: bold;">[Mở Bài Tập]</a>'

            logging.debug("Running safe update_index_links")
            new_index_content = update_index_links(index_content, day, status_html, archival_link_html, mode)
            
            logging.debug("Writing index.html")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(new_index_content)

        # --- SYNC: Cập nhật exercises_data.json để App Python đọc lại được ---
        json_path = os.path.join(target_dir, "exercises_data.json")
        try:
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as fj:
                    ex_data = json.load(fj)
            else:
                ex_data = {}
            # Ghi đè block wysiwyg cho ngày này
            ex_data[day] = [{"type": "wysiwyg", "html": html_content}]
            with open(json_path, "w", encoding="utf-8") as fj:
                json.dump(ex_data, fj, ensure_ascii=False, indent=2)
            logging.debug("exercises_data.json synced with wysiwyg block")
        except Exception as sync_err:
            logging.warning(f"Could not sync exercises_data.json: {sync_err}")

        logging.debug("Done save successfully")
        return jsonify({'status': 'success'})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def run_server(port=None):
    # Disable werkzeug logging
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    config = load_settings().get("server", {})
    host = config.get("host", "127.0.0.1")
    if port is None:
        port = config.get("port", 5678)
    
    print(f"[*] Starting Exercise Server on http://{host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_server()
