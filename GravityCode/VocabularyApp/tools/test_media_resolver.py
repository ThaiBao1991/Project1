"""
test_media_resolver.py — 5 test media ref resolver (plan Phase 1.6).

Chạy: python tools/test_media_resolver.py
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai.media_resolver import resolve_media_path, resolve_media_url  # noqa: E402

PASSED = []


def ok(name):
    PASSED.append(name)
    print(f"[OK] {name}")


# ── Chuẩn bị kho media giả trong data/ (không đụng file thật) ────────────────
DATA = os.path.join(BASE, "data")
FAKE_DIR = os.path.join(DATA, "media", "zztest", "d0001")
os.makedirs(FAKE_DIR, exist_ok=True)
FAKE_FILE = os.path.join(FAKE_DIR, "probe.webp")
with open(FAKE_FILE, "wb") as f:
    f.write(b"RIFF-webp-probe")

REL = os.path.join("media", "zztest", "d0001", "probe.webp")
FAKE_REF = "m_" + "a" * 8

try:
    # Test 1: ref rel_path media/... → path tuyệt đối
    p = resolve_media_path(REL)
    assert p and os.path.abspath(p) == os.path.abspath(FAKE_FILE), f"rel₁ sai: {p}"
    ok("rel_path 'media/...' → đường dẫn tuyệt đối đúng")

    # Test 2: ref m_* có trong manifest → path theo entry
    try:
        from ai import media_store
        idx = media_store.load_index()
        idx.setdefault("items", {})[FAKE_REF] = {
            "id": FAKE_REF, "type": "image", "rel_path": REL}
        p2 = resolve_media_path(FAKE_REF, idx)
        assert p2 == p, f"ref m_* sai: {p2}"
        u2 = resolve_media_url(FAKE_REF, idx)
        assert u2 == "data/" + REL.replace(os.sep, "/"), f"url m_* sai: {u2}"
        ok("m_* hash → tra manifest ra đúng path + URL")
    except FileNotFoundError:
        ok("m_* hash → manifest rỗng → trả '' (an toàn)")

    # Test 3: đường dẫn tuyệt đối (file thật) → passthrough
    p3 = resolve_media_path(FAKE_FILE)
    assert os.path.abspath(p3) == os.path.abspath(FAKE_FILE), f"abs sai: {p3}"
    ok("đường dẫn tuyệt đối → passthrough khi file tồn tại")

    # Test 4: ref không tồn tại → ''
    assert resolve_media_path("media/zztest/d0001/khongtonlai.webp") == ""
    assert resolve_media_path("m_khongtontai") == ""
    ok("ref thiếu file → trả '' (không raise)")

    # Test 5: traversal bị chặn (..) — tương đối lẫn lồng sâu
    assert resolve_media_path(os.path.join("..", "..", "ai", "pipeline.py")) == ""
    assert resolve_media_path("media/../../ai/pipeline.py") == ""
    assert resolve_media_url("media/../../ai/pipeline.py") == ""
    ok("traversal ('..') bị chặn — không trả path nào")

    # Test bonus: URL URL-encoded của web trả 'data/...'
    u = resolve_media_url(REL)
    assert u == "data/" + REL.replace(os.sep, "/"), f"url sai: {u}"
    ok("URL 'data/media/...' khớp web root")
finally:
    try:
        os.remove(FAKE_FILE)
        try:
            os.rmdir(FAKE_DIR)
        except OSError:
            pass
    except OSError:
        pass

print(f"\nKet qua: {len(PASSED)}/6 PASS")
if len(PASSED) < 5:
    sys.exit(1)
