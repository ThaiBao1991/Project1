# -*- coding: utf-8 -*-
"""Test fix 429 "tốc độ" (QUOTA_RATE) — KHÔNG gọi mạng thật (mock requests.post).

Chạy:  python tools/test_quota_rate.py

Bao phủ (theo plan fix log "429 tốc độ → thử model" + xoay 197 key vô tận):
  1. request(): model A 429-tốc-độ → model B 200 ⇒ OK trên CÙNG key,
     log có "→ thử", KHÔNG có "Đổi sang account", key KHÔNG bị khóa oan.
  2. _try_models(): mọi model 429-tốc-độ ⇒ trả QUOTA_RATE (không rơi về
     return "hết model fallback" mập mờ như trước).
  3. request(): mọi model 429-tốc-độ ⇒ lock_key(retry_delay) THẬT + đổi
     key/account thật + cooldown SỐNG SÓT qua pool.sync(dict mới).
  4. request(): mọi model 429-quota-ngày ⇒ khóa account 60 phút + đổi key,
     không còn nhánh log "→ thử model kế" nói dối.
  5. _try_models(): 429 quota ngày ⇒ thử model tiếp trên cùng key (regression).
  6. pace(): burst không bao giờ nhanh hơn target quá 15% (uniform ≥ 0.85).
  7. classify_response(): phân biệt 429 daily vs 429 rate.
  8. lock_key() sống sót qua pool.sync() với dict loader mới (bug production).
"""
import os
import sys
import time as _real_time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests  # noqa: E402
import api.gemini_safe as gs  # noqa: E402

PASSED = []
FAILED = []


def ck(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print("[OK] " + name)
    else:
        FAILED.append(name)
        print("[FAIL] " + name + ((" | " + str(extra)) if extra else ""))


# ── Mock network ──────────────────────────────────────────────────────────────
_orig_post = requests.post
_handler = {"fn": None}


class _Resp:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body
        self.headers = {"content-type": "application/json"}

    def json(self):
        return self._body


def _fake_post(url, *a, **k):
    return _handler["fn"](url)


requests.post = _fake_post

RATE_BODY = {"error": {"message": "Resource has been exhausted (e.g. check quota).",
                       "status": "RESOURCE_EXHAUSTED"}}
DAILY_BODY = {"error": {"message": "Quota exceeded for metric: "
                                   "generativelanguage.googleapis.com/"
                                   "generate_content_free_tier_requests, "
                                   "limit: 20, model: m-slow "
                                   "Please retry in 13h33m50s.",
                        "status": "RESOURCE_EXHAUSTED"}}
OK_BODY = {"candidates": [{"content": {"parts": [{"text": "NOI DUNG OK"}]}}]}

# pace() thật sẽ sleep ~2.5-3s/lần → tắt trong các test request() cho nhanh.
_orig_pace = gs.pace
gs.pace = lambda *a, **k: None


def reset_pool():
    p = gs._get_pool()
    p._keys = []
    p._cooldown = {}
    p._key_cooldown = {}
    p._last_account = None
    p._acct_counters = {}
    return p


def make_coord(models, keys, logs):
    store = list(keys)

    def loader():
        # Giống production (_load_gemini_keys): trả dict MỚI mỗi lần gọi
        return [dict(k) for k in store]

    c = gs.GeminiCoordinator(models=models, log_fn=logs.append, key_loader=loader)
    c._adaptive = False          # bỏ exploration cho ổn định mặt trận test
    logs[:] = []                 # bỏ log phát sinh khi khởi tạo
    return c, loader


KEY1 = {"key": "AIzaTestKey0001", "email": "a@gmail.com", "status": "active"}
KEY2 = {"key": "AIzaTestKey0002", "email": "b@gmail.com", "status": "active"}


# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 1. 429 tốc độ ở model A → model B OK trên CÙNG key (request) ===")
reset_pool()
logs = []
coord, _ = make_coord(["m-slow", "m-fast"], [KEY1], logs)
urls = []


def _h1(url):
    urls.append(url)
    if "models/m-slow" in url:
        return _Resp(429, RATE_BODY)
    return _Resp(200, OK_BODY)


_handler["fn"] = _h1
res = coord.request("xin chao")
ck("request() trả ok=True", res.get("ok") is True, res)
ck("model chạy thành công là m-fast", res.get("model") == "m-fast", res.get("model"))
ck("text đúng", res.get("text") == "NOI DUNG OK", res.get("text"))
ck("cùng key (không đổi key)", res.get("key", {}).get("key") == "AIzaTestKey0001",
   res.get("key"))
ck("thử đúng 2 POST (m-slow fail → m-fast ok), cùng key1",
   len(urls) == 2 and all("AIzaTestKey0001" in u for u in urls), urls)
joined = "\n".join(logs)
ck("log có '429 tốc độ'", "429 tốc độ" in joined, logs)
ck("log có '→ thử m-fast' (đúng lời hứa)", "→ thử 'm-fast'" in joined, logs)
ck("KHÔNG có 'Đổi sang account' (hết xoay account oan)",
   "Đổi sang account" not in joined, logs)
ck("key KHÔNG bị khóa oan (cooldown rỗng)", not coord._pool._key_cooldown,
   coord._pool._key_cooldown)

print("\n=== 2. Mọi model 429 tốc độ ⇒ QUOTA_RATE (không rơi return mập mờ) ===")
reset_pool()
logs2 = []
coord2, _ = make_coord(["m-a", "m-b"], [KEY1], logs2)
urls2 = []


def _h2(url):
    urls2.append(url)
    return _Resp(429, RATE_BODY)


_handler["fn"] = _h2
r2 = coord2._try_models("hi", "AIzaTestKey0001", False, None, 0.1, 100, 10,
                        ordered_models=["m-a", "m-b"], email="a@gmail.com")
ck("_try_models trả kind=quota_rate", r2.get("kind") == gs.ErrorKind.QUOTA_RATE, r2)
ck("đã thử cả 2 model trên cùng key (2 POST)",
   len(urls2) == 2 and all("AIzaTestKey0001" in u for u in urls2), urls2)
ck("log 429 tốc độ có mũi tên '→ thử'", "→ thử" in "\n".join(logs2), logs2)

print("\n=== 3. Mọi model 429 tốc độ ⇒ lock_key THẬT + đổi key + cooldown sống ===")
reset_pool()
logs3 = []
coord3, loader3 = make_coord(["m-a", "m-b"], [KEY1, KEY2], logs3)


def _h3(url):
    if "AIzaTestKey0001" in url:
        return _Resp(429, RATE_BODY)
    return _Resp(200, OK_BODY)


_handler["fn"] = _h3
res3 = coord3.request("xin chao")
now = _real_time.time()
ck("request() vẫn trả ok=True (key2 cứu được)", res3.get("ok") is True, res3)
ck("key dùng cuối là key2", res3.get("key", {}).get("key") == "AIzaTestKey0002",
   res3.get("key"))
j3 = "\n".join(logs3)
ck("log cooldown key THẬT ('Cooldown riêng key')", "Cooldown riêng key" in j3, logs3)
ck("log đổi account THẬT ('Đổi sang account: b@')",
   "Đổi sang account: b@gmail.com" in j3, logs3)
ck("key1 bị khóa (lock_key) trong ~65s",
   coord3._pool._key_cooldown.get("AIzaTestKey0001", 0) > now + 30,
   coord3._pool._key_cooldown)
coord3._pool.sync(loader3())          # loader trả dict MỚI như production
k1 = next((k for k in coord3._pool._keys if k["key"] == "AIzaTestKey0001"), None)
ck("cooldown vẫn còn sau pool.sync(dict mới)", bool(k1) and k1.get("cooldown_until", 0) > now,
   k1)

print("\n=== 4. Mọi model 429 quota NGÀY ⇒ khóa account 60 phút + đổi key ===")
reset_pool()
logs4 = []
coord4, _ = make_coord(["m-a", "m-b"], [KEY1, KEY2], logs4)


def _h4(url):
    if "AIzaTestKey0001" in url:
        return _Resp(429, DAILY_BODY)
    return _Resp(200, OK_BODY)


_handler["fn"] = _h4
res4 = coord4.request("xin chao")
now4 = _real_time.time()
ck("request() vẫn ok=True (key2 cứu)", res4.get("ok") is True, res4)
j4 = "\n".join(logs4)
ck("log 'hết quota ngày (mọi model)'", "hết quota ngày (mọi model)" in j4, logs4)
# Log "→ thử 'm-b' [a@gmail.com]" là THẬT (đến từ _try_models, thử model kế
# ngay trên cùng key). Log NÓI DỊR cũ nằm ở request(): không tag account,
# kết thúc bằng "…" và KHÔNG bao giờ thử model kế thật — phải biến mất.
_daily_arrow = [l for l in logs4 if "quota ngày) → thử" in l]
ck("mọi log '→ thử' quota ngày đều có tag account (thật, cùng key)",
   all("[a@gmail.com]" in l for l in _daily_arrow), _daily_arrow)
ck("KHÔNG còn log nói dối cấp request() (kết thúc '…')",
   not any(l.rstrip().endswith("…") and "quota ngày" in l for l in logs4), logs4)
ck("account a@ bị khóa ~60 phút",
   coord4._pool.account_locked("a@gmail.com") and
   coord4._pool._cooldown.get("a@gmail.com", 0) - now4 > 3500,
   coord4._pool._cooldown)
ck("key2 được dùng", res4.get("key", {}).get("key") == "AIzaTestKey0002", res4.get("key"))

print("\n=== 5. Regression: 429 quota ngày ở model A → model B OK cùng key ===")
reset_pool()
logs5 = []
coord5, _ = make_coord(["m-a", "m-b"], [KEY1], logs5)


def _h5(url):
    if "models/m-a" in url:
        return _Resp(429, DAILY_BODY)
    return _Resp(200, OK_BODY)


_handler["fn"] = _h5
r5 = coord5._try_models("hi", "AIzaTestKey0001", False, None, 0.1, 100, 10,
                        ordered_models=["m-a", "m-b"], email="a@gmail.com")
ck("_try_models daily → model kế cứu được", r5.get("kind") == gs.ErrorKind.OK
   and r5.get("model") == "m-b", r5)
ck("log daily có '→ thử'", "→ thử 'm-b'" in "\n".join(logs5), logs5)

print("\n=== 6. pace(): burst không nhanh hơn target quá 15% ===")
gs.pace = _orig_pace          # test pace THẬT
calls = []
slept = []


class _Rand:
    def uniform(self, a, b):
        calls.append((a, b))
        return a                      # kịch bản xấu nhất: luôn lấy cận dưới


class _TimeProxy:
    def time(self):
        return _real_time.time()

    def sleep(self, s):
        slept.append(s)

    def __getattr__(self, n):
        return getattr(_real_time, n)


_orig_rand, _orig_time = gs.random, gs.time
_last_ts_orig = gs._last_call_ts
try:
    gs.random = _Rand()
    gs.time = _TimeProxy()
    gs._last_call_ts = _real_time.time()      # elapsed ≈ 0 ⇒ wait = base + jitter
    INTERVAL = 2.0
    for _ in range(5):
        gs.pace(interval=INTERVAL)
finally:
    gs.random, gs.time = _orig_rand, _orig_time
    gs._last_call_ts = _last_ts_orig

base_calls = [(a, b) for a, b in calls if b == 1.15]
ck("pace dùng uniform(0.85, 1.15) cho base", bool(base_calls) and
   all(c == (0.85, 1.15) for c in base_calls), calls)
ck("KHÔNG còn uniform(0.6, 1.0) (bị burst 1.67×)",
   (0.6, 1.0) not in calls and all(a >= 0.85 for a, b in calls if b != 1.5), calls)
ck("kịch bản xấu nhất: nghỉ ≥ 0.85 × interval (≤117% target)",
   bool(slept) and min(slept) >= 0.85 * INTERVAL - 1e-6, slept)
gs.pace = lambda *a, **k: None     # trả lại pace tắt cho các test còn lại

print("\n=== 7. classify_response(): 429 daily vs 429 rate ===")
k_daily, _ = gs.classify_response(429, DAILY_BODY)
k_rate, _ = gs.classify_response(429, RATE_BODY)
k_limit0, _ = gs.classify_response(
    429, {"error": {"message": "Quota exceeded for metric x, limit: 0"}})
k_perday, _ = gs.classify_response(
    429, {"error": {"message": "Quota exceeded per day for model"}})
ck("429 'Please retry in 13h' → QUOTA_DAILY", k_daily == gs.ErrorKind.QUOTA_DAILY, k_daily)
ck("429 'exhausted' → QUOTA_RATE", k_rate == gs.ErrorKind.QUOTA_RATE, k_rate)
ck("429 'limit: 0' → QUOTA_DAILY", k_limit0 == gs.ErrorKind.QUOTA_DAILY, k_limit0)
ck("429 'per day' → QUOTA_DAILY", k_perday == gs.ErrorKind.QUOTA_DAILY, k_perday)

print("\n=== 8. lock_key() sống sót qua pool.sync(dict loader mới) ===")
p8 = reset_pool()
fresh = lambda: [{"key": "k1", "email": "a@x", "status": "active"}]
p8.sync(fresh())
k8 = p8.pick()
ck("pick được key", bool(k8), k8)
p8.lock_key(k8, duration=60)
ck("sau lock: usable = 0", p8.usable_count() == 0, p8.usable_count())
p8.sync(fresh())                      # bug cũ: cooldown bị vứt mất → usable = 1
ck("sau sync lại: usable vẫn = 0 (cooldown giữ)", p8.usable_count() == 0,
   p8.usable_count())

# ── kết thúc ─────────────────────────────────────────────────────────────────
requests.post = _orig_post
gs.pace = _orig_pace
print("\nKết quả: %d PASS / %d FAIL (tổng %d)" %
      (len(PASSED), len(FAILED), len(PASSED) + len(FAILED)))
if FAILED:
    for f in FAILED:
        print("  ✗ " + f)
    sys.exit(1)
