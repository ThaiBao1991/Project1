"""
media_card.py — WORD-CARD: render chữ nước ngoài (Nhật/Trung/Hàn/…) ra PNG.

Vì sao: ảnh minh hoạ của kho tiếng Nhật đều hỏng (nền tối có chữ "tofu" ô ở giữa),
không thể dùng. Thay thế = thẻ chữ NHẬT in nét, sắc (vector font, không phải ảnh AI)
⇒ người học vẫn thấy từ ngay trên bảng media.

Đặc điểm:
  • Nền gradient theo chặng (6 màu) — đổi màu theo JLPT/chặng (level 0-5).
  • Font chữ Nhật Windows: Meiryo → YuGothM → MS Gothic → fallback mặc định.
  • Auto-shrink: từ dài (≥ 6 ký tự, VD "忌み言葉", "時候の挨拶") giảm cỡ + xuống dòng.
  • Cache: data/media/_cards/<sha1>.png — mở lại hôm sau không render lại.

API:
  render_word_card(word, reading="", meaning="", size=192, level=0) -> PIL.Image
  get_word_card_path(word, reading="", meaning="", size=192, level=0) -> str
"""

import hashlib
import os

try:
    from PIL import Image, ImageDraw, ImageFont
    _HAS_PIL = True
except Exception:  # pragma: no cover — máy không có Pillow thì tính năng tắt
    _HAS_PIL = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARD_DIR = os.path.join(BASE_DIR, "data", "media", "_cards")

# ─── Font chữ Nhật / CJK có sẵn trên Windows ──────────────────────────────────
FONT_CANDIDATES_CJK = (
    r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\YuGothM.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
    r"C:\Windows\Fonts\msyh.ttc",       # Trung giản thể
    r"C:\Windows\Fonts\malgun.ttf",     # Hàn
)

# Font LATIN đủ dấu tiếng Việt (ơ ệ ỵ …) — Meiryo thiếu toàn bộ Latin Extended
FONT_CANDIDATES_LATIN = (
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\consola.ttf",
    r"C:\Windows\Fonts\Calibri.ttf",
)

# Gradient nền (top, bottom) — 6 chặng / N5→N1
CARD_GRADIENTS = (
    ((60, 64, 96),   (34, 38, 62)),      # 0 — N5 / vỡ lòng  (xanh tím than)
    ((72, 60, 88),   (44, 34, 62)),      # 1 — N5 trôi chảy
    ((58, 96, 78),   (30, 58, 48)),      # 2 — N4            (xanh ngọc)
    ((96, 78, 44),   (58, 46, 26)),      # 3 — N3            (nâu vàng)
    ((104, 56, 60),  (62, 32, 36)),      # 4 — N2            (đỏ đậm)
    ((74, 56, 110),  (42, 30, 66)),      # 5 — N1 / kính ngữ
)

_WORD_FONT_COLOR = (245, 245, 250)
_SUB_COLOR = (196, 200, 214)
_MEAN_COLOR = (158, 164, 186)


def _load_font(size: int, tier: str = "cjk"):
    """tier='cjk' — font chữ Nhật/Trung/Hàn; tier='latin' — đủ dấu tiếng Việt."""
    if not _HAS_PIL:
        return None
    for p in (FONT_CANDIDATES_CJK if tier == "cjk" else FONT_CANDIDATES_LATIN):
        try:
            if os.path.isfile(p):
                return ImageFont.truetype(p, size=size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def _text_w(draw, txt, font):
    try:
        b = draw.textbbox((0, 0), txt, font=font)
        return b[2] - b[0]
    except Exception:
        return font.size * len(txt) * 0.6 if hasattr(font, "size") else 0


def _fit_lines(word: str, box_w: int, box_h: int, max_size: int, min_size: int = 17):
    """Chọn cỡ chữ + xuống dòng để từ KHÔNG bị cắt/có tofu.

    Ưu tiên: 1 dòng auto-shrink → nếu tới dưới min mà vẫn tràn thì
    xuống dòng đều (CJK tách theo ký tự; cụm có dấu cách tách theo từ).
    Trả (font, list_line, line_gap_px).
    """
    size = max(min_size, int(max_size))
    while size >= min_size:
        font = _load_font(size)
        if font is None:
            break
        if _text_w(_PROBE_DRAW, word, font) <= box_w:
            return font, [word], 0
        size -= 2  # nhỏ dần 2px/lượt — nhanh & mượt

    # Xuống dòng: ưu tiên tách theo dấu cách, sau đó nhóm 2 ký tự
    for pick_size in (max_size, max(min_size, max_size - 4), min_size):
        font = _load_font(pick_size)
        if font is None:
            break
        for lines in (_wrap_by_space(word, box_w, font),
                      _wrap_by_chunk(word, box_w, font, chunk=2),
                      _wrap_by_chunk(word, box_w, font, chunk=1)):
            if lines and all(_text_w(_PROBE_DRAW, ln, font) <= box_w for ln in lines):
                gap = 4 if pick_size >= 34 else 2
                return font, lines[:2], gap
    return _load_font(min_size), [word], 2


_PROBE_DRAW = None


def _wrap_by_space(word: str, box_w: int, font) -> list:
    parts = word.split(" ")
    if len(parts) <= 1:
        return []
    out, cur = [], ""
    for p in parts:
        cand = f"{cur} {p}".strip()
        if _text_w(_PROBE_DRAW, cand, font) <= box_w or not cur:
            cur = cand
        else:
            out.append(cur)
            cur = p
    if cur:
        out.append(cur)
    return out


def _wrap_by_chunk(word: str, box_w: int, font, chunk: int = 2) -> list:
    w = word.replace(" ", "")  # CJK: bỏ dấu cách, ghép theo nhóm
    if len(w) < 4:
        return []
    half = (len(w) + 1) // 2
    candidates = ((w[:half], w[half:]),)
    if chunk == 1 and len(w) % 2 == 0:
        candidates = ((w[:half], w[half:]),)
    for a, b in candidates:
        if (_text_w(_PROBE_DRAW, a, font) <= box_w
                and _text_w(_PROBE_DRAW, b, font) <= box_w and b):
            return [a, b]
    return []


def render_word_card(word: str, reading: str = "", meaning: str = "",
                     size: int = 192, level: int = 0) -> "Image.Image":
    """Render thẻ chữ (bỏ qua cache) — trả PIL.Image RGB."""
    if not _HAS_PIL:
        raise RuntimeError("Render word-card cần Pillow.")

    word = str(word or "").strip() or "?"
    reading = str(reading or "").strip()
    meaning = str(meaning or "").strip()
    size = max(96, int(size))
    img = Image.new("RGB", (size, size), (44, 44, 54))
    draw = ImageDraw.Draw(img)

    # ── Nền gradient 2 màu theo chặng ──
    top, bottom = CARD_GRADIENTS[int(level) % len(CARD_GRADIENTS)]
    for y in range(size):
        t = y / max(1, size - 1)
        row = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (size, y)], fill=row)

    pad = int(size * 0.07)
    box_w, box_h = size - pad * 2, size - pad * 2

    # ── Lesson volume: từ chính (cỡ 0.36–0.44 * size / tratta) ──
    global _PROBE_DRAW
    _PROBE_DRAW = draw
    max_word = int(size * 0.40) if len(word) <= 3 else int(size * 0.26)
    font_word, wl, gap = _fit_lines(word, box_w, box_h, max_size=max_word,
                                    min_size=max(17, int(size * 0.10)))
    wdt_h = sum(_text_h(draw, ln, font_word) for ln in wl) + gap * (len(wl) - 1)
    y_top = size * 0.30 - wdt_h / 2
    if reading:    # đẩy lên một chút tạo khoảng cho reading ở dưới
        y_top = size * 0.27 - wdt_h / 2
    for ln in wl:
        w = _text_w(draw, ln, font_word)
        draw.text(((size - w) / 2, y_top), ln, font=font_word,
                  fill=_WORD_FONT_COLOR)
        y_top += _text_h(draw, ln, font_word) + gap

    # ── Reading (kana / romaji) ──
    if reading:
        f_r = _load_font(max(12, int(size * 0.115)))
        rtxt = f"/{reading}/"
        if reading.replace(" ", "").isascii():
            rtxt = reading
        if _text_w(draw, rtxt, f_r) > box_w:
            rtxt = reading[: int(len(reading) * box_w / max(1, _text_w(draw, reading, f_r)))]
        w = _text_w(draw, rtxt, f_r)
        draw.text(((size - w) / 2, y_top + int(size * 0.04)), rtxt,
                  font=f_r, fill=_SUB_COLOR)

    # ── Nghĩa VI dưới đáy (tối đa 2 dòng) — font LATIN đủ dấu tiếng Việt ──
    if meaning:
        f_m = _load_font(max(11, int(size * 0.085)), tier="latin")
        for mln in _wrap_meaning(draw, meaning, box_w, f_m)[:2]:
            w = _text_w(draw, mln, f_m)
            draw.text(((size - w) / 2, size - pad - int(size * 0.10)), mln,
                      font=f_m, fill=_MEAN_COLOR)
            break  # chỉ 1 dòng đáy — nghĩa dài sẽ bị cắt, UI row ở dưới có đủ

    # ── Viền mảnh ──
    draw.rectangle([0, 0, size - 1, size - 1], outline=(66, 68, 84), width=2)
    return img


def _text_h(draw, txt, font):
    try:
        b = draw.textbbox((0, 0), txt, font=font)
        return b[3] - b[1]
    except Exception:
        return getattr(font, "size", 14)


def _wrap_meaning(draw, text: str, box_w: int, font) -> list:
    out, cur = [], ""
    for ch in text:
        cand = cur + ch
        if _text_w(draw, cand, font) <= box_w or not cur:
            cur = cand
        else:
            out.append(cur)
            cur = ch
        if len(out) >= 2:
            break
    if cur and len(out) < 2:
        out.append(cur)
    return out


def get_word_card_path(word: str, reading: str = "", meaning: str = "",
                       size: int = 192, level: int = 0) -> str:
    """Đường dẫn PNG đã cache của thẻ — render 1 lần, mở lại trả cache."""
    if not _HAS_PIL:
        return ""
    key = hashlib.sha1(f"{word}|{reading}|{meaning}|{size}|{level}"
                       .encode("utf-8")).hexdigest()
    path = os.path.join(CARD_DIR, f"{key}.png")
    if os.path.isfile(path):
        return path
    try:
        os.makedirs(CARD_DIR, exist_ok=True)
        tmp = path + ".tmp.png"
        render_word_card(word, reading, meaning, size, level).save(tmp)
        os.replace(tmp, path)
        return path
    except Exception:
        return ""


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = get_word_card_path("理由", "りゆう", "lý do", 192, 2)
    print("card:", p or "FAILED")
    for w, r, m, lv in (("あ", "a", "ba chữ a", 0),
                        ("日本語", "にほんご", "tiếng Nhật", 0),
                        ("忌み言葉", "いみことば", "lời kiêng kỵ", 5),
                        ("時候の挨拶", "じこうのあいさつ", "lời chào theo mùa", 5)):
        q = get_word_card_path(w, r, m, 192, lv)
        print(f"  {w}: {'OK ' + q if q else 'FAILED'}")
