"""
pipeline_log.py — Structured logging dạng JSONL cho pipeline tự trị.

Định dạng: mỗi dòng = 1 JSON object (JSONL), flush ngay sau mỗi dòng
để `tail -f` xem real-time và để kill -9 không mất log.

Ví dụ:
{"ts":"2026-10-20T09:12:03.412","run_id":"...","level":"info","event":"llm.ok",
 "lang":"Tiếng Nhật","slug":"tiếng_nhật","stage":"content","day":12,"attempt":1,
 "msg":"Sinh nội dung ngày 12 thành công","ctx":{"model":"gemini-3.5-flash","latency_ms":38220}}
"""

import json
import os
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "data", "logs")

# Giữ 30 file log mới nhất cho mỗi slug
LOG_KEEP = 30

# Danh sách event chuẩn — dùng để tài liệu hoá & kiểm tra
EVENTS = (
    # vòng đời run
    "run.start", "run.end", "run.resume", "run.paused", "run.abort", "run.lock",
    # stage
    "stage.start", "stage.ok", "stage.retry", "stage.skip", "stage.degraded",
    "stage.fail", "stage.resume_skip",
    # ngày
    "day.start", "day.ok", "day.defer", "day.fail", "day.resume",
    # LLM
    "llm.request", "llm.ok", "llm.error", "llm.truncated",
    # model / key / quota
    "model.dead", "model.disabled", "model.restored",
    "key.exhausted", "key.invalid", "key.cooldown", "key.recover",
    "quota.daily_exhausted", "quota.rate_limited", "quota.wait",
    # media
    "image.ok", "image.fail", "image.skip", "audio.ok", "audio.fail", "audio.skip",
    "dialogue.ok", "dialogue.fail", "media.verify", "media.missing",
    # provider / hạ tầng
    "provider.switch", "provider.unavailable", "provider.recover",
    "network.down", "network.up", "disk.low", "disk.full",
    # tiền & trạng thái
    "budget.check", "budget.exhausted", "budget.pause",
    # checkpoint / backup
    "checkpoint.write", "checkpoint.read", "checkpoint.invalid",
    "backup.rotate", "backup.restore", "course.flush",
    # người dùng
    "user.stop", "signal.stop",
    # json
    "json.truncated", "json.split_retry", "json.salvaged", "json.invalid",
)

_LEVELS = {"debug": 10, "info": 20, "warn": 30, "error": 40, "fatal": 50}


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"


class PipelineLogger:
    """Ghi log JSONL. Dùng `with` hoặc gọi close() thủ công."""

    def __init__(self, path: str, run_id: str = "", level: str = "info", echo=None):
        self.path = path
        self.run_id = run_id
        self.min_level = _LEVELS.get(level, 20)
        self.echo = echo
        self._fh = None
        self._lang = ""
        self._slug = ""
        self._stage = None
        self._day = None
        self._attempt = 0

    # ── context ─────────────────────────────────────────────────────────────
    def context(self, lang: str = "", stage=None, day=None, attempt: int = 0):
        if lang:
            self._lang = lang
            self._slug = lang.strip().lower().replace(" ", "_")
        if stage is not None:
            self._stage = stage
        if day is not None:
            self._day = day
        self._attempt = attempt
        return self

    # ── mở/đóng ────────────────────────────────────────────────────────────
    def open(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._fh = open(self.path, "a", encoding="utf-8")
        return self

    def close(self):
        if self._fh:
            try:
                self._fh.flush()
                self._fh.close()
            except Exception:
                pass
            self._fh = None

    def __enter__(self):
        return self.open()

    def __exit__(self, *a):
        self.close()
        return False

    # ── ghi ─────────────────────────────────────────────────────────────────
    def _write(self, level: str, event: str, msg: str = "", ctx=None):
        if _LEVELS.get(level, 20) < self.min_level:
            return
        ctx = dict(ctx or {})
        # day/stage/attempt truyền trong ctx được NÂNG LÊN field cấp trên
        day = ctx.pop("day", None)
        stage = ctx.pop("stage", None)
        attempt = ctx.pop("attempt", None)
        rec = {
            "ts": _now_iso(),
            "run_id": self.run_id,
            "level": level,
            "event": event,
            "lang": self._lang or None,
            "slug": self._slug or None,
            "stage": stage if stage is not None else self._stage,
            "day": day if day is not None else self._day,
            "attempt": attempt if attempt is not None else self._attempt,
            "msg": msg,
            "ctx": ctx,
        }
        line = json.dumps(rec, ensure_ascii=False)
        if self._fh:
            try:
                self._fh.write(line + "\n")
                self._fh.flush()
            except Exception:
                pass
        if self.echo:
            try:
                self.echo(f"[{level.upper()}] {event}: {msg}")
            except Exception:
                pass

    def debug(self, event, msg="", **ctx): self._write("debug", event, msg, ctx)
    def info(self, event, msg="", **ctx):  self._write("info", event, msg, ctx)
    def warn(self, event, msg="", **ctx):  self._write("warn", event, msg, ctx)
    def error(self, event, msg="", **ctx): self._write("error", event, msg, ctx)
    def fatal(self, event, msg="", **ctx): self._write("fatal", event, msg, ctx)

    def event(self, name, msg="", **ctx):
        """Ghi event với mức info (hoặc tự chọn theo tiền tố tên)."""
        if name.startswith("error") or name.endswith(".fail") or name.endswith(".abort"):
            return self._write("error", name, msg, ctx)
        if name.startswith("warn") or name.endswith(".retry") or name.endswith(".degraded"):
            return self._write("warn", name, msg, ctx)
        return self._write("info", name, msg, ctx)


def log_path(language: str, run_id: str = "") -> str:
    slug = (language or "").strip().lower().replace(" ", "_")
    stamp = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(LOGS_DIR, f"{slug}_{stamp}.log")


def open_logger(language: str, run_id: str = "", level: str = "info", echo=None) -> PipelineLogger:
    return PipelineLogger(log_path(language, run_id), run_id=run_id, level=level, echo=echo).open()


def prune_logs(language: str = "", keep: int = LOG_KEEP) -> int:
    """Xoá log cũ. Nếu language rỗng ⇒ dọn tất cả."""
    if not os.path.isdir(LOGS_DIR):
        return 0
    n = 0
    if language:
        slug = language.strip().lower().replace(" ", "_")
        groups = [(LOGS_DIR, [f for f in os.listdir(LOGS_DIR) if f.startswith(slug + "_")])]
    else:
        groups = [(LOGS_DIR, os.listdir(LOGS_DIR))]
    for folder, files in groups:
        files = sorted(files)
        for f in files[:-keep] if len(files) > keep else []:
            try:
                os.remove(os.path.join(folder, f))
                n += 1
            except OSError:
                pass
    return n
