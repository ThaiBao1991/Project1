"""
Novel Indexer - Module quét và quản lý thư viện tiểu thuyết dịch bằng AI.
Tự động lập danh mục chi tiết, thống kê số chương, từ điển thuật ngữ,
và lưu vào file ai_translated_novels.json để phục vụ tra cứu nhanh.
"""

import os
import sys
import re
import json
import datetime
from typing import List, Dict, Any, Optional

KNOWN_BOOK_MAPPINGS = {
    "26390": {
        "title_zh": "我的诡异人生",
        "title_vi": "Cuộc Đời Quỷ Dị Của Tôi (Ngã Đích Quỷ Dị Nhân Sinh)",
        "author": "白骨定兆"
    },
    "40175": {
        "title_zh": "我在尊魂幡里当主魂",
        "title_vi": "Tôi Là Linh Hồn Chính Trong Biểu Ngữ Zunhun",
        "author": "光头大战保龄球"
    }
}


def parse_novel_titles(folder_name: str, parent_dir: str, dich_dir: str) -> Dict[str, str]:
    """Phân tích tên truyện tiếng Trung và tiếng Việt từ tên thư mục hoặc nội dung file."""
    title_zh = ""
    title_vi = ""

    # 1. Kiểm tra pattern dạng: China-TênTrung-(TênViệt) hoặc China-TênTrung-(TênViệt)_tach
    m = re.match(r'^(?:China-)?([^\(\)]+?)(?:-\(([^\(\)]+)\))?(?:_tach)?$', folder_name)
    if m:
        part1 = (m.group(1) or '').strip()
        part2 = (m.group(2) or '').strip()

        # Kiểm tra part1 có chứa chữ Hán
        if re.search(r'[\u4e00-\u9fff]', part1):
            title_zh = part1
            title_vi = part2 or part1
        else:
            title_vi = part1 or part2

    # 2. Xử lý trường hợp thư mục có mã số như China-26390 hoặc 26390
    m_num = re.search(r'(\d{4,6})', folder_name)
    if m_num:
        book_id = m_num.group(1)
        if book_id in KNOWN_BOOK_MAPPINGS:
            info = KNOWN_BOOK_MAPPINGS[book_id]
            title_zh = info["title_zh"]
            title_vi = info["title_vi"]

    # 3. Xử lý trường hợp "(Bốn Vạn Năm Tu Luyện_tach" hoặc "修真四万年"
    if "bốn vạn năm tu luyện" in folder_name.lower() or "tu chân tứ vạn niên" in folder_name.lower():
        title_zh = "修真四万年"
        title_vi = "Bốn Vạn Năm Tu Luyện (Tu Chân Tứ Vạn Niên)"
    elif "trận vấn trường sinh" in folder_name.lower() or "hỏi về tuổi thọ" in folder_name.lower():
        title_zh = "阵问长生"
        title_vi = "Trận Vấn Trường Sinh (Hỏi Về Tuổi Thọ)"

    # Fallback nếu chưa có title_vi
    if not title_vi:
        title_vi = folder_name.replace("China-", "").replace("_tach", "").strip()

    return {
        "title_zh": title_zh,
        "title_vi": title_vi
    }


def find_source_resume(parent_dir: str, base_dir: str) -> Dict[str, Any]:
    """Tìm file Resume JSON để trích xuất source URL và host gốc."""
    result = {"source_host": "", "source_url": "", "story_title": ""}
    folder_name = os.path.basename(parent_dir)

    # Thử tìm file _Resume.json tương ứng
    candidates = [
        os.path.join(parent_dir, f"{folder_name}_Resume.json"),
        os.path.join(base_dir, f"{folder_name}_Resume.json"),
        os.path.join(base_dir, f"{folder_name.replace('_tach', '')}_Resume.json"),
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    result["story_title"] = data.get("story_title", "")
                    links = data.get("all_links", [])
                    if links and isinstance(links, list):
                        first_link = str(links[0])
                        result["source_url"] = first_link
                        m_host = re.search(r'https?://([^/]+)', first_link)
                        if m_host:
                            result["source_host"] = m_host.group(1)
                    break
            except Exception:
                pass

    if not result["source_host"] and "69shuba" in str(result.get("source_url", "")):
        result["source_host"] = "69shuba.com"
    elif not result["source_host"]:
        result["source_host"] = "69shuba.com"  # Nguồn mặc định của các truyện China

    return result


def find_merged_files(parent_dir: str, dich_dir: str, base_dir: str) -> Dict[str, Optional[str]]:
    """Tìm file gộp HTML và file ebook PRC tương ứng."""
    folder_name = os.path.basename(parent_dir).lower()
    merged_html = None
    merged_prc = None

    search_dirs = [
        parent_dir,
        dich_dir,
        os.path.join(base_dir, "prc"),
        base_dir
    ]

    for s_dir in search_dirs:
        if not os.path.exists(s_dir):
            continue
        try:
            for f in os.listdir(s_dir):
                f_lower = f.lower()
                if f_lower.endswith("_dich.html") and (folder_name in f_lower or folder_name.replace("_tach", "") in f_lower):
                    if not merged_html:
                        merged_html = os.path.abspath(os.path.join(s_dir, f))
                if f_lower.endswith("_dich.prc") and (folder_name in f_lower or folder_name.replace("_tach", "") in f_lower):
                    if not merged_prc:
                        merged_prc = os.path.abspath(os.path.join(s_dir, f))
        except Exception:
            pass

    return {
        "merged_html": merged_html,
        "merged_prc": merged_prc
    }


def scan_ai_translated_novels(base_dir: str = r"D:\Tai Ebook\html") -> Dict[str, Any]:
    """Quét toàn bộ thư mục và tạo danh mục các truyện đã dịch bằng AI."""
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"Thư mục không tồn tại: {base_dir}")

    novels = []
    seen_dich_dirs = set()

    for root, dirs, files in os.walk(base_dir):
        # Bỏ qua thư mục prc
        if os.path.basename(root).lower() == "prc":
            continue

        if os.path.basename(root).lower() == "dich":
            dich_path = os.path.abspath(root)
            if dich_path in seen_dich_dirs:
                continue
            seen_dich_dirs.add(dich_path)

            parent_dir = os.path.abspath(os.path.dirname(dich_path))
            folder_name = os.path.basename(parent_dir)

            # Đếm số chương đã dịch (file html trong dich/)
            html_chaps = [f for f in files if (f.endswith(".html") or f.endswith(".htm")) and not f.endswith("_Dich.html")]
            translated_count = len(html_chaps)
            if translated_count == 0:
                continue

            # Đếm số chương nguồn trong parent_dir
            src_files = os.listdir(parent_dir)
            src_chaps = [f for f in src_files if (f.endswith(".html") or f.endswith(".htm")) and not f.endswith("_Dich.html")]
            source_count = len(src_chaps) or translated_count

            # Phân tích tiêu đề
            titles = parse_novel_titles(folder_name, parent_dir, dich_path)

            # Kiểm tra từ điển glossary
            glossary_file = os.path.join(dich_path, "_glossary.json")
            glossary_count = 0
            if os.path.exists(glossary_file):
                try:
                    with open(glossary_file, "r", encoding="utf-8") as fp:
                        gdata = json.load(fp)
                        if isinstance(gdata, dict):
                            glossary_count = sum(len(v) for v in gdata.values() if isinstance(v, dict))
                except Exception:
                    pass

            # Tìm file gộp
            merged = find_merged_files(parent_dir, dich_path, base_dir)

            # Tìm thông tin nguồn
            source_info = find_source_resume(parent_dir, base_dir)

            # Thời gian cập nhật gần nhất
            mtime = os.path.getmtime(dich_path)
            last_updated_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

            # Trạng thái dịch
            if translated_count >= source_count or (source_count > 0 and translated_count >= source_count - 2):
                status = "Hoàn thành"
            else:
                pct = round((translated_count / source_count) * 100, 1) if source_count else 0
                status = f"Đang dịch ({pct}%)"

            # Tạo slug id
            slug = re.sub(r'[^a-zA-Z0-9]+', '-', titles["title_vi"].lower()).strip('-')

            novel_item = {
                "id": slug or f"novel-{len(novels) + 1}",
                "title_vi": titles["title_vi"],
                "title_zh": titles["title_zh"],
                "source_host": source_info["source_host"],
                "source_url": source_info["source_url"],
                "folder_path": parent_dir,
                "dich_path": dich_path,
                "total_source_chapters": source_count,
                "translated_chapters": translated_count,
                "status": status,
                "glossary_count": glossary_count,
                "has_merged_html": bool(merged["merged_html"]),
                "merged_html_path": merged["merged_html"] or "",
                "has_prc": bool(merged["merged_prc"]),
                "merged_prc_path": merged["merged_prc"] or "",
                "last_updated": last_updated_str,
                "last_updated_ts": mtime
            }
            novels.append(novel_item)

    # Sắp xếp theo thời gian cập nhật mới nhất lên đầu
    novels.sort(key=lambda x: x["last_updated_ts"], reverse=True)

    # Bỏ trường sort tạm trước khi lưu
    for n in novels:
        del n["last_updated_ts"]

    return {
        "title": "Danh Mục Quản Lý Tiểu Thuyết Dịch AI",
        "description": "Quản lý và tra cứu trạng thái toàn bộ các bộ truyện được dịch bằng AI trong D:\\Tai Ebook\\html.",
        "last_scanned": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "base_directory": base_dir,
        "total_novels": len(novels),
        "total_translated_chapters": sum(n["translated_chapters"] for n in novels),
        "novels": novels
    }


def save_novel_index(output_file: str = r"D:\Tai Ebook\html\ai_translated_novels.json",
                     base_dir: str = r"D:\Tai Ebook\html") -> Dict[str, Any]:
    """Quét và ghi danh mục ra file JSON."""
    data = scan_ai_translated_novels(base_dir)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    return data


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    out_path = r"D:\Tai Ebook\html\ai_translated_novels.json"
    print(f"🚀 Đang quét các truyện dịch AI tại D:\\Tai Ebook\\html...")
    catalog = save_novel_index(out_path)
    print(f"✅ Đã lập chỉ mục thành công {catalog['total_novels']} bộ truyện! (Tổng cộng {catalog['total_translated_chapters']:,} chương đã dịch)")
    print(f"💾 File JSON lưu tại: {out_path}\n")
    print(f"{'#':<3} | {'Tên Tiếng Việt':<42} | {'Tên Trung':<18} | {'Đã dịch':<12} | {'Trạng thái'}")
    print("-" * 100)
    for idx, n in enumerate(catalog["novels"], start=1):
        chaps_str = f"{n['translated_chapters']}/{n['total_source_chapters']}"
        print(f"{idx:<3} | {n['title_vi'][:40]:<42} | {n['title_zh'][:16]:<18} | {chaps_str:<12} | {n['status']}")
