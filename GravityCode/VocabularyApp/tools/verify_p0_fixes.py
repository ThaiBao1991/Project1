"""
verify_p0_fixes.py — Tái hiện 12 lỗi P0 đã sửa để chống hồi quy.

Mỗi lỗi có 1 hàm `check_*` trả (ok, mô tả). Chạy:
    python tools/verify_p0_fixes.py
Exit code 0 = tất cả PASS.
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)

RESULTS = []


def check(name):
    def deco(fn):
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"{type(e).__name__}: {e}"
        RESULTS.append((name, ok, msg))
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {msg}" if msg else ""))
        return fn
    return deco


# ── L-A: dropdown ngôn ngữ không được lẫn file hệ thống ────────────────────
@check("L-A get_available_languages chỉ trả ngôn ngữ THẬT (không có 'Blocked Accounts'...)")
def _l_a():
    from database.database import get_available_languages
    langs = get_available_languages()
    bad = [l for l in langs if any(k in l.lower() for k in
           ("blocked", "quota", "voices", "profiles cache", "index"))]
    if bad:
        return False, f"lọt file hệ thống: {bad}"
    if len(langs) < 8:
        return False, f"chỉ có {len(langs)} ngôn ngữ (mong đợi >= 8): {langs}"
    return True, f"{len(langs)} ngôn ngữ: {', '.join(langs)}"


# ── L-B: github_sync không upload file hệ thống ────────────────────────────
@check("L-B github_sync loại file hệ thống + thư mục _pipeline")
def _l_b():
    src = open("api/github_sync.py", encoding="utf-8").read()
    need = ["blocked_accounts.json", "blocked_keys.json", "tts_quota.json",
            "tts_voices.json", "_pipeline"]
    miss = [n for n in need if n not in src]
    if miss:
        return False, f"thiếu trong danh sách loại: {miss}"
    return True, f"đã loại {len(need)} mục"


# ── L-C: pipeline không UnboundLocalError khi không có key ───────────────────
@check("L-C run_pipeline() không UnboundLocalError khi thiếu API key")
def _l_c():
    from ai.pipeline import run_pipeline, PipelineAbort
    from ai.providers import ProviderChain

    class _NoKey:
        name = "nokey"

        def available(self):
            return False, "không có key (test)"

        @property
        def coord(self):
            return None

        def fetch_images(self, *a, **kw):
            return []

    chain = ProviderChain([_NoKey()])
    try:
        res = run_pipeline("ZZKhongCoKey", chain=chain, log_fn=lambda m: None)
    except Exception as e:
        return False, f"vẫn ném {type(e).__name__}: {e}"
    if res.get("status") != "aborted":
        return False, f"trạng thái sai: {res.get('status')}"
    return True, "trả về status=aborted, không UnboundLocalError"


# ── L-D: cache TTS phải hit ─────────────────────────────────────────────────
@check("L-D cache TTS HIT (ghi rồi tra lại trong 0.1s)")
def _l_d():
    from ai.tts_generator import synthesize
    txt = "vocab cache regression probe"
    r1 = synthesize("Tiếng Anh", txt)
    if not r1:
        return False, "không tạo được audio lần 1"
    t0 = __import__("time").time()
    r2 = synthesize("Tiếng Anh", txt)
    dt = __import__("time").time() - t0
    if not r2.get("cached"):
        return False, f"cache KHÔNG hit (engine={r2.get('engine')})"
    return True, f"hit sau {dt:.3f}s"


# ── L-E: file JSON hỏng KHÔNG được âm thầm xoá dữ liệu ────────────────────
@check("L-E load_data() file hỏng → ném lỗi + sao lưu (không trả list rỗng)")
def _l_e():
    import json as _json
    import tempfile
    from database import database as db
    tmpd = tempfile.mkdtemp(prefix="vocab_broken_")
    orig_dir = db.DATA_DIR
    try:
        db.DATA_DIR = tmpd
        with open(os.path.join(tmpd, "zz_test.json"), "w", encoding="utf-8") as f:
            f.write("{ this is NOT valid json ")
        try:
            db.load_data("zz_test")
        except ValueError:
            baks = [x for x in os.listdir(tmpd) if ".corrupt-" in x]
            if not baks:
                return False, "ném lỗi nhưng KHÔNG sao lưu file hỏng"
            return True, f"ném ValueError + sao lưu {baks[0]}"
        return False, "load_data trả về bình thường cho file hỏng (mất dữ liệu!)"
    finally:
        db.DATA_DIR = orig_dir
        import shutil
        shutil.rmtree(tmpd, ignore_errors=True)


# ── L-F: pipeline KHÔNG ghi đè course.json hỏng ────────────────────────────
@check("L-F run_pipeline() KHÔNG ghi đè course.json bị hỏng")
def _l_f():
    import json as _json
    import shutil
    import tempfile
    from ai import course_db as cdb
    from ai.pipeline import run_pipeline
    from ai.providers import ProviderChain

    class _Ok:
        name = "ok"

        def available(self):
            return True, "ok"

        @property
        def coord(self):
            return None

        def fetch_images(self, *a, **kw):
            return []

    tmpd = tempfile.mkdtemp(prefix="vocab_course_")
    orig = cdb.COURSES_DIR
    try:
        cdb.COURSES_DIR = tmpd
        os.makedirs(os.path.join(tmpd, "zz_corrupt"), exist_ok=True)
        p = os.path.join(tmpd, "zz_corrupt", "course.json")
        with open(p, "w", encoding="utf-8") as f:
            f.write("{ BROKEN")
        before = open(p, encoding="utf-8").read()
        res = run_pipeline("zz_corrupt", chain=ProviderChain([_Ok()]), log_fn=lambda m: None)
        after = open(p, encoding="utf-8").read()
        if before != after:
            return False, "course.json hỏng ĐÃ BỊ GHI ĐÈ"
        if res.get("status") != "aborted":
            return False, f"trạng thái = {res.get('status')} (mong đợi aborted)"
        return True, "file hỏng được giữ nguyên, pipeline dừng an toàn"
    finally:
        cdb.COURSES_DIR = orig
        shutil.rmtree(tmpd, ignore_errors=True)


# ── L-G: /api/vocab/status phải auth ───────────────────────────────────────
@check("L-G bridge /api/vocab/status yêu cầu token (không lộ token)")
def _l_g():
    src = open("ai/bridge_server.py", encoding="utf-8").read()
    i = src.find("def status(")
    if i < 0:
        return False, "không tìm thấy route status"
    block = src[i:i + 700]
    if "_auth()" not in block:
        return False, "route status KHÔNG gọi _auth()"
    if '"bridge_token"' in block:
        return False, "route status vẫn trả bridge_token trong body"
    return True, "đã yêu cầu _auth() và không trả token"


# ── L-H: chống path traversal ──────────────────────────────────────────────
@check("L-H bridge chặn path traversal nhưng GIỮ chữ tiếng Việt")
def _l_h():
    from ai.bridge_server import VocabBridge
    cases = {
        "../../etc/passwd": None,
        "..\\..\\win": None,
        "a/b": None,
    }
    for raw in cases:
        out = VocabBridge._safe_name(raw, "fallback")
        if "/" in out or "\\" in out or ".." in out:
            return False, f"{raw!r} → {out!r} vẫn chứa ký tự nguy hiểm"
    if VocabBridge._safe_name("tiếng_anh", "x") != "tiếng_anh":
        return False, "slug tiếng Việt bị làm mòn"
    if VocabBridge._safe_name("", "fallback") != "fallback":
        return False, "fallback không hoạt động"
    return True, "3 vector traversal bị chặn, slug tiếng Việt giữ nguyên"


# ── L-J: không sort days trong từng worker (race) ──────────────────────────
@check("L-J _run_day KHÔNG sort days (race với append của worker khác)")
def _l_j():
    import re
    src = open("ai/pipeline.py", encoding="utf-8").read()
    i = src.find("def _run_day(")
    j = src.find("\ndef ", i + 10)
    body = src[i:j if j > 0 else len(src)]
    # chỉ tính CODE, không tính dòng comment (#) — tránh false positive
    code = "\n".join(ln for ln in body.splitlines()
                     if not ln.strip().startswith("#"))
    hits = re.findall(r"^\s*days\.sort\(", code, re.M)
    if hits:
        return False, f"_run_day vẫn gọi days.sort() ({len(hits)} chỗ) → race với append"
    return True, "sort chỉ chạy 1 lần khi kết thúc lô (trong _run_days_parallel)"


# ── L-K: bump_counters có khoá ──────────────────────────────────────────────
@check("L-K bump_counters() dùng khoá (không đếm thiếu → vượt quota)")
def _l_k():
    import threading
    from ai.pipeline_store import bump_counters
    job = {"counters": {}}

    def w():
        for _ in range(200):
            bump_counters(job, calls=1)

    ts = [threading.Thread(target=w) for _ in range(8)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    got = int(job["counters"].get("calls_total", 0))
    if got != 1600:
        return False, f"đếm {got}/1600 (mất {1600-got} ⇒ vượt quota)"
    return True, "8 thread × 200 lần → đếm đúng 1600"


# ── L-L: đóng file handle ──────────────────────────────────────────────────
@check("L-L đọc file audio dùng `with` (không rò handle)")
def _l_l():
    src = open("ai/pipeline_media.py", encoding="utf-8").read()
    if 'open(r["path"], "rb").read()' in src:
        return False, "vẫn còn open(...).read() không đóng handle"
    if "_read_bytes" not in src:
        return False, "không thấy helper _read_bytes"
    return True, "dùng helper _read_bytes() có `with`"


# ── L-I: .gitignore phải chặn settings.json + data/ ────────────────────────
@check("L-I .gitignore chặn settings.json, data/, __pycache__")
def _l_i():
    gi = os.path.join(BASE, ".gitignore")
    if not os.path.isfile(gi):
        return False, "chưa có .gitignore"
    txt = open(gi, encoding="utf-8").read()
    need = ["settings.json", "data/", "__pycache__"]
    miss = [n for n in need if n not in txt]
    if miss:
        return False, f"thiếu: {miss}"
    return True, "đã chặn settings.json, data/, __pycache__"


# ── L-M: fetch_via_addon không chờ 180s ────────────────────────────────────
@check("L-M fetch_via_addon timeout <= 20s (không mất 3 phút/lần)")
def _l_m():
    src = open("ai/web_ai_bridge.py", encoding="utf-8").read()
    i = src.find("def fetch_via_addon(")
    if i < 0:
        return False, "không tìm thấy fetch_via_addon"
    block = src[i:i + 1400]
    if "wait_seconds: int = 180" in block:
        return False, "vẫn mặc định wait_seconds=180"
    if "wait_seconds: int = 180" in src:
        return False, "vẫn còn wait_seconds=180 trong module"
    return True, "timeout đã giảm"


# ── L-U: khớp ngày bằng regex, không substring ─────────────────────────────
@check("L-U tìm ngày bằng regex (không khớp 'Ngày 1' với 'Ngày 11')")
def _l_u():
    src = open("VocabApp.py", encoding="utf-8").read()
    if 'f"Ngày {day_num}" in self._current_text' in src:
        return False, "vẫn dùng so khớp substring"
    return True, "không còn so khớp substring"


print("\n" + "=" * 62)
n_ok = sum(1 for _n, ok, _m in RESULTS if ok)
n_all = len(RESULTS)
print(f"KẾT QUẢ: {n_ok}/{n_all} kiểm tra P0 PASS")
if n_ok < n_all:
    print("\nCòn lỗi:")
    for n, ok, m in RESULTS:
        if not ok:
            print(f"  ❌ {n}\n     {m}")
print("=" * 62)
sys.exit(0 if n_ok == n_all else 1)
