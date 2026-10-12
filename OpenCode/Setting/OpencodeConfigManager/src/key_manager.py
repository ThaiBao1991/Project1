"""
Key Manager - Hệ thống quản lý API Key với rotation/fallback tự động
Dựa trên gemini_safe.py từ project Antigravity (AskCpl)
"""

import json
import os
import base64
import threading
import time
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class ErrorKind(Enum):
    OK = "ok"
    QUOTA_DAILY = "quota_daily"
    QUOTA_RATE = "quota_rate"
    INVALID_KEY = "invalid_key"
    REQUEST_BAD = "request_bad"
    SERVER = "server"
    NETWORK = "network"
    EMPTY = "empty"
    NO_KEY = "no_key"
    STOPPED = "stopped"
    ALL_BUDGET_EXHAUSTED = "all_budget_exhausted"


@dataclass
class APIKey:
    key: str                    # Raw API key (ENC: encoded khi lưu)
    email: str                  # Account email/name
    project_id: str = ""        # Google Cloud project ID
    status: str = "active"      # active, exhausted, invalid
    cooldown_until: int = 0     # Unix timestamp khi hết cooldown
    reset_time: int = 0         # Khi quota sẽ reset (24h sau)
    next_check_time: int = 0    # Khi check lại key exhausted (3h sau)
    last_check_time: int = 0    # Lần cuối check
    today_calls: int = 0        # Số call hôm nay
    today_account_calls: int = 0 # Số call account hôm nay
    call_date: str = ""         # Ngày gọi cuối
    error_msg: str = ""         # Thông báo lỗi cuối

    def get_raw_key(self) -> str:
        """Giải mã key nếu là ENC:"""
        if self.key.startswith("ENC:"):
            try:
                b64 = self.key[4:]
                return base64.b64decode(b64.encode("utf-8")).decode("utf-8")[::-1]
            except Exception:
                return ""
        return self.key

    def set_raw_key(self, raw_key: str):
        """Mã hóa key thành ENC: format"""
        if not raw_key:
            self.key = ""
            return
        if raw_key.startswith("ENC:"):
            self.key = raw_key
            return
        reversed_str = raw_key[::-1]
        b64 = base64.b64encode(reversed_str.encode("utf-8")).decode("utf-8")
        self.key = f"ENC:{b64}"

    def is_usable(self, now: int = None, account_budget: int = 1000) -> bool:
        """Kiểm tra key có dùng được không"""
        now = now or int(time.time())
        if self.status == "invalid":
            return False
        if self.status == "exhausted":
            if self.reset_time > 0 and now > self.reset_time:
                return True  # Đã qua 24h, có thể dùng lại
            if self.next_check_time > 0 and now < self.next_check_time:
                return False  # Chưa đến lúc check lại
            return True  # Đã qua 3h, cho phép thử
        if self.cooldown_until > now:
            return False
        if self.today_account_calls >= account_budget:
            return False
        return True


class KeyPool:
    """Quản lý pool key theo account, xoay vòng, cooldown"""

    def __init__(self, account_daily_budget: int = 1000, max_keys_per_account: int = 2):
        self._keys: List[APIKey] = []
        self._cooldown: Dict[str, int] = {}  # account -> unlock ts
        self._last_account: Optional[str] = None
        self._acct_counters: Dict[str, int] = {}
        self._account_daily_budget = account_daily_budget
        self._account_last_used: Dict[str, float] = {}
        self._lock = threading.Lock()
        self.max_keys_per_account = max_keys_per_account

    def load_from_list(self, key_list: List[Dict]):
        """Load từ list dict (từ settings.json)"""
        self._keys = []
        for k in key_list:
            ak = APIKey(
                key=k.get("key", ""),
                email=k.get("email", "unknown"),
                project_id=k.get("project_id", ""),
                status=k.get("status", "active"),
                cooldown_until=k.get("cooldown_until", 0),
                reset_time=k.get("reset_time", 0),
                next_check_time=k.get("next_check_time", 0),
                last_check_time=k.get("last_check_time", 0),
                today_calls=k.get("today_calls", 0),
                today_account_calls=k.get("today_account_calls", 0),
                call_date=k.get("call_date", ""),
                error_msg=k.get("error_msg", "")
            )
            self._keys.append(ak)

    def to_list(self) -> List[Dict]:
        """Xuất ra list dict để lưu"""
        result = []
        for k in self._keys:
            result.append({
                "key": k.key,
                "email": k.email,
                "project_id": k.project_id,
                "status": k.status,
                "cooldown_until": k.cooldown_until,
                "reset_time": k.reset_time,
                "next_check_time": k.next_check_time,
                "last_check_time": k.last_check_time,
                "today_calls": k.today_calls,
                "today_account_calls": k.today_account_calls,
                "call_date": k.call_date,
                "error_msg": k.error_msg
            })
        return result

    def get_accounts(self) -> List[str]:
        """Danh sách account duy nhất"""
        return list(set(k.email.lower() for k in self._keys))

    def get_keys_for_account(self, account: str) -> List[APIKey]:
        """Lấy key của 1 account"""
        return [k for k in self._keys if k.email.lower() == account.lower()]

    def account_health_check(self) -> List[str]:
        """Kiểm tra account có quá nhiều key không"""
        issues = []
        counts = {}
        for k in self._keys:
            counts[k.email.lower()] = counts.get(k.email.lower(), 0) + 1
        for acct, n in counts.items():
            if n > self.max_keys_per_account:
                issues.append(f"⚠ Account '{acct}' có {n} key — vượt {self.max_keys_per_account}/account, rủi ro bị khóa!")
        return issues

    def lock_account(self, account: str, duration: int = 3600):
        """Khóa account trong duration giây"""
        with self._lock:
            until = int(time.time() + duration)
            self._cooldown[account] = until
            for k in self._keys:
                if k.email.lower() == account.lower():
                    k.cooldown_until = until

    def unlock_account(self, account: str):
        with self._lock:
            self._cooldown.pop(account, None)
            for k in self._keys:
                if k.email.lower() == account.lower():
                    k.cooldown_until = 0

    def is_account_locked(self, account: str, now: int = None) -> bool:
        now = now or int(time.time())
        with self._lock:
            if self._cooldown.get(account, 0) > now:
                return True
            for k in self._keys:
                if k.email.lower() == account.lower() and k.cooldown_until > now:
                    return True
            return False

    def pick_key(self, exclude_keys: set = None) -> Optional[APIKey]:
        """Chọn key: round-robin account, luân phiên key trong account, giữ gap >= 8s"""
        exclude_keys = exclude_keys or set()
        with self._lock:
            now = time.time()
            usable = []
            for k in self._keys:
                if not k.is_usable(now, self._account_daily_budget):
                    continue
                if k.get_raw_key() in exclude_keys:
                    continue
                usable.append(k)

            if not usable:
                return None

            # Group by account
            groups = {}
            for k in usable:
                groups.setdefault(k.email.lower(), []).append(k)

            accounts = sorted(groups.keys())
            if self._last_account and self._last_account in accounts:
                idx = (accounts.index(self._last_account) + 1) % len(accounts)
            else:
                idx = 0

            # Kiểm tra gap >= 8s trên cùng account
            acct = accounts[idx]
            last_ts = self._account_last_used.get(acct, 0)
            if now - last_ts < 8.0 and len(accounts) > 1:
                ready = [a for a in accounts if (now - self._account_last_used.get(a, 0)) >= 8.0]
                if ready:
                    acct = ready[0]

            self._last_account = acct
            keys = groups[acct]
            counter = self._acct_counters.get(acct, 0)
            self._acct_counters[acct] = counter + 1
            picked = keys[counter % len(keys)]
            self._account_last_used[acct] = time.time()
            return picked

    def all_accounts_exhausted(self) -> bool:
        """Tất cả account đã đạt ngân sách?"""
        accounts = set(k.email.lower() for k in self._keys if k.status != "invalid")
        if not accounts:
            return True
        now = int(time.time())
        for acct in accounts:
            total = sum(k.today_account_calls for k in self._keys if k.email.lower() == acct)
            if total < self._account_daily_budget and not self.is_account_locked(acct, now):
                return False
        return True


# Global pace limiter
_pace_lock = threading.Lock()
_last_call_ts = 0.0
PACE_MIN = 3.5
PACE_MAX = 5.0
PACE_JITTER = (0.5, 1.5)
PER_ACCOUNT_MIN_GAP = 8.0
ACCOUNT_COOLDOWN = 3600
MAX_ACCOUNT_ATTEMPTS = 3


def pace():
    """Global pacing: 3.5-5.0s + jitter 0.5-1.5s"""
    global _last_call_ts
    with _pace_lock:
        base = random.uniform(PACE_MIN, PACE_MAX)
        jitter = random.uniform(*PACE_JITTER)
        elapsed = time.time() - _last_call_ts
        wait = base + jitter - elapsed
        if wait > 0:
            time.sleep(wait)
        _last_call_ts = time.time()


# Call tracking
_call_stats_lock = threading.Lock()
_call_date = None
_call_stats = {"total": 0}
_account_call_stats = {}
_key_call_stats = {}


def track_call(key_obj: APIKey):
    """Tăng bộ đếm call theo ngày"""
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
            acct = key_obj.email.lower()
            _account_call_stats[acct] = _account_call_stats.get(acct, 0) + 1
            acct_total = _account_call_stats[acct]

            raw_key = key_obj.get_raw_key()
            kid = f"{acct}_{key_obj.project_id}_{raw_key[:12]}"
            _key_call_stats[kid] = _key_call_stats.get(kid, 0) + 1

            key_obj.today_calls = _key_call_stats[kid]
            key_obj.today_account_calls = acct_total
            key_obj.call_date = today
        return _call_stats["total"], acct_total


def get_account_daily_calls(account: str) -> int:
    today = time.strftime("%Y-%m-%d")
    with _call_stats_lock:
        if _call_date != today:
            return 0
        return _account_call_stats.get(account.lower(), 0)


def get_today_call_stats() -> Dict:
    today = time.strftime("%Y-%m-%d")
    with _call_stats_lock:
        if _call_date != today:
            return {"date": today, "total": 0, "accounts": {}}
        return {
            "date": today,
            "total": _call_stats["total"],
            "accounts": dict(_account_call_stats)
        }


def classify_response(status_code: int, body: Any) -> tuple:
    """Phân loại HTTP response thành ErrorKind"""
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


def retry_delay_from(msg: str) -> int:
    """Parse retryDelay từ message lỗi 429"""
    m = re.search(r'retryDelay["\':\s]+(\d+)s?', msg, re.IGNORECASE)
    if m:
        return int(m.group(1)) + 5
    return 65


def is_model_restriction(msg: str) -> bool:
    """Lỗi 403/404 về quyền truy cập model"""
    low = (msg or "").lower()
    markers = (
        "denied access", "has been denied", "no longer available", "is not found",
        "not found for api version", "not supported for generatecontent",
        "does not have access", "access to the model", "permission denied",
        "no longer available to new users",
    )
    return any(m in low for m in markers)


def extract_text(body: Dict) -> str:
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


MODEL_FALLBACKS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.7-flash"
]


class GeminiCoordinator:
    """Bộ điều phối gọi Gemini an toàn với key rotation"""

    def __init__(self, models=None, log_fn=None, on_key_status=None,
                 key_loader=None, stop_check=None, temperature=0.1,
                 max_output_tokens=8192, timeout=90, max_transient=6,
                 daily_budget=3000, account_budget=1000,
                 lock_after_success=True):
        self._models = list(models) if models else list(MODEL_FALLBACKS)
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
        self._pool = KeyPool(account_daily_budget=account_budget)

    def _mark(self, key_obj: APIKey, status: str, error_msg: str):
        if self._on_key_status:
            try:
                self._on_key_status(key_obj, status, error_msg)
            except Exception as e:
                self._log(f"⚠ Không cập nhật được trạng thái key: {e}")

    def _touch(self, key_obj: APIKey):
        if key_obj.status == "exhausted":
            self._mark(key_obj, "active", "")
        else:
            try:
                key_obj.last_check_time = int(time.time())
                self._mark(key_obj, key_obj.status, "")
            except Exception:
                pass

    def _lock_account(self, key_obj: APIKey, duration: int = ACCOUNT_COOLDOWN, reason: str = ""):
        until = self._pool.lock_account(key_obj.email, duration)
        key_obj.cooldown_until = until
        self._mark(key_obj, key_obj.status, reason or "Account cooldown")
        return until

    def _maybe_lock_after_success(self, key_obj: APIKey):
        used = key_obj.email.lower()
        accounts = set()
        for k in self._pool._keys:
            if k.status in ("active", "exhausted"):
                accounts.add(k.email.lower())
        if len(accounts) < 2:
            return
        now = time.time()
        has_free = any(acct != used and not self._pool.is_account_locked(acct, now) for acct in accounts)
        if has_free:
            self._lock_account(key_obj, reason="Batch rotation lock")

    def _try_models(self, prompt_text: str, api_key: str, json_mode: bool, response_schema: Dict,
                    temperature: float, max_output_tokens: int, timeout: int):
        last = None
        for model in self._models:
            if self._stop_check():
                return {"kind": ErrorKind.STOPPED, "model": model}
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            config = {"maxOutputTokens": max_output_tokens, "temperature": temperature}
            if response_schema:
                config["responseMimeType"] = "application/json"
                config["responseSchema"] = response_schema
            elif json_mode:
                config["responseMimeType"] = "application/json"
            try:
                import requests
                resp = requests.post(url, headers={"Content-Type": "application/json"},
                                     json={"contents": [{"parts": [{"text": prompt_text}]}],
                                           "generationConfig": config},
                                     timeout=timeout)
                ctype = resp.headers.get("content-type", "")
                body = resp.json() if "application/json" in ctype else {}
                status_code = resp.status_code
            except requests.exceptions.Timeout:
                if model is not self._models[-1]:
                    self._log(f"⏱ Model '{model}' timeout > {timeout}s; chuyển fallback...")
                    last = {"kind": ErrorKind.NETWORK, "message": "timeout", "model": model}
                    continue
                return {"kind": ErrorKind.NETWORK, "message": "timeout", "model": model}
            except requests.exceptions.RequestException as exc:
                if model is not self._models[-1]:
                    self._log(f"🌐 Model '{model}' lỗi kết nối ({type(exc).__name__}); chuyển fallback...")
                    last = {"kind": ErrorKind.NETWORK, "message": f"{type(exc).__name__}: {exc}", "model": model}
                    continue
                return {"kind": ErrorKind.NETWORK, "message": f"{type(exc).__name__}: {exc}", "model": model}

            kind, msg = classify_response(status_code, body)
            if kind == ErrorKind.OK:
                text = extract_text(body)
                if text:
                    return {"kind": ErrorKind.OK, "text": text, "model": model, "message": msg}
                kind = ErrorKind.EMPTY
                msg = "phản hồi rỗng"
                if model is not self._models[-1]:
                    self._log(f"⚠ Model '{model}' phản hồi rỗng; chuyển fallback...")
                    last = {"kind": kind, "message": msg, "status_code": status_code, "model": model}
                    continue
                return {"kind": kind, "message": msg, "status_code": status_code, "model": model}
            if kind == ErrorKind.REQUEST_BAD:
                if model is not self._models[-1]:
                    self._log(f"⚠ Model '{model}' từ chối request; thử fallback.")
                    last = {"kind": kind, "message": msg, "status_code": status_code, "model": model}
                    continue
                return {"kind": kind, "message": msg, "status_code": status_code, "model": model}
            if kind in (ErrorKind.SERVER, ErrorKind.NETWORK, ErrorKind.EMPTY):
                if model is not self._models[-1]:
                    self._log(f"⚠ Model '{model}' lỗi {kind.value}; thử fallback.")
                    last = {"kind": kind, "message": msg, "status_code": status_code, "model": model}
                    continue
                return {"kind": kind, "message": msg, "status_code": status_code, "model": model}
            return {"kind": kind, "message": msg, "status_code": status_code, "model": model}
        return last or {"kind": ErrorKind.NETWORK, "message": "hết model fallback", "model": None}

    def request(self, prompt_text: str, json_mode: bool = False, response_schema: Dict = None,
                temperature: float = None, max_output_tokens: int = None, timeout: int = None):
        """Gửi 1 prompt với pacing + account rotation + error handling"""
        import requests
        exclude = set()
        transient = 0
        temp = temperature if temperature is not None else self._temperature
        mout = max_output_tokens or self._max_output_tokens
        tout = timeout or self._timeout
        account_attempts = 0

        while True:
            if self._stop_check():
                return {"ok": False, "text": "", "error": {"kind": ErrorKind.STOPPED.value}}

            # Sync pool từ key_loader
            self._pool.load_from_list(self._key_loader() or [])

            if self._pool.all_accounts_exhausted():
                stats = get_today_call_stats()
                tot = stats.get("total", 0)
                accts = stats.get("accounts", {})
                self._log(
                    f"🛑 TẤT CẢ {len(accts)} tài khoản Google (tổng {tot:,} calls) "
                    f"đã đạt ngân sách an toàn ({self._account_budget:,} calls/account). "
                    f"DỪNG AN TOÀN để bảo vệ tài khoản."
                )
                return {
                    "ok": False, "text": "",
                    "error": {"kind": ErrorKind.ALL_BUDGET_EXHAUSTED.value,
                              "message": f"Tất cả {len(accts)} accounts đã đạt ngân sách an toàn hôm nay."}
                }

            key_obj = self._pool.pick_key(exclude)
            if not key_obj:
                if self._pool.all_accounts_exhausted():
                    stats = get_today_call_stats()
                    tot = stats.get("total", 0)
                    accts = stats.get("accounts", {})
                    return {
                        "ok": False, "text": "",
                        "error": {"kind": ErrorKind.ALL_BUDGET_EXHAUSTED.value,
                                  "message": f"Tất cả {len(accts)} accounts đã đạt ngân sách an toàn hôm nay."}
                    }
                if account_attempts > 0:
                    self._log("⏳ Tạm thời chưa có key sẵn sàng. Chờ 15s...")
                    time.sleep(15)
                    exclude.clear()
                    account_attempts = 0
                    continue
                return {"ok": False, "text": "", "error": {"kind": ErrorKind.NO_KEY.value}}

            api_key = key_obj.get_raw_key()
            email = key_obj.email
            pace()
            res = self._try_models(prompt_text, api_key, json_mode, response_schema, temp, mout, tout)
            kind = res.get("kind")
            msg = res.get("message", "")

            if kind == ErrorKind.OK:
                total, acct_total = track_call(key_obj)
                self._touch(key_obj)
                if self._lock_after_success:
                    self._maybe_lock_after_success(key_obj)
                if acct_total >= self._account_budget:
                    self._log(f"ℹ Account '{email}' đạt {acct_total:,}/{self._account_budget:,} calls. Tạm ngưng.")
                if total > self._daily_budget:
                    self._log(f"⚠ Đã gọi {total:,} lần hôm nay (ngân sách tổng {self._daily_budget:,}/ngày).")
                return {"ok": True, "text": res["text"], "key": key_obj,
                        "model": res.get("model"), "total_calls": total, "acct_calls": acct_total}

            if kind == ErrorKind.QUOTA_DAILY:
                self._log(f"⚠ Key {email} hết quota ngày (Daily). Khóa account 60 phút...")
                self._lock_account(key_obj, duration=ACCOUNT_COOLDOWN, reason=f"HTTP 429 Daily: {msg[:90]}")
                self._mark(key_obj, "exhausted", f"HTTP 429 Daily: {msg[:90]}")
                key_obj.reset_time = int(time.time()) + 86400
                key_obj.next_check_time = int(time.time()) + 10800
                exclude.add(api_key)
                account_attempts += 1
                if account_attempts >= MAX_ACCOUNT_ATTEMPTS:
                    self._log(f"⚠ Đã thử {MAX_ACCOUNT_ATTEMPTS} account liên tiếp. Nghỉ 15s...")
                    time.sleep(15)
                    account_attempts = 0
                continue

            if kind == ErrorKind.QUOTA_RATE:
                retry_delay = retry_delay_from(msg)
                self._log(f"⚠ Key {email} chạm giới hạn RPM/TPM ({retry_delay}s). Cooldown {retry_delay}s...")
                self._lock_account(key_obj, duration=retry_delay, reason=f"HTTP 429 Rate: {msg[:90]}")
                exclude.add(api_key)
                account_attempts += 1
                if account_attempts >= MAX_ACCOUNT_ATTEMPTS:
                    self._log(f"⚠ Đã thử {MAX_ACCOUNT_ATTEMPTS} account gặp giới hạn tốc độ. Tạm dừng 15s...")
                    time.sleep(15)
                    account_attempts = 0
                continue

            if kind == ErrorKind.INVALID_KEY:
                self._mark(key_obj, "invalid", f"HTTP {res.get('status_code', '')}: {msg[:90]}")
                self._log(f"✗ Key {email} Invalid. Chuyển key...")
                exclude.add(api_key)
                continue

            if kind == ErrorKind.REQUEST_BAD:
                if is_model_restriction(msg):
                    self._log(f"⚠ Key {email} không được phép dùng model này. Khóa account...")
                    self._lock_account(key_obj, reason=f"Model restriction: {msg[:80]}")
                    exclude.add(api_key)
                    continue
                return {"ok": False, "text": "",
                        "error": {"kind": kind.value, "message": msg[:200], "status_code": res.get("status_code")}}

            if kind == ErrorKind.NETWORK:
                transient += 1
                if transient >= self._max_transient:
                    self._log(f"🌐 Mất kết nối mạng. Chế độ chờ hồi phục (kiểm tra mỗi 30s, tối đa 10 phút)...")
                    network_recovered = False
                    for wait_round in range(1, 21):
                        if self._stop_check():
                            return {"ok": False, "text": "", "error": {"kind": ErrorKind.STOPPED.value}}
                        time.sleep(30)
                        try:
                            chk = requests.get("https://www.google.com/generate_204", timeout=10)
                            if chk.status_code in (200, 204):
                                self._log(f"✅ Mạng đã hồi phục (sau {wait_round * 30}s). Tiếp tục...")
                                network_recovered = True
                                transient = 0
                                break
                        except Exception:
                            self._log(f"⏳ Vẫn chờ mạng ({wait_round * 30}s / 600s)...")
                    if not network_recovered:
                        return {"ok": False, "text": "", "error": {"kind": kind.value, "message": "Mất kết nối mạng quá 10 phút."}}
                    continue
                delay = min(2 ** transient, 30)
                self._log(f"🌐 Lỗi mạng: {msg[:70]}. Chờ {delay}s (lần {transient}/{self._max_transient})...")
                time.sleep(delay)
                continue

            if kind in (ErrorKind.SERVER, ErrorKind.EMPTY):
                transient += 1
                if transient >= self._max_transient:
                    return {"ok": False, "text": "", "error": {"kind": kind.value, "message": msg[:200]}}
                delay = min(2 ** transient, 30)
                self._log(f"⚠ Máy chủ bận/rỗng: {msg[:70]}. Chờ {delay}s (lần {transient}/{self._max_transient})...")
                time.sleep(delay)
                continue

            return {"ok": False, "text": "", "error": {"kind": kind.value, "message": msg[:200]}}


# Provider-specific coordinators
class OpenRouterCoordinator:
    """Coordinator cho OpenRouter (free models)"""
    def __init__(self, api_key: str, log_fn=None, stop_check=None):
        self._api_key = api_key
        self._log = log_fn or (lambda m: None)
        self._stop_check = stop_check or (lambda: False)
        self._free_models = [
            "google/gemma-4-26b-a4b-it:free",
            "google/gemma-4-31b-it:free",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
            "openai/gpt-oss-20b:free",
            "openai/gpt-oss-120b:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "mistralai/mistral-7b-instruct:free"
        ]

    def request(self, prompt: str, model: str = None, temperature=0.7, max_tokens=4096):
        import requests
        model = model or self._free_models[0]
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://opencode.ai",
            "X-Title": "OpenCode Config Manager"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=60)
            if resp.status_code == 200:
                result = resp.json()
                text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"ok": True, "text": text, "model": model}
            elif resp.status_code == 429:
                return {"ok": False, "error": {"kind": "quota", "message": "Rate limited"}}
            else:
                return {"ok": False, "error": {"kind": "error", "message": resp.text[:200]}}
        except Exception as e:
            return {"ok": False, "error": {"kind": "network", "message": str(e)}}


class DeepSeekCoordinator:
    """Coordinator cho DeepSeek API"""
    def __init__(self, api_key: str, log_fn=None, stop_check=None):
        self._api_key = api_key
        self._log = log_fn or (lambda m: None)
        self._stop_check = stop_check or (lambda: False)
        self._models = ["deepseek-chat", "deepseek-reasoner"]

    def request(self, prompt: str, model: str = None, temperature=0.7, max_tokens=4096):
        import requests
        model = model or self._models[0]
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=60)
            if resp.status_code == 200:
                result = resp.json()
                text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"ok": True, "text": text, "model": model}
            elif resp.status_code == 429:
                return {"ok": False, "error": {"kind": "quota", "message": "Rate limited"}}
            else:
                return {"ok": False, "error": {"kind": "error", "message": resp.text[:200]}}
        except Exception as e:
            return {"ok": False, "error": {"kind": "network", "message": str(e)}}


class GroqCoordinator:
    """Coordinator cho Groq (free, fast)"""
    def __init__(self, api_key: str, log_fn=None, stop_check=None):
        self._api_key = api_key
        self._log = log_fn or (lambda m: None)
        self._stop_check = stop_check or (lambda: False)
        self._free_models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "qwen-2.5-32b",
            "gemma-7b-it",
            "mixtral-8x7b-32768"
        ]

    def request(self, prompt: str, model: str = None, temperature=0.7, max_tokens=4096):
        import requests
        model = model or self._free_models[0]
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=60)
            if resp.status_code == 200:
                result = resp.json()
                text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"ok": True, "text": text, "model": model}
            elif resp.status_code == 429:
                return {"ok": False, "error": {"kind": "quota", "message": "Rate limited"}}
            else:
                return {"ok": False, "error": {"kind": "error", "message": resp.text[:200]}}
        except Exception as e:
            return {"ok": False, "error": {"kind": "network", "message": str(e)}}