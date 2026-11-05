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
  9. P1 backoff RPM: compute_rpm_cooldown 65→120→300s + record/clear/reset.
 10. P1 tích hợp: 429 liên tiếp ⇒ khoá key 65 → 120 → 300s (request()).
 11. P2 gap cứng ≥8s giữa 2 call cùng account (pace(account=...)).
 12. P5 phản hồi rỗng: thử model kế + demote + dừng ở 3 account (safety filter).
 13. P6a+bug X ảnh: 429 model ảnh → model ảnh khác CÙNG key; URL gọi ĐÚNG
     model ảnh (không còn rơi về model text); mọi model 429 → QUOTA_RATE;
     request_image lock_key + đổi key thật.
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
    p._rpm_429 = {}
    p._last_account = None
    p._acct_counters = {}
    gs._account_last_used = {}
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

# ════════════════════════════════════════════════════════════════════════════
print("\n=== 9. P1: backoff RPM lũy tiến 65 → 120 → 300s ===")
d1 = gs.compute_rpm_cooldown("Resource has been exhausted", 1)
d2 = gs.compute_rpm_cooldown("Resource has been exhausted", 2)
d3 = gs.compute_rpm_cooldown("Resource has been exhausted", 3)
d9 = gs.compute_rpm_cooldown("Resource has been exhausted", 9)
ck("lần 1 → 65s", d1 == 65, d1)
ck("lần 2 → 120s", d2 == 120, d2)
ck("lần ≥3 → 300s (capped)", d3 == 300 and d9 == 300, (d3, d9))
ck("retryDelay thật của Google (>65) vẫn được tôn trọng",
   gs.compute_rpm_cooldown("retryDelay: 150s", 1) >= 150)
p9 = reset_pool()
ck("record lần lượt 1→2→3",
   (p9.record_rpm_429("x@y"), p9.record_rpm_429("x@y"), p9.record_rpm_429("x@y"))
   == (1, 2, 3))
p9.clear_rpm_429("x@y")
ck("clear khi thành công ⇒ đếm lại từ 1", p9.record_rpm_429("x@y") == 1)
p9._rpm_429["old@y"] = (5, _real_time.time() - 700)   # 429 cũ >10 phút
ck("chuỗi cách >10 phút ⇒ không còn 'liên tiếp' (reset về 1)",
   p9.record_rpm_429("old@y") == 1)

print("\n=== 10. P1: 429 liên tiếp ⇒ khoá key 65 → 120 → 300s (request) ===")
reset_pool()
logs10 = []
coord10, loader10 = make_coord(["m-a"], [KEY1, KEY2], logs10)
_handler["fn"] = lambda url: (_Resp(429, RATE_BODY)
                              if "AIzaTestKey0001" in url else _Resp(200, OK_BODY))


def _unlock_key1():
    coord10._pool._key_cooldown.pop("AIzaTestKey0001", None)
    for k in coord10._pool._keys:
        if k.get("key") == "AIzaTestKey0001":
            k.pop("cooldown_until", None)


def _round():
    _unlock_key1()                      # mở key1 để ép 429 lại (counter tăng)
    t0 = _real_time.time()
    r = coord10.request("xin chao")
    until = coord10._pool._key_cooldown.get("AIzaTestKey0001", 0)
    return r, until - t0


r10a, d10a = _round()                   # 429 lần 1 → 65s
ck("round 1: key1 khoá ~65s", 58 <= d10a <= 72, d10a)
r10b, d10b = _round()                   # lần 2 → 120s
ck("round 2: key1 khoá ~120s (backoff)", 112 <= d10b <= 132, d10b)
r10c, d10c = _round()                   # lần 3 → 300s
ck("round 3: key1 khoá ~300s (capped)", 288 <= d10c <= 315, d10c)
ck("cả 3 round vẫn ok nhờ key2 (không treo)",
   all(r.get("ok") for r in (r10a, r10b, r10c)),
   (r10a.get("ok"), r10b.get("ok"), r10c.get("ok")))
ck("counter a@ = 3 sau 3 lần 429",
   coord10._pool._rpm_429.get("a@gmail.com", (0,))[0] == 3,
   coord10._pool._rpm_429)
j10 = "\n".join(logs10)
ck("log ghi rõ số lần liên tiếp 1/2/3",
   all(f"lần {n} liên tiếp" in j10 for n in (1, 2, 3)), j10)
# a@ gọi tốt ⇒ reset backoff
_handler["fn"] = lambda url: _Resp(200, OK_BODY)
_unlock_key1()
coord10.request("xin chao")
ck("gọi thành công ⇒ clear backoff của a@",
   "a@gmail.com" not in coord10._pool._rpm_429, coord10._pool._rpm_429)

# ════════════════════════════════════════════════════════════════════════════
print("\n=== 11. P2: gap cứng ≥8s giữa 2 call CÙNG account (pace thật) ===")
gs.pace = _orig_pace                    # dùng pace THẬT (sleep giả, không thật)
slept11 = []


class _Rand11:
    def uniform(self, a, b):
        return a                       # kịch bản xấu nhất: base nhỏ nhất


class _TimeProxy11:
    def time(self):
        return _real_time.time()

    def sleep(self, s):
        slept11.append(s)              # ghi nhận chứ KHÔNG ngủ thật (test nhanh)

    def __getattr__(self, n):
        return getattr(_real_time, n)


_orig_rand11, _orig_time11 = gs.random, gs.time
_last_ts_orig11 = gs._last_call_ts
_saved_used11 = gs._account_last_used
try:
    gs.random = _Rand11()
    gs.time = _TimeProxy11()
    gs._last_call_ts = 0.0             # elapsed cực lớn → không chờ global
    gs._account_last_used = {}
    gs.pace(interval=1.0, account="acct@test")   # lần đầu: chưa từng dùng → không chờ
    gs.pace(interval=1.0, account="acct@test")   # ngay sau đó: gap 8s chưa đủ
    ck("call thứ 2 cùng account PHẢI chờ ≥8s (gap cứng)",
       bool(slept11) and slept11[-1] >= 7.9, slept11)
    gs._account_last_used.clear()
    gs.pace(interval=1.0, account="acct2@test")  # account khác → không bị vướng gap
    ck("account khác không bị ảnh hưởng bởi gap của acct1",
       bool(slept11) and slept11[-1] < 7.9, slept11)
finally:
    gs.random, gs.time = _orig_rand11, _orig_time11
    gs._last_call_ts = _last_ts_orig11
    gs._account_last_used = _saved_used11
    gs.pace = lambda *a, **k: None     # trả lại pace tắt cho các test sau

# ════════════════════════════════════════════════════════════════════════════
print("\n=== 12. P5: phản hồi rỗng → thử model kế + dừng ở 3 account ===")
reset_pool()
logs12 = []
coord12, _ = make_coord(["m-a", "m-b"], [KEY1], logs12)
EMPTY_BODY = {"candidates": [{"content": {"parts": []}}]}
urls12 = []


def _h12(url):
    urls12.append(url)
    return _Resp(200, EMPTY_BODY)


_handler["fn"] = _h12
r12 = coord12._try_models("hi", "AIzaTestKey0001", False, None, 0.1, 100, 10,
                          ordered_models=["m-a", "m-b"], email="a@gmail.com")
ck("mọi model rỗng đều được thử (2 POST, không bỏ cuộc sau 1 model)",
   len(urls12) == 2, urls12)
ck("_try_models trả kind=empty", r12.get("kind") == gs.ErrorKind.EMPTY, r12)
j12 = "\n".join(logs12)
ck("log rỗng có mũi tên '→ thử' (đúng lời hứa)",
   "phản hồi rỗng" in j12 and "→ thử 'm-b'" in j12, logs12)
urls12[:] = []
r12b = coord12._try_models("hi", "AIzaTestKey0001", False, None, 0.1, 100, 10,
                           ordered_models=["m-a", "m-b"], email="a@gmail.com")
ck("rỗng 2 lần liên tiếp ⇒ demote (cooldown 300s) model m-a",
   coord12._model_cooldown.get("m-a", 0) > _real_time.time() + 250,
   coord12._model_cooldown)
ck("log demote ghi '2 lần liên tiếp'", "2 lần liên tiếp" in "\n".join(logs12), logs12)
ck("round 2 vẫn trả kind=empty (không treo)", r12b.get("kind") == gs.ErrorKind.EMPTY, r12b)

# 12c: 3 account đều rỗng → báo ĐÚNG bệnh (safety filter), không retry chậm
reset_pool()
logs12c = []
keys3 = [{"key": "AIzaTestKey0001", "email": "a@gmail.com", "status": "active"},
         {"key": "AIzaTestKey0002", "email": "b@gmail.com", "status": "active"},
         {"key": "AIzaTestKey0003", "email": "c@gmail.com", "status": "active"}]
coord12c, _ = make_coord(["m-a"], keys3, logs12c)
_handler["fn"] = lambda url: _Resp(200, EMPTY_BODY)
t12 = _real_time.time()
r12c = coord12c.request("xin chao")
took12 = _real_time.time() - t12
ck("fail sau đúng 3 account rỗng (kind=empty)",
   r12c.get("ok") is False and r12c.get("error", {}).get("kind") == gs.ErrorKind.EMPTY,
   r12c)
ck("message chỉ đúng bệnh: safety filter",
   "safety filter" in r12c.get("error", {}).get("message", ""), r12c)
ck("log đủ các lần (lần N/3)",
   sum("phản hồi rỗng với key" in l for l in logs12c) == 2, logs12c)
ck("KHÔNG sleep retry 2^n như lỗi mạng (nhanh <2s)", took12 < 2.0, took12)
ck("KHÔNG còn log 'Máy chủ bận' cho lỗi rỗng",
   not any("Máy chủ bận" in l for l in logs12c), logs12c)

# ════════════════════════════════════════════════════════════════════════════
print("\n=== 13. P6a + bug X: ảnh 429 → model ảnh khác + URL ĐÚNG model ảnh ===")
reset_pool()
logs13 = []
coord13, _ = make_coord(["m-text"], [KEY1], logs13)
IMG_OK = {"candidates": [{"content": {"parts": [
    {"inlineData": {"mimeType": "image/png", "data": "QUJD"}}]}}]}
urls13 = []


def _h13(url):
    urls13.append(url)
    if "models/img-a" in url:
        return _Resp(429, RATE_BODY)
    return _Resp(200, IMG_OK)


_handler["fn"] = _h13
r13 = coord13._try_image_models("ve con meo", "AIzaTestKey0001",
                                ["img-a", "img-b"], 10)
ck("bug X: URL gọi ĐÚNG model ảnh (img-a → img-b, không rơi về text)",
   len(urls13) == 2 and "models/img-a" in urls13[0] and "models/img-b" in urls13[1],
   urls13)
ck("P6a: ảnh OK trên model ảnh kế, CÙNG key", r13.get("kind") == gs.ErrorKind.OK
   and r13.get("model") == "img-b" and r13.get("b64") == "QUJD", r13)
ck("log 429 tốc độ ảnh có '→ thử img-b'",
   "429 tốc độ" in "\n".join(logs13) and "→ thử 'img-b'" in "\n".join(logs13), logs13)
ck("key KHÔNG bị khoá oan (cooldown rỗng)", not coord13._pool._key_cooldown,
   coord13._pool._key_cooldown)

# 13b: mọi model ảnh 429 tốc độ ⇒ trả QUOTA_RATE sau khi thử đủ (không rơi return)
urls13[:] = []


def _h13b(url):
    urls13.append(url)
    return _Resp(429, RATE_BODY)


_handler["fn"] = _h13b
r13b = coord13._try_image_models("ve", "AIzaTestKey0001", ["img-a", "img-b"], 10)
ck("mọi model ảnh 429 ⇒ kind=quota_rate (không rơi return mập mờ)",
   r13b.get("kind") == gs.ErrorKind.QUOTA_RATE, r13b)
ck("đã thử đủ 2 model ảnh (2 POST)", len(urls13) == 2, urls13)

# 13c: request_image — key1 429 mọi model ⇒ lock_key thật + đổi key, key2 OK
reset_pool()
logs13c = []
coord13c, _ = make_coord(["m-text"], [KEY1, KEY2], logs13c)


def _h13c(url):
    if "AIzaTestKey0001" in url:
        return _Resp(429, RATE_BODY)
    return _Resp(200, IMG_OK)


_handler["fn"] = _h13c
t13 = _real_time.time()
r13c = coord13c.request_image("ve con meo", models=["img-a", "img-b"])
delta13 = coord13c._pool._key_cooldown.get("AIzaTestKey0001", 0) - t13
ck("request_image ok trên key2", r13c.get("ok") is True
   and r13c.get("key", {}).get("key") == "AIzaTestKey0002", r13c)
ck("key1 bị lock_key thật ~65s (backoff lần 1)", 58 <= delta13 <= 72, delta13)
j13 = "\n".join(logs13c)
ck("log ảnh: 'Cooldown riêng key' THẬT + số lần liên tiếp",
   "Cooldown riêng key" in j13 and "lần 1 liên tiếp" in j13, logs13c)

# ── kết thúc ─────────────────────────────────────────────────────────────────
requests.post = _orig_post
gs.pace = _orig_pace
print("\nKết quả: %d PASS / %d FAIL (tổng %d)" %
      (len(PASSED), len(FAILED), len(PASSED) + len(FAILED)))
if FAILED:
    for f in FAILED:
        print("  ✗ " + f)
    sys.exit(1)
