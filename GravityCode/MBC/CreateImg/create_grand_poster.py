# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw, ImageFont

base_dir = os.path.dirname(__file__)
scenes_dir = os.path.join(base_dir, 'generated_scenes')
output_path = os.path.join(scenes_dir, 'dai_tiec_toan_canh_6_ban.jpg')

# 4K resolution 16:9
W, H = 3840, 2160
canvas = Image.new('RGB', (W, H), (15, 23, 42))
draw = ImageDraw.Draw(canvas)

# Create rich festive background gradient
for y in range(H):
    r = int(15 + (y / H) * 20)
    g = int(23 + (y / H) * 15)
    b = int(42 - (y / H) * 20)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# Try loading system font or fallback
def get_font(size, bold=False):
    font_names = ['segoeui.ttf', 'arial.ttf', 'calibri.ttf']
    if bold:
        font_names = ['segoeuib.ttf', 'arialbd.ttf', 'calibrib.ttf']
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except:
            pass
    return ImageFont.load_default()

title_font = get_font(84, bold=True)
sub_font = get_font(42, bold=False)
table_label_font = get_font(34, bold=True)
footer_font = get_font(36, bold=True)

# Draw Top Header Banner
header_h = 240
draw.rectangle([(0, 0), (W, header_h)], fill=(12, 18, 34))
draw.line([(0, header_h), (W, header_h)], fill=(245, 158, 11), width=5)

# Golden Title
title_text = "🍻 ĐẠI TIỆC NHẬU CÔNG TY MBC 2026 - TOÀN CẢNH 6 BÀN VUÔNG 🍻"
draw.text((W // 2, 70), title_text, font=title_font, fill=(251, 191, 36), anchor="mm")

# Subtitle
sub_text = "HỘI TỤ 33 NHÂN SỰ • BÀN VUÔNG 6 GHẾ • ZÔ 100% KHÔNG SAY KHÔNG VỀ!"
draw.text((W // 2, 160), sub_text, font=sub_font, fill=(241, 245, 249), anchor="mm")

# Grid layout: 2 rows x 3 columns
margin_x = 80
margin_y = 280
footer_h = 100
avail_w = W - margin_x * 2
avail_h = H - margin_y - footer_h

cols = 3
rows = 2
gap_x = 40
gap_y = 40

card_w = (avail_w - gap_x * (cols - 1)) // cols
card_h = (avail_h - gap_y * (rows - 1)) // rows

table_configs = [
    {
        'file': 'slide_ban1_vip.jpg',
        'title': '⭐ BÀN 1: BÀN VIP LÃNH ĐẠO & TẤN SỸ QUA MỜI SẾP',
        'color': (245, 158, 11)
    },
    {
        'file': 'slide_ban2_thucthan.jpg',
        'title': '🍗 BÀN 2: THỰC THẦN ĐÙI GÀ & THẦY BÓI TIỆC NHẬU',
        'color': (239, 68, 68)
    },
    {
        'file': 'slide_ban3_chiem.jpg',
        'title': '💃 BÀN 3: HỘI CHỊ EM RẠNG RỠ & SELFIE SỐNG ẢO',
        'color': (236, 72, 153)
    },
    {
        'file': 'slide_ban4_suachua.jpg',
        'title': '🍨 BÀN 4: NỮ DOANH NHÂN SỮA CHUA & ANH CHÀNG BÓC TÔM',
        'color': (16, 185, 129)
    },
    {
        'file': 'slide_ban5_bolero.jpg',
        'title': '🎤 BÀN 5: BAN NHẠC BOLERO & TUYỆT ĐỈNH RÓT BIA',
        'color': (139, 92, 246)
    },
    {
        'file': 'scene_template_ban_vuong_6nguoi.jpg',
        'title': '🦾 BÀN 6: BIỆT ĐỘI BẤT TỬ 100% & ĐẾM VỎ CHAI KỶ LỤC',
        'color': (59, 130, 246)
    }
]

for idx, conf in enumerate(table_configs):
    r_idx = idx // cols
    c_idx = idx % cols
    
    x = margin_x + c_idx * (card_w + gap_x)
    y = margin_y + r_idx * (card_h + gap_y)
    
    img_p = os.path.join(scenes_dir, conf['file'])
    if os.path.exists(img_p):
        img = Image.open(img_p).convert('RGB')
        
        # Reserve top 45px for card title banner
        header_card_h = 48
        img_avail_h = card_h - header_card_h
        
        img_resized = img.resize((card_w, img_avail_h), Image.Resampling.LANCZOS)
        
        # Draw frame card background
        draw.rectangle([(x - 4, y - 4), (x + card_w + 4, y + card_h + 4)], outline=conf['color'], width=4)
        
        # Draw card header banner
        draw.rectangle([(x, y), (x + card_w, y + header_card_h)], fill=(20, 29, 47))
        draw.line([(x, y + header_card_h), (x + card_w, y + header_card_h)], fill=conf['color'], width=2)
        
        # Card title text
        draw.text((x + 16, y + header_card_h // 2), conf['title'], font=table_label_font, fill=(255, 255, 255), anchor="lm")
        
        # Paste image
        canvas.paste(img_resized, (x, y + header_card_h))

# Draw Footer
draw.line([(0, H - footer_h), (W, H - footer_h)], fill=(245, 158, 11), width=3)
draw.rectangle([(0, H - footer_h), (W, H)], fill=(12, 18, 34))
footer_text = "🎉 CHÚC BAN LÃNH ĐẠO VÀ TOÀN THỂ ANH CHỊ EM CÔNG TY MBC ĐOÀN KẾT - VỮNG MẠNH - ĐẠI THẮNG 2026! 🍻"
draw.text((W // 2, H - footer_h // 2), footer_text, font=footer_font, fill=(251, 191, 36), anchor="mm")

# Save high quality JPEG
canvas.save(output_path, 'JPEG', quality=95)
print(f"SUCCESS: Created Grand 4K Panorama Poster at: {output_path} (Size: {os.path.getsize(output_path)} bytes)")
