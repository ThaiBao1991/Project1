import os
import re

def expand_roadmap(roadmap_path, doc_dir, output_path, pages_per_day=10, log_callback=None):
    """
    Đọc roadmap gốc, với mỗi Day có PDF:
    - Đếm tổng số trang của PDF đó
    - Nếu PDF > pages_per_day trang, tách ra thành nhiều sub-Day
    - Mỗi sub-Day có metadata <!-- pages: start-end -->
    Ghi kết quả ra output_path (file .md mới)
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    try:
        import fitz
    except ImportError:
        log("❌ Lỗi: Cần cài PyMuPDF (fitz) để đếm trang PDF.")
        return False

    log(f"📖 Đang đọc roadmap gốc: {os.path.basename(roadmap_path)} ...")
    with open(roadmap_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Tách các block Day
    parts = re.split(r'\n(## Day \d+.*?)\n', "\n" + content)
    
    # Phần header trước Day đầu tiên
    header = parts[0].strip() + "\n\n" if parts[0].strip() else ""
    
    output_blocks = []
    total_days_new = 0
    
    for i in range(1, len(parts), 2):
        day_title = parts[i].strip()     # e.g. "## Day 5 — Tên"
        day_content = parts[i+1]          # Nội dung bên trong

        # Tìm tên file PDF
        pdf_filename = None
        url_match = re.search(r'\(http.*?/([^/\s\)]+\.pdf)\)', day_content, re.IGNORECASE)
        if url_match:
            pdf_filename = url_match.group(1)

        total_pages = 0
        if pdf_filename:
            pdf_path = find_file(doc_dir, pdf_filename)
            if pdf_path:
                try:
                    doc = fitz.open(pdf_path)
                    total_pages = len(doc)
                    doc.close()
                except Exception as e:
                    log(f"⚠️ Không đọc được trang PDF '{pdf_filename}': {e}")

        if total_pages <= pages_per_day or total_pages == 0:
            # Không cần tách — giữ nguyên, thêm metadata trang nếu biết
            if total_pages > 0:
                block = f"{day_title}\n<!-- pages: 1-{total_pages} -->\n{day_content}"
            else:
                block = f"{day_title}\n{day_content}"
            output_blocks.append(block)
            total_days_new += 1
        else:
            # Tách thành nhiều sub-Day
            num_parts = (total_pages + pages_per_day - 1) // pages_per_day
            suffix_labels = [''] + [chr(ord('b') + j) for j in range(num_parts - 1)]
            
            # Lấy số Day gốc và tên
            day_num_match = re.match(r'## (Day \d+)(.*)', day_title)
            if day_num_match:
                day_num = day_num_match.group(1)   # "Day 5"
                day_rest = day_num_match.group(2)  # " — Tên Day"
            else:
                day_num = day_title.replace("## ", "")
                day_rest = ""

            for part_idx in range(num_parts):
                start_page = part_idx * pages_per_day + 1
                end_page = min((part_idx + 1) * pages_per_day, total_pages)
                suffix = suffix_labels[part_idx]
                
                sub_title = f"## {day_num}{suffix}{day_rest} (Phần {part_idx+1}/{num_parts} - Trang {start_page}-{end_page})"
                block = f"{sub_title}\n<!-- pages: {start_page}-{end_page} -->\n{day_content}"
                output_blocks.append(block)
                total_days_new += 1

    # Ghi file mới
    final_content = header + "\n".join(output_blocks)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    log(f"\n✅ Đã tạo roadmap mở rộng: {os.path.basename(output_path)}")
    log(f"   Roadmap gốc: {(len(parts)-1)//2} Days")
    log(f"   Roadmap mới: {total_days_new} Days (sau khi chia nhỏ {pages_per_day} trang/Day)")
    return True

def find_file(root_dir, filename):
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if f.lower() == filename.lower():
                return os.path.join(dirpath, f)
    return None
