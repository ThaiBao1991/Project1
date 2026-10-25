"""
evidence.py — Thu thập DẪN CHỨNG (evidence / sources) cho từ vựng & ngữ pháp.

Nguồn (KHÔNG cần API key):
  1. Wikipedia (ngôn ngữ đích) → trích đoạn mở đầu + link bài
  2. Wiktionary (ngôn ngữ đích) → IPA + từ nguyên + tài liệu tham khảo
  3. Wikipedia (en)            → nguồn dự phòng khi trang ngôn ngữ đích không có
  4. AI (tuỳ chọn)             → sinh sources[] rồi KIỂM TRA từng URL còn sống

Đã kiểm chứng trên máy (2026-10-22):
  • en.wikipedia / en.wiktionary   → 0.4-1.5 s/request, dữ liệu đầy đủ
  • API gateway Wikimedia (server: envoy) trả 429 + "Retry-After: 15" khi burst
    > ~10 request ⇒ phải throttle 0.5 s/request + tôn trọng Retry-After.
  • ja/zh/ko.wiktionary KHÔNG dùng template {{IPA}} ⇒ lấy IPA từ en.wiktionary.
  • "Etymology" nằm trong mục ngôn ngữ (==English==) — bên ngoài là mục
    "Translingual" ⇒ phải khoanh theo mục ngôn ngữ, nếu không lấy nhầm.

Nguyên tắc bất di bất dịch:
  • Network layer KHÔNG BAO GIỜ raise — luôn trả fallback an toàn ({}).
  • Cache bền 30 ngày, ghi cả kết quả "không có gì" để không hỏi lại.
  • LỖI MẠNG thì KHÔNG ghi cache (fetch_failed) — nếu ghi thì từ đó không
    bao giờ được tra lại trong 30 ngày.
  • URL do AI sinh PHẢI verify còn sống mới được giữ (tối đa 3 URL).
  • Mọi field ghi vào bài học là ADDITIVE: sources / ipa_ev / etymology.
"""

import inspect
import json
import os
import re
import sys
import threading
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import requests

UA = "VocabularyApp/1.0 (educational vocabulary app)"
TIMEOUT = 12                   # giây cho 1 request Wikimedia (lần thử lại: 8 s)
CACHE_TTL_DAYS = 30
AI_VERIFY_BUDGET = 8.0         # tổng thời gian verify URL của AI (giây)
AI_MAX_URLS = 3                # số URL AI được giữ tối đa
AI_MAX_TRY = 5                 # số URL AI được thử tối đa

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(BASE_DIR, "data", "evidence_cache.json")

# ─── Throttle Wikimedia (đo thật 2026-10-22) ───────────────────────────────
# Wikimedia API gateway (server: envoy) trả 429 "too many requests" + Retry-After: 15
# khi IP bị vượt burst limit (đo: ~10 request liên tiếp là 429).
# ⇒ throttle 0.5 s/request + tôn trọng Retry-After + tự hạ nhịp 60 s sau 429.
_WIKI_SEM = threading.Semaphore(3)
_WIKI_MIN_INTERVAL = 0.5
_WIKI_COOLDOWN_GAP = 2.0        # nhịp tạm thời trong lúc cooldown
_BLOCK_AFTER = 6               # số 429 liên tiếp thì khoá
_BLOCK_SECONDS = 120
_cooldown_until = 0.0
_block_until = 0.0
_strikes = 0
_last_req = 0.0
_net_lock = threading.Lock()
_net_ok = 0                 # số request thành công (HTTP 200)
_net_fail = 0               # số request lỗi mạng / bị chặn


def _net_snapshot() -> tuple:
    with _net_lock:
        return _net_ok, _net_fail


def _throttle():
    """Chờ tối thiểu khoảng cách giữa 2 request (toàn tiến trình)."""
    global _last_req
    with _net_lock:
        now = time.time()
        gap = _WIKI_COOLDOWN_GAP if now < _cooldown_until else _WIKI_MIN_INTERVAL
        wait = gap - (now - _last_req)
        if wait > 0:
            time.sleep(wait)
        _last_req = time.time()


def _http_get(url: str, params: dict, tries: int = 3,
              timeout: int = TIMEOUT) -> "requests.Response | None":
    """GET có throttle + retry (tôn trọng Retry-After của Wikimedia)."""
    global _block_until, _strikes, _net_ok, _net_fail, _cooldown_until
    if time.time() < _block_until:
        with _net_lock:
            _net_fail += 1
        return None
    delay = 1.5
    for attempt in range(tries):
        with _WIKI_SEM:
            _throttle()
            try:
                r = requests.get(url, params=params,
                                 headers={"User-Agent": UA},
                                 timeout=timeout if attempt == 0 else min(timeout, 8))
            except Exception:
                with _net_lock:
                    _net_fail += 1
                time.sleep(delay)
                delay *= 2
                continue
        if r.status_code == 200:
            _strikes = 0
            with _net_lock:
                _net_ok += 1
            return r
        if r.status_code in (429, 403, 503):
            _strikes += 1
            with _net_lock:
                _net_fail += 1
            # Wikimedia trả Retry-After (đo: 15 s) khi vượt burst limit
            try:
                wait = float(r.headers.get("Retry-After") or 0)
            except (TypeError, ValueError):
                wait = 0
            if attempt == tries - 1:
                if _strikes >= _BLOCK_AFTER:
                    _block_until = time.time() + _BLOCK_SECONDS
                return None
            # hạ nhịp 60 s + chờ Retry-After rồi thử lại
            _cooldown_until = time.time() + 60
            time.sleep(min(max(wait, delay), 20))
            delay *= 2
            continue
        with _net_lock:
            _net_fail += 1
        return r
    return None


# ─── Ngôn ngữ ───────────────────────────────────────────────────────────────
# Tên tiếng Việt → mã ISO (dùng chung với tts_config / dictionary_image)
LANG_NAMES = {
    "Tiếng Anh": "en", "Tiếng Nhật": "ja", "Tiếng Trung": "zh",
    "Tiếng Hàn Quốc": "ko", "Tiếng Pháp": "fr", "Tiếng Đức": "de",
    "Tiếng Nga": "ru", "Tiếng Tây Ban Nha": "es", "Tiếng Thái": "th",
    "Tiếng Ả Rập": "ar", "Tiếng Việt": "vi", "Tiếng Phổ Thông": "en",
}
LANG_CODES = ("en", "ja", "zh", "ko", "fr", "de", "ru", "es", "th", "ar", "vi")

# Tên tiếng Anh dùng trong heading mục ngôn ngữ của Wiktionary
_LANG_SECTION = {
    "en": ("english",), "ja": ("japanese",), "zh": ("chinese",),
    "ko": ("korean",), "fr": ("french",), "de": ("german",),
    "ru": ("russian",), "es": ("spanish",), "th": ("thai",),
    "ar": ("arabic",), "vi": ("vietnamese",),
}

# Heading "Từ nguyên" / "Etymology" theo từng ngôn ngữ
_ETY_HEADINGS = {
    "en": ("etymology",), "ja": ("字源", "語源"), "zh": ("字源", "词源", "詞源"),
    "ko": ("어원", "어근"), "fr": ("étymologie", "etymologie"),
    "de": ("herkunft", "etymologie"), "ru": ("этимология",),
    "es": ("etimología", "etimologia"), "th": ("รากศัพท์",),
    "ar": ("أصل", "اشتقاق"), "vi": ("từ nguyên", "nguồn gốc"),
}

# Heading "Tài liệu tham khảo" / "References"
_REF_HEADINGS = {
    "en": ("references", "citations", "sources"),
    "ja": ("参照", "参考文献"), "zh": ("參考資料", "参考资料", "参考文献"),
    "ko": ("참고 자료", "참고문헌", "각주"),
    "fr": ("références", "references", "sources"),
    "de": ("referenzen", "quellen", "literatur"),
    "ru": ("ссылки", "источники", "литература"),
    "es": ("referencias", "fuentes"),
    "th": ("อ้างอิง",), "ar": ("مراجع", "المراجع"),
    "vi": ("tham khảo", "nguồn"),
}


def normalize_lang(lang) -> str:
    """'Tiếng Nhật' → 'ja' ; 'ja' → 'ja' ; rác → 'en'."""
    s = str(lang or "").strip()
    if not s:
        return "en"
    if s in LANG_CODES:
        return s
    if s in LANG_NAMES:
        return LANG_NAMES[s]
    low = s.lower()
    for name, code in LANG_NAMES.items():
        if name.lower() == low:
            return code
    for code in LANG_CODES:
        if low == code:
            return code
    # 'zh-cn', 'ja-jp' → lấy phần đầu
    head = low.split("-")[0].split("_")[0]
    return head if head in LANG_CODES else "en"


def _norm_word(w: str) -> str:
    return unicodedata.normalize("NFKC", (w or "").strip().lower())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_iso(s: str):
    try:
        return datetime.fromisoformat(str(s))
    except Exception:
        return None


# ─── CACHE BỀN (atomic + lock, TTL 30 ngày) ────────────────────────────────
_cache_lock = threading.RLock()
_cache = None            # {"entries": {key: value}, "stamps": {key: iso}}
_cache_dirty = 0


def _read_cache_file() -> dict:
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return {"entries": {}, "stamps": {}}
    if not isinstance(raw, dict):
        return {"entries": {}, "stamps": {}}
    if "entries" in raw and isinstance(raw.get("entries"), dict):
        entries = raw["entries"]
        stamps = raw.get("stamps") if isinstance(raw.get("stamps"), dict) else {}
        return {"entries": entries, "stamps": stamps}
    # file cũ dạng phẳng key → value
    return {"entries": raw, "stamps": {}}


def _cache_state() -> dict:
    global _cache
    with _cache_lock:
        if _cache is None:
            _cache = _read_cache_file()
        return _cache


def load_cache() -> dict:
    """Trả toàn bộ entries đang cache (key → value)."""
    return _cache_state()["entries"]


def save_cache() -> None:
    """Ghi cache xuống đĩa (tmp + os.replace ⇒ không hỏng file khi crash)."""
    global _cache_dirty
    with _cache_lock:
        st = _cache_state()
        if not _cache_dirty:
            return
        try:
            os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
            tmp = CACHE_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"entries": st["entries"], "stamps": st["stamps"]},
                          f, ensure_ascii=False, indent=1)
            os.replace(tmp, CACHE_PATH)
            _cache_dirty = 0
        except OSError:
            pass


def cache_key(lang, word) -> str:
    """'{slug}|{word}' — slug = mã ngôn ngữ đã chuẩn hoá."""
    return f"{normalize_lang(lang)}|{_norm_word(word)}"


def _is_fresh(stamp_iso: str) -> bool:
    dt = _parse_iso(stamp_iso)
    if not dt:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - dt <= timedelta(days=CACHE_TTL_DAYS)


def _cache_lookup(key) -> tuple:
    """Trả (hit, value). Entry quá hạn TTL ⇒ coi như không có."""
    with _cache_lock:
        st = _cache_state()
        if key not in st["entries"]:
            return False, None
        stamp = st["stamps"].get(key) or ""
        if not stamp:
            val = st["entries"].get(key) or {}
            stamp = (val.get("fetched_at") if isinstance(val, dict) else "") or ""
        if stamp and not _is_fresh(stamp):
            st["entries"].pop(key, None)
            st["stamps"].pop(key, None)
            return False, None
        return True, st["entries"].get(key)


def cache_get(key):
    """Trả value đang cache (kể cả {} = đã biết là không có), None nếu miss/hết hạn."""
    hit, val = _cache_lookup(key)
    return val if hit else None


def cache_put(key, val) -> None:
    """Ghi 1 entry vào cache (value = dict kết quả, kể cả {})."""
    global _cache_dirty
    with _cache_lock:
        st = _cache_state()
        st["entries"][key] = val
        st["stamps"][key] = _now_iso()
        _cache_dirty += 1
        if _cache_dirty >= 50:
            save_cache()


# ─── Tiện ích phân tích wikitext ───────────────────────────────────────────
_HEAD_RE = re.compile(r"^(={2,6})\s*(.+?)\s*\1\s*$")
_WIKI_LINK_RE = re.compile(r"\[\[([^\]|]*\|)?([^\]]*)\]\]")
_EXT_LINK_RE = re.compile(r"\[(?:https?://|//)[^\s\]]*\s*([^\]]*)\]")
_HTML_RE = re.compile(r"<[^>]+>")

# Template hiển thị TỪ (giữ phần chứa từ, bỏ mã ngôn ngữ)
_TERM_TEMPLATES = {
    "m": 1, "l": 1, "mention": 1, "link": 1, "w": 1, "wikipedia": 1,
    "term": 1, "t": 1, "tt": 1, "tlb": 1, "alt": 1, "synonym": 1,
    "synonyms": 1, "gloss": 1, "desc": 1, "sense": 1, "taxlink": 1,
    "inh": -1, "der": -1, "dbt": -1,
}
# Template KHÔNG có nội dung đọc được
_SKIP_TEMPLATES = {"ety", "etymon", "root", "etypos", "top", "bottom",
                   "clear", "wikipedia", "main", "topics", "catlangname"}
# Khoá hiển thị của template tài liệu tham khảo
_REF_KEYS = ("title", "author", "publisher", "journal", "year", "work",
             "website", "text", "url", "date", "archive")


def _norm_heading(s: str) -> str:
    """Chuẩn hoá tiêu đề heading: bỏ template, bỏ link wiki, hạ chữ thường."""
    s = re.sub(r"\{\{[^{}]*\}\}", " ", str(s or ""))
    s = _WIKI_LINK_RE.sub(r"\2", s)
    s = s.replace("'''", "").replace("''", "")
    s = s.strip("= ").strip().lower()
    return re.sub(r"\s+", " ", s)


def _tpl_to_text(body: str) -> str:
    """Rút text hiển thị từ nội dung 1 template wiki."""
    body = str(body or "").strip()
    if not body:
        return ""
    parts = body.split("|")
    name = parts[0].strip()
    named, positional = [], []
    for p in parts[1:]:
        p = p.strip()
        if "=" in p:
            k, val = p.split("=", 1)
            named.append((k.strip().lower(), val.strip()))
        else:
            positional.append(p)
    lname = name.lower()
    if lname in _SKIP_TEMPLATES and lname not in _TERM_TEMPLATES:
        return ""
    if lname in _TERM_TEMPLATES:
        idx = _TERM_TEMPLATES[lname]
        if lname == "wikipedia" and len(positional) == 1:
            return "Wikipedia"
        if 0 <= idx < len(positional):
            return _WIKI_LINK_RE.sub(r"\2", positional[idx])
        if positional:
            return _WIKI_LINK_RE.sub(r"\2", positional[-1])
        for k, v in named:
            if k in ("1", "2", "3", "alt", "text"):
                return _WIKI_LINK_RE.sub(r"\2", v)
        return ""
    picked = [v for k, v in named if k in _REF_KEYS and v]
    if picked:
        return " — ".join(picked[:3])
    if positional:
        return positional[0]
    if ":" in name:
        return name.rsplit(":", 1)[-1].strip()
    return name


def _clean_wiki(text: str) -> str:
    """Biến wikitext thành văn bản thuần (bỏ template, link, HTML)."""
    s = str(text or "")
    # comment HTML phải bỏ TRƯỚC: bên trong comment có thể chứa <ref .../> ⇒
    # nếu bỏ ref trước sẽ nuốt mất dấu "-->" ⇒ comment không đóng ⇒ sót text.
    s = re.sub(r"<!--.*?(?:-->|$)", " ", s, flags=re.S)

    def _tpl_sub(m):
        return _tpl_to_text(m.group(1))

    s = re.sub(r"\{\{([^{}]*)\}\}", _tpl_sub, s)
    s = _WIKI_LINK_RE.sub(r"\2", s)
    s = _EXT_LINK_RE.sub(r"\1", s)
    s = _HTML_RE.sub(" ", s)
    s = s.replace("'''", "").replace("''", "")
    s = s.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", s).strip()


def _extract_language_section(wt: str, code: str) -> str:
    """Lấy phần `==English==` / `=={{L|ja}}==` … tới heading `==` kế tiếp."""
    names = _LANG_SECTION.get(code, ())
    out, inside, level = [], False, 0
    for line in (wt or "").split("\n"):
        m = _HEAD_RE.match(line)
        if m:
            lv = len(m.group(1))
            raw = m.group(2)
            if inside:
                # heading con (===Etymology===) vẫn GIỮ để tìm mục bên trong
                if lv <= level:
                    break
                out.append(line)
                continue
            norm = _norm_heading(raw)
            hit = norm in names
            if not hit:
                hit = bool(re.search(r"\{\{\s*L\s*\|\s*%s\s*\}\}" % re.escape(code),
                                     raw, re.IGNORECASE))
            if hit:
                inside, level = True, lv
                continue
        if inside:
            out.append(line)
    return "\n".join(out).strip()


def _extract_section(text: str, names) -> str:
    """Nội dung sau heading (===Etymology=== …) tới heading kế tiếp."""
    if not text:
        return ""
    names = [n.lower() for n in names]
    out, inside = [], False
    for line in text.split("\n"):
        m = _HEAD_RE.match(line)
        if m:
            norm = _norm_heading(m.group(2))
            if inside:
                break
            if any(norm == n or norm.startswith(n + " ") for n in names):
                inside = True
                continue
        if inside:
            out.append(line)
    return "\n".join(out).strip()


def _clean_ipa(tok: str) -> str:
    s = re.sub(r"<[^>]+>", "", str(tok or "")).strip()
    s = s.replace("[[", "").replace("]]", "").strip()
    return s


def _ipa_from_value(value: str) -> list:
    """'/kæt/|[kʰæt]|a=RP' → ['/kæt/', '[kʰæt]'] (bỏ tham số a=, ref=…)."""
    out = []
    for p in str(value or "").split("|"):
        p = _clean_ipa(p)
        if p.startswith(("/", "[")) and p not in out:
            out.append(p)
    return out


def _extract_ipa(wt: str, code: str, lang_section: str) -> list:
    """IPA từ template {{IPA|code|…}} (ưu tiên đúng ngôn ngữ), fallback {{IPAchar|…}}."""
    scopes = [lang_section, wt]
    for scope in scopes:
        if not scope:
            continue
        hits = re.findall(r"\{\{\s*[Ii][Pp][Aa]\s*\|\s*%s\s*\|([^}]+)\}\}"
                          % re.escape(code), scope)
        if hits:
            out = []
            for h in hits:
                toks = _ipa_from_value(h)
                if toks and toks[0] not in out:
                    out.append(toks[0])          # lấy biến thể chính của mỗi template
            if out:
                return out[:4]
        # trang không dùng {{IPA}} mà dùng {{IPAchar|/…/}}
        chars = re.findall(r"\{\{\s*[Ii][Pp][Aa][Cc]har\s*\|([^}]+)\}\}", scope)
        if chars:
            out = []
            for c in chars:
                t = _clean_ipa(c)
                if t.startswith(("/", "[")):
                    if t not in out:
                        out.append(t)
            if out:
                return out[:4]
    # fallback chung: lấy template IPA đầu tiên (bỏ mã ngôn ngữ lạ)
    for scope in scopes:
        if not scope:
            continue
        hits = re.findall(r"\{\{\s*[Ii][Pp][Aa]\s*\|\s*([^|}]*)\s*\|([^}]+)\}\}", scope)
        for _lang, val in hits:
            toks = _ipa_from_value(val)
            if toks:
                return toks[:4]
    return []


def _extract_references(wt: str, code: str, lang_section: str) -> list:
    """Tối đa 8 mục tài liệu tham khảo (mục bullet trong mục References)."""
    names = _REF_HEADINGS.get(code, ("references",))
    sec = _extract_section(lang_section, names) if lang_section else ""
    if not sec:
        sec = _extract_section(wt, names)
    items = []
    for line in sec.split("\n"):
        s = line.strip()
        if not s or not (s.startswith("*") or s.startswith("#")):
            continue
        s = re.sub(r"^[*#]+\s*", "", s).strip()
        txt = _clean_wiki(s)
        if len(txt) < 3:
            continue
        if txt not in items:
            items.append(txt[:220])
    if not items:
        # trang không có mục References (chỉ có {{reflist}}) → lấy thẻ <ref> có nội dung
        # (bỏ qua thẻ tự đóng <ref name="x"/> để khỏi nuốt nhầm đoạn dài)
        for m in re.findall(r"<ref(?![^>]*?/>)[^>]*>(.*?)</ref>", wt or "",
                            re.DOTALL | re.IGNORECASE):
            txt = _clean_wiki(m)
            if len(txt) > 3 and txt not in items:
                items.append(txt[:220])
    return items[:8]


def _extract_wikipedia_links(wt: str) -> list:
    """Tên bài Wikipedia nhúng trong wikitext ({{wikipedia|en|…}}, {{wp|…}})."""
    out = []
    pats = (
        r"\{\{\s*[Ww]ikipedia\s*\|\s*([^|}]*)\s*\|\s*([^}]+?)\s*\}\}",
        r"\{\{\s*[Ww]p\s*\|\s*([a-z\-]{2,12})\s*:\s*([^}|]+?)\s*\}\}",
        r"\{\{\s*[Ww]p\s*\|\s*([^|}]*)\s*\|\s*([^}]+?)\s*\}\}",
        r"\{\{\s*[Ww]ikipedia\s*\|\s*([^}|]+?)\s*\}\}",
    )
    for pat in pats:
        for m in re.findall(pat, wt or ""):
            title = (m[1] if isinstance(m, tuple) else m).strip()
            title = _clean_wiki(title)
            if not title or title.lower() in ("wikipedia", "wp"):
                continue
            if title not in out:
                out.append(title)
    return out[:10]


# ─── Wiktionary ─────────────────────────────────────────────────────────────
def fetch_wiktionary(word: str, lang: str = "en") -> dict:
    """Lấy IPA + từ nguyên + tài liệu tham khảo từ Wiktionary. Lỗi ⇒ {}."""
    w = (word or "").strip()
    if not w:
        return {}
    code = normalize_lang(lang)
    r = _http_get(f"https://{code}.wiktionary.org/w/api.php",
                   {"action": "parse", "page": w, "prop": "wikitext",
                    "format": "json", "redirects": 1})
    if r is None or r.status_code != 200:
        return {}
    try:
        data = r.json()
    except Exception:
        return {}
    if not isinstance(data, dict) or "error" in data:
        return {}
    parse = data.get("parse") or {}
    wt = ((parse.get("wikitext") or {}).get("*") or "")
    if not wt.strip():
        return {}
    title = parse.get("title") or w
    sect = _extract_language_section(wt, code)
    ipa = _extract_ipa(wt, code, sect)
    ety_raw = _extract_section(sect, _ETY_HEADINGS.get(code, ("etymology",))) if sect else ""
    if not ety_raw:
        ety_raw = _extract_section(wt, _ETY_HEADINGS.get(code, ("etymology",)))
    # bỏ trích dẫn nội tuyến (đã có mục References riêng) cho gọn
    ety_raw = re.sub(r"<!--.*?(?:-->|$)", " ", ety_raw, flags=re.S | re.IGNORECASE)
    ety_raw = re.sub(r"<ref[^>]*/>", " ", ety_raw)
    ety_raw = re.sub(r"<ref[^>]*>.*?</ref>", " ", ety_raw, flags=re.S | re.IGNORECASE)
    etymology = _clean_wiki(ety_raw)[:800]
    references = _extract_references(wt, code, sect)
    links = _extract_wikipedia_links(wt)
    url = f"https://{code}.wiktionary.org/wiki/{quote(str(title).replace(' ', '_'))}"
    return {
        "ipa": ipa,
        "etymology": etymology,
        "references": references,
        "wiktionary_links": links,
        "wiki_title": title,
        "url": url,
        "has_data": True,
    }


# ─── Wikipedia ──────────────────────────────────────────────────────────────
def _wiki_page_info(code: str, word: str) -> dict:
    """Query nhẹ (prop=info) — dùng khi extracts API chậm/lỗi."""
    r = _http_get(f"https://{code}.wikipedia.org/w/api.php",
                   {"action": "query", "prop": "info", "inprop": "url",
                    "titles": word, "format": "json", "redirects": 1},
                   tries=1, timeout=8)
    if r is None or r.status_code != 200:
        return {}
    try:
        data = r.json()
    except Exception:
        return {}
    pages = (data.get("query") or {}).get("pages") or {}
    for _pid, pg in pages.items():
        if not isinstance(pg, dict) or "missing" in pg:
            continue
        title = pg.get("title") or word
        url = pg.get("fullurl") or (
            f"https://{code}.wikipedia.org/wiki/{quote(str(title).replace(' ', '_'))}")
        return {"title": title, "extract": "", "url": url,
                "pageid": pg.get("pageid"), "has_data": True}
    return {}


def fetch_wikipedia(word: str, lang: str = "en") -> dict:
    """Lấy đoạn mở đầu của bài Wikipedia. Lỗi ⇒ {}."""
    w = (word or "").strip()
    if not w:
        return {}
    code = normalize_lang(lang)
    r = _http_get(f"https://{code}.wikipedia.org/w/api.php",
                   {"action": "query", "prop": "extracts|info", "exintro": "",
                    "explaintext": "", "inprop": "url", "titles": w,
                    "format": "json", "redirects": 1})
    if r is None or r.status_code != 200:
        # extracts API hay timeout với bài dài → thử query nhẹ lấy URL
        return _wiki_page_info(code, w)
    try:
        data = r.json()
    except Exception:
        return _wiki_page_info(code, w)
    if not isinstance(data, dict):
        return {}
    pages = (data.get("query") or {}).get("pages") or {}
    for _pid, pg in pages.items():
        if not isinstance(pg, dict) or "missing" in pg:
            continue
        title = pg.get("title") or w
        extract = (pg.get("extract") or "")[:600]
        url = pg.get("fullurl") or (
            f"https://{code}.wikipedia.org/wiki/{quote(str(title).replace(' ', '_'))}")
        return {
            "title": title,
            "extract": extract,
            "url": url,
            "pageid": pg.get("pageid"),
            "has_data": bool(extract.strip()),
        }
    return {}


# ─── Kiểm tra URL còn sống ──────────────────────────────────────────────────
def verify_url(url: str, timeout: int = 8) -> bool:
    """HEAD (fallback GET nếu server chặn HEAD) — True nếu status < 400."""
    u = (url or "").strip()
    if not u.lower().startswith(("http://", "https://")):
        return False
    try:
        r = requests.head(u, headers={"User-Agent": UA}, timeout=timeout,
                          allow_redirects=True)
        if r.status_code in (403, 405, 501):
            # nhiều server chặn HEAD → thử GET (không tải hết body)
            try:
                r = requests.get(u, headers={"User-Agent": UA}, timeout=timeout,
                                 allow_redirects=True, stream=True)
            except Exception:
                return False
            try:
                r.close()
            except Exception:
                pass
        return r.status_code < 400
    except Exception:
        return False


# ─── Gọi AI (tuỳ chọn) ─────────────────────────────────────────────────────
def _call_ai(fn, payload: dict):
    """Gọi callable AI theo nhiều dạng chữ ký (word/lang/meaning_vi hoặc 1 payload)."""
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        sig = None
    if sig is not None:
        params = sig.parameters
        has_var_kw = any(p.kind == p.VAR_KEYWORD for p in params.values())
        kwargs = dict(payload) if has_var_kw else {
            k: v for k, v in payload.items() if k in params}
        missing = [p.name for p in params.values()
                   if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                   and p.default is p.empty and p.name not in kwargs]
        if not missing:
            try:
                return fn(**kwargs)
            except TypeError:
                pass
    for args in ((payload,), ()):
        try:
            return fn(*args)
        except TypeError:
            continue
    return None


def _normalize_ai_sources(raw) -> list:
    """Chuẩn hoá output AI thành list {title,url,kind,quote}."""
    if raw is None:
        return []
    if isinstance(raw, str):
        txt = raw.strip()
        txt = re.sub(r"^```(?:json)?|```$", "", txt, flags=re.MULTILINE).strip()
        try:
            raw = json.loads(txt)
        except Exception:
            return []
    if isinstance(raw, dict):
        if isinstance(raw.get("sources"), list):
            raw = raw["sources"]
        elif raw.get("url"):
            raw = [raw]
        else:
            return []
    if not isinstance(raw, list):
        return []
    out = []
    for it in raw:
        if not isinstance(it, dict):
            continue
        url = str(it.get("url") or "").strip()
        if not url.lower().startswith(("http://", "https://")):
            continue
        out.append({
            "title": str(it.get("title") or it.get("name") or url)[:200],
            "url": url,
            "kind": str(it.get("kind") or it.get("type") or "web")[:60],
            "quote": str(it.get("quote") or it.get("snippet") or "")[:400],
        })
    return out


def _verify_ai_sources(items: list, budget: float = AI_VERIFY_BUDGET) -> list:
    """Chỉ giữ URL còn sống (tối đa 3 URL, tổng ngân sách timeout 8 s)."""
    deadline = time.time() + budget
    out, tried = [], 0
    for it in items:
        if len(out) >= AI_MAX_URLS or tried >= AI_MAX_TRY:
            break
        remain = deadline - time.time()
        if remain <= 0.5:
            break
        tried += 1
        if verify_url(it["url"], timeout=max(2, int(min(8, remain)))):
            out.append(it)
    return out


# ─── Chuỗi thu thập dẫn chứng ──────────────────────────────────────────────
def gather(word: str, lang: str = "en", meaning_vi: str = "",
           use_ai=None, log_fn=None, use_cache: bool = True) -> dict:
    """Thu thập dẫn chứng cho 1 từ. KHÔNG BAO GIỜ raise.

    use_cache=True: đọc/ghi cache bền. Kết quả rỗng do LỖI MẠNG không được
    ghi cache (nếu ghi, từ đó sẽ không bao giờ được tra lại trong 30 ngày).
    """
    def _log(m):
        if log_fn:
            try:
                log_fn(m)
            except Exception:
                pass

    w = (word or "").strip()
    if not w:
        return {}
    code = normalize_lang(lang)
    key = cache_key(code, w)
    if use_cache:
        hit, val = _cache_lookup(key)
        if hit:
            _log(f"   📚 {w} [{code}] → cache ({key})")
            return val or {}

    ok0, fail0 = _net_snapshot()
    sources, ipa, ety, refs = [], [], "", []

    # a) Wikipedia (ngôn ngữ đích) — nguồn #1
    wp = fetch_wikipedia(w, code)
    if wp.get("has_data"):
        sources.append({
            "title": wp["title"], "url": wp["url"], "kind": "wikipedia",
            "quote": (wp.get("extract") or "")[:240], "lang": code,
            "license": "CC-BY-SA",
        })

    # b) Wiktionary (ngôn ngữ đích) — nguồn #2 (IPA + từ nguyên + tham khảo)
    wt = fetch_wiktionary(w, code)
    if wt.get("has_data"):
        ipa = list(wt.get("ipa") or [])
        ety = wt.get("etymology") or ""
        refs = list(wt.get("references") or [])
        sources.append({
            "title": wt.get("wiki_title") or w, "url": wt.get("url") or "",
            "kind": "wiktionary",
            "quote": (ety or wt.get("wiki_title") or "")[:240], "lang": code,
            "license": "CC-BY-SA",
        })
        # Trang đích không có IPA (ja/zh/ko hay vậy) → lấy từ en.wiktionary
        if not ipa and code != "en":
            wt_en = fetch_wiktionary(w, "en")
            if wt_en.get("ipa"):
                ipa = list(wt_en["ipa"])[:4]

    # c) Wikipedia (en) — nguồn #3 dự phòng
    if code != "en" and len(sources) < 2:
        wp_en = fetch_wikipedia(w, "en")
        if wp_en.get("has_data"):
            sources.append({
                "title": wp_en["title"], "url": wp_en["url"],
                "kind": "wikipedia-en", "quote": (wp_en.get("extract") or "")[:240],
                "lang": "en", "license": "CC-BY-SA",
            })

    # d) AI sinh nguồn → verify URL còn sống mới giữ
    if use_ai:
        try:
            payload = {
                "word": w, "lang": code, "meaning_vi": (meaning_vi or "").strip(),
                "task": "sources",
                "instruction": ("Return JSON list of reliable sources for this word: "
                                "[{title, url, kind, quote}]. url must be a real, "
                                "directly visitable page."),
            }
            ai_items = _normalize_ai_sources(_call_ai(use_ai, payload))
            alive = _verify_ai_sources(ai_items)
            for it in alive:
                sources.append({
                    "title": it["title"], "url": it["url"], "kind": it["kind"],
                    "quote": it["quote"], "lang": code,
                })
            if ai_items:
                _log(f"   📚 {w}: AI {len(alive)}/{len(ai_items)} URL còn sống")
        except Exception:
            pass

    # bỏ nguồn trùng URL (Wikipedia + AI hay trả cùng 1 trang)
    seen, uniq = set(), []
    for s in sources:
        u = (s.get("url") or "").strip()
        if u in seen:
            continue
        seen.add(u)
        uniq.append(s)
    sources = uniq

    n = len(sources)
    if n >= 3:
        confidence = "high"
    elif n == 2:
        confidence = "high" if (ipa or ety) else "medium"
    elif n == 1:
        confidence = "medium"
    else:
        confidence = "low"

    # Không có request nào thành công và có lỗi ⇒ mạng chết / bị chặn
    ok1, fail1 = _net_snapshot()
    fetch_failed = (ok1 == ok0) and (fail1 > fail0)

    res = {
        "word": w,
        "sources": sources,
        "ipa": ipa,
        "etymology": ety,
        "wiktionary_references": refs,
        "confidence": confidence,
        "fetched_at": _now_iso(),
    }
    if fetch_failed:
        res["fetch_failed"] = True
    if use_cache and not fetch_failed:
        cache_put(key, res)

    _log(f"   📚 {w} [{code}] → {n} nguồn | ipa={len(ipa)} | "
         f"etym={'có' if ety else 'không'}"
         f"{' | LỖI MẠNG (không cache)' if fetch_failed else ''}")
    return res


# ─── Gắn dẫn chứng vào bài học ─────────────────────────────────────────────
def attach_to_lesson(lesson: dict, lang, use_ai=None, log_fn=None, limit: int = 0) -> dict:
    """Gắn sources / ipa_ev / etymology vào từng từ trong lesson['vocab'].

    Trả {"ok": số từ có nguồn, "cached": số từ lấy từ cache,
         "failed": số từ không có nguồn}.

    `limit` > 0 ⇒ chỉ tra tối đa N từ đầu (tiết kiệm request Wikimedia —
    IP bị chặn sau ~30.000 request). 0 = không giới hạn.
    """
    stats = {"ok": 0, "cached": 0, "failed": 0}
    if not isinstance(lesson, dict):
        return stats
    vocab = lesson.get("vocab") or []
    if not isinstance(vocab, list):
        return stats
    code = normalize_lang(lang)

    items = [(i, v) for i, v in enumerate(vocab) if isinstance(v, dict)]
    if limit and limit > 0:
        items = items[:int(limit)]
    results = {}

    def _fetch(item):
        _i, v = item
        word = (v.get("word") or "").strip()
        hit = _cache_lookup(cache_key(code, word))[0]
        res = gather(word, code, v.get("meaning_vi") or "",
                     use_ai=use_ai, log_fn=log_fn)
        return _i, (res or {}), hit

    if items:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as ex:
            for i, res, cached in ex.map(_fetch, items):
                results[i] = (res or {}, cached)

    for i, v in items:
        res, cached = results.get(i, ({}, False))
        src = res.get("sources") or []
        v["sources"] = src
        ipa_list = res.get("ipa") or []
        if ipa_list:
            v["ipa_ev"] = ipa_list[0]
        elif not v.get("ipa_ev"):
            v["ipa_ev"] = v.get("ipa") or v.get("pronunciation") or ""
        # KHÔNG xoá etymology do AI sinh nếu Wiktionary không có.
        ety = res.get("etymology") or ""
        if ety:
            v["etymology"] = ety
        if src:
            stats["ok"] += 1
        else:
            stats["failed"] += 1
        if cached:
            stats["cached"] += 1
    save_cache()
    return stats


# ─── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="Thu thập dẫn chứng (evidence) cho 1 từ")
    ap.add_argument("--word", required=True, help="từ cần tra (VD: cat, 猫)")
    ap.add_argument("--lang", default="en", help="mã ngôn ngữ (en/ja/zh/…) hoặc tên tiếng Việt")
    ap.add_argument("--meaning-vi", default="", help="nghĩa tiếng Việt (tuỳ chọn)")
    ap.add_argument("--no-cache", action="store_true", help="bỏ qua cache, tra lại từ đầu")
    args = ap.parse_args()

    _code = normalize_lang(args.lang)
    _key = cache_key(_code, args.word)
    if args.no_cache:
        _res = gather(args.word, _code, args.meaning_vi, log_fn=print,
                      use_cache=False)
    else:
        _res = gather(args.word, _code, args.meaning_vi, log_fn=print)
        save_cache()
        if not _res:
            print(f"(cache: {_key} — không có dẫn chứng nào)")
    print(json.dumps(_res, ensure_ascii=False, indent=2))
