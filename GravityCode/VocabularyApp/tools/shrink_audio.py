# -*- coding: utf-8 -*-
"""tools/shrink_audio.py — Giảm dung lượng audio TTS (MP3) trước khi pack.

ĐO THẬT (19/11/2026):
  • 110.384 file MP3 = 1,88 GB, mono 24 kHz, 48 hoặc 64 kbps.
  • Re-encode 32 kbps mono 24 kHz: giảm ~31–50%, thời lượng lệch <0,1 giây.
  • Ảnh WebP chỉ ~71 MB nên không cần đụng.

CÁCH LÀM:
  • Giữ NGUYÊN tên file/đường dẫn ⇒ `media_map` và ref không đổi.
  • Chỉ nén file MP3 có bitrate > 40 kbps; file đã nén thì bỏ qua.
  • Ghi ra file tạm, kiểm tra thời lượng ±10%, chỉ thay khi nhỏ hơn.
  • Chạy song song 2 worker, ưu tiên Below Normal.

CÁCH DÙNG:
  python -X utf8 tools/shrink_audio.py --lang tiếng_anh --dry-run
  python -X utf8 tools/shrink_audio.py --lang tiếng_anh
  python -X utf8 tools/shrink_audio.py --lang all --workers 2
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MEDIA = os.path.join(BASE, "data", "media")
FFMPEG = os.environ.get("FFMPEG_BIN") or "ffmpeg"
TARGET_BPS = 32000
SKIP_KBPS = 40

try:
    from mutagen.mp3 import MP3
except Exception:  # pragma: no cover
    MP3 = None


def _log(m: str) -> None:
    print(m, flush=True)


def _nice_below_normal(pid: int) -> None:
    try:
        import psutil
        psutil.Process(pid).nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass


def _info(path: str):
    """(bitrate_bps, duration_s) hoặc (None, None)."""
    if MP3 is not None:
        try:
            a = MP3(path)
            return int(a.info.bitrate), float(a.info.length)
        except Exception:
            return None, None
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration,bit_rate", "-of", "default=noprint_wrappers=1",
             path], capture_output=True, text=True, timeout=30)
        vals = dict(line.split("=", 1) for line in r.stdout.splitlines() if "=" in line)
        return int(float(vals.get("bit_rate", 0))), float(vals.get("duration", 0))
    except Exception:
        return None, None


def _convert(path: str, bitrate: int) -> tuple[bool, int, int]:
    """Trả (đã_thay, bytes_cũ, bytes_mới)."""
    old_size = os.path.getsize(path)
    if old_size < 3000:
        return False, old_size, old_size
    br, dur = _info(path)
    if br is None:
        return False, old_size, old_size
    if br <= SKIP_KBPS * 1000:
        return False, old_size, old_size
    tmp = path + ".tmp_shrink.mp3"
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
           "-i", path, "-codec:a", "libmp3lame",
           "-b:a", f"{bitrate//1000}k", "-ac", "1", "-ar", "24000", tmp]
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        _nice_below_normal(p.pid)
        if p.wait(timeout=120) != 0:
            raise RuntimeError("ffmpeg exit")
        new_size = os.path.getsize(tmp)
        _, new_dur = _info(tmp)
        if new_size <= 0 or new_size >= old_size * 0.97:
            raise RuntimeError("không nhỏ hơn")
        if dur and new_dur and abs(new_dur - dur) > max(0.75, dur * 0.10):
            raise RuntimeError("thời lượng lệch")
        os.replace(tmp, path)
        return True, old_size, new_size
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False, old_size, old_size


def _lang_dirs(arg: str) -> list[str]:
    if arg == "all":
        return [os.path.join(MEDIA, d) for d in sorted(os.listdir(MEDIA))
                if os.path.isdir(os.path.join(MEDIA, d))
                and not d.startswith("_") and d != "zztest"]
    return [os.path.join(MEDIA, arg)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="all")
    ap.add_argument("--bitrate", type=int, default=TARGET_BPS)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass

    files = []
    for d in _lang_dirs(args.lang):
        for dp, _ds, fs in os.walk(d):
            for f in fs:
                if f.lower().endswith(".mp3"):
                    files.append(os.path.join(dp, f))
    if args.limit:
        files = files[:args.limit]
    _log(f"{args.lang}: {len(files)} file MP3 | target {args.bitrate//1000} kbps | "
         f"workers={args.workers}" + ("  (DRY-RUN)" if args.dry_run else ""))

    if args.dry_run:
        old = new = n = 0
        for p in files:
            br, _d = _info(p)
            if br and br > SKIP_KBPS * 1000:
                sz = os.path.getsize(p)
                old += sz
                new += int(sz * args.bitrate / br)
                n += 1
        _log(f"   ước tính: {n} file cần nén | {old/1e6:.1f} MB → ~{new/1e6:.1f} MB "
             f"(tiết kiệm ~{(old-new)/1e6:.1f} MB)")
        return 0

    done = converted = skipped = 0
    old_total = new_total = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = {ex.submit(_convert, p, args.bitrate): p for p in files}
        for fut in as_completed(futs):
            ok, old, new = fut.result()
            done += 1
            old_total += old
            if ok:
                converted += 1
                new_total += new
            else:
                skipped += 1
            if done % 500 == 0:
                saved = (old_total - new_total) / 1e6
                _log(f"   {done}/{len(files)} | nén {converted} | bỏ qua {skipped} | "
                     f"tiết kiệm {saved:.1f} MB | {time.time()-t0:.0f}s")
    saved = (old_total - new_total) / 1e6
    _log(f"✓ xong: {done} file | nén {converted} | bỏ qua {skipped} | "
         f"tiết kiệm {saved:.1f} MB | {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
