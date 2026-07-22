"""
gdrive_sync.py — Đồng bộ file MP3/MP4 lên Google Drive
- OAuth2: đăng nhập 1 lần, lưu token tự động
- Tự tạo cấu trúc thư mục: VocabularyApp/mp3/, VocabularyApp/mp4/
- Upload / Xóa file theo ID
- Trả về shareable file ID
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
CREDS_PATH = os.path.join(BASE_DIR, "credentials.json")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]

# Built-in OAuth client (Desktop app type - public client, an toàn cho local use)
# User sẽ cần tạo credentials.json từ Google Cloud Console (hướng dẫn trong app)
_BUILTIN_CLIENT = None  # Sẽ load từ credentials.json


def _safe_print(msg: str):
    """Print an toàn, bỏ qua ký tự không encode được trên Windows."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))


class GDriveSync:
    def __init__(self, log_fn=None):
        self.log = log_fn or _safe_print
        self._service = None

    # ─── Auth ──────────────────────────────────────────────────────────────────

    def is_authenticated(self) -> bool:
        """Kiểm tra đã đăng nhập chưa."""
        try:
            if self._service:
                return True
            if os.path.exists(TOKEN_PATH):
                self._load_service()
                return self._service is not None
        except Exception:
            pass
        return False

    def _load_service(self):
        """Load service từ token đã lưu."""
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_PATH, "w") as f:
                    f.write(creds.to_json())
            self._service = build("drive", "v3", credentials=creds)
        except Exception as e:
            self.log(f"⚠️ Lỗi load token: {e}")
            self._service = None

    def authenticate(self, log_fn=None) -> bool:
        """Mở trình duyệt để đăng nhập Google OAuth2."""
        if log_fn:
            self.log = log_fn
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            if not os.path.exists(CREDS_PATH):
                self.log("❌ Chưa có file credentials.json!")
                self.log("   → Xem hướng dẫn trong tab 'Cài Đặt > Google Drive'")
                return False

            self.log("🌐 Mở trình duyệt để đăng nhập Google...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)

            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())

            self._service = build("drive", "v3", credentials=creds)
            self.log("✅ Đăng nhập Google Drive thành công!")
            return True
        except Exception as e:
            self.log(f"❌ Lỗi đăng nhập: {e}")
            return False

    def logout(self):
        """Xóa token đã lưu."""
        self._service = None
        if os.path.exists(TOKEN_PATH):
            os.remove(TOKEN_PATH)

    # ─── Folder management ─────────────────────────────────────────────────────

    def _find_folder(self, name: str, parent_id: str = None) -> str | None:
        """Tìm folder theo tên."""
        q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            q += f" and '{parent_id}' in parents"
        result = self._service.files().list(
            q=q, fields="files(id,name)", pageSize=5
        ).execute()
        files = result.get("files", [])
        return files[0]["id"] if files else None

    def _create_folder(self, name: str, parent_id: str = None) -> str:
        """Tạo folder mới."""
        meta = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            meta["parents"] = [parent_id]
        folder = self._service.files().create(body=meta, fields="id").execute()
        return folder["id"]

    def _get_or_create_folder(self, name: str, parent_id: str = None) -> str:
        fid = self._find_folder(name, parent_id)
        if fid:
            return fid
        fid = self._create_folder(name, parent_id)
        self.log(f"📁 Tạo thư mục: {name}")
        return fid

    def ensure_folders(self, root_name: str = "VocabularyApp") -> dict:
        """Tạo cấu trúc thư mục nếu chưa có."""
        root_id = self._get_or_create_folder(root_name)
        mp3_id = self._get_or_create_folder("mp3", root_id)
        mp4_id = self._get_or_create_folder("mp4", root_id)
        return {"root": root_id, "mp3": mp3_id, "mp4": mp4_id}

    def make_public(self, file_id: str):
        """Cho phép link công khai (anyone can view)."""
        try:
            self._service.permissions().create(
                fileId=file_id,
                body={"role": "reader", "type": "anyone"},
            ).execute()
        except Exception:
            pass

    # ─── Upload ────────────────────────────────────────────────────────────────

    def upload_file(self, local_path: str, folder_id: str,
                    existing_id: str = None) -> str | None:
        """
        Upload file lên Google Drive.
        Nếu existing_id có → update file cũ (không tạo trùng).
        Trả về Google Drive file ID.
        """
        if not os.path.exists(local_path):
            self.log(f"⚠️ File không tồn tại: {local_path}")
            return None

        from googleapiclient.http import MediaFileUpload

        fname = os.path.basename(local_path)
        mime = "audio/mpeg" if local_path.lower().endswith(".mp3") else "video/mp4"

        try:
            if existing_id:
                # Update file cũ
                media = MediaFileUpload(local_path, mimetype=mime, resumable=True)
                updated = self._service.files().update(
                    fileId=existing_id, media_body=media
                ).execute()
                self.log(f"♻️ Cập nhật: {fname}")
                return existing_id
            else:
                # Upload mới
                meta = {"name": fname, "parents": [folder_id]}
                media = MediaFileUpload(local_path, mimetype=mime, resumable=True)
                file = self._service.files().create(
                    body=meta, media_body=media, fields="id"
                ).execute()
                file_id = file["id"]
                self.make_public(file_id)
                self.log(f"⬆️ Uploaded: {fname} (ID: {file_id[:20]}...)")
                return file_id
        except Exception as e:
            self.log(f"❌ Upload thất bại [{fname}]: {e}")
            return None

    # ─── Delete ────────────────────────────────────────────────────────────────

    def delete_file(self, file_id: str, name: str = "") -> bool:
        """Xóa file trên Google Drive theo ID."""
        if not file_id:
            return False
        try:
            self._service.files().delete(fileId=file_id).execute()
            self.log(f"🗑️ Đã xóa trên Drive: {name or file_id[:20]}")
            return True
        except Exception as e:
            self.log(f"⚠️ Không xóa được [{name}]: {e}")
            return False

    # ─── Full sync ─────────────────────────────────────────────────────────────

    def sync_vocab_media(self, vocab: dict, folders: dict) -> dict:
        """
        Upload MP3/MP4 của 1 từ vựng lên Drive.
        Trả về dict cập nhật: {'mp3_gdrive_id': ..., 'mp4_gdrive_id': ...}
        """
        updates = {}

        # MP3
        mp3_path = vocab.get("mp3_local_path", "")
        if mp3_path and os.path.exists(mp3_path):
            existing_mp3 = vocab.get("mp3_gdrive_id", "")
            fid = self.upload_file(mp3_path, folders["mp3"], existing_mp3 or None)
            if fid:
                updates["mp3_gdrive_id"] = fid

        # MP4
        mp4_path = vocab.get("mp4_local_path", "")
        if mp4_path and os.path.exists(mp4_path):
            existing_mp4 = vocab.get("mp4_gdrive_id", "")
            fid = self.upload_file(mp4_path, folders["mp4"], existing_mp4 or None)
            if fid:
                updates["mp4_gdrive_id"] = fid

        return updates

    def get_account_info(self) -> dict:
        """Lấy thông tin tài khoản Google đã đăng nhập."""
        try:
            about = self._service.about().get(fields="user,storageQuota").execute()
            user = about.get("user", {})
            quota = about.get("storageQuota", {})
            used = int(quota.get("usage", 0)) // (1024 * 1024)
            total = int(quota.get("limit", 0)) // (1024 * 1024)
            return {
                "name": user.get("displayName", ""),
                "email": user.get("emailAddress", ""),
                "used_mb": used,
                "total_mb": total,
            }
        except Exception:
            return {}
