"""
tts_config.py — Bảng cấu hình giọng đọc đa ngôn ngữ (dùng chung desktop + web).

Đã kiểm chứng trên máy (2026-10-21):
  • Gemini TTS  gemini-3.8-flash-tts  → audio/wav           ✅ (vi/ja/zh/ko/en đều OK)
  • Gemini TTS  gemini-3.8-flash-lite-tts → audio/wav       ✅
  • Gemini TTS  gemini-2.5-flash-preview-tts → audio/L16 PCM 24000 ✅
  • edge-tts    (cần cài edge-tts>=7.3) — neural, 10/10 ngôn ngữ
  • gTTS        2.5.4 (đã có) — 10/10 ngôn ngữ, chỉ 2 mức tốc độ
  • pyttsx3     2.99 (đã có) — SAPI5; máy này CHỈ có en-US×2 + ja-JP×1
                 → 8/10 ngôn ngữ KHÔNG có giọng offline ⇒ TUYỆT ĐỐI không
                   fallback sang giọng Anh.

Bảng voice Gemini TTS (prebuilt): Puck, Charon, Kore, Fenrir, Aoede, Leda,
Orus, Zephyr, Sulafat, Vindemir, Sadachiel, Sadaltager, Iapetus...
"""

import os

# ─── Cấu hình giọng theo ngôn ngữ ───────────────────────────────────────────
# gemini_voice : voice prebuilt của Gemini TTS
# edge_voice   : voice neural của edge-tts
# gtts_lang    : mã lang của gTTS
# sapi_voices  : danh sách voice SAPI5 khớp (nếu máy có)
# stages       : tốc độ đọc theo 6 chặng học
LANG_VOICES = {
    "Tiếng Anh": {
        "gemini_voice": "Kore", "edge_voice": "en-US-AriaNeural",
        "gtts_lang": "en", "sapi": ["en-US"],
    },
    "Tiếng Nhật": {
        "gemini_voice": "Puck", "edge_voice": "ja-JP-NanamiNeural",
        "gtts_lang": "ja", "sapi": ["ja-JP"],
    },
    "Tiếng Trung": {
        "gemini_voice": "Charon", "edge_voice": "zh-CN-XiaoxiaoNeural",
        "gtts_lang": "zh-CN", "sapi": [],
    },
    "Tiếng Hàn Quốc": {
        "gemini_voice": "Fenrir", "edge_voice": "ko-KR-SunHiNeural",
        "gtts_lang": "ko", "sapi": [],
    },
    "Tiếng Pháp": {
        "gemini_voice": "Aoede", "edge_voice": "fr-FR-DeniseNeural",
        "gtts_lang": "fr", "sapi": [],
    },
    "Tiếng Đức": {
        "gemini_voice": "Sadaltager", "edge_voice": "de-DE-KatjaNeural",
        "gtts_lang": "de", "sapi": [],
    },
    "Tiếng Nga": {
        "gemini_voice": "Aoede", "edge_voice": "ru-RU-SvetlanaNeural",
        "gtts_lang": "ru", "sapi": [],
    },
    "Tiếng Tây Ban Nha": {
        "gemini_voice": "Leda", "edge_voice": "es-ES-ElviraNeural",
        "gtts_lang": "es", "sapi": [],
    },
    "Tiếng Thái": {
        "gemini_voice": "Sulafat", "edge_voice": "th-TH-PremwadeeNeural",
        "gtts_lang": "th", "sapi": [],
    },
    "Tiếng Ả Rập": {
        "gemini_voice": "Orus", "edge_voice": "ar-SA-ZariyahNeural",
        "gtts_lang": "ar", "sapi": [],
    },
    "Tiếng Việt": {
        "gemini_voice": "Kore", "edge_voice": "vi-VN-HoaiMyNeural",
        "gtts_lang": "vi", "sapi": [],
    },
}

DEFAULT_VOICE = LANG_VOICES["Tiếng Anh"]

# Từ khóa nhận diện ngôn ngữ từ tên (dùng khi map nội dung về ngôn ngữ)
LANG_KEYWORDS = (
    ("anh", "Tiếng Anh"),
    ("english", "Tiếng Anh"),
    ("nhật", "Tiếng Nhật"),
    ("japan", "Tiếng Nhật"),
    ("trung", "Tiếng Trung"),
    ("chin", "Tiếng Trung"),
    ("hàn", "Tiếng Hàn Quốc"),
    ("korea", "Tiếng Hàn Quốc"),
    ("pháp", "Tiếng Pháp"),
    ("french", "Tiếng Pháp"),
    ("đức", "Tiếng Đức"),
    ("german", "Tiếng Đức"),
    ("nga", "Tiếng Nga"),
    ("russia", "Tiếng Nga"),
    ("tây ban nha", "Tiếng Tây Ban Nha"),
    ("spanish", "Tiếng Tây Ban Nha"),
    ("thái", "Tiếng Thái"),
    ("thai", "Tiếng Thái"),
    ("ả rập", "Tiếng Ả Rập"),
    ("arabic", "Tiếng Ả Rập"),
    ("việt", "Tiếng Việt"),
    ("vietnam", "Tiếng Việt"),
)

# ─── Đặc tả đọc theo 6 chặng học ────────────────────────────────────────────
# Mỗi chặng: tốc độ, có sinh bản "slow" không, có dùng giọng narrative không.
STAGE_SPEC = {
    0: {"name": "Vỡ lòng", "rate": "-45%", "pitch": "+0Hz", "slow": True,
        "unit": "char", "narrative": False},
    1: {"name": "Ghép âm", "rate": "-30%", "pitch": "+0Hz", "slow": True,
        "unit": "syllable", "narrative": False},
    2: {"name": "Sơ cấp", "rate": "-15%", "pitch": "+0Hz", "slow": True,
        "unit": "word", "narrative": False},
    3: {"name": "Trung cấp", "rate": "+0%", "pitch": "+0Hz", "slow": False,
        "unit": "sentence", "narrative": False},
    4: {"name": "Cao cấp", "rate": "-5%", "pitch": "+0Hz", "slow": False,
        "unit": "paragraph", "narrative": True},
    5: {"name": "Bản xứ", "rate": "+0%", "pitch": "+0Hz", "slow": False,
        "unit": "idiom", "narrative": True},
}
DEFAULT_STAGE_SPEC = STAGE_SPEC[3]

# Voice Gemini TTS dùng cho văn bản dài (giọng trình bày)
NARRATIVE_GEMINI_VOICES = ("Charon", "Fenrir", "Aoede", "Orus", "Zephyr", "Vindemir")


def detect_language(name: str) -> str:
    """'Tiếng Nhật' → 'Tiếng Nhật' (khớp LANG_VOICES). Trả '' nếu không nhận diện được."""
    n = (name or "").strip().lower()
    for kw, lang in LANG_KEYWORDS:
        if kw in n:
            return lang
    # khớp theo tên chuẩn
    for lang in LANG_VOICES:
        if n == lang.lower():
            return lang
    return ""


def voice_for(language: str) -> dict:
    lang = detect_language(language) or language
    return LANG_VOICES.get(lang, DEFAULT_VOICE)


def stage_spec(stage_idx) -> dict:
    try:
        return STAGE_SPEC.get(int(stage_idx), DEFAULT_STAGE_SPEC)
    except (TypeError, ValueError):
        return DEFAULT_STAGE_SPEC


def stage_index_from_phase(phase: str) -> int:
    """'Vỡ lòng chữ cái & phát âm' → 0."""
    p = (phase or "").lower()
    for i, spec in STAGE_SPEC.items():
        if spec["name"].lower() in p:
            return i
    if "vỡ lòng" in p or "phát âm" in p or "chữ cái" in p:
        return 0
    if "ghép âm" in p:
        return 1
    if "sơ cấp" in p:
        return 2
    if "trung cấp" in p:
        return 3
    if "cao cấp" in p:
        return 4
    if "bản xứ" in p or "bản xứ" in p:
        return 5
    return 3


# ─── Bảng tra cứu cho web app ───────────────────────────────────────────────
def web_voice_table() -> list:
    """Danh sách [{lang, edge_voice, gtts_lang, gemini_voice}] — web đọc để map locale."""
    out = []
    for lang, v in LANG_VOICES.items():
        out.append({
            "lang": lang,
            "edge_voice": v["edge_voice"],
            "gtts_lang": v["gtts_lang"],
            "gemini_voice": v["gemini_voice"],
        })
    return out


def export_web_table(path: str) -> bool:
    """Ghi bảng voice ra data/tts_voices.json cho web app đọc (1 nguồn sự thật)."""
    import json
    from datetime import datetime
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "format_version": 1,
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "voices": web_voice_table(),
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return True


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("== Bảng voice ==")
    for lang, v in LANG_VOICES.items():
        print(f"  {lang:18s} gemini={v['gemini_voice']:12s} edge={v['edge_voice']:24s} "
              f"gtts={v['gtts_lang']:6s} sapi={v['sapi']}")
    print("\n== Đặc tả 6 chặng ==")
    for i, s in STAGE_SPEC.items():
        print(f"  {i} {s['name']:12s} rate={s['rate']:6s} slow={s['slow']} unit={s['unit']}")
    print("\n== Nhận diện ==")
    for n in ("Tiếng Nhật", "tiếng_anh", "Nhật", "Tiếng Hàn Quốc", "Tiếng Tây Ban Nha"):
        print(f"  {n!r:22s} → {detect_language(n)!r}")
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "tts_voices.json")
    export_web_table(p)
    print(f"\nĐã ghi {p}")
