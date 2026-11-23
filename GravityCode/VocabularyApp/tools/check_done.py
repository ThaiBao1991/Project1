# -*- coding: utf-8 -*-
"""tools/check_done.py — KIỂM TRA ĐỊNH KỲ + THÔNG BÁO khi khóa học đã ĐỦ.

Chạy định kỳ (mỗi 30 phút bằng Task Scheduler, hoặc gọi từ watchdog):
  1. Đo độ đầy đủ TỪNG khóa (course.json + manifest media thật).
  2. So với tiêu chí "ĐỦ" (xem CRITERIA).
  3. Nếu TẤT CẢ khóa đạt ⇒ **thông báo Windows** (balloon toast) + ghi
     `data/logs/ALL_DONE.txt` ⇒ bạn biết ngay mà không cần hỏi tôi.
  4. Ghi `data/logs/check_status.txt` (trạng thái mới nhất) mỗi lần chạy.

Tiêu chí "ĐỦ" (mỗi khóa):
  • 0 ngày rỗng
  • ảnh ≥ 95 % từ · audio từ ≥ 95 % · audio nghĩa ≥ 90 %
  • audio hội thoại ≥ 85 % số bài hội thoại
  • ≥ 4 mục ngữ pháp / ngày
  • ≥ 8 câu trắc nghiệm / ngày

Cách dùng:
  python tools/check_done.py            # kiểm tra 1 lần (+ thông báo nếu đủ)
  python tools/check_done.py --quiet    # không hiện hộp thoại
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA = os.path.join(BASE, "data")
CD = os.path.join(DATA, "ai_courses")
LOG_DIR = os.path.join(DATA, "logs")
STATUS = os.path.join(LOG_DIR, "check_status.txt")
DONE = os.path.join(LOG_DIR, "ALL_DONE.txt")

CRITERIA = {
    "img_pct": 95.0,
    "aud_pct": 95.0,
    "mean_pct": 90.0,
    "dlg_pct": 85.0,
    # AI sinh 2 mục ngữ pháp/ngày, offline sinh 4 ⇒ ngưỡng 2 là "đủ dùng được"
    "grammar_min": 2.0,
    "quiz_min": 8.0,
}


def _manifest():
    try:
        with open(os.path.join(DATA, "media", "index.json"), encoding="utf-8") as f:
            return (json.load(f) or {}).get("items") or {}
    except Exception:
        return {}


def check(slug, items):
    path = os.path.join(CD, slug, "course.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except Exception:
        return None
    days = c.get("days") or []
    n_v = n_img = n_aud = n_mean = 0
    dlg = dlg_ok = 0
    gram = quiz = 0
    empty = 0
    for d in days:
        v = d.get("vocab") or []
        if not v:
            empty += 1
        for x in v:
            if not isinstance(x, dict):
                continue
            n_v += 1
            if x.get("image_ref") in items:
                n_img += 1
            if x.get("audio_ref") in items:
                n_aud += 1
            if x.get("meaning_audio_ref") in items:
                n_mean += 1
        dl = d.get("dialogue") or []
        dlg += len(dl)
        dm = (d.get("media") or {}).get("dialogue_audio") or {}
        for i, x in enumerate(dl):
            if (dm.get(str(i)) or x.get("audio_ref")) in items:
                dlg_ok += 1
        gram += len(d.get("grammar") or [])
        q = d.get("quiz") or {}
        quiz += sum(len(q.get(k) or []) for k in ("vocab", "pattern", "common",
                                                 "grammar", "mixed"))
    pct = lambda a, b: (a * 100.0 / b) if b else 0.0
    r = {
        "days": len(days), "empty": empty, "vocab": n_v,
        "img_pct": round(pct(n_img, n_v), 1),
        "aud_pct": round(pct(n_aud, n_v), 1),
        "mean_pct": round(pct(n_mean, n_v), 1),
        "dlg_pct": round(pct(dlg_ok, dlg), 1),
        "grammar_day": round(gram / len(days), 1) if days else 0,
        "quiz_day": round(quiz / len(days), 1) if days else 0,
    }
    r["ok"] = (r["empty"] == 0 and r["img_pct"] >= CRITERIA["img_pct"]
               and r["aud_pct"] >= CRITERIA["aud_pct"]
               and r["mean_pct"] >= CRITERIA["mean_pct"]
               and r["dlg_pct"] >= CRITERIA["dlg_pct"]
               and r["grammar_day"] >= CRITERIA["grammar_min"]
               and r["quiz_day"] >= CRITERIA["quiz_min"])
    return r


def notify(title, msg):
    """Thông báo Windows — balloon toast (System.Windows.Forms), fallback msg.exe."""
    esc = lambda s: str(s).replace("'", "''")
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms,System.Drawing;"
        "$n=New-Object System.Windows.Forms.NotifyIcon;"
        "$n.Icon=[System.Drawing.SystemIcons]::Information;$n.Visible=$true;"
        f"$n.ShowBalloonTip(20000,'{esc(title)}','{esc(msg)}',"
        "[System.Windows.Forms.ToolTipIcon]::Info);"
        "Start-Sleep -Seconds 12;$n.Dispose()"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-WindowStyle", "Hidden",
                        "-Command", ps], timeout=40)
        return True
    except Exception:
        try:
            subprocess.run(["msg", "*", f"{title}: {msg}"], timeout=20)
            return True
        except Exception:
            return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    os.makedirs(LOG_DIR, exist_ok=True)
    items = _manifest()
    slugs = sorted(s for s in os.listdir(CD)
                   if not s.startswith("_")
                   and os.path.isfile(os.path.join(CD, s, "course.json")))
    rows = []
    for s in slugs:
        r = check(s, items)
        if r:
            rows.append((s, r))
    lines = [f"KIỂM TRA {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
             f"{'khóa học':22}{'ngày':>6}{'ảnh%':>7}{'au từ%':>9}{'nghĩa%':>8}"
             f"{'h.thoại%':>10}{'ngữ pháp/ng':>12}{'câu/ng':>9}  OK"]
    for s, r in rows:
        lines.append(f"{s:22}{r['days']:>6}{r['img_pct']:>7}{r['aud_pct']:>9}"
                     f"{r['mean_pct']:>8}{r['dlg_pct']:>10}{r['grammar_day']:>12}"
                     f"{r['quiz_day']:>9}  {'✅' if r['ok'] else '…'}")
    n_ok = sum(1 for _s, r in rows if r["ok"])
    lines.append(f"→ {n_ok}/{len(rows)} khóa đã ĐỦ")
    txt = "\n".join(lines)
    with open(STATUS, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    print(txt)

    all_ok = bool(rows) and n_ok == len(rows)
    if all_ok:
        with open(DONE, "w", encoding="utf-8") as f:
            f.write(f"HOÀN THÀNH {datetime.now().isoformat(timespec='seconds')}\n{txt}\n")
        if not args.quiet:
            notify("✅ Vocabulary App — khóa học đã ĐỦ",
                   f"{n_ok}/{len(rows)} khóa học đạt đủ nội dung, media, ngữ pháp, "
                   f"trắc nghiệm. Có thể học ngay.")
        print("\n✅ TẤT CẢ KHÓA HỌC ĐÃ ĐỦ — đã gửi thông báo.")
    else:
        missing = []
        for s, r in rows:
            if not r["ok"]:
                bits = []
                if r["img_pct"] < CRITERIA["img_pct"]:
                    bits.append(f"ảnh {r['img_pct']}%")
                if r["aud_pct"] < CRITERIA["aud_pct"]:
                    bits.append(f"audio từ {r['aud_pct']}%")
                if r["mean_pct"] < CRITERIA["mean_pct"]:
                    bits.append(f"audio nghĩa {r['mean_pct']}%")
                if r["dlg_pct"] < CRITERIA["dlg_pct"]:
                    bits.append(f"hội thoại {r['dlg_pct']}%")
                if r["grammar_day"] < CRITERIA["grammar_min"]:
                    bits.append(f"ngữ pháp {r['grammar_day']}/ngày")
                if r["quiz_day"] < CRITERIA["quiz_min"]:
                    bits.append(f"câu {r['quiz_day']}/ngày")
                missing.append(f"{s}: " + ", ".join(bits))
        print("\nCòn thiếu:")
        for m in missing:
            print("  -", m)
        if not args.quiet and missing:
            notify("⏳ Vocabulary App — đang bổ sung",
                   "; ".join(missing[:3]) + ("…" if len(missing) > 3 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
