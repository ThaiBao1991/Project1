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
        if os.path.exists(DATA_DIR):
            json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
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

        # 3. Upload cac file web len root
        for wfile in ["index.html", "style.css", "script.js"]:
            wpath = os.path.join(WEB_DIR, wfile)
            if os.path.exists(wpath):
                self.upload_file(wpath, wfile, f"update: {wfile}", log_fn)
            else:
                if wfile == "index.html":
                    log_fn(f"WARN: web/{wfile} khong tim thay!")

        # manifest.json (PWA)
        mf = os.path.join(WEB_DIR, "manifest.json")
        if os.path.exists(mf):
            self.upload_file(mf, "manifest.json", "update: manifest", log_fn)

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
