"""tools/smoke_test_pipeline.py — Smoke test THẬT 1 ngày cho pipeline.

Mục đích: xác minh trong worktree rằng pipeline sinh được:
  content -> quiz AB -> quiz CD -> ảnh -> audio -> media_verify
mà KHÔNG cần chạy backbone 1400 ngày.

Cách làm:
  - Tạo khóa tạm `tiếng_nhật_smoke` với đúng 1 ngày rỗng.
  - Chạy run_pipeline với stages per-day (không profile/backbone/plan).
  - Kiểm tra course.json + file media thật.

Chạy:
  python tools/smoke_test_pipeline.py
  python tools/smoke_test_pipeline.py --keep   # giữ khóa test để xem web
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
from ai.pipeline import run_pipeline  # noqa: E402
from ai.course_generator import LEVELS  # noqa: E402

LANG = "tiếng_nhật_smoke"
LEVEL = LEVELS[1]  # "1. Vỡ lòng (Bảng chữ cái & Khẩu hình phát âm)"
PHASE = "Vỡ lòng — kana & phát âm"
FAKE_RE = re.compile(r"単語\d+|tango\d+|Nghĩa từ vựng số", re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="Giữ khóa test sau khi chạy")
    ap.add_argument("--images", type=int, default=2)
    ap.add_argument("--audio", type=int, default=2)
    args = ap.parse_args()

    # 1) Tạo khóa tạm 1 ngày rỗng (không đụng khóa thật)
    course_db.delete_course(LANG)
    course = course_db.new_course(LANG, [], 10)
    course["level"] = LEVEL
    course["days"] = [{
        "day": 1,
        "title": "Bài 1 — Chào hỏi & giới thiệu bản thân",
        "phase": PHASE,
        "level": LEVEL,
        "topic": "Chào hỏi cơ bản",
        "words": [],
        "vocab": [],
        "quiz": {},
        "format_version": 4,
    }]
    course_db.save_course(LANG, course)
    print(f"🧪 Đã tạo khóa test '{LANG}' (1 ngày rỗng).")

    stages = ["content", "quiz_ab", "quiz_cd", "images", "audio",
              "dialogue", "media_verify"]
    print(f"▶ Chạy stages: {', '.join(stages)}")
    res = run_pipeline(
        LANG,
        words_per_day=10,
        level=LEVEL,
        stages=stages,
        full=False,
        mode="full",
        target_days=1,
        workers=1,
        max_images_per_day=args.images,
        max_audio_per_day=args.audio,
        allow_degraded=True,
        resume=False,
        force_new=False,
        media=True,
        log_fn=print,
    )

    print("\n" + "=" * 70)
    print(f"KẾT QUẢ PIPELINE: status={res.get('status')} "
          f"days={res.get('days_done')}/{res.get('total_days')} "
          f"calls={res.get('calls')} images={res.get('images')} "
          f"DoD={res.get('definition_of_done', {}).get('met')}")
    print(f"Log: {res.get('log_file')}")
    print("=" * 70)

    # 2) Kiểm tra dữ liệu thật
    c = course_db.get_course(LANG) or {}
    days = c.get("days") or []
    lesson = next((d for d in days if int(d.get("day", 0)) == 1), None)
    if not lesson:
        print("❌ FAIL: không có ngày 1 trong course.json")
        return 1

    vocab = lesson.get("vocab") or []
    quiz = lesson.get("quiz") or {}
    img_refs = [v.get("image_ref") for v in vocab if v.get("image_ref")]
    audio_refs = [v.get("audio_ref") for v in vocab if v.get("audio_ref")]
    fake = [v.get("word", "") for v in vocab if FAKE_RE.search(v.get("word", ""))]

    print(f"\n📊 Ngày 1: {len(vocab)} từ vựng")
    print(f"   Mẫu câu={len(lesson.get('sentence_patterns') or [])} "
          f"câu thông dụng={len(lesson.get('common_sentences') or [])} "
          f"ngữ pháp={len(lesson.get('grammar') or [])}")
    print(f"   Quiz: vocab={len(quiz.get('vocab') or [])} "
          f"pattern={len(quiz.get('pattern') or [])} "
          f"common={len(quiz.get('common') or [])} "
          f"grammar={len(quiz.get('grammar') or [])}")
    print(f"   Ảnh: {len(img_refs)}/{len(vocab)} từ có image_ref")
    print(f"   Audio: {len(audio_refs)}/{len(vocab)} từ có audio_ref")
    print(f"   Từ giả: {len(fake)}")

    # In vài mẫu để thấy dữ liệu thật
    for v in vocab[:3]:
        print(f"   · {v.get('word')} — {v.get('meaning_vi')} "
              f"| img={v.get('image_ref') or '—'} | audio={v.get('audio_ref') or '—'}")

    # 3) Kiểm tra file media thật trên đĩa
    media_ok = 0
    media_missing = []
    for ref in img_refs + audio_refs:
        try:
            from ai.media_resolver import resolve_media_path
            path = resolve_media_path(ref)
            if path and os.path.exists(path):
                media_ok += 1
            else:
                media_missing.append(ref)
        except Exception as e:
            media_missing.append(f"{ref} ({e})")
    print(f"   File media tồn tại: {media_ok}/{len(img_refs) + len(audio_refs)}")
    if media_missing:
        print(f"   ⚠ Media thiếu: {media_missing[:3]}")

    ok = (
        len(vocab) >= 5
        and len(lesson.get("sentence_patterns") or []) > 0
        and len(lesson.get("common_sentences") or []) > 0
        and len(lesson.get("grammar") or []) > 0
        and len(quiz.get("vocab") or []) > 0
        and len(quiz.get("pattern") or []) > 0
        and len(quiz.get("common") or []) > 0
        and len(quiz.get("grammar") or []) > 0
        and len(fake) == 0
        and len(img_refs) > 0
        and len(audio_refs) > 0
        and media_ok >= 1
    )
    print("\n" + ("✅ SMOKE TEST PASS" if ok else "❌ SMOKE TEST FAIL"))
    if not ok:
        print("   Điều kiện: >=5 từ; có mẫu câu + câu thông dụng + ngữ pháp; "
              "quiz đủ 4 loại; 0 từ giả; có ít nhất 1 image_ref + 1 audio_ref "
              "+ 1 file media thật.")
    if not args.keep:
        print("   (Khóa test được giữ lại để kiểm tra; xóa bằng: "
              f"python -c \"from ai import course_db; course_db.delete_course('{LANG}')\")")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
