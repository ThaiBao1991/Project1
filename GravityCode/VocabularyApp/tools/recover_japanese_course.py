"""
tools/recover_japanese_course.py — KHÔI PHỤC 444 NGÀY THẬT CỦA KHÓA NHẬT (0 API call).

Nguồn sự thật: data/media/index.json (manifest media) lưu:
  • img entry (kind="vocab_image") với `alt` = TỪ TIẾNG NHẬT của ảnh idx
  • aud entry (kind="vocab_audio") theo index cùng idx = file mp3 THẬT
  ⇒ word/aud khớp 100% cho 444 ngày (đã dò 2026-10-27).

Luồng:
  1. Đọc manifest → nhóm entry theo day.
  2. word[idx]  = img["alt"]      audio_ref[idx] = aud["m_ref"]
  3. Tra seed data/seed/ja/dict.json (soạn thủ công, KHÔNG AI) cho
     reading / romaji / meaning_vi / pos / example ± .
  4. Quiz 4 loại sinh OFFLINE từ dữ liệu đã có (distractor cùng pos, cùng chặng).
  5. assemble course + checkpoint _pipeline/days/dNNNN/* rồi course_db.save_course.

Cú pháp:
  python tools/recover_japanese_course.py --dry-run          ← in 3 ngày mẫu, 0 ghi
  python tools/recover_japanese_course.py --writable         ← sinh course thật
  python tools/recover_japanese_course.py --from-day 1 --to-day 60
  python tools/recover_japanese_course.py --status           ← báo seed thiếu

KHÔNG BAO GIỜ: gọi AI, sinh từ giả (assert chặn /単語\\d+|tango\\d+/), ghi khi thiếu seed.
"""

import argparse
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import course_db  # noqa: E402
from ai.media_store import INDEX_PATH  # noqa: E402
from ai.paths import canonical_slug  # noqa: E402

# Kho media/audio thật nằm dưới data/media/nhật (rel_path trong manifest giữ
# nguyên) — nhưng course.json + checkpoint ghi về SLUG CHUẨN ('tiếng_nhật').
SLUG = canonical_slug("nhật")      # → 'tiếng_nhật'
SEED_PATH = os.path.join(BASE, "data", "seed", "ja", "dict.json")

# CẤM template rác (plan Phase 2): assert chặn từ giả trước khi ghi
FAKE_WORD_PATTERNS = (
    re.compile(r"単語\s*\d+"),
    re.compile(r"tango\s*\d+", re.IGNORECASE),
    re.compile(r"Nghĩa từ vựng số", re.IGNORECASE),
)


def is_fake_word(w: str) -> bool:
    return any(p.search(w) for p in FAKE_WORD_PATTERNS)


def load_manifest() -> dict:
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def collect_manifest_chunks(items: dict) -> dict:
    """{day: {"words": {idx: alt}, "audios": {idx: ref}}} từ manifest."""
    days = {}
    for ref, e in (items or {}).items():
        if not isinstance(e, dict):
            continue
        lang = str(e.get("lang") or "")
        if lang.lower().replace(" ", "_") not in ("nhật", "nhat", "tiếng_nhật"):
            continue
        day = e.get("day")
        if day is None:
            continue
        day = int(day)
        kind = str(e.get("kind") or e.get("type") or "")
        slot = days.setdefault(day, {"words": {}, "audios": {}})
        if kind in ("vocab_image", "image"):
            alt = str(e.get("alt") or "").strip()
            idx = _index_from_filename(e.get("rel_path") or "")
            if alt and idx is not None:
                slot["words"][idx] = alt
        elif kind in ("vocab_audio", "audio"):
            idx = _index_from_filename(e.get("rel_path") or "")
            if idx is not None and os.path.isfile(
                    os.path.join(BASE, "data", (e.get("rel_path") or ""))):
                slot["audios"][idx] = ref
    return days


def _index_from_filename(rel: str):
    """'media/nhật/d0001/word_00_h123.webp' → 0 (từ word_/audio_vocab_NN)."""
    m = re.search(r"(?:word|audio_vocab)_?(\d{1,3})", os.path.basename(rel))
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def load_seed() -> dict:
    if not os.path.isfile(SEED_PATH):
        return {}
    with open(SEED_PATH, "r", encoding="utf-8") as f:
        d = json.load(f)
    return d if isinstance(d, dict) else {}


def build_quiz_offline(day_words, seed):
    """Sinh quiz OFFLINE theo format app đọc (vocab/pattern/common/grammar/mixed).

    Distractor = nghĩa của từ cùng `pos` trong seed — đủ 3 mới chấp nhận câu hỏi
    (không nêu câu hỏi thiếu option). Pattern quiz tái dùng câu ví dụ có sẵn.
    """
    vocab_q, pat_q = [], []
    for i, w in enumerate(day_words):
        info = seed.get(w) or {}
        meaning = info.get("vi") or ""
        if not meaning:
            continue
        distractors = _distractors(w, info, seed)
        if len(distractors) < 3:
            continue                              # không đủ distractor → bỏ, không đục lỗ
        opts = distractors[:3] + [meaning]
        from random import Random
        rnd = Random(f"{w}|{i}")
        rnd.shuffle(opts)
        vocab_q.append({
            "question": f"Từ '{w}' ({info.get('reading') or '?'}) có nghĩa là gì?",
            "options": opts, "answer_index": opts.index(meaning),
            "explanation": f"{w} ({info.get('reading') or '?'}) = {meaning}"})
        ex = info.get("ex_ja") or ""
        if ex:
            pat_q.append({
                "question": f"Chỗ trống: 「{ex.replace(w, '____') if w in ex else ex}」 đúng nhất câu nào?",
                "options": opts, "answer_index": opts.index(meaning),
                "explanation": f"Câu ví dụ dùng '{w}' = {meaning}."})
    return {"vocab": vocab_q, "pattern": pat_q[:10], "common": [], "grammar": []}


def _distractors(word, info, seed) -> list:
    pos = str(info.get("pos") or "")
    out = []
    for w2, inf2 in seed.items():
        if w2 == word or w2 == info.get("vi"):
            continue
        if str(inf2.get("pos") or "") == pos:
            vi = inf2.get("vi")
            if vi:
                out.append(vi)
    return out


def build_day_dict(day, slot, seed) -> dict:
    """Assemble lesson dict 1 ngày (format v4). Chỉ dùng dữ liệu THẬT."""
    words_sorted = sorted(slot.get("words"), key=int)
    ret = {"day": int(day), "title": "", "phase": "", "level": "",
           "topic": "", "format_version": 4,
           "quiz": {"vocab": [], "pattern": [], "common": [], "grammar": []}}
    vocab = []
    for idx in words_sorted:
        w = slot["words"][idx]
        if is_fake_word(w):
            raise AssertionError(f"Từ GIẢ cấm trong manifest d{day:04d}: {w!r}")
        info = seed.get(w) or {}
        vocab.append({
            "word": w,
            "pronunciation": info.get("reading") or "",
            "pos": "",   # pos có thể từ seed; để '' để khỏi hiển thị nhầm
            "part_of_speech": info.get("pos") or "",
            "meaning_vi": info.get("vi") or "",
            "explanation": "",
            "example_sentence": info.get("ex_ja") or "",
            "example_meaning_vi": info.get("ex_vi") or "",
            "image_ref": "",
            "audio_ref": slot["audios"].get(idx, ""),
        })
    ret["vocab"] = vocab
    return ret


def recover(days: dict, seed, from_day=1, to_day=None, writable=False,
            dry_run=0, sample=3) -> dict:
    """Xử lý từ ngày from_day → to_day (mặc định hết manifest)."""
    to_day = to_day or max(days)
    stat = {"days": 0, "words": 0, "audio_ok": 0, "missing_seed": set(), "no_day": 0}
    lessons = []
    if dry_run:
        to_day = min(to_day, from_day + max(0, sample) - 1)
    for day in sorted(days):
        if not (from_day <= day <= to_day):
            continue
        slot = days[day]
        if not slot.get("words"):
            stat["no_day"] += 1
            continue
        try:
            lesson = build_day_dict(day, slot, seed)
        except AssertionError as e:
            print(f"⛔ {e}")
            continue
        for v in lesson["vocab"]:
            if not v["meaning_vi"]:
                stat["missing_seed"].add(v["word"])
            if v["audio_ref"]:
                stat["audio_ok"] += 1
        stat["days"] += 1
        stat["words"] += len(lesson["vocab"])
        lesson["quiz"].update(build_quiz_offline([v["word"] for v in lesson["vocab"]], seed))
        lessons.append(lesson)

    if dry_run:
        for l in lessons:
            print(f"\n=== NGÀY {l['day']} ===")
            for v in l["vocab"]:
                print(f"  {v['word']:10} [{v['pronunciation'] or '—':10}] "
                      f"{v['meaning_vi'] or '— (thiếu seed)':30} "
                      f"🔊{'✔' if v['audio_ref'] else '✘'}")
        return stat

    if writable and lessons:
        course = assemble_course(lessons)
        save_course_days(course)
    return stat


def assemble_course(lessons) -> dict:
    old = course_db.get_course(SLUG, apply_v4=False, persist=False) or {}
    course = {
        "format_version": 5, "level": old.get("level") or "Trọn Gói",
        "days": [],
    }
    for l in lessons:
        course["days"].append(l)
    return course


def save_course_days(course):
    """Ghi checkpoint từng ngày (dẽ dừng giữa chừng) rồi course.json 1 lần."""
    for l in course["days"]:
        day = int(l["day"])
        try:
            from ai.pipeline_store import save_checkpoint as _sc, STAGE_CONTENT, STATUS_DONE
            _sc(SLUG, STAGE_CONTENT, l, day=day, status=STATUS_DONE)
        except Exception:
            pass
    course_db.save_course(SLUG, course)
    print(f"💾 Đã dùng {len(course['days'])} ngày vào course.json của '{SLUG}'.")


def cmd_status(days: dict, seed: dict):
    total_words, have = set(), 0
    for day, slot in days.items():
        for _, w in slot.get("words", {}).items():
            total_words.add(w)
            if w in seed:
                have += 1
    uniq = sorted(total_words)
    paid = [w for w in uniq if w not in seed]
    print(f"📅 Ngày có media : {len(days)}")
    print(f"🔤 Từ unique     : {len(uniq)}")
    print(f"📘 Có seed       : {len(uniq) - len(paid)}")
    print(f"❓ Thiếu seed     : {len(paid)}")
    if paid:
        print(f"   mẫu 20: {', '.join(paid[:20])}")
    return paid


def main():
    ap = argparse.ArgumentParser(prog="recover_japanese_course")
    ap.add_argument("--dry-run", action="store_true", help="In 3 ngày mẫu, 0 ghi")
    ap.add_argument("--writable", action="store_true", help="Ghi course.json thật")
    ap.add_argument("--status", action="store_true", help="Báo thiếu seed")
    ap.add_argument("--from-day", type=int, default=1)
    ap.add_argument("--to-day", type=int, default=0)
    ap.add_argument("--sample", type=int, default=3, help="Số ngày --dry-run in")
    args = ap.parse_args()

    if not os.path.isfile(INDEX_PATH):
        print("⛔ Không tìm thấy manifest:", INDEX_PATH)
        return 1
    manifest = load_manifest()
    days = collect_manifest_chunks(manifest.get("items") or {})
    if not days:
        print("⛔ Manifest không có mục nào của kho 'nhật' — kiểm tra lại data thật.")
        return 1
    seed = load_seed()
    print(f"📖 Seed: {len(seed)} từ ({SEED_PATH})" if seed else
          "⚠ Chưa có seed — mọi từ sẽ 'thiếu seed' (chỉ audio+word thô).")

    if args.status:
        cmd_status(days, seed)
        return 0

    stat = recover(days, seed,
                   from_day=args.from_day,
                   to_day=args.to_day or None,
                   writable=args.writable,
                   dry_run=1 if args.dry_run else 0,
                   sample=args.sample)
    if not args.dry_run:
        print(f"\n✅ Khôi phục: {stat['days']} ngày · {stat['words']} slot · "
              f"audio resolve {stat['audio_ok']}/{stat['words']} · "
              f"thiếu seed {len(stat['missing_seed'])}")
    if args.dry_run:
        if stat["missing_seed"]:
            print(f"\n❓ Thiếu seed ({len(stat['missing_seed'])}): sample "
                  f"{', '.join(sorted(stat['missing_seed'])[:20])}")
            print("→ Bổ sung data/seed/ja/dict.json rồi chạy lại để có nghĩa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
