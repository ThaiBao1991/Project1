"""
pipeline_store.py — Checkpoint, bảng job và backup rotation cho pipeline tự trị.

Cấu trúc checkpoint:
    data/ai_courses/_jobs.json                       ← bảng job + budget BỀN
    data/ai_courses/_jobs.lock
    data/ai_courses/<slug>/_pipeline/profile.json
    data/ai_courses/<slug>/_pipeline/backbone.json
    data/ai_courses/<slug>/_pipeline/plan.json
    data/ai_courses/<slug>/_pipeline/state.json
    data/ai_courses/<slug>/_pipeline/dead_models.json
    data/ai_courses/<slug>/_pipeline/days/d0001/<stage>.json
    data/ai_courses/<slug>/_pipeline/media/d0001/...
    data/logs/<slug>_<YYYYMMDD>_<HHMMSS>.log          ← JSONL

Nguyên tắc:
  • Sự thật = tập file checkpoint stage + course.json.  state.json chỉ là cache.
  • Mọi ghi file atomic (tmp + os.replace).
  • Budget đếm BỀN trong _jobs.json (không chỉ RAM như track_call()).
"""

import json

from ai.paths import lang_slug
import os
import shutil
import threading
import time
from datetime import datetime

# Khoá ghi file — nhiều ngày chạy song song có thể ghi cùng 1 checkpoint/manifest.
_WRITE_LOCK = threading.RLock()
# Khoá bộ đếm ngân sách — bump_counters() được gọi từ N thread cùng lúc.
# BUG ĐÃ SỬA (L-K): không có khoá ⇒ đếm thiếu ⇒ VƯỢT quota Gemini.
_COUNTER_LOCK = threading.RLock()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COURSES_DIR = os.path.join(BASE_DIR, "data", "ai_courses")
JOBS_PATH = os.path.join(COURSES_DIR, "_jobs.json")
JOBS_LOCK = os.path.join(COURSES_DIR, "_jobs.lock")
LOGS_DIR = os.path.join(BASE_DIR, "data", "logs")

JOBS_FORMAT_VERSION = 1
STAGE_SCHEMA = "vocabapp.pipeline.stage.v1"
STATE_SCHEMA = "vocabapp.pipeline.state.v1"
JOBS_SCHEMA = "vocabapp.jobs.v1"

# Số bản backup giữ lại cho course.json / progress.json
BACKUP_KEEP = 5

# ─── Stage ────────────────────────────────────────────────────────────────────
STAGE_PROFILE = "profile"
STAGE_BACKBONE = "backbone"
STAGE_PLAN = "plan"
STAGE_CONTENT = "content"
STAGE_QUIZ_AB = "quiz_ab"
STAGE_QUIZ_CD = "quiz_cd"
STAGE_IMAGES = "images"
STAGE_AUDIO = "audio"
STAGE_DIALOGUE = "dialogue"
STAGE_MEDIA_VERIFY = "media_verify"
# Stage DẪN CHỨNG — KHÔNG nằm trong STAGES mặc định: tra Wikimedia (IP bị
# chặn sau ~30.000 request) ⇒ phải bật tay bằng --evidence / --stages evidence.
STAGE_EVIDENCE = "evidence"

STAGES = (
    STAGE_PROFILE, STAGE_BACKBONE, STAGE_PLAN,
    STAGE_CONTENT, STAGE_QUIZ_AB, STAGE_QUIZ_CD,
    STAGE_IMAGES, STAGE_AUDIO, STAGE_DIALOGUE, STAGE_MEDIA_VERIFY,
)

# Stage chạy THÊM khi bật tay (evidence + grammar enrichment)
STAGES_OPTIONAL = (STAGE_EVIDENCE,)

# Trạng thái stage
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_DEGRADED = "degraded"
STATUS_SKIPPED = "skipped"
STATUS_FAILED = "failed"

# ─── Đường dẫn ────────────────────────────────────────────────────────────────


def pipeline_dir(language: str) -> str:
    return os.path.join(COURSES_DIR, lang_slug(language), "_pipeline")


def stage_path(language: str, stage: str) -> str:
    return os.path.join(pipeline_dir(language), f"{stage}.json")


def day_dir(language: str, day: int) -> str:
    return os.path.join(pipeline_dir(language), "days", f"d{int(day):04d}")


def day_stage_path(language: str, day: int, stage: str) -> str:
    return os.path.join(day_dir(language, day), f"{stage}.json")


def media_day_dir(language: str, day: int) -> str:
    return os.path.join(pipeline_dir(language), "media", f"d{int(day):04d}")


def dead_models_path(language: str) -> str:
    return os.path.join(pipeline_dir(language), "dead_models.json")


def state_path(language: str) -> str:
    return os.path.join(pipeline_dir(language), "state.json")


# ─── Ghi/đọc atomic ───────────────────────────────────────────────────────────
def atomic_write_json(path: str, data) -> None:
    with _WRITE_LOCK:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)


def read_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


# ─── Backup rotation ──────────────────────────────────────────────────────────
def rotate_backup(path: str, keep: int = BACKUP_KEEP) -> str:
    """Tạo bản backup .bak1 (mới nhất) .. .bakN (cũ nhất) của `path`."""
    if not os.path.exists(path):
        return ""
    for i in range(keep, 1, -1):
        src = f"{path}.bak{i-1}"
        dst = f"{path}.bak{i}"
        if os.path.exists(src):
            try:
                os.replace(src, dst)
            except OSError:
                pass
    try:
        shutil.copy2(path, f"{path}.bak1")
        return f"{path}.bak1"
    except OSError:
        return ""


def restore_backup(path: str, keep: int = BACKUP_KEEP):
    """Khôi phục từ .bak mới nhất còn đọc được. Trả path đã khôi phục hoặc None."""
    for i in range(1, keep + 1):
        bak = f"{path}.bak{i}"
        if not os.path.exists(bak):
            continue
        try:
            with open(bak, "r", encoding="utf-8") as f:
                json.load(f)
        except Exception:
            continue
        try:
            shutil.copy2(bak, path)
            return bak
        except OSError:
            continue
    return None


# ─── Checkpoint stage ─────────────────────────────────────────────────────────
def save_checkpoint(language: str, stage: str, data, *, day=None, status: str = STATUS_DONE,
                    attempts: int = 1, provider: str = "", model: str = "",
                    error=None, started_at: str = "", duration_ms: int = 0) -> str:
    """Ghi 1 checkpoint stage. Trả đường dẫn file."""
    path = (day_stage_path(language, day, stage) if day is not None
            else stage_path(language, stage))
    payload = {
        "schema": STAGE_SCHEMA,
        "stage": stage,
        "lang": language,
        "slug": lang_slug(language),
        "day": int(day) if day is not None else None,
        "status": status,
        "attempts": int(attempts),
        "provider": provider,
        "model": model,
        "started_at": started_at or _now(),
        "finished_at": _now(),
        "duration_ms": int(duration_ms or 0),
        "error": error,
        "data": data,
    }
    atomic_write_json(path, payload)
    return path


def load_checkpoint(language: str, stage: str, day=None):
    path = (day_stage_path(language, day, stage) if day is not None
            else stage_path(language, stage))
    return read_json(path, None)


def stage_is_done(language: str, stage: str, day=None, allow_degraded: bool = True) -> bool:
    """R1: stage xong ⟺ checkpoint tồn tại ∧ status ∈ {done} (hoặc degraded nếu cho phép)."""
    cp = load_checkpoint(language, stage, day)
    if not cp or not isinstance(cp, dict):
        return False
    st = cp.get("status")
    if st == STATUS_DONE:
        return True
    if allow_degraded and st in (STATUS_DEGRADED, STATUS_SKIPPED):
        return True
    return False


def clear_stale_running(language: str, max_age_seconds: int = 1800) -> int:
    """R2: checkpoint 'running' quá hạn ⇒ xoá để chạy lại. Trả số file bị xoá."""
    n = 0
    base = pipeline_dir(language)
    if not os.path.isdir(base):
        return 0
    now = time.time()
    for root, _dirs, files in os.walk(base):
        for f in files:
            if not f.endswith(".json"):
                continue
            p = os.path.join(root, f)
            cp = read_json(p, None)
            if not isinstance(cp, dict) or cp.get("status") != STATUS_RUNNING:
                continue
            try:
                age = now - os.path.getmtime(p)
            except OSError:
                continue
            if age > max_age_seconds:
                try:
                    os.remove(p)
                    n += 1
                except OSError:
                    pass
    return n


# ─── Model chết ──────────────────────────────────────────────────────────────
DEAD_MODEL_COOLDOWN_MINUTES = 30          # Khóa model 30 phút sau 3 lần lỗi
MAX_FAILURES_BEFORE_DEAD = 3              # Số lần lỗi trước khi khóa model


def load_dead_models(language: str) -> dict:
    """Trả dict {model_name: {"until": ts, "fail_count": n}} hoặc {}."""
    data = read_json(dead_models_path(language), {}) or {}
    now = time.time()
    # Tự động xóa model đã hết hạn cooldown
    cleaned = {}
    for model, info in data.items():
        if not isinstance(info, dict):
            # Format cũ: list ⇒ chuyển sang dict với fail_count=0, không khóa
            cleaned[model] = {"until": 0, "fail_count": 0}
            continue
        until = info.get("until", 0)
        if until <= now:
            continue  # Đã hết hạn cooldown ⇒ bỏ qua (cho phép thử lại)
        cleaned[model] = info
    if len(cleaned) != len(data):
        save_dead_models(language, cleaned)
    return cleaned


def save_dead_models(language: str, dead: dict) -> None:
    atomic_write_json(dead_models_path(language), dead)


def mark_dead_model(language: str, model: str, reason: str = "") -> dict:
    """Đánh dấu model lỗi. Sau MAX_FAILURES_BEFORE_DEAD lần ⇒ khóa DEAD_MODEL_COOLDOWN_MINUTES phút."""
    dead = load_dead_models(language)
    now = time.time()
    entry = dead.get(model, {"until": 0, "fail_count": 0})
    if not isinstance(entry, dict):
        entry = {"until": 0, "fail_count": 0}
    entry["fail_count"] = int(entry.get("fail_count", 0)) + 1
    entry["reason"] = reason[:200]
    entry["last_fail_at"] = _now()

    if entry["fail_count"] >= MAX_FAILURES_BEFORE_DEAD:
        entry["until"] = now + DEAD_MODEL_COOLDOWN_MINUTES * 60
        entry["status"] = "dead"
    else:
        entry["status"] = "warning"

    dead[model] = entry
    save_dead_models(language, dead)
    return dead


def is_dead_model(language: str, model: str) -> bool:
    """Kiểm tra model hiện đang bị khóa cooldown hay không."""
    dead = load_dead_models(language)
    entry = dead.get(model)
    if not entry:
        return False
    until = entry.get("until", 0)
    return until > time.time()


def reset_dead_model(language: str, model: str) -> dict:
    """Mở khóa model (dùng cho nút Reset trong GUI)."""
    dead = load_dead_models(language)
    if model in dead:
        dead[model] = {"until": 0, "fail_count": 0, "status": "active",
                       "reason": "reset by user", "reset_at": _now()}
        save_dead_models(language, dead)
    return dead


def get_available_models(language: str, all_models: list) -> list:
    """Lọc ra các model chưa bị khóa cooldown."""
    dead = load_dead_models(language)
    now = time.time()
    available = []
    for m in all_models:
        entry = dead.get(m)
        if not entry:
            available.append(m)
            continue
        until = entry.get("until", 0)
        if until <= now:
            available.append(m)
    return available


# ─── State (cache) ────────────────────────────────────────────────────────────
def load_state(language: str) -> dict:
    st = read_json(state_path(language), None)
    if not isinstance(st, dict):
        st = {}
    st.setdefault("schema", STATE_SCHEMA)
    st.setdefault("lang", language)
    st.setdefault("slug", lang_slug(language))
    st.setdefault("cursor", {})
    st.setdefault("counters", {})
    return st


def save_state(language: str, state: dict) -> None:
    state["updated_at"] = _now()
    atomic_write_json(state_path(language), state)


# ─── Bảng job + budget bền ───────────────────────────────────────────────────
def load_jobs() -> dict:
    jobs = read_json(JOBS_PATH, None)
    if not isinstance(jobs, dict):
        jobs = {}
    jobs.setdefault("schema", JOBS_SCHEMA)
    jobs.setdefault("runs", {})
    jobs.setdefault("languages", {})
    return jobs


def save_jobs(jobs: dict) -> None:
    jobs["updated_at"] = _now()
    atomic_write_json(JOBS_PATH, jobs)


def get_language_job(jobs: dict, language: str) -> dict:
    slug = lang_slug(language)
    job = jobs.setdefault("languages", {}).setdefault(slug, {})
    job.setdefault("language", language)
    job.setdefault("slug", slug)
    job.setdefault("status", "idle")
    job.setdefault("current_stage", None)
    job.setdefault("current_day", None)
    job.setdefault("stages", {})
    job.setdefault("days", {})
    job.setdefault("counters", {
        "calls_today": 0, "images_today": 0, "tts_today": 0,
        "calls_total": 0, "images_total": 0, "tts_total": 0,
        "calls_day_date": time.strftime("%Y-%m-%d"),
    })
    job.setdefault("definition_of_done", {"met": False, "checks": {}})
    job.setdefault("deferred_days", [])
    job.setdefault("last_error", None)
    return job


def bump_counters(job: dict, calls: int = 0, images: int = 0, tts: int = 0) -> None:
    """Tăng bộ đếm bền. Tự reset theo ngày cho bộ đếm 'today'.

    BUG ĐÃ SỬA (L-K): trước đây đọc–cộng–ghi KHÔNG có khoá ⇒ N thread
    cùng gọi sẽ mất số ⇒ đếm thiếu ⇒ VƯỢT quota Gemini ⇒ bị khoá account.
    """
    global _COUNTER_LOCK
    with _COUNTER_LOCK:
        c = job.setdefault("counters", {})
        today = time.strftime("%Y-%m-%d")
        if c.get("calls_day_date") != today:
            c["calls_day_date"] = today
            c["calls_today"] = 0
            c["images_today"] = 0
            c["tts_today"] = 0
        c["calls_today"] = int(c.get("calls_today", 0)) + calls
        c["images_today"] = int(c.get("images_today", 0)) + images
        c["tts_today"] = int(c.get("tts_today", 0)) + tts
        c["calls_total"] = int(c.get("calls_total", 0)) + calls
        c["images_total"] = int(c.get("images_total", 0)) + images
        c["tts_total"] = int(c.get("tts_total", 0)) + tts


def record_run(jobs: dict, run_id: str, info: dict) -> None:
    jobs.setdefault("runs", {})[run_id] = info


def list_pipeline_languages() -> list:
    """Danh sách ngôn ngữ đã có khóa học AI trên đĩa."""
    out = []
    if not os.path.isdir(COURSES_DIR):
        return out
    for name in sorted(os.listdir(COURSES_DIR)):
        if name.startswith("_"):
            continue
        if os.path.isfile(os.path.join(COURSES_DIR, name, "course.json")):
            out.append(name)
    return out
