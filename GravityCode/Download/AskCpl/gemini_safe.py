import random
import re
import threading
import time

import requests

# ─────────────────────────────────────────────────────────────
# Cấu hình an toàn chuẩn (skill: gemini_api_key_handling)
# ─────────────────────────────────────────────────────────────
PACE_MIN = 3.5
PACE_MAX = 5.0
PACE_JITTER = (0.5, 1.5)          # jitter phá tần số bot
ACCOUNT_COOLDOWN = 3600           # 60 phút nghỉ cho 1 account sau batch/429
MAX_KEYS_PER_ACCOUNT = 2          # khuyến nghị 1-2 key/account
DAILY_CALL_BUDGET = 3000          # ngân sách call/ngày, vượt thì cảnh báo
MODEL_FALLBACKS = ["gemini-flash-latest", "gemini-3-flash-preview", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-flash-lite-latest"]

# ─────────────────────────────────────────────────────────────
# Global Rate Limiter — mọi call Gemini đều đi qua pace()
# ─────────────────────────────────────────────────────────────
_pace_lock = threading.Lock()
_last_call_ts = 0.0


def pace():
    """Nghỉ 3.5-5.0s + jitter 0.5-1.5s kể từ lần gọi trước (thread-safe, toàn tiến trình)."""
    global _last_call_ts
    with _pace_lock:
        base = random.uniform(PACE_MIN, PACE_MAX)
        jitter = random.uniform(*PACE_JITTER)
        elapsed = time.time() - _last_call_ts
        wait = base + jitter - elapsed
        if wait > 0:
            time.sleep(wait)
        _last_call_ts = time.time()


# ─────────────────────────────────────────────────────────────
# Ngân sách call / ngày
# ─────────────────────────────────────────────────────────────
_call_stats_lock = threading.Lock()
_call_date = None
_call_stats = {"total": 0}


def track_call():
    """Tăng bộ đếm call hôm nay; trả về tổng số call (reset theo ngày)."""
    global _call_date
    today = time.strftime("%Y-%m-%d")
    with _call_stats_lock:
        if _call_date != today:
            _call_date = today
            _call_stats["total"] = 0
        _call_stats["total"] += 1
        return _call_stats["total"]


def account_health_report(keys):
    """Cảnh báo nếu 1 account có quá nhiều key (nguy cơ bị Google khóa)."""
    counts = {}
    for k in keys or []:
        acct = (k.get("email") or "unknown").strip() or "unknown"
        counts[acct] = counts.get(acct, 0) + 1
    issues = []
    for acct, n in counts.items():
        if n > MAX_KEYS_PER_ACCOUNT:
            issues.append(
                f"⚠ Account '{acct}' có {n} key — vượt mức khuyến nghị {MAX_KEYS_PER_ACCOUNT}/account, "
                f"dễ bị Google khóa. Nên tách sang account khác."
            )
        elif n >= 2:
            issues.append(f"ℹ Account '{acct}' có {n} key (tối đa khuyến nghị {MAX_KEYS_PER_ACCOUNT}).")
    return issues


_health_logged = set()


def warn_account_health(keys, log_fn):
    """Log cảnh báo health một lần mỗi tiến trình."""
    for issue in account_health_report(keys):
        sig = issue[:60]
        if sig not in _health_logged:
            _health_logged.add(sig)
            log_fn(issue)


# ─────────────────────────────────────────────────────────────
# Phân loại lỗi chuẩn
# ─────────────────────────────────────────────────────────────
class ErrorKind:
    OK = "ok"
    QUOTA_DAILY = "quota_daily"   # 429 PerDay → exhausted + khóa account
    QUOTA_RATE = "quota_rate"     # 429 RPM/TPM → đợi retryDelay rồi thử lại
    INVALID_KEY = "invalid_key"   # 401/403 + API_KEY_INVALID → invalid
    REQUEST_BAD = "request_bad"   # 400/schema/model → không vô hiệu key
    SERVER = "server"             # 5xx/UNAVAILABLE → xoay key + backoff
    NETWORK = "network"           # timeout/lỗi mạng → xoay key + backoff
    EMPTY = "empty"               # 200 nhưng phản hồi rỗng
    NO_KEY = "no_key"
    STOPPED = "stopped"


def classify_response(status_code, body):
    """Phân loại HTTP response thành ErrorKind theo chuẩn skill."""
    if isinstance(body, dict):
        err = body.get("error", {})
        if isinstance(err, dict):
            message = err.get("message", "") or ""
            status = err.get("status", "") or ""
        else:
            message = str(err)
            status = ""
    else:
        message = str(body)
        status = ""
    full = f"{message} {status}"
    low = full.lower()

    if status_code == 200:
        return ErrorKind.OK, message
    if status_code == 429:
        if "perday" in low or "per-day" in low or "per day" in low or "daily" in low:
            return ErrorKind.QUOTA_DAILY, message
        return ErrorKind.QUOTA_RATE, message
    if status_code in (401, 403):
        if ("api_key_invalid" in low or "invalid authentication" in low
                or "invalid key" in low or "api key not valid" in low
                or "api key not found" in low or "access_token_type_unsupported" in low):
            return ErrorKind.INVALID_KEY, message
        return ErrorKind.REQUEST_BAD, message
    if status_code == 400:
        if "api_key_invalid" in low:
            return ErrorKind.INVALID_KEY, message
        return ErrorKind.REQUEST_BAD, message
    if status_code >= 500:
        return ErrorKind.SERVER, message
    return ErrorKind.REQUEST_BAD, message


def retry_delay_from(msg):
    """Parse retryDelay (vd: 'retryDelay: 4s') từ message lỗi 429."""
    m = re.search(r'retryDelay["' + chr(92) + r's:]+"?(\d+)s?"?', msg, re.IGNORECASE)
    if m:
        return int(m.group(1)) + 5
    return 65


def is_model_restriction(msg):
    """Lỗi 403/404 về quyền truy cập model/account, không phải lỗi prompt.

    Các project khác nhau có danh sách model khác nhau; key bị 'denied access'
    hay model 'no longer available' nên xoay account thay vì báo REQUEST_BAD."""
    low = (msg or "").lower()
    markers = (
        "denied access", "has been denied", "no longer available", "is not found",
        "not found for api version", "not supported for generatecontent",
        "does not have access", "access to the model", "permission denied",
        "no longer available to new users",
    )
    return any(m in low for m in markers)


def extract_text(body):
    try:
        candidates = body.get("candidates", []) if isinstance(body, dict) else []
        candidate = candidates[0] if candidates else {}
        parts = candidate.get("content", {}).get("parts", []) if isinstance(candidate, dict) else []
        return parts[0].get("text", "") if parts else ""
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────
# Account-Cluster Rotation + Cooldown 1h
# ─────────────────────────────────────────────────────────────
class AccountPool:
    """Gom key theo account; xoay vòng account; khóa account sau 429 hoặc xong batch."""

    def __init__(self):
        self._keys = []
        self._cooldown = {}          # account -> unlock ts
        self._last_account = None
        self._acct_counters = {}
        self._lock = threading.Lock()

    def sync(self, keys):
        self._keys = list(keys or [])

    @staticmethod
    def account_of(key_obj):
        return (key_obj.get("email") or "unknown").strip() or "unknown"

    def lock_account(self, key_obj=None, account=None, duration=ACCOUNT_COOLDOWN):
        acct = account or (self.account_of(key_obj) if key_obj else None)
        if not acct:
            return
        with self._lock:
            self._cooldown[acct] = time.time() + duration

    def unlock_account(self, key_obj=None, account=None):
        acct = account or (self.account_of(key_obj) if key_obj else None)
        if not acct:
            return
        with self._lock:
            self._cooldown.pop(acct, None)

    def account_locked(self, account, now=None):
        now = now or time.time()
        with self._lock:
            return self._cooldown.get(account, 0) > now

    def _usable_keys(self, exclude):
        now = time.time()
        usable = []
        for k in self._keys:
            status = k.get("status", "active")
            if status == "invalid":
                continue
            if status == "exhausted":
                nct = k.get("next_check_time", 0)
                if nct > 0 and now < nct:
                    continue
            raw = k.get("key")
            if not raw or raw in exclude:
                continue
            acct = self.account_of(k)
            if self._cooldown.get(acct, 0) > now:
                continue
            usable.append(k)
        return usable

    def pick(self, exclude=None):
        """Chọn key: ưu tiên account kế tiếp (round-robin), luân phiên key trong account."""
        exclude = set(exclude or [])
        with self._lock:
            usable = self._usable_keys(exclude)
            if not usable:
                return None
            groups = {}
            for k in usable:
                groups.setdefault(self.account_of(k), []).append(k)
            names = sorted(groups)
            if self._last_account and self._last_account in names:
                idx = (names.index(self._last_account) + 1) % len(names)
            else:
                idx = 0
            acct = names[idx]
            self._last_account = acct
            keys = groups[acct]
            counter = self._acct_counters.get(acct, 0)
            self._acct_counters[acct] = counter + 1
            return keys[counter % len(keys)]


_pool_instance = None


def _get_pool():
    global _pool_instance
    if _pool_instance is None:
        _pool_instance = AccountPool()
    return _pool_instance


# ─────────────────────────────────────────────────────────────
# GeminiCoordinator — bộ điều phối gọi an toàn dùng chung
# ─────────────────────────────────────────────────────────────
class GeminiCoordinator:
    def __init__(self, models=None, log_fn=None, on_key_status=None,
                 key_loader=None, stop_check=None, temperature=0.1,
                 max_output_tokens=8192, timeout=90, max_transient=6,
                 daily_budget=DAILY_CALL_BUDGET, lock_after_success=True):
        self._models = models or list(MODEL_FALLBACKS)
        self._log = log_fn or (lambda msg: None)
        self._on_key_status = on_key_status
        self._key_loader = key_loader or (lambda: [])
        self._stop_check = stop_check or (lambda: False)
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._timeout = timeout
        self._max_transient = max_transient
        self._daily_budget = daily_budget
        self._lock_after_success = lock_after_success
        self._pool = _get_pool()
        try:
            warn_account_health(self._key_loader(), self._log)
        except Exception:
            pass

    # ── callback nội bộ ──
    def _mark(self, key_obj, status, error_msg):
        if self._on_key_status:
            try:
                self._on_key_status(key_obj, status, error_msg)
            except Exception as e:
                self._log(f"⚠ Không cập nhật được trạng thái key: {e}")

    def _touch(self, key_obj):
        """Cập nhật last_check_time; khôi phục active nếu key trước đó exhausted."""
        if key_obj.get("status") == "exhausted":
            self._mark(key_obj, "active", "")
        else:
            try:
                key_obj["last_check_time"] = int(time.time())
            except Exception:
                pass

    def _maybe_lock_after_success(self, key_obj, keys):
        """Sau 1 batch thành công: khóa account 1h nếu có >=2 account và còn account khác mở."""
        pool = self._pool
        used = pool.account_of(key_obj)
        accounts = set()
        for k in keys:
            if k.get("status") in ("active", "exhausted"):
                accounts.add(pool.account_of(k))
        if len(accounts) < 2:
            return
        now = time.time()
        has_free = any(acct != used and not pool.account_locked(acct, now) for acct in accounts)
        if has_free:
            pool.lock_account(key_obj)

    def _try_models(self, prompt_text, api_key, json_mode, response_schema,
                    temperature, max_output_tokens, timeout):
        last = None
        for model in self._models:
            if self._stop_check():
                return {"kind": ErrorKind.STOPPED, "model": model}
            url = (f"https://generativelanguage.googleapis.com/v1beta/"
                   f"models/{model}:generateContent?key={api_key}")
            config = {"maxOutputTokens": max_output_tokens, "temperature": temperature}
            if response_schema:
                config["responseMimeType"] = "application/json"
                config["responseSchema"] = response_schema
            elif json_mode:
                config["responseMimeType"] = "application/json"
            try:
                resp = requests.post(url, headers={"Content-Type": "application/json"},
                                     json={"contents": [{"parts": [{"text": prompt_text}]}],
                                           "generationConfig": config},
                                     timeout=timeout)
                ctype = resp.headers.get("content-type", "")
                body = resp.json() if "application/json" in ctype else {}
                status_code = resp.status_code
            except requests.exceptions.Timeout:
                return {"kind": ErrorKind.NETWORK, "message": "timeout", "model": model}
            except requests.exceptions.RequestException as exc:
                return {"kind": ErrorKind.NETWORK,
                        "message": f"{type(exc).__name__}: {exc}", "model": model}

            kind, msg = classify_response(status_code, body)
            if kind == ErrorKind.OK:
                text = extract_text(body)
                if text:
                    return {"kind": ErrorKind.OK, "text": text,
                            "model": model, "message": msg}
                kind = ErrorKind.EMPTY
                msg = "phản hồi rỗng"
                return {"kind": kind, "message": msg, "status_code": status_code, "model": model}
            if kind == ErrorKind.REQUEST_BAD:
                if model is not self._models[-1]:
                    self._log(f"⚠ Model '{model}' từ chối request ({msg[:60]}); thử model fallback.")
                    last = {"kind": kind, "message": msg, "status_code": status_code, "model": model}
                    continue
                return {"kind": kind, "message": msg, "status_code": status_code, "model": model}
            # Lỗi key/server-level: thử model fallback cho cùng key trước khi xoay key.
            # High-demand (503) theo model, không theo key nên model khác có thể cứu được.
            raw_msg = ""
            if isinstance(body, dict):
                err = body.get("error", {})
                if isinstance(err, dict):
                    raw_msg = err.get("message", "") or ""
            if kind in (ErrorKind.SERVER, ErrorKind.NETWORK, ErrorKind.EMPTY):
                if model is not self._models[-1]:
                    self._log(f"⚠ Model '{model}' lỗi {kind} ({msg[:60]}); thử model fallback.")
                    last = {"kind": kind, "message": msg, "status_code": status_code,
                            "raw_msg": raw_msg, "model": model}
                    continue
                return {"kind": kind, "message": msg, "raw_msg": raw_msg,
                        "status_code": status_code, "model": model}
            return {"kind": kind, "message": msg, "raw_msg": raw_msg,
                    "status_code": status_code, "model": model}
        return last or {"kind": ErrorKind.NETWORK, "message": "hết model fallback", "model": None}

    def request(self, prompt_text, json_mode=False, response_schema=None,
                temperature=None, max_output_tokens=None, timeout=None):
        """Gửi 1 prompt với pacing + account rotation + phân loại lỗi chuẩn.

        Trả về dict: {"ok": bool, "text": str, "key": dict, "model": str, "error": {...}}
        """
        pool = self._pool
        exclude = set()
        transient = 0
        temp = temperature if temperature is not None else self._temperature
        mout = max_output_tokens or self._max_output_tokens
        tout = timeout or self._timeout

        while True:
            if self._stop_check():
                return {"ok": False, "text": "", "error": {"kind": ErrorKind.STOPPED}}
            pool.sync(self._key_loader() or [])
            key_obj = pool.pick(exclude)
            if not key_obj:
                return {"ok": False, "text": "", "error": {"kind": ErrorKind.NO_KEY}}
            api_key = key_obj.get("key") or ""
            email = key_obj.get("email") or "?"
            pace()
            res = self._try_models(prompt_text, api_key, json_mode, response_schema,
                                   temp, mout, tout)
            kind = res.get("kind")
            msg = res.get("message", "")

            if kind == ErrorKind.OK:
                total = track_call()
                self._touch(key_obj)
                if self._lock_after_success:
                    self._maybe_lock_after_success(key_obj, pool._keys)
                if total > self._daily_budget:
                    self._log(f"⚠ Đã gọi {total:,} lần hôm nay (ngân sách {self._daily_budget:,}/ngày); "
                              f"nên dừng để tránh bị Google khóa account.")
                return {"ok": True, "text": res["text"], "key": key_obj,
                        "model": res.get("model"), "total_calls": total}

            if kind == ErrorKind.QUOTA_DAILY:
                self._log(f"⚠ Key {email} hết quota ngày (Daily). Khóa account 60 phút, chuyển key...")
                pool.lock_account(key_obj)
                self._mark(key_obj, "exhausted", f"HTTP 429 Daily: {msg[:90]}")
                exclude.add(api_key)
                continue

            if kind == ErrorKind.QUOTA_RATE:
                if transient < self._max_transient:
                    delay = retry_delay_from(res.get("raw_msg") or msg)
                    self._log(f"⏳ Quá tải tốc độ (RPM/TPM): {msg[:60]}. Chờ {delay}s rồi thử lại...")
                    time.sleep(delay)
                    transient += 1
                    continue
                self._log(f"⚠ Key {email} quá tải liên tục. Khóa account 60 phút, chuyển key...")
                pool.lock_account(key_obj)
                exclude.add(api_key)
                continue

            if kind == ErrorKind.INVALID_KEY:
                self._mark(key_obj, "invalid", f"HTTP {res.get('status_code', '')}: {msg[:90]}")
                self._log(f"✗ Key {email} bị từ chối (Invalid). Chuyển key...")
                exclude.add(api_key)
                continue

            if kind == ErrorKind.REQUEST_BAD:
                if is_model_restriction(msg):
                    # 403 denied access / model đã ngừng: lỗi theo account, xoay account.
                    self._log(f"⚠ Key {email} không được phép dùng model này ({msg[:80]}). Khóa account, xoay key...")
                    pool.lock_account(key_obj)
                    exclude.add(api_key)
                    continue
                return {"ok": False, "text": "",
                        "error": {"kind": kind, "message": msg[:200],
                                  "status_code": res.get("status_code")}}

            if kind in (ErrorKind.SERVER, ErrorKind.NETWORK, ErrorKind.EMPTY):
                transient += 1
                if transient >= self._max_transient:
                    return {"ok": False, "text": "",
                            "error": {"kind": kind, "message": msg[:200]}}
                # Lỗi 503 high-demand/NETWORK theo model/region, không theo key:
                # retry lại CÙNG key với backoff lũy tiến thay vì xoay key rồi bỏ cuộc.
                delay = min(2 ** transient, 30)
                self._log(f"⚠ {kind} key {email}: {msg[:80]}. Chờ {delay}s rồi thử lại (lần {transient}/{self._max_transient})...")
                time.sleep(delay)
                continue

            return {"ok": False, "text": "", "error": {"kind": kind, "message": msg[:200]}}