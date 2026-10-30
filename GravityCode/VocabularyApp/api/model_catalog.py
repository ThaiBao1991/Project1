"""
model_catalog.py — Catalog model Gemini thật (GET /v1beta/models) + tiền hạng.

Khắc phục: fallback log lặp 3.6→3.5 vì _infer_tier cũ (thời 3.5) xếp
3.6/3.7/3.8/4-argon/pro-latest hết tier C ⇒ model mới không được ưu tiên.

Chức năng:
  • fetch_catalog(key): GET /v1beta/models?pageSize=200 (lặp trang bằng
    next_page_token, tối đa 3 trang), lọc generateContent + loại
    embed/imagen/audio/…; cache 24h → data/model_catalog.json.
  • infer_tier(name): quy tắc 2026 — `pro` → S · `lite` → B · `flash` → A ·
    còn lại C (check "lite" TRƯỚC "flash" vì "flash-lite"); hậu tố
    -preview/-exp/-alpha/-beta/-lite-preview hạ 1 bậc (S→A→B→C).
  • version_key/ rank_models: tier + version + độ trễ đã đo + dead-model
    (pipeline_store.dead_models) ⇒ chọn "Mới nhất" luôn vùi 3.8 lên đầu.
  • build_run_priority(choice): menu Tự động/Mới nhất/Ổn định/Rẻ–nhanh/<tên>
    → danh sách model fallback cho 1 lần chạy (không ghi đè settings).

Cú pháp:
  python -m api.model_catalog --status    # liệt kê cache + tier
  python -m api.model_catalog --refresh   # gọi API dò mới (cần key)
"""

import json
import os
import re
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(BASE_DIR, "data", "model_catalog.json")
CACHE_TTL = 24 * 3600                    # 24 giờ

EXCLUDE_SUBSTR = ("embed", "vision", "imagen", "image", "audio", "tts",
                  "transcribe", "robotics", "aistudio", "desktop", "veo",
                  "gemini-3.8-flash-tts")
_PREVIEW_HINT = ("-preview", "-exp", "-alpha", "-beta", "-internal")

_TIER_BONUS = {"S": 4000.0, "A": 3000.0, "B": 2000.0, "C": 1000.0}


# ─── Tier & version ──────────────────────────────────────────────────────────
def infer_tier(name: str) -> str:
    """'gemini-3.8-flash' → A · '…-pro' → S · '…-flash-lite' → B · khác → C.

    Cùng tier hậu tố đặc biệt (preview/exp/…) bị HẠ XUỐNG 1 bậc.
    (Quy tắc dùng chung: _TIER_META trên dialog cùng thứ tự S > A > B > C.)
    """
    n = (name or "").lower()
    if "pro" in n:
        t = "S"
    elif "lite" in n:                       # "flash-lite" vẫn là lite
        t = "B"
    elif "flash" in n:
        t = "A"
    else:
        t = "C"
    if any(h in n for h in _PREVIEW_HINT) or n.endswith("-fp-latest"):
        t = _demote(t)
    return t


def _demote(t: str) -> str:
    return {"S": "A", "A": "B", "B": "C", "C": "C"}.get(t, t)


def version_key(name: str):
    """'gemini-3.8-flash' → (3, 8); không có số → (0, 0). Dùng để chọn 'Mới nhất'."""
    m = re.search(r"(\d+)\.(\d+)", (name or "").lower())
    if m:
        try:
            return (int(m.group(1)), int(m.group(2)))
        except ValueError:
            pass
    m2 = re.search(r"\b(\d{3,})\b", (name or "").lower())
    if m2:
        try:
            v = int(m2.group(1))
            return (v, 0)
        except ValueError:
            pass
    return (0, 0)


def is_preview(name: str) -> bool:
    n = (name or "").lower()
    return any(h in n for h in _PREVIEW_HINT)


def _looks_deprecated(name: str) -> bool:
    n = (name or "").lower()
    return "deprecated" in n or "retire" in n


def rank_models(names, latencies: dict = None, dead_names=None,
                preview_last=True) -> list:
    """Sắp: tier (S>A>B>C) + version + độ trễ đo được + trừ điểm dead/preview.

    Trả list tên model (mới đầu — chạy đầu tiên => tránh lặp fallback cũ).
    """
    latencies = latencies or {}
    dead = set(dead_names or [])
    def _score(n):
        t = infer_tier(n)
        s = _TIER_BONUS.get(t, 0.0)
        maj, mnr = version_key(n)
        s += maj * 100.0 + mnr
        lat = latencies.get(n)
        if isinstance(lat, (int, float)) and lat > 0:
            s += 600.0 if lat < 800 else 300.0
        if is_preview(n) and preview_last:
            s -= 500.0
        if n in dead or _looks_deprecated(n):
            s -= 10000.0
        return s
    return sorted({str(n) for n in names}, key=_score, reverse=True)


# ─── Fetch + cache ───────────────────────────────────────────────────────────
def read_cache(force: bool = False):
    """Cache 24h — trả None nếu hết hạn/không có/bị ép force."""
    try:
        if os.path.isfile(CACHE_PATH):
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                c = json.load(f)
            got = float(c.get("fetched_at") or 0)
            if got and (time.time() - got) < CACHE_TTL and not force:
                return c
    except Exception:
        pass
    return None


def write_cache(models: list) -> str:
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        tmp = CACHE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"fetched_at": time.time(),
                       "tmod": time.strftime("%Y-%m-%d %H:%M"),
                       "models": models}, f, ensure_ascii=False, indent=1)
        os.replace(tmp, CACHE_PATH)
    except Exception:
        pass
    return CACHE_PATH


def _filter_catalog(raw_models: list) -> list:
    """Chuẩn hoá entry + lọc model KHÔNG phù hợp sinh content."""
    out = []
    for m in raw_models or []:
        name = str(m.get("name") or "").replace("models/", "")
        methods = m.get("supportedGenerationMethods") or []
        if "generateContent" not in methods:
            continue
        n = name.lower()
        if any(x in n for x in EXCLUDE_SUBSTR):
            continue
        out.append({
            "name": name,
            "display": m.get("displayName") or name,
            "tier": infer_tier(name),
            "version": "%d.%d" % version_key(name),
            "preview": is_preview(name),
            "deprecated": _looks_deprecated(name),
        })
    # dedupe theo tên
    seen, ded = set(), []
    for e in out:
        if e["name"] not in seen:
            seen.add(e["name"])
            ded.append(e)
    return ded


def fetch_catalog(api_key: str, timeout: int = 25, log=None) -> list:
    """GET phân trang; trả entries đã lọc. Raise khi mạng/HTTP lỗi."""
    import requests
    entries, page_token, pages = [], "", 0
    base = "https://generativelanguage.googleapis.com/v1beta/models"
    while pages < 3:
        params = {"key": api_key, "pageSize": 200}
        if page_token:
            params["pageToken"] = page_token
        r = requests.get(base, params=params, timeout=timeout)
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:160]}")
        body = r.json() or {}
        entries += _filter_catalog(body.get("models") or [])
        page_token = body.get("nextPageToken") or ""
        pages += 1
        if not page_token:
            break
    if log:
        log(f"🌐 Catalog: {len(entries)} model sinh nội dung (đã lọc).")
    return entries


def get_catalog(api_key: str = None, force: bool = False, log=None) -> list:
    """Cache 24h trước, hết hạn mới fetch. Không key/mất mạng → cache cũ."""
    c = read_cache(force=force)
    if c is not None:
        return c.get("models") or []
    if not api_key:
        api_key = first_active_key()
    if not api_key:
        if log:
            log("⚠ Không có key — dùng cache cũ nếu có.")
        return (read_cache(force=False) or {}).get("models") or []
    try:
        entries = fetch_catalog(api_key, log=log)
    except Exception as e:
        if log:
            log(f"⚠ Fetch catalog lỗi ({e}); dùng cache cũ nếu có.")
        return (read_cache(force=False) or {}).get("models") or []
    write_cache(entries)
    return entries


def first_active_key() -> str:
    """Lấy 1 key active (course_generator._load_gemini_keys — 1 nguồn dùng chung)."""
    try:
        from ai.course_generator import _load_gemini_keys
        import time as _t
        now = _t.time()
        for k in (_load_gemini_keys() or []):
            if k.get("status", "active") == "active" and \
                    k.get("cooldown_until", 0) <= now and k.get("key"):
                return k.get("key")
    except Exception:
        pass
    return ""


# ─── Menu chọn model cho CourseGenerationDialog ──────────────────────────────
def build_run_priority(choice: str, settings_models: list = None,
                       latencies: dict = None, dead_names=None) -> list:
    """'Tự động' → [] (không đụng). 'Mới nhất'/'Ổn định'/'Rẻ–nhanh'/<tên>
    → list tên model cho 1 lần chạy GeminiCoordinator."""
    lat = latencies or {}
    dead = dead_names or []
    choice = (choice or "").strip()
    if not choice or choice in ("Tự động", "Auto"):
        return []
    saved = [str(m.get("name")) for m in (settings_models or [])
             if str(m.get("name"))]
    cat = [e["name"] for e in get_catalog(force=False)]
    names = list(dict.fromkeys(saved + [n for n in cat if n not in saved]))
    if choice == "Mới nhất":
        return rank_models(names, latencies=lat, dead_names=dead,
                           preview_last=True)
    if choice == "Ổn định":
        stable = [n for n in names if (lat.get(n) or 0) > 0
                  or not is_preview(n)]
        return rank_models(stable or names, latencies=lat, dead_names=dead)
    if choice in ("Rẻ–nhanh", "Rẻ - nhanh"):
        cheap = [n for n in names if "lite" in n.lower() or "flash" in n.lower()]
        return rank_models(cheap or names, latencies=lat, dead_names=dead)
    # <Tên cụ thể> — model chọn chạy ĐẦU, phần sau giữ rank thông thường
    pick = [n for n in names if normalize_name(n) == normalize_name(choice)]
    if not pick:
        return []
    rest = [n for n in names if normalize_name(n) != normalize_name(pick[0])]
    return pick + rank_models(rest, latencies=lat, dead_names=dead,
                              preview_last=True)


def normalize_name(n: str) -> str:
    return (n or "").strip().lower()


# ─── CLI ────────────────────────────────────────────────────────────────────
def _log_default(m):
    print(m)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import argparse
    ap = argparse.ArgumentParser(prog="api.model_catalog")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--rank", action="store_true", help="Xếp hạng từ settings")
    args = ap.parse_args()

    if args.refresh:
        entries = get_catalog(force=True, log=_log_default)
        print(f"Có {len(entries)} entry — cache {CACHE_PATH}")
        for e in entries[:15]:
            print(f"  [{e['tier']}] {e['name']:36} v{e['version']}"
                  + (" (preview)" if e["preview"] else ""))
        return 0

    c = read_cache()
    if not c:
        print("Cache trống — chạy `--refresh` hoặc để app dò qua UI.")
        return 0
    print(f"Cache cập nhật: {c.get('tmod')} — {len(c.get('models', []))} model")
    if args.rank:
        try:
            from settings import load_settings
            saved = load_settings().get("ai", {}).get("model_priority") or []
            lat = {m.get("name"): (m.get("latency_ms") or 0)
                   for m in saved if m.get("name")}
            names = [m.get("name") for m in saved if m.get("name")]
            for n in rank_models(names, latencies=lat):
                print(f"  [{infer_tier(n)}] {n}")
        except Exception as e:
            print(f"⚠ rank lỗi: {e}")
    else:
        for e in (c.get("models") or [])[:15]:
            print(f"  [{e['tier']}] {e['name']:36} v{e['version']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
