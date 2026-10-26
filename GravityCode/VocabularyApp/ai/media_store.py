"""
media_store.py — Lưu trữ media (ảnh minh họa + âm thanh) cho VocabularyApp.

Cấu trúc:
    data/media/<lang_slug>/<day>/word_<idx>_<hash8>.webp
    data/media/<lang_slug>/<day>/audio_<idx>_<hash8>.mp3
    data/media/<lang_slug>/<day>/dialogue_<idx>.mp3
    data/media/index.json          ← manifest (chỉ text, KHÔNG base64)

Nguyên tắc:
  • Manifest chỉ chứa entry cho media THỰC SỰ tồn tại.
  • Mọi ghi file đều atomic (tmp + os.replace).
  • Ảnh được nén WebP 512px quality 80 (PIL đã có sẵn, features.check('webp')==True).
  • Cache theo sha256 ⇒ cùng 1 prompt không gọi lại AI.
"""

import base64
import hashlib
import io
import json

from ai.paths import lang_slug
import os
import shutil
import threading

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_DIR = os.path.join(BASE_DIR, "data", "media")
INDEX_PATH = os.path.join(MEDIA_DIR, "index.json")

# Khoá read-modify-write của manifest.
# Pipeline chạy N ngày SONG SONG ⇒ nếu không khoá, mỗi thread đọc index cũ
# rồi ghi đè → MẤT entry của thread khác (đo thật: 18.500 file ảnh nhưng
# manifest chỉ còn 1.369 entry).
_INDEX_LOCK = threading.RLock()

# Khoá ghi — pipeline chạy N ngày SONG SONG, mỗi ngày lưu ảnh/audio
# ⇒ manifest phải serialize (và load→modify→save phải atomic, tránh mất entry).
_WRITE_LOCK = threading.RLock()

INDEX_FORMAT_VERSION = 1

# Nguồn media — dùng để ghi attribution + fallback logic
SOURCE_AI = "ai"
SOURCE_WEB = "web"
SOURCE_DICT = "dict"
SOURCE_PLACEHOLDER = "placeholder"

_MIME_EXT = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/svg+xml": "svg",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/ogg": "ogg",
    "audio/webm": "webm",
}

try:
    from PIL import Image
    _HAS_PIL = True
    # Pillow 10+ đã XOÁ Image.LANCZOS → phải dùng Image.Resampling.LANCZOS
    _LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS", None)
except Exception:  # pragma: no cover
    _HAS_PIL = False
    _LANCZOS = None


# ─── Đường dẫn ────────────────────────────────────────────────────────────────


def media_dir(lang: str, day=None) -> str:
    d = os.path.join(MEDIA_DIR, lang_slug(lang))
    if day is not None:
        d = os.path.join(d, f"d{int(day):04d}")
    return d


def rel_path_for(lang: str, day, filename: str) -> str:
    """Đường dẫn tương đối so với thư mục data/ (dùng cho web + manifest)."""
    daypart = f"d{int(day):04d}" if day is not None else "_"
    return f"media/{lang_slug(lang)}/{daypart}/{filename}"


def abs_path_for(rel: str) -> str:
    """Đường dẫn tuyệt đối của 1 media theo rel_path ('media/<slug>/<day>/<file>')."""
    rel = (rel or "").replace("/", os.sep)
    if rel.startswith("media" + os.sep):
        rel = rel[len("media") + 1:]
    return os.path.join(MEDIA_DIR, rel)


# ─── Hash ─────────────────────────────────────────────────────────────────────
def hash_key(*parts) -> str:
    """sha256 của các phần → 8 ký tự hex. Ổn định, an toàn cho tên file."""
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p or "").encode("utf-8"))
        h.update(b"\x1f")
    return h.hexdigest()[:8]


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


# ─── Manifest: cache trong RAM + ghi theo LÔ ─────────────────────────────────
# Với 39.532 entry, file manifest ~20 MB JSON. Nếu ghi lại toàn bộ sau MỖI
# media ⇒ 132 lần ghi × 20 MB = 2.6 GB I/O / vòng ngày ⇒ treo.
# → Cache index trong RAM, ghi theo lô (>=100 entry hoặc >=15s), flush tận cùng.
_index_cache = None
_unsaved = 0
_last_flush = 0.0
FLUSH_EVERY_ITEMS = 100
FLUSH_EVERY_SECONDS = 15.0


def load_index() -> dict:
    """Manifest (có cache trong RAM — file có thể tới 20 MB)."""
    global _index_cache
    if _index_cache is not None:
        return _index_cache
    if not os.path.exists(INDEX_PATH):
        _index_cache = {"format_version": INDEX_FORMAT_VERSION, "items": {}}
        return _index_cache
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError
    except Exception:
        data = {"format_version": INDEX_FORMAT_VERSION, "items": {}}
    data.setdefault("format_version", INDEX_FORMAT_VERSION)
    data.setdefault("items", {})
    _index_cache = data
    return data


def save_index(index: dict) -> None:
    """Ghi manifest (atomic) — CÓ retry cho Windows.

    Lý do retry: trên Windows, `os.replace` ném PermissionError nếu file đích
    đang được tiến trình khác mở để đọc. Lỗi này làm MẤT entry manifest
    trong khi file media đã ghi xong ⇒ file "mồ côi" (đo thật: 18.500 file ảnh
    nhưng manifest chỉ còn 1.369 entry).
    """
    import time
    from datetime import datetime
    global _last_flush
    index["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    os.makedirs(MEDIA_DIR, exist_ok=True)
    tmp = INDEX_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    for attempt in range(10):
        try:
            os.replace(tmp, INDEX_PATH)
            _last_flush = time.time()
            return
        except PermissionError:
            time.sleep(0.02 * (attempt + 1))
        except OSError:
            time.sleep(0.05)
    # Hết cách retry → ghi trực tiếp (chấp nhận rủi ro, tốt hơn mất entry)
    try:
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except OSError:
        pass



def _upsert_index(entry: dict) -> None:
    """Thêm/cập nhật 1 entry manifest — ghi theo LÔ (không ghi lại 20 MB mỗi lần)."""
    global _unsaved
    with _WRITE_LOCK:
        index = load_index()
        index.setdefault("items", {})[entry["id"]] = entry
        _unsaved += 1
        import time
        if (_unsaved >= FLUSH_EVERY_ITEMS
                or (time.time() - _last_flush) >= FLUSH_EVERY_SECONDS):
            save_index(index)
            _unsaved = 0


def flush_index() -> int:
    """Ghi ngay manifest ra đĩa. Trả số entry chưa được ghi trước đó."""
    global _unsaved
    with _WRITE_LOCK:
        n = _unsaved
        save_index(load_index())
        _unsaved = 0
    return n


# ─── Reindex: dựng lại manifest từ file trên đĩa (khôi phục file mồ côi) ──
_MIME_BY_EXT = {
    ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png", ".gif": "image/gif", ".mp3": "audio/mpeg",
    ".wav": "audio/wav", ".ogg": "audio/ogg",
}


def reindex(log_fn=None) -> dict:
    """Dựng lại manifest từ toàn bộ file trong data/media/.

    Dùng để khôi phục các file "mồ côi" (đã ghi xong nhưng mất entry manifest
    do race condition trước đây). Giữ lại entry cũ nếu có.
    """
    with _WRITE_LOCK:
        old = load_index()
        old_items = old.get("items") or {}
        new_items = {}
        scanned = 0
        if os.path.isdir(MEDIA_DIR):
            for root, _dirs, files in os.walk(MEDIA_DIR):
                for fn in files:
                    if fn == "index.json" or fn.endswith(".tmp"):
                        continue
                    ext = os.path.splitext(fn)[1].lower()
                    if ext not in _MIME_BY_EXT:
                        continue
                    fp = os.path.join(root, fn)
                    try:
                        size = os.path.getsize(fp)
                    except OSError:
                        continue
                    if size <= 0:
                        continue
                    rel = os.path.relpath(fp, os.path.join(BASE_DIR, "data")).replace(os.sep, "/")
                    sha = file_sha256(fp)
                    ref = "m_" + hash_key(rel, sha)
                    prev = old_items.get(ref) or {}
                    # đoán ngày + ngôn ngữ từ đường dẫn: media/<slug>/dNNNN/<file>
                    parts = rel.split("/")
                    slug = parts[1] if len(parts) > 1 else ""
                    day = None
                    if len(parts) > 2 and parts[2].startswith("d"):
                        try:
                            day = int(parts[2][1:])
                        except ValueError:
                            day = None
                    is_img = ext in (".webp", ".jpg", ".jpeg", ".png", ".gif")
                    new_items[ref] = {
                        "id": ref,
                        "type": "image" if is_img else "audio",
                        "kind": ("vocab_image" if is_img else "vocab_audio"),
                        "lang": prev.get("lang") or slug,
                        "day": prev.get("day") if prev.get("day") is not None else day,
                        "rel_path": rel,
                        "mime": _MIME_BY_EXT.get(ext),
                        "bytes": size,
                        "sha256": sha,
                        "source": prev.get("source") or ("placeholder" if is_img else "tts"),
                        "prompt": prev.get("prompt", ""),
                        "credit": prev.get("credit", ""),
                        "license": prev.get("license", ""),
                        "source_url": prev.get("source_url", ""),
                        "alt": prev.get("alt", ""),
                    }
                    scanned += 1
        new = {"format_version": INDEX_FORMAT_VERSION, "items": new_items}
        global _index_cache, _unsaved
        _index_cache = new
        _unsaved = 0
        save_index(new)
        if log_fn:
            log_fn(f"🔄 Reindex media: quét {scanned} file, manifest {len(new_items)} entry "
                   f"(trước: {len(old_items)}).")
        return {"scanned": scanned, "items": len(new_items), "before": len(old_items)}


def resolve(index: dict, ref: str):
    """Trả entry media theo key, hoặc None."""
    if not ref:
        return None
    items = (index or {}).get("items") or {}
    return items.get(ref)


def ref_exists(index: dict, ref: str) -> bool:
    """True nếu ref có trong manifest VÀ file thật vẫn tồn tại."""
    e = resolve(index, ref)
    return verify_entry(e) if e else False


# ─── Ghi media ────────────────────────────────────────────────────────────────
def _atomic_write_bytes(path: str, raw: bytes) -> int:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(raw)
    os.replace(tmp, path)
    return len(raw)

def _compress_image(raw: bytes, mime: str, max_px: int = 512, quality: int = 80):
    """Nén ảnh về WebP (JPEG fallback nếu PIL thiếu). Trả (bytes, mime, ext)."""
    if not _HAS_PIL or _LANCZOS is None:
        ext = _MIME_EXT.get(mime, "jpg")
        return raw, mime, ext
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in img.mode else "RGB")
        if max(img.size) > max_px:
            img.thumbnail((max_px, max_px), _LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "webp", quality=quality)
        return buf.getvalue(), "image/webp", "webp"
    except Exception as e:
        # Ghi log 1 lần để chẩn đoán (không spam)
        global _compress_warned
        if not _compress_warned:
            _compress_warned = True
            try:
                import sys
                print(f"⚠ Nén WebP thất bại ({type(e).__name__}: {e}) — giữ ảnh gốc.",
                      file=sys.stderr)
            except Exception:
                pass
        ext = _MIME_EXT.get(mime, "jpg")
        return raw, mime, ext


_compress_warned = False


def save_image(lang: str, day, name: str, raw: bytes, mime: str = "image/png",
               source: str = SOURCE_AI, prompt: str = "", credit: str = "",
               license_: str = "", source_url: str = "", alt: str = "",
               max_px: int = 512, quality: int = 80) -> dict:
    """Lưu 1 ảnh, cập nhật manifest, trả entry media."""
    if not raw:
        return {}
    data, out_mime, ext = _compress_image(raw, mime, max_px=max_px, quality=quality)
    filename = name if name.lower().endswith("." + ext) else f"{name}.{ext}"
    path = os.path.join(media_dir(lang, day), filename)
    size = _atomic_write_bytes(path, data)
    rel = rel_path_for(lang, day, filename)

    ref = "m_" + hash_key(rel, file_sha256(path))
    entry = {
        "id": ref,
        "type": "image",
        "kind": "vocab_image",
        "lang": lang,
        "day": int(day) if day is not None else None,
        "rel_path": rel,
        "mime": out_mime,
        "bytes": size,
        "sha256": file_sha256(path),
        "source": source,
        "prompt": prompt,
        "credit": credit,
        "license": license_,
        "source_url": source_url,
        "alt": alt,
    }
    _upsert_index(entry)
    return entry


def save_audio(lang: str, day, name: str, raw: bytes, mime: str = "audio/mpeg",
               source: str = SOURCE_AI, text: str = "", engine: str = "",
               voice: str = "", rate: str = "", duration_ms: int = 0,
               kind: str = "vocab_audio") -> dict:
    """Lưu 1 file âm thanh, cập nhật manifest, trả entry media."""
    if not raw:
        return {}
    ext = _MIME_EXT.get(mime, "mp3")
    filename = name if name.lower().endswith("." + ext) else f"{name}.{ext}"
    path = os.path.join(media_dir(lang, day), filename)
    size = _atomic_write_bytes(path, raw)
    rel = rel_path_for(lang, day, filename)

    ref = "m_" + hash_key(rel, file_sha256(path))
    entry = {
        "id": ref,
        "type": "audio",
        "kind": kind,
        "lang": lang,
        "day": int(day) if day is not None else None,
        "rel_path": rel,
        "mime": mime,
        "bytes": size,
        "sha256": file_sha256(path),
        "source": source,
        "text": text,
        "engine": engine,
        "voice": voice,
        "rate": rate,
        "duration_ms": int(duration_ms or 0),
    }
    _upsert_index(entry)
    return entry


def save_b64_image(lang: str, day, name: str, b64: str, mime: str = "image/png", **kw) -> dict:
    """Tiện ích: nhận base64 (từ Gemini inlineData hoặc addon) → lưu."""
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return {}
    return save_image(lang, day, name, raw, mime=mime, **kw)


def save_image_bytes(lang: str, day, name: str, raw: bytes, mime: str = "image/png", **kw) -> dict:
    """Lưu ảnh từ RAW BYTES (đã tải sẵn) — KHÔNG base64-decode."""
    if not raw:
        return {}
    return save_image(lang, day, name, raw, mime=mime, **kw)


# ─── Kiểm tra tồn tại ────────────────────────────────────────────────────────
def verify_entry(entry: dict) -> bool:
    if not entry:
        return False
    rel = entry.get("rel_path")
    if not rel:
        return False
    path = abs_path_for(rel)
    try:
        return os.path.isfile(path) and os.path.getsize(path) > 0
    except OSError:
        return False


def prune_missing(index: dict) -> int:
    """Xoá entry manifest mà file đã không còn. Trả số entry bị xoá."""
    with _WRITE_LOCK:
        items = index.get("items") or {}
        dead = [k for k, v in items.items() if not verify_entry(v)]
        for k in dead:
            items.pop(k, None)
        if dead:
            save_index(index)
        return len(dead)


def total_bytes() -> int:
    total = 0
    for root, _dirs, files in os.walk(MEDIA_DIR):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def copy_dir(src: str, dst: str) -> int:
    """Copy thư mục media (dùng khi sync có chọn lọc). Trả số file."""
    if not os.path.isdir(src):
        return 0
    n = 0
    for root, _dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        target = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(target, exist_ok=True)
        for f in files:
            shutil.copy2(os.path.join(root, f), os.path.join(target, f))
            n += 1
    return n
