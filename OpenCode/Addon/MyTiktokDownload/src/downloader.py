"""
TikTok Downloader Core Module
Sử dụng yt-dlp để bypass TikTok API (không bị lỗi Mar695)
Có SQLite database để index video, tránh trùng lặp, export CSV/JSON
"""

import yt_dlp
import json
import os
import time
import sqlite3
import threading
import csv
from pathlib import Path
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import subprocess
import sys


@dataclass
class VideoInfo:
    id: str
    url: str
    title: str
    author: str
    author_id: str
    duration: int
    view_count: int
    like_count: int
    comment_count: int
    create_time: int
    thumbnail: str
    download_url: str = ""
    file_path: str = ""
    status: str = "pending"  # pending, downloading, completed, failed, skipped
    error: str = ""
    file_size: int = 0
    downloaded_at: str = ""
    category: str = "manual"  # manual, likes, favorites, follows

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'VideoInfo':
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class DownloadResult:
    success: bool
    video: VideoInfo
    error: str = ""


class VideoIndex:
    """SQLite database để index video đã tải, tránh trùng lặp"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    author TEXT,
                    author_id TEXT,
                    duration INTEGER,
                    view_count INTEGER,
                    like_count INTEGER,
                    comment_count INTEGER,
                    create_time INTEGER,
                    thumbnail TEXT,
                    download_url TEXT,
                    file_path TEXT,
                    status TEXT DEFAULT 'pending',
                    error TEXT DEFAULT '',
                    file_size INTEGER DEFAULT 0,
                    downloaded_at TEXT,
                    category TEXT DEFAULT 'manual',
                    UNIQUE(id, category)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_author ON videos(author)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_category ON videos(category)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_downloaded_at ON videos(downloaded_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON videos(status)
            """)
            conn.commit()
            
    def is_downloaded(self, video_id: str, category: str = "manual") -> bool:
        """Kiểm tra video đã tải chưa"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM videos WHERE id = ? AND category = ? AND status = 'completed'",
                    (video_id, category)
                )
                return cursor.fetchone() is not None
                
    def get_existing(self, video_id: str, category: str = "manual") -> Optional[VideoInfo]:
        """Lấy thông tin video đã có trong DB"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM videos WHERE id = ? AND category = ?",
                    (video_id, category)
                )
                row = cursor.fetchone()
                if row:
                    return VideoInfo.from_dict(dict(row))
        return None
        
    def add_or_update(self, video: VideoInfo):
        """Thêm hoặc cập nhật video"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                data = video.to_dict()
                data['downloaded_at'] = video.downloaded_at or datetime.now().isoformat()
                cols = ', '.join(data.keys())
                placeholders = ', '.join(['?'] * len(data))
                updates = ', '.join([f"{k} = excluded.{k}" for k in data.keys() if k != 'id'])
                conn.execute(f"""
                    INSERT INTO videos ({cols}) VALUES ({placeholders})
                    ON CONFLICT(id, category) DO UPDATE SET {updates}
                """, tuple(data.values()))
                conn.commit()
                
    def mark_downloaded(self, video_id: str, category: str, file_path: str, file_size: int):
        """Đánh dấu video đã tải xong"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE videos SET 
                        status = 'completed',
                        file_path = ?,
                        file_size = ?,
                        downloaded_at = ?,
                        error = ''
                    WHERE id = ? AND category = ?
                """, (file_path, file_size, datetime.now().isoformat(), video_id, category))
                conn.commit()
                
    def mark_failed(self, video_id: str, category: str, error: str):
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE videos SET status = 'failed', error = ?
                    WHERE id = ? AND category = ?
                """, (error, video_id, category))
                conn.commit()
                
    def search(self, query: str = "", author: str = "", category: str = "", 
               status: str = "", limit: int = 100, offset: int = 0) -> List[VideoInfo]:
        """Tìm kiếm video trong DB"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                where = ["1=1"]
                params = []
                
                if query:
                    where.append("(title LIKE ? OR author LIKE ?)")
                    params.extend([f"%{query}%", f"%{query}%"])
                if author:
                    where.append("author LIKE ?")
                    params.append(f"%{author}%")
                if category:
                    where.append("category = ?")
                    params.append(category)
                if status:
                    where.append("status = ?")
                    params.append(status)
                    
                sql = f"""
                    SELECT * FROM videos 
                    WHERE {' AND '.join(where)}
                    ORDER BY downloaded_at DESC
                    LIMIT ? OFFSET ?
                """
                params.extend([limit, offset])
                
                cursor = conn.execute(sql, params)
                return [VideoInfo.from_dict(dict(row)) for row in cursor.fetchall()]
                
    def get_stats(self) -> dict:
        """Thống kê"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                        SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped,
                        SUM(file_size) as total_size,
                        COUNT(DISTINCT author) as unique_authors,
                        COUNT(DISTINCT category) as categories
                    FROM videos
                """)
                row = cursor.fetchone()
                return {
                    'total': row[0] or 0,
                    'completed': row[1] or 0,
                    'failed': row[2] or 0,
                    'skipped': row[3] or 0,
                    'total_size': row[4] or 0,
                    'unique_authors': row[5] or 0,
                    'categories': row[6] or 0
                }
                
    def get_by_category(self, category: str) -> List[VideoInfo]:
        return self.search(category=category, status="completed")
        
    def export_json(self, filepath: str, category: str = "", status: str = "completed"):
        """Export ra JSON (format giống myfaveTT)"""
        videos = self.search(category=category, status=status, limit=10000)
        
        # Format giống myfaveTT
        authors_map = {}
        for v in videos:
            if v.author_id not in authors_map:
                authors_map[v.author_id] = {
                    'id': v.author_id,
                    'u': v.author,  # username
                    'n': v.author,  # nickname (same for now)
                    'b': [],  # favorites/bookmarks
                    'l': [],  # likes
                }
            authors_map[v.author_id][category if category in ('b', 'l') else 'b'].append([v.id, v.create_time])
            
        output = {
            'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'stats': {
                'fav': sum(len(a['b']) for a in authors_map.values()),
                'likes': sum(len(a['l']) for a in authors_map.values()),
                'authors': len(authors_map)
            },
            'authors': list(authors_map.values())
        }
        
        Path(filepath).write_text(json.dumps(output, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        return len(videos)
        
    def export_csv(self, filepath: str, category: str = "", status: str = "completed"):
        """Export ra CSV"""
        videos = self.search(category=category, status=status, limit=10000)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'video_id', 'url', 'title', 'author', 'author_id',
                'duration', 'view_count', 'like_count', 'comment_count',
                'create_time', 'downloaded_at', 'file_path', 'file_size', 'category'
            ])
            for v in videos:
                writer.writerow([
                    v.id, v.url, v.title, v.author, v.author_id,
                    v.duration, v.view_count, v.like_count, v.comment_count,
                    v.create_time, v.downloaded_at, v.file_path, v.file_size, v.category
                ])
        return len(videos)


class TikTokDownloader:
    def __init__(self, 
                 output_dir: str = "downloads",
                 db_path: str = "downloads/video_index.db",
                 cookies_file: str = None,
                 proxy: str = None,
                 rate_limit: str = "1M",
                 max_retries: int = 3,
                 skip_existing: bool = True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cookies_file = cookies_file
        self.proxy = proxy
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.skip_existing = skip_existing
        
        # Video Index (SQLite)
        self.index = VideoIndex(db_path)
        
        # Default yt-dlp options
        self.ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': str(self.output_dir / '%(uploader)s_%(id)s.%(ext)s'),
            'writethumbnail': True,
            'writeinfojson': True,
            'ignoreerrors': False,
            'no_warnings': False,
            'quiet': True,
            'extract_flat': False,
            'retries': max_retries,
            'fragment_retries': max_retries,
            'skip_unavailable_fragments': True,
            'keepvideo': False,
            'postprocessors': [
                {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'},
            ],
        }
        
        if cookies_file and os.path.exists(cookies_file):
            self.ydl_opts['cookiefile'] = cookies_file
            
        if proxy:
            self.ydl_opts['proxy'] = proxy
            
        if rate_limit:
            try:
                import yt_dlp.utils
                parsed_rate = yt_dlp.utils.parse_bytes(str(rate_limit)) if isinstance(rate_limit, str) else float(rate_limit)
                if parsed_rate:
                    self.ydl_opts['ratelimit'] = parsed_rate
            except Exception:
                pass

    def extract_info(self, url: str) -> Optional[VideoInfo]:
        """Trích xuất thông tin video không tải xuống"""
        opts = self.ydl_opts.copy()
        opts['quiet'] = True
        opts['skip_download'] = True
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None
                return self._parse_video_info(info, url)
        except Exception as e:
            return None

    def _parse_video_info(self, info: dict, url: str) -> VideoInfo:
        return VideoInfo(
            id=info.get('id', ''),
            url=url,
            title=info.get('title', ''),
            author=info.get('uploader', ''),
            author_id=info.get('uploader_id', ''),
            duration=info.get('duration', 0),
            view_count=info.get('view_count', 0),
            like_count=info.get('like_count', 0),
            comment_count=info.get('comment_count', 0),
            create_time=int(info.get('timestamp', 0)),
            thumbnail=info.get('thumbnail', ''),
            download_url=info.get('url', ''),
        )

    def download_video(self, video_info: VideoInfo, 
                       progress_callback: Callable = None) -> DownloadResult:
        """Tải một video"""
        # Check duplicate
        if self.skip_existing and self.index.is_downloaded(video_info.id, video_info.category):
            existing = self.index.get_existing(video_info.id, video_info.category)
            video_info.status = "skipped"
            video_info.file_path = existing.file_path if existing else ""
            video_info.file_size = existing.file_size if existing else 0
            video_info.downloaded_at = existing.downloaded_at if existing else ""
            return DownloadResult(True, video_info, "Already downloaded (skipped)")
            
        video_info.status = "downloading"
        if progress_callback:
            progress_callback(video_info, 0, "Starting...")
            
        opts = self.ydl_opts.copy()
        opts['progress_hooks'] = [lambda d: self._progress_hook(d, video_info, progress_callback)]
        
        last_error = ""
        for attempt in range(self.max_retries):
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([video_info.url])
                    
                file_path = self._find_downloaded_file(video_info.id)
                if file_path:
                    video_info.file_path = str(file_path)
                    video_info.file_size = file_path.stat().st_size
                    video_info.status = "completed"
                    video_info.downloaded_at = datetime.now().isoformat()
                    # Save to index
                    self.index.add_or_update(video_info)
                    self.index.mark_downloaded(video_info.id, video_info.category, str(file_path), video_info.file_size)
                    return DownloadResult(True, video_info)
                else:
                    last_error = "File không tìm thấy sau khi tải"
                    
            except yt_dlp.utils.DownloadError as e:
                last_error = str(e)
                if "Video unavailable" in str(e) or "Private video" in str(e):
                    break
                time.sleep(2 ** attempt)
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                time.sleep(2 ** attempt)
                
        video_info.status = "failed"
        video_info.error = last_error
        self.index.mark_failed(video_info.id, video_info.category, last_error)
        return DownloadResult(False, video_info, last_error)

    def _progress_hook(self, d: dict, video_info: VideoInfo, callback: Callable):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            if total > 0:
                percent = (downloaded / total) * 100
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                if callback:
                    callback(video_info, percent, 
                           f"{self._format_bytes(downloaded)}/{self._format_bytes(total)} "
                           f"@{self._format_bytes(speed)}/s ETA: {eta}s")
        elif d['status'] == 'finished':
            if callback:
                callback(video_info, 100, "Processing...")

    def _find_downloaded_file(self, video_id: str) -> Optional[Path]:
        patterns = [
            f"*_{video_id}.mp4",
            f"*_{video_id}.mkv",
            f"*_{video_id}.webm",
            f"*_{video_id}.*",
        ]
        for pattern in patterns:
            files = list(self.output_dir.glob(pattern))
            if files:
                return max(files, key=lambda f: f.stat().st_mtime)
        return None

    @staticmethod
    def _format_bytes(b: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if b < 1024:
                return f"{b:.1f}{unit}"
            b /= 1024
        return f"{b:.1f}TB"

    def batch_download(self, urls: List[str], 
                       progress_callback: Callable = None,
                       complete_callback: Callable = None,
                       category: str = "manual") -> List[DownloadResult]:
        """Tải nhiều video"""
        results = []
        for i, url in enumerate(urls):
            if progress_callback:
                progress_callback(i, len(urls), url, "Extracting info...")
                
            video_info = self.extract_info(url)
            if not video_info:
                results.append(DownloadResult(False, 
                    VideoInfo(id="", url=url, title="", author="", author_id="", 
                             duration=0, view_count=0, like_count=0, comment_count=0,
                             create_time=0, thumbnail=""),
                    "Không thể trích xuất thông tin"))
                continue
                
            video_info.category = category
            
            if progress_callback:
                progress_callback(i, len(urls), url, f"Downloading: {video_info.title[:50]}...")
                
            result = self.download_video(video_info, 
                lambda v, p, m: progress_callback(i, len(urls), url, f"{p:.1f}% - {m}") if progress_callback else None)
            results.append(result)
            
            if complete_callback:
                complete_callback(result)
                
        return results

    def download_to_custom_path(self,
                                url: str,
                                video_target: Path,
                                cover_target: Path,
                                cover_url: str = "",
                                progress_callback: Callable = None) -> DownloadResult:
        """
        Tải video trực tiếp vào đúng video_target (.mp4) và cover_target (.jpg) của Extension
        """
        video_target = Path(video_target)
        cover_target = Path(cover_target)
        video_target.parent.mkdir(parents=True, exist_ok=True)
        cover_target.parent.mkdir(parents=True, exist_ok=True)
        
        opts = self.ydl_opts.copy()
        opts['outtmpl'] = str(video_target.parent / f"{video_target.stem}.%(ext)s")
        opts['writethumbnail'] = False
        opts['writeinfojson'] = False
        opts['quiet'] = True
        opts['no_warnings'] = True
        
        extracted_info = None
        last_error = ""
        
        for attempt in range(self.max_retries):
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    extracted_info = ydl.extract_info(url, download=True)
                break
            except yt_dlp.utils.DownloadError as e:
                last_error = str(e)
                if "Video unavailable" in str(e) or "Private video" in str(e):
                    break
                time.sleep(2 ** attempt)
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                time.sleep(2 ** attempt)
                
        # Tìm file video đã tải
        found_video = None
        for ext in ['.mp4', '.mkv', '.webm', '.ts', '']:
            candidate = video_target.parent / f"{video_target.stem}{ext}"
            if candidate.exists() and candidate.is_file():
                found_video = candidate
                break
                
        if not found_video:
            return DownloadResult(False, VideoInfo(id="", url=url, title="", author="", author_id="", duration=0, view_count=0, like_count=0, comment_count=0, create_time=0, thumbnail=""), last_error or "Không tìm thấy file sau khi tải")
            
        # Đảm bảo file đích là video_target (.mp4)
        if found_video != video_target:
            if video_target.exists():
                video_target.unlink()
            found_video.rename(video_target)
            
        # Tải cover ảnh bìa nếu có URL và file chưa tồn tại
        target_cover_url = cover_url or (extracted_info.get('thumbnail') if extracted_info else "")
        if target_cover_url and not cover_target.exists():
            try:
                import requests
                resp = requests.get(target_cover_url, timeout=15)
                if resp.status_code == 200 and resp.content:
                    cover_target.write_bytes(resp.content)
            except Exception:
                pass
                
        # Parse VideoInfo
        v_info = self._parse_video_info(extracted_info, url) if extracted_info else VideoInfo(
            id=video_target.stem, url=url, title="", author="", author_id="", duration=0, view_count=0, like_count=0, comment_count=0, create_time=int(time.time()), thumbnail=""
        )
        v_info.file_path = str(video_target)
        v_info.file_size = video_target.stat().st_size
        v_info.status = "completed"
        return DownloadResult(True, v_info)

    # ===== New: Fetch from TikTok API (like myfaveTT) =====
    def fetch_likes_favorites(self, cookies: str, max_items: int = 0) -> Tuple[List[VideoInfo], List[VideoInfo]]:
        """
        Lấy danh sách Likes và Favorites từ TikTok API
        Giống myfaveTT intercept api/post/item_list/
        """
        import requests
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.tiktok.com/',
            'Cookie': cookies,
        }
        
        likes = []
        favorites = []
        
        # Fetch Likes
        likes = self._fetch_item_list(cookies, headers, "like", max_items)
        # Fetch Favorites (bookmarks)
        favorites = self._fetch_item_list(cookies, headers, "bookmark", max_items)
        
        return likes, favorites
        
    def _fetch_item_list(self, cookies: str, headers: dict, item_type: str, max_items: int) -> List[VideoInfo]:
        """Fetch từ TikTok API item_list"""
        import requests
        
        base_url = "https://www.tiktok.com/api/post/item_list/"
        params = {
            'aid': '1988',
            'app_language': 'vi',
            'app_name': 'tiktok_web',
            'browser_language': 'vi-VN',
            'browser_name': 'Mozilla',
            'browser_online': 'true',
            'browser_platform': 'Win32',
            'browser_version': '120.0.0.0',
            'channel': 'tiktok_web',
            'cookie_enabled': 'true',
            'count': '30',
            'device_id': '0',
            'device_platform': 'web_pc',
            'from_page': 'user',
            'history_len': '4',
            'is_fullscreen': 'false',
            'odinId': '0',
            'os': 'windows',
            'priority_region': 'VN',
            'referer': 'https://www.tiktok.com/',
            'region': 'VN',
            'screen_height': '1080',
            'screen_width': '1920',
            'tz_name': 'Asia/Ho_Chi_Minh',
            'webcast_language': 'vi',
        }
        
        if item_type == "like":
            params['type'] = '1'
        elif item_type == "bookmark":
            params['type'] = '2'
            
        results = []
        cursor = 0
        
        while True:
            params['cursor'] = str(cursor)
            
            try:
                resp = requests.get(base_url, params=params, headers=headers, timeout=30)
                if resp.status_code != 200:
                    break
                    
                data = resp.json()
                if data.get('status_code') != 0:
                    break
                    
                item_list = data.get('itemList', [])
                if not item_list:
                    break
                    
                for item in item_list:
                    video_info = self._parse_api_item(item)
                    if video_info:
                        video_info.category = 'l' if item_type == 'like' else 'b'
                        results.append(video_info)
                        
                has_more = data.get('hasMore', False)
                cursor = data.get('cursor', 0)
                
                if not has_more or (max_items > 0 and len(results) >= max_items):
                    break
                    
                time.sleep(1)  # Rate limit
                
            except Exception as e:
                print(f"Fetch error: {e}")
                break
                
        return results[:max_items] if max_items > 0 else results
        
    def _parse_api_item(self, item: dict) -> Optional[VideoInfo]:
        """Parse item từ TikTok API"""
        try:
            video = item.get('video', {})
            author = item.get('author', {})
            stats = item.get('stats', {})
            
            return VideoInfo(
                id=item.get('id', ''),
                url=f"https://www.tiktok.com/@{author.get('uniqueId', '')}/video/{item.get('id', '')}",
                title=item.get('desc', ''),
                author=author.get('nickname', ''),
                author_id=author.get('uniqueId', ''),
                duration=video.get('duration', 0),
                view_count=stats.get('playCount', 0),
                like_count=stats.get('diggCount', 0),
                comment_count=stats.get('commentCount', 0),
                create_time=item.get('createTime', 0),
                thumbnail=video.get('cover', ''),
                download_url=video.get('playAddr', ''),
            )
        except Exception:
            return None


def get_chrome_cookies(domain: str = "tiktok.com") -> Optional[str]:
    import sqlite3
    import tempfile
    import shutil
    
    cookie_paths = [
        Path(os.environ['LOCALAPPDATA']) / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Network' / 'Cookies',
        Path(os.environ['LOCALAPPDATA']) / 'Google' / 'Chrome' / 'User Data' / 'Profile 3' / 'Network' / 'Cookies',
    ]
    
    for cookie_db in cookie_paths:
        if not cookie_db.exists():
            continue
            
        temp_db = Path(tempfile.gettempdir()) / f"chrome_cookies_{int(time.time())}.db"
        
        # Try to copy with retries (Chrome locks the file)
        copied = False
        for attempt in range(3):
            try:
                shutil.copy2(cookie_db, temp_db)
                copied = True
                break
            except PermissionError:
                time.sleep(0.5)  # Wait a bit and retry
            except Exception:
                break
        
        if not copied:
            continue
            
        try:
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT host_key, name, value, path, expires_utc, is_secure, is_httponly
                FROM cookies 
                WHERE host_key LIKE ?
            """, (f"%{domain}%",))
            
            cookies = []
            for row in cursor.fetchall():
                host, name, value, path, expires, secure, httponly = row
                cookies.append(f"{name}={value}")
                
            conn.close()
            temp_db.unlink()
            
            if cookies:
                return "; ".join(cookies)
        except Exception:
            if temp_db.exists():
                temp_db.unlink()
            continue
            
    return None


# ======================================================================
# HYBRID DOWNLOADER - API First, yt-dlp Fallback
# ======================================================================
class HybridDownloader:
    """
    Unified downloader: TikTok API (like extension) → yt-dlp fallback
    Cùng output format: VideoInfo, SQLite index, JSON myfaveTT format
    """
    
    def __init__(self, 
                 output_dir: str = "downloads",
                 db_path: str = "downloads/video_index.db",
                 cookies: str = "",
                 proxy: str = None,
                 rate_limit: str = "1M",
                 max_retries: int = 3,
                 skip_existing: bool = True):
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cookies = cookies
        self.proxy = proxy
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.skip_existing = skip_existing
        
        # Shared SQLite index
        self.index = VideoIndex(db_path)
        
        # yt-dlp fallback downloader
        self._yt_downloader = TikTokDownloader(
            output_dir=output_dir,
            db_path=db_path,
            cookies_file=None,
            proxy=proxy,
            rate_limit=rate_limit,
            max_retries=max_retries,
            skip_existing=skip_existing
        )
        
        # API config
        self.api_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.tiktok.com/',
            'Cookie': cookies,
        }
        self.api_base_url = "https://www.tiktok.com/api/post/item_list/"
        self.api_default_params = {
            'aid': '1988',
            'app_language': 'vi',
            'app_name': 'tiktok_web',
            'browser_language': 'vi-VN',
            'browser_name': 'Mozilla',
            'browser_online': 'true',
            'browser_platform': 'Win32',
            'browser_version': '120.0.0.0',
            'channel': 'tiktok_web',
            'cookie_enabled': 'true',
            'count': '30',
            'device_id': '0',
            'device_platform': 'web_pc',
            'from_page': 'user',
            'history_len': '4',
            'is_fullscreen': 'false',
            'odinId': '0',
            'os': 'windows',
            'priority_region': 'VN',
            'referer': 'https://www.tiktok.com/',
            'region': 'VN',
            'screen_height': '1080',
            'screen_width': '1920',
            'tz_name': 'Asia/Ho_Chi_Minh',
            'webcast_language': 'vi',
        }
        
        # Update yt-dlp with cookies
        if cookies:
            self._yt_downloader.ydl_opts['cookiefile'] = None
            self._yt_downloader.ydl_opts['http_headers'] = {'Cookie': cookies}
    
    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------
    def extract_info(self, url: str, method: str = "auto") -> Optional[VideoInfo]:
        """
        Extract video info.
        method: "auto" (API→yt-dlp), "api", "yt-dlp"
        """
        if method in ("auto", "api") and self.cookies:
            info = self._extract_via_api(url)
            if info:
                return info
        
        if method in ("auto", "yt-dlp"):
            return self._yt_downloader.extract_info(url)
        
        return None
    
    def download_video(self, video_info: VideoInfo, 
                       progress_callback: Callable = None,
                       method: str = "auto") -> DownloadResult:
        """
        Download video with fallback.
        method: "auto" (API→yt-dlp), "api", "yt-dlp"
        """
        # Check duplicate first
        if self.skip_existing and self.index.is_downloaded(video_info.id, video_info.category):
            existing = self.index.get_existing(video_info.id, video_info.category)
            video_info.status = "skipped"
            video_info.file_path = existing.file_path if existing else ""
            video_info.file_size = existing.file_size if existing else 0
            video_info.downloaded_at = existing.downloaded_at if existing else ""
            return DownloadResult(True, video_info, "Already downloaded (skipped)")
        
        # Try API first if cookies available
        if method in ("auto", "api") and self.cookies:
            result = self._download_via_api(video_info, progress_callback)
            if result.success:
                return result
            # Log API failure, fallback to yt-dlp
            print(f"  ⚠️ API failed: {result.error}. Fallback to yt-dlp...")
        
        # Fallback to yt-dlp
        return self._yt_downloader.download_video(video_info, progress_callback)
    
    def batch_download(self, urls: List[str], 
                       progress_callback: Callable = None,
                       complete_callback: Callable = None,
                       category: str = "manual",
                       method: str = "auto") -> List[DownloadResult]:
        """Batch download with fallback"""
        results = []
        for i, url in enumerate(urls):
            if progress_callback:
                progress_callback(i, len(urls), url, "Extracting info...")
            
            video_info = self.extract_info(url, method)
            if not video_info:
                results.append(DownloadResult(False, 
                    VideoInfo(id="", url=url, title="", author="", author_id="", 
                             duration=0, view_count=0, like_count=0, comment_count=0,
                             create_time=0, thumbnail=""),
                    "Không thể trích xuất thông tin (cả API và yt-dlp)"))
                continue
            
            video_info.category = category
            
            if progress_callback:
                progress_callback(i, len(urls), url, f"Downloading: {video_info.title[:50]}...")
            
            result = self.download_video(video_info, 
                lambda v, p, m: progress_callback(i, len(urls), url, f"{p:.1f}% - {m}") if progress_callback else None,
                method)
            results.append(result)
            
            if complete_callback:
                complete_callback(result)
                
        return results
    
    def download_to_custom_path(self,
                                url: str,
                                video_target: Path,
                                cover_target: Path,
                                cover_url: str = "",
                                progress_callback: Callable = None) -> DownloadResult:
        """Download directly to specific paths using yt-dlp"""
        return self._yt_downloader.download_to_custom_path(
            url=url,
            video_target=video_target,
            cover_target=cover_target,
            cover_url=cover_url,
            progress_callback=progress_callback
        )
    
    # ------------------------------------------------------------------
    # API METHODS (like myfaveTT extension)
    # ------------------------------------------------------------------
    def fetch_likes_favorites(self, max_items: int = 0) -> Tuple[List[VideoInfo], List[VideoInfo]]:
        """Fetch Likes & Favorites via TikTok API (requires cookies)"""
        if not self.cookies:
            raise ValueError("Cần cookie TikTok để dùng API. Chạy mode cookies trước.")
        
        likes = self._fetch_item_list("like", max_items)
        favorites = self._fetch_item_list("bookmark", max_items)
        return likes, favorites
    
    def _fetch_item_list(self, item_type: str, max_items: int) -> List[VideoInfo]:
        """Fetch từ TikTok API item_list"""
        import requests
        
        params = self.api_default_params.copy()
        params['type'] = '1' if item_type == "like" else '2'
        
        results = []
        cursor = 0
        
        while True:
            params['cursor'] = str(cursor)
            
            try:
                resp = requests.get(self.api_base_url, params=params, 
                                  headers=self.api_headers, timeout=30)
                if resp.status_code != 200:
                    break
                    
                data = resp.json()
                if data.get('status_code') != 0:
                    error_msg = data.get('status_msg', 'Unknown API error')
                    raise Exception(f"API Error: {error_msg}")
                    
                item_list = data.get('itemList', [])
                if not item_list:
                    break
                    
                for item in item_list:
                    video_info = self._parse_api_item(item)
                    if video_info:
                        video_info.category = 'l' if item_type == 'like' else 'b'
                        results.append(video_info)
                        
                has_more = data.get('hasMore', False)
                cursor = data.get('cursor', 0)
                
                if not has_more or (max_items > 0 and len(results) >= max_items):
                    break
                    
                time.sleep(1)  # Rate limit
                
            except Exception as e:
                raise Exception(f"API fetch failed: {e}")
                
        return results[:max_items] if max_items > 0 else results
    
    def _parse_api_item(self, item: dict) -> Optional[VideoInfo]:
        """Parse item từ TikTok API -> VideoInfo (cùng format yt-dlp)"""
        try:
            video = item.get('video', {})
            author = item.get('author', {})
            stats = item.get('stats', {})
            
            return VideoInfo(
                id=item.get('id', ''),
                url=f"https://www.tiktok.com/@{author.get('uniqueId', '')}/video/{item.get('id', '')}",
                title=item.get('desc', ''),
                author=author.get('nickname', ''),
                author_id=author.get('uniqueId', ''),
                duration=video.get('duration', 0),
                view_count=stats.get('playCount', 0),
                like_count=stats.get('diggCount', 0),
                comment_count=stats.get('commentCount', 0),
                create_time=item.get('createTime', 0),
                thumbnail=video.get('cover', ''),
                download_url=video.get('playAddr', ''),
                category='api'
            )
        except Exception:
            return None
    
    # ------------------------------------------------------------------
    # INTERNAL: API download for single video (fallback to yt-dlp)
    # ------------------------------------------------------------------
    def _extract_via_api(self, url: str) -> Optional[VideoInfo]:
        """Extract single video info via API (need video_id from URL)"""
        import re
        match = re.search(r'/video/(\d+)', url)
        if not match:
            return None
        # API doesn't have single video endpoint easily, use yt-dlp instead
        return None
    
    def _download_via_api(self, video_info: VideoInfo, progress_callback: Callable) -> DownloadResult:
        """
        Download via API: Get playAddr from API, then download direct
        This is complex because API doesn't give single video easily.
        For now, delegate to yt-dlp which handles playAddr extraction better.
        """
        return DownloadResult(False, video_info, "API single download not implemented, use yt-dlp")
    
    # ------------------------------------------------------------------
    # DELEGATE TO SHARED INDEX
    # ------------------------------------------------------------------
    def search(self, *args, **kwargs):
        return self.index.search(*args, **kwargs)
    
    def get_stats(self):
        return self.index.get_stats()
    
    def export_json(self, *args, **kwargs):
        return self.index.export_json(*args, **kwargs)
    
    def export_csv(self, *args, **kwargs):
        return self.index.export_csv(*args, **kwargs)


# ======================================================================
# UTILITY FUNCTIONS
# ======================================================================
def get_chrome_cookies(domain: str = "tiktok.com") -> Optional[str]:
    import sqlite3
    import tempfile
    import shutil
    
    cookie_paths = [
        Path(os.environ['LOCALAPPDATA']) / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Network' / 'Cookies',
        Path(os.environ['LOCALAPPDATA']) / 'Google' / 'Chrome' / 'User Data' / 'Profile 3' / 'Network' / 'Cookies',
    ]
    
    for cookie_db in cookie_paths:
        if not cookie_db.exists():
            continue
            
        temp_db = Path(tempfile.gettempdir()) / f"chrome_cookies_{int(time.time())}.db"
        
        # Try to copy with retries (Chrome locks the file)
        copied = False
        for attempt in range(3):
            try:
                shutil.copy2(cookie_db, temp_db)
                copied = True
                break
            except PermissionError:
                time.sleep(0.5)  # Wait a bit and retry
            except Exception:
                break
        
        if not copied:
            continue
            
        try:
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT host_key, name, value, path, expires_utc, is_secure, is_httponly
                FROM cookies 
                WHERE host_key LIKE ?
            """, (f"%{domain}%",))
            
            cookies = []
            for row in cursor.fetchall():
                host, name, value, path, expires, secure, httponly = row
                cookies.append(f"{name}={value}")
                
            conn.close()
            temp_db.unlink()
            
            if cookies:
                return "; ".join(cookies)
        except Exception:
            if temp_db.exists():
                temp_db.unlink()
            continue
            
    return None


def save_cookies_to_file(cookies_str: str, filepath: str = "cookies.txt"):
    lines = [
        "# Netscape HTTP Cookie File",
        "# This file was generated by TikTok Downloader",
        ""
    ]
    for cookie in cookies_str.split("; "):
        if "=" in cookie:
            name, value = cookie.split("=", 1)
            lines.append(f".tiktok.com\tTRUE\t/\tFALSE\t0\t{name}\t{value}")
    Path(filepath).write_text("\n".join(lines), encoding='utf-8')
    return filepath