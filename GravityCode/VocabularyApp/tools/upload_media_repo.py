# -*- coding: utf-8 -*-
"""tools/upload_media_repo.py — ĐƯA GÓI MEDIA LÊN REPO DỮ LIỆU (để tải qua raw.githubusercontent.com).

VÌ SAO CẦN REPO RIÊNG (đo thật 17/11/2026):
  • `github.com/<repo>/releases/download/<tag>/m01.zip`  → KHÔNG có CORS
    ⇒ fetch() từ trình duyệt bị chặn.
  • `api.github.com/.../releases/assets/<id>` → 302 sang
    `release-assets.githubusercontent.com` — host này CŨNG KHÔNG có CORS
    ⇒ vẫn bị chặn.
  • `raw.githubusercontent.com` → **CÓ CORS** (đo thật: fetch đọc được bytes)
    ⇒ đây là kênh tải media đúng cho điện thoại.

CẤU TRÚC repo dữ liệu (mặc định `ThaiBao1991/VocabularyData`):
    media/index.json          { "<slug>": { "dir": "tieng-nhat", "months": 85 } }
    media/tieng-nhat/m01.zip … m85.zip
    media/tieng-trung/m01.zip …
    …

Cách dùng:
  python tools/upload_media_repo.py                 # tất cả khóa đã pack
  python tools/upload_media_repo.py --lang tiếng_nhật
  python tools/upload_media_repo.py --repo ThaiBao1991/VocabularyData
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import unicodedata
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = os.path.join(BASE, "publish")
WORK = os.path.join(OUT, "_repo")
DEFAULT_REPO = os.environ.get("MEDIA_REPO", "ThaiBao1991/VocabularyData")


def log(m):
    print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def ascii_dir(slug: str) -> str:
    s = (slug or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("_", "-").replace(" ", "-")
    s = "".join(c for c in s if c.isalnum() or c == "-").strip("-").lower()
    return s or "lang"


def token() -> str:
    """Token GitHub — KHÔNG bật hộp thoại đăng nhập (xem tools/gh_token.py)."""
    from gh_token import get_token
    return get_token()


def api_req(url: str, tok: str, data=None, method=None):
    import urllib.request
    body = json.dumps(data).encode() if data is not None else None
    h = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
         "User-Agent": "VocabularyApp-media"}
    if body:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read().decode() or "{}")


def ensure_repo(repo: str, tok: str) -> bool:
    import urllib.error
    try:
        api_req(f"https://api.github.com/repos/{repo}", tok)
        log(f"repo {repo} đã có")
        return True
    except urllib.error.HTTPError as e:
        if e.code != 404:
            log(f"⚠ kiểm tra repo: {e.code}")
            return False
    try:
        j = api_req("https://api.github.com/user/repos", tok, {
            "name": repo.split("/")[1],
            "description": "Dữ liệu media của VocabularyApp (gói 30 ngày) — tải qua raw.githubusercontent.com",
            "private": False, "auto_init": True,
        }, method="POST")
        log(f"✓ đã tạo repo {j.get('full_name')}")
        time.sleep(3)
        return True
    except Exception as e:
        log(f"⚠ không tạo được repo: {e}")
        return False


def git(*args, timeout=7200):
    return subprocess.run(["git", "-C", WORK, *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)


def prepare(repo: str, tok: str) -> bool:
    if os.path.isdir(WORK):
        shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK, exist_ok=True)
    git("init", "-q", "-b", "main")
    url = f"https://x-access-token:{tok}@github.com/{repo}.git"
    git("remote", "add", "origin", url)
    r = git("fetch", "origin", "main", timeout=1800)
    if r.returncode == 0:
        git("checkout", "-q", "-B", "main", "FETCH_HEAD")
        log("đã lấy repo dữ liệu hiện có")
    else:
        log("repo dữ liệu còn rỗng — tạo mới")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--lang", default="")
    ap.add_argument("--keep-work", action="store_true")
    args = ap.parse_args()

    tok = token()
    if not tok:
        log("⚠ thiếu token GitHub")
        return 1
    if not ensure_repo(args.repo, tok):
        return 1
    prepare(args.repo, tok)

    slugs = ([args.lang] if args.lang else
             [s for s in sorted(os.listdir(OUT))
              if os.path.isdir(os.path.join(OUT, s, "media"))])
    if not slugs:
        log("⚠ chưa có gói nào trong publish/ — chạy --pack trước")
        return 1

    idx_path = os.path.join(WORK, "media", "index.json")
    index = {}
    if os.path.isfile(idx_path):
        try:
            with open(idx_path, encoding="utf-8") as f:
                index = json.load(f)
        except Exception:
            index = {}

    for slug in slugs:
        src = os.path.join(OUT, slug, "media")
        if not os.path.isdir(src):
            log(f"⚠ {slug}: chưa pack")
            continue
        d = ascii_dir(slug)
        dst = os.path.join(WORK, "media", d)
        os.makedirs(dst, exist_ok=True)
        n = 0
        total = 0
        for fn in sorted(os.listdir(src)):
            fp = os.path.join(src, fn)
            if not os.path.isfile(fp) or os.path.getsize(fp) <= 1024:
                continue          # bỏ gói rỗng
            shutil.copy2(fp, os.path.join(dst, fn))
            n += 1
            total += os.path.getsize(fp)
        index[slug] = {"dir": d, "months": n}
        os.makedirs(os.path.join(WORK, "media"), exist_ok=True)
        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=1, sort_keys=True)

        git("add", "-A")
        st = git("status", "--porcelain")
        if not (st.stdout or "").strip():
            log(f"{slug}: không có thay đổi")
            continue
        git("-c", "user.email=app@local", "-c", "user.name=VocabularyApp",
            "commit", "-q", "-m", f"media: {slug} ({n} gói, {total/1048576:.0f} MB)")
        t0 = time.time()
        r = git("push", "origin", "main", timeout=21600)
        if r.returncode != 0:
            log(f"⚠ push {slug} lỗi: {(r.stderr or '')[-300:]}")
            continue
        log(f"✓ {slug}: {n} gói / {total/1048576:.0f} MB — push {time.time()-t0:.0f}s")

    if not args.keep_work:
        shutil.rmtree(WORK, ignore_errors=True)
    log(f"✅ xong. Dữ liệu tại: https://raw.githubusercontent.com/{args.repo}/main/media/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
