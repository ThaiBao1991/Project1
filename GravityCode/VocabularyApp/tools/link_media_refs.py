"""
link_media_refs.py — Gắn lại `image_ref` / `audio_ref` cho các ngày đã render.

Bối cảnh: pipeline tạo file media + ghi manifest, nhưng nếu bị kill giữa chừng
hoặc code cũ chưa gắn ref vào lesson ⇒ file có trên đĩa nhưng app không thấy.

Cách làm: khớp theo (lang, day, tên file `word_<idx>_<hash>.<ext>`) cho ảnh và
theo (lang, day, text) cho audio.

Chạy:  python tools/link_media_refs.py [--dry-run]
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)

from ai import course_db, media_store

DRY = "--dry-run" in sys.argv

idx = media_store.load_index()
items = idx.get("items", {})

def _norm_lang(v):
    """Chuẩn hoá tên ngôn ngữ về slug (để khớp giữa 'Tiếng Trung' và 'tiếng_trung')."""
    return re.sub(r"[^a-z0-9]+", "_", str(v or "").strip().lower()).strip("_")


# ảnh: key = (lang_slug, day, word_index)
# audio: key = (lang_slug, day, kind, index)  — khớp theo TÊN FILE (đáng tin hơn
#        vì entry cũ có text=None).
img_by = {}
aud_by = {}
aud_by_text = {}
for e in items.values():
    lang = _norm_lang(e.get("lang"))
    day = e.get("day")
    rel = e.get("rel_path", "") or ""
    if e.get("type") == "image":
        m = re.search(r"word_(\d+)_", rel)
        if m:
            img_by[(lang, day, int(m.group(1)))] = e["id"]
    elif e.get("type") == "audio":
        m = re.search(r"audio_([a-z]+)_(\d+)_", rel)
        if m:
            aud_by[(lang, day, m.group(1), int(m.group(2)))] = e["id"]
        if e.get("text"):
            aud_by_text[(lang, day, e["text"])] = e["id"]

langs = sorted(os.listdir(course_db.COURSES_DIR))
langs = [l for l in langs if not l.startswith("_")
         and os.path.isfile(os.path.join(course_db.COURSES_DIR, l, "course.json"))]

tot_img = tot_aud = tot_days = 0
for slug in langs:
    course = course_db.get_course(slug, apply_v4=False, persist=False)
    if not course:
        continue
    lang = course.get("language") or slug
    lang_n = _norm_lang(lang)
    changed = False
    n_i = n_a = 0
    for lesson in course.get("days", []):
        day = int(lesson.get("day", 0))
        vocab = lesson.get("vocab") or []
        media = lesson.setdefault("media", {})
        va = media.setdefault("vocab_audio", {})
        for i, v in enumerate(vocab):
            if not isinstance(v, dict):
                continue
            # Dọn ref không còn trong manifest (sau reindex, id có thể đổi)
            for fld in ("image_ref", "audio_ref"):
                r = v.get(fld)
                if r and r not in items:
                    v[fld] = None
                    changed = True
            if not v.get("image_ref"):
                ref = (img_by.get((lang_n, day, i))
                       or img_by.get((_norm_lang(slug), day, i)))
                if ref:
                    v["image_ref"] = ref
                    n_i += 1
                    changed = True
            if not v.get("audio_ref"):
                ref = (aud_by.get((lang_n, day, "vocab", i))
                       or aud_by.get((_norm_lang(slug), day, "vocab", i))
                       or aud_by_text.get((lang_n, day, v.get("word") or ""))
                       or aud_by_text.get((_norm_lang(slug), day, v.get("word") or "")))
                if ref:
                    v["audio_ref"] = ref
                    va[v.get("word", str(i))] = ref
                    n_a += 1
                    changed = True
        # dialogue audio
        da = media.setdefault("dialogue_audio", {})
        for di, dlg in enumerate(lesson.get("dialogue") or []):
            if not isinstance(dlg, dict):
                continue
            r = dlg.get("audio_ref")
            if r and r not in items:
                dlg["audio_ref"] = None
                changed = True
            if isinstance(dlg, dict) and not dlg.get("audio_ref"):
                ref = (aud_by.get((lang_n, day, "dialogue", di))
                       or aud_by_text.get((lang_n, day, dlg.get("title") or "")))
                if ref:
                    dlg["audio_ref"] = ref
                    da[str(di)] = ref
                    changed = True
    if changed and not DRY:
        course_db.save_course(slug, course)
    tot_img += n_i
    tot_aud += n_a
    tot_days += len(course.get("days", []))
    print(f"  {slug:20s} gắn ảnh={n_i:5d}  audio={n_a:5d}  "
          f"{'(đã lưu)' if changed and not DRY else '(DRY-RUN)'}")

print(f"\nTỔNG: ảnh {tot_img} · audio {tot_aud}  ({tot_days} ngày)")
if DRY:
    print("DRY-RUN: không ghi gì. Bỏ --dry-run để áp dụng.")
