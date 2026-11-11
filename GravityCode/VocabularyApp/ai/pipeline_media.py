"""
pipeline_media.py — Các stage media của pipeline (ảnh, audio, hội thoại, verify).

Mỗi stage:
  • Có checkpoint riêng (data/ai_courses/<slug>/_pipeline/days/dNNNN/<stage>.json)
  • Idempotent — chạy lại không tạo trùng
  • Lỗi media KHÔNG BAO GIỜ làm hỏng nội dung chữ
"""

import os

from ai import media_store
from ai.media_schema import DIALOGUE_LIMITS, cefr_for_stage, validate_dialogue
from ai.pipeline_store import (STAGE_AUDIO, STAGE_DIALOGUE, STAGE_IMAGES,
                               STAGE_MEDIA_VERIFY, STATUS_DEGRADED,
                               STATUS_DONE, STATUS_PENDING, STATUS_SKIPPED,
                               load_checkpoint, save_checkpoint, stage_is_done)
from ai.tts_config import stage_index_from_phase, stage_spec, voice_for


# ─── TẦNG ẢNH ────────────────────────────────────────────────────────────────
def run_images_stage(language: str, day: int, lesson: dict, chain, log_fn=print,
                     max_images: int = 10, budget=None, dead_models=None,
                     allow_degraded: bool = True, stop_check=None) -> dict:
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
    if stop_check and stop_check():
        # FIX nút Dừng: ảnh đã sinh vẫn gắn vào vocab (generate ghi ref trực
        # tiếp) — checkpoint PENDING để lần sau sinh nốt, RỒI dừng ngay
        # (không chạy audio/dialogue/verify phía sau khi đã bấm Dừng).
        from ai.course_generator import GenerationStopped
        save_checkpoint(language, STAGE_IMAGES, data, day=day,
                        status=STATUS_PENDING)
        raise GenerationStopped()
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
            item = {"text": w, "kind": "vocab", "index": len(items)}
            # TTS song ngữ cần NGHĨA VIỆT của từ — trước đây không copy ⇒
            # it.get("meaning_vi") luôn None ⇒ đọc lại TỪ NHẬT bằng giọng
            # Việt (thay vì đọc nghĩa). (bug ẩn trong commit 704b2ad)
            mv = str(v.get("meaning_vi") or "").strip()
            if mv:
                item["meaning_vi"] = mv
            items.append(item)

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


def _reattach_audio(lesson: dict, data: dict) -> None:
    """Gắn lại `audio_ref` từ checkpoint vào lesson khi skip (fix log mâu thuẫn).

    Bug đã sửa: skip trả `data` nhưng KHÔNG ghi ref vào lesson ⇒ sau khi content
    sinh lại (vocab mới mất ref), verify báo "thiếu 12 audio" trong CÙNG run với
    log "Audio đã có — bỏ qua". Guard `text == word`: checkpoint cũ trỏ từ KHÁC
    (content đã đổi) ⇒ KHÔNG gắn ref sai vào từ mới — verify sẽ mark pending
    để sinh bù.
    """
    # ── Audio HỘI THOẠI (kind=dialogue) — guard theo TITLE: dialogue sinh lại
    # đổi title ⇒ KHÔNG gắn ref cũ vào hội thoại mới (verify sẽ mark pending).
    dlg_list = (lesson or {}).get("dialogue") or []
    if dlg_list:
        dlg_audio = (lesson or {}).setdefault("media", {}) \
                                 .setdefault("dialogue_audio", {})
        for tr in (data.get("dialogue_tracks") or []):
            if not isinstance(tr, dict):
                continue
            try:
                di = int(tr.get("index", -1))
            except Exception:
                continue
            if not (0 <= di < len(dlg_list)) or not tr.get("ref"):
                continue
            if not isinstance(dlg_list[di], dict):
                continue
            d = dlg_list[di]
            if d.get("audio_ref"):
                continue
            if str(tr.get("text") or "") != str(d.get("title") or ""):
                continue                    # title đổi ⇒ không gắn ref cũ
            dlg_audio[str(di)] = tr["ref"]
            d["audio_ref"] = tr["ref"]

    vocab = (lesson or {}).get("vocab") or []
    if not vocab:
        return
    vocab_audio = lesson.setdefault("media", {}).setdefault("vocab_audio", {})
    for tr in (data.get("tracks") or []):
        if not isinstance(tr, dict) or tr.get("kind") != "vocab":
            continue
        vi = tr.get("index", -1)
        if not (0 <= vi < len(vocab)) or not tr.get("ref"):
            continue
        if str(tr.get("text") or "") != str(vocab[vi].get("word") or ""):
            continue                    # từ đã đổi ⇒ không gắn ref cũ
        if tr.get("variant") == "vi":
            vocab[vi]["meaning_audio_ref"] = tr["ref"]
            continue
        vocab[vi]["audio_ref"] = tr["ref"]
        vocab_audio[vocab[vi].get("word", str(vi))] = tr["ref"]


def run_audio_stage(language: str, day: int, lesson: dict, chain, log_fn=print,
                    max_items: int = 12, budget=None,
                    allow_degraded: bool = True, stop_check=None) -> dict:
    """Sinh âm thanh cho 1 ngày (từ vựng · nghĩa · CÂU · hội thoại).

    FIX 2026-11-11:
      • `stop_check` — bấm Dừng ⇒ dừng giữa chừng, giữ phần đã sinh (PENDING).
      • Make-up chỉ sinh phần THIẾU (từ đã có ref ⇒ KHÔNG TTS lại).
      • Sinh audio HỘI THOẠI (trước đây 0/1.302 hội thoại có audio).
    """
    if stage_is_done(language, STAGE_AUDIO, day, allow_degraded=allow_degraded):
        cp = load_checkpoint(language, STAGE_AUDIO, day) or {}
        data = cp.get("data") or {"skipped": True}
        _reattach_audio(lesson, data)
        log_fn(f"   ⏭  Audio Ngày {day} đã có — bỏ qua.")
        return data

    from ai.course_generator import GenerationStopped
    if stop_check and stop_check():
        raise GenerationStopped()

    stage_idx = stage_index_from_phase(lesson.get("phase", ""))
    items = _audio_items_for(lesson, stage_idx, max_items)
    if not items and not (lesson.get("dialogue") or []):
        # Không có từ VÀ không có hội thoại ⇒ không có gì để đọc.
        save_checkpoint(language, STAGE_AUDIO, {"skipped": True, "tracks": []},
                        day=day, status=STATUS_SKIPPED)
        return {"skipped": True, "tracks": []}

    from ai.tts_generator import synthesize, tts_quota_remaining
    coord = chain.providers[0].coord if (chain and chain.providers) else None

    # Locale của từ vựng theo NGÔN NGỮ KHÓA HỌC (edge_voice "ja-JP-NanamiNeural"
    # → "ja-JP"). Trước đây hardcode "ja-JP" ⇒ khóa học tiếng Trung/Hàn… bị đọc
    # giọng Nhật. Nếu không map được → để "" (synthesize tự chọn theo language).
    _edge = voice_for(language).get("edge_voice") or ""
    _loc_target = "-".join(_edge.split("-")[:2]) if _edge.count("-") >= 1 else ""

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
    # Lỗi TTS tích lũy cho NGÀY NÀY (closure — pipeline chạy 4 luồng song song
    # ⇒ KHÔNG dùng list module-level, sẽ bị race khi clear()).
    audio_errors = []

    vocab_live = lesson.get("vocab") or []
    try:
        from settings import load_settings
        _bilingual = bool((load_settings().get("media") or {})
                          .get("tts_bilingual_mode"))
    except Exception:
        _bilingual = False

    def _one(i_item):
        i, it = i_item
        if stop_check and stop_check():
            return i, None              # đã bấm Dừng — không synth thêm
        errs = []
        # Make-up chỉ sinh phần THIẾU: từ đã có audio_ref (và audio nghĩa nếu
        # bật song ngữ) ⇒ KHÔNG TTS lại toàn bộ (trước đây pass bù tốn ~20
        # file/ngày đã đủ).
        need_jp, need_vi = True, False
        if it["kind"] == "vocab" and 0 <= it.get("index", -1) < len(vocab_live):
            v = vocab_live[it["index"]]
            need_jp = not v.get("audio_ref")
            if _bilingual and it.get("meaning_vi"):
                need_vi = not v.get("meaning_audio_ref")
            if not need_jp and not need_vi:
                return i, ()            # đã đủ 2 loại — bỏ qua
        res_jp, res_vi = None, None
        try:
            if need_jp:
                res_jp = synthesize(language, it["text"], stage_idx=stage_idx,
                                    coord=coord, log_fn=errs.append,
                                    voice=_loc_target)
                if not (res_jp and res_jp.get("path")):
                    res_jp = None
                    if errs:
                        audio_errors.append(f"#{it.get('index')}: {errs[-1]}")
            if need_vi:
                # Chỉ đọc nghĩa khi CÓ meaning_vi thật — trước đây fallback
                # sang it["text"] ⇒ đọc lại từ Nhật bằng giọng Việt.
                vi_raw = str(it.get("meaning_vi") or "").split(",")[0].strip()
                if vi_raw and not (stop_check and stop_check()):
                    try:
                        res_vi = synthesize(language, vi_raw, stage_idx=stage_idx,
                                            coord=coord, log_fn=errs.append,
                                            voice="vi-VN")
                        if not (res_vi and res_vi.get("path")):
                            res_vi = None
                    except Exception as e_vi:
                        errs.append(f"bilingual: {type(e_vi).__name__}: {e_vi}")
        except Exception as e:
            audio_errors.append(f"#{it.get('index')}: {type(e).__name__}: {e}")
            return i, None
        if res_jp and res_vi:
            return i, (res_jp, res_vi)
        if res_jp:
            return i, res_jp
        if res_vi:
            return i, (None, res_vi)     # chỉ thiếu audio nghĩa ⇒ sinh nốt
        return i, None

    with ThreadPoolExecutor(max_workers=6) as ex:
        for i, r in ex.map(_one, list(enumerate(items))):
            results[i] = r

    # Bật đèn lỗi (thay cho nuốt im lặng): in 3 lỗi đầu + tổng số.
    if audio_errors:
        for msg in audio_errors[:3]:
            log_fn(f"   ⚠️ Lỗi TTS Ngày {day}: {msg}")
        if len(audio_errors) > 3:
            log_fn(f"   ⚠️ ...và {len(audio_errors) - 3} lỗi TTS khác.")

    tracks = []
    for it, r in zip(items, results):
        if not r:
            continue
        # TTS song ngữ trả TUPLE (res_jp, res_vi) — trước đây đưa thẳng tuple
        # vào r.get() ⇒ AttributeError (bug ẩn, bị mask bởi TypeError ở trên).
        # Giờ tách từng track: JP (đọc từ) + VI (đọc nghĩa).
        parts = list(r) if isinstance(r, tuple) else [r]
        for pi, res in enumerate(parts):
            if not res or not res.get("path"):
                continue
            is_vi = isinstance(r, tuple) and pi == 1
            entry = media_store.save_audio(
                language, day,
                f"audio_{it['kind']}_{it['index']:02d}"
                f"{'_vi' if is_vi else ''}_"
                f"{media_store.hash_key(it['text'], res.get('engine'))}",
                _read_bytes(res["path"]),
                mime="audio/mpeg" if res["path"].endswith(".mp3") else "audio/wav",
                source="tts", text=it["text"], engine=res.get("engine", ""),
                voice=res.get("voice", ""), rate=res.get("rate", ""),
                kind=f"{it['kind']}_audio")
            if entry:
                tracks.append({
                    "kind": it["kind"], "index": it["index"], "text": it["text"],
                    "ref": entry.get("id"), "engine": res.get("engine"),
                    "file": entry.get("rel_path"),
                    "variant": "vi" if is_vi else "target",
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
        if tr.get("variant") == "vi":
            # Track NGHĨA tiếng Việt — ref phụ, KHÔNG đè audio_ref (mặc định
            # phát âm từ). App chưa đọc field này nhưng dữ liệu được giữ.
            if 0 <= vi < len(vocab):
                vocab[vi]["meaning_audio_ref"] = tr["ref"]
            continue
        if 0 <= vi < len(vocab):
            vocab[vi]["audio_ref"] = tr["ref"]
            vocab_audio[vocab[vi].get("word", str(vi))] = tr["ref"]
        else:
            vocab_audio[str(tr["index"])] = tr["ref"]

    # ── AUDIO HỘI THOẠI (Fix 2026-11-11) ─────────────────────────────────────
    # Web luôn render nút phát hội thoại (media.dialogue_audio[di] || dlg.audio_ref)
    # nhưng KHÔNG stage nào từng sinh ref ⇒ 0/1.302 hội thoại có audio
    # ("nhiều ngày chưa đủ âm thanh"). 1 file/hội thoại — edge-TTS, 0 quota AI.
    dialogues = [d for d in (lesson.get("dialogue") or []) if isinstance(d, dict)]
    dlg_audio = media_map.setdefault("dialogue_audio", {})
    dialogue_tracks = []
    dlg_errs = []
    for di, d in enumerate(dialogues):
        if stop_check and stop_check():
            break
        if dlg_audio.get(str(di)) or d.get("audio_ref"):
            continue                       # đã có — idempotent
        turns = d.get("turns") or []
        text = " … ".join(
            str(t.get("line_target") or t.get("line") or "").strip()
            for t in turns if isinstance(t, dict)
            and (t.get("line_target") or t.get("line"))
        ).strip()
        if not text:
            continue
        try:
            res_d = synthesize(language, text, stage_idx=stage_idx, coord=coord,
                               log_fn=dlg_errs.append, voice=_loc_target)
        except Exception as e_d:
            audio_errors.append(f"dialogue#{di}: {type(e_d).__name__}: {e_d}")
            continue
        if not (res_d and res_d.get("path")):
            if dlg_errs:
                audio_errors.append(f"dialogue#{di}: {dlg_errs[-1]}")
            continue
        entry = media_store.save_audio(
            language, day, f"audio_dialogue_{di:02d}_"
            f"{media_store.hash_key(text, res_d.get('engine'))}",
            _read_bytes(res_d["path"]),
            mime="audio/mpeg" if res_d["path"].endswith(".mp3") else "audio/wav",
            source="tts", text=text, engine=res_d.get("engine", ""),
            voice=res_d.get("voice", ""), rate=res_d.get("rate", ""),
            kind="dialogue_audio")
        if entry:
            ref = entry.get("id")
            dlg_audio[str(di)] = ref
            d["audio_ref"] = ref
            dialogue_tracks.append({"index": di, "text": d.get("title", ""),
                                    "ref": ref, "engine": res_d.get("engine", ""),
                                    "file": entry.get("rel_path")})
            if budget is not None:
                budget.consume_tts()

    stopped = bool(stop_check and stop_check())
    data = {"engine_stage": stage_idx, "tracks": tracks,
            "generated": len(tracks), "dialogue_tracks": dialogue_tracks,
            "skipped": not (tracks or dialogue_tracks)}
    if stopped:
        # Dừng giữa chừng: GIỮ phần đã sinh (refs đã gắn vào lesson),
        # checkpoint PENDING để lần sau sinh nốt — KHÔNG đánh dấu done.
        save_checkpoint(language, STAGE_AUDIO, data, day=day,
                        status=STATUS_PENDING)
        raise GenerationStopped()
    status = STATUS_DONE if (tracks or dialogue_tracks) else (
        STATUS_DEGRADED if allow_degraded else STATUS_SKIPPED)
    save_checkpoint(language, STAGE_AUDIO, data, day=day, status=status)
    log_fn(f"   🔊 Audio Ngày {day}: {len(tracks)} track"
           + (f" + {len(dialogue_tracks)} audio hội thoại"
              if dialogue_tracks else "")
           + f" ({sum(1 for t in tracks if t['kind'] == 'vocab')} gắn vào từ vựng).")
    return data


# ─── TẦNG HỘI THOẠI ──────────────────────────────────────────────────────────
def _validate_dialogues(dialogues: list, lesson: dict) -> list:
    """Chạy media_schema.validate_dialogue() cho từng hội thoại. KHÔNG nâng lỗi."""
    vocab_words = []
    for v in (lesson.get("vocab") or []):
        if isinstance(v, dict):
            w = str(v.get("word", "")).strip()
            if w:
                vocab_words.append(w)
    out = []
    for d in dialogues:
        if not isinstance(d, dict):
            continue
        try:
            out.append(validate_dialogue(d, vocab_words))
        except Exception as e:          # validator không bao giờ được phá stage
            out.append({"ok": False, "errors": [f"validator lỗi: {type(e).__name__}: {e}"],
                        "stats": {}})
    return out


def _dialogue_retry_prompt(prompt: str, invalid: list) -> str:
    """Thêm lời nhắc mạnh hơn khi lần 1 AI không tôn trọng giới hạn hội thoại NGẮN."""
    flat = " | ".join(invalid)[:300]
    max_turns = int(DIALOGUE_LIMITS.get("max_turns", 6))
    max_chars = int(DIALOGUE_LIMITS.get("max_total_chars", 220))
    max_words = int(DIALOGUE_LIMITS.get("max_words_per_line", 8))
    return (
        prompt
        + f"\n\n⚠ CẢNH BÁO NHIỆM VỤ TRƯỚC VI PHẠM GIỚI HẠN: {flat}\n"
        f"- Hãy RÚT NGẮN MỘT TRẦN ĐỘNG HUYẾT: TỐI ĐA {max_turns} lượt, "
        f"TỐI ĐA {max_chars} ký tự tổng, mỗi lượt ≤ {max_words} từ.\n"
        f"- KHÔNG dồn nhiều ý vào một lượt dài — mỗi lượt CHỈ 1 câu NGẮN tự nhiên.\n"
    )


def run_dialogue_stage(language: str, day: int, lesson: dict, coord, log_fn=print,
                       level: str = "", budget=None,
                       allow_degraded: bool = True) -> dict:
    """Sinh hội thoại roleplay cho 1 ngày (gọi AI riêng — không gộp vào content)."""
    if stage_is_done(language, STAGE_DIALOGUE, day, allow_degraded=allow_degraded):
        cp = load_checkpoint(language, STAGE_DIALOGUE, day) or {}
        data = cp.get("data") or {"skipped": True}
        # Fix: skip không re-attach ⇒ lesson.dialogue=0 bị flush vào course.json
        # (mất hội thoại vĩnh viễn vì verify KHÔNG đếm dialogue). Gắn lại ngay.
        if not (lesson.get("dialogue") or []) and (data.get("dialogues") or []):
            lesson["dialogue"] = data["dialogues"]
        log_fn(f"   ⏭  Hội thoại Ngày {day} đã có — bỏ qua.")
        return data

    if not coord:
        save_checkpoint(language, STAGE_DIALOGUE, {"skipped": True, "dialogues": []},
                        day=day, status=STATUS_SKIPPED)
        return {"skipped": True, "dialogues": []}

    from ai.course_generator import (DIALOGUE_SCHEMA, GenerationStopped,
                                     build_dialogue_prompt,
                                     parse_dialogue_json)
    stage_idx = stage_index_from_phase(lesson.get("phase", ""))
    level_tag = cefr_for_stage(stage_idx)
    review = bool(lesson.get("is_review_day"))

    prompt = build_dialogue_prompt(language, lesson, level=level,
                                   level_tag=level_tag, review=review)
    try:
        res = coord.request(prompt, response_schema=DIALOGUE_SCHEMA)
    except GenerationStopped:
        raise
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
        if err.get("kind") == "stopped":
            # FIX nút Dừng (2026-11-11): TRƯỚC đây nuốt lỗi → vẫn lưu checkpoint
            # degraded + chạy tiếp media_verify → "đánh dấu sinh bù lần sau"
            # ngay cả khi người dùng vừa bấm ⏹. Giờ dừng NGAY tại đây.
            raise GenerationStopped()
        log_fn(f"   ⚠ Hội thoại thất bại [{err.get('kind')}]: {str(err.get('message',''))[:80]}")

    # ── KIỂM TRA GIỚI HẠN HỘI THOẠI (6 lượt / 220 ký tự / ≤8 từ mỗi lượt) ──
    validation = _validate_dialogues(dialogues, lesson)
    invalid = [errs for v in validation if not v.get("ok") for errs in (v.get("errors") or [])]
    retried = False
    if dialogues and invalid and res.get("ok"):
        # AI không tuân thủ giới hạn ⇒ thử lại ĐÚNG 1 lần, chỉ khi còn ngân sách.
        if budget is None or getattr(budget, "can_call", lambda n: True)(1):
            log_fn(f"   ⚠ Hội thoại Ngày {day} vi phạm giới hạn — thử lại 1 lần: "
                   f"{('; '.join(invalid))[:200]}")
            try:
                res2 = coord.request(_dialogue_retry_prompt(prompt, invalid),
                                     response_schema=DIALOGUE_SCHEMA)
                if (res2.get("error") or {}).get("kind") == "stopped":
                    raise GenerationStopped()      # dừng ngay (không nuốt)
                if budget is not None:
                    budget.consume_call()
                if res2.get("ok"):
                    dialogues2 = parse_dialogue_json(res2.get("text", ""))
                    v2 = _validate_dialogues(dialogues2, lesson)
                    bad2 = sum(1 for v in v2 if not v.get("ok"))
                    bad1 = sum(1 for v in validation if not v.get("ok"))
                    if dialogues2 and bad2 < bad1:
                        dialogues, validation, retried = dialogues2, v2, True
            except GenerationStopped:
                raise
            except Exception as e:
                log_fn(f"   ⚠ Thử lại hội thoại lỗi: {type(e).__name__}: {e}")
        else:
            log_fn(f"   ⚠ Hết ngân sách — bỏ qua thử lại hội thoại Ngày {day}.")

    # Gắn vào lesson (để web + desktop đọc)
    if dialogues:
        lesson["dialogue"] = dialogues

    data = {"dialogues": dialogues, "generated": len(dialogues), "level_tag": level_tag,
            "validation": {"ok": not invalid, "n_invalid": sum(1 for v in validation
                                                              if not v.get("ok")),
                           "errors": invalid, "retried": retried}}
    status = STATUS_DONE if dialogues else (STATUS_DEGRADED if allow_degraded else STATUS_SKIPPED)
    save_checkpoint(language, STAGE_DIALOGUE, data, day=day, status=status)
    warn = "" if not invalid else f" — ⚠ {sum(1 for v in validation if not v.get('ok'))} kịch bản vi phạm giới hạn"
    log_fn(f"   💬 Hội thoại Ngày {day}: {len(dialogues)} kịch bản ({level_tag}){warn}.")
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

    # Ngày thiếu ref ⇒ đánh dấu lại stage tương ứng là PENDING để sinh bù.
    # Fix 2: GIỮ data cũ khi mark pending (trước đây ghi đè bằng {"pending_reason"}
    # ⇒ phá checkpoint: mất list tracks/images/dialogues đã sinh).
    # Fix đếm thêm DIALOGUE: lesson.dialogue rỗng mà verify không đếm ⇒ checkpoint
    # dialogue vẫn done → skip mãi → hội thoại mất vĩnh viễn trong course.json
    # mà DoD vẫn báo all_days_dialogue=true (lừa).
    n_no_dlg = 0 if (lesson.get("dialogue") or []) else 1

    # FIX 2026-11-11 (âm thanh): trước đây verify CHỈ đếm image_ref/audio_ref
    # của TỪ ⇒ audio NGHĨA (bật song ngữ) và audio HỘI THOẠI thiếu → KHÔNG
    # mark pending → không bao giờ sinh bù ("nhiều ngày chưa đủ âm thanh").
    try:
        from settings import load_settings
        _bilingual = bool((load_settings().get("media") or {})
                          .get("tts_bilingual_mode"))
    except Exception:
        _bilingual = False
    n_no_mean = 0
    if _bilingual:
        for v in vocab:
            if (isinstance(v, dict) and str(v.get("meaning_vi") or "").strip()
                    and v.get("audio_ref") and not v.get("meaning_audio_ref")):
                n_no_mean += 1
    n_no_dlg_aud = 0
    _dlg_list = lesson.get("dialogue") or []
    if _dlg_list:
        _dmap = (lesson.get("media") or {}).get("dialogue_audio") or {}
        for _di, _d in enumerate(_dlg_list):
            if not (isinstance(_d, dict) and
                    (_dmap.get(str(_di)) or _d.get("audio_ref"))):
                n_no_dlg_aud += 1
    n_aud_gap = n_no_aud + n_no_mean + n_no_dlg_aud

    # Ngày thiếu ref ⇒ đánh dấu lại stage tương ứng là PENDING để sinh bù.
    # Fix 2: GIỮ data cũ khi mark pending (trước đây ghi đè bằng {"pending_reason"}
    # ⇒ phá checkpoint: mất list tracks/images/dialogues đã sinh).
    if n_no_img or n_aud_gap or n_no_dlg:
        for stg, cnt in ((STAGE_IMAGES, n_no_img), (STAGE_AUDIO, n_aud_gap),
                         (STAGE_DIALOGUE, n_no_dlg)):
            if cnt > 0:
                try:
                    old = load_checkpoint(language, stg, day) or {}
                    merged = dict(old.get("data") or {})
                    merged["pending_reason"] = f"thiếu {cnt} ref"
                    save_checkpoint(language, stg, merged,
                                    day=day, status=STATUS_PENDING)
                except Exception:
                    pass
        _gap = []
        if n_no_img:
            _gap.append(f"{n_no_img} ảnh")
        if n_no_aud:
            _gap.append(f"{n_no_aud} audio từ")
        if n_no_mean:
            _gap.append(f"{n_no_mean} audio nghĩa")
        if n_no_dlg_aud:
            _gap.append(f"{n_no_dlg_aud} audio hội thoại")
        if n_no_dlg:
            _gap.append(f"{n_no_dlg} hội thoại")
        log_fn(f"   ⚠ Ngày {day} thiếu " + " / ".join(_gap)
               + " — đánh dấu để sinh bù (run này sẽ bù ngay nếu còn ngân sách).")

    result = "pass" if not missing else ("partial" if items else "fail")
    data = {"result": result, "items": items, "missing": missing,
            "no_image_ref": n_no_img, "no_audio_ref": n_aud_gap,
            "no_meaning_audio_ref": n_no_mean,
            "no_dialogue_audio_ref": n_no_dlg_aud,
            "policy": "media_optional", "checked_at": _now()}
    status = STATUS_DONE if result in ("pass", "partial") else STATUS_DEGRADED
    save_checkpoint(language, STAGE_MEDIA_VERIFY, data, day=day, status=status)
    if missing:
        log_fn(f"   ⚠ Thiếu {len(missing)} file media ở Ngày {day}.")
    return data


def _now() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
