import base64
import json
import os
import random
import re
import threading
import time

import requests

from ai.pipeline_store import (load_dead_models, mark_dead_model,
                               is_dead_model, reset_dead_model,
                               get_available_models, DEAD_MODEL_COOLDOWN_MINUTES,
                               MAX_FAILURES_BEFORE_DEAD)

# ─────────────────────────────────────────────────────────────
# Blocklist account bị từ chối vĩnh viễn (403 denied access)
# Lưu bền trên đĩa để các lần chạy sau bỏ qua ngay, không tốn call.
# ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCKED_ACCOUNTS_PATH = os.path.join(BASE_DIR, "data", "blocked_accounts.json")
BLOCKED_KEYS_PATH = os.path.join(BASE_DIR, "data", "blocked_keys.json")
_blocked_lock = threading.Lock()


def _load_blocked(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save_blocked(path: str, data: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def load_blocked_accounts() -> dict:
    return _load_blocked(BLOCKED_ACCOUNTS_PATH)


def block_account(account: str, reason: str = "") -> bool:
    """Ghi account vào blocklist bền. Trả True nếu mới thêm."""
    if not account:
        return False
    with _blocked_lock:
        data = load_blocked_accounts()
        if account in data:
            return False
        data[account] = {"reason": reason[:200], "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        if not _save_blocked(BLOCKED_ACCOUNTS_PATH, data):
            return False
    return True


def unblock_account(account: str) -> bool:
    with _blocked_lock:
        data = load_blocked_accounts()
        if account not in data:
            return False
        data.pop(account, None)
        if not _save_blocked(BLOCKED_ACCOUNTS_PATH, data):
            return False
    return True


def load_blocked_keys() -> dict:
    return _load_blocked(BLOCKED_KEYS_PATH)


def _blocked_entry_active(entry) -> bool:
    """Entry blocklist còn hiệu lực? Không có `until` = vĩnh viễn (key chết)."""
    try:
        until = int((entry or {}).get("until") or 0)
    except Exception:
        until = 0
    return until <= 0 or until > time.time()


def block_key(api_key: str, reason: str = "", ttl: int = None) -> bool:
    """Ghi key vào blocklist bền (theo hash, không lưu key gốc).

    ttl=None  → vĩnh viễn (key invalid/chết thật).
    ttl=giây  → tạm nghỉ, hết hạn sẽ tự thử lại. Dùng cho 403 free-tier:
                key vẫn còn sống, chỉ project chưa bật billing.
    """
    if not api_key:
        return False
    import hashlib
    khash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
    with _blocked_lock:
        data = load_blocked_keys()
        if khash in data and _blocked_entry_active(data[khash]):
            return False
        entry = {"reason": reason[:200], "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        if ttl:
            entry["until"] = int(time.time() + ttl)
        data[khash] = entry
        if not _save_blocked(BLOCKED_KEYS_PATH, data):
            return False
    return True


def is_blocked_key(api_key: str) -> bool:
    if not api_key:
        return False
    import hashlib
    khash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
    entry = load_blocked_keys().get(khash)
    return bool(entry) and _blocked_entry_active(entry)

# ─────────────────────────────────────────────────────────────
# Cấu hình an toàn chuẩn (skill: gemini_api_key_handling)
# ─────────────────────────────────────────────────────────────
PACE_MIN = 3.5
PACE_MAX = 5.0
PACE_JITTER = (0.5, 1.5)          # jitter phá tần số bot
ACCOUNT_COOLDOWN = 3600           # 60 phút nghỉ cho 1 account sau batch/429
# 403 "free tier is not available" là lỗi cấp PROJECT: key còn sống, chỉ project
# chưa đủ điều kiện free tier. Bật billing là key cũ dùng lại được ⇒ tạm nghỉ
# 24h rồi tự thử lại, KHÔNG block vĩnh viễn.
FREE_TIER_RETRY_SECONDS = 24 * 3600
MAX_KEYS_PER_ACCOUNT = 2          # khuyến nghị 1-2 key/account
DAILY_CALL_BUDGET = 3000          # ngân sách call/ngày, vượt thì cảnh báo
MODEL_FALLBACKS = [
    "gemini-3.5-flash",        # 🥇 Tốt nhất — thế hệ mới nhất
    "gemini-3-flash-preview",  # 🥈 Rất tốt
    "gemini-flash-latest",     # 🥉 Tốt, stable
    "gemini-3.1-flash-lite",   # 🔵 Lite, dự phòng
    "gemini-flash-lite-latest" # 🔵 Lite, dự phòng cuối
]

# Model SINH ẢNH (Gemini native image) — dùng responseModalities=["TEXT","IMAGE"]
IMAGE_MODEL_FALLBACKS = [
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
    "gemini-nano-banana-2.1",
]

# ─────────────────────────────────────────────────────────────
# Global Rate Limiter — mọi call Gemini đều đi qua pace()
# ─────────────────────────────────────────────────────────────
_pace_lock = threading.Lock()
_last_call_ts = 0.0


def pace(interval: float = None):
    """Nghỉ giữa 2 lần gọi Gemini (thread-safe, khoá toàn tiến trình).

    Mặc định: khoảng nghỉ THÍCH ỨNG theo số **PROJECT** (account) khả dụng.

    ⚠️ QUOTA RPM CỦA GEMINI FREE TIER LÀ **15/PHÚT MỖI PROJECT**, không phải
    mỗi key. Đo thật: 9-10 key/account nhưng 1 project/account ⇒ 5 account
    chỉ chịu được 5 × 15 = 75 call/phút TỔNG.
    Tính theo số KEY (47) ⇒ 94 call/phút ⇒ 429 ⇒ mọi key bị cooldown ⇒
    vòng lặp chờ 6 × 20 s ⇒ treo pipeline.
    """
    global _last_call_ts
    if interval is None:
        try:
            n = max(1, _get_pool().usable_project_count())
        except Exception:
            n = 5
        # 60 / (n_project × 11) giây ⇒ ~11 call/phút/project (dưới 15 RPM)
        interval = min(5.0, max(0.8, 60.0 / (n * 11.0)))
    with _pace_lock:
        base = random.uniform(0.6, 1.0) * interval
        jitter = random.uniform(*PACE_JITTER) * 0.2
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
        # Gemini free tier báo hạn mứn NGÀY theo message:
        #   "Quota exceeded for metric: ..._free_tier_requests, limit: 20, model: X
        #    Please retry in 13h33m50s."
        # Message KHÔNG chứa chữ "perday" ⇒ nếu không nhận diện, sẽ bị coi là
        # rate-limit tạm thời ⇒ retry vô ích 12 lần × 65 s ⇒ TREO pipeline.
        if "please retry in" in low:
            m = re.search(r"please retry in\s*(\d+(?:\.\d+)?)\s*h", low)
            if m and float(m.group(1)) >= 0.25:
                return ErrorKind.QUOTA_DAILY, message
        if "limit: 0" in low:
            return ErrorKind.QUOTA_DAILY, message
        return ErrorKind.QUOTA_RATE, message
    if status_code in (401, 403):
        if ("api_key_invalid" in low or "invalid authentication" in low
                or "invalid key" in low or "api key not valid" in low
                or "api key not found" in low or "access_token_type_unsupported" in low
                or is_dead_key_message(low)):
            return ErrorKind.INVALID_KEY, message
        return ErrorKind.REQUEST_BAD, message
    if status_code == 400:
        if "api_key_invalid" in low or is_dead_key_message(low):
            return ErrorKind.INVALID_KEY, message
        return ErrorKind.REQUEST_BAD, message
    if status_code >= 500:
        return ErrorKind.SERVER, message
    return ErrorKind.REQUEST_BAD, message


# Message của API key chết vĩnh viễn (service account bị xoá/vô hiệu).
# Đo trên máy: "The bound service account is deleted or disabled. The service
# account bound to the API key must be active." (HTTP 400).
# Nếu không phân loại đúng, 1 key chết sẽ ABORT cả request dù còn 47 key tốt.
_DEAD_KEY_MARKERS = (
    "bound service account is deleted",
    "service account bound to the api key",
    "service account is deleted or disabled",
    "api key has been deleted",
    "key is invalid or has been deleted",
)


def is_dead_key_message(low: str) -> bool:
    return any(m in (low or "") for m in _DEAD_KEY_MARKERS)


# Từ chối ở CẤP ACCOUNT (không phải cấp model) — không đáng thử model khác,
# phải khoá account và xoay key ngay.
_ACCOUNT_DENIAL_MARKERS = (
    "has been denied access",
    "your project has been denied access",
    "permission denied",
    "does not have access to",
)


def is_account_denial(msg: str) -> bool:
    low = (msg or "").lower()
    return any(m in low for m in _ACCOUNT_DENIAL_MARKERS)


def retry_delay_from(msg):
    """Parse retryDelay (vd: 'retryDelay: 4s') từ message lỗi 429."""
    m = re.search(r'retryDelay["' + chr(92) + r's:]+"?(\d+)s?"?', msg, re.IGNORECASE)
    if m:
        return int(m.group(1)) + 5
    return 65


def is_project_billing_error(msg) -> bool:
    """403 'free tier is not available' → cả PROJECT không dùng được model nào.

    Google docs (troubleshooting#project-unavailable): eligibility được xét ở
    cấp Google Cloud project; tạo key mới trong cùng project KHÔNG sửa được.
    Nhưng key không chết: bật billing cho project là key cũ dùng lại được.
    """
    return "free tier is not available" in (msg or "").lower()


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


def extract_image(body):
    """Trả (b64, mime) từ phần tử ảnh đầu tiên trong response Gemini.

    Xử lý CẢ 2 casing của key (inlineData / inline_data, mimeType / mime_type)
    — theo mẫu AskCpl/gemini_image_pipeline.py:39-44.
    """
    try:
        candidates = body.get("candidates", []) if isinstance(body, dict) else []
        if not candidates:
            return "", ""
        parts = (candidates[0].get("content", {}) or {}).get("parts", []) or []
        for part in parts:
            if not isinstance(part, dict):
                continue
            inline = part.get("inlineData") or part.get("inline_data") or {}
            if not isinstance(inline, dict):
                continue
            data = inline.get("data")
            if not data:
                continue
            mime = inline.get("mimeType") or inline.get("mime_type") or "image/png"
            return str(data), str(mime)
    except Exception:
        pass
    return "", ""


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

    def lock_key(self, key_obj, duration=60):
        """Khoá RIÊNG 1 key (giới hạn RPM/TPM là theo project = theo key).

        Khoá cả account (lock_account) là quá nặng: 1 key chạm RPM sẽ chặn
        luôn 9-10 key khác của account đó ⇒ 5 luồng song song hết key.
        """
        if not key_obj:
            return 0
        until = int(time.time() + duration)
        with self._lock:
            key_obj["cooldown_until"] = until
        return until

    def usable_count(self) -> int:
        """Số key hiện dùng được (không tính key đang cooldown/exhausted)."""
        try:
            return len(self._usable_keys(set()))
        except Exception:
            return 1

    def usable_project_count(self) -> int:
        """Số PROJECT (account) hiện dùng được.

        QUOTA RPM của Gemini free tier là **15/phút mỗi PROJECT** ⇒ phải tính
        theo số account, không theo số key (1 account có 9-10 key nhưng chỉ
        1 project ⇒ cộng dồn về 1 hạn mức 15 RPM).
        """
        try:
            accts = set()
            for k in self._usable_keys(set()):
                accts.add(self.account_of(k))
            return max(1, len(accts))
        except Exception:
            return 5

    def _usable_keys(self, exclude):
        now = time.time()
        blocked = load_blocked_accounts()
        blocked_keys = load_blocked_keys()
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
            import hashlib
            khash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
            entry = blocked_keys.get(khash)
            if entry and _blocked_entry_active(entry):
                continue
            acct = self.account_of(k)
            if acct in blocked:
                continue
            cd_until = max(self._cooldown.get(acct, 0), k.get("cooldown_until", 0))
            if cd_until > now:
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
                 max_output_tokens=8192, timeout=90, max_transient=3,
                 daily_budget=DAILY_CALL_BUDGET, lock_after_success=False,
                 image_models=None):
        # Danh sách model fallback — ưu tiên đọc từ settings.json (người dùng tùy chỉnh)
        if models:
            self._models = list(models)
        else:
            try:
                from settings import get_active_model_list
                _from_settings = get_active_model_list()
                self._models = _from_settings if _from_settings else list(MODEL_FALLBACKS)
            except Exception:
                self._models = list(MODEL_FALLBACKS)
        # Danh sách model SINH ẢNH (Gemini native image) — đọc từ settings ai.image_models
        if image_models:
            self._image_models = list(image_models)
        else:
            try:
                from settings import load_settings
                _img = (load_settings().get("ai", {}) or {}).get("image_models") or []
                self._image_models = list(_img) if _img else list(IMAGE_MODEL_FALLBACKS)
            except Exception:
                self._image_models = list(IMAGE_MODEL_FALLBACKS)
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
        self._last_email_used = None   # email key vừa dùng — log khi ĐỔI account
        # ── Model performance tracking (probe + adaptive rotation) ──
        self._model_stats = {}   # model -> {ok, fail, total_ms, count, consec_fail, last_ok_ts}
        self._model_cooldown = {}  # model -> ts hết cooldown (tránh gọi lại model vừa timeout/503)
        self._probe_done = set() # models đã từng được probe-tested
        self._probe_counter = 0  # đếm lượt gọi để định kỳ chọc model khác
        try:
            from settings import load_settings
            _ad = (load_settings().get("ai", {}) or {}).get("adaptive_model", True)
            self._adaptive = bool(_ad)
        except Exception:
            self._adaptive = True
        self._stats_pending = 0  # đếm để định kỳ lưu stats vào settings (không ghi mỗi call)
        # Seed stats từ settings (kết quả probe của các lần chạy trước) nếu có
        try:
            from settings import load_settings
            _ps = (load_settings().get("ai", {}) or {}).get("model_probe_stats") or {}
            for m, st in _ps.items():
                self._model_stats[str(m)] = {
                    "ok": int(st.get("ok", 0)),
                    "fail": int(st.get("fail", 0)),
                    "total_ms": int(st.get("total_ms", 0)),
                    "count": int(st.get("count", 0)),
                    "consec_fail": int(st.get("consec_fail", 0)),
                    "last_ok_ts": float(st.get("last_ok_ts", 0)),
                }
                if self._model_stats[str(m)]["count"] > 0:
                    self._probe_done.add(str(m))
        except Exception:
            pass
        # Dead model tracking: {model_name: {"fail_count": n, "until": ts}}
        self._dead_fail_count = {}
        self._dead_lock = threading.Lock()
        # Nạp dead models từ persistent storage (per-language __global__)
        try:
            from ai.pipeline_store import load_dead_models as _ldm
            _saved = _ldm("__global__") or {}
            now = time.time()
            for model, info in _saved.items():
                if not isinstance(info, dict):
                    continue
                until = info.get("until", 0)
                if until > now:
                    self._dead_fail_count[model] = info
        except Exception:
            pass
        try:
            warn_account_health(self._key_loader(), self._log)
        except Exception:
            pass

    @property
    def models(self):
        """Danh sách model fallback đang được điều phối."""
        return list(self._models)

    @property
    def image_models(self):
        """Danh sách model SINH ẢNH đang được điều phối."""
        return list(self._image_models)

    # ── Dead model tracking ──
    def _is_model_dead(self, model: str) -> bool:
        """Kiểm tra model hiện đang bị khóa cooldown (30 phút sau 3 lần lỗi)."""
        with self._dead_lock:
            entry = self._dead_fail_count.get(model)
            if not entry:
                return False
            until = entry.get("until", 0)
            if until <= time.time():
                # Hết hạn cooldown ⇒ xóa khỏi tracking
                del self._dead_fail_count[model]
                return False
            return True

    def _mark_model_dead(self, model: str, reason: str = "") -> None:
        """Đánh dấu model lỗi. Sau MAX_FAILURES_BEFORE_DEAD lần ⇒ khóa 30 phút."""
        with self._dead_lock:
            entry = self._dead_fail_count.get(model, {"fail_count": 0, "until": 0})
            entry["fail_count"] = int(entry.get("fail_count", 0)) + 1
            entry["reason"] = reason[:200]
            entry["last_fail_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

            if entry["fail_count"] >= MAX_FAILURES_BEFORE_DEAD:
                entry["until"] = time.time() + DEAD_MODEL_COOLDOWN_MINUTES * 60
                entry["status"] = "dead"
                self._log(f"⛔ Model '{model}' bị khóa {DEAD_MODEL_COOLDOWN_MINUTES} phút "
                          f"(sau {entry['fail_count']} lần lỗi): {reason[:80]}")
            else:
                entry["status"] = "warning"
                self._log(f"⚠ Model '{model}' lỗi lần {entry['fail_count']}/{MAX_FAILURES_BEFORE_DEAD}: {reason[:80]}")

            self._dead_fail_count[model] = entry

        # Đồng bộ xuống persistent storage (per-language)
        try:
            from ai.pipeline_store import (load_dead_models as _ldm,
                                           save_dead_models as _sdm,
                                           mark_dead_model as _mdm)
            # Sử dụng slug 'default' cho dead model chung cho tất cả ngôn ngữ
            _mdm("__global__", model, reason)
        except Exception:
            pass

    def _reset_model_dead(self, model: str) -> None:
        """Mở khóa model (dùng cho nút Reset trong GUI)."""
        with self._dead_lock:
            self._dead_fail_count.pop(model, None)

        # Đồng bộ xuống persistent storage
        try:
            from ai.pipeline_store import (load_dead_models as _ldm,
                                           save_dead_models as _sdm,
                                           reset_dead_model as _rdm)
            _rdm("__global__", model)
        except Exception:
            pass

    def _get_available_models(self) -> list:
        """Lọc ra các model chưa bị khóa cooldown."""
        with self._dead_lock:
            now = time.time()
            available = []
            for m in self._models:
                entry = self._dead_fail_count.get(m)
                if not entry:
                    available.append(m)
                    continue
                until = entry.get("until", 0)
                if until <= now:
                    # Hết hạn cooldown ⇒ xóa và cho phép thử lại
                    del self._dead_fail_count[m]
                    available.append(m)
            return available

    def get_dead_models_info(self) -> dict:
        """Trả thông tin dead models để GUI hiển thị."""
        with self._dead_lock:
            now = time.time()
            result = {}
            for m in self._models:
                entry = self._dead_fail_count.get(m)
                if not entry:
                    result[m] = {"status": "active", "fail_count": 0, "until": 0,
                                 "wait_seconds": 0}
                    continue
                until = entry.get("until", 0)
                if until <= now:
                    result[m] = {"status": "active", "fail_count": 0, "until": 0,
                                 "wait_seconds": 0}
                    continue
                wait_seconds = int(until - now)
                result[m] = {
                    "status": entry.get("status", "warning"),
                    "fail_count": entry.get("fail_count", 0),
                    "until": until,
                    "wait_seconds": wait_seconds,
                    "reason": entry.get("reason", ""),
                    "last_fail_at": entry.get("last_fail_at", ""),
                }
            return result

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

    # ── Model performance tracking ──
    def _model_score(self, model: str) -> float:
        """Điểm ưu tiên model: thành công cao + latency thấp + ít fail liên tiếp.
        Chưa probe → điểm 0 (trung lập, sẽ được chọc thử sau)."""
        s = self._model_stats.get(model)
        if not s or s["count"] == 0:
            return 0.0
        # Model chưa từng thành công ⇒ xếp cuối, tránh việc timeout nhanh
        # (avg_ms thấp) lại được điểm cao hơn model chậm nhưng chạy được.
        if s["ok"] == 0:
            return -100000.0 - (s["consec_fail"] * 1000.0)
        rate = s["ok"] / max(1, s["count"])
        avg_ms = s["total_ms"] / max(1, s["ok"])
        # Chặn trần phạt latency: model chậm 30-60s vẫn hơn model fail 100%.
        latency_penalty = min(avg_ms / 10.0, 500.0)
        return rate * 1000.0 - latency_penalty - (s["consec_fail"] * 100.0)

    def _record_model_result(self, model: str, ok: bool, ms=None):
        """Ghi nhận kết quả 1 lần gọi model (dùng cho thống kê + adaptive order)."""
        s = self._model_stats.setdefault(
            model, {"ok": 0, "fail": 0, "total_ms": 0, "count": 0, "consec_fail": 0, "last_ok_ts": 0.0})
        s["count"] += 1
        if ok:
            s["ok"] += 1
            s["consec_fail"] = 0
            s["last_ok_ts"] = time.time()
            self._model_cooldown.pop(model, None)
            if ms is not None:
                s["total_ms"] += ms
        else:
            s["fail"] += 1
            s["consec_fail"] += 1
        self._probe_done.add(model)
        # Định kỳ lưu stats vào settings.json (mỗi 10 lần) để giữ nguyên qua các lần chạy
        self._stats_pending += 1
        if self._stats_pending >= 10:
            self._stats_pending = 0
            self.save_probe_stats_to_settings()

    def _cooldown_model(self, model: str, seconds: int):
        """Tạm bỏ qua model vừa timeout/503 để request sau không chờ lại từ đầu."""
        if not model:
            return
        self._model_cooldown[model] = time.time() + max(30, int(seconds))

    def report_invalid_output(self, model: str, reason: str = "", seconds: int = 180):
        """Model trả JSON hợp lệ nhưng thiếu field bắt buộc (vd vocab rỗng).

        Không coi là thành công: ghi fail + cooldown để lần retry chuyển model
        khác thay vì lặp lại đúng model vừa trả output rỗng.
        """
        if not model:
            return
        self._record_model_result(model, ok=False)
        self._cooldown_model(model, seconds)
        self._log(f"⚠ Model '{model}' trả output không hợp lệ "
                  f"({str(reason)[:90]}) — tạm bỏ qua {seconds}s.")

    def get_model_ranking(self) -> list:
        """Trả danh sách model sắp xếp theo điểm (tốt nhất đầu) — dùng GUI hiển thị."""
        return sorted(self._models, key=self._model_score, reverse=True)

    def _adaptive_model_order(self) -> list:
        """
        Thứ tự gọi model cho lần này:
        - Exploitation: sắp theo điểm (model tốt nhất trước).
        - Exploration: mỗi PROBE_EVERY lượt gọi, chèn 1 model chưa probe / ít probe
          vào vị trí cao (sau model tốt nhất) để không giẫm chân mãi ở 1 chỗ,
          vẫn cho model còn lại cơ hội chứng minh mình tốt hơn.
        """
        PROBE_EVERY = 6
        self._probe_counter += 1
        now = time.time()
        alive = [m for m in self._models if self._model_cooldown.get(m, 0) <= now]
        if not alive:
            # Tất cả đang cooldown: chọn model hết cooldown sớm nhất để không kẹt.
            alive = [min(self._models, key=lambda m: self._model_cooldown.get(m, 0))]
        unprobed = [m for m in alive if m not in self._probe_done]
        low_tested = [m for m in alive
                      if self._model_stats.get(m, {}).get("count", 0) < 3 and m not in unprobed]
        exploration_pool = unprobed or low_tested or []

        ordered = sorted(alive, key=self._model_score, reverse=True)

        if self._adaptive and self._probe_counter % PROBE_EVERY == 0 and exploration_pool:
            challenger = exploration_pool[0]
            if challenger in ordered:
                ordered.remove(challenger)
                pos = min(2, len(ordered))          # sau model tốt nhất (index 0)
                ordered.insert(pos, challenger)
                self._log(f"🔍 Thử(model-thử): '{challenger}' (khám phá model thay thế)")
        return ordered

    def save_probe_stats_to_settings(self):
        """Lưu _model_stats vào settings.json (ai.model_probe_stats) để giữ nguyên qua các lần chạy."""
        try:
            from settings import load_settings, update_ai_settings
            st = {}
            for m, s in self._model_stats.items():
                if s["count"] > 0:
                    st[m] = {
                        "ok": s["ok"], "fail": s["fail"], "total_ms": s["total_ms"],
                        "count": s["count"], "consec_fail": s["consec_fail"],
                        "last_ok_ts": s["last_ok_ts"],
                    }
            if st:
                update_ai_settings(model_probe_stats=st)
        except Exception:
            pass

    def _lock_account(self, key_obj, duration=ACCOUNT_COOLDOWN, reason=""):
        """Khóa toàn bộ account (mọi key cùng Gmail) trong `duration` giây."""
        until = self._pool.lock_account(key_obj=key_obj, duration=duration)
        if key_obj:
            key_obj["cooldown_until"] = until
            self._mark(key_obj, key_obj.get("status", "active"), reason or "Account cooldown")
        return until

    def _maybe_lock_after_success(self, key_obj, keys):
        """Sau 1 batch thành công: chỉ khóa khi lock_after_success được bật chủ động."""
        if not self._lock_after_success:
            return
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

    def get_all_keys_status(self) -> list:
        """Trả về danh sách trạng thái tất cả key để GUI hiển thị (email, key masked, status, cooldown...)."""
        now = time.time()
        out = []
        try:
            pool = self._pool
            # Nạp key từ settings trước khi đọc trạng thái (nếu không pool sẽ rỗng).
            pool.sync(self._key_loader() or [])
            for k in pool._keys:
                email = k.get("email", "unknown")
                raw = k.get("key", "")
                # Mask key: chỉ hiển thị 4 ký tự cuối
                masked = ("*" * max(0, len(raw) - 4)) + raw[-4:] if raw else ""
                status = k.get("status", "active")
                cd = max(pool._cooldown.get(email, 0), k.get("cooldown_until", 0))
                locked = cd > now
                out.append({
                    "email": email,
                    "key_masked": masked,
                    "status": status,
                    "cooldown_until": cd,
                    "locked": locked,
                    "next_check": k.get("next_check_time", 0),
                })
        except Exception:
            pass
        return out

    def _log_key_pick(self, pool, key_obj, email):
        """Hiển thị key/account ĐANG DÙNG trong log sinh khóa.

        Mục đích: người theo dõi bằng MẮT thấy rõ việc xoay vòng account
        (không để 1 account bị dùng liên tục gây vi phạm quota).
        Chỉ hiện khi ĐỔI account — không spam mỗi request.
        """
        try:
            keys = getattr(pool, "_keys", []) or []
            idx = next((i for i, k in enumerate(keys) if k is key_obj), -1)
            tag = f" [key {idx + 1}/{len(keys)}]" if idx >= 0 else ""
            if email != self._last_email_used:
                arrow = "🔑 Đang dùng key của account: " if self._last_email_used is None \
                        else "🔄 Đổi sang account: "
                self._last_email_used = email
                self._log(f"{arrow}{email}{tag}")
        except Exception:
            pass

    def _try_models(self, prompt_text, api_key, json_mode, response_schema,
                    temperature, max_output_tokens, timeout, ordered_models=None,
                    email=None, deadline=None):
        last = None
        billing_hits = 0
        # Thứ tự model: adaptive (nếu có) — lọc bỏ model đang dead cooldown
        base = ordered_models if ordered_models is not None else self._models
        available_models = [m for m in base if m in self._get_available_models()]
        if not available_models:
            available_models = list(base)
        models = available_models
        n_models = len(models)
        acct = email or "?"
        for mi, model in enumerate(models):
            if self._stop_check():
                return {"kind": ErrorKind.STOPPED, "model": model}
            if deadline is not None and time.time() > deadline:
                return {"kind": ErrorKind.NETWORK,
                        "message": "request deadline exceeded", "model": model}
            # Log fallback rõ ràng: "⚠ '3.6-flash' fail (429) → thử '3.8-flash' [gmail]"
            _nxt = models[mi + 1] if mi + 1 < n_models else None
            _arw = f" → thử '{_nxt}'" if _nxt else ""
            _acct_tag = f" [{acct}]" if acct and acct != "?" else ""
            url = (f"https://generativelanguage.googleapis.com/v1beta/"
                   f"models/{model}:generateContent?key={api_key}")
            config = {"maxOutputTokens": max_output_tokens, "temperature": temperature}
            if response_schema:
                config["responseMimeType"] = "application/json"
                config["responseSchema"] = response_schema
            elif json_mode:
                config["responseMimeType"] = "application/json"
            t0 = time.time()
            try:
                resp = requests.post(url, headers={"Content-Type": "application/json"},
                                     json={"contents": [{"parts": [{"text": prompt_text}]}],
                                           "generationConfig": config},
                                     timeout=timeout)
                ctype = resp.headers.get("content-type", "")
                body = resp.json() if "application/json" in ctype else {}
                status_code = resp.status_code
                ms = int((time.time() - t0) * 1000)
            except requests.exceptions.Timeout:
                ms = None
                self._record_model_result(model, False, None)
                self._cooldown_model(model, 300)
                self._mark_model_dead(model, "timeout")
                if _nxt:
                    self._log(f"⏱ '{model}' fail (timeout >{timeout}s){_arw}{_acct_tag}")
                    last = {"kind": ErrorKind.NETWORK, "message": "timeout", "model": model}
                    continue
                return {"kind": ErrorKind.NETWORK, "message": "timeout", "model": model}
            except requests.exceptions.RequestException as exc:
                ms = None
                self._record_model_result(model, False, None)
                self._cooldown_model(model, 120)
                self._mark_model_dead(model, f"{type(exc).__name__}: {exc}")
                if _nxt:
                    self._log(f"🌐 '{model}' fail ({type(exc).__name__}){_arw}{_acct_tag}")
                    last = {"kind": ErrorKind.NETWORK, "message": f"{type(exc).__name__}: {exc}", "model": model}
                    continue
                return {"kind": ErrorKind.NETWORK,
                        "message": f"{type(exc).__name__}: {exc}", "model": model}

            kind, msg = classify_response(status_code, body)
            text = extract_text(body) if kind == ErrorKind.OK else None
            ok = (kind == ErrorKind.OK) and bool(text)
            self._record_model_result(model, ok, ms)
            if kind == ErrorKind.REQUEST_BAD and is_project_billing_error(msg):
                # 403 free-tier có thể là cấp PROJECT hoặc chỉ model này. Thử
                # tối đa 1 model kế để xác nhận; nếu model kế chạy được thì
                # KHÔNG tạm nghỉ key (tránh khóa oan vì model cũ).
                billing_hits += 1
                if billing_hits < 2 and _nxt:
                    self._log(f"⚠ '{model}' báo free-tier — thử '{_nxt}' "
                              f"để xác nhận cấp project…{_acct_tag}")
                    last = {"kind": kind, "message": msg,
                            "status_code": status_code, "model": model,
                            "billing": True}
                    continue
                return {"kind": kind, "message": msg,
                        "status_code": status_code, "model": model,
                        "billing": True, "confirmed": True}
            if kind == ErrorKind.OK:
                # Reset fail_count dead-model khi gọi thành công
                with self._dead_lock:
                    self._dead_fail_count.pop(model, None)
                if text:
                    return {"kind": ErrorKind.OK, "text": text,
                            "model": model, "message": msg}
                kind = ErrorKind.EMPTY
                msg = "phản hồi rỗng"
                return {"kind": kind, "message": msg, "status_code": status_code, "model": model}
            if kind == ErrorKind.QUOTA_DAILY:
                # Mỗi model là 1 quota bucket riêng (20 call/ngày/project/model)
                # → hết quota model này thì THỬ MODEL KHÁC trước khi đổi key.
                if _nxt:
                    self._log(f"⏳ '{model}' fail (429 quota ngày){_arw}{_acct_tag}")
                    last = {"kind": kind, "message": msg, "status_code": status_code,
                            "model": model}
                    continue
                return {"kind": kind, "message": msg, "status_code": status_code,
                        "model": model}

            if kind == ErrorKind.REQUEST_BAD:
                if is_account_denial(msg):
                    # Lỗi cấp ACCOUNT → trả về ngay để request() khoá account + xoay key.
                    return {"kind": kind, "message": msg, "status_code": status_code, "model": model}
                if _nxt:
                    self._log(f"⚠ '{model}' fail ({status_code} — {msg[:60]}){_arw}{_acct_tag}")
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
                # 503 high-demand / timeout: tạm bỏ qua model này ở các request sau.
                self._cooldown_model(model, 180 if status_code == 503 else 90)
                self._mark_model_dead(model, f"{kind}: {msg[:100]}")
                if _nxt:
                    self._log(f"⚠ '{model}' fail ({status_code} — {msg[:60]}){_arw}{_acct_tag}")
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
        transient_accounts = 0
        temp = temperature if temperature is not None else self._temperature
        mout = max_output_tokens or self._max_output_tokens
        tout = timeout or self._timeout
        account_attempts = 0
        retry_exhausted_rounds = 0
        MAX_ACCOUNT_ATTEMPTS = 3  # Giới hạn thử tối đa 3 account khác nhau/lượt gọi để tránh đốt sạch pool
        started = time.time()
        MAX_REQUEST_SECONDS = 300  # 1 request không được phép treo quá 5 phút

        while True:
            if self._stop_check():
                return {"ok": False, "text": "", "error": {"kind": ErrorKind.STOPPED}}
            if time.time() - started > MAX_REQUEST_SECONDS:
                self._log(f"⏱ Request vượt {MAX_REQUEST_SECONDS}s — dừng thử để tránh treo pipeline.")
                return {"ok": False, "text": "",
                        "error": {"kind": ErrorKind.NETWORK,
                                  "message": f"request timeout budget {MAX_REQUEST_SECONDS}s"}}
            pool.sync(self._key_loader() or [])
            key_obj = pool.pick(exclude)
            if not key_obj:
                now = time.time()
                # Kiểm tra các key đang trong thời gian cooldown ngắn (do RPM/TPM)
                future_cooldowns = []
                for k in pool._keys:
                    if k.get("status") in ("active", "exhausted"):
                        acct = pool.account_of(k)
                        cd = max(pool._cooldown.get(acct, 0), k.get("cooldown_until", 0))
                        if cd > now:
                            future_cooldowns.append(cd - now)

                # Nếu có key đang cooldown hoặc đã thử qua các account trong exclude
                if (account_attempts > 0 or future_cooldowns or exclude) and retry_exhausted_rounds < 3:
                    retry_exhausted_rounds += 1
                    wait_s = min(future_cooldowns) if future_cooldowns else 15
                    wait_s = max(5, min(int(wait_s) + 1, 15))
                    self._log(f"⏳ Tất cả key đang tạm nghỉ tốc độ (cooldown). Tự động chờ {wait_s}s để hồi phục (lần {retry_exhausted_rounds}/12)...")
                    for _ in range(wait_s):
                        if self._stop_check():
                            return {"ok": False, "text": "", "error": {"kind": ErrorKind.STOPPED}}
                        time.sleep(1)
                    exclude.clear()
                    account_attempts = 0
                    continue
                return {"ok": False, "text": "", "error": {"kind": ErrorKind.NO_KEY}}
            api_key = key_obj.get("key") or ""
            email = key_obj.get("email") or "?"
            self._log_key_pick(pool, key_obj, email)
            pace()
            # Thứ tự model thích nghi: tốt nhất trước + định kỳ chọc model mới (exploration)
            ordered = self._adaptive_model_order() if self._adaptive else None
            res = self._try_models(prompt_text, api_key, json_mode, response_schema,
                                   temp, mout, tout, ordered_models=ordered, email=email,
                                   deadline=started + MAX_REQUEST_SECONDS)
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
                # Quota Gemini free tier là **20 call/ngày / PROJECT / MODEL**
                # ⇒ mỗi model là một "quota bucket" RIÊNG.
                # Phải thử model TIẾP THEO trước khi đổi key, nếu không sẽ
                # vô hiệu hoá 8-10 key/account chỉ vì 1 model hết quota.
                _m = res.get("model")
                _mi = self._models.index(_m) if _m in self._models else -1
                if 0 <= _mi < len(self._models) - 1:
                    # (hiếm — _try_models đã tự xoay model; đường lùi an toàn)
                    self._log(f"⏳ '{_m}' fail (429 quota ngày) → thử '{self._models[_mi + 1]}'…")
                    last = {"kind": kind, "message": msg,
                            "status_code": res.get("status_code"), "model": _m}
                    continue
                self._log(f"⚠ Key {email} hết quota ngày (mọi model). Khóa account 60 phút, chuyển key...")
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
                # 429 RPM/TPM là giới hạn THEO PROJECT (theo key) → khoá riêng key,
                # KHÔNG khoá cả account (sẽ chặn 9-10 key khác của account).
                # Mỗi model cũng có RPM bucket riêng → thử model khác trước.
                retry_delay = retry_delay_from(msg)
                # FIX (Phase 5): trước đây dùng biến `model`/`status_code` KHÔNG
                # tồn tại trong hàm này ⇒ NameError mỗi khi gặp 429 tốc độ.
                _m = res.get("model")
                _mi = self._models.index(_m) if _m in self._models else -1
                if 0 <= _mi < len(self._models) - 1:
                    self._log(f"⚠ '{_m}' fail (429 tốc độ) → thử '{self._models[_mi + 1]}'…")
                    last = {"kind": kind, "message": msg,
                            "status_code": res.get("status_code"), "model": _m}
                    continue
                self._log(f"⚠ Key {email} chạm giới hạn tốc độ ({retry_delay}s). Cooldown riêng key, đổi key...")
                self._pool.lock_key(key_obj, duration=retry_delay)
                exclude.add(api_key)
                account_attempts += 1
                if account_attempts >= MAX_ACCOUNT_ATTEMPTS:
                    time.sleep(5)
                    account_attempts = 0
                continue

            if kind == ErrorKind.INVALID_KEY:
                block_key(api_key, f"HTTP {res.get('status_code', '')}: {msg[:120]}")
                self._mark(key_obj, "invalid", f"HTTP {res.get('status_code', '')}: {msg[:90]}")
                self._log(f"✗ Key {email} bị từ chối (Invalid). Đã blocklist, chuyển key...")
                exclude.add(api_key)
                continue

            if kind == ErrorKind.REQUEST_BAD:
                if is_project_billing_error(msg):
                    # "free tier is not available for this project" là lỗi cấp
                    # PROJECT, không phải cấp Gmail. Chỉ tạm nghỉ KEY này (24h)
                    # để các key khác (project khác) vẫn được thử; KHÔNG khóa
                    # account và KHÔNG block vĩnh viễn — bật billing là dùng lại.
                    block_key(api_key,
                              f"HTTP {res.get('status_code', '')}: {msg[:120]}",
                              ttl=FREE_TIER_RETRY_SECONDS)
                    self._log(f"⚠ Key {email} thuộc project chưa có free tier — "
                              f"tạm nghỉ 24h (bật billing rồi thử lại), chuyển key...")
                    exclude.add(api_key)
                    continue
                if is_account_denial(msg):
                    # Lỗi cấp ACCOUNT (403 denied access) → khoá vĩnh viễn + xoay key.
                    block_account(pool.account_of(key_obj), msg)
                    self._log(f"⚠ Account {email} bị từ chối vĩnh viễn (denied access). "
                              f"Đã đưa vào blocklist, chuyển key...")
                    self._lock_account(key_obj, reason=f"Account denied: {msg[:80]}")
                    exclude.add(api_key)
                    account_attempts += 1
                    if account_attempts >= MAX_ACCOUNT_ATTEMPTS:
                        time.sleep(15)
                        account_attempts = 0
                    continue
                if is_model_restriction(msg):
                    # 403 denied access / model đã ngừng: lỗi theo account, xoay account.
                    self._log(f"⚠ Key {email} không được phép dùng model này ({msg[:80]}). Khóa account, xoay key...")
                    self._lock_account(key_obj, reason=f"Model restriction: {msg[:80]}")
                    exclude.add(api_key)
                    continue
                return {"ok": False, "text": "",
                        "error": {"kind": kind, "message": msg[:200],
                                  "status_code": res.get("status_code")}}

            if kind in (ErrorKind.SERVER, ErrorKind.NETWORK, ErrorKind.EMPTY):
                transient += 1
                # Đổi key/account ở lần sau; không thử lại cùng key 6 vòng.
                exclude.add(api_key)
                transient_accounts += 1
                if transient >= self._max_transient or transient_accounts >= 2:
                    return {"ok": False, "text": "",
                            "error": {"kind": kind, "message": msg[:200]}}
                delay = min(2 ** transient, 30)
                if kind == ErrorKind.NETWORK:
                    self._log(f"🌐 Lỗi kết nối mạng: {msg[:70]}. Chờ {delay}s để kết nối lại (lần {transient}/{self._max_transient})...")
                else:
                    self._log(f"⚠ Máy chủ bận/phản hồi rỗng: {msg[:70]}. Chờ {delay}s rồi thử lại (lần {transient}/{self._max_transient})...")
                time.sleep(delay)
                continue

            return {"ok": False, "text": "", "error": {"kind": kind, "message": msg[:200]}}

    # ────────────────────────────────────────────────────────────────────────
    # ẢNH: Gemini native image (responseModalities = ["TEXT","IMAGE"])
    # Tái dùng AccountPool.pick() + pace() + classify_response() + model fallback
    # (KHÔNG gọi requests.post trần như bản AskCpl — thiếu pace/retry/rotation)
    # ────────────────────────────────────────────────────────────────────────
    def _try_image_models(self, prompt_text, api_key, models, timeout):
        last = None
        billing_hits = 0
        # Lọc model ảnh dead (chưa bị khóa cooldown); giao với list truyền vào nếu có
        available_models = self._get_available_models()
        if models:
            available_models = [m for m in models if m in available_models] or available_models
        if not available_models:
            available_models = list(models) if models else list(self._image_models)
        models = available_models    # fallback checks (models[-1]) dùng chung list đã lọc

        for model in available_models:
            if self._stop_check():
                return {"kind": ErrorKind.STOPPED, "model": model}
            url = (f"https://generativelanguage.googleapis.com/v1beta/"
                   f"models/{model}:generateContent?key={api_key}")
            config = {"responseModalities": ["TEXT", "IMAGE"]}
            try:
                resp = requests.post(url, headers={"Content-Type": "application/json"},
                                     json={"contents": [{"parts": [{"text": prompt_text}]}],
                                           "generationConfig": config},
                                     timeout=timeout)
                ctype = resp.headers.get("content-type", "")
                body = resp.json() if "application/json" in ctype else {}
                status_code = resp.status_code
            except requests.exceptions.Timeout:
                self._mark_model_dead(model, "timeout")
                if model is not available_models[-1]:
                    self._log(f"⏱ Model ảnh '{model}' quá lâu (Timeout > {timeout}s); thử model ảnh khác...")
                    last = {"kind": ErrorKind.NETWORK, "message": "timeout", "model": model}
                    continue
                return {"kind": ErrorKind.NETWORK, "message": "timeout", "model": model}
            except requests.exceptions.RequestException as exc:
                self._mark_model_dead(model, f"{type(exc).__name__}: {exc}")
                if model is not available_models[-1]:
                    self._log(f"🌐 Model ảnh '{model}' lỗi kết nối ({type(exc).__name__}); thử model ảnh khác...")
                    last = {"kind": ErrorKind.NETWORK,
                            "message": f"{type(exc).__name__}: {exc}", "model": model}
                    continue
                return {"kind": ErrorKind.NETWORK,
                        "message": f"{type(exc).__name__}: {exc}", "model": model}

            kind, msg = classify_response(status_code, body)
            if kind == ErrorKind.OK:
                # Reset fail_count khi gọi thành công
                with self._dead_lock:
                    self._dead_fail_count.pop(model, None)
                b64, mime = extract_image(body)
                if b64:
                    return {"kind": ErrorKind.OK, "b64": b64, "mime": mime,
                            "model": model, "message": msg}
                kind = ErrorKind.EMPTY
                msg = "phản hồi không chứa ảnh"
                return {"kind": kind, "message": msg, "status_code": status_code, "model": model}
            # Model ảnh bị giới hạn cứng (limit: 0) → vô hiệu vĩnh viễn, KHÔNG phải
            # rate-limit tạm thời. Bỏ qua model, KHÔNG đánh dấu key exhausted
            # (quota là theo MODEL, không phải theo key).
            if kind == ErrorKind.QUOTA_RATE and "limit: 0" in msg:
                if model is not models[-1]:
                    self._log(f"⛔ Model ảnh '{model}' bị giới hạn cứng (limit: 0) — vô hiệu vĩnh viễn.")
                    last = {"kind": ErrorKind.QUOTA_DAILY, "message": msg,
                            "status_code": status_code, "model": model, "hard_quota": True}
                    continue
                return {"kind": ErrorKind.QUOTA_DAILY, "message": msg,
                        "status_code": status_code, "model": model, "hard_quota": True}
            if kind == ErrorKind.REQUEST_BAD:
                if is_project_billing_error(msg):
                    # Xác nhận bằng tối đa 1 model ảnh kế trước khi tạm nghỉ key.
                    billing_hits += 1
                    if billing_hits < 2 and model != models[-1]:
                        self._log(f"⚠ Model ảnh '{model}' báo free-tier — thử "
                                  f"'{models[models.index(model) + 1]}' để xác nhận…")
                        last = {"kind": kind, "message": msg,
                                "status_code": status_code, "model": model,
                                "billing": True}
                        continue
                    return {"kind": kind, "message": msg,
                            "status_code": status_code, "model": model,
                            "billing": True, "confirmed": True}
                if is_account_denial(msg):
                    return {"kind": kind, "message": msg, "status_code": status_code, "model": model}
                if is_model_restriction(msg):
                    # Model ảnh chết / account bị chặn → thử model ảnh khác
                    if model is not available_models[-1]:
                        self._log(f"⚠ Model ảnh '{model}' không khả dụng ({msg[:70]}); thử model ảnh khác.")
                        last = {"kind": kind, "message": msg, "status_code": status_code,
                                "model": model}
                        continue
                return {"kind": kind, "message": msg, "status_code": status_code, "model": model}
            if kind in (ErrorKind.SERVER, ErrorKind.NETWORK, ErrorKind.EMPTY):
                self._mark_model_dead(model, f"{kind}: {msg[:100]}")
                if model is not available_models[-1]:
                    self._log(f"⚠ Model ảnh '{model}' lỗi {kind} ({msg[:60]}); thử model ảnh khác.")
                    last = {"kind": kind, "message": msg, "status_code": status_code,
                            "model": model}
                    continue
            return {"kind": kind, "message": msg, "status_code": status_code, "model": model}
        return last or {"kind": ErrorKind.NETWORK, "message": "hết model ảnh fallback", "model": None}

    def request_image(self, prompt_text, model=None, timeout=None, models=None) -> dict:
        """Sinh 1 ảnh bằng Gemini native image.

        Trả về:
          {"ok": True,  "b64": str, "mime": str, "model": str, "key": dict}
          {"ok": False, "error": {"kind": str, "message": str}}
        """
        pool = self._pool
        exclude = set()
        # Lọc model ảnh theo dead_models (không gọi model đang cooldown)
        cand_models = list(models) if models else ([model] if model else list(self._image_models))
        available = self._get_available_models()
        if available:
            # Chỉ giữ những model trong available, nhưng nếu models được truyền vào rõ ràng
            # thì ưu tiên danh sách đó (lọc theo available)
            if models:
                cand_models = [m for m in models if m in available] or available
            else:
                cand_models = available
        if not cand_models:
            return {"ok": False, "error": {"kind": ErrorKind.REQUEST_BAD,
                                           "message": "không có model ảnh nào được cấu hình"}}
        tout = timeout or 180
        account_attempts = 0
        MAX_ACCOUNT_ATTEMPTS = 3

        while True:
            if self._stop_check():
                return {"ok": False, "error": {"kind": ErrorKind.STOPPED}}
            pool.sync(self._key_loader() or [])
            key_obj = pool.pick(exclude)
            if not key_obj:
                if account_attempts > 0 and exclude:
                    # Tất cả key đang cooldown → chờ ngắn rồi thử lại
                    wait_s = 15
                    self._log(f"⏳ Key ảnh đang cooldown — chờ {wait_s}s rồi thử lại...")
                    for _ in range(wait_s):
                        if self._stop_check():
                            return {"ok": False, "error": {"kind": ErrorKind.STOPPED}}
                        time.sleep(1)
                    exclude.clear()
                    account_attempts = 0
                    continue
                return {"ok": False, "error": {"kind": ErrorKind.NO_KEY}}
            api_key = key_obj.get("key") or ""
            email = key_obj.get("email") or "?"
            self._log_key_pick(pool, key_obj, email)
            pace()
            res = self._try_image_models(prompt_text, api_key, cand_models, tout)
            kind = res.get("kind")
            msg = res.get("message", "")

            if kind == ErrorKind.OK:
                total = track_call()
                self._touch(key_obj)
                if total > self._daily_budget:
                    self._log(f"⚠ Đã gọi {total:,} lần hôm nay (ngân sách {self._daily_budget:,}/ngày).")
                return {"ok": True, "b64": res["b64"], "mime": res.get("mime", "image/png"),
                        "model": res.get("model"), "key": key_obj, "total_calls": total}

            if kind == ErrorKind.QUOTA_DAILY:
                if res.get("hard_quota"):
                    # Giới hạn cứng theo MODEL → đánh dấu model chết, KHÔNG phí key.
                    self._log(f"⛔ Model ảnh '{res.get('model')}' hết quota cứng (limit: 0) — bỏ qua model này.")
                    return {"ok": False,
                            "error": {"kind": ErrorKind.QUOTA_DAILY,
                                      "message": msg[:200],
                                      "model": res.get("model"),
                                      "hard_quota": True}}
                self._log(f"⚠ Key {email} hết quota ngày khi sinh ảnh. Chuyển key...")
                self._lock_account(key_obj, duration=ACCOUNT_COOLDOWN, reason=f"HTTP 429 Daily (image): {msg[:80]}")
                self._mark(key_obj, "exhausted", f"HTTP 429 Daily (image): {msg[:80]}")
                exclude.add(api_key)
                account_attempts += 1
                if account_attempts >= MAX_ACCOUNT_ATTEMPTS:
                    time.sleep(15)
                    account_attempts = 0
                continue

            if kind == ErrorKind.QUOTA_RATE:
                retry_delay = retry_delay_from(msg)
                self._log(f"⚠ Key {email} chạm giới hạn tốc độ (ảnh, {retry_delay}s). Cooldown riêng key, đổi key...")
                self._pool.lock_key(key_obj, duration=retry_delay)
                exclude.add(api_key)
                account_attempts += 1
                if account_attempts >= MAX_ACCOUNT_ATTEMPTS:
                    time.sleep(5)
                    account_attempts = 0
                continue

            if kind == ErrorKind.INVALID_KEY:
                block_key(api_key, f"HTTP {res.get('status_code', '')} (image): {msg[:120]}")
                self._mark(key_obj, "invalid", f"HTTP {res.get('status_code', '')} (image): {msg[:80]}")
                exclude.add(api_key)
                continue

            if kind == ErrorKind.REQUEST_BAD:
                if is_project_billing_error(msg):
                    block_key(api_key,
                              f"HTTP {res.get('status_code', '')} (image): {msg[:120]}",
                              ttl=FREE_TIER_RETRY_SECONDS)
                    self._log(f"⚠ Key {email} thuộc project chưa có free tier (ảnh) — "
                              f"tạm nghỉ 24h (bật billing rồi thử lại), chuyển key...")
                    exclude.add(api_key)
                    continue
                if is_account_denial(msg):
                    block_account(pool.account_of(key_obj), msg)
                    self._log(f"⚠ Account {email} bị từ chối vĩnh viễn (denied access). Đã blocklist.")
                    self._lock_account(key_obj, reason=f"Account denied (image): {msg[:80]}")
                    exclude.add(api_key)
                    account_attempts += 1
                    continue
                if is_model_restriction(msg):
                    self._lock_account(key_obj, reason=f"Model image restriction: {msg[:80]}")
                    exclude.add(api_key)
                    account_attempts += 1
                    continue
                return {"ok": False,
                        "error": {"kind": kind, "message": msg[:200],
                                  "status_code": res.get("status_code"),
                                  "model": res.get("model")}}

            if kind in (ErrorKind.SERVER, ErrorKind.NETWORK, ErrorKind.EMPTY):
                return {"ok": False,
                        "error": {"kind": kind, "message": msg[:200],
                                  "model": res.get("model")}}

            return {"ok": False, "error": {"kind": kind, "message": msg[:200]}}