# -*- coding: utf-8 -*-
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw, ImageFont

base_dir = r"c:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\MBC\CreateImg"
scenes_dir = os.path.join(base_dir, "generated_scenes")
output_path = os.path.join(scenes_dir, "dai_tiec_5_ban_vuong.jpg")

W, H = 3840, 2160
canvas = Image.new("RGB", (W, H), (15, 23, 42))
draw = ImageDraw.Draw(canvas)

# Create rich festive background gradient
for y in range(H):
    r = int(14 + (y / H) * 22)
    g = int(20 + (y / H) * 16)
    b = int(38 - (y / H) * 18)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

def get_font(size, bold=True):
    font_names = ['segoeuib.ttf', 'arialbd.ttf', 'tahoma.ttf'] if bold else ['segoeui.ttf', 'arial.ttf', 'tahoma.ttf']
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except:
            pass
    return ImageFont.load_default()

title_font = get_font(80, bold=True)
sub_font = get_font(38, bold=False)
table_title_font = get_font(32, bold=True)
footer_font = get_font(34, bold=True)

# Top Header Banner
header_h = 230
draw.rectangle([(0, 0), (W, header_h)], fill=(12, 18, 34))
draw.line([(0, header_h), (W, header_h)], fill=(245, 158, 11), width=5)

draw.text((W // 2, 70), "🍻 ĐẠI TIỆC NHẬU CÔNG TY MBC 2026 - TOÀN CẢNH 5 BÀN VUÔNG 🍻", font=title_font, fill=(251, 191, 36), anchor="mm")
draw.text((W // 2, 155), "HỘI TỤ BAN LÃNH ĐẠO & CÁC PHÒNG BAN • BÀN VUÔNG 6 GHẾ • 1 - 2 - 3... ZÔ 100%!", font=sub_font, fill=(241, 245, 249), anchor="mm")

margin_x = 70
margin_y = 265
footer_h = 95
avail_w = W - margin_x * 2
avail_h = H - margin_y - footer_h

gap_x = 45
gap_y = 35

card_w = (avail_w - gap_x * 2) // 3
card_h = (avail_h - gap_y) // 2

tables_5_conf = [
    # Hàng trên: 3 bàn
    {
        'file': 'slide_ban1_vip.jpg',
        'title': '⭐ BÀN 1: BÀN VIP LÃNH ĐẠO & TẤN SỸ QUA MỜI SẾP',
        'color': (245, 158, 11),
        'row': 0, 'col': 0
    },
    {
        'file': 'slide_ban2_thucthan.jpg',
        'title': '🍗 BÀN 2: THỰC THẦN ĐÙI GÀ & THẦY BÓI TIỆC NHẬU',
        'color': (239, 68, 68),
        'row': 0, 'col': 1
    },
    {
        'file': 'slide_ban3_chiem.jpg',
        'title': '💃 BÀN 3: HỘI CHỊ EM RẠNG RỠ & SELFIE SỐNG ẢO',
        'color': (236, 72, 153),
        'row': 0, 'col': 2
    },
    # Hàng dưới: 2 bàn căn giữa
    {
        'file': 'slide_ban4_suachua.jpg',
        'title': '🍨 BÀN 4: NỮ DOANH NHÂN SỮA CHUA & ANH CHÀNG BÓC TÔM',
        'color': (16, 185, 129),
        'row': 1, 'col': 0, 'center_row': True
    },
    {
        'file': 'slide_ban5_bolero.jpg',
        'title': '🎤 BÀN 5: BAN NHẠC BOLERO & TUYỆT ĐỈNH RÓT BIA',
        'color': (139, 92, 246),
        'row': 1, 'col': 1, 'center_row': True
    }
]

# Tính vị trí căn giữa cho 2 bàn ở hàng dưới
row2_total_w = card_w * 2 + gap_x
row2_start_x = (W - row2_total_w) // 2

for conf in tables_5_conf:
    if conf.get('center_row'):
        x = row2_start_x + conf['col'] * (card_w + gap_x)
    else:
        x = margin_x + conf['col'] * (card_w + gap_x)
        
    y = margin_y + conf['row'] * (card_h + gap_y)
    
    img_p = os.path.join(scenes_dir, conf['file'])
    if os.path.exists(img_p):
        t_img = Image.open(img_p).convert("RGB")
        header_card_h = 44
        img_avail_h = card_h - header_card_h
        
        t_resized = t_img.resize((card_w, img_avail_h), Image.Resampling.LANCZOS)
        
        # Khung viền kim loại ánh vàng
        draw.rectangle([(x - 4, y - 4), (x + card_w + 4, y + card_h + 4)], outline=conf['color'], width=4)
        # Header thẻ bàn
        draw.rectangle([(x, y), (x + card_w, y + header_card_h)], fill=(20, 29, 47))
        draw.line([(x, y + header_card_h), (x + card_w, y + header_card_h)], fill=conf['color'], width=2)
        # Tên bàn
        draw.text((x + 16, y + header_card_h // 2), conf['title'], font=table_title_font, fill=(255, 255, 255), anchor="lm")
        # Dán ảnh bàn
        canvas.paste(t_resized, (x, y + header_card_h))

# Footer
draw.line([(0, H - footer_h), (W, H - footer_h)], fill=(245, 158, 11), width=3)
draw.rectangle([(0, H - footer_h), (W, H)], fill=(12, 18, 34))
footer_msg = "🎉 CHÚC BAN LÃNH ĐẠO VÀ TOÀN THỂ ANH CHỊ EM CÔNG TY MBC ĐOÀN KẾT - GẮN BÓ - ĐẠI THẮNG 2026! 🍻"
draw.text((W // 2, H - footer_h // 2), footer_msg, font=footer_font, fill=(251, 191, 36), anchor="mm")

canvas.save(output_path, "JPEG", quality=95)
print(f"SUCCESS: Created Grand 4K Panorama Poster at: {output_path} ({os.path.getsize(output_path)} bytes)")
