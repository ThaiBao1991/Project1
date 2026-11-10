"""
bridge_server.py — Cầu nối HTTP giữa app desktop và Chrome addon.

Addon chạy trong trình duyệt (không thể gọi trực tiếp hàm Python) ⇒ cần
1 HTTP server nội bộ trên 127.0.0.1 để trao đổi job.

API:
  GET  /api/vocab/health          → ping (addon kiểm tra bridge còn sống)
  GET  /api/vocab/next            → lấy job tiếp theo (prompt cần gửi lên web AI)
  POST /api/vocab/result          → addon trả về {html, images[], ...}
  GET  /api/vocab/status          → trạng thái + đếm
  POST /api/vocab/cancel          → huỷ job đang chạy

Bảo mật:
  • Bind 127.0.0.1 CỐ ĐỊNH (KHÔNG đổi sang LAN IP như AskCpl — tránh mở cổng cho mạng)
  • Header `X-Vocab-Bridge` = token sinh mỗi lần app khởi động
  • Không dùng `app.run()` (reloader sinh process con) → `werkzeug.serving.make_server`
"""

import os
import queue
import re
import secrets
import sys
import threading
import time
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5690
TOKEN_HEADER = "X-Vocab-Bridge"

MAX_CONTENT_LENGTH = 64 * 1024 * 1024      # ảnh base64 làm payload phình ~33%


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


class VocabBridge:
    """Bridge server cho addon. Dùng `with` hoặc gọi start()/stop()."""

    def __init__(self, out_root: str = None, port: int = PORT):
        self.port = port
        self.token = secrets.token_hex(16)
        self.out_root = out_root or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "ai_courses")
        self.jobs = queue.Queue()
        self.state = {
            "state": "idle", "current": None, "queue_depth": 0,
            "requested": 0, "ok": 0, "failed": 0, "images": 0,
            "last_error": None, "last_result_at": None,
        }
        self._server = None
        self._thread = None
        self._lock = threading.Lock()
        self._app = None

    # ── Flask app ───────────────────────────────────────────────────────
    def _build_app(self):
        from flask import Flask, request, jsonify
        # Đảm bảo import được package `ai`, `database` cả khi chạy CLI
        # (python ai/bridge_server.py → sys.path[0] chỉ có thư mục ai/).
        _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _base not in sys.path:
            sys.path.insert(0, _base)
        app = Flask("vocab_bridge")
        app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
        bridge = self

        def _auth():
            return request.headers.get(TOKEN_HEADER) == bridge.token

        @app.get("/api/vocab/health")
        def health():
            # KHÔNG trả token ở health (cũng không auth) — chỉ trả trạng thái
            return jsonify({"ok": True, "state": bridge.state["state"],
                            "port": bridge.port})

        @app.get("/api/vocab/next")
        def next_job():
            if not _auth():
                return jsonify({"ok": False, "error": "bad_token"}), 401
            try:
                job = bridge.jobs.get_nowait()
            except queue.Empty:
                return jsonify({"ok": False, "reason": "no_pending_job",
                                "state": bridge.state["state"]}), 404
            with bridge._lock:
                bridge.state["state"] = "running"
                bridge.state["current"] = {k: job.get(k) for k in
                                          ("job_id", "platform", "course", "day")}
                bridge.state["requested"] += 1
                bridge.state["queue_depth"] = bridge.jobs.qsize()
            job = dict(job)
            job["bridge_token"] = bridge.token
            job["bridge_port"] = bridge.port
            return jsonify({"ok": True, **job})

        @app.post("/api/vocab/result")
        def post_result():
            if not _auth():
                return jsonify({"ok": False, "error": "bad_token"}), 401
            data = request.get_json(force=True, silent=True) or {}
            job_id = data.get("job_id")
            with bridge._lock:
                cur = bridge.state.get("current") or {}
                if job_id and cur.get("job_id") and job_id != cur.get("job_id"):
                    return jsonify({"ok": False, "error": "job_id_mismatch"}), 409
                bridge.state["last_result_at"] = _now()
                bridge.state["queue_depth"] = bridge.jobs.qsize()
                bridge.state["current"] = None
                bridge.state["state"] = "running" if bridge.jobs.qsize() else "idle"
            try:
                saved = bridge.persist(data)
            except Exception as e:
                with bridge._lock:
                    bridge.state["failed"] += 1
                    bridge.state["last_error"] = str(e)[:300]
                return jsonify({"ok": False, "error": "persist_failed",
                                "detail": str(e)[:200]}), 200
            with bridge._lock:
                bridge.state["ok"] += 1
                bridge.state["images"] += len(data.get("images") or [])
            return jsonify({"ok": True, "saved": saved,
                            "state": bridge.state["state"]})

        @app.get("/api/vocab/status")
        def status():
            # BUG ĐÃ SỬA (L-G): endpoint này KHÔNG auth nhưng lại trả bridge_token
            # ⇒ mọi tiến trình local đều lấy được token ⇒ gọi được /result.
            # Giờ: yêu cầu header token, và KHÔNG trả token trong body.
            if not _auth():
                return jsonify({"ok": False, "error": "bad_token"}), 401
            st = {k: v for k, v in bridge.state.items()}
            st["ok"] = True
            st["bridge_port"] = bridge.port
            st["has_token"] = True
            return jsonify(st)

        @app.post("/api/vocab/cancel")
        def cancel():
            if not _auth():
                return jsonify({"ok": False, "error": "bad_token"}), 401
            with bridge._lock:
                bridge.state["current"] = None
                bridge.state["state"] = "idle"
            return jsonify({"ok": True})

        # ── Dashboard web (localhost) — xem UPGRADE_17 §7.16 ────────────
        # Trang điều khiển: start/dừng pipeline + log realtime + tiến độ.
        # Vẫn bind 127.0.0.1 (không LAN); mọi API điều khiển BẮT BUỘC token
        # (header X-Vocab-Bridge hoặc ?token= cho browser) chống CSRF.
        _dash_html_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "web", "dashboard.html")

        def _auth_dash():
            tok = request.headers.get(TOKEN_HEADER) or request.args.get("token") or ""
            return bool(tok) and tok == bridge.token

        def _need_dash_auth():
            if _auth_dash():
                return None
            return jsonify({"ok": False, "error": "bad_token"}), 401

        def _pctl():
            # Import pipeline_control: chạy trong app (cwd=VocabApp) hay CLI
            # (python ai/bridge_server.py → sys.path[0]=ai/) đều được.
            try:
                from ai import pipeline_control
            except ImportError:
                import pipeline_control
            return pipeline_control

        @app.get("/dashboard")
        def dashboard_page():
            try:
                with open(_dash_html_path, "r", encoding="utf-8") as f:
                    html = f.read()
            except OSError:
                return (jsonify({"ok": False, "error": "dashboard_missing",
                                 "path": _dash_html_path}), 404)
            # Nhúng token CHỈ khi request mang token hợp lệ (?token=…);
            # token sai/rỗng → KHÔNG đụng placeholder → JS coi là chưa auth.
            if request.args.get("token") == bridge.token:
                html = html.replace("__TOKEN_PLACEHOLDER__", bridge.token)
            return html, 200, {"Content-Type": "text/html; charset=utf-8"}

        @app.get("/api/vocab/dash/status")
        def dash_status():
            err = _need_dash_auth()
            if err:
                return err
            pc = _pctl()
            return jsonify({"ok": True, "port": bridge.port,
                            **pc.status_snapshot()})

        @app.get("/api/vocab/dash/logs")
        def dash_logs():
            err = _need_dash_auth()
            if err:
                return err
            pc = _pctl()
            try:
                since = max(0, int(request.args.get("since", 0)))
            except Exception:
                since = 0
            return jsonify({"ok": True, **pc.log_snapshot(since)})

        @app.get("/api/vocab/dash/courses")
        def dash_courses():
            err = _need_dash_auth()
            if err:
                return err
            try:
                from database.database import get_available_languages
                langs = get_available_languages() or []
            except Exception:
                langs = []
            try:
                from ai.course_generator import LEVELS, DEFAULT_LEVEL
                levels, default_level = list(LEVELS), DEFAULT_LEVEL
            except Exception:
                levels, default_level = [], ""
            return jsonify({"ok": True, "languages": langs,
                            "levels": levels, "default_level": default_level})

        @app.post("/api/vocab/dash/start")
        def dash_start():
            err = _need_dash_auth()
            if err:
                return err
            pc = _pctl()
            data = request.get_json(silent=True) or {}

            def _pos_int(v):
                try:
                    iv = int(v)
                    return iv if iv > 0 else None
                except Exception:
                    return None

            ok, reason = pc.start_pipeline(
                data.get("language"),
                words_per_day=_pos_int(data.get("words_per_day")) or 10,
                level=(data.get("level") or None),
                target_days=_pos_int(data.get("target_days")),
                force_new=bool(data.get("force_new")),
                source="web",
            )
            if not ok:
                # missing_language = lỗi input (400); đã đang chạy = xung đột (409)
                code = 400 if reason == "missing_language" else 409
                return jsonify({"ok": False, "reason": reason,
                                "error": reason}), code
            return jsonify({"ok": True, "reason": reason})

        @app.post("/api/vocab/dash/stop")
        def dash_stop():
            err = _need_dash_auth()
            if err:
                return err
            pc = _pctl()
            return jsonify({"ok": True, "stopped": pc.request_stop()})

        # ── Trang học từ vựng web/index.html + static + data (§7.17) ────
        # index.html fetch relative: "data/index.json", "data/<slug>.json",
        # "data/ai_courses/<slug>/course.json", "data/media/index.json" + ảnh/
        # audio qua "data/media|audio/<slug>/…" + assets (script.js, style.css…).
        # KHÔNG auth: chỉ đọc file tĩnh/data (giao diện học), bind 127.0.0.1.
        from flask import send_from_directory
        from werkzeug.security import safe_join as _safe_join
        _web_dir = os.path.join(_base, "web")
        _data_dir = os.path.join(_base, "data")

        @app.get("/index")
        def web_index():
            return send_from_directory(_web_dir, "index.html")

        @app.get("/<path:fn>")
        def web_static(fn):
            # File trong web/ (script.js, style.css, paths.js, manifest.json,
            # icons/…). send_from_directory tự chặn path traversal.
            # Route CHẶT (/dashboard, /api/…) sort trước → không bị đè.
            return send_from_directory(_web_dir, fn)

        @app.get("/data/<path:fn>")
        def web_data(fn):
            real = _safe_join(_data_dir, fn)
            if real and os.path.isfile(real):
                return send_from_directory(_data_dir, fn)
            # Fallback: data/index.json CHƯA CÓ (chưa export) → synth danh sách
            # khóa AI CÓ THẬT trên đĩa → tab "Khóa học AI" hiển thị ngay.
            if fn == "index.json":
                langs = []
                ac = os.path.join(_data_dir, "ai_courses")
                if os.path.isdir(ac):
                    for name in sorted(os.listdir(ac)):
                        if os.path.isfile(os.path.join(ac, name, "course.json")):
                            langs.append(name)
                return jsonify({"languages": langs})
            # File vocab <slug>.json chưa export → list rỗng để UI hiển thị
            # sạch ("Không tìm thấy…") thay vì lỗi đỏ "Error loading".
            if fn.endswith(".json") and "/" not in fn:
                return jsonify({"vocabularies": []})
            return jsonify({"ok": False, "error": "not_found"}), 404

        return app

    # ── Lưu kết quả ────────────────────────────────────────────────────
    @staticmethod
    def _safe_name(value: str, fallback: str = "") -> str:
        """BUG ĐÃ SỬA (L-H): chống PATH TRAVERSAL nhưng GIỮ NGUYÊN chữ tiếng Việt.

        `course` và `filename` từ request HTTP trước đây đưa thẳng vào
        os.path.join ⇒ addon (hoặc bất kỳ tiến trình local nào biết token) có
        thể ghi file ra NGOÀI thư mục đích (ví dụ "../../evil").

        Giờ: chặn dấu phân cách đường dẫn + ".." + ký tự điều khiển,
        nhưng GIỮ nguyên chữ cái tiếng Việt (slug "tiếng_anh" phải còn nguyên).
        """
        s = str(value or "").strip()
        s = s.replace("\\", "_").replace("/", "_")
        s = re.sub(r"[\x00-\x1f\x7f]", "", s)
        while ".." in s:
            s = s.replace("..", "_")
        s = s.strip(". ")
        s = s[:80]
        return s or fallback

    def persist(self, data: dict) -> dict:
        """Ghi HTML + ảnh nhận từ addon xuống đĩa. Trả dict mô tả file đã lưu."""
        import base64
        import json
        course = self._safe_name(data.get("course") or "", "unknown")
        day = self._safe_name(data.get("day") or "", "0")
        day = re.sub(r"\D", "", day) or "0"
        out_dir = os.path.join(self.out_root, course, "_web")
        os.makedirs(out_dir, exist_ok=True)
        written = []

        html = data.get("html") or ""
        if html:
            hp = os.path.join(out_dir, f"day_{int(day):03d}.html")
            tmp = hp + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(html)
            os.replace(tmp, hp)
            written.append(hp)

        md = data.get("markdown")
        if md:
            mp = os.path.join(out_dir, f"day_{int(day):03d}.md")
            tmp = mp + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(md)
            os.replace(tmp, mp)
            written.append(mp)

        img_dir = os.path.join(out_dir, "images")
        for im in (data.get("images") or []):
            b64 = im.get("b64")
            url = im.get("url") or ""
            if not b64 and url:
                b64 = _download_b64(url)
            if not b64:
                continue
            name = self._safe_name(
                im.get("filename") or "",
                f"day_{int(day):03d}_img_{im.get('index', 0):02d}.jpg")
            if not name.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
                name += ".jpg"
            try:
                raw = base64.b64decode(b64)
            except Exception:
                continue
            os.makedirs(img_dir, exist_ok=True)
            fp = os.path.join(img_dir, name)
            with open(fp, "wb") as f:
                f.write(raw)
            written.append(fp)

        meta = {
            "job_id": data.get("job_id"),
            "platform": data.get("platform"),
            "course": course,
            "day": day,
            "elapsed_ms": data.get("elapsed_ms"),
            "received_at": _now(),
            "files": [os.path.relpath(p, self.out_root).replace(os.sep, "/")
                       for p in written],
        }
        mp = os.path.join(out_dir, f"day_{int(day):03d}.json")
        tmp = mp + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        os.replace(tmp, mp)
        written.append(mp)
        return {"files": meta["files"], "count": len(written)}

    # ── Hàng đợi ────────────────────────────────────────────────────────
    def push_job(self, job: dict) -> str:
        job = dict(job)
        job.setdefault("job_id", secrets.token_hex(12))
        job.setdefault("created_at", _now())
        self.jobs.put(job)
        with self._lock:
            self.state["queue_depth"] = self.jobs.qsize()
            self.state["state"] = "running"
        return job["job_id"]

    def pop_job(self):
        try:
            return self.jobs.get_nowait()
        except queue.Empty:
            return None

    # ── Vòng đời ────────────────────────────────────────────────────────
    def start(self):
        if self._thread:
            return self
        from werkzeug.serving import make_server
        self._app = self._build_app()
        self._server = make_server(HOST, self.port, self._app, threaded=True)
        self._thread = threading.Thread(target=self._server.serve_forever,
                                        name="vocab-bridge", daemon=True)
        self._thread.start()
        return self

    def stop(self):
        if self._server:
            try:
                self._server.shutdown()
                self._server.server_close()
            except Exception:
                pass
        self._server = None
        self._thread = None

    def __enter__(self):
        return self.start()

    def __exit__(self, *a):
        self.stop()
        return False


def _download_b64(url: str, timeout: int = 40):
    """Tải ảnh từ URL (fallback khi addon không gửi base64). Có Referer chống hotlink."""
    try:
        import requests
        r = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://gemini.google.com/",
        })
        ctype = (r.headers.get("content-type") or "").split(";")[0].lower()
        if r.status_code != 200 or not ctype.startswith("image/"):
            return ""
        if ctype == "image/svg+xml":
            return ""
        import base64
        return base64.b64encode(r.content).decode("ascii")
    except Exception:
        return ""


# ── CLI kiểm tra nhanh ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    b = VocabBridge().start()
    print(f"Bridge đang chạy: http://{HOST}:{b.port}")
    print(f"Token: {b.token}")
    print(f"Header: {TOKEN_HEADER}: {b.token}")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        b.stop()
