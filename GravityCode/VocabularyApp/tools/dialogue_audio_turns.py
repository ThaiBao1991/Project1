# -*- coding: utf-8 -*-
"""tools/dialogue_audio_turns.py — audio TỪNG LƯỢT hội thoại, 2 ngôn ngữ.

Mỗi lượt có:
  • audio_ref     — đọc câu ngôn ngữ đích (ja-JP, zh-CN, …)
  • vi_audio_ref  — đọc bản dịch tiếng Việt (vi-VN)

Idempotent: lượt đã có đủ 2 ref thì bỏ qua.
State resume: data/logs/dialogue_audio_<slug>.json

DÙNG:
  python -X utf8 tools/dialogue_audio_turns.py --lang tiếng_nhật --dry-run
  python -X utf8 tools/dialogue_audio_turns.py --lang tiếng_nhật --limit 5
  python -X utf8 tools/dialogue_audio_turns.py --lang tiếng_nhật
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOGS = os.path.join(BASE, "data", "logs")


def log(m: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def state_path(slug: str) -> str:
    return os.path.join(LOGS, f"dialogue_audio_{slug}.json")


def load_state(slug: str) -> dict:
    try:
        with open(state_path(slug), encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def save_state(slug: str, st: dict) -> None:
    os.makedirs(LOGS, exist_ok=True)
    tmp = state_path(slug) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)
    os.replace(tmp, state_path(slug))


def target_locale(lang: str) -> str:
    from ai.tts_config import voice_for
    edge = str(voice_for(lang).get("edge_voice") or "")
    parts = edge.split("-")
    return "-".join(parts[:2]) if len(parts) >= 2 else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True)
    ap.add_argument("--limit", type=int, default=0, help="số NGÀY tối đa")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    from ai import course_db, media_store
    from ai.paths import canonical_slug
    from ai.tts_generator import synthesize
    import media_index_swap

    slug = canonical_slug(args.lang)
    # Manifest 262 MB: tách theo khóa để giảm RAM khi ghi hàng nghìn audio.
    if not args.dry_run:
        try:
            media_index_swap.begin(slug)
        except Exception as e:
            log(f"⚠ shard manifest: {e}")
    loc = target_locale(args.lang)
    if not loc:
        log(f"✗ không xác định locale cho {args.lang}")
        return 1
    course = course_db.get_course(args.lang, persist=False)
    if not course:
        log("✗ không đọc được khóa")
        return 1
    st = load_state(slug)
    done = set(st.get("done_days") or [])
    days = []
    for les in course.get("days") or []:
        try:
            dn = int(les.get("day", 0))
        except Exception:
            continue
        if dn in done or not les.get("dialogue"):
            continue
        turns = [t for d in les["dialogue"] for t in (d.get("turns") or [])]
        if turns and all(t.get("audio_ref") and t.get("vi_audio_ref") for t in turns):
            done.add(dn)
            continue
        days.append(les)
    log(f"{slug}: {len(days)} ngày cần audio (đã xong {len(done)}) · locale={loc}")
    if args.limit:
        days = days[:args.limit]
    if args.dry_run:
        for les in days[:10]:
            log(f"  - ngày {les.get('day')}: {sum(len(d.get('turns') or []) for d in les['dialogue'])} lượt")
        return 0

    changed = 0
    for les in days:
        dn = int(les.get("day", 0))
        n_ok = 0
        for di, d in enumerate(les.get("dialogue") or []):
            for ti, t in enumerate(d.get("turns") or []):
                text = str(t.get("line_target") or "").strip()
                vi = str(t.get("line_vi") or "").strip()
                try:
                    if text and not t.get("audio_ref"):
                        r = synthesize(args.lang, text, voice=loc, log_fn=log)
                        if r.get("path"):
                            with open(r["path"], "rb") as f:
                                data = f.read()
                            e = media_store.save_audio(
                                args.lang, dn,
                                f"dlg_{di:02d}_{ti:02d}_{media_store.hash_key(text, r.get('engine'))}",
                                data, mime="audio/mpeg" if r["path"].endswith(".mp3") else "audio/wav",
                                source="tts", text=text, engine=r.get("engine", ""),
                                voice=r.get("voice", ""), rate=r.get("rate", ""),
                                kind="dialogue_turn_audio")
                            if e:
                                t["audio_ref"] = e.get("id"); n_ok += 1
                    if vi and not t.get("vi_audio_ref"):
                        r2 = synthesize("vi", vi, voice="vi-VN", log_fn=log)
                        if r2.get("path"):
                            with open(r2["path"], "rb") as f:
                                data = f.read()
                            e2 = media_store.save_audio(
                                args.lang, dn,
                                f"dlgvi_{di:02d}_{ti:02d}_{media_store.hash_key(vi, r2.get('engine'))}",
                                data, mime="audio/mpeg" if r2["path"].endswith(".mp3") else "audio/wav",
                                source="tts", text=vi, engine=r2.get("engine", ""),
                                voice=r2.get("voice", ""), rate=r2.get("rate", ""),
                                kind="dialogue_turn_vi_audio")
                            if e2:
                                t["vi_audio_ref"] = e2.get("id"); n_ok += 1
                except Exception as ex:
                    log(f"  ⚠ ngày {dn} lượt {di}:{ti}: {type(ex).__name__}: {ex}")
        if n_ok:
            changed += 1
            done.add(dn)
            log(f"  ✓ ngày {dn}: +{n_ok} audio")
        if changed and changed % 10 == 0:
            course_db.save_course(args.lang, course)
            save_state(slug, {"done_days": sorted(done),
                              "at": f"{datetime.now():%Y-%m-%d %H:%M:%S}"})
            log(f"  💾 lưu ({changed} ngày)")
    course_db.save_course(args.lang, course)
    save_state(slug, {"done_days": sorted(done),
                      "at": f"{datetime.now():%Y-%m-%d %H:%M:%S}"})
    try:
        media_index_swap.end(slug)
    except Exception as e:
        log(f"⚠ gộp manifest: {e}")
    log(f"HOÀN TẤT: {changed} ngày có audio mới")
    return 0


if __name__ == "__main__":
    sys.exit(main())
