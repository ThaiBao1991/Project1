# -*- coding: utf-8 -*-
"""tools/deploy_pages.py — ĐẨY BẢN WEB LÊN GITHUB PAGES (để học trên điện thoại).

CÁCH LÀM (không cần Actions, không cần repo mới):
  1. Tạo/ cập nhật nhánh `gh-pages` chứa thư mục `web/` (index.html, script.js,
     style.css, manifest.json, data/<khóa>/…) — Pages phục vụ nhánh này.
  2. Bật Pages: source = branch `gh-pages`, path = `/`.
  3. In URL public (https://<user>.github.io/<repo>/).

DÙNG TOKEN: settings.json (AskCpl) hoặc $env:GITHUB_TOKEN.

Cách dùng:
  python tools/deploy_pages.py --dry-run     # xem sẽ đẩy gì
  python tools/deploy_pages.py               # đẩy thật
  python tools/deploy_pages.py --enable-only # chỉ bật Pages
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WEB = os.path.join(BASE, "web")
REPO = os.environ.get("GITHUB_REPO", "ThaiBao1991/Project1")
BRANCH = "gh-pages"


def _log(m):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {m}", flush=True)


def _token() -> str:
    """Token GitHub có quyền ghi — KHÔNG bật hộp thoại đăng nhập.

    Xem tools/gh_token.py: đọc env → file token cục bộ → settings.json →
    `git credential fill` (chế độ không tương tác, 15 giây).
    """
    from gh_token import get_token
    return get_token()


def _api(token: str):
    base = f"https://api.github.com/repos/{REPO}"
    H = {"Authorization": f"Bearer {token}",
         "Accept": "application/vnd.github+json",
         "User-Agent": "VocabularyApp-pages"}

    def req(path, data=None, method=None, raw=False):
        body = data if isinstance(data, (bytes, type(None))) else (
            json.dumps(data).encode() if data is not None else None)
        h = dict(H)
        if body is not None and not isinstance(data, bytes):
            h["Content-Type"] = "application/json"
        r = urllib.request.Request(base + path, data=body, headers=h, method=method)
        with urllib.request.urlopen(r, timeout=300) as resp:
            content = resp.read()
            if raw:
                return content
            return json.loads(content.decode() or "{}")
    return req


def enable_pages(token: str) -> bool:
    """Bật GitHub Pages từ nhánh gh-pages."""
    req = _api(token)
    try:
        cur = req("/pages")
        _log(f"Pages đang bật: source={cur.get('source')} url={cur.get('html_url')}")
        return True
    except urllib.error.HTTPError as e:
        if e.code != 404:
            _log(f"⚠ lỗi đọc Pages: {e}")
            return False
    try:
        res = req("/pages", {
            "source": {"branch": BRANCH, "path": "/"},
            "build_type": "legacy"}, method="POST")
        _log(f"✓ đã bật Pages: {res.get('html_url')}")
        return True
    except urllib.error.HTTPError as e:
        _log(f"⚠ không bật được Pages: {e.code} {e.read()[:200]}")
        return False


def deploy(token: str, dry: bool = False) -> bool:
    """Đẩy web/ lên nhánh gh-pages bằng git (không cần Actions)."""
    if not os.path.isfile(os.path.join(WEB, "index.html")):
        _log(f"⚠ không có {WEB}/index.html")
        return False
    tmp = tempfile.mkdtemp(prefix="vocab_pages_")
    try:
        # 1) checkout nhánh gh-pages (nếu có) vào thư mục tạm
        def git(*a):
            return subprocess.run(["git", "-C", tmp, *a], capture_output=True,
                                  text=True, timeout=900)
        r = git("init", "-q")
        r = git("remote", "add", "origin", f"https://github.com/{REPO}.git")
        r = git("fetch", "origin", BRANCH)
        if r.returncode == 0:
            git("checkout", "-q", "-B", BRANCH, "FETCH_HEAD")
            _log("đã lấy nhánh " + BRANCH + " hiện có")
        else:
            git("checkout", "-q", "--orphan", BRANCH)
            _log("tạo nhánh " + BRANCH + " mới")
        # 2) ĐỒNG BỘ TUYỆT ĐỐI: xoá hết file cũ (trừ .git) rồi copy web/
        #    ⇒ file đã bỏ không còn sót trên Pages.
        for item in os.listdir(tmp):
            if item == ".git":
                continue
            p = os.path.join(tmp, item)
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            else:
                try:
                    os.remove(p)
                except OSError:
                    pass
        for item in os.listdir(WEB):
            src = os.path.join(WEB, item)
            dst = os.path.join(tmp, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        # 3) commit + push
        git("add", "-A")
        st = git("status", "--porcelain")
        changed = bool((st.stdout or "").strip())
        if changed:
            git("-c", "user.email=app@local", "-c", "user.name=VocabularyApp",
                "commit", "-q", "-m",
                f"deploy: web + du lieu tinh cho dien thoai ({datetime.now():%Y-%m-%d %H:%M})")
        else:
            _log("không có thay đổi so với nhánh " + BRANCH)
        if dry:
            r = git("status", "--short")
            _log("DRY-RUN — chưa push. Thay đổi:")
            for line in (r.stdout or "").splitlines()[:15]:
                _log("   " + line[:120])
            return True
        if not changed:
            return True
        # push bằng token (không lưu token trong .git/config lâu dài)
        url = f"https://x-access-token:{token}@github.com/{REPO}.git"
        r = subprocess.run(["git", "-C", tmp, "push", url, f"{BRANCH}:{BRANCH}"],
                           capture_output=True, text=True, timeout=7200)
        if r.returncode == 0:
            _log("✓ đã push lên nhánh " + BRANCH)
            return True
        _log(f"⚠ push thất bại: {(r.stderr or '')[-300:]}")
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def wait_pages(token: str, timeout: int = 900) -> bool:
    """Chờ GitHub build xong trang Pages (status 'built')."""
    import time
    req = _api(token)
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            b = req("/pages/builds/latest")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                time.sleep(10)
                continue
            _log(f"⚠ đọc build: {e.code}")
            return False
        st = b.get("status")
        _log(f"Pages build: {st}")
        if st == "built":
            return True
        if st == "errored":
            return False
        time.sleep(15)
    return False


def main() -> int:
    global REPO
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--enable-only", action="store_true")
    ap.add_argument("--repo", default=REPO)
    args = ap.parse_args()
    REPO = args.repo

    tok = _token()
    if not tok:
        print("⚠ thiếu token GitHub")
        return 1

    if args.enable_only:
        return 0 if enable_pages(tok) else 1

    if not deploy(tok, args.dry_run):
        return 1
    if not args.dry_run:
        enable_pages(tok)
        wait_pages(tok)
        print(f"\n🌐 Trang học trên điện thoại: https://{REPO.split('/')[0]}.github.io/{REPO.split('/')[1]}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
