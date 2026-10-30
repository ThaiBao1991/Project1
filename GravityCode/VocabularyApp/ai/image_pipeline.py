"""
image_pipeline.py — Sinh ảnh minh họa cho từ vựng.

CHUỖI PROVIDER (thực tế đo trên máy 2026-10-21):
  T1  Gemini native image   → ❌ KHÔNG KHẢ DỤNG: free tier có "limit: 0" cho mọi
                              model ảnh. Code vẫn giữ để dùng khi có key trả phí.
  T2  Web AI (addon/Selenium/OpenClaw) → xem ai/web_ai_bridge.py (Phase 4)
  T3  Từ điển / kho ảnh Wikimedia     → ✅ ĐANG HOẠT ĐỘNG (0 key, 0.5-2.2s/ảnh)
  T4  Placeholder (chữ cái đầu)        → luôn có, không bao giờ để trống

Nguyên tắc bất di bất dịch (theo AskCpl/gemini_image_pipeline.py:20-23):
    "A failure leaves the lesson intact: generated visuals are enhancement assets,
     never a condition for declaring a project complete."
    → Lỗi ảnh KHÔNG BAO GIỜ làm hỏng bài học.

Cache: sha256(prompt|model|lang) ⇒ cùng 1 prompt không gọi lại AI.
"""

import os
import re
import sys

from ai import media_store
from ai.media_store import (SOURCE_AI, SOURCE_DICT, SOURCE_PLACEHOLDER,
                            SOURCE_WEB, hash_key)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Chain model ảnh AI — thứ tự thử. Model chết sẽ bị ghi vào dead_models.json.
IMAGE_MODEL_FALLBACKS = [
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
    "gemini-nano-banana-2.1",
]

# Provider ảnh theo thứ tự ưu tiên. Có thể ghi đè trong settings.json (media.image_providers).
#
# MẶC ĐỊNH KHÔNG BẬT "web": tầng Web AI cần Chrome addon được cài THỦ CÔNG
# (load unpacked) hoặc chromedriver khớp Chrome. Khi thiếu, mỗi lần gọi mất
# ~60 s chờ timeout (đo thật) ⇒ chậm gấp 20 lần.
# Muốn bật: thêm "web" vào đầu danh sách trong settings.json → media.image_providers
# (sau khi đã cài addon tại VocabularyApp/addon/VocabAIExtractor/).
DEFAULT_IMAGE_PROVIDERS = ["dict", "placeholder"]

# Ngưỡng loại ảnh rác (theo DownloadImgFacebook/.../background.js:280-285)
MIN_IMAGE_PX = 150
MIN_IMAGE_BYTES = 5 * 1024

# Từ khóa trong `alt` bị loại (background.js:273-278)
_JUNK_ALT_TOKENS = (
    "nhãn dán", "sticker", "biểu tượng", "icon", "ảnh đại diện",
    "profile picture", "avatar", "logo", "badge",
)

_JUNK_URL_TOKENS = ("/rsrc.php", "emoji", "static.xx", "spacer", "blank.gif")


# ─── Prompt ───────────────────────────────────────────────────────────────────
def build_image_prompt(word: str, meaning_vi: str = "", image_prompt: str = "") -> str:
    """Dùng prompt do AI viết sẵn; nếu thiếu thì tự dựng từ từ + nghĩa."""
    p = (image_prompt or "").strip()
    if p:
        return p
    subject = " ".join(w for w in [(word or "").strip(), (meaning_vi or "").strip()] if w)
    return (f"Flat vector illustration of {subject}, simple shapes, clear plain "
            f"background, educational flashcard style, no text, no watermark.")


# ─── Bộ lọc ảnh rác (6 lớp) ───────────────────────────────────────────────────
def filter_junk_images(images: list) -> list:
    """Loại ảnh rác. Mỗi phần tử: {url, alt, width, height, bytes, content_type}."""
    out = []
    for im in images or []:
        if not isinstance(im, dict):
            continue
        url = str(im.get("url") or "").strip()
        if not url.lower().startswith(("http://", "https://")):
            continue
        alt = str(im.get("alt") or "").lower()
        if any(tok in alt for tok in _JUNK_ALT_TOKENS):
            continue
        if any(tok in url.lower() for tok in _JUNK_URL_TOKENS):
            continue
        w = int(im.get("width") or 0)
        h = int(im.get("height") or 0)
        if w and w <= MIN_IMAGE_PX:
            continue
        if h and h <= MIN_IMAGE_PX:
            continue
        b = int(im.get("bytes") or 0)
        if b and b < MIN_IMAGE_BYTES:
            continue
        ctype = str(im.get("content_type") or "").lower()
        if ctype and not ctype.startswith("image/"):
            continue
        out.append(im)
    return out


# ─── aHash 16×16 (dedupe) ────────────────────────────────────────────────────
def ahash(pil_img) -> str:
    """aHash 256-bit (16x16 grayscale) — dùng để LOẠI ảnh trùng, không để xác nhận đúng từ."""
    try:
        import numpy as np
        from PIL import Image
        lanczos = getattr(getattr(Image, "Resampling", Image), "LANCZOS", None)
        if lanczos is None:
            return ""
        if pil_img.mode != "L":
            pil_img = pil_img.convert("L")
        small = pil_img.resize((16, 16), lanczos)
        arr = np.asarray(small, dtype=np.float64)
        return "".join("1" if v >= arr.mean() else "0" for v in arr.flatten())
    except Exception:
        return ""


def ahash_similarity(h1: str, h2: str) -> float:
    if not h1 or not h2 or len(h1) != len(h2):
        return 0.0
    diff = sum(1 for a, b in zip(h1, h2) if a != b)
    return 1.0 - diff / max(1, len(h1))


# ─── Placeholder (Tầng 4) ────────────────────────────────────────────────────
def make_placeholder_image(word: str, size: int = 512):
    """Tạo ảnh placeholder: chữ cái đầu trên nền tối. Trả (bytes PNG, mime)."""
    try:
        import io
        from PIL import Image, ImageDraw
        ch = (word or "?").strip()[:1].upper() or "?"
        img = Image.new("RGB", (size, size), (30, 30, 46))
        d = ImageDraw.Draw(img)
        try:
            bbox = d.textbbox((0, 0), ch)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            tw = th = int(size * 0.4)
        d.text(((size - tw) / 2, (size - th) / 2), ch, fill=(187, 134, 252))
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return buf.getvalue(), "image/png"
    except Exception:
        return b"", "image/png"


# ─── Sinh ảnh cho 1 ngày (chuỗi provider) ───────────────────────────────────
def generate_images_for_day(language: str, day: int, lesson: dict, coord=None,
                            log_fn=print, max_images: int = 10,
                            budget=None, dead_models=None,
                            providers=None, web_fetcher=None) -> list:
    """Sinh ảnh minh họa cho các từ vựng trong 1 ngày.

    providers: list tên provider, theo thứ tự ưu tiên. Mặc định lấy từ
    settings.json (media.image_providers), fallback DEFAULT_IMAGE_PROVIDERS.
    web_fetcher: callable(language, day, vocab) -> list dict ảnh (tầng Web AI).

    Trả list media entry (đã lưu + đã ghi manifest).
    Lỗi 1 ảnh → bỏ qua ảnh đó, KHÔNG fail cả ngày.
    """
    entries = []
    vocab = (lesson or {}).get("vocab") or []
    if not vocab:
        return entries

    if not providers:
        try:
            from settings import load_settings
            providers = (load_settings().get("media", {}) or {}).get("image_providers") \
                or list(DEFAULT_IMAGE_PROVIDERS)
        except Exception:
            providers = list(DEFAULT_IMAGE_PROVIDERS)
    providers = [p for p in providers if p]

    dead = set(dead_models or [])
    models = [m for m in IMAGE_MODEL_FALLBACKS if m not in dead]
    made = 0

    # Dọn ref cũ trỏ tới file KHÔNG còn tồn tại (media bị xoá/đổi tên)
    # → để tầng sau sinh lại, không để trống.
    try:
        _idx = media_store.load_index()
        for v in vocab:
            ref = v.get("image_ref")
            if ref and not media_store.ref_exists(_idx, ref):
                v["image_ref"] = None
    except Exception:
        pass

    words_payload = [
        {"word": v.get("word", ""), "pronunciation": v.get("pronunciation", ""),
         "meaning_vi": v.get("meaning_vi", ""), "image_prompt": v.get("image_prompt", "")}
        for v in vocab
    ]

    for prov in providers:
        if made >= max_images:
            break
        if prov == "gemini":
            made += _stage_gemini(language, day, vocab, coord, log_fn, models,
                                  max_images - made, budget, entries)
        elif prov == "web":
            if web_fetcher is None:
                log_fn("   ⏭ Bỏ qua tầng Web AI (chưa có bộ lấy nội dung).")
                continue
            made += _stage_web(language, day, vocab, web_fetcher, log_fn,
                               max_images - made, budget, entries)
        elif prov == "dict":
            made += _stage_dict(language, day, vocab, log_fn,
                                max_images - made, budget, entries)
        elif prov == "placeholder":
            made += _stage_placeholder(language, day, vocab, log_fn,
                                       max_images - made, entries)

    log_fn(f"   🖼️  Xong ảnh Ngày {day}: {made} ảnh "
           f"(nguồn: {', '.join(providers)}).")
    return entries


def _save_image_entry(language, day, idx, word, raw, mime, source, prompt,
                      credit, license_, source_url, alt, log_fn, entries):
    name = f"word_{idx:02d}_{hash_key(word, prompt, source)}"
    try:
        entry = media_store.save_image_bytes(
            language, day, name, raw, mime=mime, source=source, prompt=prompt,
            alt=alt or word, credit=credit, license_=license_, source_url=source_url)
    except Exception as e:
        log_fn(f"   ⚠ Không lưu được ảnh '{word}': {e}")
        return None
    if entry:
        entries.append(entry)
    return entry


def _stage_gemini(language, day, vocab, coord, log_fn, models, quota,
                  budget, entries) -> int:
    """T1 — Gemini native image (chỉ chạy nếu còn quota; free tier hiện limit:0)."""
    if not coord or not models:
        return 0
    made = 0
    for idx, v in enumerate(vocab):
        if made >= quota:
            break
        if budget is not None and not budget.can_image(1):
            break
        word = str(v.get("word", "")).strip()
        if not word:
            continue
        prompt = build_image_prompt(word, str(v.get("meaning_vi", "")),
                                    str(v.get("image_prompt", "")))
        res = coord.request_image(prompt, models=models)
        if not res.get("ok"):
            err = res.get("error", {})
            if err.get("hard_quota"):
                log_fn(f"   ⛔ Model ảnh AI bị giới hạn cứng (limit: 0) — bỏ qua tầng này.")
                return made
            log_fn(f"   ⚠ Ảnh AI '{word}' thất bại [{err.get('kind')}]: "
                   f"{str(err.get('message',''))[:80]}")
            continue
        e = _save_image_entry(language, day, idx, word, res["b64"],
                              res.get("mime", "image/png"), SOURCE_AI, prompt,
                              "AI-generated (Gemini)", "AI-generated", "",
                              str(v.get("meaning_vi") or word), log_fn, entries)
        if e:
            v["image_ref"] = e.get("id")
            made += 1
            if budget is not None:
                budget.consume_image()
    return made


def _stage_web(language, day, vocab, web_fetcher, log_fn, quota, budget, entries) -> int:
    """T2 — Web AI (addon Chrome / Selenium / OpenClaw)."""
    try:
        results = web_fetcher(language, day, vocab)
    except Exception as e:
        log_fn(f"   ⚠ Tầng Web AI lỗi: {e}")
        return 0
    made = 0
    for idx, (v, r) in enumerate(zip(vocab, results or [])):
        if made >= quota:
            break
        if not r or not r.get("bytes"):
            continue
        e = _save_image_entry(language, day, idx, str(v.get("word", "")),
                              r["bytes"], r.get("content_type", "image/jpeg"),
                              SOURCE_WEB, r.get("prompt", ""),
                              r.get("credit", "Web AI"), r.get("license", ""),
                              r.get("source_url", ""),
                              str(v.get("meaning_vi") or v.get("word", "")),
                              log_fn, entries)
        if e:
            v["image_ref"] = e.get("id")
            made += 1
            if budget is not None:
                budget.consume_image()
    return made


def _stage_dict(language, day, vocab, log_fn, quota, budget, entries) -> int:
    """T3 — Ảnh từ từ điển / kho ảnh Wikimedia (0 key, đang hoạt động).

    KHÔNG ghi đè ảnh THẬT đã có: nếu `image_ref` hiện tại trỏ tới một media
    không phải "placeholder" thì giữ nguyên, chỉ tìm ảnh cho từ còn thiếu
    hoặc đang là placeholder.
    """
    from ai import dictionary_image
    index = media_store.load_index()

    def _has_real(v):
        r = (v or {}).get("image_ref")
        if not r:
            return False
        e = media_store.resolve(index, r)
        return bool(e) and e.get("source") != "placeholder"

    pairs = [(i, v) for i, v in enumerate(vocab) if not _has_real(v)]
    if not pairs:
        return 0
    if len(pairs) < len(vocab):
        log_fn(f"   🖼️  Giữ {len(vocab) - len(pairs)} ảnh thật, "
               f"tìm {len(pairs)} ảnh còn thiếu.")
        # Đánh dấu từ còn thiếu để bù lần sau (không ghi đè ảnh thật)
    # Nếu chưa có ảnh thật cho từ → giữ placeholder; không ghi đè thật bằng placeholder

    words = [{"word": v.get("word", ""), "pronunciation": v.get("pronunciation", ""),
              "meaning_vi": v.get("meaning_vi", "")} for _i, v in pairs]
    results = dictionary_image.find_images_for_words(
        words, language, log_fn=None, max_workers=6)
    made = 0
    for (idx, v), r in zip(pairs, results):
        if made >= quota:
            break
        if not r or not r.get("bytes"):
            continue
        e = _save_image_entry(language, day, idx, str(v.get("word", "")),
                              r["bytes"], r.get("content_type", "image/jpeg"),
                              SOURCE_DICT, f"search:{r.get('query','')}",
                              r.get("credit", ""), r.get("license", ""),
                              r.get("source_url", ""),
                              str(v.get("meaning_vi") or v.get("word", "")),
                              log_fn, entries)
        if e:
            v["image_ref"] = e.get("id")
            e["confidence"] = r.get("confidence", "medium")
            e["provider"] = r.get("provider", "dict")
            made += 1
            if budget is not None:
                budget.consume_image()
    return made


def _stage_placeholder(language, day, vocab, log_fn, quota, entries) -> int:
    """T4 — Placeholder (chữ cái đầu). CHỈ điền cho từ CHƯA có ảnh."""
    made = 0
    for idx, v in enumerate(vocab):
        if made >= quota:
            break
        if v.get("image_ref"):
            continue          # đã có ảnh thật → không ghi đè bằng placeholder
        word = str(v.get("word", "")).strip()
        if not word:
            continue
        raw, mime = make_placeholder_image(word)
        if not raw:
            continue
        e = _save_image_entry(language, day, idx, word, raw, mime,
                              SOURCE_PLACEHOLDER, "placeholder",
                              "Generated placeholder", "n/a", "",
                              word, log_fn, entries)
        if e:
            v["image_ref"] = e.get("id")
            made += 1
    return made


# ─── Verify model ảnh còn sống (1 call THẬT) ────────────────────────────────
def verify_image_model(coord, log_fn=print, prompt: str = None) -> str:
    """Gọi thật 1 lần để xác minh model ảnh nào còn sống. Trả tên model hoặc ''."""
    prompt = prompt or ("Flat vector illustration of a red apple, simple shapes, "
                        "plain background, educational flashcard style, no text.")
    for model in IMAGE_MODEL_FALLBACKS:
        try:
            res = coord.request_image(prompt, models=[model], timeout=180)
        except Exception as e:
            log_fn(f"   ⚠ Kiểm tra model ảnh '{model}' lỗi: {e}")
            continue
        if res.get("ok"):
            log_fn(f"   ✅ Model ảnh khả dụng: '{model}' ({len(res.get('b64',''))} ký tự base64).")
            return model
        err = res.get("error", {})
        if err.get("hard_quota"):
            log_fn(f"   ⛔ Model ảnh '{model}' bị giới hạn cứng (limit: 0 free tier).")
            continue
        log_fn(f"   ⚠ Model ảnh '{model}' không dùng được [{err.get('kind')}] "
               f"{str(err.get('message',''))[:90]}")
    log_fn("   ❌ KHÔNG có model ảnh nào còn sống — dùng tầng ảnh từ từ điển/Wikimedia.")
    return ""


# ─── CLI kiểm tra nhanh ──────────────────────────────────────────────────────
if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from ai.course_generator import _load_gemini_keys
    from api.gemini_safe import GeminiCoordinator

    keys = _load_gemini_keys()
    print(f"Gemini keys: {len(keys)}")
    if not keys:
        sys.exit(2)
    coord = GeminiCoordinator(key_loader=_load_gemini_keys, log_fn=print, timeout=180)
    print("Image models:", coord.image_models)
    m = verify_image_model(coord)
    print("RESULT:", m or "NONE (dùng tầng ảnh từ từ điển)")
    sys.exit(0)
