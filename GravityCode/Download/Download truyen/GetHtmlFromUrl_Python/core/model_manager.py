import os
import json
import time
import requests
from typing import List, Dict, Tuple, Optional, Callable

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
MODEL_PRIORITY_FILE = os.path.join(CONFIG_DIR, "model_priority.json")

# ── Tier metadata chuẩn theo AskCpl ─────────────────────────────
TIER_META = {
    "S": {"color": "#e74c3c", "badge": "🔴 S", "score_bonus": 500, "desc": "Mới nhất, siêu nhanh & chất lượng cao"},
    "A": {"color": "#e67e22", "badge": "🟠 A", "score_bonus": 300, "desc": "Ổn định, mạnh mẽ, phù hợp văn học"},
    "B": {"color": "#f1c40f", "badge": "🟡 B", "score_bonus": 100, "desc": "Bản Lite, nhẹ và nhanh"},
    "C": {"color": "#95a5a6", "badge": "⚪ C", "score_bonus":   0, "desc": "Bản thử nghiệm hoặc model khác"}
}

DEFAULT_MODEL_FALLBACKS = [
    {"name": "gemini-3.8-flash",         "enabled": True, "tier": "S", "note": "Mới nhất — Gemini 3.8 Flash",   "latency_ms": 0},
    {"name": "gemini-3.5-flash-lite",    "enabled": True, "tier": "S", "note": "Siêu tốc — Gemini 3.5 Lite",    "latency_ms": 0},
    {"name": "gemini-3.5-flash",         "enabled": True, "tier": "S", "note": "Mạnh mẽ — Gemini 3.5 Flash",   "latency_ms": 0},
    {"name": "gemini-3-flash-preview",   "enabled": True, "tier": "A", "note": "Rất tốt — Gemini 3 Preview",    "latency_ms": 0},
    {"name": "gemini-flash-latest",      "enabled": True, "tier": "A", "note": "Ổn định — Flash Latest",        "latency_ms": 0},
    {"name": "gemini-flash-lite-latest", "enabled": True, "tier": "B", "note": "Nhanh nhẹ — Flash Lite Latest", "latency_ms": 0},
    {"name": "gemini-3.1-flash-lite",    "enabled": True, "tier": "B", "note": "Nhẹ & Nhanh — Gemini 3.1 Lite", "latency_ms": 0},
    {"name": "gemini-3.7-flash",         "enabled": True, "tier": "A", "note": "Dự phòng — Gemini 3.7 Flash",   "latency_ms": 0}
]


def infer_tier(name: str) -> str:
    """Tự động suy luận hạng Tier dựa trên tên model."""
    n = name.lower()
    if "3.8" in n or "3.5" in n or "3-ultra" in n:
        return "S"
    if "3.7" in n or "3.6" in n or "3-flash" in n or "3.0" in n or "flash-latest" in n:
        return "A"
    if "lite" in n or "3.1" in n:
        return "B"
    return "C"


def load_model_priority() -> List[Dict]:
    """Tải cấu hình thứ tự ưu tiên model từ config/model_priority.json."""
    if os.path.exists(MODEL_PRIORITY_FILE):
        try:
            with open(MODEL_PRIORITY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    return data
        except Exception:
            pass
    # Trả về danh sách mặc định
    return [dict(m) for m in DEFAULT_MODEL_FALLBACKS]


def save_model_priority(models: List[Dict]) -> bool:
    """Lưu cấu hình thứ tự model vào config/model_priority.json."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(MODEL_PRIORITY_FILE, "w", encoding="utf-8") as f:
            json.dump(models, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_active_models() -> List[str]:
    """Lấy danh sách các model đang bật (enabled=True) theo thứ tự ưu tiên."""
    models = load_model_priority()
    active = [m["name"] for m in models if m.get("enabled", True)]
    if not active:
        active = [m["name"] for m in DEFAULT_MODEL_FALLBACKS]
    return active


def auto_discover_and_benchmark(
    api_key: str,
    existing_models: Optional[List[Dict]] = None,
    stop_flag: Optional[List[bool]] = None,
    log_callback: Optional[Callable[[str], None]] = None
) -> List[Dict]:
    """Gọi Google API /v1beta/models để tự động phát hiện tất cả các model Gemini mới,
    sau đó benchmark đo độ trễ thực tế, chấm điểm và tự động sắp xếp (chuẩn AskCpl).
    """
    def _log(msg: str):
        if log_callback:
            log_callback(msg)

    if stop_flag is None:
        stop_flag = [False]

    if not api_key:
        _log("❌ Chưa có API key hợp lệ để quét.")
        return existing_models or load_model_priority()

    # ── Bước 1: GET /v1beta/models ──────────────────────
    _log("🌐 Bước 1: Gọi GET /v1beta/models để khám phá danh sách model trên Google Cloud...")
    try:
        resp = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}&pageSize=100",
            timeout=20
        )
        if resp.status_code != 200:
            _log(f"⚠️ Google API trả về HTTP {resp.status_code}: {resp.text[:120]}")
            return existing_models or load_model_priority()
        raw_list = resp.json().get("models", [])
    except Exception as e:
        _log(f"❌ Không kết nối được với Google API: {e}")
        return existing_models or load_model_priority()

    # Lọc model hỗ trợ generateContent & loại trừ model chuyên biệt hình ảnh/âm thanh/robotics
    discovered = []
    for m in raw_list:
        mname = m.get("name", "").replace("models/", "")
        supported = m.get("supportedGenerationMethods", [])
        if "generateContent" not in supported:
            continue
        n = mname.lower()
        if "flash" not in n and "gemini" not in n:
            continue
        if any(x in n for x in ("embed", "vision", "imagen", "thinking", "image", "transcribe", "audio", "tts", "robotics", "er-2", "computer-use")):
            continue
        discovered.append(mname)

    _log(f"✅ Tìm thấy {len(discovered)} model văn bản: {', '.join(discovered[:6])}{'...' if len(discovered) > 6 else ''}")

    if not discovered:
        return existing_models or load_model_priority()

    # ── Bước 2: Benchmark đo độ trễ từng model ───────────────────
    _log(f"⏱ Bước 2: Đo độ trễ (latency) từng model với prompt ngắn 'Hi'...")
    payload = {
        "contents": [{"parts": [{"text": "Hi"}]}],
        "generationConfig": {"maxOutputTokens": 3}
    }
    results = {}  # mname -> latency_ms

    for mname in discovered:
        if stop_flag[0]:
            _log("🛑 Người dùng đã yêu cầu dừng quét.")
            break

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{mname}:generateContent?key={api_key}"
        try:
            t0 = time.time()
            r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=12)
            ms = int((time.time() - t0) * 1000)
            if r.status_code == 200:
                results[mname] = ms
                _log(f"  ✅ {mname}: {ms}ms (HTTP 200)")
            elif r.status_code == 429:
                results[mname] = -2  # Quota limit tạm
                _log(f"  ⚠️ {mname}: Bị 429 Rate Limit (tạm thời hạn chế)")
            elif r.status_code in (404, 400):
                results[mname] = -3
                _log(f"  ✗ {mname}: HTTP {r.status_code} (Không khả dụng với key này)")
            else:
                results[mname] = -1
                _log(f"  ✗ {mname}: HTTP {r.status_code}")
        except requests.exceptions.Timeout:
            results[mname] = -4
            _log(f"  ⏱ {mname}: Timeout >12s")
        except Exception as ex:
            results[mname] = -1
            _log(f"  ✗ {mname}: {ex}")

        time.sleep(0.4)  # Nghỉ nhẹ giữa các request tránh spam tần số cao

    # ── Bước 3: Cập nhật danh sách & tính điểm xếp hạng ───────────────────
    _log("🔄 Bước 3: Đánh giá phân hạng Tier và chấm điểm xếp hạng...")
    models_dict = {m["name"]: dict(m) for m in (existing_models or load_model_priority())}

    for mname, ms in results.items():
        tier = infer_tier(mname)
        if ms > 0:
            note_suffix = f"({ms}ms)"
        elif ms == -2:
            note_suffix = "(Rate limit)"
        elif ms == -3:
            note_suffix = "(Không khả dụng)"
        elif ms == -4:
            note_suffix = "(Timeout)"
        else:
            note_suffix = "(Lỗi)"

        if mname in models_dict:
            models_dict[mname]["latency_ms"] = max(ms, 0)
            models_dict[mname]["tier"] = tier
            models_dict[mname]["note"] = f"Tier {tier} — {note_suffix}"
            if ms > 0:
                models_dict[mname]["enabled"] = True
        else:
            # Model mới khám phá được
            models_dict[mname] = {
                "name": mname,
                "enabled": ms > 0,
                "tier": tier,
                "note": f"[Mới] Tier {tier} — {note_suffix}",
                "latency_ms": max(ms, 0)
            }

    updated_models = list(models_dict.values())

    # Thuật toán tính điểm (AskCpl Formula): Tier Bonus + Speed (1000 / latency_ms)
    def _calc_score(m):
        ms_val = m.get("latency_ms", 0)
        t_bonus = TIER_META.get(m.get("tier", "C"), TIER_META["C"])["score_bonus"]
        spd = (1000 / ms_val) if ms_val > 0 else 0
        return t_bonus + spd

    updated_models.sort(key=_calc_score, reverse=True)
    save_model_priority(updated_models)

    _log(f"🎉 Hoàn tất đánh giá {len(updated_models)} model! Đã tự động xếp hạng model tối ưu nhất lên đầu.")
    return updated_models
