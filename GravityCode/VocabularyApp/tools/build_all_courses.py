# -*- coding: utf-8 -*-
"""tools/build_all_courses.py — DỰNG/BỔ SUNG khóa học "0 → bản xứ" cho MỌI
ngôn ngữ bằng **MỘT LỆNH**, chạy lại được (idempotent), LẶP tới khi hoàn thành.

Vòng lặp (mỗi vòng tự động bỏ qua phần đã đủ):
  B1 · Nguồn từ     : wordfreq (tần suất thật) + DỊCH LÔ 25 từ/request → tiếng Việt
  B2 · Giáo trình   : 6 chặng N5→N1 (từ thấp lên cao) + ngữ pháp theo cấp độ
                      + hội thoại + trắc nghiệm → course.json + checkpoint
  B3 · Media        : ảnh (Wikipedia/điển) + audio edge-TTS (từ/nghĩa/hội thoại)
                      — 0 quota Gemini, chạy SONG SONG nhiều khóa
  B4 · Kiểm tra    : tools/check_done.py → tiêu chí "đủ" + toast Windows
  → nếu còn khóa chưa đủ ⇒ LẶP vòng (tới khi đủ, hoặc hết số vòng cho phép)

Cách dùng:
  python tools/build_all_courses.py                    # tất cả ngôn ngữ, lặp tới khi đủ
  python tools/build_all_courses.py --lang tiếng_hàn_quốc
  python tools/build_all_courses.py --rounds 1         # chỉ 1 vòng
  python tools/build_all_courses.py --only-source      # chỉ lấy nguồn từ
  python tools/build_all_courses.py --status           # chỉ in bảng độ đầy đủ

Ngôn ngữ mới: thêm 1 dòng vào ISO_BY_LANG (ai/offline_content.py) rồi chạy lại.
"""
from __future__ import annotations

import argparse
import json
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
# "ja" dùng EDICT/JMdict (đã có sẵn) ⇒ KHÔNG cần fetch wordfreq.
LANGS = [
    ("ja", "tiếng_nhật"),
    ("zh", "tiếng_trung"),
    ("en", "tiếng_anh"),
    ("ko", "tiếng_hàn_quốc"),
    ("ru", "tiếng_nga"),
    ("fr", "tiếng_pháp"),
    ("de", "tiếng_đức"),
    ("es", "tiếng_tây_ban_nha"),
    # 3 ngôn ngữ "tương lai" (đã khai báo trong ISO_BY_LANG) — cùng 1 lệnh.
    ("it", "tiếng_italia"),
    ("pt", "tiếng_bồ_đào_nha"),
    ("vi", "tiếng_việt"),
]
ISO_BY_SLUG = {slug: iso for iso, slug in LANGS}


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


# ─── B1: nguồn từ + nghĩa tiếng Việt ─────────────────────────────────────────
def ensure_source(iso: str, limit: int) -> int:
    if iso == "ja":
        # Nhật dùng EDICT/JMdict (đã có sẵn trong data/offline_src/edict.gz)
        _log("   nguồn [ja] dùng EDICT/JMdict — bỏ qua fetch")
        return 0
    path = os.path.join(offline_content.SRC_DIR, f"words_{iso}.json")
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


# ─── B2: giáo trình 0 → bản xứ ───────────────────────────────────────────────
def build_course(lang: str, days: int) -> bool:
    _run([sys.executable, "-X", "utf8", "tools/build_offline_course.py",
          "--lang", lang, "--days", str(days), "--apply"], 3600, f"dựng {lang}")
    return True


# ─── B3: media (0 quota) ─────────────────────────────────────────────────────
def fill_media(langs, jobs: int, workers: int, all_days: bool) -> None:
    # FIX 2026-11-14: `--lang` trong fill_media là action="append" ⇒ truyền
    # nhiều lần mới giữ được HẾT các khóa (trước đây argparse chỉ giữ giá
    # trị CUỐI ⇒ chỉ bù được 1 khóa).
    cmd = [sys.executable, "-X", "utf8", "tools/fill_media.py",
           "--jobs", str(jobs), "--workers", str(workers), "--rounds", "1"]
    if all_days:
        cmd.append("--all-days")
    for lg in langs:
        cmd += ["--lang", lg]
    _run(cmd, 14 * 3600, f"media {len(langs)} khóa (song song)")


# ─── B4: kiểm tra ────────────────────────────────────────────────────────────
def verify(langs=None) -> str:
    _run([sys.executable, "-X", "utf8", "tools/verify_courses.py"], 3600, "verify")
    try:
        p = subprocess.run([sys.executable, "-X", "utf8", "tools/check_done.py",
                            "--quiet"], cwd=BASE, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=2400)
        out = p.stdout or ""
        for line in out.splitlines():
            if line.strip():
                print("   " + line.strip()[:150], flush=True)
        return out
    except Exception as e:
        _log(f"   ⚠ check_done lỗi: {e}")
        return ""


def _not_done(out: str) -> list:
    """Danh sách khóa chưa đủ (parse từ output check_done)."""
    bad = []
    for line in (out or "").splitlines():
        s = line.strip()
        if not s or s.startswith("→") or s.startswith("KIỂM TRA"):
            continue
        if s.startswith("Còn thiếu"):
            break
        # dòng dạng: tiếng_anh   2520  12.1 ... ✅/…
        if "…" in s or s.rstrip().endswith("...") or "✅" not in s:
            parts = s.split()
            if len(parts) >= 2 and parts[0].startswith("tiếng"):
                bad.append(parts[0])
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="")
    ap.add_argument("--days", type=int, default=2520)
    ap.add_argument("--word-limit", type=int, default=26000)
    ap.add_argument("--only-source", action="store_true")
    ap.add_argument("--no-media", action="store_true")
    ap.add_argument("--rounds", type=int, default=3,
                    help="số vòng lặp tối đa (mỗi vòng bỏ qua phần đã đủ)")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--all-days", action="store_true",
                    help="bù media tới hết ngay (mặc định: chặng 1-2 trước)")
    ap.add_argument("--status", action="store_true", help="chỉ in bảng độ đầy đủ")
    args = ap.parse_args()

    if args.status:
        verify()
        return 0

    targets = ([x for x in LANGS if x[1] == args.lang] if args.lang else LANGS)
    if not targets:
        print(f"⚠ chưa hỗ trợ '{args.lang}' "
              f"(có: {', '.join(l for _i, l in LANGS)})")
        return 1

    for rnd in range(1, max(1, args.rounds) + 1):
        _log(f"══════════ VÒNG {rnd}/{args.rounds} ══════════")
        for iso, lang in targets:
            t0 = time.time()
            _log(f"─────── {lang} (iso={iso}) ───────")
            ensure_source(iso, args.word_limit)
            if args.only_source:
                continue
            build_course(lang, args.days)
            _log(f"◀ {lang} nội dung xong sau {(time.time()-t0)/60:.1f} phút")
        if args.only_source:
            break
        if not args.no_media:
            fill_media([l for _i, l in targets], args.jobs, args.workers,
                       args.all_days)
        out = verify()
        bad = _not_done(out)
        if not bad:
            _log("✅ TẤT CẢ KHÓA ĐÃ ĐỦ — hoàn thành!")
            break
        _log(f"⟳ còn {len(bad)} khóa chưa đủ: {', '.join(bad)} → vòng tiếp")
        if rnd >= args.rounds:
            _log(f"⚠ đã hết {args.rounds} vòng — chạy lại lệnh này để tiếp.")
    _log("HOÀN TẤT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
