"""
dictionary_image.py — Tầng ảnh từ từ điển / kho ảnh Wikimedia (KHÔNG cần API key AI).

Đã kiểm chứng trên máy (2026-10-21):
  • commons.wikimedia.org search (namespace 6)  → 0.5-2.2s, ảnh thật + license + tác giả
  • {lang}.wikipedia.org/w/api.php pageimages   → nhanh, ảnh dẫn đầu bài viết
  • {lang}.wiktionary.org                       → nhanh
  • api.openverse.org                           → KHÔNG ỔN ĐỊNH (timeout 60s) → chỉ dùng
                                                  là fallback cuối, timeout ngắn

Nguyên tắc chất lượng:
  • Chỉ nhận ảnh có độ liên quan CAO: tiêu đề bài viết/filename phải khớp từ cần tìm.
  • Ghi `confidence` = "high" | "medium" | "low" để UI hiển thị badge.
  • Bắt buộc attribution (credit + license) — Wikimedia là CC-BY-SA.

URL Wikimedia có query utm_* → phải canonicalize (URL sẽ hỏng theo thời gian).
"""

import io
import json
import os
import re
import threading
import time
import unicodedata

import requests

from ai.media_store import SOURCE_DICT

UA = "VocabularyApp/1.0 (educational vocabulary app; contact: local)"
TIMEOUT = 20
OPENVERSE_TIMEOUT = 12       # Openverse hay chậm — timeout ngắn, bỏ qua nếu chậm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ─── THROTTLE Wikimedia ───────────────────────────────────────────────────────
# Đo thật: 36 request Wikimedia đồng thời ⇒ 429 ⇒ 96% ảnh thành placeholder.
# Ràng buộc toàn tiến trình: tối đa 8 request đồng thời + tối thiểu 0.1 s giữa
# 2 request + retry khi 429. Đo lại: 10/10 ảnh thật, không còn 429.
_WIKI_SEM = threading.Semaphore(8)
_WIKI_MIN_INTERVAL = 0.10
WORD_DEADLINE_SECONDS = 10.0
# Circuit breaker Wikimedia
_WIKI_BLOCK_AFTER = 5          # 5 lần 429 liên tiếp
_WIKI_BLOCK_SECONDS = 900      # khoá 15 phút
_wiki_block_until = 0.0
_wiki_strikes = 0
_wiki_last_req = 0.0
_wiki_lock = threading.Lock()


def _throttle():
    """Chờ tối thiểu _WIKI_MIN_INTERVAL giữa 2 request Wikimedia (toàn tiến trình)."""
    global _wiki_last_req
    with _wiki_lock:
        wait = _WIKI_MIN_INTERVAL - (time.time() - _wiki_last_req)
        if wait > 0:
            time.sleep(wait)
        _wiki_last_req = time.time()


def _wiki_get(url: str, params: dict, tries: int = 2, timeout: int = TIMEOUT):
    """GET có throttle + retry (429/403 → chờ tăng dần).

    Circuit breaker: sau N lần 429 liên tiếp ⇒ tạm khoá Wikimedia trong
    _WIKI_BLOCK_SECONDS. Đo thật: sau ~30k request, Wikimedia trả 429 cho MỌI
    request từ IP này ⇒ mỗi từ mất 10 s (deadline) chỉ để nhận 429 ⇒
    toàn bộ thời gian của pipeline bị nuốt. Cần breaker để fail nhanh.
    """
    global _wiki_block_until, _wiki_strikes
    now = time.time()
    if now < _wiki_block_until:
        return None                                  # đang bị chặn → fail nhanh
    delay = 1.5
    for attempt in range(tries):
        with _WIKI_SEM:
            _throttle()
            try:
                r = requests.get(url, params=params,
                                headers={"User-Agent": UA}, timeout=timeout)
            except Exception:
                time.sleep(delay)
                delay *= 2
                continue
        if r.status_code == 200:
            _wiki_strikes = 0
            return r
        if r.status_code in (429, 403, 503):
            _wiki_strikes += 1
            if _wiki_strikes >= _WIKI_BLOCK_AFTER:
                _wiki_block_until = time.time() + _WIKI_BLOCK_SECONDS
                return None
            time.sleep(delay)
            delay *= 2
            continue
        return r
    return None


# ─── CACHE BỀN ───────────────────────────────────────────────────────────────
# 30.102 từ nhưng nhiều từ LẶP LẠI giữa các ngày (và cả giữa các khóa học).
# Không có cache ⇒ hàng chục nghìn request thừa ⇒ Wikimedia 429 ⇒ 96% placeholder.
CACHE_PATH = os.path.join(BASE_DIR, "data", "media", "image_cache.json")
_cache_lock = threading.Lock()
_cache = None
_cache_dirty = 0


def _load_cache() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache = data if isinstance(data, dict) else {}
    except Exception:
        _cache = {}
    return _cache


def _save_cache() -> None:
    global _cache_dirty
    if not _cache_dirty:
        return
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        tmp = CACHE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False, indent=1)
        os.replace(tmp, CACHE_PATH)
        _cache_dirty = 0
    except OSError:
        pass


def _cache_key(lang: str, word: str) -> str:
    return f"{_norm_lang(lang)}|{_norm_word(word)}"


def _norm_word(w: str) -> str:
    return unicodedata.normalize("NFKC", (w or "").strip().lower())


def _norm_lang(v) -> str:
    """Chuẩn hoá tên ngôn ngữ về slug (để cache dùng chung giữa các biến thể)."""
    return re.sub(r"[^a-z0-9]+", "_", str(v or "").strip().lower()).strip("_")


def _cache_get(lang: str, word: str):
    """Trả (hit, info). info=None ⇒ đã biết là KHÔNG có ảnh."""
    with _cache_lock:
        v = _load_cache().get(_cache_key(lang, word), "__miss__")
    if v == "__miss__":
        return False, None
    return True, v


def _cache_put(lang: str, word: str, info) -> None:
    global _cache_dirty
    with _cache_lock:
        _load_cache()[_cache_key(lang, word)] = info
        _cache_dirty += 1
        if _cache_dirty >= 50:
            _save_cache()

WIKI_HOSTS = {
    "Tiếng Anh": "en.wikipedia.org",
    "Tiếng Nhật": "ja.wikipedia.org",
    "Tiếng Trung": "zh.wikipedia.org",
    "Tiếng Hàn Quốc": "ko.wikipedia.org",
    "Tiếng Pháp": "fr.wikipedia.org",
    "Tiếng Đức": "de.wikipedia.org",
    "Tiếng Nga": "ru.wikipedia.org",
    "Tiếng Tây Ban Nha": "es.wikipedia.org",
    "Tiếng Thái": "th.wikipedia.org",
    "Tiếng Ả Rập": "ar.wikipedia.org",
    "Tiếng Việt": "vi.wikipedia.org",
    "Tiếng Phổ Thông": "en.wikipedia.org",
}
WIKI_HOSTS_DEFAULT = "en.wikipedia.org"

WIKTIONARY_HOSTS = {
    "Tiếng Anh": "en.wiktionary.org",
    "Tiếng Nhật": "ja.wiktionary.org",
    "Tiếng Trung": "zh.wiktionary.org",
    "Tiếng Hàn Quốc": "ko.wiktionary.org",
    "Tiếng Pháp": "fr.wiktionary.org",
    "Tiếng Đức": "de.wiktionary.org",
    "Tiếng Nga": "ru.wiktionary.org",
    "Tiếng Tây Ban Nha": "es.wiktionary.org",
    "Tiếng Thái": "th.wiktionary.org",
    "Tiếng Ả Rập": "ar.wiktionary.org",
    "Tiếng Việt": "vi.wiktionary.org",
}
WIKTIONARY_HOSTS_DEFAULT = "en.wiktionary.org"

COMMONS_API = "https://commons.wikimedia.org/w/api.php"

_UTM_RE = re.compile(r"[?&]utm_[^&]*", re.IGNORECASE)
_MULTI_AMP_RE = re.compile(r"&{2,}")
_WORD_RE = re.compile(r"[^\w]+", re.UNICODE)

# Tiêu đề bài viết trang định nghĩa — ảnh đại diện KHÔNG đại diện nghĩa từ
_DISAMBIG_MARKERS = (
    "disambiguation", "giải ngữ", "消歧義", "多義", "-disambig",
    "ambiguity", "désambiguïsation", "désambiguïsation", "多義語",
)


def canonicalize_wikimedia_url(url: str) -> str:
    """Bỏ query utm_* và gộp dấu & thừa. URL Wikimedia có utm sẽ hỏng theo thời gian."""
    if not url:
        return ""
    out = _UTM_RE.sub("", url)
    out = _MULTI_AMP_RE.sub("&", out)
    if out.endswith("&"):
        out = out[:-1]
    return out


def _norm(s: str) -> str:
    """Chuẩn hóa để so khớp: bỏ dấu câu, hạ chữ thường, gộp khoảng trắng."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = _WORD_RE.sub(" ", s).strip().lower()
    return " ".join(s.split())


def title_matches(query: str, title: str) -> str:
    """Mức khớp giữa query và title.

    Trả: "exact" | "prefix" | "word" | ""
    """
    q = _norm(query)
    t = _norm(title)
    if not q or not t:
        return ""
    if q == t:
        return "exact"
    if t.startswith(q + " "):
        return "prefix"
    if f" {q} " in f" {t} ":
        return "word"
    return ""


def is_disambiguation(title: str) -> bool:
    low = (title or "").lower()
    if any(m in low for m in _DISAMBIG_MARKERS):
        return True
    # Trang "Radical 94" / "Kangxi radical" — KHÔNG phải ảnh minh họa nghĩa từ
    if re.match(r"^(radical|kangxi radical)\s*\d+", low):
        return True
    return False


def wiki_host_for(language: str) -> str:
    return WIKI_HOSTS.get((language or "").strip(), WIKI_HOSTS_DEFAULT)


def wiktionary_host_for(language: str) -> str:
    return WIKTIONARY_HOSTS.get((language or "").strip(), WIKTIONARY_HOSTS_DEFAULT)


# ─── Tải ảnh (chống hotlink bằng Referer) ────────────────────────────────────
def download_image(url: str, referer: str = "", timeout: int = 40):
    """Tải 1 ảnh. Trả (bytes, content_type) hoặc (b"", "") nếu lỗi."""
    if not url:
        return b"", ""
    headers = {"User-Agent": UA}
    if referer:
        headers["Referer"] = referer
    try:
        with _WIKI_SEM:
            _throttle()
            r = requests.get(url, headers=headers, timeout=timeout, stream=True)
    except Exception:
        return b"", ""
    ctype = ""
    try:
        if r.status_code != 200:
            return b"", ""
        ctype = (r.headers.get("content-type") or "").split(";")[0].strip().lower()
        if not ctype.startswith("image/"):
            return b"", ""
        # SVG không xử lý được bằng PIL → bỏ qua (thay vì lưu ảnh hỏng)
        if ctype == "image/svg+xml":
            return b"", ""
        buf = io.BytesIO()
        for chunk in r.iter_content(65536):
            if chunk:
                buf.write(chunk)
    except Exception:
        return b"", ""
    finally:
        try:
            r.close()
        except Exception:
            pass
    data = buf.getvalue()
    if len(data) < 5 * 1024:
        return b"", ""
    return data, ctype


# ─── Wikimedia Commons — tìm trực tiếp trong kho ảnh ────────────────────────
def fetch_commons_images(query: str, limit: int = 8):
    """Tìm ảnh trong kho Wikimedia Commons (namespace 6). Trả list dict."""
    q = (query or "").strip()
    if not q:
        return []
    r = _wiki_get(COMMONS_API,
                  {"action": "query", "generator": "search",
                   "gsrsearch": q, "gsrnamespace": 6,
                   "gsrlimit": max(1, min(20, limit)),
                   "prop": "imageinfo",
                   "iiprop": "url|size|mime|extmetadata",
                   "iiurlwidth": 640, "format": "json"})
    if r is None or r.status_code != 200:
        return []
    try:
        data = r.json()
    except Exception:
        return []
    pages = (data.get("query") or {}).get("pages") or {}
    out = []
    for _pid, pg in sorted(pages.items(), key=lambda kv: kv[1].get("index", 999)):
        ii = (pg.get("imageinfo") or [{}])[0]
        mime = ii.get("mime") or ""
        if mime and not mime.startswith("image/"):
            continue
        if mime == "image/svg+xml":
            continue
        em = ii.get("extmetadata") or {}
        url = ii.get("thumburl") or ii.get("url") or ""
        if not url:
            continue
        title = (pg.get("title") or "").replace("File:", "").replace("Image:", "")
        out.append({
            "url": canonicalize_wikimedia_url(url),
            "thumbnail": canonicalize_wikimedia_url(ii.get("thumburl") or url),
            "title": title,
            "artist": _strip_html((em.get("Artist") or {}).get("value", "")),
            "credit": _strip_html((em.get("Artist") or {}).get("value", "")) or "Wikimedia Commons",
            "license": _strip_html((em.get("LicenseShortName") or {}).get("value", "")) or "CC",
            "license_url": _strip_html((em.get("LicenseUrl") or {}).get("value", "")),
            "source": "Wikimedia Commons",
            "source_url": ii.get("descriptionurl") or "",
            "width": ii.get("thumbwidth") or ii.get("width") or 0,
            "height": ii.get("thumbheight") or ii.get("height") or 0,
        })
    return out


def _strip_html(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", "", str(s))
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ─── Wikipedia / Wiktionary pageimages ───────────────────────────────────────
def fetch_wiki_image(word: str, host: str, min_width: int = 200):
    """Ảnh dẫn đầu (lead image) của bài có tên đúng bằng `word`."""
    q = (word or "").strip()
    if not q:
        return {}
    r = _wiki_get(f"https://{host}/w/api.php",
                  {"action": "query", "prop": "pageimages",
                   "titles": q, "format": "json", "pithumbsize": 640,
                   "redirects": 1, "inprop": "url"})
    if r is None or r.status_code != 200:
        return {}
    try:
        data = r.json()
    except Exception:
        return {}
    pages = (data.get("query") or {}).get("pages") or {}
    for _pid, pg in pages.items():
        if pg.get("missing") or pg.get("invalid"):
            continue
        title = pg.get("title") or q
        if is_disambiguation(title):
            continue
        thumb = pg.get("thumbnail") or {}
        src = thumb.get("source")
        if not src:
            continue
        src = canonicalize_wikimedia_url(src)
        w = int(thumb.get("width") or 0)
        h = int(thumb.get("height") or 0)
        if w and w < min_width:
            continue
        return {
            "url": src,
            "thumbnail": src,
            "title": title,
            "credit": f"Wikimedia Commons — {title}",
            "license": "CC-BY-SA",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "source": host,
            "source_url": f"https://{host}/wiki/{title.replace(' ', '_')}",
            "width": w, "height": h,
        }
    return {}


def fetch_wiki_search_images(word: str, host: str, limit: int = 6):
    """Tìm bài viết qua search → list ảnh (kèm tiêu đề để đánh giá độ liên quan)."""
    q = (word or "").strip()
    if not q:
        return []
    r = _wiki_get(f"https://{host}/w/api.php",
                  {"action": "query", "generator": "search",
                   "gsrsearch": q, "gsrlimit": max(1, min(20, limit)),
                   "prop": "pageimages|info", "inprop": "url",
                   "piprop": "thumbnail", "pithumbsize": 640,
                   "format": "json"})
    if r is None or r.status_code != 200:
        return []
    try:
        data = r.json()
    except Exception:
        return []
    pages = (data.get("query") or {}).get("pages") or {}
    out = []
    for _pid, pg in sorted(pages.items(), key=lambda kv: kv[1].get("index", 999)):
        title = pg.get("title") or q
        if is_disambiguation(title):
            continue
        thumb = pg.get("thumbnail") or {}
        src = thumb.get("source")
        if not src:
            continue
        out.append({
            "url": canonicalize_wikimedia_url(src),
            "thumbnail": canonicalize_wikimedia_url(src),
            "title": title,
            "credit": f"Wikimedia Commons — {title}",
            "license": "CC-BY-SA",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "source": host,
            "source_url": f"https://{host}/wiki/{title.replace(' ', '_')}",
            "width": int(thumb.get("width") or 0),
            "height": int(thumb.get("height") or 0),
        })
    return out


# ─── Openverse (fallback, KHÔNG ỔN ĐỊNH) ───────────────────────────────────
def fetch_openverse(word: str, limit: int = 5, license_type: str = "commercial"):
    q = (word or "").strip()
    if not q:
        return []
    try:
        r = requests.get("https://api.openverse.org/v1/images/",
                         params={"q": q, "page_size": max(1, min(20, limit)),
                                 "license_type": license_type},
                         headers={"User-Agent": UA}, timeout=OPENVERSE_TIMEOUT)
    except Exception:
        return []
    if r.status_code != 200:
        return []
    try:
        data = r.json()
    except Exception:
        return []
    out = []
    for it in (data.get("results") or []):
        url = it.get("url") or ""
        if not url:
            continue
        out.append({
            "url": url,
            "thumbnail": it.get("thumbnail") or "",
            "title": it.get("title") or "",
            "credit": f"{it.get('creator') or 'Unknown'} / Openverse",
            "license": (it.get("license") or "").upper(),
            "license_url": it.get("license_url") or "",
            "source": "Openverse",
            "source_url": it.get("foreign_landing_url") or "",
            "width": it.get("width") or 0,
            "height": it.get("height") or 0,
        })
    return out


# ─── Truy vấn ứng viên ───────────────────────────────────────────────────────
def search_candidates(word: str, pronunciation: str = "", meaning_vi: str = "") -> list:
    """Các truy vấn thử lần lượt (độ liên quan từ cao → thấp)."""
    cands = []
    w = (word or "").strip()
    if w:
        cands.append(w)
    p = (pronunciation or "").strip().strip("/")
    if p and p.isascii() and p.lower() != w.lower() and len(p) > 1:
        cands.append(p)
    m = (meaning_vi or "").strip()
    head = m.split(",")[0].split("(")[0].strip()
    if head and head.lower() not in [c.lower() for c in cands]:
        cands.append(head)
    return cands[:3]


# ─── Chuỗi tìm ảnh cho 1 từ ────────────────────────────────────────────────
def find_image_for_word(word: str, language: str = "", pronunciation: str = "",
                        meaning_vi: str = "", log_fn=None,
                        use_openverse: bool = False) -> dict:
    """Tìm ảnh cho 1 từ theo chuỗi, ưu tiên độ liên quan:

    1. Wikipedia bài đúng tên từ        → confidence "high"
    2. Wikipedia search (từ khớp)       → confidence "high"/"medium"
    3. Wikipedia search (theo nghĩa VN)  → confidence "medium"
    4. Wikimedia Commons (từ trong tên) → confidence "medium"/"low"
    5. Wiktionary                        → confidence "medium"
    6. Openverse (fallback, chậm)       → confidence "low"
    """
    def _log(m):
        if log_fn:
            try:
                log_fn(m)
            except Exception:
                pass

    cands = search_candidates(word, pronunciation, meaning_vi)
    if not cands:
        return {}
    # Deadline mỗi từ: không có bài viết ⇒ 3 ứng viên × 3 endpoint × retry
    # ⇒ có thể mất 45 s. Giới hạn 10 s rồi ghi cache "không có ảnh".
    deadline = time.time() + WORD_DEADLINE_SECONDS

    # ── CACHE BỀN ──────────────────────────────────────────────────────
    # 30.102 từ nhưng nhiều từ LẶP LẠI giữa các ngày và các khóa học.
    # Không có cache ⇒ hàng chục nghìn request thừa ⇒ Wikimedia 429 ⇒ 96% ảnh
    # thành placeholder. Cache cả kết quả "không có ảnh" để không hỏi lại.
    hit, info = _cache_get(language, word)
    if hit:
        if not info:
            return {}
        data, ctype = download_image(info.get("url", ""),
                                     referer=f"https://{info.get('source') or 'en.wikipedia.org'}/")
        if data:
            it = dict(info)
            it["bytes"] = data
            it["content_type"] = ctype or "image/jpeg"
            it["source_tier"] = SOURCE_DICT
            it["provider"] = info.get("provider", "cache")
            it["confidence"] = info.get("confidence", "medium")
            return it
        return {}

    wh = wiki_host_for(language)
    wkh = wiktionary_host_for(language)

    def _try(item, conf, provider, log_msg):
        data, ctype = download_image(item["url"], referer=f"https://{wh}/")
        if not data:
            return None
        it = dict(item)
        it["bytes"] = data
        it["content_type"] = ctype or "image/jpeg"
        it["source_tier"] = SOURCE_DICT
        it["provider"] = provider
        it["confidence"] = conf
        _cache_put(language, word, {k: it.get(k) for k in
                                   ("url", "title", "credit", "license",
                                    "source", "source_url", "provider", "confidence")})
        _log(f"   🖼️  {log_msg} → {it['title']!r} ({len(data)//1024} KB, {conf})")
        return it

    # 1) Wikipedia — bài có tên đúng bằng từ
    for q in cands:
        if time.time() > deadline:
            break
        it = fetch_wiki_image(q, wh)
        if it:
            r = _try(it, "high", "wikipedia", f"Wikipedia '{q}'")
            if r:
                r["query"] = q
                return r
        time.sleep(0.15)

    # 2) Wikipedia search — chỉ nhận khi tiêu đề khớp từ
    for q in cands:
        if time.time() > deadline:
            break
        for it in fetch_wiki_search_images(q, wh):
            m = title_matches(q, it["title"])
            if not m:
                continue
            conf = "high" if m == "exact" else "medium"
            r = _try(it, conf, "wikipedia-search", f"Wikipedia '{q}'")
            if r:
                r["query"] = q
                return r
            break
        time.sleep(0.15)

    # 3) Wikipedia search theo NGHĨA tiếng Việt (tìm khái niệm tương đương)
    #    YÊU CẦU khớp CHÍNH XÁC — nếu cho "prefix" thì "chạy" sẽ khớp bài
    #    "Chay Bowes" (cầu thủ) ⇒ ảnh sai nghĩa.
    m_head = (meaning_vi or "").split(",")[0].split("(")[0].strip()
    if m_head and len(m_head) > 2 and time.time() <= deadline:
        for host in (wh, "vi.wikipedia.org"):
            for it in fetch_wiki_search_images(m_head, host):
                m = title_matches(m_head, it["title"])
                if m != "exact":
                    continue
                r = _try(it, "medium", "wikipedia-meaning", f"Wikipedia(nghĩa) '{m_head}'")
                if r:
                    r["query"] = m_head
                    return r
                break
            time.sleep(0.15)

    # 4) Wikimedia Commons — yêu cầu từ xuất hiện trong tên file
    for q in cands:
        if time.time() > deadline:
            break
        best = None
        for it in fetch_commons_images(q, limit=8):
            m = title_matches(q, it["title"])
            if not m:
                continue
            best = (it, m)
            break
        if best:
            it, m = best
            conf = "medium" if m in ("exact", "prefix") else "low"
            r = _try(it, conf, "commons", f"Commons '{q}'")
            if r:
                r["query"] = q
                return r
            break
        time.sleep(0.15)

    # 5) Wiktionary
    for q in cands:
        if time.time() > deadline:
            break
        it = fetch_wiki_image(q, wkh)
        if it:
            r = _try(it, "medium", "wiktionary", f"Wiktionary '{q}'")
            if r:
                r["query"] = q
                return r
        for it in fetch_wiki_search_images(q, wkh):
            if not title_matches(q, it["title"]):
                continue
            r = _try(it, "medium", "wiktionary", f"Wiktionary '{q}'")
            if r:
                r["query"] = q
                return r
            break
        time.sleep(0.15)

    # 6) Openverse — fallback cuối (chậm, không ổn định)
    if use_openverse:
        for q in cands:
            for it in fetch_openverse(q, limit=4):
                data, ctype = download_image(it["url"], referer="https://openverse.org/")
                if not data:
                    data, ctype = download_image(it.get("thumbnail") or "",
                                                 referer="https://openverse.org/")
                if data:
                    it = dict(it)
                    it["bytes"] = data
                    it["content_type"] = ctype or "image/jpeg"
                    it["source_tier"] = SOURCE_DICT
                    it["provider"] = "openverse"
                    it["confidence"] = "low"
                    it["query"] = q
                    _log(f"   🖼️  Openverse '{q}' → {it['title']!r} ({len(data)//1024} KB, low)")
                    return it
            time.sleep(0.15)

    _cache_put(language, word, None)       # đã biết: từ này không có ảnh
    return {}


def find_images_for_words(words: list, language: str = "", log_fn=None,
                          max_workers: int = 4, use_openverse: bool = False) -> list:
    """Tìm ảnh cho N từ SONG SONG (ThreadPoolExecutor)."""
    from concurrent.futures import ThreadPoolExecutor
    words = list(words or [])
    if not words:
        return []
    results = [{}] * len(words)

    def _one(i_w):
        i, w = i_w
        try:
            return i, find_image_for_word(
                w.get("word", ""), language,
                w.get("pronunciation", ""), w.get("meaning_vi", ""),
                log_fn=None, use_openverse=use_openverse)
        except Exception:
            return i, {}

    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as ex:
        for i, r in ex.map(_one, list(enumerate(words))):
            results[i] = r
    _save_cache()
    if log_fn:
        for w, r in zip(words, results):
            if r:
                log_fn(f"   🖼️  {w.get('word','')} → {r.get('provider')} "
                       f"({len(r.get('bytes', b''))//1024} KB, {r.get('confidence')})")
            else:
                log_fn(f"   ⚠ Không tìm được ảnh cho '{w.get('word','')}'")
    return results


# ─── CLI kiểm tra nhanh ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tests = [
        {"word": "Apple", "pronunciation": "/ˈæp.əl/", "meaning_vi": "quả táo"},
        {"word": "猫", "pronunciation": "neko", "meaning_vi": "con mèo"},
        {"word": "cat", "pronunciation": "/kæt/", "meaning_vi": "con mèo"},
        {"word": "water", "pronunciation": "/ˈwɔː.tər/", "meaning_vi": "nước"},
        {"word": "book", "pronunciation": "/bʊk/", "meaning_vi": "quyển sách"},
        {"word": "resilient", "pronunciation": "/rɪˈzɪl.jənt/", "meaning_vi": "kiên cường"},
        {"word": "犬", "pronunciation": "inu", "meaning_vi": "con chó"},
    ]
    print("=== batch song song (7 từ) ===")
    res = find_images_for_words(tests, "Tiếng Anh", log_fn=print, max_workers=7)
    ok = sum(1 for r in res if r)
    print(f"\nKẾT QUẢ: {ok}/{len(tests)} từ có ảnh")
    for t, r in zip(tests, res):
        if r:
            print(f"  {t['word']:12s} → {r.get('provider'):18s} {r.get('confidence'):7s} "
                  f"{r.get('title')[:34]!r:38s} {len(r.get('bytes', b''))//1024:4d} KB")
