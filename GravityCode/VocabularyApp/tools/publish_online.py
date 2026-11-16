# -*- coding: utf-8 -*-
"""tools/publish_online.py — ĐÓNG GÓI & ĐẨY DỮ LIỆU LÊN GITHUB để học trên ĐIỆN THOẠI.

BỐI CẢNH (17/11): dữ liệu hiện tại quá lớn để push lên repo:
    course.json  8 × ~55 MB  = 443 MB   (>50 MB ⇒ cảnh báo)
    media/       211.549 file = 2,6 GB  (repo >5 GB ⇒ GitHub cảnh báo)
    manifest     103 MB                  (>100 MB ⇒ BỊ CHẶN push)
⇒ Không thể push thẳng. Chiến lược **2 tầng**:

  TẦNG 1 — NỘI DUNG (nhỏ, tải nhanh) → **GitHub Pages** (repo hiện tại)
      web/data/<slug>/index.json          ~ danh sách 2.520 ngày + metadata
      web/data/<slug>/day/<n>.json        nội dung 1 ngày (~25 KB)
      ⇒ 8 khóa × 2.520 × 25 KB ≈ 500 MB (dưới giới hạn Pages 1 GB)

  TẦNG 2 — MEDIA (nặng, tải theo nhu cầu) → **GitHub Releases**
      1 asset .zip cho mỗi (khóa × tháng) ≈ 11 MB
      ⇒ 8 khóa × 84 tháng = 672 asset (1 release/khóa ⇒ 84 asset/release)
      Điện thoại tải gói tháng khi học tới tháng đó (~11 MB), giải nén client-side.

  TẦNG 3 — TIẾN ĐỘ → localStorage trên máy (không cần server, không tốn băng thông).

Cách dùng:
  python tools/publish_online.py --pack --lang tiếng_nhật     # đóng gói 1 khóa
  python tools/publish_online.py --pack --all                 # đóng gói tất cả
  python tools/publish_online.py --pages                     # copy sang web/ (Pages)
  python tools/publish_online.py --upload --lang tiếng_nhật --tag v1
      (cần $env:GITHUB_TOKEN hoặc --token)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import urllib.request
import urllib.error
import zipfile
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CD = os.path.join(BASE, "data", "ai_courses")
MEDIA_DIR = os.path.join(BASE, "data", "media")
OUT = os.path.join(BASE, "publish")
WEB = os.path.join(BASE, "web")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "ThaiBao1991/Project1")


def _log(m):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {m}", flush=True)


def _slug_dirs(slug: str):
    """(media dir, day-json dir) cho 1 khóa."""
    from ai.paths import canonical_slug
    cs = canonical_slug(slug)
    return (os.path.join(MEDIA_DIR, cs), os.path.join(OUT, cs, "day"))


def _day_media_map(slug: str, day: int) -> dict:
    """{ref: rel_path} cho media của 1 ngày — đọc từ CHECKPOINT (nhỏ).

    Không đọc manifest 103 MB (quá nặng + chậm); checkpoint `images.json` /
    `audio.json` đã chứa id + rel_path của từng file.
    """
    out = {}
    base = os.path.join(CD, slug, "_pipeline", "days", f"d{day:04d}")
    for stage in ("images", "audio"):
        fp = os.path.join(base, stage + ".json")
        if not os.path.isfile(fp):
            continue
        try:
            with open(fp, encoding="utf-8") as f:
                cp = json.load(f)
        except Exception:
            continue
        data = cp.get("data") or {}
        for e in (data.get("images") or []):
            if isinstance(e, dict) and e.get("id") and e.get("rel_path"):
                out[e["id"]] = e["rel_path"]
        for tr in (data.get("tracks") or []) + (data.get("dialogue_tracks") or []):
            if not isinstance(tr, dict):
                continue
            rid = tr.get("ref") or tr.get("id")
            rel = tr.get("file") or tr.get("rel_path")
            if rid and rel:
                out[rid] = rel
    return out


def pack_course(slug: str, zip_month: bool = True) -> dict:
    """Tách course.json thành: index.json + day/<n>.json + media/<YYYY-MM>.zip."""
    src = os.path.join(CD, slug, "course.json")
    if not os.path.isfile(src):
        return {"slug": slug, "error": "không có course.json"}
    _log(f"đọc {slug} …")
    with open(src, encoding="utf-8") as f:
        course = json.load(f)
    days = course.get("days") or []
    media_dir, day_dir = _slug_dirs(slug)
    zip_dir = os.path.join(OUT, slug, "media")
    os.makedirs(day_dir, exist_ok=True)
    os.makedirs(zip_dir, exist_ok=True)

    index = {"slug": slug, "level": course.get("level", ""),
             "total_days": len(days), "days": [], "months": []}
    months = {}
    n_day = 0
    for d in days:
        try:
            n = int(d.get("day", 0))
        except Exception:
            continue
        # 1) nội dung 1 ngày (bỏ phần media khỏi lesson để nhẹ)
        lesson = {k: v for k, v in d.items() if k != "media"}
        lesson["media"] = {"vocab_audio": (d.get("media") or {}).get("vocab_audio", {}),
                           "dialogue_audio": (d.get("media") or {}).get("dialogue_audio", {})}
        # 1b) MAP ref → đường dẫn file (để web tải đúng file trong gói zip).
        # Đọc từ CHECKPOINT (nhỏ) thay vì manifest 103 MB.
        lesson["media_map"] = _day_media_map(slug, n)
        with open(os.path.join(day_dir, f"{n:04d}.json"), "w", encoding="utf-8") as f:
            json.dump(lesson, f, ensure_ascii=False, separators=(",", ":"))
        n_day += 1
        # 2) gom media theo tháng
        mkey = f"{n // 30 + 1:02d}"          # 30 ngày ≈ 1 "tháng học"
        months.setdefault(mkey, []).append(n)
        index["days"].append({"day": n, "title": d.get("title", ""),
                               "phase": d.get("phase", ""),
                               "level": d.get("level", ""),
                               "month": mkey,
                               "n_vocab": len(d.get("vocab") or []),
                               "n_quiz": sum(len(v) for v in (d.get("quiz") or {}).values()
                                             if isinstance(v, list))})

    # 3) đóng gói media theo nhóm 30 ngày
    n_zip = 0
    total_mb = 0
    if not zip_month:
        for mkey, day_nums in sorted(months.items()):
            index["months"].append({"key": mkey, "days": [day_nums[0], day_nums[-1]],
                                    "zip": f"media/m{mkey}.zip", "files": 0, "bytes": 0})
        with open(os.path.join(OUT, slug, "index.json"), "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
        _log(f"✅ {slug}: {n_day} ngày (KHÔNG nén media)")
        return {"slug": slug, "days": n_day, "zips": 0, "media_mb": 0}
    for mkey, day_nums in sorted(months.items()):
        zpath = os.path.join(zip_dir, f"m{mkey}.zip")
        n_files = 0
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for dn in day_nums:
                ddir = os.path.join(media_dir, f"d{dn:04d}")
                if not os.path.isdir(ddir):
                    continue
                for fn in sorted(os.listdir(ddir)):
                    fp = os.path.join(ddir, fn)
                    if not os.path.isfile(fp):
                        continue
                    zf.write(fp, f"d{dn:04d}/{fn}")
                    n_files += 1
        sz = os.path.getsize(zpath)
        total_mb += sz / 1024 / 1024
        n_zip += 1
        index["months"].append({"key": mkey, "days": [day_nums[0], day_nums[-1]],
                                "zip": f"media/m{mkey}.zip", "files": n_files,
                                "bytes": sz})
        _log(f"   gói {slug} m{mkey}: {n_files} file, {sz/1024/1024:.1f} MB")

    with open(os.path.join(OUT, slug, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    _log(f"✅ {slug}: {n_day} ngày · {n_zip} gói media · tổng media {total_mb:.0f} MB")
    return {"slug": slug, "days": n_day, "zips": n_zip, "media_mb": total_mb}


def publish_pages() -> int:
    """Copy web/ + dữ liệu đã đóng gói vào web/data/ (để GitHub Pages phục vụ)."""
    dst = os.path.join(WEB, "data")
    os.makedirs(dst, exist_ok=True)
    n = 0
    total = 0
    langs = []
    names = {}
    for slug in sorted(os.listdir(OUT)):
        sdir = os.path.join(OUT, slug)
        if not os.path.isfile(os.path.join(sdir, "index.json")):
            continue
        ddir = os.path.join(dst, slug)
        if os.path.isdir(ddir):
            shutil.rmtree(ddir)
        shutil.copytree(os.path.join(sdir, "day"), os.path.join(ddir, "day"))
        shutil.copy2(os.path.join(sdir, "index.json"), os.path.join(ddir, "index.json"))
        for root, _d, files in os.walk(os.path.join(ddir, "day")):
            for fn in files:
                total += os.path.getsize(os.path.join(root, fn))
                n += 1
        langs.append(slug)
        names[slug] = _display_name(slug)
        # File TỪ VỰNG (tab Danh sách · Flashcard · Ôn tập) — export từ course.json
        vp = os.path.join(dst, slug + ".json")
        vocab = _export_vocab(slug)
        with open(vp, "w", encoding="utf-8") as f:
            json.dump({"vocabularies": vocab}, f, ensure_ascii=False,
                      separators=(",", ":"))
        total += os.path.getsize(vp)
        n += 1
        _log(f"  {slug}: index.json + day/*.json + {slug}.json ({len(vocab)} từ)")

    # Danh sách khóa cho web (dropdown ngôn ngữ)
    with open(os.path.join(dst, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"languages": langs, "names": names}, f, ensure_ascii=False,
                  indent=1)
    _log(f"✅ Pages: {n} file · {total/1024/1024:.0f} MB trong {dst}")
    return 0


def _display_name(slug: str) -> str:
    from ai.paths import LANG_ALIASES
    for k, v in (LANG_ALIASES or {}).items():
        if k == slug:
            return v
    return slug.replace("tiếng_", "Tiếng ").replace("_", " ").title()


def _export_vocab(slug: str, limit_per_day: int = 0) -> list:
    """Xuất danh sách từ vựng (tab Danh sách · Flashcard · Ôn tập)."""
    src = os.path.join(CD, slug, "course.json")
    out = []
    if not os.path.isfile(src):
        return out
    with open(src, encoding="utf-8") as f:
        course = json.load(f)
    for d in (course.get("days") or []):
        dn = d.get("day")
        for v in (d.get("vocab") or []):
            if not isinstance(v, dict):
                continue
            out.append({
                "word": v.get("word", ""),
                "meaning": v.get("meaning_vi", ""),
                "reading": v.get("reading", "") or v.get("pronunciation", ""),
                "type": v.get("part_of_speech", "") or v.get("pos", ""),
                "topic": d.get("topic", "") or d.get("title", ""),
                "date_tag": f"Day {dn}",
                "example": v.get("example_sentence", ""),
                "image_ref": v.get("image_ref", ""),
                "audio_ref": v.get("audio_ref", ""),
            })
    return out


def _github_token() -> str:
    """Lấy token GitHub từ settings.json của AskCpl (đã mã hoá ENC:)."""
    import base64
    cands = [
        os.path.join(BASE, "..", "Download", "AskCpl", "settings.json"),
        os.path.join(BASE, "settings.json"),
    ]
    for p in cands:
        p = os.path.abspath(p)
        if not os.path.isfile(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            raw = (d.get("github") or {}).get("token") or ""
            if raw.startswith("ENC:"):
                raw = base64.b64decode(raw[4:].encode("utf-8")).decode("utf-8")[::-1]
            if raw:
                return raw
        except Exception:
            continue
    return os.environ.get("GITHUB_TOKEN", "")


def upload_release(slug: str, tag: str, token: str) -> int:
    """Đẩy gói media của 1 khóa lên 1 GitHub Release."""
    zdir = os.path.join(OUT, slug, "media")
    if not os.path.isdir(zdir):
        _log(f"⚠ chưa đóng gói {slug}")
        return 1
    api = f"https://api.github.com/repos/{GITHUB_REPO}"
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json",
               "User-Agent": "VocabularyApp-publisher"}

    def _req(url, data=None, method=None, headers_extra=None):
        h = dict(headers)
        if headers_extra:
            h.update(headers_extra)
        body = json.dumps(data).encode() if data is not None else None
        if body:
            h["Content-Type"] = "application/json"
        r = urllib.request.Request(url, data=body, headers=h, method=method)
        with urllib.request.urlopen(r, timeout=180) as resp:
            return json.loads(resp.read().decode() or "{}")

    # tạo (hoặc dùng lại) release
    try:
        rel = _req(f"{api}/releases/tags/{tag}")
        _log(f"release {tag} đã tồn tại — dùng lại")
    except urllib.error.HTTPError:
        rel = _req(f"{api}/releases", {
            "tag_name": tag, "name": f"Vocabulary data — {slug}",
            "body": f"Nội dung học + media của khóa {slug} (gói theo 30 ngày).",
            "draft": True}, method="POST")
        _log(f"đã tạo release {tag}")

    existing = {a.get("name") for a in (rel.get("assets") or [])}
    n = 0
    for fn in sorted(os.listdir(zdir)):
        if fn in existing:
            continue
        fp = os.path.join(zdir, fn)
        url = f"{api}/releases/{rel['id']}/assets?name={urllib.parse.quote(fn)}"
        h = dict(headers)
        h["Content-Type"] = "application/octet-stream"
        data = open(fp, "rb").read()
        r = urllib.request.Request(url, data=data, headers=h, method="POST")
        with urllib.request.urlopen(r, timeout=3600) as resp:
            resp.read()
        n += 1
        _log(f"   ↑ {fn} ({os.path.getsize(fp)/1024/1024:.1f} MB)")
    _log(f"✅ {slug}: đã đẩy {n} asset vào release {tag}")
    return 0


def main() -> int:
    global GITHUB_REPO
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--pack", action="store_true", help="đóng gói nội dung + media")
    ap.add_argument("--no-zip", action="store_true",
                    help="chỉ tách ngày (bỏ qua nén media) — dùng để thử nhanh")
    ap.add_argument("--pages", action="store_true", help="copy sang web/ (Pages)")
    ap.add_argument("--upload", action="store_true", help="đẩy lên GitHub Release")
    ap.add_argument("--tag", default="")
    ap.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPO", GITHUB_REPO))
    args = ap.parse_args()
    GITHUB_REPO = args.repo

    if args.pack:
        slugs = ([args.lang] if args.lang else
                 [s for s in sorted(os.listdir(CD))
                  if os.path.isfile(os.path.join(CD, s, "course.json"))])
        for s in slugs:
            pack_course(s, zip_month=not args.no_zip)
    if args.pages:
        publish_pages()
    if args.upload:
        tok = args.token or _github_token()
        if not tok:
            print("⚠ thiếu GITHUB_TOKEN (--token, $env:GITHUB_TOKEN hoặc settings.json)")
            return 1
        slugs = ([args.lang] if args.lang else
                 [s for s in sorted(os.listdir(OUT))
                  if os.path.isdir(os.path.join(OUT, s, "media"))])
        for s in slugs:
            upload_release(s, args.tag or f"data-{s}-v1", tok)
    return 0


if __name__ == "__main__":
    import urllib.parse
    sys.exit(main())
