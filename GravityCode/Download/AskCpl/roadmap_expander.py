import os
import re

_DAY_HEADING = re.compile(r'\n## (Day \d+[a-z]?\s+—\s+[^\n]+)\n')
_SOURCES_META = re.compile(r'<!--\s*sources:\s*([^>]+)\s*-->', re.IGNORECASE)
_URL_PDF = re.compile(r'\(http.*?/([^/\s\)]+\.pdf)\)', re.IGNORECASE)
_PAGES_META = re.compile(r'<!--\s*pages:\s*(\d+)-(\d+)\s*-->', re.IGNORECASE)
_PROMPT_SPLIT = re.compile(r'\*\*Prompt:\*\*(.*?)(?=\*\*Bài tập:\*\*|\*\*Tags:\*\*|\Z)', re.DOTALL)


def _split_prompt(prompt_text, words_per_day):
    """Chia prompt thành các đoạn theo từ, mỗi đoạn là 1 sub-Day."""
    words = prompt_text.split()
    if len(words) <= words_per_day:
        return [prompt_text]
    chunks = []
    for i in range(0, len(words), words_per_day):
        chunks.append(" ".join(words[i:i + words_per_day]))
    return chunks


def _pdf_filename(day_content):
    """Tìm tên file PDF trong nội dung Day: ưu tiên URL, rồi metadata sources."""
    url_match = _URL_PDF.search(day_content)
    if url_match:
        return url_match.group(1)
    source_match = _SOURCES_META.search(day_content)
    if source_match:
        candidates = [part.strip() for part in source_match.group(1).split(',')]
        return next((part for part in candidates if part.lower().endswith('.pdf')), None)
    return None


def _restructure(day_title, day_content, page_start, page_end, pdf_name,
                 prompt_override, part_idx, num_parts):
    """Dựng lại 1 sub-Day: title chuẩn, metadata trang, prompt đã chỉnh."""
    # Bỏ metadata sources/pages cũ để không sót lẫn trong content mới
    content = _SOURCES_META.sub('', day_content)
    content = _PAGES_META.sub('', content)

    sub_title = f"## {day_title} (Phần {part_idx}/{num_parts} - Trang {page_start}-{page_end})"
    lines = []
    for line in content.splitlines():
        if line.startswith('**Prompt:**'):
            lines.append(line)
            if pdf_name and prompt_override:
                lines.append(prompt_override)
            continue
        lines.append(line)
    block = "\n".join(lines)
    block = f"{sub_title}\n<!-- sources: {pdf_name} -->\n<!-- pages: {page_start}-{page_end} -->\n{block}"
    return block


def _restructure_text(day_title, day_content, prompt_start, prompt_end,
                      raw_prompt, intro, part_idx, num_parts):
    """Text-only: dựng sub-Day từ phần Prompt gốc đã chia, giữ nguyên Bài tập/Tags."""
    pre = day_content[:prompt_start]
    post = day_content[prompt_end:]
    body = intro + raw_prompt.strip() + "\n"
    sub_title = f"## {day_title} (Phần {part_idx}/{num_parts})"
    return f"{sub_title}\n{pre}**Prompt:**\n{body}{post.strip()}"


def expand_roadmap(roadmap_path, doc_dir, output_path, pages_per_day=10,
                   words_per_day=400, log_callback=None):
    """
    Mở rộng roadmap: chia Day có PDF theo số trang, Day text-only theo từ.

    - PDF: tách theo pages_per_day, mỗi sub-Day gắn <!-- sources/pages --> và
      prompt tự chỉnh "chỉ dùng trang X-Y" để AI tập trung đúng phần.
    - Text-only: tách Prompt theo words_per_day (mặc định 400 từ), mỗi phần
      thành 1 sub-Day, giữ nguyên cấu trúc **Prompt:**/**Bài tập:**/**Tags:**.
    - Cú pháp `## Day N...` giữ nguyên để auto_ai_worker parse được.
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

    # Tách block Day theo đúng chuẩn parser của auto_ai_worker
    parts = _DAY_HEADING.split("\n" + content)
    header = parts[0].strip() + "\n\n" if parts and parts[0].strip() else ""
    if len(parts) < 2:
        log("⚠ Không tìm thấy Day nào đúng định dạng '## Day N — ...'.")
        return False

    output_blocks = []
    total_days_new = 0
    split_count = 0

    for i in range(1, len(parts), 2):
        day_title = parts[i].strip()
        day_content = parts[i + 1]

        pdf_name = _pdf_filename(day_content)
        pdf_path = None
        total_pages = 0
        if pdf_name:
            pdf_path = find_file(doc_dir, pdf_name)
            if pdf_path:
                try:
                    doc = fitz.open(pdf_path)
                    total_pages = len(doc)
                    doc.close()
                except Exception as e:
                    log(f"⚠ Không đọc được PDF '{pdf_name}': {e}")
            else:
                log(f"⚠ KHÔNG tìm thấy file '{pdf_name}' trong thư mục Docs.")

        if pdf_path and total_pages > pages_per_day:
            # ── Chế độ PDF: chia theo trang ──
            num_parts = (total_pages + pages_per_day - 1) // pages_per_day
            for part_idx in range(1, num_parts + 1):
                start_page = (part_idx - 1) * pages_per_day + 1
                end_page = min(part_idx * pages_per_day, total_pages)
                if part_idx == 1:
                    prompt_override = (f"[Nguồn cục bộ: dùng trang {start_page}-{end_page} / {total_pages} "
                                       f"của '{pdf_name}'. Chỉ dùng phần này, không tóm tắt toàn bộ tài liệu.]")
                else:
                    prompt_override = (f"[Tiếp nối Day trước — dùng trang {start_page}-{end_page} / {total_pages} "
                                       f"của '{pdf_name}'. TUYỆT ĐỐI không lặp lại nội dung các trang trước.]")
                block = _restructure(day_title, day_content, start_page, end_page, pdf_name,
                                     prompt_override, part_idx, num_parts)
                output_blocks.append(block)
                total_days_new += 1
            split_count += 1
            log(f"✂️  Day '{day_title[:40]}...': {total_pages} trang → {num_parts} sub-Day "
                f"(mỗi {pages_per_day} trang).")
            continue

        if pdf_name and total_pages > 0:
            # PDF nhỏ hơn ngưỡng: giữ nguyên, gắn metadata trang 1-N
            block = _restructure(day_title, day_content, 1, total_pages, pdf_name,
                                 None, 1, 1)
            output_blocks.append(block)
            total_days_new += 1
            continue

        # ── Text-only: chia Prompt theo từ ──
        prompt_m = _PROMPT_SPLIT.search(day_content)
        prompt_len = len(prompt_m.group(1).split()) if prompt_m else 0
        if prompt_len > words_per_day:
            chunks = _split_prompt(prompt_m.group(1).strip(), words_per_day)
            num_parts = len(chunks)
            for part_idx, chunk in enumerate(chunks, start=1):
                if part_idx == 1:
                    intro = (f"[Nội dung được chia thành {num_parts} phần. Đây là PHẦN {part_idx}: "
                             f"hãy dạy đúng trọng tâm của đoạn này, không dạy lan sang phần sau.]\n\n")
                else:
                    intro = (f"[PHẦN {part_idx}/{num_parts} — TIẾP NỐI: chỉ dạy nội dung đoạn này, "
                             f"KHÔNG lặp lại phần đã dạy trước đó.]\n\n")
                block = _restructure_text(day_title, day_content, prompt_m.start(), prompt_m.end(),
                                          chunk, intro, part_idx, num_parts)
                output_blocks.append(block)
                total_days_new += 1
            split_count += 1
            log(f"✂️  Day '{day_title[:40]}...': prompt {prompt_len} từ → {num_parts} sub-Day "
                f"(mỗi {words_per_day} từ).")
            continue

        # Không cần tách
        output_blocks.append(f"## {day_title}\n{day_content}")
        total_days_new += 1

    final_content = header + "\n".join(output_blocks)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)

    log(f"\n✅ Đã tạo roadmap mở rộng: {os.path.basename(output_path)}")
    log(f"   Roadmap gốc: {(len(parts) - 1) // 2} Days")
    log(f"   Roadmap mới: {total_days_new} Days (chia nhỏ {split_count} Day)")
    return True


def find_file(root_dir, filename):
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if f.lower() == filename.lower():
                return os.path.join(dirpath, f)
    return None