"""
Extension Sync Module - Sync dữ liệu giữa Python Downloader và Extension myfaveTT
Đọc/ghi file db_*.js (base64 + gzip) của extension chuẩn 100% schema
"""

import base64
import gzip
import json
import re
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class ExtensionSync:
    """
    Sync dữ liệu giữa Python Downloader và Extension myfaveTT
    Đọc/ghi các file db_*.js (base64 + gzip) và quản lý failed_videos.json
    """

    def __init__(self, ext_data_path: str = r"D:\dlvideott\data\.appdata"):
        self.ext_path = Path(ext_data_path)
        # archive_root thường là thư mục cha của 'data/.appdata'
        if self.ext_path.name == ".appdata" and self.ext_path.parent.name == "data":
            self.archive_root = self.ext_path.parent.parent
        else:
            self.archive_root = self.ext_path.parent

        self.files = {
            'authors': self.ext_path / 'db_authors.js',       # window.dba_base64
            'videos': self.ext_path / 'db_videos.js',         # window.dbv_base64
            'bookmarked': self.ext_path / 'db_bookmarked.js', # window.dbb_base64
            'likes': self.ext_path / 'db_likes.js',            # window.db_base64
            'texts': self.ext_path / 'db_texts.js',           # window.dbvd_base64
            'following': self.ext_path / 'db_following.js',   # window.dbf_base64
        }
        self.var_names = {
            'authors': 'dba_base64',
            'videos': 'dbv_base64',
            'bookmarked': 'dbb_base64',
            'likes': 'db_base64',
            'texts': 'dbvd_base64',
            'following': 'dbf_base64',
        }
        self.failed_json_path = self.ext_path / "failed_videos.json"

    # ==================== LOW LEVEL DECODE / ENCODE ====================
    def _decode_file(self, file_path: Path, var_name: str) -> Optional[Any]:
        """Decode file .js base64+gzip → python object"""
        if not file_path.exists():
            return None
        try:
            content = file_path.read_text(encoding='utf-8')
            match = re.search(r'window\.' + re.escape(var_name) + r'\s*=\s*"([^"]+)"', content)
            if not match:
                return None
            b64 = match.group(1)
            gz = base64.b64decode(b64)
            return json.loads(gzip.decompress(gz).decode('utf-8'))
        except Exception as e:
            print(f"❌ Lỗi decode {file_path.name}: {e}")
            return None

    def _encode_file(self, data: Any, file_path: Path, var_name: str) -> bool:
        """Encode python object → base64+gzip → write file .js"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            gz = gzip.compress(json_str.encode('utf-8'))
            b64 = base64.b64encode(gz).decode('utf-8')
            content = f'window.{var_name}="{b64}";'
            file_path.write_text(content, encoding='utf-8')
            return True
        except Exception as e:
            print(f"❌ Lỗi encode {file_path.name}: {e}")
            return False

    # ==================== TARGET PATH RESOLVER ====================
    def get_target_media_paths(self, video_id: str, category: str, author_id: str = "") -> Tuple[Path, Path]:
        """
        Trả về (video_path, cover_path) chuẩn 100% theo cây thư mục của Extension:
        - Favorites: data/Favorites/videos/{id}.mp4 và covers/{id}.jpg
        - Likes: data/Likes/videos/{id}.mp4 và covers/{id}.jpg
        - Following: data/Following/{author_id}/videos/{id}.mp4 và covers/{id}.jpg
        """
        cat_lower = str(category).lower()
        if cat_lower in ('b', 'bookmarked', 'favorites', 'fav'):
            base = self.archive_root / "data" / "Favorites"
        elif cat_lower in ('l', 'liked', 'likes', 'like'):
            base = self.archive_root / "data" / "Likes"
        elif cat_lower in ('following', 'f'):
            aid = author_id or "unknown"
            base = self.archive_root / "data" / "Following" / aid
        else:
            base = self.archive_root / "data" / "Favorites"

        videos_dir = base / "videos"
        covers_dir = base / "covers"
        videos_dir.mkdir(parents=True, exist_ok=True)
        covers_dir.mkdir(parents=True, exist_ok=True)

        video_path = videos_dir / f"{video_id}.mp4"
        cover_path = covers_dir / f"{video_id}.jpg"
        return video_path, cover_path

    # ==================== READ STATUS ====================
    def is_video_downloaded(self, video_id: str, category: str) -> bool:
        """Kiểm tra video đã nằm trong mảng downloaded của Extension chưa"""
        cat_lower = str(category).lower()
        if cat_lower in ('b', 'bookmarked', 'favorites', 'fav'):
            dbb = self._decode_file(self.files['bookmarked'], self.var_names['bookmarked'])
            if isinstance(dbb, dict):
                dl = dbb.get('downloaded', [])
                return video_id in dl
        elif cat_lower in ('l', 'liked', 'likes', 'like'):
            dbl = self._decode_file(self.files['likes'], self.var_names['likes'])
            if isinstance(dbl, dict):
                likes_obj = dbl.get('likes', {})
                dl = likes_obj.get('downloaded', [])
                return video_id in dl
        return False

    # ==================== REGISTER DOWNLOADED VIDEO (CORE) ====================
    def register_downloaded_video(self,
                                  video_id: str,
                                  author_id: str,
                                  author_name: str = "",
                                  category: str = "b",
                                  title: str = "",
                                  create_time: int = 0,
                                  file_size_str: str = "",
                                  stats: dict = None) -> bool:
        """
        Cập nhật toàn diện metadata vào Database Extension:
        1. db_videos.js: thông tin size, createTime, authorId
        2. db_texts.js: caption/title
        3. db_authors.js: tác giả (uniqueIds, nicknames)
        4. db_bookmarked.js hoặc db_likes.js: thêm video_id vào mảng 'downloaded'
        --> Extension Chrome mở lại sẽ thấy ngay downloaded.has(video_id) và BỎ QUA KHÔNG TẢI LẠI!
        """
        try:
            if not video_id:
                return False

            author_id = str(author_id or "unknown")
            author_name = str(author_name or author_id)
            stats = stats or {}

            # 1. Update db_videos.js
            videos = self._decode_file(self.files['videos'], self.var_names['videos'])
            if not isinstance(videos, dict):
                videos = {}
            videos[video_id] = {
                'authorId': author_id,
                'createTime': create_time or int(time.time()),
                'itemMute': False,
                'diggCount': stats.get('like_count', 0),
                'playCount': stats.get('view_count', 0),
                'audioId': '',
                'size': file_size_str or "0.0MB"
            }
            self._encode_file(videos, self.files['videos'], self.var_names['videos'])

            # 2. Update db_texts.js (caption / desc)
            texts = self._decode_file(self.files['texts'], self.var_names['texts'])
            if not isinstance(texts, dict):
                texts = {}
            texts[video_id] = title or ""
            self._encode_file(texts, self.files['texts'], self.var_names['texts'])

            # 3. Update db_authors.js
            if author_id and author_id != "unknown":
                authors = self._decode_file(self.files['authors'], self.var_names['authors'])
                if not isinstance(authors, dict):
                    authors = {}
                if author_id not in authors:
                    authors[author_id] = {
                        'uniqueIds': [author_name] if author_name else [],
                        'nicknames': [author_name] if author_name else [],
                        'followerCount': 0,
                        'heartCount': 0,
                        'videoCount': 0
                    }
                else:
                    uids = authors[author_id].setdefault('uniqueIds', [])
                    if author_name and author_name not in uids:
                        uids.append(author_name)
                self._encode_file(authors, self.files['authors'], self.var_names['authors'])

            # 4. Update 'downloaded' array in Category DB
            cat_lower = str(category).lower()
            if cat_lower in ('b', 'bookmarked', 'favorites', 'fav'):
                dbb = self._decode_file(self.files['bookmarked'], self.var_names['bookmarked'])
                if not isinstance(dbb, dict):
                    dbb = {
                        'officialList': [],
                        'downloaded': [],
                        'total': 0,
                        'numDisappeared': 0,
                        'lastRun': {'start': 0, 'finish': 0}
                    }
                dl_list = dbb.setdefault('downloaded', [])
                if video_id not in dl_list:
                    dl_list.append(video_id)
                dbb['total'] = max(dbb.get('total', 0), len(dl_list))
                self._encode_file(dbb, self.files['bookmarked'], self.var_names['bookmarked'])

            elif cat_lower in ('l', 'liked', 'likes', 'like'):
                dbl = self._decode_file(self.files['likes'], self.var_names['likes'])
                if not isinstance(dbl, dict):
                    dbl = {
                        'schemaVersion': 7,
                        'user': {'uid': '', 'id': '', 'uniqueId': '', 'nickname': ''},
                        'likes': {
                            'downloadStatus': 'unset',
                            'officialList': [],
                            'downloaded': [],
                            'total': 0,
                            'numDisappeared': 0,
                            'lastRun': {'start': 0, 'finish': 0}
                        }
                    }
                likes_obj = dbl.setdefault('likes', {})
                dl_list = likes_obj.setdefault('downloaded', [])
                if video_id not in dl_list:
                    dl_list.append(video_id)
                likes_obj['total'] = max(likes_obj.get('total', 0), len(dl_list))
                self._encode_file(dbl, self.files['likes'], self.var_names['likes'])

            elif cat_lower in ('following', 'f'):
                dbf = self._decode_file(self.files['following'], self.var_names['following'])
                if not isinstance(dbf, dict):
                    dbf = {
                        'officialAuthorList': [],
                        'started': [],
                        'notInterested': [],
                        'authorItems': {},
                        'lastRun': {}
                    }
                author_items = dbf.setdefault('authorItems', {})
                a_info = author_items.setdefault(author_id, {'inFolder': [], 'disappeared': []})
                in_folder = a_info.setdefault('inFolder', [])
                if video_id not in in_folder:
                    in_folder.append(video_id)
                self._encode_file(dbf, self.files['following'], self.var_names['following'])

            return True

        except Exception as e:
            print(f"❌ Lỗi register_downloaded_video ({video_id}): {e}")
            return False

    # ==================== FAILED VIDEOS QUEUE MANAGEMENT ====================
    def load_failed_queue(self, custom_path: Optional[str] = None) -> List[Dict]:
        """Đọc danh sách video lỗi (failed_videos.json)"""
        path = Path(custom_path) if custom_path else self.failed_json_path
        if not path.exists():
            # Check fallback in current project directory
            fallback = Path(__file__).parent.parent / "failed_videos.json"
            if fallback.exists():
                path = fallback
            else:
                return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"❌ Lỗi đọc failed queue ({path}): {e}")
            return []

    def save_failed_queue(self, queue: List[Dict], custom_path: Optional[str] = None) -> bool:
        """Ghi danh sách video lỗi đã cập nhật lại file"""
        path = Path(custom_path) if custom_path else self.failed_json_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(queue, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Lỗi lưu failed queue ({path}): {e}")
            return False

    def remove_from_failed_queue(self, video_id: str, custom_path: Optional[str] = None) -> bool:
        """Xóa một video đã tải thành công khỏi failed queue"""
        queue = self.load_failed_queue(custom_path)
        before = len(queue)
        queue = [item for item in queue if item.get("id") != video_id]
        if len(queue) != before:
            self.save_failed_queue(queue, custom_path)
            return True
        return False


def get_ext_sync(ext_data_path: str = r"D:\dlvideott\data\.appdata") -> ExtensionSync:
    """Factory function để tạo ExtensionSync instance"""
    return ExtensionSync(ext_data_path)