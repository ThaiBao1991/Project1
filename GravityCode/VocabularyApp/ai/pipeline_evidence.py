"""
pipeline_evidence.py — Stage DẪN CHỨNG (evidence) cho pipeline.

Dẫn chứng = trích dẫn có thật (Wikipedia / Wiktionary / Commons) cho mỗi từ
vựng, kèm IPA chuẩn và từ nguyên. Nguồn: `ai/evidence.py` (Wikipedia API +
Wiktionary API, không cần API key).

Vì sao là stage RIÊNG (không gộp vào content)?
  • Content gọi Gemini (tốn quota, 20 call/ngày/project/model) — dẫn chứng
    tra bằng HTTP miễn phí ⇒ tách ra để không đụng quota.
  • Wikimedia CHẶN IP sau ~30.000 request ⇒ cần giới hạn số từ/ngày và
    cache bền (đã có trong evidence.py: data/evidence_cache.json).
  • Media lỗi / dẫn chứng thiếu KHÔNG BAO GIỜ chặn nội dung chữ.

Bật stage:  `python -m ai.pipeline --all --stages evidence --full`
           hoặc `--evidence` (bật kèm media/content đang chạy)
"""

from __future__ import annotations

from ai.pipeline_store import (STAGE_EVIDENCE, STATUS_DEGRADED, STATUS_DONE,
                               STATUS_SKIPPED, load_checkpoint, save_checkpoint,
                               stage_is_done)

# Số từ tối đa tra dẫn chứng trong 1 ngày.
# Mỗi từ = 2-3 request Wikimedia ⇒ 10 từ/ngày ≈ 30 request/ngày.
# 30.000 request ⇒ ~1.000 ngày ⇒ đủ cho 8 ngôn ngữ.
MAX_WORDS_PER_DAY = 10


def run_evidence_stage(language: str, day: int, lesson: dict, log_fn=print,
                       max_words: int = MAX_WORDS_PER_DAY, use_ai=None,
                       force: bool = False) -> dict:
    """Gắn dẫn chứng cho từ vựng của 1 ngày. KHÔNG BAO GIỜ raise."""
    if not force and stage_is_done(language, STAGE_EVIDENCE, day, allow_degraded=True):
        cp = load_checkpoint(language, STAGE_EVIDENCE, day) or {}
        log_fn(f"   ⏭ Dẫn chứng Ngày {day} đã có — bỏ qua.")
        return cp.get("data") or {"skipped": True}

    vocab = (lesson or {}).get("vocab") or []
    targets = [v for v in vocab
               if isinstance(v, dict) and str(v.get("word") or "").strip()]
    if not targets:
        save_checkpoint(language, STAGE_EVIDENCE,
                        {"skipped": True, "reason": "no_vocab", "sources": 0},
                        day=day, status=STATUS_SKIPPED)
        return {"skipped": True, "reason": "no_vocab", "sources": 0}

    limit = int(max_words or 0)
    if limit <= 0:
        limit = len(targets)

    try:
        from ai import evidence
        stats = evidence.attach_to_lesson(lesson, language, use_ai=use_ai,
                                          log_fn=log_fn, limit=limit)
    except Exception as e:
        log_fn(f"   ⚠ Dẫn chứng Ngày {day} lỗi: {type(e).__name__}: {e}")
        save_checkpoint(language, STAGE_EVIDENCE,
                        {"error": f"{type(e).__name__}: {e}", "sources": 0},
                        day=day, status=STATUS_DEGRADED)
        return {"error": str(e), "sources": 0}

    n_src = sum(len(v.get("sources") or [])
                for v in vocab if isinstance(v, dict))
    data = {
        "ok": stats.get("ok", 0),
        "cached": stats.get("cached", 0),
        "failed": stats.get("failed", 0),
        "sources": n_src,
        "words": len(targets),
        "limit": limit,
    }
    status = STATUS_DONE if n_src else STATUS_DEGRADED
    save_checkpoint(language, STAGE_EVIDENCE, data, day=day, status=status)
    log_fn(f"   📚 Dẫn chứng Ngày {day}: {stats.get('ok', 0)}/{len(targets)} từ có nguồn "
           f"({stats.get('cached', 0)} từ lấy từ cache).")
    return data
