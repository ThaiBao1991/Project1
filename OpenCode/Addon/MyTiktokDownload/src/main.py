#!/usr/bin/env python3
"""
TikTok Downloader - Main Entry Point
Modes: download, view, export, cookies, settings, stats, full-sync
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from downloader import HybridDownloader, TikTokDownloader, VideoIndex, VideoInfo, DownloadResult, get_chrome_cookies, save_cookies_to_file
from ext_sync import ExtensionSync, get_ext_sync


SETTINGS_FILE = Path(__file__).parent / "settings.json"
DB_FILE = Path(__file__).parent / "downloads" / "video_index.db"


def analyze_error(error_msg: str, url: str):
    """Phân tích lỗi và đưa ra nguyên nhân + giải pháp"""
    print(f"\n{'='*60}")
    print(f"🔍 PHÂN TÍCH LỖI CHI TIẾT")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Lỗi: {error_msg}")
    print(f"{'='*60}")
    
    error_lower = error_msg.lower()
    
    if "sign in to confirm age" in error_lower or "age restricted" in error_lower:
        print("🔞 NGUYÊN NHÂN: Video 18+ (Age Restricted)")
        print("💡 GIẢI PHÁP:")
        print("   1. Cookie phải từ tài khoản đã verify 18+")
        print("   2. Chạy: python sync_and_download.py --mode cookies")
        print("   3. Đảm bảo đăng nhập TikTok trên Chrome bằng tài khoản 18+")
        
    elif "video unavailable" in error_lower or "video not found" in error_lower:
        print("🗑️ NGUYÊN NHÂN: Video không tồn tại / đã bị xóa / private")
        print("💡 GIẢI PHÁP: Video này không thể tải được (đã bị xóa hoặc thiết lập riêng tư)")
        
    elif "sign in" in error_lower or "login required" in error_lower or "unauthorized" in error_lower:
        print("🔐 NGUYÊN NHÂN: Cần đăng nhập / Cookie hết hạn / Sai cookie")
        print("💡 GIẢI PHÁP:")
        print("   1. Đăng nhập TikTok trên Chrome")
        print("   2. Chạy: python sync_and_download.py --mode cookies")
        print("   3. Kiểm tra settings.json có cookie không")
        
    elif "rate limit" in error_lower or "too many requests" in error_lower or "429" in error_lower:
        print("⏱️ NGUYÊN NHÂN: Rate Limit (TikTok chặn IP/requests quá nhiều)")
        print("💡 GIẢI PHÁP:")
        print("   1. Giảm rate_limit trong settings.json: \"500K\" hoặc \"200K\"")
        print("   3. Bật VPN / đổi IP")
        print("   4. Chờ 10-15 phút rồi thử lại")
        
    elif "403" in error_lower or "forbidden" in error_lower:
        print("🚫 NGUYÊN NHÂN: 403 Forbidden - Không có quyền truy cập")
        print("💡 GIẢI PHÁP:")
        print("   1. Video có thể là private / region-locked / 18+")
        print("   2. Thử dùng VPN (VN/US) + cookie tài khoản có quyền xem")
        
    elif "mar695" in error_lower or "unstable" in error_lower:
        print("🔧 NGUYÊN NHÂN: Lỗi TikTok Server (Mar695 / Unstable)")
        print("💡 GIẢI PHÁP: Downloader đã có fallback yt-dlp, thử lại sau vài phút")
        
    elif "private" in error_lower or "friends only" in error_lower:
        print("🔒 NGUYÊN NHÂN: Video riêng tư / Chỉ bạn bè")
        print("💡 GIẢI PHÁP: Cần cookie từ tài khoản trong danh sách bạn bè của tác giả")
        
    elif "region" in error_lower or "geo" in error_lower:
        print("🌍 NGUYÊN NHÂN: Region Lock (Video chỉ cho phép một số quốc gia)")
        print("💡 GIẢI PHÁP: Bật VPN region VN/US/JP tùy video")
        
    elif "network" in error_lower or "timeout" in error_lower or "connection" in error_lower:
        print("🌐 NGUYÊN NHÂN: Lỗi mạng / Timeout")
        print("💡 GIẢI PHÁP: Kiểm tra internet, thử lại, hoặc tăng timeout")
        
    else:
        print("❓ NGUYÊN NHÂN: Lỗi chưa phân loại được")
        print("💡 GIẢI PHÁP THỬ:")
        print("   1. Cập nhật yt-dlp: pip install -U yt-dlp")
        print("   2. Thử lại sau 5-10 phút")
        print("   3. Kiểm tra log chi tiết ở trên")
    
    print(f"{'='*60}")
    print(f"💡 GỢI Ý: Chạy với --stop-on-error để dừng tại video này và debug")
    print(f"{'='*60}\n")


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "output_dir": str(Path(__file__).parent / "downloads"),
        "rate_limit": "1M",
        "retries": 3,
        "skip_existing": True,
        "subfolder_per_author": True,
        "writethumbnail": True,
        "writeinfojson": True,
    }


def save_settings(s: dict):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(s, f, indent=2, ensure_ascii=False)


def safe_print(text: str):
    """Print with UTF-8 support on Windows"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: replace emojis with ASCII
        text = text.encode('ascii', 'replace').decode('ascii')
        print(text)


def print_header(title: str):
    safe_print(f"\n{'='*60}")
    safe_print(f"  {title}")
    safe_print(f"{'='*60}\n")


def get_downloader() -> HybridDownloader:
    settings = load_settings()
    cookies = settings.get("cookies", "")
    return HybridDownloader(
        output_dir=settings.get("output_dir", "downloads"),
        db_path=str(Path(settings.get("output_dir", "downloads")) / "video_index.db"),
        cookies=cookies,
        rate_limit=settings.get("rate_limit", "1M"),
        max_retries=settings.get("retries", 3),
        skip_existing=settings.get("skip_existing", True),
    )


def get_index() -> VideoIndex:
    settings = load_settings()
    return VideoIndex(str(Path(settings.get("output_dir", "downloads")) / "video_index.db"))


# ===== MODE: DOWNLOAD =====
def mode_download(args):
    """Download video(s) from URLs"""
    print_header("📥 DOWNLOAD VIDEOS")
    
    urls = []
    if args.urls:
        urls = args.urls
    else:
        # Interactive input
        print("Nhập URLs TikTok (mỗi dòng 1 link, dòng trống để kết thúc):")
        while True:
            line = input("> ").strip()
            if not line:
                break
            if 'tiktok.com' in line:
                urls.append(line)
            else:
                print("  ⚠️ Không phải link TikTok hợp lệ")
    
    if not urls:
        print("❌ Không có URL nào")
        return
        
    stop_on_error = getattr(args, 'stop_on_error', False)
    print(f"\n📋 Sẽ tải {len(urls)} video... {'(Dừng khi lỗi)' if stop_on_error else '(Tiếp tục nếu lỗi)'}")
    
    downloader = get_downloader()
    
    def progress_cb(i, total, url, msg):
        print(f"\r[{i+1}/{total}] {msg[:80]}", end="", flush=True)
    
    def complete_cb(result):
        if result.success:
            status = "✅" if result.video.status != "skipped" else "⏭️"
            print(f"\n{status} {result.video.title[:50]} - {result.video.file_size/1024/1024:.1f}MB")
        else:
            print(f"\n❌ THẤT BẠI: {result.error}")
            analyze_error(result.error, result.video.url)
    
    # Patch batch_download to support stop_on_error
    results = batch_download_with_stop(downloader, urls, progress_cb, complete_cb, stop_on_error)
    
    success = sum(1 for r in results if r.success)
    skipped = sum(1 for r in results if r.success and r.video.status == "skipped")
    failed = len(results) - success
    
    print(f"\n{'='*60}")
    print(f"✅ Thành công: {success}  ⏭️ Bỏ qua (đã có): {skipped}  ❌ Thất bại: {failed}")
    print(f"{'='*60}")


def batch_download_with_stop(downloader, urls, progress_cb, complete_cb, stop_on_error):
    """Batch download with stop_on_error support"""
    results = []
    for i, url in enumerate(urls):
        if progress_cb:
            progress_cb(i, len(urls), url, "Extracting info...")
        
        video_info = downloader.extract_info(url)
        if not video_info:
            result = DownloadResult(False, 
                VideoInfo(id="", url=url, title="", author="", author_id="", 
                         duration=0, view_count=0, like_count=0, comment_count=0,
                         create_time=0, thumbnail=""),
                "Không thể trích xuất thông tin (cả API và yt-dlp)")
            results.append(result)
            if complete_cb:
                complete_cb(result)
            if stop_on_error:
                print(f"\n🛑 DỪNG TẠI VIDEO {i+1}/{len(urls)} (stop_on_error=True)")
                break
            continue
            
        video_info.category = "manual"
        
        if progress_cb:
            progress_cb(i, len(urls), url, f"Downloading: {video_info.title[:50]}...")
        
        result = downloader.download_video(video_info, 
            lambda v, p, m: progress_cb(i, len(urls), url, f"{p:.1f}% - {m}") if progress_cb else None)
        results.append(result)
        
        if complete_cb:
            complete_cb(result)
        
        if not result.success and stop_on_error:
            print(f"\n🛑 DỪNG TẠI VIDEO {i+1}/{len(urls)} (stop_on_error=True)")
            break
    
    return results


# ===== MODE: VIEW =====
def mode_view(args):
    """Search and view downloaded videos"""
    print_header("🔍 VIEW / SEARCH VIDEOS")
    
    index = get_index()
    
    while True:
        print("\n--- Tìm kiếm video ---")
        query = input("Từ khóa (tên video/author, Enter để xem tất cả): ").strip()
        author = input("Tác giả (bỏ qua): ").strip() or None
        category = input("Category [manual/likes/favorites/all] (mặc định all): ").strip().lower()
        if category not in ('manual', 'likes', 'favorites', 'b', 'l'):
            category = None
        elif category in ('b', 'favorites'):
            category = 'b'
        elif category in ('l', 'likes'):
            category = 'l'
            
        status = input("Status [completed/failed/pending/all] (mặc định completed): ").strip().lower()
        if status not in ('completed', 'failed', 'pending'):
            status = 'completed'
            
        limit = input("Số lượng kết quả (mặc định 50): ").strip()
        limit = int(limit) if limit.isdigit() else 50
        
        print(f"\n🔍 Đang tìm...")
        results = index.search(query=query, author=author, category=category, status=status, limit=limit)
        
        if not results:
            print("❌ Không tìm thấy video nào")
        else:
            print(f"\n📋 Tìm thấy {len(results)} video:")
            print(f"{'#':<4} {'Video ID':<20} {'Title':<40} {'Author':<20} {'Size':<10} {'Date'}")
            print("-" * 120)
            for i, v in enumerate(results, 1):
                size = f"{v.file_size/1024/1024:.1f}MB" if v.file_size else "-"
                date = v.downloaded_at[:10] if v.downloaded_at else "-"
                print(f"{i:<4} {v.id:<20} {v.title[:38]:<40} {v.author[:18]:<20} {size:<10} {date}")
        
        cont = input("\nTiếp tục tìm kiếm? (y/n): ").strip().lower()
        if cont != 'y':
            break


# ===== MODE: EXPORT =====
def mode_export(args):
    """Export to CSV/JSON"""
    print_header("📤 EXPORT DATA")
    
    index = get_index()
    
    print("Chọn định dạng:")
    print("  1. CSV")
    print("  2. JSON (format myfaveTT)")
    fmt = input("Chọn [1/2]: ").strip()
    
    category = input("Category [manual/likes/favorites/all] (mặc định all): ").strip().lower()
    if category not in ('manual', 'likes', 'favorites', 'b', 'l'):
        category = None
    elif category in ('b', 'favorites'):
        category = 'b'
    elif category in ('l', 'likes'):
        category = 'l'
        
    status = input("Status [completed/failed/all] (mặc định completed): ").strip().lower()
    if status not in ('completed', 'failed'):
        status = 'completed'
    
    if fmt == '1':
        filepath = Path(load_settings().get("output_dir", "downloads")) / "export.csv"
        count = index.export_csv(str(filepath), category=category, status=status)
        print(f"\n✅ Đã export {count} video ra: {filepath}")
    else:
        filepath = Path(load_settings().get("output_dir", "downloads")) / "export_myfaveTT.json"
        count = index.export_json(str(filepath), category=category, status=status)
        print(f"\n✅ Đã export {count} video ra: {filepath} (format myfaveTT)")


# ===== MODE: COOKIES =====
def mode_cookies(args):
    """Auto-detect cookies from Chrome"""
    print_header("🔑 AUTO-DETECT TIKTOK COOKIES")
    
    print("🔍 Đang tìm cookie TikTok từ Chrome...")
    cookies = get_chrome_cookies("tiktok.com")
    
    if cookies:
        print(f"\n✅ Tìm thấy cookie ({len(cookies)} chars)")
        print(f"Preview: {cookies[:80]}...")
        
        # Save to settings
        settings = load_settings()
        settings["cookies"] = cookies
        save_settings(settings)
        print("✅ Đã lưu vào settings.json")
        
        # Also export Netscape format
        filepath = Path(__file__).parent / "cookies_tiktok.txt"
        save_cookies_to_file(cookies, str(filepath))
        print(f"✅ Đã export Netscape format: {filepath}")
    else:
        print("\n❌ Không tìm thấy cookie TikTok")
        print("💡 Hãy đăng nhập TikTok trên Chrome trước, sau đó chạy lại.")


# ===== MODE: SETTINGS =====
def mode_settings(args):
    """Manage settings"""
    print_header("⚙️ SETTINGS")
    
    settings = load_settings()
    
    print("Cài đặt hiện tại:")
    for k, v in settings.items():
        if k == "cookies":
            print(f"  {k}: {'***' if v else 'Not set'}")
        else:
            print(f"  {k}: {v}")
    
    print("\nThay đổi (Enter để giữ nguyên):")
    
    # Output dir
    new = input(f"Output dir [{settings.get('output_dir', 'downloads')}]: ").strip()
    if new: settings["output_dir"] = new
    
    # Rate limit
    print("Rate limit: No limit / 500K / 1M / 2M / 5M")
    new = input(f"Rate limit [{settings.get('rate_limit', '1M')}]: ").strip()
    if new: settings["rate_limit"] = new
    
    # Retries
    new = input(f"Max retries [{settings.get('retries', 3)}]: ").strip()
    if new and new.isdigit(): settings["retries"] = int(new)
    
    # Skip existing
    new = input(f"Skip existing videos? (y/n) [{'y' if settings.get('skip_existing') else 'n'}]: ").strip().lower()
    if new in ('y', 'yes'): settings["skip_existing"] = True
    elif new in ('n', 'no'): settings["skip_existing"] = False
    
    # Subfolder
    new = input(f"Subfolder per author? (y/n) [{'y' if settings.get('subfolder_per_author') else 'n'}]: ").strip().lower()
    if new in ('y', 'yes'): settings["subfolder_per_author"] = True
    elif new in ('n', 'no'): settings["subfolder_per_author"] = False
    
    save_settings(settings)
    print("\n✅ Đã lưu settings.json")


# ===== MODE: STATS =====
def mode_stats(args):
    """Show statistics"""
    print_header("📊 STATISTICS")
    
    index = get_index()
    stats = index.get_stats()
    
    print(f"  Tổng video trong index:    {stats['total']:,}")
    print(f"  ✅ Đã tải thành công:      {stats['completed']:,}")
    print(f"  ⏭️ Bỏ qua (đã có):         {stats.get('skipped', 0):,}")
    print(f"  ❌ Thất bại:               {stats['failed']:,}")
    print(f"  💾 Tổng dung lượng:        {stats['total_size']/1024/1024:.1f} MB")
    print(f"  👤 Số tác giả duy nhất:    {stats['unique_authors']:,}")
    print(f"  📂 Số category:            {stats['categories']:,}")
    
    # By category
    for cat in ['manual', 'b', 'l']:
        cat_name = {'manual': 'Manual URLs', 'b': 'Favorites (b)', 'l': 'Likes (l)'}.get(cat, cat)
        results = index.search(category=cat, status='completed', limit=1)
        total = index.search(category=cat, status='completed', limit=10000)
        print(f"  📁 {cat_name}:              {len(total):,} videos")


# ===== MODE: FULL SYNC =====
def mode_full_sync(args):
    """Fetch Likes/Favorites from TikTok API + Download"""
    print_header("🚀 FULL SYNC: FETCH LIKES/FAVORITES + DOWNLOAD")
    
    settings = load_settings()
    cookies = settings.get("cookies", "").strip()
    
    if not cookies:
        print("❌ Chưa có cookie TikTok!")
        print("💡 Chạy mode 4 (cookies) trước để lấy cookie từ Chrome")
        return
    
    downloader = get_downloader()
    
    max_items = args.max_items or 0
    if not args.max_items:
        max_items = input("Số lượng tối đa mỗi loại (0 = không giới hạn): ").strip()
        max_items = int(max_items) if max_items.isdigit() else 0
    
    print(f"\n🔄 Đang fetch Likes & Favorites từ TikTok API...")
    print(f"   (Max items mỗi loại: {'không giới hạn' if max_items == 0 else max_items})")
    
    likes, favorites = downloader.fetch_likes_favorites(cookies, max_items)
    
    print(f"\n📊 Kết quả fetch:")
    print(f"  ❤️ Likes:       {len(likes):,} video")
    print(f"  ⭐ Favorites:   {len(favorites):,} video")
    
    if not likes and not favorites:
        print("❌ Không fetch được video nào. Kiểm tra cookie.")
        return
    
    # Download
    print("\n📥 Bắt đầu tải...")
    
    all_results = []
    
    if likes:
        print(f"\n--- Tải {len(likes)} Likes ---")
        like_urls = [v.url for v in likes]
        def like_progress(i, total, url, msg):
            print(f"\r[Likes {i+1}/{total}] {msg[:80]}", end="", flush=True)
        results = downloader.batch_download(like_urls, progress_callback=like_progress, category='l')
        all_results.extend(results)
        success = sum(1 for r in results if r.success)
        print(f"\n✅ Likes: {success}/{len(likes)} thành công")
    
    if favorites:
        print(f"\n--- Tải {len(favorites)} Favorites ---")
        fav_urls = [v.url for v in favorites]
        def fav_progress(i, total, url, msg):
            print(f"\r[Fav {i+1}/{total}] {msg[:80]}", end="", flush=True)
        results = downloader.batch_download(fav_urls, progress_callback=fav_progress, category='b')
        all_results.extend(results)
        success = sum(1 for r in results if r.success)
        print(f"\n✅ Favorites: {success}/{len(favorites)} thành công")
    
    total_success = sum(1 for r in all_results if r.success)
    total_failed = len(all_results) - total_success
    print(f"\n{'='*60}")
    print(f"🎉 HOÀN THÀNH FULL SYNC")
    print(f"  ✅ Thành công: {total_success}")
    print(f"  ❌ Thất bại:   {total_failed}")
    print(f"{'='*60}")


# ===== MODE: SYNC TO EXTENSION =====
def mode_sync_to_ext(args):
    """Sync dữ liệu từ Python → Extension"""
    print_header("🔄 SYNC PYTHON → EXTENSION")
    
    settings = load_settings()
    ext_path = getattr(args, "ext_path", None) or settings.get("ext_data_path", r"D:\dlvideott\data\.appdata")
    ext_sync = get_ext_sync(ext_path)
    downloader = get_downloader()
    
    print("🔄 Đang sync video từ Python Downloader → Extension...")
    synced = ext_sync.sync_from_python_downloader(downloader)
    
    if synced > 0:
        print(f"✅ Đã sync {synced} video mới vào Extension")
        print("💡 Lần sau extension chạy sẽ không tải lại các video này")
    else:
        print("ℹ️ Không có video mới cần sync")


# ===== MODE: DOWNLOAD FAILED VIDEOS FROM EXTENSION =====
def mode_download_failed(args):
    """Tải các video bị lỗi từ Extension (dùng chung dữ liệu và xóa khỏi list lỗi khi xong)"""
    print_header("🚨 TẢI VIDEO LỖI TỪ EXTENSION (CHUNG DỮ LIỆU)")
    
    settings = load_settings()
    ext_path = getattr(args, "ext_path", None) or settings.get("ext_data_path", r"D:\dlvideott\data\.appdata")
    ext_sync = get_ext_sync(ext_path)
    downloader = get_downloader()
    
    custom_file = getattr(args, "failed_file", None)
    failed_queue = ext_sync.load_failed_queue(custom_file)
    
    if not failed_queue:
        safe_print("ℹ️ Không tìm thấy video nào trong danh sách lỗi (failed_videos.json).")
        safe_print(f"   Đường dẫn kiểm tra: {ext_sync.failed_json_path}")
        return
        
    safe_print(f"📋 Tìm thấy {len(failed_queue)} video bị lỗi cần tải:")
    for i, item in enumerate(failed_queue[:10]):
        err_code = item.get("errorCode", "ERR")
        vid_id = item.get("id", "")
        author = item.get("author", "")
        cat = item.get("category", "b")
        safe_print(f"  {i+1}. [{err_code}] {vid_id} - @{author} ({cat})")
    if len(failed_queue) > 10:
        safe_print(f"  ... và {len(failed_queue) - 10} video khác.")
        
    safe_print("\n📥 Bắt đầu tải và đồng bộ vào Extension... (Bấm Ctrl+C để dừng an toàn)")
    
    success_count = 0
    fail_count = 0
    remaining_queue = []
    stopped_early = False
    
    for i, item in enumerate(failed_queue):
        vid_id = str(item.get("id", "")).strip()
        if not vid_id:
            continue
        author_name = item.get("author", "")
        author_id = item.get("authorId", "")
        cat = item.get("category", "b")
        title = item.get("title", "")
        cover_url = item.get("cover", "")
        url = item.get("url") or (f"https://www.tiktok.com/@{author_name}/video/{vid_id}" if author_name else f"https://www.tiktok.com/video/{vid_id}")
        
        try:
        
            video_path, cover_path = ext_sync.get_target_media_paths(vid_id, cat, author_id)
            safe_print(f"  📁 Video đích: {video_path}")
            safe_print(f"  🖼️ Cover đích: {cover_path}")
        
            # Kiểm tra nếu file video đã tồn tại và hợp lệ (> 100KB)
            already_has_video = video_path.exists() and video_path.stat().st_size > 100000
        
            if already_has_video:
                safe_print("  ⚡ File video đã có sẵn trên ổ đĩa. Đồng bộ ngay vào DB Extension...")
                file_size = video_path.stat().st_size
                size_mb_str = f"{file_size / (1024*1024):.1f}MB"
                synced = ext_sync.register_downloaded_video(
                    video_id=vid_id,
                    author_id=author_id,
                    author_name=author_name,
                    category=cat,
                    title=title,
                    file_size_str=size_mb_str
                )
                if synced:
                    safe_print(f"  ✅ Đã đồng bộ thành công! Xóa {vid_id} khỏi list lỗi.")
                    success_count += 1
                    continue
                
            # Tải bằng downloader
            result = downloader.download_to_custom_path(
                url=url,
                video_target=video_path,
                cover_target=cover_path,
                cover_url=cover_url
            )
        
            if result.success:
                file_size = video_path.stat().st_size if video_path.exists() else 0
                size_mb_str = f"{file_size / (1024*1024):.1f}MB"
                v_info = result.video
            
                synced = ext_sync.register_downloaded_video(
                    video_id=vid_id,
                    author_id=author_id or (v_info.author_id if v_info else ""),
                    author_name=author_name or (v_info.author if v_info else ""),
                    category=cat,
                    title=title or (v_info.title if v_info else ""),
                    create_time=(v_info.create_time if v_info else 0),
                    file_size_str=size_mb_str,
                    stats={'like_count': v_info.like_count if v_info else 0, 'view_count': v_info.view_count if v_info else 0}
                )
            
                if synced:
                    safe_print(f"  ✅ Tải & đồng bộ Extension thành công! Đã xóa khỏi list lỗi.")
                    success_count += 1
                    # Không thêm vào remaining_queue -> XÓA KHỎI QUEUE
                else:
                    safe_print(f"  ⚠️ Đã tải video nhưng không ghi được DB Extension.")
                    item["errorMessage"] = "Ghi DB Extension thất bại"
                    remaining_queue.append(item)
                    fail_count += 1
            else:
                safe_print(f"  ❌ Tải thất bại: {result.error}")
                item["errorMessage"] = result.error
                remaining_queue.append(item)
                fail_count += 1
        except KeyboardInterrupt:
            safe_print(f"\n Dung boi Ctrl+C tai video {i+1}/{len(failed_queue)}")
            safe_print("   Cac video chua tai duoc giu lai trong danh sach loi.")
            remaining_queue.extend(failed_queue[i+1:])
            stopped_early = True
            break
        except Exception as ex_loop:
            safe_print(f"  Loi bat ngo: {ex_loop}")
            remaining_queue.append(item)
            fail_count += 1
    # Lưu lại danh sách lỗi đã dọn sạch các video thành công
    ext_sync.save_failed_queue(remaining_queue, custom_file)
    
    safe_print(f"\n{'='*60}")
    safe_print(f"🎉 KẾT QUẢ XỬ LÝ VIDEO LỖI")
    safe_print(f"  ✅ Tải & đồng bộ thành công: {success_count} (Đã dọn sạch khỏi list lỗi)")
    safe_print(f"  ❌ Còn lại chưa tải được:    {fail_count}")
    safe_print(f"  💾 Số video còn trong list:  {len(remaining_queue)}")
    safe_print(f"{'='*60}\n")


# ===== MAIN =====
def main():
    parser = argparse.ArgumentParser(description="TikTok Downloader")
    parser.add_argument("--mode", choices=["download", "view", "export", "cookies", "settings", "stats", "full-sync", "sync-to-ext", "download-failed"],
                       help="Chế độ chạy")
    parser.add_argument("--max-items", type=int, help="Số lượng tối đa cho full-sync")
    parser.add_argument("--stop-on-error", action="store_true", help="Dừng lại khi gặp video lỗi và phân tích nguyên nhân")
    parser.add_argument("--failed-file", type=str, help="Đường dẫn file failed_videos.json tuỳ chỉnh")
    parser.add_argument("--ext-path", type=str, help="Đường dẫn thư mục data/.appdata của Extension")
    parser.add_argument("urls", nargs="*", help="URLs để tải (cho mode download)")
    args = parser.parse_args()
    
    # If no mode specified, run interactive menu
    if not args.mode:
        interactive_menu()
        return
    
    # Run specific mode
    modes = {
        "download": mode_download,
        "view": mode_view,
        "export": mode_export,
        "cookies": mode_cookies,
        "settings": mode_settings,
        "stats": mode_stats,
        "full-sync": mode_full_sync,
        "sync-to-ext": mode_sync_to_ext,
        "download-failed": mode_download_failed,
    }
    
    try:
        modes[args.mode](args)
    except KeyboardInterrupt:
        print("\n\n⏹ Đã dừng bởi user")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()


def interactive_menu():
    """Menu tương tác khi chạy trực tiếp hoặc qua bat file"""
    while True:
        print_header("TIKTOK DOWNLOADER - MENU CHÍNH")
        print("  1. 🚨 Tải danh sách video lỗi từ Extension (Chung dữ liệu, tự xóa khi xong)")
        print("  2. 📥 Tải video từ URLs (Nhập link trực tiếp)")
        print("  3. 🔄 Full Sync: Tải toàn bộ Likes & Favorites qua TikTok API")
        print("  4. 📤 Đồng bộ dữ liệu Python → Extension (Sync to Extension)")
        print("  5. 🍪 Quản lý Cookies TikTok")
        print("  6. 📊 Xem thống kê video đã tải")
        print("  7. ⚙️ Cài đặt hệ thống (Thư mục lưu trữ, rate limit)")
        print("  0. ❌ Thoát")
        print()
        
        choice = input("👉 Chọn chức năng (0-7): ").strip()
        
        if choice == "1":
            class Args:
                ext_path = None
                failed_file = None
            mode_download_failed(Args())
        elif choice == "2":
            mode_download(argparse.Namespace(urls=[]))
        elif choice == "3":
            mode_full_sync(argparse.Namespace(max_items=None))
        elif choice == "4":
            mode_sync_to_ext(argparse.Namespace())
        elif choice == "5":
            mode_cookies(argparse.Namespace())
        elif choice == "6":
            mode_stats(argparse.Namespace())
        elif choice == "7":
            mode_settings(argparse.Namespace())
        elif choice == "0":
            print("\n👋 Tạm biệt!\n")
            break
        else:
            print("❌ Lựa chọn không hợp lệ, vui lòng chọn lại.")
            
        input("\nNhấn Enter để quay lại menu...")


if __name__ == "__main__":
    main()