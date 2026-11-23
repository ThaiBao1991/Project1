# -*- coding: utf-8 -*-
"""tools/upload_media_api.py — ĐẨY GÓI MEDIA LÊN REPO DỮ LIỆU **KHÔNG CLONE**.

VÌ SAO CẦN TOOL NÀY (đo thật 17/11/2026):
    `upload_media_repo.py` clone toàn bộ repo media rồi copy zip vào worktree.
    Khi repo media đủ 8 khóa (~11 GB) thì mỗi lần upload cần thêm ~11 GB đĩa
    ⇒ máy chỉ còn ~14 GB sẽ KHÔNG đủ. Tool này dùng GitHub **Git Data API**:
      • đọc tree hiện có 1 lần (1 request),
      • so SHA git-blob của từng zip (tính tại máy) ⇒ chỉ đẩy gói MỚI/ĐỔI,
      • tạo blob → tree → commit → cập nhật ref (1 commit/khóa),
      • không clone, không worktree, không tốn đĩa.

Cấu trúc repo dữ liệu (giống upload_media_repo.py):
    media/index.json          { "<slug>": { "dir": "tieng-nhat", "months": 85 } }
    media/tieng-nhat/m01.zip … m85.zip

Cách dùng:
  python tools/upload_media_api.py --dry-run          # xem sẽ đẩy gì
  python tools/upload_media_api.py --lang tiếng_nhật
  python tools/upload_media_api.py                    # tất cả khóa đã pack
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = os.path.join(BASE, "publish")
DEFAULT_REPO = os.environ.get("MEDIA_REPO", "ThaiBao1991/VocabularyData")
API = "https://api.github.com"


def log(m):
    print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def ascii_dir(slug: str) -> str:
    s = (slug or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("_", "-").replace(" ", "-")
    s = "".join(c for c in s if c.isalnum() or c == "-").strip("-").lower()
    return s or "lang"


def git_blob_sha(path: str) -> str:
    """SHA-1 git blob của file trên đĩa (khớp `sha` GitHub trả về)."""
    h = hashlib.sha1()
    size = os.path.getsize(path)
    h.update(f"blob {size}\0".encode("utf-8"))
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class Api:
    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.token = token

    def req(self, method: str, path: str, data=None, timeout=180):
        body = json.dumps(data).encode() if data is not None else None
        h = {"Authorization": f"Bearer {self.token}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "VocabularyApp-media-api"}
        if body:
            h["Content-Type"] = "application/json"
        url = path if path.startswith("http") else f"{API}{path}"
        r = urllib.request.Request(url, data=body, headers=h, method=method)
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode() or "{}"
            return json.loads(raw)

    def get(self, path, timeout=180):
        return self.req("GET", path, timeout=timeout)

    def post(self, path, data, timeout=600):
        return self.req("POST", path, data, timeout=timeout)

    def patch(self, path, data, timeout=180):
        return self.req("PATCH", path, data, timeout=timeout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--lang", action="append", default=[],
                    help="giới hạn khóa (lặp lại được)")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    from gh_token import get_token
    tok = get_token()
    if not tok:
        log("⚠ thiếu token GitHub (xem tools/gh_token.py)")
        return 1
    api = Api(args.repo, tok)

    if args.lang:
        slugs = list(dict.fromkeys(args.lang))
    elif os.path.isdir(OUT):
        slugs = [s for s in sorted(os.listdir(OUT))
                 if os.path.isdir(os.path.join(OUT, s, "media"))]
    else:
        slugs = []
    if not slugs:
        log("⚠ chưa có gói nào trong publish/ — chạy --pack trước")
        return 1

    # 1) ref + tree hiện có (1 lần)
    try:
        ref = api.get(f"/repos/{args.repo}/git/ref/heads/{args.branch}")
        head = ref["object"]["sha"]
        commit = api.get(f"/repos/{args.repo}/git/commits/{head}")
        base_tree = commit["tree"]["sha"]
        tree = api.get(f"/repos/{args.repo}/git/trees/{base_tree}?recursive=1")
        remote = {e["path"]: e["sha"] for e in tree.get("tree") or []
                  if e.get("type") == "blob"}
        log(f"repo {args.repo}@{args.branch}: {len(remote)} file · head {head[:8]}")
    except urllib.error.HTTPError as e:
        log(f"⚠ không đọc được repo: HTTP {e.code} {e.reason}")
        return 1

    # 2) index hiện có
    index = {}
    if "media/index.json" in remote:
        try:
            blob = api.get(f"/repos/{args.repo}/git/blobs/{remote['media/index.json']}")
            index = json.loads(base64.b64decode(blob["content"]).decode("utf-8"))
        except Exception as e:
            log(f"⚠ không đọc được media/index.json: {e}")
            index = {}

    changed = 0
    for slug in slugs:
        src = os.path.join(OUT, slug, "media")
        if not os.path.isdir(src):
            log(f"⚠ {slug}: chưa pack")
            continue
        d = ascii_dir(slug)
        entries = []
        n_new = n_same = 0
        total = 0
        for fn in sorted(os.listdir(src)):
            fp = os.path.join(src, fn)
            if not os.path.isfile(fp) or os.path.getsize(fp) <= 1024:
                continue
            path = f"media/{d}/{fn}"
            sha = git_blob_sha(fp)
            total += os.path.getsize(fp)
            if remote.get(path) == sha:
                n_same += 1
                continue
            n_new += 1
            entries.append({"path": path, "mode": "100644", "type": "blob",
                            "sha": sha, "_file": fp})
        log(f"{slug}: {n_new} gói mới/đổi · {n_same} gói đã đúng · "
            f"{total/1048576:.0f} MB")
        if not n_new:
            index[slug] = {"dir": d, "months": n_same}
            continue
        if args.dry_run:
            changed += n_new
            continue

        # 3) upload blob (chỉ gói mới/đổi)
        t0 = time.time()
        blobs = []
        for i, e in enumerate(entries, 1):
            with open(e["_file"], "rb") as f:
                content = base64.b64encode(f.read()).decode("ascii")
            r = api.post(f"/repos/{args.repo}/git/blobs",
                         {"content": content, "encoding": "base64"})
            blobs.append({"path": e["path"], "mode": "100644",
                          "type": "blob", "sha": r["sha"]})
            if i % 10 == 0 or i == len(entries):
                log(f"   blob {i}/{len(entries)} · {time.time()-t0:.0f}s")
        index[slug] = {"dir": d, "months": n_same + n_new}
        changed += n_new

        # 4) tree + commit + ref
        index_blob = api.post(f"/repos/{args.repo}/git/blobs", {
            "content": base64.b64encode(json.dumps(
                index, ensure_ascii=False, indent=1, sort_keys=True
            ).encode("utf-8")).decode("ascii"),
            "encoding": "base64"})
        blobs.append({"path": "media/index.json", "mode": "100644",
                      "type": "blob", "sha": index_blob["sha"]})
        new_tree = api.post(f"/repos/{args.repo}/git/trees",
                            {"base_tree": base_tree, "tree": blobs})
        new_commit = api.post(f"/repos/{args.repo}/git/commits", {
            "message": f"media: {slug} ({n_same + n_new} gói, "
                       f"{total/1048576:.0f} MB)",
            "tree": new_tree["sha"], "parents": [head]})
        api.patch(f"/repos/{args.repo}/git/refs/heads/{args.branch}",
                  {"sha": new_commit["sha"], "force": False})
        head = new_commit["sha"]
        base_tree = new_tree["sha"]
        log(f"✓ {slug}: đã đẩy {n_new} gói trong {time.time()-t0:.0f}s "
            f"(commit {head[:8]})")

    if args.dry_run:
        log(f"[dry-run] sẽ đẩy {changed} gói")
    else:
        log(f"✅ xong {len(slugs)} khóa · {changed} gói mới/đổi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
