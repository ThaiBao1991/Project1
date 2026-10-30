"""
test_model_catalog.py — Phase 5: tier/rank/priority/cache của api/model_catalog.py.

LOGIC THUẦN — không gọi mạng (monkeypatch get_catalog), cache ghi vào TEMP.
Chạy: python tools/test_model_catalog.py
"""
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import time

from api import model_catalog as mc  # noqa: E402

PASSED = []


def ok(name):
    PASSED.append(name)
    print(f"[OK] {name}")


# ── 1. infer_tier: quy tắc 2026 (lite check TRƯỚC flash) ──
assert mc.infer_tier("gemini-3.8-pro") == "S"
assert mc.infer_tier("gemini-3.8-flash") == "A"
assert mc.infer_tier("gemini-3.7-flash") == "A"
assert mc.infer_tier("gemini-3.6-flash") == "A"
assert mc.infer_tier("gemini-3.8-flash-lite") == "B"      # lite → B (không phải A)
assert mc.infer_tier("gemini-2.0") == "C"
ok("infer_tier: pro→S · flash(3.6/3.7/3.8)→A · flash-lite→B · khác→C")

# ── 2. preview/exp hạ 1 bậc ──
assert mc.infer_tier("gemini-4.0-pro-preview") == "A"     # S → A
assert mc.infer_tier("gemini-3.8-flash-exp") == "B"       # A → B
assert mc.infer_tier("gemini-3.8-flash-lite-preview") == "C"  # B → C
assert mc.is_preview("gemini-4.0-pro-preview")
assert not mc.is_preview("gemini-3.8-flash")
ok("infer_tier: hậu tố preview/exp hạ 1 bậc (S→A→B→C)")

# ── 3. version_key: chọn 'Mới nhất' cần so được 3.8 vs 3.6 ──
assert mc.version_key("gemini-3.8-flash") == (3, 8)
assert mc.version_key("gemini-3.6-flash") == (3, 6)
assert mc.version_key("gemini") == (0, 0)
ok("version_key: (3,8) > (3,6), không số → (0,0)")

# ── 4. rank_models: 3.8 vùi 3.6 lên đầu; preview/dead xuống cuối ──
names = ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.8-pro",
         "gemini-4.0-flash-preview"]
ranked = mc.rank_models(names)
assert ranked[0] == "gemini-3.8-pro", ranked          # tier S
assert ranked[1] == "gemini-3.8-flash", ranked        # tier A rồi version cao hơn
assert ranked[2] == "gemini-3.6-flash", ranked
assert ranked[3] == "gemini-4.0-flash-preview", ranked  # preview −500
ok("rank_models: 3.8-pro > 3.8-flash > 3.6-flash; preview xuống cuối")

# độ trễ < 800ms được cộng điểm
r_fast = mc.rank_models(["gemini-3.6-flash", "gemini-3.7-flash"],
                        latencies={"gemini-3.6-flash": 400})
assert r_fast[0] == "gemini-3.6-flash", r_fast        # nhanh (<800ms) bù được version
# dead model bị hạ sâu (−10000)
r_dead = mc.rank_models(["gemini-3.8-flash", "gemini-3.6-flash"],
                        dead_names=["gemini-3.8-flash"])
assert r_dead[0] == "gemini-3.6-flash", r_dead
ok("rank_models: latency<800ms cộng điểm · dead model (−10000) chìm xuống")

# ── 5. build_run_priority: menu 4 lựa chọn ──
CATALOG = [{"name": n} for n in ("gemini-3.8-flash", "gemini-3.8-flash-lite",
                                 "gemini-3.6-flash", "gemini-4.0-pro-preview",
                                 "gemini-3.8-pro")]
SAVED = [{"name": "gemini-3.6-flash", "enabled": True}]
mc.get_catalog = (lambda force=False, log=None: list(CATALOG))   # không mạng
old_get = mc.get_catalog
try:
    assert mc.build_run_priority("Tự động", settings_models=SAVED) == []
    ok("build_run_priority: 'Tự động' → [] (không đụng settings)")

    newest = mc.build_run_priority("Mới nhất", settings_models=SAVED)
    assert newest[0] == "gemini-3.8-pro", newest          # 3.8 > 3.6
    # preview (−500) phải xếp SAU model cùng tier không preview
    assert newest.index("gemini-4.0-pro-preview") > newest.index("gemini-3.8-pro")
    assert "gemini-3.6-flash" in newest
    ok("'Mới nhất' → 3.8-pro trên đầu · preview tụt sau 3.8-pro · 3.6 vẫn còn")

    cheap = mc.build_run_priority("Rẻ–nhanh", settings_models=SAVED)
    assert "pro" not in cheap[0], cheap                  # lite/flash đầu
    assert "pro" in cheap[-1] + "" or all("lite" in n or "flash" in n
                                          for n in cheap), cheap
    ok("'Rẻ–nhanh' → lite/flash lên đầu, pro rời khỏi nhóm đầu")

    specific = mc.build_run_priority("gemini-3.8-pro", settings_models=SAVED)
    assert specific[0] == "gemini-3.8-pro", specific
    assert "gemini-3.6-flash" in specific
    ok("tên cụ thể → model chạy đầu, phần sau là rank")

    unknown = mc.build_run_priority("model-không-tồn-tại", settings_models=SAVED)
    assert unknown == [], unknown
    ok("tên lạ → [] (an toàn, không crash)")
finally:
    mc.get_catalog = old_get

# ── 6. dedupe/merge: settings + catalog không lặp tên ──
entries_old = mc.get_catalog
try:
    mc.get_catalog = lambda force=False, log=None: [
        {"name": "gemini-3.6-flash"},  # trùng settings
        {"name": "gemini-3.8-flash"},  # mới
    ]
    got = mc.build_run_priority("Mới nhất", settings_models=SAVED)
    assert got.count("gemini-3.6-flash") == 1, got      # dedupe
    assert "gemini-3.8-flash" in got
finally:
    mc.get_catalog = entries_old
ok("dedupe/merge: settings + catalog không lặp tên")

# ── 7. cache roundtrip 24h (TEMP path) ──
with tempfile.TemporaryDirectory() as tmp:
    old_cache = mc.CACHE_PATH
    mc.CACHE_PATH = os.path.join(tmp, "model_catalog.json")
    try:
        assert mc.read_cache() is None                   # chưa có
        entries = [{"name": "gemini-3.8-flash", "tier": "A"}]
        mc.write_cache(entries)
        c = mc.read_cache()
        assert c and c["models"] == entries, c
        assert mc.read_cache(force=True) is None          # force → bỏ cache
        # hết hạn: fetched_at cách đây 25h
        with open(mc.CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({"fetched_at": time.time() - 25 * 3600, "models": entries}, f)
        assert mc.read_cache() is None                    # hết hạn 24h
        _path = mc.write_cache(entries)
        assert os.path.isfile(_path)
        ok_cache = "cache roundtrip: ghi→đọc khớp · force bỏ qua · quá 24h hết hạn"
    finally:
        mc.CACHE_PATH = old_cache
ok(ok_cache)

# ── 8. _filter_catalog: lọc embed/imagen + chỉ generateContent ──
raw = [
    {"name": "models/gemini-3.8-flash",
     "supportedGenerationMethods": ["generateContent"]},
    {"name": "models/text-embedding-004",
     "supportedGenerationMethods": ["embedContent"]},
    {"name": "models/gemini-3.8-imagen",
     "supportedGenerationMethods": ["generateContent"]},
    {"name": "models/gemini-3.8-flash",       # trùng → dedupe
     "supportedGenerationMethods": ["generateContent"]},
]
filtered = mc._filter_catalog(raw)
names_f = [e["name"] for e in filtered]
assert names_f == ["gemini-3.8-flash"], names_f
ok("_filter_catalog: bỏ embed/imagen, dedupe theo tên")

print(f"\nKet qua: {len(PASSED)}/8 PASS")
if len(PASSED) < 8:
    sys.exit(1)
