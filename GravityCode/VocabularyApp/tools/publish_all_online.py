# -*- coding: utf-8 -*-
"""tools/publish_all_online.py — 1 LỆNH đưa TOÀN BỘ khóa lên bản học trên điện thoại.

Thứ tự (idempotent — chạy lại nhiều lần vẫn đúng):
  1. pack    : course.json → data/<slug>/index.json + day/<n>.json + media/mXX.zip
  2. upload  : đẩy media/mXX.zip lên GitHub Releases (bỏ qua asset đã có)
  3. pages   : copy dữ liệu tĩnh vào web/data/ (app + nội dung)
  4. deploy  : push nhánh `gh-pages` + bật GitHub Pages
  5. verify  : kiểm tra thật bằng HTTP (Pages + Release + giải nén zip)

Cách dùng:
  python tools/publish_all_online.py                # tất cả khóa
  python tools/publish_all_online.py --lang tiếng_nhật
  python tools/publish_all_online.py --skip-pack    # chỉ upload + deploy
  python tools/publish_all_online.py --tag-version v2   # khi media đã bù thêm
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CD = os.path.join(BASE, "data", "ai_courses")
PY = sys.executable


def log(m):
    print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def run(args: list[str], label: str, timeout: int = 21600) -> int:
    log(f"▶ {label}")
    try:
        p = subprocess.run([PY, "-X", "utf8", *args], cwd=BASE, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout)
        for line in (p.stdout or "").splitlines()[-4:]:
            if line.strip():
                log("   " + line.strip()[:150])
        if p.returncode != 0:
            log(f"   ⚠ {label} trả mã {p.returncode}")
            for line in (p.stderr or "").splitlines()[-5:]:
                if line.strip():
                    log("   ERR " + line.strip()[:150])
        return p.returncode
    except subprocess.TimeoutExpired:
        log(f"   ⏱ {label} quá thời gian")
        return -1


def slugs(lang: str = "") -> list[str]:
    if lang:
        return [lang]
    return [s for s in sorted(os.listdir(CD))
            if os.path.isfile(os.path.join(CD, s, "course.json"))]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="")
    ap.add_argument("--skip-pack", action="store_true")
    ap.add_argument("--skip-upload", action="store_true")
    ap.add_argument("--skip-deploy", action="store_true")
    ap.add_argument("--tag-version", default="v1",
                    help="v1, v2… (đổi khi media đã bù thêm — asset không trùng tên)")
    args = ap.parse_args()

    t0 = time.time()
    target = slugs(args.lang)
    log(f"khóa: {len(target)} — {', '.join(target)}")

    if not args.skip_pack:
        for s in target:
            run(["tools/publish_online.py", "--pack", "--lang", s], f"pack {s}")

    if not args.skip_upload:
        for s in target:
            tag = f"data-{_ascii(s)}-{args.tag_version}"
            run(["tools/publish_online.py", "--upload", "--lang", s, "--tag", tag],
                f"upload {s} ({tag})")

    if not args.skip_deploy:
        run(["tools/publish_online.py", "--pages"], "copy web/data (Pages)")
        rc = run(["tools/deploy_pages.py"], "deploy gh-pages + bật Pages", timeout=14400)
        if rc != 0:
            log("⚠ deploy lỗi — bỏ qua bước verify")
            return 1
        run(["tools/verify_online.py", "--slug", target[0]], "verify online")

    log(f"✅ XONG sau {(time.time()-t0)/60:.1f} phút")
    user, name = _repo().split("/")
    log(f"🌐 https://{user}.github.io/{name}/")
    return 0


def _ascii(s: str) -> str:
    import re
    import unicodedata
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z0-9-]", "", s.replace("_", "-").replace(" ", "-")).lower()


def _repo() -> str:
    return os.environ.get("GITHUB_REPO", "ThaiBao1991/Project1")


if __name__ == "__main__":
    sys.exit(main())
