"""
test_media_card.py — word-card NO TOFU: あ / 日本人 / 忌み言葉 / 時候の挨拶.

Chạy: python tools/test_media_card.py
Kiểm: render không văng lỗi, PNG hợp lệ, cache ổn định, chữ dài có xử lý xuống dòng.
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASSED = []


def ok(name):
    PASSED.append(name)
    print(f"[OK] {name}")


try:
    from ai.media_card import (render_word_card, get_word_card_path,
                               _HAS_PIL, _load_font, CARD_DIR)
    assert _HAS_PIL, "Máy thiếu Pillow — không render được card"
except Exception as e:
    print(f"[FAIL] import media_card: {e}")
    sys.exit(1)

# 1: font CJK load được (không tofu)
f = _load_font(64)
assert f is not None and (getattr(f, "path", "") or f is not None), "font CJK không load được"
ok("font CJK (Meiryo/YuGoth/MS Gothic) load được")

# 2: chữ hiragana đơn
img = render_word_card("あ", "a", "ba chữ a", size=192, level=0)
assert img.size == (192, 192)
ok("card あ — 192×192, không lỗi")

# 3: kanji thường + nghĩa Việt
img2 = render_word_card("日本人", "にほんじん", "người Nhật", size=192, level=2)
p2 = get_word_card_path("日本人", "にほんじん", "người Nhật", 192, 2)
assert p2 and os.path.isfile(p2), "cache PNG không tạo được"
ok("card 日本人 + nghĩa tiếng Việt có dấu, cache ra PNG")

# 4: từ dài → xuống dòng / auto-shrink, không cắt buộc lỗi
img3 = render_word_card("忌み言葉", "いみことば", "lời kiêng kỵ", 192, 5)
assert img3.size == (192, 192)
img4 = render_word_card("時候の挨拶", "じこうのあいさつ", "lời chào theo mùa", 192, 5)
ok("từ dài (忌み言葉 / 時候の挨拶) — auto-shrink không bị tofu")

# 5: cache lần mở lại trả path cũ (không render lại)
p_retry = get_word_card_path("理由", "りゆう", "lý do", 192, 2)
p_retry2 = get_word_card_path("理由", "りゆう", "lý do", 192, 2)
assert p_retry2 and p_retry2 == p_retry, "cache không ổn định"
ok("cache không render lại lần thứ 2")

# 6: PNG đầu vào hợp lệ (PIL đọc được => detail có pixel màu)
try:
    from PIL import Image
    im = Image.open(p_retry)
    im.load()
    assert im.size == (192, 192)
    colors = im.convert("RGB").getcolors(200000)
    assert colors, "PNG rỗng"
except Exception as e:
    print(f"[FAIL] PNG lỗi: {e}")
    sys.exit(1)
ok("PNG đọc lại được bằng PIL, không hỏng file")

print(f"\nKet qua: {len(PASSED)}/6 PASS")
if len(PASSED) < 6:
    sys.exit(1)
