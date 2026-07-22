import os
import shutil
import re

PRISM_CSS = "https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css"
PRISM_JS = "https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"
PRISM_AUTOLOADER = "https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"

def save_exercise_to_html(html_file_path: str, blocks: list, target_dir: str, is_completed: bool = False, mode: str = "direct"):
    # For direct mode, html_file_path must exist. For archival, it's just the day_X file path to get the name
    if mode == "direct" and not os.path.exists(html_file_path):
        return False, "File HTML không tồn tại."

    day_file_name = os.path.basename(html_file_path)
    day_file_base = os.path.splitext(day_file_name)[0]
    archival_file_name = f"{day_file_base} exercise.html"

    attachments_dir = os.path.join(target_dir, "attachments")
    if mode == "archival":
        attachments_dir = os.path.join(target_dir, "exercise", "attachments")
    
    html_snippets = ["<!-- EXERCISE START -->"]
    
    if mode == "archival":
        # Full HTML page boilerplate for archival
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

    html_snippets.append('<div class="exercise-container" style="margin-top: 20px; padding: 20px; border-top: 2px dashed #0078d4; background-color: #f9f9f9; font-family: sans-serif; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-radius: 8px;">')
    html_snippets.append('  <h2 style="color: #0078d4;">Bài Tập & Lời Giải</h2>')
    
    has_code = False

    for block in blocks:
        b_type = block.get("type")
        if b_type == "text":
            content = block.get("content", "").replace("\n", "<br>")
            html_snippets.append(f'  <div class="ex-text" style="margin-bottom: 15px; font-size: 16px; line-height: 1.5;">{content}</div>')
        elif b_type == "code":
            has_code = True
            language = block.get("language", "python").lower()
            content = block.get("content", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_snippets.append(f'  <div class="ex-code" style="margin-bottom: 15px; border-radius: 6px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">')
            html_snippets.append(f'    <pre><code class="language-{language}">{content}</code></pre>')
            html_snippets.append('  </div>')
        elif b_type == "file":
            filepath = block.get("filepath", "")
            filename = block.get("filename", "")
            if os.path.exists(filepath):
                if not os.path.exists(attachments_dir):
                    os.makedirs(attachments_dir)
                dest_path = os.path.join(attachments_dir, filename)
                try:
                    shutil.copy2(filepath, dest_path)
                except Exception as e:
                    print(f"Lỗi copy file: {e}")
                
                file_ext = filename.split('.')[-1].lower()
                icon = "📁"
                if file_ext in ["zip", "rar", "7z"]: icon = "📦"
                elif file_ext in ["py", "js", "html", "css"]: icon = "📄"
                
                html_snippets.append(f'  <div class="ex-file" style="margin-bottom: 15px;">')
                html_snippets.append(f'    <a href="attachments/{filename}" download style="display: inline-block; padding: 10px 15px; background: #2ea043; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">{icon} Tải xuống dự án đính kèm: {filename}</a>')
                html_snippets.append('  </div>')

    html_snippets.append('</div>')

    if has_code:
        html_snippets.insert(1 if mode == "direct" else 10, f'<link href="{PRISM_CSS}" rel="stylesheet" />')
        html_snippets.append(f'<script src="{PRISM_JS}"></script>')
        html_snippets.append(f'<script src="{PRISM_AUTOLOADER}"></script>')

    if mode == "archival":
        html_snippets.append('</body>')
        html_snippets.append('</html>')

    html_snippets.append("<!-- EXERCISE END -->")
    
    new_ex_content = "\n".join(html_snippets)

    if mode == "direct":
        with open(html_file_path, "r", encoding="utf-8") as f:
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

        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    elif mode == "archival":
        exercise_dir = os.path.join(target_dir, "exercise")
        if not os.path.exists(exercise_dir):
            os.makedirs(exercise_dir)
        archival_path = os.path.join(exercise_dir, archival_file_name)
        with open(archival_path, "w", encoding="utf-8") as f:
            f.write(new_ex_content)

    # Cập nhật index.html
    index_path = os.path.join(target_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            index_content = f.read()

        if is_completed:
            status_html = f' <span class="ex-status" data-day="{day_file_name}" style="color: white; background-color: #2ea043; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold; margin-left: 10px;">Đã hoàn thành</span>'
        else:
            status_html = f' <span class="ex-status" data-day="{day_file_name}" style="color: white; background-color: #d97706; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold; margin-left: 10px;">Đang thực hiện</span>'
            
        archival_link_html = f' <a href="exercise/{archival_file_name}" class="ex-archival-link" data-day="{day_file_name}" style="margin-left: 5px; color: #0078d4; text-decoration: none; font-weight: bold;">[Mở Bài Tập]</a>'

        escaped_day = re.escape(day_file_name)
        # Tìm link gốc của bài học
        # Chú ý: Có thể có status hoặc link cũ rồi, ta sẽ thay thế bằng nhóm mới
        pattern = r'(<a [^>]*href="' + escaped_day + r'"[^>]*>.*?</a>)(?:\s*<span class="ex-status" data-day="' + escaped_day + r'".*?</span>)?(?:\s*<a href="exercise/[^"]+" class="ex-archival-link" data-day="' + escaped_day + r'".*?</a>)?'
        
        if mode == "direct":
            new_index_content = re.sub(pattern, r'\1' + status_html, index_content, flags=re.DOTALL)
        else:
            new_index_content = re.sub(pattern, r'\1' + status_html + archival_link_html, index_content, flags=re.DOTALL)
        
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(new_index_content)

    return True, "Thành công"

def remove_exercise_from_html(html_file_path: str, target_dir: str):
    """
    Dọn dẹp bài tập khỏi index.html và day_X.html hoặc xóa file exercise tương ứng
    Hàm này dọn dẹp chung luôn không cần biết trước đó là mode gì (xóa sạch cả 2 nếu có)
    """
    day_file_name = os.path.basename(html_file_path)
    day_file_base = os.path.splitext(day_file_name)[0]
    archival_file_name = f"{day_file_base} exercise.html"
    
    # 1. Dọn dẹp index.html
    index_path = os.path.join(target_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            index_content = f.read()
            
        search_str = f'href="{day_file_name}"'
        idx = index_content.find(search_str)
        if idx != -1:
            a_end_idx = index_content.find('</a>', idx)
            if a_end_idx != -1:
                a_end_idx += 4
                chunk = index_content[a_end_idx:a_end_idx+500]
                escaped_day = re.escape(day_file_name)
                pattern = r'^(?:\s*<span class="ex-status" data-day="' + escaped_day + r'".*?</span>)?(?:\s*<a href="exercise/[^"]+" class="ex-archival-link" data-day="' + escaped_day + r'".*?</a>)?'
                
                match = re.match(pattern, chunk, flags=re.DOTALL)
                if match:
                    replace_len = len(match.group(0))
                    new_index_content = index_content[:a_end_idx] + index_content[a_end_idx + replace_len:]
                    
                    with open(index_path, "w", encoding="utf-8") as f:
                        f.write(new_index_content)
            
    # 2. Dọn dẹp day_X.html (nếu có nhúng trực tiếp)
    if os.path.exists(html_file_path):
        with open(html_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        start_marker = "<!-- EXERCISE START -->"
        end_marker = "<!-- EXERCISE END -->"
        if start_marker in content and end_marker in content:
            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker) + len(end_marker)
            # Nếu dư khoảng trắng, cắt bớt 1 dòng nếu có (đơn giản là replace)
            content = content[:start_idx].rstrip() + "\n" + content[end_idx:].lstrip("\n")
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
    # 3. Xóa file bài tập lưu trữ (nếu có)
    archival_path = os.path.join(target_dir, "exercise", archival_file_name)
    if os.path.exists(archival_path):
        try:
            os.remove(archival_path)
        except:
            pass
            
    return True
