"""
pipeline_grammar.py — Stage NGỮ PHÁP BỔ SUNG (grammar enrichment).

Mục tiêu: Gemini hay BỎ QUA mảng lồng optional (common_mistakes / mini_quiz) khi
response content lớn. Stage này gọi AI RIÊNG, output nhỏ ⇒ không bị cắt JSON.

Chạy SAU content stage (và sau quiz nếu muốn). Chỉ bổ sung khi lesson còn thiếu
common_mistakes / mini_quiz ⇒ không tốn quota vô ích.

KHÔNG BAO GIỜ raise; media/nội dung lỗi không chặn nội dung chữ.
"""

from __future__ import annotations

from ai.pipeline_store import (STAGE_GRAMMAR_ENRICH, STATUS_DONE, STATUS_DEGRADED,
                               STATUS_SKIPPED, load_checkpoint, save_checkpoint,
                               stage_is_done)


def _needs_enrich(lesson: dict) -> bool:
    """True nếu có ít nhất 1 bài ngữ pháp thiếu common_mistakes hoặc mini_quiz."""
    for g in (lesson.get("grammar") or []):
        if not isinstance(g, dict) or not str(g.get("title", "")).strip():
            continue
        cm = g.get("common_mistakes")
        mq = g.get("mini_quiz")
        if not isinstance(cm, list) or len(cm) == 0:
            return True
        if not isinstance(mq, list) or len(mq) == 0:
            return True
    return False


def _merge_enrichment(lesson: dict, enrich_list: list) -> int:
    """Gộp kết quả enrichment vào lesson grammar (khớp theo title). Trả số bài đã gộp."""
    merged = 0
    by_title = {}
    for g in enrich_list:
        if isinstance(g, dict) and str(g.get("title", "")).strip():
            by_title[str(g["title"]).strip().lower()] = g
    for g in (lesson.get("grammar") or []):
        if not isinstance(g, dict):
            continue
        key = str(g.get("title", "")).strip().lower()
        if not key or key not in by_title:
            continue
        src = by_title[key]
        cm = src.get("common_mistakes")
        mq = src.get("mini_quiz")
        changed = False
        if isinstance(cm, list) and len(cm) > 0:
            g["common_mistakes"] = cm
            changed = True
        if isinstance(mq, list) and len(mq) > 0:
            g["mini_quiz"] = mq
            changed = True
        if changed:
            merged += 1
    return merged


def run_grammar_enrich_stage(language: str, day: int, lesson: dict, coord,
                             log_fn=print, budget=None,
                             force: bool = False) -> dict:
    """Bổ sung common_mistakes + mini_quiz cho ngữ pháp (call AI riêng).

    Trả dict kết quả. KHÔNG BAO GIỜ raise.
    """
    if not force and stage_is_done(language, STAGE_GRAMMAR_ENRICH, day,
                                   allow_degraded=True):
        cp = load_checkpoint(language, STAGE_GRAMMAR_ENRICH, day) or {}
        log_fn(f"   ⏭ Ngữ pháp bổ sung Ngày {day} đã có — bỏ qua.")
        return cp.get("data") or {"skipped": True}

    if not coord:
        save_checkpoint(language, STAGE_GRAMMAR_ENRICH,
                        {"skipped": True, "reason": "no_coordinator"},
                        day=day, status=STATUS_SKIPPED)
        return {"skipped": True, "reason": "no_coordinator"}

    grammars = [g for g in (lesson.get("grammar") or [])
                if isinstance(g, dict) and str(g.get("title", "")).strip()]
    if not grammars:
        save_checkpoint(language, STAGE_GRAMMAR_ENRICH,
                        {"skipped": True, "reason": "no_grammar", "merged": 0},
                        day=day, status=STATUS_SKIPPED)
        return {"skipped": True, "reason": "no_grammar", "merged": 0}

    # Nếu toàn bộ grammar đã đủ common_mistakes + mini_quiz ⇒ không gọi AI.
    if not force and not _needs_enrich(lesson):
        save_checkpoint(language, STAGE_GRAMMAR_ENRICH,
                        {"skipped": True, "reason": "already_complete", "merged": 0},
                        day=day, status=STATUS_DONE)
        return {"skipped": True, "reason": "already_complete", "merged": 0}

    from ai.course_generator import (GRAMMAR_ENRICH_SCHEMA,
                                     build_grammar_enrich_prompt,
                                     parse_grammar_enrich_json)

    try:
        if budget is not None and not budget.can_call(1):
            raise PipelinePauseLocal("Hết ngân sách call — bỏ qua grammar enrichment.")
        res = coord.request(build_grammar_enrich_prompt(language, lesson),
                            response_schema=GRAMMAR_ENRICH_SCHEMA)
    except PipelinePauseLocal as e:
        log_fn(f"   ⚠ {e}")
        save_checkpoint(language, STAGE_GRAMMAR_ENRICH,
                        {"skipped": True, "reason": "budget", "merged": 0},
                        day=day, status=STATUS_DEGRADED)
        return {"skipped": True, "reason": "budget", "merged": 0}
    except Exception as e:
        log_fn(f"   ⚠ Lỗi gọi AI ngữ pháp bổ sung: {type(e).__name__}: {e}")
        save_checkpoint(language, STAGE_GRAMMAR_ENRICH,
                        {"error": f"{type(e).__name__}: {e}", "merged": 0},
                        day=day, status=STATUS_DEGRADED)
        return {"error": str(e), "merged": 0}

    merged = 0
    if res.get("ok"):
        try:
            enrich_list = parse_grammar_enrich_json(res.get("text", ""))
            merged = _merge_enrichment(lesson, enrich_list)
        except Exception as e:
            log_fn(f"   ⚠ Parse ngữ pháp bổ sung lỗi: {type(e).__name__}: {e}")
    else:
        err = res.get("error", {})
        log_fn(f"   ⚠ Ngữ pháp bổ sung thất bại [{err.get('kind')}]: "
               f"{str(err.get('message',''))[:80]}")

    if budget is not None:
        try:
            budget.consume_call()
        except Exception:
            pass

    status = STATUS_DONE if merged > 0 else STATUS_DEGRADED
    data = {"merged": merged, "total_grammar": len(grammars)}
    save_checkpoint(language, STAGE_GRAMMAR_ENRICH, data, day=day, status=status)
    log_fn(f"   📐 Ngữ pháp bổ sung Ngày {day}: gộp {merged}/{len(grammars)} bài.")
    return data


class PipelinePauseLocal(Exception):
    """Pause nội bộ cho module này (tránh import chéo pipeline)."""
    def __init__(self, message, reason=""):
        super().__init__(message)
        self.reason = reason
