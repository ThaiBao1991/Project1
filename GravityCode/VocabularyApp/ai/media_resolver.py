"""
media_resolver.py — GIẢI 1 media ref thành đường dẫn file thật / URL web.

Dùng chung cho desktop (VocabApp.py) + web (data/... relative path). Chấp nhận:

  1. "m_<hash8>"             → tra manifest data/media/index.json (media_store)
  2. "media/<slug>/d.../x"   → rel_path tương đối so với data/ (ghi trong manifest)
  3. "audio/<slug>/.../x"    → kho audio flat (TTS cache) tương đối so với data/
  4. đường dẫn tuyệt đối     → giữ nguyên nếu tồn tại trên đĩa
  5. ref lạ / thiếu file     → "" (renderer tự fallback sang TTS hoặc ẩn)

An toàn (5 test: m_* · rel · abs · thiếu · traversal):
  • chặn thu mục bậc cao (..) — phần trả về "" dù file tồn tại
  • đường dẫn rel PHẢI nằm trong thư mục data/ của app
  • không chấp nhận URL http(s) (renderer web tự xử lý)
"""

import os

from ai import media_store
from ai.paths import DATA_DIR

_SEPARATOR_ATTEMPT = ("/", os.sep)


def _normalize(rel: str) -> str:
    """Chuẩn hoá phân cách; trả '' nếu có dấu hiệu traversal."""
    r = (rel or "").strip()
    if not r:
        return ""
    if "\x00" in r:
        return ""
    for sep in _SEPARATOR_ATTEMPT:
        r = r.replace(sep, os.sep)
    try:
        norm = os.path.normpath(r)
    except (ValueError, TypeError):
        return ""
    if norm.split(os.sep, 1)[0] == ".." or norm.startswith("..%s" % os.sep):
        return ""
    if os.path.isabs(norm):
        return ""
    return norm


def _contained_in(base: str, path: str) -> bool:
    """path có nằm trong base (đã absolute) không? Chống traversal."""
    try:
        base_n = os.path.abspath(base)
        path_n = os.path.abspath(path)
        return os.path.commonpath([base_n, path_n]) == base_n
    except (ValueError, OSError):
        return False


def media_entry(ref, index: dict = None) -> dict:
    """Entry manifest của ref (m_*), hoặc {} nếu không có."""
    r = str(ref or "").strip()
    if not r.startswith("m_"):
        return {}
    try:
        if index is None:
            index = media_store.load_index()
        return (index.get("items") or {}).get(r) or {}
    except Exception:
        return {}


def resolve_media_path(ref, index: dict = None) -> str:
    """Đường dẫn TUYỆT ĐỐI trên đĩa, hoặc '' nếu không tồn tại / không hợp lệ."""
    r = str(ref or "").strip()
    if not r or "\x00" in r:
        return ""
    if r.lower().startswith(("http://", "https://")):
        return ""

    # 1) ref hash của manifest
    if r.startswith("m_"):
        entry = media_entry(r, index)
        rel = entry.get("rel_path") or ""
        if not rel:
            return ""
        return resolve_media_path(rel, index)

    # 4) đường dẫn tuyệt đối (do bước pipeline/media_verify tạo trước đó)
    if os.path.isabs(r):
        try:
            return r if os.path.isfile(r) else ""
        except (OSError, ValueError):
            return ""

    # 2/3) path tương đối — PHẢI nằm trong data/
    norm = _normalize(r)
    if not norm:
        return ""
    path = os.path.join(DATA_DIR, norm)
    if not _contained_in(DATA_DIR, path):
        return ""
    return path if os.path.isfile(path) else ""


def resolve_media_url(ref, index: dict = None) -> str:
    """URL web ('data/<rel_path>') cho ref hợp lệ, phục vụ web/script.js."""
    r = str(ref or "").strip()
    if not r or r.lower().startswith(("http://", "https://")):
        return ""
    if r.startswith("m_"):
        entry = media_entry(r, index)
        if not entry:
            return ""
        if entry.get("url"):
            return str(entry["url"])
        r = entry.get("rel_path") or ""
        if not r:
            return ""
    if os.path.isabs(r):
        return ""
    norm = _normalize(r)
    if not norm or ".." in norm:
        return ""
    # chỉ chấp nhận path bên dưới data/media hoặc data/audio
    first = norm.split(os.sep, 1)[0]
    if first not in ("media", "audio"):
        return ""
    return "data/" + norm.replace(os.sep, "/")


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for probe in ("m_khontontai", "media/x/d0001/a.png", "..%smedia" % os.sep,
                  "etc/passwd", "c:%sbill.doc" % os.sep, "audio/nhật/x.mp3"):
        print(f"{probe!r:35} → path={resolve_media_path(probe)!r} "
              f"url={resolve_media_url(probe)!r}")
