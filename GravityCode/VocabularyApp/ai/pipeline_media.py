"""
pipeline_media.py — Các stage media của pipeline (ảnh, audio, hội thoại, verify).

Mỗi stage:
  • Có checkpoint riêng (data/ai_courses/<slug>/_pipeline/days/dNNNN/<stage>.json)
  • Idempotent — chạy lại không tạo trùng
  • Lỗi media KHÔNG BAO GIỜ làm hỏng nội dung chữ
"""

import os

from ai import media_store
from ai.media_schema import cefr_for_stage
from ai.pipeline_store import (STAGE_AUDIO, STAGE_DIALOGUE, STAGE_IMAGES,
                               STAGE_MEDIA_VERIFY, STATUS_DEGRADED,
                               STATUS_DONE, STATUS_PENDING, STATUS_SKIPPED,
                               load_checkpoint, save_checkpoint, stage_is_done)
from ai.tts_config import stage_index_from_phase, stage_spec, voice_for


# ─── TẦNG ẢNH ────────────────────────────────────────────────────────────────
def run_images_stage(language: str, day: int, lesson: dict, chain, log_fn=print,
                     max_images: int = 10, budget=None, dead_models=None,
                     allow_degraded: bool = True) -> dict:
    """Sinh ảnh minh họa cho 1 ngày. Trả dict kết quả stage."""
    if stage_is_done(language, STAGE_IMAGES, day, allow_degraded=allow_degraded):
        cp = load_checkpoint(language, STAGE_IMAGES, day) or {}
        log_fn(f"   ⏭ Ảnh Ngày {day} đã có — bỏ qua.")
        return cp.get("data") or {"skipped": True}

    vocab = (lesson or {}).get("vocab") or []
    if not vocab:
        save_checkpoint(language, STAGE_IMAGES, {"skipped": True, "images": []},
                        day=day, status=STATUS_SKIPPED)
        return {"skipped": True, "images": []}

    from ai.image_pipeline import generate_images_for_day
    entries = generate_images_for_day(
        language, day, lesson, coord=(chain.providers[0].coord if chain.providers else None),
        log_fn=log_fn, max_images=max_images, budget=budget,
        dead_models=dead_models, providers=None,
        web_fetcher=(lambda l, d, v: chain.fetch_images(l, d, v, only=["web_ai"]))
        if chain else None)

    data = {
        "requested": len(vocab),
        "generated": len(entries),
        "images": entries,
        "skipped": False,
    }
    status = STATUS_DONE if entries else (STATUS_DEGRADED if allow_degraded else STATUS_SKIPPED)
    save_checkpoint(language, STAGE_IMAGES, data, day=day, status=status)
    return data


# ─── TẦNG AUDIO ──────────────────────────────────────────────────────────────
def _read_bytes(path: str) -> bytes:
    """BUG ĐÃ SỬA (L-L): `open(...).read()` không đóng handle ⇒ rò 25.000+ file
    handle (Windows giới hạn ~32k ⇒ 'Too many open files')."""
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return b""



def _audio_items_for(lesson: dict, stage_idx: int, max_items: int) -> list:
    """Danh sách nội dung cần đọc cho 1 ngày (theo ưu tiên chặng)."""
    items = []
    spec = stage_spec(stage_idx)

    for v in (lesson.get("vocab") or []):
        w = str(v.get("word") or "").strip()
        if w:
            items.append({"text": w, "kind": "vocab", "index": len(items)})

    if spec["unit"] in ("sentence", "paragraph", "idiom"):
        for p in (lesson.get("sentence_patterns") or [])[:4]:
            t = str(p.get("pattern") or "").strip()
            if t:
                items.append({"text": t, "kind": "pattern", "index": len(items)})
        for c in (lesson.get("common_sentences") or [])[:4]:
            t = str(c.get("sentence") or "").strip()
            if t:
                items.append({"text": t, "kind": "common", "index": len(items)})

    if spec["unit"] == "char":
        # Vỡ lòng: đọc từng ký tự
        for v in (lesson.get("vocab") or [])[:6]:
            w = str(v.get("word") or "").strip()
            for ch in w[:3]:
                items.append({"text": ch, "kind": "char", "index": len(items)})
            items = items[:max_items]

    return items[:max_items]


def run_audio_stage(language: str, day: int, lesson: dict, chain, log_fn=print,
                    max_items: int = 12, budget=None,
                    allow_degraded: bool = True) -> dict:
    """Sinh âm thanh cho 1 ngày."""
    if stage_is_done(language, STAGE_AUDIO, day, allow_degraded=allow_degraded):
        cp = load_checkpoint(language, STAGE_AUDIO, day) or {}
        log_fn(f"   ⏭  Audio Ngày {day} đã có — bỏ qua.")
        return cp.get("data") or {"skipped": True}

    stage_idx = stage_index_from_phase(lesson.get("phase", ""))
    items = _audio_items_for(lesson, stage_idx, max_items)
    if not items:
        save_checkpoint(language, STAGE_AUDIO, {"skipped": True, "tracks": []},
                        day=day, status=STATUS_SKIPPED)
        return {"skipped": True, "tracks": []}

    from ai.tts_generator import synthesize, tts_quota_remaining
    coord = chain.providers[0].coord if chain.providers else None

    # Quota TTS hôm nay đã cạn? → đánh dấu PENDING (chưa xong) để chạy lại
    # ngày mai, KHÔNG đánh dấu done (để không bỏ sót vĩnh viễn).
    try:
        remaining = tts_quota_remaining()
    except Exception:
        remaining = 999
    if remaining <= 0:
        log_fn("   🔊 Hết quota TTS hôm nay — bỏ qua audio (chạy lại để tiếp tục).")
        save_checkpoint(language, STAGE_AUDIO,
                        {"skipped": True, "reason": "tts_quota_exhausted", "tracks": []},
                        day=day, status=STATUS_PENDING)
        return {"skipped": True, "reason": "tts_quota_exhausted", "tracks": []}

    # Sinh SONG SONG (TTS là nút thắt cổ chai: 12 track × ~8s nếu tuần tự)
    from concurrent.futures import ThreadPoolExecutor
    results = [{}] * len(items)

    def _one(i_item):
        i, it = i_item
        try:
            return i, synthesize(language, it["text"], stage_idx=stage_idx,
                                 coord=coord, log_fn=None)
        except Exception:
            return i, {}

    with ThreadPoolExecutor(max_workers=6) as ex:
        for i, r in ex.map(_one, list(enumerate(items))):
            results[i] = r

    tracks = []
    for it, r in zip(items, results):
        if not r:
            continue
        entry = media_store.save_audio(
            language, day,
            f"audio_{it['kind']}_{it['index']:02d}_{media_store.hash_key(it['text'], r.get('engine'))}",
            _read_bytes(r["path"]),
            mime="audio/mpeg" if r["path"].endswith(".mp3") else "audio/wav",
            source="tts", text=it["text"], engine=r.get("engine", ""),
            voice=r.get("voice", ""), rate=r.get("rate", ""),
            kind=f"{it['kind']}_audio")
        if entry:
            tracks.append({
                "kind": it["kind"], "index": it["index"], "text": it["text"],
                "ref": entry.get("id"), "engine": r.get("engine"),
                "file": entry.get("rel_path"),
            })
        if budget is not None:
            budget.consume_tts()

    # ── GẮN audio vào TỪ VỰNG + bảng media của ngày ──────────────────────
    # BẮT BUỘC: web + desktop đọc `v["audio_ref"]` và `lesson["media"]["vocab_audio"]`.
    # Nếu không gắn ⇒ file mp3 có trên đĩa nhưng app không tìm thấy.
    vocab = lesson.get("vocab") or []
    media_map = lesson.setdefault("media", {})
    vocab_audio = media_map.setdefault("vocab_audio", {})
    for tr in tracks:
        if tr["kind"] != "vocab":
            continue
        vi = tr["index"]
        if 0 <= vi < len(vocab):
            vocab[vi]["audio_ref"] = tr["ref"]
            vocab_audio[vocab[vi].get("word", str(vi))] = tr["ref"]
        else:
            vocab_audio[str(tr["index"])] = tr["ref"]

    data = {"engine_stage": stage_idx, "tracks": tracks, "generated": len(tracks),
            "skipped": not tracks}
    status = STATUS_DONE if tracks else (STATUS_DEGRADED if allow_degraded else STATUS_SKIPPED)
    save_checkpoint(language, STAGE_AUDIO, data, day=day, status=status)
    log_fn(f"   🔊 Audio Ngày {day}: {len(tracks)} track "
           f"({sum(1 for t in tracks if t['kind'] == 'vocab')} gắn vào từ vựng).")
    return data


# ─── TẦNG HỘI THOẠI ──────────────────────────────────────────────────────────
def run_dialogue_stage(language: str, day: int, lesson: dict, coord, log_fn=print,
                       level: str = "", budget=None,
                       allow_degraded: bool = True) -> dict:
    """Sinh hội thoại roleplay cho 1 ngày (gọi AI riêng — không gộp vào content)."""
    if stage_is_done(language, STAGE_DIALOGUE, day, allow_degraded=allow_degraded):
        cp = load_checkpoint(language, STAGE_DIALOGUE, day) or {}
        log_fn(f"   ⏭  Hội thoại Ngày {day} đã có — bỏ qua.")
        return cp.get("data") or {"skipped": True}

    if not coord:
        save_checkpoint(language, STAGE_DIALOGUE, {"skipped": True, "dialogues": []},
                        day=day, status=STATUS_SKIPPED)
        return {"skipped": True, "dialogues": []}

    from ai.course_generator import (DIALOGUE_SCHEMA, build_dialogue_prompt,
                                     parse_dialogue_json)
    stage_idx = stage_index_from_phase(lesson.get("phase", ""))
    level_tag = cefr_for_stage(stage_idx)
    review = bool(lesson.get("is_review_day"))

    try:
        res = coord.request(build_dialogue_prompt(language, lesson, level=level,
                                                   level_tag=level_tag, review=review),
                            response_schema=DIALOGUE_SCHEMA)
    except Exception as e:
        log_fn(f"   ⚠ Lỗi gọi AI cho hội thoại: {e}")
        res = {"ok": False}

    dialogues = []
    if res.get("ok"):
        try:
            dialogues = parse_dialogue_json(res.get("text", ""))
        except Exception:
            dialogues = []
    else:
        err = res.get("error", {})
        log_fn(f"   ⚠ Hội thoại thất bại [{err.get('kind')}]: {str(err.get('message',''))[:80]}")

    # Gắn vào lesson (để web + desktop đọc)
    if dialogues:
        lesson["dialogue"] = dialogues

    data = {"dialogues": dialogues, "generated": len(dialogues), "level_tag": level_tag}
    status = STATUS_DONE if dialogues else (STATUS_DEGRADED if allow_degraded else STATUS_SKIPPED)
    save_checkpoint(language, STAGE_DIALOGUE, data, day=day, status=status)
    log_fn(f"   💬 Hội thoại Ngày {day}: {len(dialogues)} kịch bản ({level_tag}).")
    return data


# ─── TẦNG KIỂM TRA MEDIA ─────────────────────────────────────────────────────
def run_media_verify_stage(language: str, day: int, lesson: dict, log_fn=print,
                           allow_degraded: bool = True) -> dict:
    """Kiểm tra mọi file media tham chiếu trong 1 ngày có tồn tại thật.

    Đồng thời: nếu từ nào THIẾU ref (vì ngày đó chưa từng được xử lý — các
    run bị kill giữa chừng để lại checkpoint "done" nhưng không có file) thì
    đánh dấu lại stage images/audio là PENDING để lần chạy sau sinh bù.
    """
    index = media_store.load_index()
    items = []
    missing = []

    vocab = lesson.get("vocab") or []
    n_no_img = sum(1 for v in vocab if isinstance(v, dict) and not v.get("image_ref"))
    n_no_aud = sum(1 for v in vocab if isinstance(v, dict) and not v.get("audio_ref"))

    for v in vocab:
        if not isinstance(v, dict):
            continue
        ref = v.get("image_ref")
        if not ref:
            continue
        e = media_store.resolve(index, ref)
        ok = media_store.verify_entry(e) if e else False
        items.append({"ref": ref, "type": "image", "exists": ok})
        if not ok:
            missing.append(ref)
        ref = v.get("audio_ref")
        if not ref:
            continue
        e = media_store.resolve(index, ref)
        ok = media_store.verify_entry(e) if e else False
        items.append({"ref": ref, "type": "audio", "exists": ok})
        if not ok:
            missing.append(ref)

    for key in ("vocab_audio", "dialogue_audio"):
        m = (lesson.get("media") or {}).get(key) or {}
        for ref in m.values():
            e = media_store.resolve(index, ref)
            ok = media_store.verify_entry(e) if e else False
            items.append({"ref": ref, "type": "audio", "exists": ok})
            if not ok:
                missing.append(ref)

    # Ngày thiếu ref ⇒ đánh dấu lại stage tương ứng là PENDING để sinh bù
    if n_no_img or n_no_aud:
        for stg, cnt in ((STAGE_IMAGES, n_no_img), (STAGE_AUDIO, n_no_aud)):
            if cnt > 0:
                try:
                    save_checkpoint(language, stg,
                                    {"pending_reason": f"thiếu {cnt} ref"},
                                    day=day, status=STATUS_PENDING)
                except Exception:
                    pass
        log_fn(f"   ⚠ Ngày {day} thiếu {n_no_img} ảnh / {n_no_aud} audio — "
               f"đánh dấu để sinh bù lần sau.")

    result = "pass" if not missing else ("partial" if items else "fail")
    data = {"result": result, "items": items, "missing": missing,
            "no_image_ref": n_no_img, "no_audio_ref": n_no_aud,
            "policy": "media_optional", "checked_at": _now()}
    status = STATUS_DONE if result in ("pass", "partial") else STATUS_DEGRADED
    save_checkpoint(language, STAGE_MEDIA_VERIFY, data, day=day, status=status)
    if missing:
        log_fn(f"   ⚠ Thiếu {len(missing)} file media ở Ngày {day}.")
    return data


def _now() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
