"""
test_web_dashboard.py — Test Dashboard web (localhost) bằng Flask TEST CLIENT.

• KHÔNG mở cổng thật, KHÔNG chạy pipeline thật, KHÔNG gọi mạng:
  - `VocabBridge()._build_app()` chỉ dựng Flask app (không bind cổng);
  - `pc._run_pipeline` bị mock TỪ ĐẦU bằng fake chờ lệnh dừng.
• Kiểm tra:
  1. pipeline_control thuần: guard thiếu language; log buffer + since_id;
     status snapshot; start clear stop event cũ; run fake thoát khi dừng.
  2. GET /dashboard: serve HTML + nhúng token CHỈ khi ?token= hợp lệ.
  3. Auth: mọi API dash (status/logs/courses/start/stop) thiếu/sai token → 401.
  4. logs: since_id chỉ trả dòng MỚI; last_id tăng dần; courses trả list.
  5. Start/Stop lifecycle: start → running(source=web) → start lại → 409
     already_running → stop → STOP_EVENT set → fake thoát → running=false
     + last_result=aborted + log chứa ▶/⏹/🏁.

Chạy: python tools/test_web_dashboard.py
"""
import os
import sys
import threading
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASSED = []
FAILED = []
SKIPPED = []


def ck(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print("[OK] " + name)
    else:
        FAILED.append(name)
        print("[FAIL] " + name + ((" | " + str(extra)) if extra else ""))


def skip(name, why):
    SKIPPED.append(name)
    print("[SKIP] " + name + " | " + why)


def wait_for(fn, timeout=8.0, step=0.05):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if fn():
            return True
        time.sleep(step)
    return False


# ── pipeline_control thuần ──────────────────────────────────────────────────
import ai.pipeline_control as pc  # noqa: E402

# Mock pipeline TỪ ĐẦU: KHÔNG BAO GIỜ chạy run_pipeline thật trong test này.
_orig_run = pc._run_pipeline
_FAKE_RUNS = []


def _fake_run(language, opts):
    pc.log_append(f"FAKE run {language} (wpd={opts.get('words_per_day')})")
    _FAKE_RUNS.append(language)
    stopped = pc.STOP_EVENT.wait(10.0)      # chờ lệnh Dừng (hoặc timeout)
    return {"ok": not stopped,
            "status": "aborted" if stopped else "done",
            "days_done": 1, "total_days": 3, "calls": 5, "images": 2,
            "definition_of_done": {"met": False}}


pc._run_pipeline = _fake_run

print("=== 1. pipeline_control thuần ===")
pc.STOP_EVENT.clear()
pc.set_running(False)

ok, reason = pc.start_pipeline("")
ck("start thiếu language → (False, missing_language)",
   ok is False and reason == "missing_language", (ok, reason))

lid0 = pc.log_snapshot(0)["last_id"]
pc.log_append("dòng thử dashboard")
snap = pc.log_snapshot(lid0)
ck("log_snapshot(since) trả đúng dòng MỚI vừa append",
   len(snap["lines"]) == 1 and snap["lines"][0]["msg"] == "dòng thử dashboard"
   and snap["lines"][0]["id"] > lid0, snap)
ck("log line có id tăng dần + timestamp HH:MM:SS",
   len(snap["lines"][0]["t"]) == 8, snap["lines"][0])
ck("log_snapshot(since=last_id) → 0 dòng (không lặp lại)",
   len(pc.log_snapshot(snap["last_id"])["lines"]) == 0)

st = pc.status_snapshot()
ck("status_snapshot: running=False + có stop_requested",
   st["running"] is False and "stop_requested" in st, st)

# start luôn CLEAR stop event cũ (lệnh dừng run trước không đè run mới)
pc.STOP_EVENT.set()
ok, reason = pc.start_pipeline("tiếng_quan_test", level="L1", words_per_day=7,
                               target_days=3, source="web")
ck("start_pipeline hợp lệ → (True, started)",
   ok is True and reason == "started", (ok, reason))
ck("start CLEAR stop event cũ ngay (trước khi thread chạy)",
   not pc.STOP_EVENT.is_set())
ck("status sau start: running=true, source=web, language đúng",
   (lambda j: j["running"] and j["source"] == "web"
    and j["language"] == "tiếng_quan_test")(pc.status_snapshot()),
   pc.status_snapshot())
ck("fake run THẬT SỰ đã chạy (mock, 0 gọi mạng)",
   wait_for(lambda: "tiếng_quan_test" in _FAKE_RUNS, timeout=5.0)
   and any("FAKE run tiếng_quan_test" in x["msg"]
           for x in pc.log_snapshot(0)["lines"]), _FAKE_RUNS)

# start lần 2 khi đang chạy → guard đã_running (bên trong pc, không qua route)
ok2, reason2 = pc.start_pipeline("khac")
ck("start lần 2 khi đang chạy → (False, already_running:web)",
   ok2 is False and reason2 == "already_running:web", (ok2, reason2))

ck("request_stop → stopped=true + SET STOP_EVENT",
   pc.request_stop() is True and pc.STOP_EVENT.is_set())
ck("run fake thoát sau lệnh dừng → running=false",
   wait_for(lambda: not pc.is_running(), timeout=8.0))
ck("last_result từ run: status=aborted",
   (pc.status_snapshot().get("last_result") or {}).get("status") == "aborted",
   pc.status_snapshot())
ck("log có dòng ⏹ Dashboard + 🏁 Dashboard",
   any("yêu cầu DỪNG" in x["msg"] for x in pc.log_snapshot(0)["lines"])
   and any("🏁 Dashboard" in x["msg"]
           for x in pc.log_snapshot(0)["lines"]))
ck("stop khi idle → stopped=false",
   pc.request_stop() is False)
pc.STOP_EVENT.clear()

# ── Flask routes ────────────────────────────────────────────────────────────
try:
    from ai.bridge_server import VocabBridge
    b = VocabBridge()
    app = b._build_app()
    client = app.test_client()
    TOK = b.token
except Exception as e:
    skip("flask_routes", f"không dựng được Flask app: {e}")
    TOK = None

if TOK:
    print("\n=== 2. GET /dashboard ===")
    r = client.get(f"/dashboard?token={TOK}")
    body = r.get_data(as_text=True)
    ck("dashboard ?token= đúng → 200 + token được nhúng",
       r.status_code == 200 and TOK in body
       and "__TOKEN_PLACEHOLDER__" not in body, r.status_code)
    r2 = client.get("/dashboard")
    b2 = r2.get_data(as_text=True)
    ck("dashboard không token → 200 nhưng KHÔNG nhúng token (placeholder còn)",
       r2.status_code == 200 and "__TOKEN_PLACEHOLDER__" in b2,
       r2.status_code)
    r3 = client.get("/dashboard?token=sai-khac")
    ck("dashboard token sai → 200 UI nhưng KHÔNG nhúng token",
       r3.status_code == 200
       and "__TOKEN_PLACEHOLDER__" in r3.get_data(as_text=True))
    ck("dashboard.html có marker điều khiển (Start/Dừng/log/pill)",
       "btnStart" in body and "btnStop" in body and "logBox" in body
       and "pill" in body)

    print("\n=== 3. Auth 401 ===")
    ck("status thiếu token → 401",
       client.get("/api/vocab/dash/status").status_code == 401)
    ck("status token sai (header) → 401",
       client.get("/api/vocab/dash/status",
                  headers={"X-Vocab-Bridge": "sai"}).status_code == 401)
    ck("logs token sai → 401",
       client.get("/api/vocab/dash/logs?since=0",
                  headers={"X-Vocab-Bridge": "sai"}).status_code == 401)
    ck("courses thiếu token → 401",
       client.get("/api/vocab/dash/courses").status_code == 401)
    ck("start thiếu token → 401",
       client.post("/api/vocab/dash/start",
                   json={"language": "x"}).status_code == 401)
    ck("stop token sai → 401",
       client.post("/api/vocab/dash/stop",
                   headers={"X-Vocab-Bridge": "sai"}).status_code == 401)

    H = {"X-Vocab-Bridge": TOK}
    print("\n=== 4. status / logs / courses (token hợp lệ) ===")
    r = client.get("/api/vocab/dash/status", headers=H)
    j = r.get_json()
    ck("status 200: ok=True + có running/source/pct/stop_requested",
       r.status_code == 200 and j.get("ok") is True
       and all(k in j for k in ("running", "source", "pct", "stop_requested")),
       j)
    ck("status qua ?token= (browser) cũng 200",
       client.get(f"/api/vocab/dash/status?token={TOK}").status_code == 200)

    lid0 = pc.log_snapshot(0)["last_id"]
    pc.log_append("dòng qua route")
    r = client.get(f"/api/vocab/dash/logs?since={lid0}", headers=H)
    j = r.get_json()
    ck("logs 200: chứa dòng vừa append + last_id tăng",
       r.status_code == 200 and any(x["msg"] == "dòng qua route"
                                    for x in j.get("lines", []))
       and j.get("last_id", 0) > lid0, j)
    j2 = client.get(f"/api/vocab/dash/logs?since={j['last_id']}",
                    headers=H).get_json()
    ck("logs since=last_id → 0 dòng mới",
       len(j2.get("lines", [])) == 0, j2)

    r = client.get("/api/vocab/dash/courses", headers=H)
    j = r.get_json()
    ck("courses 200: có languages (list) + levels (list)",
       r.status_code == 200 and isinstance(j.get("languages"), list)
       and isinstance(j.get("levels"), list), j)

    print("\n=== 5. Start/Stop lifecycle qua route (run bị mock) ===")
    r = client.post("/api/vocab/dash/start", headers=H, json={})
    ck("start thiếu language → 400 missing_language",
       r.status_code == 400 and r.get_json().get("error") == "missing_language",
       (r.status_code, r.get_json()))

    pc.STOP_EVENT.set()   # stop cũ phải bị start clear
    r = client.post("/api/vocab/dash/start", headers=H, json={
        "language": "tiếng_route", "words_per_day": 7,
        "level": "1. Vỡ lòng", "target_days": 3})
    j = r.get_json()
    ck("start hợp lệ → 200 ok=true",
       r.status_code == 200 and j.get("ok") is True, (r.status_code, j))
    ck("start CLEAR stop event cũ (không dính lệnh dừng run trước)",
       not pc.STOP_EVENT.is_set())
    rr = client.post("/api/vocab/dash/start", headers=H,
                     json={"language": "khac"})
    ck("start lần 2 khi đang chạy → 409 already_running",
       rr.status_code == 409
       and "already_running" in rr.get_json().get("reason", ""),
       (rr.status_code, rr.get_json()))

    j = client.get("/api/vocab/dash/status", headers=H).get_json()
    ck("status khi chạy: running=true, source=web, language=tiếng_route",
       j.get("running") is True and j.get("source") == "web"
       and j.get("language") == "tiếng_route", j)
    ck("fake run qua route đã chạy (log FAKE tiếng_route)",
       wait_for(lambda: "tiếng_route" in _FAKE_RUNS, timeout=5.0)
       and any("FAKE run tiếng_route" in x["msg"]
               for x in pc.log_snapshot(0)["lines"]), _FAKE_RUNS)

    r = client.post("/api/vocab/dash/stop", headers=H)
    j = r.get_json()
    ck("stop → 200 + stopped=true (đang có run)",
       r.status_code == 200 and j.get("stopped") is True, j)
    ck("stop SET STOP_EVENT (dùng chung với GUI)",
       pc.STOP_EVENT.is_set())
    ck("run fake thoát sau lệnh dừng → running=false",
       wait_for(lambda: not pc.is_running(), timeout=8.0))
    ck("log có dòng ⏹ yêu cầu DỪNG qua route",
       any("yêu cầu DỪNG" in x["msg"]
           for x in pc.log_snapshot(0)["lines"]))

    j = client.get("/api/vocab/dash/status", headers=H).get_json()
    ck("status sau stop: last_result.status=aborted",
       (j.get("last_result") or {}).get("status") == "aborted", j)

    r = client.post("/api/vocab/dash/stop", headers=H)
    ck("stop khi idle → stopped=false",
       r.get_json().get("stopped") is False, r.get_json())

    print("\n=== 6. Trang học /index + static + data ===")
    r = client.get("/index")
    body = r.get_data(as_text=True)
    ck("/index → 200 là index.html thật (không trỏ nhầm static generic)",
       r.status_code == 200 and "<title>" in body and "script.js" in body
       and "Vocabulary" in body, r.status_code)
    r = client.get("/script.js")
    sj = r.get_data(as_text=True)
    ck("/script.js → 200 + có init()", r.status_code == 200
       and "async function init" in sj, r.status_code)
    ck("/script.js hết nhắc 'Đồng Bộ lên GitHub' (dữ liệu LOCAL, không cần GitHub)",
       "Đồng Bộ lên GitHub" not in sj, sj.find("GitHub"))
    ck("/script.js hướng dẫn mở 127.0.0.1:5690/index khi load lỗi + phân biệt file://",
       "127.0.0.1:5690/index" in sj and 'location.protocol === "file:"' in sj, None)
    ck("/script.js có listener đổi ngày khóa học (change → renderCourseDay)",
       'daySelect.addEventListener("change"' in sj, None)
    ck("/style.css → 200", client.get("/style.css").status_code == 200)
    ck("/paths.js → 200 + VOCAB_LANGS", client.get("/paths.js").status_code == 200
       and "VOCAB_LANGS" in client.get("/paths.js").get_data(as_text=True))
    ck("/manifest.json → 200", client.get("/manifest.json").status_code == 200)

    r = client.get("/data/index.json")
    j = r.get_json()
    langs = (j.get("languages") or []) if r.status_code == 200 else []
    ck("data/index.json → 200 + languages KHÔNG rỗng (file thật hoặc synth khóa AI)",
       r.status_code == 200 and isinstance(j.get("languages"), list)
       and len(langs) >= 1, j)
    # Môi trường thích ứng: file THẬT có (đã export) → nội dung do nó quyết
    # định; file THIẾU → route synth từ dir khóa AI. Tên dir KHÁC NHAU giữa
    # máy (worktree 'tiếng_nhật' vs Desktop 'nhật') → KHÔNG hardcode slug,
    # chỉ bắt buộc: mọi slug synth đều trỏ tới course.json THẬT trên đĩa.
    _idx_real = os.path.isfile(os.path.join(BASE, "data", "index.json"))
    if not _idx_real:
        _all_real = bool(langs) and all(
            os.path.isfile(os.path.join(BASE, "data", "ai_courses",
                                        s, "course.json"))
            for s in langs)
        ck("index.json THIẾU → synth từ khóa AI có course.json THẬT trên đĩa",
           _all_real, langs[:5])

    slug0 = langs[0] if langs else "tiếng_nhật"
    r = client.get(f"/data/ai_courses/{slug0}/course.json")
    cj = r.get_json() if r.status_code == 200 else None
    ck("course.json THẬT → 200 + có mảng days (tab Khóa học AI render)",
       r.status_code == 200 and isinstance((cj or {}).get("days"), list),
       r.status_code)

    _vocab_real = os.path.isfile(os.path.join(BASE, "data", f"{slug0}.json"))
    r = client.get(f"/data/{slug0}.json")
    if _vocab_real:
        ck("vocab <slug>.json THẬT đã export → 200 + có vocabularies",
           r.status_code == 200
           and isinstance(r.get_json().get("vocabularies"), list),
           r.status_code)
    else:
        ck("vocab <slug>.json chưa export → {vocabularies:[]} 200 (UI sạch)",
           r.status_code == 200 and r.get_json().get("vocabularies") == [],
           r.get_json())
    ck("data thiếu (có '/') → 404 JSON",
       client.get("/data/nonexistent_dir/xx.json").status_code == 404)
    rt = client.get("/data/../../settings.json")
    ck("path traversal /data/../../ → KHÔNG lộ file ngoài (4xx)",
       rt.status_code in (400, 404), rt.status_code)
    ck("media manifest thật → 200 (data/media/index.json)",
       client.get("/data/media/index.json").status_code == 200)

# ── kết thúc (restore nguyên trạng) ─────────────────────────────────────────
pc.STOP_EVENT.set()
wait_for(lambda: not pc.is_running(), timeout=15.0)   # chắc thread fake đã thoát
pc._run_pipeline = _orig_run
pc.STOP_EVENT.clear()
pc.set_running(False)

print(f"\nKết quả: {len(PASSED)} PASS / {len(FAILED)} FAIL"
      f" (tổng {len(PASSED) + len(FAILED)}, skip {len(SKIPPED)})")
sys.exit(1 if FAILED else 0)
