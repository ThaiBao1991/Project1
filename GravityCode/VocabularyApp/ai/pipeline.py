"""
pipeline.py — Orchestrator TỰ TRỊ: render toàn bộ từ điển + media, không cần con người.

Single source of truth cho cả GUI lẫn CLI.

    python -m ai.pipeline --lang japanese --full
    python -m ai.pipeline --all --full
    python -m ai.pipeline --lang tiếng_anh --status
    python -m ai.pipeline --lang tiếng_anh --dry-run

Luồng stage:
    GLOBAL : profile → backbone → plan
    PER-DAY: content → quiz_ab → quiz_cd → images → audio → dialogue → media_verify → commit

Đặc tính:
  • Checkpoint từng stage (dừng giữa chừng chạy lại là tiếp tục)
  • Budget BỀN trong data/ai_courses/_jobs.json (không mất khi restart)
  • Log JSONL có cấu trúc (data/logs/<slug>_<ts>.log)
  • Tự quyết định fallback, tự chuyển stage, tự dừng mềm khi hết quota
  • Media lỗi KHÔNG bao giờ làm hỏng nội dung chữ
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime

from ai import course_db
from ai.pipeline_log import EVENTS, open_logger, prune_logs
from ai.pipeline_store import (STAGE_AUDIO, STAGE_BACKBONE, STAGE_CONTENT,
                               STAGE_DIALOGUE, STAGE_EVIDENCE, STAGE_IMAGES,
                               STAGE_MEDIA_VERIFY,
                               STAGE_PLAN, STAGE_PROFILE, STAGE_QUIZ_AB,
                               STAGE_QUIZ_CD, STAGES, STATUS_DEGRADED,
                               STATUS_DONE, STATUS_FAILED, STATUS_SKIPPED,
                               atomic_write_json, bump_counters,
                               clear_stale_running, day_stage_path,
                               get_language_job, is_dead_model, list_pipeline_languages,
                               load_checkpoint, load_dead_models, load_jobs,
                               load_state, mark_dead_model, pipeline_dir,
                               record_run, rotate_backup, save_checkpoint,
                               save_jobs, save_state, stage_is_done,
                               stage_path, state_path)

# ─── Hằng số ngân sách ──────────────────────────────────────────────────────
# Sức chứa thật (đo 2026-10-21):
#   90 key = 10 project_id × 9 account (mỗi key 1 project, 1 account)
#   Quota Gemini free tier = 20 call/ngày / PROJECT / MODEL
#   ⇒ 10 project × 10 model × 20 = 2.000 call/ngày (thực tế ~1.200 vì ~1/3 key chết)
#   ⇒ 3.010 ngày dialogue ≈ 2-3 ngày chạy nền (pipeline tự resume mỗi ngày)
MAX_CALLS_PER_DAY = 1400
MAX_IMAGES_PER_DAY = 60
MAX_CALLS_PER_LANGUAGE = 20000
MAX_IMAGES_PER_LANGUAGE = 5000
# TTS dùng QUOTA METRIC KHÁC với generateContent (đo thật: TTS chạy ổn khi
# generateContent đã 429) ⇒ tách ngân sách riêng.
MAX_TTS_PER_DAY = 3000
MAX_TTS_PER_LANGUAGE = 40000
MAX_RUN_SECONDS = 6 * 3600
MAX_STAGE_ATTEMPTS = {
    STAGE_CONTENT: 3, STAGE_QUIZ_AB: 3, STAGE_QUIZ_CD: 3,
    STAGE_IMAGES: 3, STAGE_AUDIO: 2, STAGE_DIALOGUE: 2,
    STAGE_PROFILE: 2, STAGE_BACKBONE: 3,
}
MAX_DEFERRED_PASSES = 3

# Exit codes
EXIT_OK = 0
EXIT_INTERNAL = 70
EXIT_DISK = 74
EXIT_CONFIG = 78
EXIT_TEMPORARY = 75
EXIT_INTERRUPT = 130


class PipelineBudget:
    """Bộ đếm bền — persist trong _jobs.json, không chỉ nằm trong RAM."""

    def __init__(self, job=None, max_calls_per_day=MAX_CALLS_PER_DAY,
                 max_images_per_day=MAX_IMAGES_PER_DAY,
                 max_calls_per_language=MAX_CALLS_PER_LANGUAGE,
                 max_images_per_language=MAX_IMAGES_PER_LANGUAGE,
                 max_tts_per_day=MAX_TTS_PER_DAY,
                 max_tts_per_language=MAX_TTS_PER_LANGUAGE):
        self.job = job if job is not None else {}
        self.max_calls_per_day = max_calls_per_day
        self.max_images_per_day = max_images_per_day
        self.max_calls_per_language = max_calls_per_language
        self.max_images_per_language = max_images_per_language
        self.max_tts_per_day = max_tts_per_day
        self.max_tts_per_language = max_tts_per_language

    @property
    def counters(self):
        return self.job.setdefault("counters", {})

    def can_call(self, n=1) -> bool:
        c = self.counters
        return (int(c.get("calls_today", 0)) + n <= self.max_calls_per_day
                and int(c.get("calls_total", 0)) + n <= self.max_calls_per_language)

    def can_image(self, n=1) -> bool:
        c = self.counters
        return (int(c.get("images_today", 0)) + n <= self.max_images_per_day
                and int(c.get("images_total", 0)) + n <= self.max_images_per_language)

    def can_tts(self, n=1) -> bool:
        c = self.counters
        return (int(c.get("tts_today", 0)) + n <= self.max_tts_per_day
                and int(c.get("tts_total", 0)) + n <= self.max_tts_per_language)

    def consume_call(self, n=1):
        bump_counters(self.job, calls=n)

    def consume_image(self, n=1):
        bump_counters(self.job, images=n)

    def consume_tts(self, n=1):
        bump_counters(self.job, tts=n)


class PipelineAbort(Exception):
    def __init__(self, message, code=EXIT_INTERNAL, reason=""):
        super().__init__(message)
        self.code = code
        self.reason = reason


class PipelinePause(Exception):
    def __init__(self, message, reason=""):
        super().__init__(message)
        self.reason = reason


# ─── Definition of Done ──────────────────────────────────────────────────────
def evaluate_dod(language: str, allow_degraded: bool = True) -> dict:
    """13 kiểm tra boolean — mô tả trạng thái 'đã render xong' của 1 ngôn ngữ."""
    checks = {}
    course = course_db.get_course(language, apply_v4=False, persist=False)
    days = (course or {}).get("days") or []

    prof = load_checkpoint(language, STAGE_PROFILE)
    checks["profile_done"] = bool(prof and prof.get("status") in
                                  (STATUS_DONE, STATUS_DEGRADED))
    bb = load_checkpoint(language, STAGE_BACKBONE)
    bb_items = ((bb or {}).get("data") or {}).get("items") or []
    checks["backbone_done"] = bool(bb and bb.get("status") == STATUS_DONE and bb_items)

    plan = load_checkpoint(language, STAGE_PLAN)
    plan_days = ((plan or {}).get("data") or {}).get("days") or []
    checks["plan_complete"] = bool(plan_days and len(plan_days) == len(plan_days))

    def _stage_all_done(stage, require_content=False):
        if not days:
            return False
        for d in days:
            if not stage_is_done(language, stage, d.get("day"), allow_degraded=allow_degraded):
                return False
        return True

    checks["all_days_content"] = _stage_all_done(STAGE_CONTENT)
    checks["all_days_quiz_ab"] = _stage_all_done(STAGE_QUIZ_AB)
    checks["all_days_quiz_cd"] = _stage_all_done(STAGE_QUIZ_CD)
    checks["all_days_images"] = _stage_all_done(STAGE_IMAGES)
    checks["all_days_audio"] = _stage_all_done(STAGE_AUDIO)
    checks["all_days_dialogue"] = _stage_all_done(STAGE_DIALOGUE)
    checks["media_verified"] = _stage_all_done(STAGE_MEDIA_VERIFY)

    checks["course_json_consistent"] = bool(
        days and all(
            isinstance(d.get("quiz"), dict)
            and d.get("quiz", {}).get("vocab") is not None
            and d.get("vocab") is not None
            for d in days))

    prog = course_db.get_progress(language) or {}
    checks["progress_json_updated"] = bool((prog.get("pipeline") or {}).get("status"))

    return {"met": all(checks.values()), "checks": checks,
            "days": len(days), "plan_days": len(plan_days)}


# ─── Orchestrator ────────────────────────────────────────────────────────────
def run_pipeline(language: str, *,
                 words_per_day: int = 10,
                 level: str = None,
                 stages=None,
                 full: bool = False,
                 mode: str = "full",
                 target_days: int = None,
                 from_day: int = 1,
                 to_day: int = None,
                 resume: bool = True,
                 force_new: bool = False,
                 media: bool = True,
                 allow_degraded: bool = False,
                 budget: PipelineBudget = None,
                 chain=None,
                 flush_every_days: int = 10,
                 wait_quota: bool = False,
                 log_fn=None,
                 on_progress=None,
                 stop_check=None,
                 coordinator_cls=None,
                 max_images_per_day: int = 10,
                 max_audio_per_day: int = 12,
                 max_run_seconds: int = MAX_RUN_SECONDS,
                 evidence: bool = False,
                 workers: int = 1) -> dict:
    """Chạy pipeline cho 1 ngôn ngữ. Tự quyết định mọi thứ.

    Trả dict:
      {"ok", "status": done|paused|aborted, "language", "run_id", "total_days",
       "days_done", "calls", "images", "definition_of_done", "errors",
       "log_file", "elapsed_s", "next_resume_command"}
    """
    from ai.course_generator import (DEFAULT_LEVEL, LEVELS, GenerationStopped,
                                     build_master_backbone, get_language_native_profile,
                                     parse_content_json, parse_dialogue_json,
                                     parse_quiz_json, build_dialogue_prompt,
                                     DIALOGUE_SCHEMA)
    from ai.pipeline_media import (run_audio_stage, run_dialogue_stage,
                                    run_images_stage, run_media_verify_stage)
    from ai.providers import ProviderChain

    # ── CHẾ ĐỘ ────────────────────────────────────────────────────────────
    #   full  : sinh lại backbone + content + quiz + media (dùng cho khóa mới)
    #   media : GIỮ NGUYÊN content/quiz sẵn có, chỉ thêm ảnh + audio + hội thoại
    #   enrich: media + regenerate content để có field v4 (ipa, phonetic_note, ...)
    if mode not in ("full", "media", "enrich"):
        mode = "full"

    if full:
        level = level or LEVELS[0]
        stages = list(STAGES)
    level = level or DEFAULT_LEVEL
    stages = list(stages or STAGES)
    if mode in ("media", "enrich"):
        # Không sinh lại backbone/plan/profile — dùng cái có sẵn trong course.json
        stages = [s for s in stages if s not in (STAGE_BACKBONE, STAGE_PLAN,
                                                STAGE_PROFILE)]
        if mode == "media":
            stages = [s for s in stages if s not in (STAGE_CONTENT, STAGE_QUIZ_AB,
                                                    STAGE_QUIZ_CD)]
        else:
            # enrich: regenerate CONTENT (để có field v4) + media, GIỮ NGUYÊN quiz cũ
            stages = [s for s in stages if s not in (STAGE_QUIZ_AB, STAGE_QUIZ_CD)]
    if not media:
        stages = [s for s in stages if s not in
                  (STAGE_IMAGES, STAGE_AUDIO, STAGE_DIALOGUE, STAGE_MEDIA_VERIFY)]
    if evidence and STAGE_EVIDENCE not in stages:
        # Stage TÙY CHỌN: tra Wikimedia (IP bị chặn sau ~30.000 request) ⇒ bật tay.
        stages = list(stages) + [STAGE_EVIDENCE]

    run_id = f"{datetime.now():%Y-%m-%dT%H-%M-%S}__{course_db.lang_slug(language)}"
    log = open_logger(language, run_id, level="info")
    log.context(lang=language)

    def emit(msg=""):
        if log_fn:
            try:
                log_fn(msg)
            except Exception:
                pass

    def progress(pct, stage=None, day=None):
        if on_progress:
            try:
                on_progress({"pct": pct, "stage": stage, "day": day})
            except Exception:
                pass

    jobs = load_jobs()
    job = get_language_job(jobs, language)
    budget = budget or PipelineBudget(job=job)
    chain = chain or ProviderChain.default(log_fn=log_fn or log.info)

    t0 = time.time()
    errors = []
    status = "done"
    exit_code = EXIT_OK
    # BUG ĐÃ SỬA (L-C): kiểm tra provider TRƯỚC khi lấy `.coord` — nếu provider
    # không khả dụng thì `.coord` có thể ném AttributeError che mất nguyên nhân thật.
    _prov_ok, _prov_reason = (chain.providers[0].available() if chain.providers
                              else (False, "no provider"))
    coord = chain.providers[0].coord if (_prov_ok and chain.providers) else None
    # BUG ĐÃ SỬA (L-C/L-F): các biến dùng ở `return` cuối PHẢI khởi tạo trước
    # `try` — nếu exception xảy ra sớm thì `plan`/`done_days` chưa gán ⇒
    # UnboundLocalError che mất nguyên nhân thật.
    plan = []
    done_days = 0
    course = {}

    log.event("run.start", msg=f"Bắt đầu pipeline: stages={','.join(stages)}",
              language=language, level=level, full=full, resume=resume)

    try:
        # ── Chuẩn bị ──────────────────────────────────────────────────────
        stale = clear_stale_running(language)
        if stale:
            log.warn("checkpoint.invalid", msg=f"Xoá {stale} checkpoint 'running' quá hạn.")
        if not resume:
            _reset_pipeline(language)
        if force_new:
            from ai.pipeline_store import restore_backup, pipeline_dir
            import shutil
            rotate_backup(course_db.course_path(language))
            rotate_backup(course_db.progress_path(language))
            log.warn("backup.rotate", msg="Đã backup course.json/progress.json trước khi xoá.")
            course_db.delete_course(language)
            course_db.reset_progress(language)
            # Xóa toàn bộ checkpoint cũ để không bị stage "done" stale từ lần chạy trước
            pdir = pipeline_dir(language)
            if os.path.isdir(pdir):
                shutil.rmtree(pdir, ignore_errors=True)
                log.warn("checkpoint.clear", msg=f"Đã xóa checkpoints cũ tại {pdir}")

        # ── Kiểm tra key ───────────────────────────────────────────────────
        ok, reason = chain.providers[0].available() if chain.providers else (False, "no provider")
        if not ok:
            raise PipelineAbort(f"Không có provider AI khả dụng: {reason}", EXIT_CONFIG, "no_key")

        # BUG ĐÃ SỬA (L-F): `get_course()` trả None khi file JSON hỏng ⇒ trước đây
        # `course = {}` rồi `save_course()` GHI ĐÈ file course.json hỏng bằng khóa
        # học rỗng ⇒ mất trọn khóa học 14-25 MB. Giờ: khôi phục từ .bak hoặc
        # dừng an toàn, TUYỆT ĐỐI không ghi đè dữ liệu.
        cpath = course_db.course_path(language)
        if os.path.isfile(cpath):
            try:
                with open(cpath, "r", encoding="utf-8") as _fp:
                    json.load(_fp)
                course = course_db.get_course(language) or {}
            except Exception as _e:
                from ai.pipeline_store import restore_backup
                restored = restore_backup(cpath)
                if restored:
                    log.warn("backup.restore",
                             msg=f"Khóa học bị hỏng — đã khôi phục từ {os.path.basename(restored)}")
                    course = course_db.get_course(language) or {}
                else:
                    raise PipelineAbort(
                        f"Khóa học '{language}' bị hỏng và không có bản backup: {_e}. "
                        f"KHÔNG ghi đè file. Hãy sửa file thủ công.",
                        EXIT_CONFIG, "course_corrupt")
        else:
            course = {}
        if not course:
            course = course_db.new_course(language, [], max(1, words_per_day))
            course["level"] = level
            course_db.save_course(language, course)
            course = course_db.get_course(language) or course
            # Nếu chế độ media/enrich nhưng chưa có course, phải tự sinh profile/backbone/plan
            if mode in ("media", "enrich"):
                for s in (STAGE_PROFILE, STAGE_BACKBONE, STAGE_PLAN):
                    if s not in stages:
                        stages.append(s)
                emit(f"🆕 Tạo course trống cho '{language}' — thêm stage profile/backbone/plan vào pipeline.")

        # ── STAGE GLOBAL ───────────────────────────────────────────────────
        fsi = None
        if STAGE_PROFILE in stages:
            fsi = _stage_profile(language, coord, log, budget, emit, resume)
            progress(2, STAGE_PROFILE)
        else:
            fsi = _cached_profile(language)

        if STAGE_BACKBONE in stages:
            _stage_backbone(language, level, fsi, coord, log, budget, emit, resume, course)
            progress(8, STAGE_BACKBONE)

        plan = []
        if STAGE_PLAN in stages:
            plan = _stage_plan(language, level, log, emit, resume, course)
            progress(12, STAGE_PLAN)
        else:
            plan = _plan_from_existing_days(course)
            emit(f"📋 Dùng plan có sẵn: {len(plan)} ngày (chế độ {mode}).")

        # ── Áp dụng target_days nếu người dùng chọn số ngày cụ thể ──
        if target_days and int(target_days) > 0 and plan:
            want = int(target_days)
            if len(plan) > want:
                plan = plan[:want]
                emit(f"🎯 Giới hạn plan còn {want} ngày theo lựa chọn của bạn (cắt từ {len(plan)} ngày).")
            else:
                emit(f"📋 Plan có {len(plan)} ngày, nhỏ hơn hoặc bằng target_days={want}, giữ nguyên.")

        # ── STAGE PER-DAY ──────────────────────────────────────────────────
        if not plan:
            log.warn("stage.skip", msg="Không có plan — bỏ qua vòng lặp ngày.")
        days_to_do = [p for p in plan
                      if from_day <= int(p.get("day", 0)) <= (to_day or 10 ** 9)]
        total = len(days_to_do) or 1
        done_days = 0

        if workers and workers > 1:
            done_days = _run_days_parallel(
                language, days_to_do, course, coord, log, budget, emit, stages,
                level, allow_degraded, max_images_per_day, max_audio_per_day,
                chain, resume, total, progress, stop_check, t0, max_run_seconds,
                workers)
        else:
            for idx, pday in enumerate(days_to_do):
                if stop_check and stop_check():
                    raise GenerationStopped()
                if time.time() - t0 > max_run_seconds:
                    raise PipelinePause("Đạt giới hạn thời gian chạy.", "max_run_seconds")
                if not budget.can_call(4):
                    raise PipelinePause("Đạt ngân sách call hôm nay.", "budget")

                dnum = int(pday.get("day", 0))
                log.context(lang=language, stage=STAGE_CONTENT, day=dnum)
                lesson = _run_day(language, dnum, pday, course, coord, log, budget, emit,
                                   stages, level, allow_degraded, max_images_per_day,
                                   max_audio_per_day, chain, resume)
                if lesson:
                    done_days += 1
                progress(12 + int(80 * (idx + 1) / total), STAGE_CONTENT, dnum)
                if (idx + 1) % flush_every_days == 0:
                    course_db.save_course(language, course)
                    log.event("course.flush", msg=f"Đã flush course.json ({idx+1}/{total})")

        # ── Commit ─────────────────────────────────────────────────────────
        course_db.save_course(language, course)
        dod = evaluate_dod(language, allow_degraded=allow_degraded)
        _write_progress_pipeline(language, job, dod, run_id, level, total)

        status = "done" if dod["met"] else "paused"
        if status == "paused":
            exit_code = EXIT_OK
        log.event("run.end", msg=f"Kết thúc: {status}", dod=dod["met"],
                  days_done=done_days)

    except GenerationStopped:
        status, exit_code = "paused", EXIT_OK
        log.event("user.stop", msg="Người dùng dừng — checkpoint đầy đủ, chạy lại là tiếp tục.")
    except PipelinePause as e:
        status, exit_code = "paused", EXIT_OK
        log.event("budget.pause", msg=str(e), reason=e.reason)
    except PipelineAbort as e:
        status, exit_code = "aborted", e.code
        errors.append(str(e))
        log.event("run.abort", msg=str(e), reason=e.reason)
    except OSError as e:
        import errno
        status = "aborted"
        exit_code = EXIT_DISK if getattr(e, "errno", None) in (28, 39) else EXIT_INTERNAL
        errors.append(f"OSError: {e}")
        log.event("disk.full" if exit_code == EXIT_DISK else "run.abort", msg=str(e))
    except Exception as e:
        status, exit_code = "aborted", EXIT_INTERNAL
        errors.append(f"{type(e).__name__}: {e}")
        log.event("run.abort", msg=f"{type(e).__name__}: {e}")
    finally:
        # Lưu trạng thái + job
        try:
            from ai import media_store
            n = media_store.flush_index()
            if n:
                log.info("checkpoint.write", msg=f"Đã ghi manifest media ({n} entry chờ ghi).")
        except Exception:
            pass
        st = load_state(language)
        st["run_id"] = run_id
        st["counters"] = budget.counters
        save_state(language, st)
        jobs = load_jobs()
        job = get_language_job(jobs, language)
        job["counters"] = budget.counters
        job["status"] = status
        job["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        dod = evaluate_dod(language, allow_degraded=allow_degraded)
        job["definition_of_done"] = dod
        record_run(jobs, run_id, {
            "language": language, "status": status, "exit_code": exit_code,
            "started_at": run_id.split("__")[0], "ended_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "calls": budget.counters.get("calls_total", 0),
            "images": budget.counters.get("images_total", 0),
            "log": log.path,
            "cli": f"python -m ai.pipeline --lang {course_db.lang_slug(language)} --full",
        })
        save_jobs(jobs)
        log.close()

    elapsed = time.time() - t0
    return {
        "ok": status == "done",
        "status": status,
        "exit_code": exit_code,
        "language": language,
        "run_id": run_id,
        "level": level,
        "total_days": len(plan),
        "days_done": done_days,
        "calls": budget.counters.get("calls_total", 0),
        "images": budget.counters.get("images_total", 0),
        "definition_of_done": dod,
        "errors": errors,
        "log_file": log.path,
        "elapsed_s": round(elapsed, 1),
        "next_resume_command": f"python -m ai.pipeline --lang {course_db.lang_slug(language)} --full",
    }


# ─── Các stage con ───────────────────────────────────────────────────────────
def _stage_profile(language, coord, log, budget, emit, resume):
    """AI Profiler — quy mô ngày chuẩn Bản xứ C2. 0-1 call (có cache)."""
    if resume and stage_is_done(language, STAGE_PROFILE):
        cp = load_checkpoint(language, STAGE_PROFILE) or {}
        emit("ℹ️ Hồ sơ ngôn ngữ đã có — bỏ qua.")
        return (cp.get("data") or {}).get("profile") or _cached_profile(language)

    from ai.course_generator import get_language_native_profile
    try:
        prof = get_language_native_profile(language, coord=coord, log_fn=log.info)
    except Exception as e:
        log.error("stage.fail", msg=f"Profiler lỗi: {e}", stage=STAGE_PROFILE)
        prof = _cached_profile(language)
    data = {"profile": prof, "source": "ai" if prof.get("is_ai_reasoned") else "fallback"}
    save_checkpoint(language, STAGE_PROFILE, data, status=STATUS_DONE)
    if budget:
        budget.consume_call()
    emit(f"📐 Hồ sơ ngôn ngữ: {prof.get('total_days')} ngày, "
         f"6 chặng {prof.get('stage_days')}")
    return prof


def _cached_profile(language):
    try:
        from ai.language_profiler import get_or_create_language_profile
        return get_or_create_language_profile(language, coord=None, log_fn=lambda *a: None)
    except Exception:
        return {}


def _stage_backbone(language, level, fsi, coord, log, budget, emit, resume, course):
    """Backbone 3 lớp — khung giáo trình bắt buộc."""
    if resume and stage_is_done(language, STAGE_BACKBONE):
        cp = load_checkpoint(language, STAGE_BACKBONE) or {}
        items = (cp.get("data") or {}).get("items") or []
        if items:
            emit("ℹ️ Backbone đã có — bỏ qua.")
            return items

    from ai.course_generator import build_master_backbone
    try:
        bb = build_master_backbone(language, fsi, coord, log.info, None)
    except Exception as e:
        log.error("stage.fail", msg=f"Backbone lỗi: {e}", stage=STAGE_BACKBONE)
        bb = {"items": course.get("backbone", {}).get("items") or []}
    items = bb.get("items") or []
    save_checkpoint(language, STAGE_BACKBONE, bb, status=STATUS_DONE if items else STATUS_FAILED)
    if items:
        course["backbone"] = bb
        course_db.save_course(language, course)
    emit(f"🧱 Backbone: {len(items)} chủ đề.")
    return items


def _stage_plan(language, level, log, emit, resume, course):
    """Plan — danh sách ngày (tất định, derive từ backbone)."""
    from ai.course_generator import _get_item_phase
    bb = load_checkpoint(language, STAGE_BACKBONE) or {}
    items = (bb.get("data") or {}).get("items") or []
    if not items:
        items = (course.get("backbone") or {}).get("items") or []
    days = []
    for i, it in enumerate(items, 1):
        days.append({
            "day": i,
            "backbone_id": it.get("id", i),
            "title": it.get("title") or it.get("generic_name", ""),
            "phase": _get_item_phase(it),
            "stage_idx": it.get("stage_idx"),
            "is_review_day": bool(it.get("is_review_day")),
            "is_ai_inserted": bool(it.get("is_ai_inserted")),
            "words": [],
        })
    data = {"total_days": len(days), "days": days}
    save_checkpoint(language, STAGE_PLAN, data, status=STATUS_DONE if days else STATUS_FAILED)
    course["plan"] = days
    course["total_days"] = len(days)
    course["level"] = level
    course_db.save_course(language, course)
    emit(f"📋 Plan: {len(days)} ngày.")
    return days


def _plan_from_existing_days(course: dict) -> list:
    """Dựng plan từ các ngày ĐÃ CÓ trong course.json (chế độ media/enrich)."""
    out = []
    for d in (course.get("days") or []):
        try:
            n = int(d.get("day", 0))
        except (TypeError, ValueError):
            continue
        if n <= 0:
            continue
        out.append({
            "day": n,
            "backbone_id": d.get("backbone_id"),
            "title": d.get("title", ""),
            "phase": d.get("phase", ""),
            "stage_idx": d.get("stage_idx"),
            "is_review_day": bool(d.get("is_review_day")),
            "words": [],
        })
    out.sort(key=lambda p: p["day"])
    return out


def _run_days_parallel(language, days_to_do, course, coord, log, budget, emit,
                       stages, level, allow_degraded, max_images, max_audio,
                       chain, resume, total, progress, stop_check, t0,
                       max_run_seconds, workers=1):
    """Xử lý N ngày SONG SONG. Mỗi ngày độc lập; chỉ save course.json có lock."""
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    save_lock = threading.Lock()
    state = {"done": 0, "completed": 0, "last_flush": 0}
    emit_safe = emit or (lambda *a, **kw: None)

    def _one(pday):
        dnum = int(pday.get("day", 0))
        if stop_check and stop_check():
            return dnum, None, "stopped"
        if time.time() - t0 > max_run_seconds:
            return dnum, None, "timeout"
        if not budget.can_call(4):
            return dnum, None, "budget"
        try:
            lesson = _run_day(language, dnum, pday, course, coord, log, budget,
                              emit_safe, stages, level, allow_degraded, max_images,
                              max_audio, chain, resume, save_each_day=False)
            return dnum, lesson, ""
        except Exception as e:
            return dnum, None, f"{type(e).__name__}: {e}"

    with ThreadPoolExecutor(max_workers=max(1, min(workers, 8))) as ex:
        futs = {ex.submit(_one, p): p for p in days_to_do}
        for fut in as_completed(futs):
            dnum, lesson, err = fut.result()
            if err == "stopped":
                raise GenerationStopped()
            if err == "timeout":
                raise PipelinePause("Đạt giới hạn thời gian chạy.", "max_run_seconds")
            if err == "budget":
                raise PipelinePause("Đạt ngân sách call hôm nay.", "budget")
            if err:
                log.error("day.fail", msg=f"Ngày {dnum} lỗi: {err}", day=dnum)
                continue
            with save_lock:
                state["done"] += 1
                if lesson:
                    state["completed"] += 1
                done = state["done"]
                if done % 10 == 0:
                    try:
                        course_db.save_course(language, course)
                    except Exception:
                        pass
            progress(12 + int(80 * done / total), STAGE_CONTENT, dnum)
            log.event("day.ok", msg=f"Ngày {dnum} hoàn tất", day=dnum)

    with save_lock:
        course_db.save_course(language, course)
        # Sort 1 lần khi kết thúc lô (không sort từng ngày — xem L-J)
        try:
            days = course.get("days") or []
            days.sort(key=lambda d: int(d.get("day", 0)))
        except Exception:
            pass
        course_db.save_course(language, course)
    emit(f"✅ Đã xử lý {state['done']}/{total} ngày ({workers} luồng song song).")
    return state["completed"]


def _run_day(language, day_num, pday, course, coord, log, budget, emit, stages,
             level, allow_degraded, max_images, max_audio, chain, resume,
             save_each_day=True):
    """Chạy 7 stage của 1 ngày. Trả lesson dict hoặc None."""
    from ai.course_generator import (DIALOGUE_SCHEMA, build_content_prompt,
                                     build_dialogue_prompt, build_quiz_prompt_ab,
                                     build_quiz_prompt_cd, normalize_lesson,
                                     parse_content_json, parse_dialogue_json,
                                     parse_quiz_json)
    from ai.pipeline_media import (run_audio_stage, run_dialogue_stage,
                                    run_images_stage, run_media_verify_stage)

    days = course.setdefault("days", [])
    lesson = next((d for d in days if int(d.get("day", 0)) == day_num), None)
    if lesson is None:
        if STAGE_CONTENT not in stages:
            # Chế độ media: ngày chưa có content → bỏ qua (không tạo rỗng)
            log.warn("day.skip", msg=f"Ngày {day_num} chưa có content — bỏ qua.",
                     day=day_num)
            return None
        lesson = {"day": day_num, "title": pday.get("title", ""),
                  "phase": pday.get("phase", ""), "level": level,
                  "topic": pday.get("title", ""), "words": [],
                  "format_version": 4}
        days.append(lesson)
    lesson.setdefault("quiz", {})
    for k in ("vocab", "pattern", "common", "grammar", "mixed"):
        lesson["quiz"].setdefault(k, [])

    # ── STAGE CONTENT ─────────────────────────────────────────────────────────
    if STAGE_CONTENT in stages and not stage_is_done(language, STAGE_CONTENT, day_num):
        if not budget.can_call(2):
            raise PipelinePause("Hết ngân sách call — dừng trước khi sinh content.", "budget")
        ok, data, err = _ask_with_retry(
            coord, build_content_prompt(language, day_num, len(course.get("plan") or [day_num]),
                                        pday.get("words") or [], pday.get("title", ""),
                                        level, pday.get("phase", "")),
            None, parse_content_json, log, STAGE_CONTENT, budget, 3)
        if ok:
            lesson.update(data)
            lesson["title"] = data.get("title") or lesson.get("title", "")
            lesson["phase"] = pday.get("phase", lesson.get("phase", ""))
            lesson["topic"] = pday.get("title", lesson.get("topic", ""))
            lesson["level"] = level
            lesson["format_version"] = 4
            save_checkpoint(language, STAGE_CONTENT, data, day=day_num, status=STATUS_DONE)
            if save_each_day:
                course_db.save_course(language, course)
            log.event("stage.ok", msg=f"Content Ngày {day_num} OK", stage=STAGE_CONTENT, day=day_num)
        else:
            log.error("stage.fail", msg=f"Content Ngày {day_num} thất bại: {err}",
                      stage=STAGE_CONTENT, day=day_num)
            return None
    elif not lesson.get("vocab"):
        # Resume: lấy từ checkpoint
        cp = load_checkpoint(language, STAGE_CONTENT, day_num) or {}
        if cp.get("data"):
            lesson.update(cp["data"])

    if not lesson.get("vocab"):
        return None

    # ── DẪN CHỨNG (Wikipedia/Wiktionary) ──────────────────────────────────
    # Stage TÙY CHỌN (--evidence): KHÔNG tốn quota Gemini, nhưng Wikimedia
    # chặn IP sau ~30.000 request ⇒ giới hạn số từ/ngày + cache bền.
    if STAGE_EVIDENCE in stages:
        try:
            from ai.pipeline_evidence import run_evidence_stage
            run_evidence_stage(language, day_num, lesson, log_fn=emit)
        except Exception as e:
            log.warn("stage.fail", msg=f"Dẫn chứng Ngày {day_num}: {e}",
                     stage=STAGE_EVIDENCE, day=day_num)

    # ── QUIZ AB ──────────────────────────────────────────────────────────
    if STAGE_QUIZ_AB in stages and not stage_is_done(language, STAGE_QUIZ_AB, day_num):
        ok, data, err = _ask_with_retry(
            coord, build_quiz_prompt_ab(language, lesson), None,
            lambda t: parse_quiz_json(t, keys=("vocab_quiz", "pattern_quiz")),
            log, STAGE_QUIZ_AB, budget, 3)
        if ok:
            lesson["quiz"].update(data)
            save_checkpoint(language, STAGE_QUIZ_AB, data, day=day_num, status=STATUS_DONE)
        else:
            log.error("stage.fail", msg=f"Quiz AB Ngày {day_num}: {err}",
                      stage=STAGE_QUIZ_AB, day=day_num)

    # ── QUIZ CD ──────────────────────────────────────────────────────────
    if STAGE_QUIZ_CD in stages and not stage_is_done(language, STAGE_QUIZ_CD, day_num):
        ok, data, err = _ask_with_retry(
            coord, build_quiz_prompt_cd(language, lesson), None,
            lambda t: parse_quiz_json(t, keys=("common_quiz", "grammar_quiz")),
            log, STAGE_QUIZ_CD, budget, 3)
        if ok:
            lesson["quiz"].update(data)
            save_checkpoint(language, STAGE_QUIZ_CD, data, day=day_num, status=STATUS_DONE)
        else:
            log.error("stage.fail", msg=f"Quiz CD Ngày {day_num}: {err}",
                      stage=STAGE_QUIZ_CD, day=day_num)

    # ── MEDIA ────────────────────────────────────────────────────────────
    if STAGE_IMAGES in stages:
        run_images_stage(language, day_num, lesson, chain, log_fn=emit,
                         max_images=max_images, budget=budget,
                         dead_models=load_dead_models(language),
                         allow_degraded=allow_degraded)
    if STAGE_AUDIO in stages:
        run_audio_stage(language, day_num, lesson, chain, log_fn=emit,
                        max_items=max_audio, budget=budget,
                        allow_degraded=allow_degraded)
    if STAGE_DIALOGUE in stages:
        run_dialogue_stage(language, day_num, lesson, coord, log_fn=emit,
                           level=level, budget=budget,
                           allow_degraded=allow_degraded)
    if STAGE_MEDIA_VERIFY in stages:
        run_media_verify_stage(language, day_num, lesson, log_fn=emit,
                               allow_degraded=allow_degraded)

    # ── Commit ngày ──────────────────────────────────────────────────────
    normalize_lesson(lesson)
    # BUG ĐÃ SỬA (L-J): trước đây `days.sort()` chạy TRONG mỗi worker ⇒
    # list.sort() nhả GIL ⇒ worker khác `days.append()` cùng lúc ⇒ mất phần tử /
    # thứ tự hỏng. Giờ: KHÔNG sort từng ngày — chỉ sort 1 lần khi kết thúc lô.
    if save_each_day:
        # Tuần tự: ghi mỗi ngày (để dừng giữa chừng không mất dữ liệu).
        # Song song: ghi theo lô (mỗi 10 ngày) — course.json có thể tới 20 MB,
        # ghi mỗi ngày ⇒ hàng chục GB I/O cho 1 khóa học.
        course_db.save_course(language, course)
    log.event("day.ok", msg=f"Ngày {day_num} hoàn tất", day=day_num)
    return lesson


def _ask_with_retry(coord, prompt, schema, parser, log, stage, budget, attempts):
    """Gọi AI + parse, thử lại N lần. Trả (ok, data, error)."""
    if coord is None:
        return False, None, "không có coordinator"
    last_err = ""
    for attempt in range(1, max(1, attempts) + 1):
        if not budget.can_call(1):
            raise PipelinePause("Hết ngân sách call.", "budget")
        try:
            res = coord.request(prompt, response_schema=schema)
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            log.error("llm.error", msg=last_err, stage=stage, attempt=attempt)
            continue
        budget.consume_call()
        if not res.get("ok"):
            err = res.get("error", {})
            last_err = f"[{err.get('kind')}] {str(err.get('message',''))[:150]}"
            log.warn("llm.error", msg=last_err, stage=stage, attempt=attempt)
            if err.get("kind") == "no_key":
                raise PipelinePause("Hết key khả dụng.", "quota")
            if err.get("kind") == "quota_daily":
                raise PipelinePause("Hết quota ngày.", "quota")
            continue
        try:
            data = parser(res.get("text", ""))
            if data is None or (isinstance(data, (list, dict)) and not data):
                last_err = "parse rỗng"
                log.warn("json.invalid", msg="Parse rỗng", stage=stage, attempt=attempt)
                continue
            return True, data, ""
        except (ValueError, json.JSONDecodeError) as e:
            last_err = f"JSON hỏng: {e}"
            log.warn("json.truncated", msg=last_err, stage=stage, attempt=attempt)
            continue
    return False, None, last_err or "thất bại"


def _write_progress_pipeline(language, job, dod, run_id, level, total_days):
    """Ghi phần pipeline vào progress.json (tương thích ngược)."""
    try:
        p = course_db.get_progress(language)
        p["pipeline"] = {
            "schema": "vocabapp.progress.pipeline.v1",
            "status": "done" if dod.get("met") else "paused",
            "run_id": run_id,
            "level": level,
            "total_days": total_days,
            "definition_of_done": dod,
            "deferred_days": job.get("deferred_days", []),
            "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "resume_command": f"python -m ai.pipeline --lang {course_db.lang_slug(language)} --full",
        }
        course_db.save_progress(language, p)
    except Exception:
        pass


def _reset_pipeline(language):
    """Xoá checkpoint (giữ nguyên course.json)."""
    import shutil
    d = pipeline_dir(language)
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)


# ─── CLI ─────────────────────────────────────────────────────────────────────
def _parse_args(argv):
    ap = argparse.ArgumentParser(
        prog="python -m ai.pipeline",
        description="Render toàn bộ từ điển + media, tự trị.")
    ap.add_argument("--lang", help="Tên ngôn ngữ (Tiếng Nhật) hoặc slug (tiếng_nhật)")
    ap.add_argument("--all", action="store_true", help="Chạy cho MỌI ngôn ngữ có sẵn")
    ap.add_argument("--full", action="store_true", help="Toàn bộ 6 chặng + toàn bộ media")
    ap.add_argument("--mode", default="full", choices=("full", "media", "enrich"),
                    help="full=sinh lại tất cả | media=GIỮ content, chỉ thêm ảnh+audio+hội thoại "
                         "| enrich=media + regenerate content để có field v4")
    ap.add_argument("--level", help="Tên level (mặc định: Trọn Gói)")
    ap.add_argument("--days", type=int, help="Giới hạn số ngày mục tiêu")
    ap.add_argument("--stages", help="Chọn subset stage (csv)")
    ap.add_argument("--from-day", type=int, default=1)
    ap.add_argument("--to-day", type=int)
    ap.add_argument("--words-per-day", type=int, default=10)
    ap.add_argument("--no-resume", action="store_true", help="Xoá checkpoint, chạy lại từ đầu")
    ap.add_argument("--force-new", action="store_true", help="Xoá khóa cũ (có backup)")
    ap.add_argument("--no-media", action="store_true", help="Chỉ sinh text")
    ap.add_argument("--evidence", action="store_true",
                    help="Bật stage DẪN CHỨNG (Wikipedia/Wiktionary). "
                         "KHÔNG tốn quota Gemini nhưng Wikimedia chặn IP sau ~30k request.")
    ap.add_argument("--allow-degraded", action="store_true", help="DoD chấp nhận stage lỗi")
    ap.add_argument("--max-calls-per-day", type=int, default=MAX_CALLS_PER_DAY)
    ap.add_argument("--max-images-per-day", type=int, default=MAX_IMAGES_PER_DAY)
    ap.add_argument("--max-calls-per-language", type=int, default=MAX_CALLS_PER_LANGUAGE)
    ap.add_argument("--max-run-seconds", type=int, default=MAX_RUN_SECONDS)
    ap.add_argument("--workers", type=int, default=1,
                    help="Số ngày xử lý SONG SONG (1 = tuần tự). 4-6 là mức an toàn.")
    ap.add_argument("--wait-quota", action="store_true", help="Chờ quota hồi thay vì thoát")
    ap.add_argument("--status", action="store_true", help="In trạng thái rồi thoát")
    ap.add_argument("--dry-run", action="store_true", help="Chỉ in kế hoạch, 0 call")
    ap.add_argument("--json", action="store_true", help="In kết quả JSON")
    ap.add_argument("--quiet", action="store_true", help="Không in log ra stdout")
    return ap.parse_args(argv)


def _resolve_languages(args):
    """Trả list tên ngôn ngữ cần chạy."""
    if args.all:
        out = []
        for slug in list_pipeline_languages():
            c = course_db.get_course(slug, apply_v4=False, persist=False) or {}
            out.append(c.get("language") or slug)
        return out
    if not args.lang:
        return []
    c = course_db.get_course(args.lang, apply_v4=False, persist=False) or {}
    return [c.get("language") or args.lang]


def main(argv=None) -> int:
    args = _parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    langs = _resolve_languages(args)
    if not langs:
        print("❌ Cần --lang <tên> hoặc --all")
        return EXIT_CONFIG

    stages = None
    if args.stages:
        stages = [s.strip() for s in args.stages.split(",") if s.strip()]

    if args.status:
        jobs = load_jobs()
        for lg in langs:
            j = get_language_job(jobs, lg)
            dod = evaluate_dod(lg, allow_degraded=args.allow_degraded)
            print(f"\n=== {lg} ===")
            print(f"  status      : {j.get('status')}")
            print(f"  stage       : {j.get('current_stage')} / day {j.get('current_day')}")
            print(f"  counters    : {j.get('counters')}")
            print(f"  deferred    : {j.get('deferred_days')}")
            print(f"  DoD         : {dod['met']}  ({dod.get('days')} ngày)")
            for k, v in (dod.get("checks") or {}).items():
                print(f"      {'✅' if v else '❌'} {k}")
        return EXIT_OK

    if args.dry_run:
        for lg in langs:
            c = course_db.get_course(lg, apply_v4=False, persist=False) or {}
            plan = c.get("plan") or []
            days = len(plan)
            print(f"\n=== {lg} ===")
            print(f"  level       : {c.get('level')}")
            print(f"  ngày (plan) : {days}")
            print(f"  ước call   : ~{days * 3} (content + quiz AB + quiz CD)")
            print(f"  ước ảnh    : ~{days * 10} (10 ảnh/ngày)")
            print(f"  lệnh chạy  : python -m ai.pipeline --lang "
                  f"{course_db.lang_slug(lg)} --full")
        return EXIT_OK

    if not args.full and not stages:
        print("⚠ Không có --full hoặc --stages → chạy full mặc định.")

    if args.mode != "full" and not args.full:
        # media/enrich: vẫn cần các stage media + dialogue
        args.full = True

    results = []
    errors_all = []
    rc = EXIT_OK
    # Quét nhiều vòng: vòng 1 sinh media, vòng 2 sinh bù những ngày bị
    # đánh dấu PENDING ở media_verify (ngày chưa từng được xử lý).
    passes = 2 if args.all else 1
    for _pass in range(passes):
        for lg in langs:
            res = run_pipeline(
                lg,
                words_per_day=args.words_per_day,
                level=args.level,
                stages=stages,
                full=args.full,
                mode=args.mode,
                target_days=args.days,
                from_day=args.from_day,
                to_day=args.to_day,
                resume=not args.no_resume,
                force_new=args.force_new,
                media=not args.no_media,
                allow_degraded=args.allow_degraded,
                log_fn=(lambda m: None) if args.quiet else print,
                wait_quota=args.wait_quota,
                max_run_seconds=args.max_run_seconds,
                evidence=args.evidence,
                workers=args.workers,
            )
            results.append(res)
            if res["status"] != "done" and res["exit_code"] != EXIT_OK:
                rc = res["exit_code"]
            if not args.json:
                print(f"\n{'='*60}")
                print(f"  {lg}: {res['status'].upper()}  "
                      f"{res['days_done']}/{res['total_days']} ngày  "
                      f"calls={res['calls']}  ảnh={res['images']}  "
                      f"{res['elapsed_s']}s")
                print(f"  DoD: {res['definition_of_done']['met']}")
                print(f"  Log: {res['log_file']}")
                print(f"  Tiếp tục: {res['next_resume_command']}")
                print(f"{'='*60}")
            if res["status"] == "aborted":
                errors_all.append(f"{lg}: {', '.join(res.get('errors') or [])}")
                continue

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    if errors_all:
        print("\n⚠ CÓ LỖI:")
        for e in errors_all:
            print("  -", e)
    prune_logs()
    return rc


if __name__ == "__main__":
    sys.exit(main())
