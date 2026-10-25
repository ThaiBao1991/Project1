"""
github_sync.py -- Dong bo du lieu len GitHub
- Tu tao repo neu chua co
- Upload data/*.json va web files (index.html, css, js)
- Bat GitHub Pages
"""

import os
import json
import base64
import shutil
import requests
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")
DATA_DIR = os.path.join(BASE_DIR, "data")


class GitHubSync:
    def __init__(self, username: str, token: str, repo_name: str, branch: str = "main"):
        self.username = username.strip()
        self.token = token.strip()
        self.repo_name = repo_name.strip()
        self.branch = branch
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.api = "https://api.github.com"

    def _repo_url(self, path=""):
        return f"{self.api}/repos/{self.username}/{self.repo_name}{path}"

    # ─── Repo management ───────────────────────────────────────────────────────

    def check_or_create_repo(self, log_fn=print) -> bool:
        """Kiểm tra repo tồn tại, tự tạo nếu chưa có."""
        r = requests.get(self._repo_url(), headers=self.headers, timeout=10)
        if r.status_code == 200:
            log_fn(f"✅ Repo '{self.repo_name}' đã tồn tại")
            return True
        if r.status_code == 404:
            log_fn(f"📦 Tạo repo mới: {self.repo_name}...")
            payload = {
                "name": self.repo_name,
                "description": "📚 VocabularyApp — Quản lý học từ vựng cá nhân",
                "private": False,
                "auto_init": True,
            }
            r2 = requests.post(f"{self.api}/user/repos", headers=self.headers,
                               json=payload, timeout=15)
            if r2.status_code in (200, 201):
                log_fn(f"✅ Tạo repo thành công!")
                return True
            log_fn(f"❌ Tạo repo thất bại: {r2.text}")
            return False
        log_fn(f"❌ Lỗi kiểm tra repo: {r.status_code} — {r.text}")
        return False

    def enable_pages(self, log_fn=print):
        """Bật GitHub Pages từ branch main."""
        payload = {"source": {"branch": self.branch, "path": "/"}}
        r = requests.post(self._repo_url("/pages"), headers=self.headers,
                          json=payload, timeout=10)
        if r.status_code in (200, 201):
            log_fn("🌐 GitHub Pages đã được bật!")
        elif r.status_code == 409:
            log_fn("🌐 GitHub Pages đã được bật sẵn")
        else:
            log_fn(f"⚠️ GitHub Pages: {r.status_code}")

    def get_pages_url(self) -> str:
        r = requests.get(self._repo_url("/pages"), headers=self.headers, timeout=10)
        if r.status_code == 200:
            return r.json().get("html_url", "")
        return f"https://{self.username}.github.io/{self.repo_name}/"

    # ─── File upload ───────────────────────────────────────────────────────────

    def _get_file_sha(self, path: str) -> str | None:
        """Lấy SHA của file (cần để update)."""
        r = requests.get(self._repo_url(f"/contents/{path}"),
                         headers=self.headers, timeout=10)
        if r.status_code == 200:
            return r.json().get("sha")
        return None

    def upload_file(self, file_path: str, repo_path: str,
                    commit_msg: str = None, log_fn=print) -> bool:
        """Upload 1 file lên GitHub repo."""
        if not os.path.exists(file_path):
            log_fn(f"⚠️ File không tồn tại: {file_path}")
            return False

        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")

        sha = self._get_file_sha(repo_path)
        payload = {
            "message": commit_msg or f"update: {repo_path}",
            "content": content,
            "branch": self.branch,
        }
        if sha:
            payload["sha"] = sha

        r = requests.put(self._repo_url(f"/contents/{repo_path}"),
                         headers=self.headers, json=payload, timeout=30)
        if r.status_code in (200, 201):
            log_fn(f"⬆️ Uploaded: {repo_path}")
            return True
        log_fn(f"❌ Upload thất bại [{repo_path}]: {r.status_code} {r.text[:200]}")
        return False

    def upload_content(self, content: str, repo_path: str,
                       commit_msg: str = None, log_fn=print) -> bool:
        """Upload nội dung string lên GitHub repo."""
        encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        sha = self._get_file_sha(repo_path)
        payload = {
            "message": commit_msg or f"update: {repo_path}",
            "content": encoded,
            "branch": self.branch,
        }
        if sha:
            payload["sha"] = sha

        r = requests.put(self._repo_url(f"/contents/{repo_path}"),
                         headers=self.headers, json=payload, timeout=30)
        if r.status_code in (200, 201):
            log_fn(f"⬆️ Uploaded: {repo_path}")
            return True
        log_fn(f"❌ Upload thất bại [{repo_path}]: {r.status_code} {r.text[:200]}")
        return False

    # ─── Full Sync ─────────────────────────────────────────────────────────────

    def full_sync(self, log_fn=print) -> bool:
        """Sync: repo check -> data/*.json -> index.html, style.css, script.js -> GitHub Pages."""
        log_fn("-" * 50)
        log_fn("Bat dau dong bo GitHub...")

        # 1. Kiem tra / tao repo
        if not self.check_or_create_repo(log_fn):
            return False

        # 2. Upload tat ca cac file JSON trong folder data/
        #    CHỈ upload file NGÔN NGỮ (data/<slug>.json).
        #    Loại trừ các file hệ thống (index.json, language_profiles_cache.json)
        #    để không bị coi nhầm là 1 "ngôn ngữ" và không đẩy cache nội bộ lên web.
        _SYSTEM_JSON = {"index.json", "language_profiles_cache.json",
                        "blocked_accounts.json", "blocked_keys.json",
                        "tts_quota.json", "tts_voices.json", "evidence_cache.json",
                        "image_cache.json"}
        # File hệ thống (bắt đầu bằng "_") cũng loại — ví dụ _jobs.json
        def _is_system_file(fname: str) -> bool:
            return fname in _SYSTEM_JSON or fname.startswith("_")
        if os.path.exists(DATA_DIR):
            json_files = [
                p for p in glob.glob(os.path.join(DATA_DIR, "*.json"))
                if not _is_system_file(os.path.basename(p))
            ]
            if not json_files:
                log_fn("Khong co du lieu JSON nao trong data/")
            else:
                for jpath in json_files:
                    fname = os.path.basename(jpath)
                    # Upload file json len thu muc data/ tren github
                    self.upload_file(jpath, f"data/{fname}", f"update: {fname} data", log_fn)

                # tao index.json liet ke cac ngon ngu co san
                available_langs = [os.path.basename(p)[:-5] for p in json_files]
                self.upload_content(json.dumps({"languages": available_langs}), "data/index.json", "update: lang list", log_fn)

            # 2b. Upload khoa hoc AI (data/ai_courses/<ngon_ngu>/*.json)
            #     BUG ĐÃ SỬA (L-O): bỏ qua thư mục checkpoint "_pipeline" và
            #     file hệ thống "_jobs.json" — đây là trạng thái nội bộ, không
            #     được đẩy lên repo public.
            courses_root = os.path.join(DATA_DIR, "ai_courses")
            if os.path.isdir(courses_root):
                uploaded = 0
                for root, _dirs, files in os.walk(courses_root):
                    rel_dir = os.path.relpath(root, DATA_DIR).replace(os.sep, "/")
                    if "_pipeline" in rel_dir.split("/"):
                        continue
                    for fname in sorted(files):
                        if not fname.endswith(".json"):
                            continue
                        if fname.startswith("_"):
                            continue
                        local = os.path.join(root, fname)
                        repo_path = f"data/{rel_dir}/{fname}"
                        if self.upload_file(local, repo_path, f"update: {repo_path}", log_fn):
                            uploaded += 1
                if uploaded:
                    log_fn(f"🎓 Đã upload {uploaded} file khóa học AI.")

        # 2c. Upload MEDIA (ảnh minh họa + âm thanh) — CHỈ ngôn ngữ được chọn
        #     Cấu hình: settings.json -> media.sync_langs (rỗng = không sync media)
        media_root = os.path.join(DATA_DIR, "media")
        if os.path.isdir(media_root):
            try:
                from settings import load_settings
                sync_langs = (load_settings().get("media", {}) or {}).get("sync_langs") or []
            except Exception:
                sync_langs = []
            uploaded_media = 0
            if sync_langs:
                for slug in sync_langs:
                    src_dir = os.path.join(media_root, slug)
                    if not os.path.isdir(src_dir):
                        log_fn(f"⚠ Không có thư mục media: {slug}")
                        continue
                    files = []
                    for root, _dirs, fnames in os.walk(src_dir):
                        for fn in fnames:
                            files.append(os.path.join(root, fn))
                    for fp in files:
                        rel = os.path.relpath(fp, media_root).replace(os.sep, "/")
                        if self.upload_file(fp, f"data/media/{rel}",
                                           f"update: data/media/{rel}", log_fn):
                            uploaded_media += 1
                    log_fn(f"📷 Đã sync media cho '{slug}' ({len(files)} file).")
                # manifest media
                mi = os.path.join(media_root, "index.json")
                if os.path.isfile(mi):
                    self.upload_file(mi, "data/media/index.json",
                                     "update: data/media/index.json", log_fn)
                if uploaded_media:
                    log_fn(f"📷 Tổng cộng {uploaded_media} file media đã upload.")
            else:
                log_fn("📷 Bỏ qua sync media (chưa chọn ngôn ngữ nào trong media.sync_langs).")

        # 3. Upload cac file web len root
        for wfile in ["index.html", "style.css", "script.js"]:
            wpath = os.path.join(WEB_DIR, wfile)
            if os.path.exists(wpath):
                self.upload_file(wpath, wfile, f"update: {wfile}", log_fn)
            else:
                if wfile == "index.html":
                    log_fn(f"WARN: web/{wfile} khong tim thay!")

        # manifest.json (PWA) + icons
        mf = os.path.join(WEB_DIR, "manifest.json")
        if os.path.exists(mf):
            self.upload_file(mf, "manifest.json", "update: manifest", log_fn)
        icon_dir = os.path.join(WEB_DIR, "icons")
        if os.path.isdir(icon_dir):
            for ifile in sorted(os.listdir(icon_dir)):
                if ifile.lower().endswith((".png", ".webp", ".svg", ".ico")):
                    self.upload_file(os.path.join(icon_dir, ifile),
                                     f"icons/{ifile}", f"update: icons/{ifile}", log_fn)

        # 4. README.md tro toi web URL
        pages_url = self.get_pages_url()
        readme = (
            "# VocabularyApp\n\n"
            "Quan ly hoc tu vung da ngon ngu.\n\n"
            f"**Web App:** [{pages_url}]({pages_url})\n\n"
            "Truy cap link de on tap tu vung bang flashcards tren dien thoai.\n"
        )
        self.upload_content(readme, "README.md", "update: README", log_fn)

        # 5. Bat GitHub Pages
        self.enable_pages(log_fn)

        log_fn("")
        log_fn("Dong bo GitHub hoan tat!")
        log_fn("Web URL: " + pages_url)
        log_fn("-" * 50)
        return True


    def validate_token(self) -> tuple[bool, str]:
        """Kiểm tra token có hợp lệ không."""
        r = requests.get(f"{self.api}/user", headers=self.headers, timeout=10)
        if r.status_code == 200:
            name = r.json().get("name") or r.json().get("login")
            return True, f"✅ Đăng nhập thành công: {name}"
        return False, f"❌ Token không hợp lệ (HTTP {r.status_code})"
