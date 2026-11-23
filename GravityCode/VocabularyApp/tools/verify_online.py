# -*- coding: utf-8 -*-
"""tools/verify_online.py — KIỂM TRA BẢN DEPLOY ONLINE (điện thoại).

Kiểm tra 4 tầng:
  1. Pages: https://<user>.github.io/<repo>/  trả 200 + có manifest.json
  2. Dữ liệu tĩnh: data/index.json (danh sách khóa) + data/<slug>/index.json
  3. Nội dung ngày: data/<slug>/day/0001.json tải được, đủ từ + media_map
  4. Release: gói media .zip tồn tại + tải được + giải nén ra đúng file

Chạy:
  python tools/verify_online.py
  python tools/verify_online.py --slug tiếng_nhật --day 1
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import urllib.parse
import urllib.request
import zipfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = os.environ.get("GITHUB_REPO", "ThaiBao1991/Project1")
USER, NAME = REPO.split("/")
PAGES = f"https://{USER}.github.io/{NAME}"
MEDIA_REPO = os.environ.get("MEDIA_REPO", "ThaiBao1991/VocabularyData")
RAW_MEDIA = f"https://raw.githubusercontent.com/{MEDIA_REPO}/main/media"


def _get(url, timeout=60, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "VocabularyApp-verify"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if raw else data.decode("utf-8", "replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="tiếng_nhật")
    ap.add_argument("--day", type=int, default=1)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    ok = True
    res = []

    def ck(name, cond, detail=""):
        nonlocal ok
        res.append((name, bool(cond), detail))
        if not cond:
            ok = False

    # 1) Pages
    try:
        html = _get(PAGES + "/")
        ck("Pages trả 200", True, f"{len(html)} byte")
        ck("Pages có manifest.json (PWA)", "manifest.json" in html)
    except Exception as e:
        ck("Pages trả 200", False, f"{type(e).__name__}: {e}")

    # 2) data/index.json
    try:
        j = json.loads(_get(PAGES + "/data/index.json"))
        langs = j.get("languages") or []
        ck("data/index.json có khóa học", len(langs) > 0, f"{langs}")
    except Exception as e:
        ck("data/index.json có khóa học", False, f"{type(e).__name__}: {e}")
        langs = []

    slug = args.slug
    q = urllib.parse.quote(slug)

    # 3) index + 1 ngày
    try:
        idx = json.loads(_get(PAGES + f"/data/{q}/index.json"))
        ck(f"data/{slug}/index.json", len(idx.get("days") or []) > 0,
           f"{len(idx.get('days') or [])} ngày")
        mk = (idx.get("days") or [{}])[0].get("month") or "01"
    except Exception as e:
        ck(f"data/{slug}/index.json", False, f"{type(e).__name__}: {e}")
        mk = "01"
    try:
        dj = json.loads(_get(PAGES + f"/data/{q}/day/{args.day:04d}.json"))
        ck(f"data/{slug}/day/{args.day:04d}.json",
           len(dj.get("vocab") or []) > 0,
           f"{len(dj.get('vocab') or [])} từ, {len(dj.get('media_map') or {})} media ref")
    except Exception as e:
        ck(f"data/{slug}/day/{args.day:04d}.json", False, f"{type(e).__name__}: {e}")

    # 4) Media: repo dữ liệu qua raw.githubusercontent.com (kênh CHÍNH)
    #    (raw CÓ CORS — xem docs/ONLINE_PHONE.md §3)
    try:
        mi = json.loads(_get(f"{RAW_MEDIA}/index.json"))
        info = mi.get(slug) or {}
        ck(f"raw media index có '{slug}'", bool(info), f"dir={info.get('dir')} months={info.get('months')}")
        d = info.get("dir")
        if d:
            name = f"m{mk}.zip"
            url = f"{RAW_MEDIA}/{d}/{name}"
            try:
                blob = _get(url, timeout=300, raw=True)
                zf = zipfile.ZipFile(io.BytesIO(blob))
                names = zf.namelist()
                ck(f"raw {name} tải+giải nén được", len(names) > 0,
                   f"{len(blob)/1024/1024:.1f} MB, {len(names)} file")
                ck(f"raw {name} chứa media ngày {args.day}",
                   any(f"d{args.day:04d}/" in n for n in names))
            except Exception as e:
                ck(f"raw {name} tải+giải nén được", False, f"{type(e).__name__}: {e}")
    except Exception as e:
        ck("raw media index", False, f"{type(e).__name__}: {e}")

    # 4b) Fallback: GitHub Releases (chỉ để biết còn dùng được không)
    try:
        from publish_online import release_tag
        tag = args.tag or release_tag(slug)
    except Exception:
        tag = args.tag or f"data-{slug}-v1"
    try:
        hdr = {"User-Agent": "VocabularyApp-verify",
               "Accept": "application/vnd.github+json"}
        try:
            from gh_token import get_token
            tok = get_token()
            if tok:
                hdr["Authorization"] = f"Bearer {tok}"
        except Exception:
            pass
        rq = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/releases/tags/{urllib.parse.quote(tag)}",
            headers=hdr)
        with urllib.request.urlopen(rq, timeout=60) as r:
            rel = json.loads(r.read().decode())
        assets = rel.get("assets") or []
        ck(f"release '{tag}' (fallback) tồn tại", len(assets) > 0, f"{len(assets)} asset")
    except Exception as e:
        ck(f"release '{tag}' (fallback)", False, f"{type(e).__name__}: {e}")

    print(f"\nKIỂM TRA BẢN ONLINE {PAGES}")
    for name, passed, detail in res:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))
    print(f"→ {sum(1 for r in res if r[1])}/{len(res)} PASS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
