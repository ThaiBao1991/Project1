"""
download_intramart_pdfs.py
--------------------------
Tải tất cả file PDF intra-mart Ver.7.2 được liệt kê trong roadmap_intramart_72.md.
Dùng 10 luồng song song, bỏ qua file đã tồn tại.

Cách chạy:
    python download_intramart_pdfs.py

Thư mục lưu mặc định: D:\\Tai truyen\\Data
"""

import os
import re
import sys
import time
import requests
import concurrent.futures
from datetime import datetime

# ── Cấu hình ──────────────────────────────────────────────────────────────────
ROADMAP_FILE = os.path.join(os.path.dirname(__file__), "roadmap_intramart_72.md")
OUTPUT_DIR   = r"D:\Tai truyen\Data"
MAX_WORKERS  = 10          # Số luồng tải song song
TIMEOUT_SEC  = 60          # Timeout mỗi file (giây)
CHUNK_SIZE   = 8192        # Kích thước buffer tải (bytes)

# ── Màu ANSI cho terminal ─────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ts():
    return datetime.now().strftime("[%H:%M:%S]")

def extract_pdf_urls(roadmap_path):
    """Trích xuất tất cả URL PDF duy nhất từ file roadmap."""
    try:
        with open(roadmap_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"{RED}✗ Không tìm thấy file roadmap: {roadmap_path}{RESET}")
        sys.exit(1)

    # Tìm tất cả URL kết thúc bằng .pdf
    urls = re.findall(r'https?://[^\s\)\]"\']+\.pdf', content, re.IGNORECASE)
    # Loại bỏ trùng lặp, giữ thứ tự
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    return unique_urls

def download_one(args):
    """Tải 1 file PDF. Trả về (url, filename, status, size_kb, message)."""
    url, out_dir, idx, total = args
    filename = url.split("/")[-1]
    save_path = os.path.join(out_dir, filename)

    # Bỏ qua nếu file đã tồn tại và có kích thước > 0
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        size_kb = os.path.getsize(save_path) / 1024
        return (url, filename, "skip", size_kb, "Đã tồn tại")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=TIMEOUT_SEC, stream=True)
        resp.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

        size_kb = os.path.getsize(save_path) / 1024
        return (url, filename, "ok", size_kb, "")

    except requests.exceptions.HTTPError as e:
        return (url, filename, "error", 0, f"HTTP {resp.status_code}")
    except requests.exceptions.ConnectionError:
        return (url, filename, "error", 0, "Lỗi kết nối")
    except requests.exceptions.Timeout:
        return (url, filename, "error", 0, f"Timeout ({TIMEOUT_SEC}s)")
    except Exception as e:
        return (url, filename, "error", 0, str(e)[:80])

def main():
    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"  Intra-mart v7.2 PDF Downloader")
    print(f"{'='*60}{RESET}\n")

    # Kiểm tra thư mục đích
    if not os.path.exists(OUTPUT_DIR):
        print(f"{YELLOW}⚠ Thư mục '{OUTPUT_DIR}' chưa tồn tại. Đang tạo...{RESET}")
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"{GREEN}✓ Đã tạo thư mục: {OUTPUT_DIR}{RESET}")
        except Exception as e:
            print(f"{RED}✗ Không thể tạo thư mục: {e}{RESET}")
            sys.exit(1)

    # Trích xuất URL từ roadmap
    print(f"{ts()} Đang đọc roadmap: {ROADMAP_FILE}")
    urls = extract_pdf_urls(ROADMAP_FILE)
    print(f"{ts()} {GREEN}✓ Tìm thấy {len(urls)} URL PDF duy nhất{RESET}")
    print(f"{ts()} Thư mục lưu   : {OUTPUT_DIR}")
    print(f"{ts()} Số luồng      : {MAX_WORKERS}")
    print()

    if not urls:
        print(f"{RED}✗ Không tìm thấy URL PDF nào trong roadmap!{RESET}")
        sys.exit(1)

    # Chuẩn bị args
    args_list = [(url, OUTPUT_DIR, idx+1, len(urls)) for idx, url in enumerate(urls)]

    # Tải song song
    results = {"ok": 0, "skip": 0, "error": 0, "total_kb": 0}
    errors_list = []

    print(f"{BOLD}Bắt đầu tải...{RESET}")
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_one, args): args for args in args_list}
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            url, filename, status, size_kb, msg = future.result()

            if status == "ok":
                results["ok"] += 1
                results["total_kb"] += size_kb
                print(f"  {GREEN}✓{RESET} [{completed:>3}/{len(urls)}] {filename:<55} {size_kb:>7.1f} KB")
            elif status == "skip":
                results["skip"] += 1
                results["total_kb"] += size_kb
                print(f"  {YELLOW}↷{RESET} [{completed:>3}/{len(urls)}] {filename:<55} {size_kb:>7.1f} KB  [bỏ qua - đã có]")
            else:
                results["error"] += 1
                errors_list.append((filename, msg))
                print(f"  {RED}✗{RESET} [{completed:>3}/{len(urls)}] {filename:<55}           {RED}{msg}{RESET}")

    elapsed = time.time() - start_time

    # Tóm tắt
    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"  Kết quả")
    print(f"{'='*60}{RESET}")
    print(f"  {GREEN}✓ Tải thành công : {results['ok']}{RESET}")
    print(f"  {YELLOW}↷ Đã tồn tại    : {results['skip']}{RESET}")
    print(f"  {RED}✗ Lỗi           : {results['error']}{RESET}")
    print(f"  Tổng dung lượng : {results['total_kb']/1024:.2f} MB")
    print(f"  Thời gian       : {elapsed:.1f}s")
    print(f"  Thư mục lưu     : {OUTPUT_DIR}")

    if errors_list:
        print(f"\n{BOLD}{RED}Các file lỗi:{RESET}")
        for fname, emsg in errors_list:
            print(f"    - {fname}: {emsg}")

    print(f"\n{GREEN}✓ Hoàn tất!{RESET}\n")

if __name__ == "__main__":
    main()
