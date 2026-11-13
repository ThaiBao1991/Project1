# -*- coding: utf-8 -*-
"""tools/build_all_courses.py — DỰNG/BỔ SUNG khóa học "0 → bản xứ" cho MỌI ngôn ngữ.

MỘT LỆNH duy nhất, chạy lại được (idempotent) — thay cho hàng chục lệnh rời rạc:
  Bước 1 · Nguồn từ: wordfreq (tần suất thật) + DỊCH LÔ sang tiếng Việt
          → cache `data/offline_src/words_<iso>.json`
  Bước 2 · Giáo trình 6 chặng N5→N1 (từ thấp lên cao) + ngữ pháp theo cấp độ
          + hội thoại + trắc nghiệm → `course.json` + checkpoint
  Bước 3 · Media (ảnh Wikipedia + audio edge-TTS, 0 quota Gemini)
  Bước 4 · Verify độ đầy đủ (tools/verify_courses.py)

Cách dùng:
  python tools/build_all_courses.py                     # tất cả ngôn ngữ còn thiếu
  python tools/build_all_courses.py --lang tiếng_anh     # 1 ngôn ngữ
  python tools/build_all_courses.py --days 2520 --only-source   # chỉ lấy nguồn từ
Ngôn ngữ mới (chưa có trong danh sách): thêm vào ISO_BY_LANG (ai/offline_content.py).
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

from ai import offline_content  # noqa: E402

# iso → slug khóa học (khớp ISO_BY_LANG trong ai/offline_content.py)
LANGS = [
    ("zh", "tiếng_trung"),
    ("en", "tiếng_anh"),
    ("ko", "tiếng_hàn_quốc"),
    ("ru", "tiếng_nga"),
    ("fr", "tiếng_pháp"),
    ("de", "tiếng_đức"),
    ("es", "tiếng_tây_ban_nha"),
]


def _log(m):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {m}", flush=True)


def _run(cmd, timeout, label):
    _log(f"▶ {label}")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, cwd=BASE)
        out = (p.stdout or "") + (p.stderr or "")
        for x in out.splitlines()[-3:]:
            if x.strip():
                _log("   " + x.strip()[:140])
        return p.returncode
    except subprocess.TimeoutExpired:
        _log(f"   ⏱ {label} hết {timeout/60:.0f} phút")
        return -1


def ensure_source(iso: str, limit: int) -> int:
    """Bước 1: nguồn từ + nghĩa tiếng Việt (dịch lô, nhanh)."""
    path = os.path.join(offline_content.SRC_DIR, f"words_{iso}.json")
    have = 0
    try:
        with open(path, encoding="utf-8") as f:
            have = len(json.load(f) or {})
    except Exception:
        have = 0
    if have >= limit:
        _log(f"   nguồn [{iso}] đã có {have} từ — bỏ qua")
        return have
    _run([sys.executable, "-X", "utf8", "tools/fetch_offline_words.py",
          "--lang", iso, "--limit", str(limit)], 4 * 3600, f"nguồn từ [{iso}]")
    try:
        with open(path, encoding="utf-8") as f:
            return len(json.load(f) or {})
    except Exception:
        return 0


def build_course(lang: str, days: int) -> bool:
    _run([sys.executable, "-X", "utf8", "tools/build_offline_course.py",
          "--lang", lang, "--days", str(days), "--apply"], 3600, f"dựng {lang}")
    return True


def fill_media(lang: str) -> None:
    _run([sys.executable, "-X", "utf8", "-m", "ai.pipeline", "--lang", lang,
          "--stages", "images,audio,media_verify", "--days", "9999",
          "--workers", "2"], 6 * 3600, f"media {lang}")


def verify(langs) -> None:
    _run([sys.executable, "-X", "utf8", "tools/verify_courses.py"], 3600, "verify")
    try:
        subprocess.run([sys.executable, "-X", "utf8", "tools/check_done.py"],
                       cwd=BASE, timeout=1800)
    except Exception:
        pass


def main() -> int:
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="")
    ap.add_argument("--days", type=int, default=2520)
    ap.add_argument("--word-limit", type=int, default=26000)
    ap.add_argument("--only-source", action="store_true")
    ap.add_argument("--no-media", action="store_true")
    args = ap.parse_args()

    targets = ([x for x in LANGS if x[1] == args.lang] if args.lang else LANGS)
    if not targets:
        print(f"⚠ chưa hỗ trợ '{args.lang}' (có: {', '.join(l for _i, l in LANGS)})")
        return 1
    for iso, lang in targets:
        t0 = time.time()
        _log(f"═══════ {lang} (iso={iso}) ═══════")
        ensure_source(iso, args.word_limit)
        if args.only_source:
            continue
        build_course(lang, args.days)
        if not args.no_media:
            fill_media(lang)
        _log(f"◀ {lang} xong sau {(time.time()-t0)/60:.1f} phút")
    verify([l for _i, l in targets])
    _log("HOÀN TẤT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
