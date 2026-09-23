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
DAILY_ACCOUNT_BUDGET = 1000   # ngân sách an toàn cho 1 account/ngày (Google Free Tier trần 1500 RPD)
DAILY_CALL_BUDGET = 3000          # ngân sách tổng toàn hệ thống
PER_ACCOUNT_MIN_GAP = 8.0         # khoảng cách tối thiểu giữa 2 request vào cùng 1 account (chuẩn anti-ban)
MODEL_FALLBACKS = [
    "gemini-3.5-flash",        # 🥇 Tốt nhất — thế hệ mới nhất
    "gemini-3-flash-preview",  # 🥈 Rất tốt
    "gemini-flash-latest",     # 🥉 Tốt, stable
    "gemini-3.1-flash-lite",   # 🔵 Lite, dự phòng
    "gemini-flash-lite-latest" # 🔵 Lite, dự phòng cuối
]

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
# Ngân sách call / ngày (Chi tiết theo Toàn Cục, theo Account & theo Key)
# ─────────────────────────────────────────────────────────────
_call_stats_lock = threading.Lock()
_call_date = None
_call_stats = {"total": 0}
_account_call_stats = {}   # account_email -> count
_key_call_stats = {}       # key_id -> count


def track_call(key_obj=None):
    """Tăng bộ đếm call hôm nay theo toàn cục, theo account và theo key; trả về (total, acct_total)."""
    global _call_date
    today = time.strftime("%Y-%m-%d")
    with _call_stats_lock:
        if _call_date != today:
            _call_date = today
            _call_stats["total"] = 0
            _account_call_stats.clear()
            _key_call_stats.clear()
        _call_stats["total"] += 1
        acct_total = 0
        if key_obj:
            acct = (key_obj.get("email") or "unknown").strip().lower() or "unknown"
            _account_call_stats[acct] = _account_call_stats.get(acct, 0) + 1
            acct_total = _account_call_stats[acct]

            raw_key = key_obj.get("key", "")
            kid = f"{acct}_{key_obj.get('project_id', '')}_{raw_key[:12]}"
            _key_call_stats[kid] = _key_call_stats.get(kid, 0) + 1

            key_obj["today_calls"] = _key_call_stats[kid]
            key_obj["today_account_calls"] = acct_total
            key_obj["call_date"] = today
        return _call_stats["total"], acct_total


def get_account_daily_calls(account):
    """Lấy số lượt gọi trong ngày hôm nay của 1 account (email)."""
    today = time.strftime("%Y-%m-%d")
    with _call_stats_lock:
        if _call_date != today:
            return 0
        acct = (account or "unknown").strip().lower() or "unknown"
        return _account_call_stats.get(acct, 0)


def get_today_call_stats():
    """Lấy toàn bộ thống kê gọi API hôm nay."""
    today = time.strftime("%Y-%m-%d")
    with _call_stats_lock:
        if _call_date != today:
            return {"date": today, "total": 0, "accounts": {}}
        return {
            "date": today,
            "total": _call_stats["total"],
            "accounts": dict(_account_call_stats)
        }


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
    ALL_BUDGET_EXHAUSTED = "all_budget_exhausted" # Đạt ngân sách an toàn hôm nay (tất cả account)


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
        if not candidates:
            return ""
        candidate = candidates[0] if isinstance(candidates[0], dict) else {}
        parts = candidate.get("content", {}).get("parts", []) if isinstance(candidate, dict) else []
        texts = []
        for p in parts:
            if isinstance(p, dict) and "text" in p and p["text"]:
                texts.append(p["text"])
        return "".join(texts).strip()
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────
# Account-Cluster Rotation + Cooldown 1h
# ─────────────────────────────────────────────────────────────
class AccountPool:
    """Gom key theo account; xoay vòng account; khóa account sau 429 hoặc xong batch."""

    def __init__(self, account_daily_budget=DAILY_ACCOUNT_BUDGET):
        self._keys = []
        self._cooldown = {}          # account -> unlock ts
        self._last_account = None
        self._acct_counters = {}
        self._account_daily_budget = account_daily_budget
        self._account_last_used = {} # account -> timestamp of last call
        self._lock = threading.Lock()

    def set_account_daily_budget(self, budget):
        with self._lock:
            self._account_daily_budget = budget

    def sync(self, keys):
        self._keys = list(keys or [])
        # Đồng bộ bộ đếm cuộc gọi nếu khởi động lại tiến trình trong cùng ngày
        today = time.strftime("%Y-%m-%d")
        with _call_stats_lock:
            global _call_date
            if _call_date != today:
                _call_date = today
                _call_stats["total"] = 0
                _account_call_stats.clear()
                _key_call_stats.clear()
                for k in self._keys:
                    if k.get("call_date") == today:
                        acct = self.account_of(k).lower()
                        k_calls = k.get("today_calls", 0)
                        acct_calls = k.get("today_account_calls", 0)
                        _account_call_stats[acct] = max(_account_call_stats.get(acct, 0), acct_calls, k_calls)
                        raw_key = k.get("key", "")
                        kid = f"{acct}_{k.get('project_id', '')}_{raw_key[:12]}"
                        _key_call_stats[kid] = max(_key_call_stats.get(kid, 0), k_calls)
                _call_stats["total"] = sum(_account_call_stats.values())

    @staticmethod
    def account_of(key_obj):
        return (key_obj.get("email") or "unknown").strip() or "unknown"

    def lock_account(self, key_obj=None, account=None, duration=ACCOUNT_COOLDOWN):
        acct = account or (self.account_of(key_obj) if key_obj else None)
        if not acct:
            return 0
        until = int(time.time() + duration)
        with self._lock:
            self._cooldown[acct] = until
            for k in self._keys:
                if self.account_of(k) == acct:
                    k["cooldown_until"] = until
        return until

    def unlock_account(self, key_obj=None, account=None):
        acct = account or (self.account_of(key_obj) if key_obj else None)
        if not acct:
            return
        with self._lock:
            self._cooldown.pop(acct, None)
            for k in self._keys:
                if self.account_of(k) == acct:
                    k.pop("cooldown_until", None)

    def account_locked(self, account, now=None):
        now = now or time.time()
        with self._lock:
            if self._cooldown.get(account, 0) > now:
                return True
            for k in self._keys:
                if self.account_of(k) == account and k.get("cooldown_until", 0) > now:
                    return True
            return False

    def all_accounts_exhausted_daily(self):
        """Kiểm tra xem tất cả account trong pool đều đã đạt ngân sách an toàn hôm nay chưa."""
        with self._lock:
            accounts = {self.account_of(k).lower() for k in self._keys if k.get("status") != "invalid"}
            if not accounts:
                return False
            return all(get_account_daily_calls(acct) >= self._account_daily_budget for acct in accounts)

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
            acct = self.account_of(k).lower()
            # Bỏ qua account nếu đã đạt ngân sách an toàn hôm nay
            if get_account_daily_calls(acct) >= self._account_daily_budget:
                continue
            cd_until = max(self._cooldown.get(acct, 0), k.get("cooldown_until", 0))
            if cd_until > now:
                continue
            usable.append(k)
        return usable

    def pick(self, exclude=None):
        """Chọn key: ưu tiên account kế tiếp (round-robin), luân phiên key trong account, giữ giãn cách >= PER_ACCOUNT_MIN_GAP."""
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

            # Kiểm tra khoảng cách an toàn PER_ACCOUNT_MIN_GAP (>= 8.0s) trên cùng 1 account
            now = time.time()
            last_ts = self._account_last_used.get(acct, 0)
            if now - last_ts < PER_ACCOUNT_MIN_GAP and len(names) > 1:
                ready_accts = [a for a in names if (now - self._account_last_used.get(a, 0)) >= PER_ACCOUNT_MIN_GAP]
                if ready_accts:
                    acct = ready_accts[0]

            self._last_account = acct
            keys = groups[acct]
            counter = self._acct_counters.get(acct, 0)
            self._acct_counters[acct] = counter + 1
            picked = keys[counter % len(keys)]
            self._account_last_used[acct] = time.time()
            return picked


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
                 daily_budget=DAILY_CALL_BUDGET, account_budget=DAILY_ACCOUNT_BUDGET,
                 lock_after_success=True):
        if models:
            self._models = list(models)
        else:
            # Ưu tiên đọc từ settings.json (người dùng có thể tuỳ chỉnh thứ tự/bật-tắt)
            try:
                from settings import get_active_model_list
                _from_settings = get_active_model_list()
                self._models = _from_settings if _from_settings else list(MODEL_FALLBACKS)
            except Exception:
                self._models = list(MODEL_FALLBACKS)
        self._log = log_fn or (lambda msg: None)
        self._on_key_status = on_key_status
        self._key_loader = key_loader or (lambda: [])
        self._stop_check = stop_check or (lambda: False)
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._timeout = timeout
        self._max_transient = max_transient
        self._daily_budget = daily_budget
        self._account_budget = account_budget
        self._lock_after_success = lock_after_success
        self._pool = _get_pool()
        self._pool.set_account_daily_budget(account_budget)
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
                self._mark(key_obj, key_obj.get("status", "active"), "")
            except Exception:
                pass

    def _lock_account(self, key_obj, duration=ACCOUNT_COOLDOWN, reason=""):
        until = self._pool.lock_account(key_obj=key_obj, duration=duration)
        if key_obj:
            key_obj["cooldown_until"] = until
            self._mark(key_obj, key_obj.get("status", "active"), reason or "Account cooldown")
        return until

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
            self._lock_account(key_obj, reason="Batch rotation lock")

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
                if model is not self._models[-1]:
                    self._log(f"⏱ Model '{model}' phản hồi quá lâu (Timeout > {timeout}s); chuyển sang model fallback...")
                    last = {"kind": ErrorKind.NETWORK, "message": "timeout", "model": model}
                    continue
                return {"kind": ErrorKind.NETWORK, "message": "timeout", "model": model}
            except requests.exceptions.RequestException as exc:
                if model is not self._models[-1]:
                    self._log(f"🌐 Model '{model}' lỗi kết nối ({type(exc).__name__}); chuyển sang model fallback...")
                    last = {"kind": ErrorKind.NETWORK, "message": f"{type(exc).__name__}: {exc}", "model": model}
                    continue
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
                if model is not self._models[-1]:
                    self._log(f"⚠ Model '{model}' phản hồi rỗng; chuyển sang model fallback...")
                    last = {"kind": kind, "message": msg, "status_code": status_code, "model": model}
                    continue
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
        account_attempts = 0
        MAX_ACCOUNT_ATTEMPTS = 3  # Giới hạn thử tối đa 3 account khác nhau/lượt gọi để tránh đốt sạch pool

        while True:
            if self._stop_check():
                return {"ok": False, "text": "", "error": {"kind": ErrorKind.STOPPED}}
            pool.sync(self._key_loader() or [])
            if pool.all_accounts_exhausted_daily():
                stats = get_today_call_stats()
                tot = stats.get("total", 0)
                accts = stats.get("accounts", {})
                self._log(
                    f"🛑 TẤT CẢ các tài khoản Google ({len(accts)} accounts, tổng {tot:,} calls) "
                    f"đã đạt ngân sách an toàn hôm nay ({self._account_budget:,} calls/account). "
                    f"Tự động dừng an toàn để bảo vệ 100% tài khoản Google."
                )
                return {
                    "ok": False,
                    "text": "",
                    "error": {
                        "kind": ErrorKind.ALL_BUDGET_EXHAUSTED,
                        "message": f"Tất cả {len(accts)} accounts đã đạt ngân sách an toàn ({self._account_budget} calls/acc) hôm nay."
                    }
                }
            key_obj = pool.pick(exclude)
            if not key_obj:
                if pool.all_accounts_exhausted_daily():
                    stats = get_today_call_stats()
                    tot = stats.get("total", 0)
                    accts = stats.get("accounts", {})
                    self._log(
                        f"🛑 TẤT CẢ các tài khoản Google ({len(accts)} accounts, tổng {tot:,} calls) "
                        f"đã đạt ngân sách an toàn hôm nay ({self._account_budget:,} calls/account). "
                        f"Tự động dừng an toàn để bảo vệ 100% tài khoản Google."
                    )
                    return {
                        "ok": False,
                        "text": "",
                        "error": {
                            "kind": ErrorKind.ALL_BUDGET_EXHAUSTED,
                            "message": f"Tất cả {len(accts)} accounts đã đạt ngân sách an toàn hôm nay."
                        }
                    }
                # Nếu đã thử qua các account nhưng hết key tạm thời do cooldown ngắn
                if account_attempts > 0:
                    self._log("⏳ Tạm thời chưa có key sẵn sàng (đang nghỉ tốc độ). Chờ 15s để hồi phục...")
                    time.sleep(15)
                    exclude.clear()
                    account_attempts = 0
                    continue
                return {"ok": False, "text": "", "error": {"kind": ErrorKind.NO_KEY}}
            api_key = key_obj.get("key") or ""
            email = key_obj.get("email") or "?"
            pace()
            res = self._try_models(prompt_text, api_key, json_mode, response_schema,
                                   temp, mout, tout)
            kind = res.get("kind")
            msg = res.get("message", "")

            if kind == ErrorKind.OK:
                total, acct_total = track_call(key_obj)
                self._touch(key_obj)
                if self._lock_after_success:
                    self._maybe_lock_after_success(key_obj, pool._keys)
                if acct_total >= self._account_budget:
                    self._log(
                        f"ℹ Account '{email}' đã đạt {acct_total:,}/{self._account_budget:,} calls hôm nay (ngân sách an toàn). "
                        f"Tạm ngưng account này đến hết ngày, tự động chuyển sang account khác..."
                    )
                if total > self._daily_budget:
                    self._log(f"⚠ Đã gọi {total:,} lần hôm nay (ngân sách tổng {self._daily_budget:,}/ngày).")
                return {"ok": True, "text": res["text"], "key": key_obj,
                        "model": res.get("model"), "total_calls": total, "acct_calls": acct_total}

            if kind == ErrorKind.QUOTA_DAILY:
                self._log(f"⚠ Key {email} hết quota ngày (Daily). Khóa account 60 phút, chuyển key...")
                self._lock_account(key_obj, duration=ACCOUNT_COOLDOWN, reason=f"HTTP 429 Daily: {msg[:90]}")
                self._mark(key_obj, "exhausted", f"HTTP 429 Daily: {msg[:90]}")
                exclude.add(api_key)
                account_attempts += 1
                if account_attempts >= MAX_ACCOUNT_ATTEMPTS:
                    self._log(f"⚠ Đã thử {MAX_ACCOUNT_ATTEMPTS} account liên tiếp gặp giới hạn. Nghỉ 15s tránh đốt dồn dập...")
                    time.sleep(15)
                    account_attempts = 0
                continue

            if kind == ErrorKind.QUOTA_RATE:
                # 429 RPM/TPM = giới hạn tốc độ 1 phút -> cooldown ngắn (60s), TUYỆT ĐỐI KHÔNG đánh dấu exhausted
                retry_delay = retry_delay_from(msg)
                self._log(f"⚠ Key {email} chạm giới hạn tốc độ RPM/TPM ({retry_delay}s). Cooldown {retry_delay}s (không khóa vĩnh viễn), đổi key...")
                self._lock_account(key_obj, duration=retry_delay, reason=f"HTTP 429 RPM/TPM: {msg[:90]}")
                exclude.add(api_key)
                account_attempts += 1
                if account_attempts >= MAX_ACCOUNT_ATTEMPTS:
                    self._log(f"⚠ Đã thử {MAX_ACCOUNT_ATTEMPTS} account gặp giới hạn tốc độ. Tạm dừng 15s để server Google giải tỏa lưu lượng...")
                    time.sleep(15)
                    account_attempts = 0
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
                    self._lock_account(key_obj, reason=f"Model restriction: {msg[:80]}")
                    exclude.add(api_key)
                    continue
                return {"ok": False, "text": "",
                        "error": {"kind": kind, "message": msg[:200],
                                  "status_code": res.get("status_code")}}

            if kind == ErrorKind.NETWORK:
                transient += 1
                if transient >= self._max_transient:
                    # Chế độ kiên trì chờ mạng (Network Keep-Alive loop)
                    self._log(f"🌐 Mất kết nối mạng ({msg[:60]}). Đang tự động vào chế độ chờ mạng hồi phục (kiểm tra mỗi 30s, tối đa 10 phút)...")
                    network_recovered = False
                    for wait_round in range(1, 21):  # 20 lần x 30s = 10 phút
                        if self._stop_check():
                            return {"ok": False, "text": "", "error": {"kind": ErrorKind.STOPPED}}
                        time.sleep(30)
                        try:
                            # Kiểm tra kết nối nhẹ tới Google/Cloudflare
                            chk = requests.get("https://www.google.com/generate_204", timeout=10)
                            if chk.status_code in (200, 204):
                                self._log(f"✅ Mạng Internet đã kết nối lại bình thường (sau {wait_round * 30}s). Tiếp tục gửi câu hỏi...")
                                network_recovered = True
                                transient = 0
                                break
                        except Exception:
                            self._log(f"⏳ Vẫn đang chờ mạng có lại (đã chờ {wait_round * 30}s / 600s)...")
                    if not network_recovered:
                        return {"ok": False, "text": "", "error": {"kind": kind, "message": "Mất kết nối mạng quá 10 phút."}}
                    continue

                delay = min(2 ** transient, 30)
                self._log(f"🌐 Lỗi kết nối mạng: {msg[:70]}. Chờ {delay}s để kết nối lại (lần {transient}/{self._max_transient})...")
                time.sleep(delay)
                continue

            if kind in (ErrorKind.SERVER, ErrorKind.EMPTY):
                transient += 1
                if transient >= self._max_transient:
                    return {"ok": False, "text": "",
                            "error": {"kind": kind, "message": msg[:200]}}
                delay = min(2 ** transient, 30)
                self._log(f"⚠ Máy chủ bận/phản hồi rỗng: {msg[:70]}. Chờ {delay}s rồi thử lại (lần {transient}/{self._max_transient})...")
                time.sleep(delay)
                continue

            return {"ok": False, "text": "", "error": {"kind": kind, "message": msg[:200]}}