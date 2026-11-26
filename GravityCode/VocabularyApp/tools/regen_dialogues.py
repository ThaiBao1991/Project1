# -*- coding: utf-8 -*-
"""tools/regen_dialogues.py — sinh lại HỘI THOẠI dùng đúng từ vựng/ngữ pháp.

VẤN ĐỀ: 1.311/2.520 ngày tiếng Nhật dùng hội thoại offline (câu rời rạc), nhiều
ngày AI chỉ chào hỏi chung, không dùng từ của bài.

CÁCH DÙNG:
  python -X utf8 tools/regen_dialogues.py --lang tiếng_nhật --scope offline --limit 3
  python -X utf8 tools/regen_dialogues.py --lang tiếng_nhật --scope offline
  python -X utf8 tools/regen_dialogues.py --lang tiếng_nhật --scope weak --dry-run

- scope offline: ngày có title "Hội thoại mẫu"
- scope weak: hội thoại dùng <2 từ vựng của ngày
- scope all: mọi ngày
- Lưu gốc vào lesson["dialogue_backup"] (chỉ lần đầu) để có thể khôi phục.
- State resume: data/logs/dialogue_regen_<slug>.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOGS = os.path.join(BASE, "data", "logs")


def log(msg: str) -> None:
    line = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)


def state_path(slug: str) -> str:
    return os.path.join(LOGS, f"dialogue_regen_{slug}.json")


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


def _hits(lesson: dict, dialogues: list) -> int:
    text = " ".join(str(t.get("line_target") or "")
                    for d in dialogues for t in (d.get("turns") or []))
    words = [str(v.get("word") or "").strip() for v in (lesson.get("vocab") or [])
             if isinstance(v, dict)]
    words = [w for w in words if w]
    return sum(1 for w in words if w in text)


def _script_ok(slug: str, dialogues: list) -> bool:
    """Tiếng Nhật: line_target phải có kanji/kana, không được chỉ romaji."""
    if "nhật" not in slug:
        return True
    import re as _re
    for d in dialogues:
        for t in (d.get("turns") or []):
            line = str(t.get("line_target") or "")
            if not _re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", line):
                return False
    return True


def _is_offline(lesson: dict) -> bool:
    d = (lesson.get("dialogue") or [{}])[0]
    return str(d.get("title") or "").startswith("Hội thoại mẫu")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True)
    ap.add_argument("--scope", choices=["offline", "weak", "all"], default="offline")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-hits", type=int, default=2)
    args = ap.parse_args()

    from ai import course_db
    from ai.course_generator import (DIALOGUE_SCHEMA, GenerationStopped,
                                     build_dialogue_prompt, parse_dialogue_json)
    from ai.media_schema import cefr_for_stage
    from ai.pipeline_media import _validate_dialogues
    from ai.providers import ProviderChain
    from ai.tts_config import stage_index_from_phase
    from ai.paths import canonical_slug

    slug = canonical_slug(args.lang)
    course = course_db.get_course(args.lang, persist=False)
    if not course:
        log(f"✗ không đọc được khóa {args.lang}")
        return 1
    days = course.get("days") or []
    log(f"khóa {slug}: {len(days)} ngày")

    offsets = args.limit
    st = load_state(slug)
    done = set(st.get("done_days") or [])

    candidates = []
    for les in days:
        try:
            dn = int(les.get("day", 0))
        except Exception:
            continue
        if dn in done:
            continue
        dl = les.get("dialogue") or []
        if not dl:
            continue
        if args.scope == "offline" and not _is_offline(les):
            continue
        if args.scope == "weak" and _hits(les, dl) >= args.min_hits:
            continue
        candidates.append(les)
    log(f"ứng viên: {len(candidates)} (scope={args.scope}, đã làm {len(done)})")
    if offsets:
        candidates = candidates[:offsets]
    if args.dry_run:
        for les in candidates[:20]:
            log(f"  - ngày {les.get('day')}: {_hits(les, les.get('dialogue') or [])} hit"
                f" | {((les.get('dialogue') or [{}])[0].get('title') or '')[:50]}")
        return 0
    if not candidates:
        return 0

    chain = ProviderChain.default(log_fn=log)
    ok_prov, reason = (chain.providers[0].available() if chain.providers
                       else (False, "no provider"))
    if not ok_prov:
        log(f"✗ không có provider AI: {reason}")
        return 1
    coord = chain.providers[0].coord

    changed = 0
    for i, les in enumerate(candidates, 1):
        dn = int(les.get("day", 0))
        try:
            stage_idx = stage_index_from_phase(les.get("phase", ""))
            level_tag = cefr_for_stage(stage_idx)
            prompt = build_dialogue_prompt(
                args.lang, les, level=les.get("level") or course.get("level") or "",
                level_tag=level_tag, review=bool(les.get("is_review_day")))
            res = coord.request(prompt, response_schema=DIALOGUE_SCHEMA)
            if not res.get("ok"):
                log(f"  ✗ ngày {dn}: {(res.get('error') or {}).get('kind')}")
                continue
            dialogues = parse_dialogue_json(res.get("text", ""))
            hits = _hits(les, dialogues)
            invalid = [e for v in _validate_dialogues(dialogues, les)
                       if not v.get("ok") for e in (v.get("errors") or [])]
            missing_vi = any(not str(t.get("line_vi") or "").strip()
                             for d in dialogues for t in (d.get("turns") or []))
            script_ok = _script_ok(slug, dialogues)
            # Thử lại 1 lần kèm phản hồi cụ thể (từ còn thiếu) — AI thường sửa được.
            if dialogues and (hits < args.min_hits or invalid or missing_vi or not script_ok):
                words = ", ".join(str(v.get("word") or "") for v in
                                  (les.get("vocab") or [])[:12] if isinstance(v, dict))
                fix = (f"\n\n⚠ LẦN TRƯỚC CHƯA ĐẠT: {'; '.join(invalid[:3]) or 'thiếu từ khoá'}"
                       f"\n- BẮT BUỘC dùng ĐÚNG các từ sau (nguyên dạng) trong câu: {words}"
                       f"\n- Mỗi lượt có ít nhất 1 từ trong danh sách; tổng ≥ {args.min_hits} từ."
                       f"\n- Mỗi lượt phải có line_vi (tiếng Việt)."
                       f"\n- line_target viết bằng kanji/kana, KHÔNG romaji. "
                       f"Ví dụ ĐÚNG: \"元気ですか。\" — SAI: \"Genki desu ka.\"")
                res2 = coord.request(prompt + fix, response_schema=DIALOGUE_SCHEMA)
                if res2.get("ok"):
                    d2 = parse_dialogue_json(res2.get("text", ""))
                    h2 = _hits(les, d2)
                    v2 = [e for v in _validate_dialogues(d2, les)
                          if not v.get("ok") for e in (v.get("errors") or [])]
                    m2 = any(not str(t.get("line_vi") or "").strip()
                             for d in d2 for t in (d.get("turns") or []))
                    s2 = _script_ok(slug, d2)
                    if d2 and h2 >= args.min_hits and not v2 and not m2 and s2:
                        dialogues, hits, invalid, missing_vi, script_ok = d2, h2, [], False, True
                        log(f"  ↻ ngày {dn}: thử lại OK ({hits} từ khoá)")
            if not dialogues or hits < args.min_hits or invalid or missing_vi or not script_ok:
                log(f"  ✗ ngày {dn}: hits={hits} invalid={invalid[:2]} missing_vi={missing_vi}")
                continue
            les["dialogue_backup"] = les.get("dialogue_backup") or les.get("dialogue")
            # Audio cũ gắn với câu cũ ⇒ bỏ ref để bước audio sinh lại đúng câu mới.
            for d in dialogues:
                d.pop("audio_ref", None)
                for t in (d.get("turns") or []):
                    t.pop("audio_ref", None)
                    t.pop("vi_audio_ref", None)
            mm = les.get("media") or {}
            for k in ("dialogue_audio", "dialogue_turn_audio", "dialogue_turn_vi_audio"):
                mm.pop(k, None)
            les["dialogue"] = dialogues
            changed += 1
            done.add(dn)
            log(f"  ✓ ngày {dn}: {len(dialogues[0].get('turns') or [])} lượt · "
                f"{hits} từ khoá · {dialogues[0].get('title','')[:40]}")
            if changed % 20 == 0:
                course_db.save_course(args.lang, course)
                save_state(slug, {"done_days": sorted(done),
                                  "at": f"{datetime.now():%Y-%m-%d %H:%M:%S}"})
                log(f"  💾 đã lưu ({changed})")
        except GenerationStopped:
            log("⏹ người dùng dừng — lưu tiến độ")
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"  ⚠ ngày {dn}: {type(e).__name__}: {e}")
        time.sleep(0.5)

    course_db.save_course(args.lang, course)
    save_state(slug, {"done_days": sorted(done),
                      "at": f"{datetime.now():%Y-%m-%d %H:%M:%S}"})
    log(f"HOÀN TẤT: cập nhật {changed} ngày")
    return 0


if __name__ == "__main__":
    sys.exit(main())
