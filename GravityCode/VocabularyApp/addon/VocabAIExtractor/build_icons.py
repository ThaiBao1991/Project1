"""Tạo icon PNG cho addon VocabAIExtractor (idempotent)."""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(HERE, "icons")

BG = (18, 18, 18, 255)
ACCENT = (187, 134, 252, 255)
WHITE = (255, 255, 255, 255)

os.makedirs(ICON_DIR, exist_ok=True)


def make(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG)
    d = ImageDraw.Draw(img)
    m = size // 8
    # sách mở
    d.rounded_rectangle([m, m * 2, size - m, size - m * 2],
                        radius=size // 12, fill=ACCENT)
    d.rounded_rectangle([m + size // 16, m * 2 + size // 16,
                          size // 2 - size // 32, size - m * 2 - size // 16],
                        radius=size // 24, fill=WHITE)
    d.rounded_rectangle([size // 2 + size // 32, m * 2 + size // 16,
                          size - m - size // 16, size - m * 2 - size // 16],
                        radius=size // 24, fill=WHITE)
    d.line([size // 2, m * 2 + size // 16, size // 2, size - m * 2 - size // 16],
           fill=ACCENT, width=max(2, size // 64))
    return img


for s in (16, 48, 128):
    p = os.path.join(ICON_DIR, f"icon{s}.png")
    make(s).save(p, "PNG")
    print("wrote", p, os.path.getsize(p), "bytes")
