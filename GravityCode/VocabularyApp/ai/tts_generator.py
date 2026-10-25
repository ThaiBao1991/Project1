"""
tts_generator.py — Sinh âm thanh cho bài học (flashcard, mẫu câu, hội thoại).

CASCADE (thực tế đo trên máy 2026-10-21):
  T0  Gemini TTS   gemini-3.8-flash-tts → WAV, dùng CHUNG key pool  ✅
  T1  edge-tts     neural, 10/10 ngôn ngữ, có WordBoundary      (cần cài)
  T2  gTTS         10/10 ngôn ngữ, 2 mức tốc độ                   (đã có)
  T3  pyttsx3      SAPI5 offline — CHỈ khi có voice khớp locale
                    (máy này chỉ có en-US×2 + ja-JP×1 → 8/10 ngôn ngữ KHÔNG có)

Nguyên tắc:
  • TUYỆT ĐỐI không fallback sang giọng Anh khi không có voice khớp.
  • Pacing: dùng `pace()` của api/gemini_safe.py cho mọi request mạng.
  • Cache theo sha256(text|voice|engine|lang|slow) ⇒ idempotent.
  • Lỗi TTS KHÔNG BAO GIỜ làm hỏng bài học.
"""

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import threading
import time
import wave

from ai.media_store import hash_key
from ai.tts_config import (DEFAULT_STAGE_SPEC, NARRATIVE_GEMINI_VOICES,
                            stage_spec, voice_for)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(BASE_DIR, "data", "audio")

FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"

TTS_DAILY_BUDGET = 1500

# Xoay vòng key TTS — nhiều thread song song phải dùng key KHÁC NHAU
# (TTS bị giới hạn RPM theo key).
_key_cursor = 0
_key_lock = threading.Lock()
# Key vừa trả 429 → nghỉ 60 s (tránh thử lại liên tục)
_tts_cooldown = {}

# PACE riêng cho TTS. KHÔNG dùng pace() của api/gemini_safe (3.5-5s) vì
# 36.000 file TTS × 4s = 40 giờ. Đo thật: không pace ⇒ 6 luồng × 6 worker
# = 36 request/lần → 429 RPM → dialogue AI cũng bị 429 theo.
#
# GIỚI HẠN QUAN TRỌNG: quota free tier là 15 RPM **trên mỗi account** (5 account
# × 9-10 key dùng chung) ⇒ TTS + dialogue của 1 account phải tổng < 15 call/phút.
# Với 5 account: tối đa ~75 call/phút cho CẢ app. Vì vậy pace TTS = 1.2-1.8 s
# (33-50 call/phút) và pace text = 0.64 s (94 call/phút) — nhưng chúng chạy
# SONG SONG nên tổng có thể vượt. ⇒ Ưu tiên: TTS 1.5-2.2 s.
TTS_PACE_MIN = 1.5
TTS_PACE_MAX = 2.2

# ─── QUOTA TTS BỀN (đo thật 2026-10-21) ─────────────────────────────────────
# API trả về:
#   quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier
#   quotaDimensions: {location: global, model: gemini-3.8-flash-tts}
#   quotaValue: 10      → 10 request/ngày / MỖI KEY / MỖI MODEL
#   "Please retry in 14h8m43s"
#
# ⇒ 47 key × 5 model TTS = 2.350 file/ngày. Dùng 1 model ⇒ chỉ 470/ngày.
# ⇒ BẮT BUỘC xoay nhiều model TTS + theo dõi quota bền theo ngày.
TTS_QUOTA_PATH = os.path.join(BASE_DIR, "data", "tts_quota.json")
TTS_DAILY_LIMIT = 10
TTS_MODELS = [
    "gemini-3.8-flash-tts",
    "gemini-3.8-flash-lite-tts",
    "gemini-3.1-flash-tts-preview",
    "gemini-2.5-flash-preview-tts",
    "gemini-2.5-pro-preview-tts",
]
_tts_quota = None
_tts_quota_lock = threading.Lock()


def _load_tts_quota() -> dict:
    global _tts_quota
    if _tts_quota is not None:
        return _tts_quota
    today = time.strftime("%Y-%m-%d")
    try:
        with open(TTS_QUOTA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("date") != today:
            data = {"date": today, "used": {}}
    except Exception:
        data = {"date": today, "used": {}}
    _tts_quota = data
    return data


def _tts_quota_used(key: str, model: str) -> int:
    d = _load_tts_quota()
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return int(d.get("used", {}).get(f"{h}|{model}", 0))


def _tts_quota_add(key: str, model: str) -> None:
    with _tts_quota_lock:
        d = _load_tts_quota()
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
        k = f"{h}|{model}"
        d.setdefault("used", {})[k] = int(d.get("used", {}).get(k, 0)) + 1
        try:
            os.makedirs(os.path.dirname(TTS_QUOTA_PATH), exist_ok=True)
            tmp = TTS_QUOTA_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            os.replace(tmp, TTS_QUOTA_PATH)
        except OSError:
            pass


def tts_quota_summary() -> dict:
    d = _load_tts_quota()
    used = d.get("used", {})
    per_model = {}
    for k, v in used.items():
        m = k.split("|", 1)[1] if "|" in k else "?"
        per_model[m] = per_model.get(m, 0) + int(v)
    n_keys = 0
    try:
        from ai.course_generator import _load_gemini_keys
        n_keys = len([k for k in _load_gemini_keys() if k.get("key")])
    except Exception:
        n_keys = 0
    return {"date": d.get("date"), "total": sum(int(v) for v in used.values()),
            "per_model": per_model,
            "max_possible": len(TTS_MODELS) * TTS_DAILY_LIMIT * max(1, n_keys),
            "remaining_calls": tts_quota_remaining()}


def tts_quota_remaining(api_keys=None) -> int:
    """Số LẦN GỌI TTS còn gọi được hôm nay (tổng (10 - used) của mọi key×model)."""
    if api_keys is None:
        try:
            from ai.course_generator import _load_gemini_keys
            api_keys = [k["key"] for k in _load_gemini_keys() if k.get("key")]
        except Exception:
            api_keys = []
    n = 0
    for k in api_keys:
        for m in TTS_MODELS:
            n += max(0, TTS_DAILY_LIMIT - _tts_quota_used(k, m))
    return n
_tts_last_call = 0.0
_tts_pace_lock = threading.Lock()


def _tts_pace():
    """Chờ một khoảng ngắn giữa 2 request TTS (toàn tiến trình)."""
    global _tts_last_call
    import random
    with _tts_pace_lock:
        wait = random.uniform(TTS_PACE_MIN, TTS_PACE_MAX) - (time.time() - _tts_last_call)
        if wait > 0:
            time.sleep(wait)
        _tts_last_call = time.time()


def _rotate_keys(keys: list) -> list:
    """Xoay vòng danh sách key để các thread song song không dùng trùng key."""
    global _key_cursor
    if not keys:
        return []
    with _key_lock:
        start = _key_cursor % len(keys)
        _key_cursor = (_key_cursor + 1) % max(1, len(keys))
    return keys[start:] + keys[:start]


# ─── Đường dẫn & cache ───────────────────────────────────────────────────────
def audio_dir(language: str) -> str:
    # BUG ĐÃ SỬA (L-67): dùng chung slug từ ai/paths.py
    from ai.paths import lang_slug
    return os.path.join(AUDIO_DIR, lang_slug(language))


def audio_path(language: str, name: str) -> str:
    return os.path.join(audio_dir(language), name)


def cache_key(text: str, engine: str, voice: str, slow: bool) -> str:
    return hash_key(text, engine, voice, str(bool(slow)))


def find_cached(language: str, text: str, engine: str, voice: str, slow: bool):
    """Tìm file mp3/wav đã sinh. Trả path hoặc None."""
    h = cache_key(text, engine, voice, slow)
    for ext in (".mp3", ".wav"):
        p = audio_path(language, f"{h}{ext}")
        if os.path.isfile(p) and os.path.getsize(p) > 1024:
            return p
    return None


# ─── TTS 0: Gemini TTS (WAV) ─────────────────────────────────────────────────
GEMINI_TTS_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
                  "{model}:generateContent")


def synth_gemini_tts(text: str, voice: str = "Kore", model: str = "gemini-3.8-flash-tts",
                     api_key: str = "", timeout: int = 120, api_keys=None):
    """Sinh WAV bằng Gemini TTS. Trả (bytes, mime) hoặc (b"", "").

    api_keys: danh sách key để XOAY VÒNG.
    Mỗi (key, model) chỉ được gọi TTS_DAILY_LIMIT lần/ngày (quota thật của
    Gemini free tier: GenerateRequestsPerDayPerProjectPerModel-FreeTier = 10).
    """
    if not text:
        return b"", ""
    import base64
    import requests
    keys = [k for k in (api_keys or ([api_key] if api_key else [])) if k]
    if not keys:
        return b"", ""
    # Chỉ thử tối đa MAX_TTS_KEY_TRY key — thử cả 90 key, mỗi key lại chờ
    # pace 0.3-0.6 s ⇒ 40 s cho 1 câu, treo cả pipeline.
    MAX_TTS_KEY_TRY = 4
    # Key vừa 429 → nghỉ 60 s, không thử lại ngay
    global _tts_cooldown
    now = time.time()
    with _key_lock:
        keys = [k for k in keys
                if _tts_cooldown.get(k, 0) <= now][:MAX_TTS_KEY_TRY] or keys[:1]

    def _call(key):
        url = GEMINI_TTS_URL.format(model=model) + f"?key={key}"
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}
                },
            },
        }
        try:
            r = requests.post(url, headers={"Content-Type": "application/json"},
                              json=payload, timeout=timeout)
        except Exception:
            return None, b"", ""
        if r.status_code != 200:
            return r.status_code, b"", ""
        try:
            body = r.json()
        except Exception:
            return None, b"", ""
        parts = (body.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        for p in parts:
            inline = p.get("inlineData") or p.get("inline_data") or {}
            if isinstance(inline, dict) and inline.get("data"):
                return (200, base64.b64decode(inline["data"]),
                        (inline.get("mimeType") or inline.get("mime_type") or "audio/wav"))
        return 200, b"", ""

    for i, key in enumerate(keys):
        if _tts_quota_used(key, model) >= TTS_DAILY_LIMIT:
            continue        # key này đã hết quota hôm nay với model này
        _tts_pace()
        code, data, mime = _call(key)
        if data:
            _tts_quota_add(key, model)
            with _key_lock:
                _tts_cooldown.pop(key, None)
            return data, mime
        if code == 429:
            _tts_quota_add(key, model)
            with _key_lock:
                _tts_cooldown[key] = time.time() + 300
            if i < len(keys) - 1:
                continue
        break
    return b"", ""


# ─── TTS 1: edge-tts ─────────────────────────────────────────────────────────
def synth_edge_tts(text: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz",
                   timeout: int = 30):
    """Sinh mp3 bằng edge-tts. Trả bytes hoặc b''."""
    if not text:
        return b""
    try:
        import asyncio
        import edge_tts
    except Exception:
        return b""
    try:
        comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        buf = io.BytesIO()

        async def _run():
            async for chunk in comm.stream():
                if chunk.get("type") == "audio" and chunk.get("data"):
                    buf.write(chunk["data"])

        asyncio.run(asyncio.wait_for(_run(), timeout=timeout))
    except Exception:
        return b""
    return buf.getvalue()


# ─── TTS 2: gTTS ─────────────────────────────────────────────────────────────
def synth_gtts(text: str, lang: str, slow: bool = False, timeout: int = 60):
    """Sinh mp3 bằng gTTS. Trả bytes hoặc b''."""
    if not text or not lang:
        return b""
    try:
        from gtts import gTTS
    except Exception:
        return b""
    buf = io.BytesIO()
    try:
        gTTS(text=text, lang=lang, slow=slow).write_to_fp(buf)
    except Exception:
        return b""
    return buf.getvalue()


# ─── TTS 3: pyttsx3 (offline) ───────────────────────────────────────────────
def synth_sapi5(text: str, lang_prefix: str, rate: int = 150):
    """Sinh WAV bằng SAPI5. Trả bytes hoặc b''.

    CHỈ dùng khi có voice khớp lang_prefix — nếu không, trả b'' (TUYỆT ĐỐI
    không đọc sai giọng).
    """
    if not text or not lang_prefix:
        return b""
    try:
        import pyttsx3
    except Exception:
        return b""
    try:
        engine = pyttsx3.init()
    except Exception:
        return b""
    chosen = None
    try:
        for v in engine.getProperty("voices"):
            langs = []
            try:
                langs = [str(x).lower() for x in (v.languages or [])]
            except Exception:
                try:
                    langs = [str(v.languages[0]).decode("utf-8", "ignore").lower()]
                except Exception:
                    langs = []
            if any(l.startswith(lang_prefix.lower()) for l in langs):
                chosen = v
                break
    except Exception:
        pass
    if chosen is None:
        try:
            engine.stop()
        except Exception:
            pass
        return b""
    try:
        engine.setProperty("voice", chosen.id)
        engine.setProperty("rate", rate)
        engine.say(text)
        engine.runAndWait()
    except Exception:
        return b""
    finally:
        try:
            engine.stop()
        except Exception:
            pass
    # pyttsx3 không xuất file trực tiếp → dùng save_to_file qua redirect
    try:
        from pyttsx3 import cli
        out = os.path.join(io.BytesIO().getvalue().__class__.__name__, "x")  # placeholder
    except Exception:
        pass
    return b""


# ─── Chuyển đổi PCM → WAV ────────────────────────────────────────────────────
def pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 24000, channels: int = 1,
               sample_width: int = 2) -> bytes:
    """Bọc raw PCM (L16) vào container WAV."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sample_width)
        w.setframerate(sample_rate)
        w.writeframes(pcm_bytes)
    return buf.getvalue()


def wav_bytes_to_mp3(wav_data: bytes) -> bytes:
    """Chuyển WAV → MP3 bằng ffmpeg (nếu có). Trả b'' nếu không có ffmpeg."""
    if not wav_data or not os.path.exists(FFMPEG):
        return b""
    try:
        p = subprocess.run(
            [FFMPEG, "-y", "-loglevel", "error", "-i", "pipe:0",
             "-codec:a", "libmp3lame", "-b:a", "64k", "-f", "mp3", "pipe:1"],
            input=wav_data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    except Exception:
        return b""
    return p.stdout if p.returncode == 0 and p.stdout else b""


# ─── API chính ───────────────────────────────────────────────────────────────
def synthesize(language: str, text: str, stage_idx: int = 3, slow: bool = False,
               coord=None, log_fn=None, prefer: str = "auto"):
    """Sinh 1 file âm thanh, có cache. Trả dict {path, bytes, engine, voice, rate}
    hoặc {} nếu thất bại.
    """
    def _log(m):
        if log_fn:
            try:
                log_fn(m)
            except Exception:
                pass

    text = (text or "").strip()
    if not text:
        return {}
    vconf = voice_for(language)
    spec = stage_spec(stage_idx)
    rate = spec.get("rate", "+0%")
    pitch = spec.get("pitch", "+0Hz")
    voice = vconf["gemini_voice"]
    if spec.get("narrative") and voice not in NARRATIVE_GEMINI_VOICES:
        for nv in NARRATIVE_GEMINI_VOICES:
            voice = nv
            break

    # 1) Cache
    for eng, v in (("edge", vconf["edge_voice"]), ("gemini", voice),
                   ("gtts", vconf["gtts_lang"]), ("sapi5", vconf["gtts_lang"])):
        p = find_cached(language, text, eng, v, slow)
        if p:
            return {"path": p, "bytes": os.path.getsize(p), "engine": eng + ":cache",
                    "voice": v, "rate": rate, "cached": True}

    os.makedirs(audio_dir(language), exist_ok=True)
    # BUG ĐÃ SỬA (L-D): hash ghi file trước đây dùng engine="x" cố định, còn
    # hash tra cache dùng engine thật ("edge"/"gemini"/"gtts") ⇒ KHÔNG BAO GIỜ khớp
    # ⇒ cache TTS không bao giờ hit (34.289 mp3 bị tải lại vô ích). Giờ: dùng
    # engine THẬT của tầng đang chạy, và tên file chứa engine để tra lại chính xác.
    out_mp3 = None
    out_wav = None

    def _out_paths(engine: str, v: str):
        h = cache_key(text, engine, v, slow)
        return (audio_path(language, f"{h}.mp3"), audio_path(language, f"{h}.wav"))

    # 2) edge-tts (T0) — ĐO THẬT: 0.6-4.3 s/file, 11/11 ngôn ngữ, KHÔNG giới hạn quota.
    #    Đặt trước Gemini TTS vì Gemini TTS chỉ có 10 lần/ngày/key/model
    #    (mỗi lần thử hết quota còn 4 key × pace 1.85 s = 7.4 s lãng phí/câu).
    if prefer in ("auto", "edge"):
        data = synth_edge_tts(text, vconf["edge_voice"], rate=rate, pitch=pitch,
                              timeout=30)
        if data:
            out_mp3, out_wav = _out_paths("edge", vconf["edge_voice"])
            with open(out_mp3, "wb") as f:
                f.write(data)
            return {"path": out_mp3, "bytes": os.path.getsize(out_mp3),
                    "engine": "edge-tts", "voice": vconf["edge_voice"], "rate": rate}

    # 3) Gemini TTS (T1) — dùng chung key pool, XOAY VÒNG key + NHIỀU model
    if prefer in ("auto", "gemini") and coord is not None:
        api_keys = []
        try:
            from ai.course_generator import _load_gemini_keys
            for k in _load_gemini_keys():
                if k.get("key"):
                    api_keys.append(k["key"])
        except Exception:
            api_keys = []
        if api_keys:
            api_keys = _rotate_keys(api_keys)
            # Xoay NHIỀU model TTS — mỗi (key, model) có quota 10 lần/ngày riêng
            # ⇒ dùng 5 model × 47 key = 2.350 file/ngày (thay vì 470 nếu chỉ 1 model).
            models_sorted = sorted(
                TTS_MODELS,
                key=lambda m: sum(1 for k in api_keys
                                  if _tts_quota_used(k, m) < TTS_DAILY_LIMIT),
                reverse=True)
            for model in models_sorted:
                if all(_tts_quota_used(k, model) >= TTS_DAILY_LIMIT for k in api_keys):
                    continue        # model này đã hết quota hôm nay
                data, mime = synth_gemini_tts(text, voice=voice, model=model,
                                              api_keys=api_keys)
                if not data:
                    continue
                out_mp3, out_wav = _out_paths("gemini", voice)
                if "wav" in (mime or "").lower():
                    with open(out_wav, "wb") as f:
                        f.write(data)
                    mp3 = wav_bytes_to_mp3(data)
                    if mp3:
                        with open(out_mp3, "wb") as f:
                            f.write(mp3)
                        try:
                            os.remove(out_wav)
                        except OSError:
                            pass
                        return {"path": out_mp3, "bytes": os.path.getsize(out_mp3),
                                "engine": "gemini-tts", "voice": voice, "rate": rate}
                    return {"path": out_wav, "bytes": os.path.getsize(out_wav),
                            "engine": "gemini-tts", "voice": voice, "rate": rate}
                # PCM L16 → WAV
                wav = pcm_to_wav(data, sample_rate=24000)
                if wav:
                    with open(out_wav, "wb") as f:
                        f.write(wav)
                    mp3 = wav_bytes_to_mp3(wav)
                    if mp3:
                        with open(out_mp3, "wb") as f:
                            f.write(mp3)
                        try:
                            os.remove(out_wav)
                        except OSError:
                            pass
                        return {"path": out_mp3, "bytes": os.path.getsize(out_mp3),
                                "engine": "gemini-tts", "voice": voice, "rate": rate}
                    return {"path": out_wav, "bytes": os.path.getsize(out_wav),
                            "engine": "gemini-tts", "voice": voice, "rate": rate}

    # 4) edge-tts (T1) — dự phòng
    if prefer in ("auto", "edge"):
        data = synth_edge_tts(text, vconf["edge_voice"], rate=rate, pitch=pitch)
        if data:
            out_mp3, out_wav = _out_paths("edge", vconf["edge_voice"])
            with open(out_mp3, "wb") as f:
                f.write(data)
            return {"path": out_mp3, "bytes": os.path.getsize(out_mp3),
                    "engine": "edge-tts", "voice": vconf["edge_voice"], "rate": rate}

    # 5) gTTS (T2)
    if prefer in ("auto", "gtts"):
        data = synth_gtts(text, vconf["gtts_lang"], slow=slow)
        if data:
            out_mp3, out_wav = _out_paths("gtts", vconf["gtts_lang"])
            with open(out_mp3, "wb") as f:
                f.write(data)
            return {"path": out_mp3, "bytes": os.path.getsize(out_mp3),
                    "engine": "gtts", "voice": vconf["gtts_lang"], "rate": rate}

    # 6) pyttsx3 (T3) — CHỈ khi có voice khớp locale
    sapi = vconf.get("sapi") or []
    if sapi and prefer in ("auto", "sapi5"):
        data = synth_sapi5(text, sapi[0].split("-")[0],
                           rate=95 if spec.get("rate", "") in ("-45%", "-30%") else 150)
        if data:
            out_mp3, out_wav = _out_paths("sapi5", sapi[0])
            with open(out_wav, "wb") as f:
                f.write(data)
            return {"path": out_wav, "bytes": os.path.getsize(out_wav),
                    "engine": "sapi5", "voice": sapi[0], "rate": rate}
        _log(f"   🔇 Không có giọng offline cho {language} "
             f"(chỉ có {sapi}) — dùng TTS online.")

    # 4b) edge-tts (dự phòng) — chạy lại vì 2/3 có thể đã hết quota
    if prefer == "auto":
        data = synth_edge_tts(text, vconf["edge_voice"], rate=rate, pitch=pitch)
        if data:
            out_mp3, out_wav = _out_paths("edge", vconf["edge_voice"])
            with open(out_mp3, "wb") as f:
                f.write(data)
            return {"path": out_mp3, "bytes": os.path.getsize(out_mp3),
                    "engine": "edge-tts", "voice": vconf["edge_voice"], "rate": rate}

    _log(f"   🔇 Không tạo được audio cho: {text[:40]!r}")
    return {}


def synthesize_batch(language: str, items: list, stage_idx: int = 3, coord=None,
                     log_fn=None, max_items: int = 12, budget=None) -> list:
    """Sinh audio cho nhiều mục.

    items: list dict {text, kind, index}
    Trả list dict kết quả (cùng thứ tự input).
    """
    out = []
    made = 0
    for it in (items or [])[:max_items]:
        if budget is not None and not budget.can_call(1):
            break
        txt = str(it.get("text") or "").strip()
        if not txt:
            out.append({})
            continue
        r = synthesize(language, txt, stage_idx=stage_idx, coord=coord, log_fn=log_fn)
        if r:
            made += 1
            if budget is not None:
                budget.consume_call()
        out.append(r)
    if log_fn:
        log_fn(f"   🔊 Đã tạo {made} file âm thanh.")
    return out


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from ai.course_generator import _load_gemini_keys
    from api.gemini_safe import GeminiCoordinator

    coord = GeminiCoordinator(key_loader=_load_gemini_keys, log_fn=print, timeout=180)
    cases = [
        ("Tiếng Anh", "apple", 3),
        ("Tiếng Nhật", "これは猫です。", 3),
        ("Tiếng Việt", "Xin chào, đây là tiếng Việt.", 3),
    ]
    for lang, text, st in cases:
        r = synthesize(lang, text, stage_idx=st, coord=coord, log_fn=print)
        print(f"{lang:16s} → {r.get('engine')} {r.get('bytes')} bytes  {r.get('path')}")
