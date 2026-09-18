# -*- coding: utf-8 -*-
import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = r"c:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\MBC\CreateImg"
SCENES_DIR = os.path.join(BASE_DIR, "generated_scenes")
OUTPUT_PATH = os.path.join(SCENES_DIR, "phong_tiec_toan_canh_5_ban.jpg")

W, H = 3840, 2160

def cv2_imread_utf8(path):
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        data = np.frombuffer(f.read(), np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)

def cv2_imwrite_utf8(path, img, quality=95):
    ext = os.path.splitext(path)[1] or '.jpg'
    params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    success, buf = cv2.imencode(ext, img, params)
    if success:
        with open(path, 'wb') as f:
            f.write(buf)
    return success

def get_font(size, bold=True):
    names = ['segoeuib.ttf', 'arialbd.ttf', 'tahomabd.ttf'] if bold else ['segoeui.ttf', 'arial.ttf', 'tahoma.ttf']
    for fn in names:
        try:
            return ImageFont.truetype(fn, size)
        except:
            pass
    return ImageFont.load_default()

print("Bắt đầu dựng không gian phòng tiệc toàn cảnh 5 bàn (3840x2160)...")

# 1. Dựng nền không gian phòng tiệc cao cấp với chiều sâu phối cảnh (Perspective Banquet Hall)
hall = np.zeros((H, W, 3), dtype=np.uint8)

# Tạo bầu trời đêm qua khung kính panorama
for y in range(int(H * 0.45)):
    ratio = y / (H * 0.45)
    r = int(10 + ratio * 25)
    g = int(14 + ratio * 20)
    b = int(32 + ratio * 20)
    hall[y, :] = (b, g, r)

# Thêm ánh đèn thành phố lung linh (city skyline bokeh)
np.random.seed(42)
for _ in range(160):
    cx = np.random.randint(100, W - 100)
    cy = np.random.randint(int(H * 0.15), int(H * 0.42))
    rad = np.random.randint(4, 18)
    color = (
        np.random.randint(100, 220), # B
        np.random.randint(160, 240), # G
        np.random.randint(220, 255)  # R
    )
    cv2.circle(hall, (cx, cy), rad, color, -1)

hall = cv2.GaussianBlur(hall, (35, 35), 18)

# Dựng sàn gỗ nhà hàng tiệc với các đường phối cảnh tụ về trung tâm
floor_y_start = int(H * 0.40)
for y in range(floor_y_start, H):
    ratio = (y - floor_y_start) / (H - floor_y_start)
    # Tông gỗ ấm áp
    r = int(45 + ratio * 55)
    g = int(28 + ratio * 35)
    b = int(18 + ratio * 22)
    hall[y, :] = (b, g, r)

# Vẽ các đường rãnh sàn gỗ tụ về điểm vanishing point (W//2, H*0.35)
vp_x, vp_y = W // 2, int(H * 0.35)
for x_base in range(-W, W * 2, 140):
    cv2.line(hall, (vp_x, vp_y), (x_base, H), (14, 18, 28), 2, cv2.LINE_AA)

# Làm mịn sàn gỗ với ánh sáng bóng nhẹ
hall = cv2.GaussianBlur(hall, (3, 3), 1)

# Thêm xà gồ trần gỗ và đèn lồng treo đỏ lung linh ở trần
ceiling_h = int(H * 0.18)
for y in range(ceiling_h):
    ratio = y / ceiling_h
    hall[y, :] = (int(16 * (1 - ratio)), int(18 * (1 - ratio)), int(30 * (1 - ratio)))

# Dây đèn lồng đỏ giăng ngang trần phòng tiệc
for lantern_x in range(120, W - 100, 220):
    lantern_y = int(H * 0.10 + np.sin(lantern_x * 0.005) * 25)
    # Ánh sáng tỏa
    cv2.circle(hall, (lantern_x, lantern_y), 65, (30, 60, 220), -1)
    # Quả lồng đèn đỏ
    cv2.ellipse(hall, (lantern_x, lantern_y), (28, 38), 0, 0, 360, (40, 50, 245), -1)
    cv2.ellipse(hall, (lantern_x, lantern_y), (14, 38), 0, 0, 360, (60, 80, 255), -1)
    cv2.circle(hall, (lantern_x, lantern_y), 12, (120, 200, 255), -1)

# Áp dụng blur cho trần đèn lồng lung linh
hall[:int(H*0.22), :] = cv2.GaussianBlur(hall[:int(H*0.22), :], (21, 21), 9)

# 2. Định nghĩa vị trí 5 bàn tiệc trong phối cảnh 3D không gian phòng:
# Bàn 1 (VIP): Trung tâm tôn nghiêm, cao quý, đặt chính giữa
# Bàn 2 (Thực Thần): Tiền cảnh góc trái (gần người xem, kích thước lớn)
# Bàn 3 (Chị Em): Tiền cảnh góc phải (gần người xem, kích thước lớn)
# Bàn 4 (Sữa Chua): Trung cảnh bên trái (kết nối giữa bàn 1 và bàn 2)
# Bàn 5 (Bolero): Trung cảnh bên phải (kết nối giữa bàn 1 và bàn 3)

tables = [
    {
        'file': 'slide_ban1_vip.jpg',
        'title': '⭐ BÀN 1: BÀN VIP LÃNH ĐẠO & TẤN SỸ SANG MỜI RƯỢU',
        'pos': (W // 2, int(H * 0.44)), # Center stage
        'scale': (1440, 804),
        'glow_color': (0, 215, 255) # Vàng ánh kim VIP
    },
    {
        'file': 'slide_ban2_thucthan.jpg',
        'title': '🍗 BÀN 2: THỰC THẦN ĐÙI GÀ & THẦY BÓI TIỆC NHẬU',
        'pos': (int(W * 0.26), int(H * 0.77)), # Tiền cảnh trái
        'scale': (1320, 737),
        'glow_color': (40, 80, 240) # Đỏ cam tiệc nướng
    },
    {
        'file': 'slide_ban3_chiem.jpg',
        'title': '💃 BÀN 3: HỘI CHỊ EM RẠNG RỠ & SELFIE SỐNG ẢO',
        'pos': (int(W * 0.74), int(H * 0.77)), # Tiền cảnh phải
        'scale': (1320, 737),
        'glow_color': (180, 80, 255) # Hồng rạng rỡ
    },
    {
        'file': 'slide_ban4_suachua.jpg',
        'title': '🍨 BÀN 4: ĐẠI BẢN DOANH SỮA CHUA & ANH BÓC TÔM',
        'pos': (int(W * 0.16), int(H * 0.38)), # Trung cảnh trái
        'scale': (1080, 603),
        'glow_color': (60, 200, 100) # Xanh tươi mới
    },
    {
        'file': 'slide_ban5_bolero.jpg',
        'title': '🎤 BÀN 5: BAN NHẠC BOLERO & TUYỆT ĐỈNH RÓT BIA',
        'pos': (int(W * 0.84), int(H * 0.38)), # Trung cảnh phải
        'scale': (1080, 603),
        'glow_color': (220, 140, 60) # Tím xanh sân khấu
    }
]

# Thứ tự vẽ: Vẽ các bàn ở xa trước (Bàn 4, Bàn 5), sau đó Bàn 1 VIP ở giữa, rồi Bàn 2 & Bàn 3 ở tiền cảnh
draw_order = [3, 4, 0, 1, 2] # Index trong danh sách tables

for idx in draw_order:
    tb = tables[idx]
    p = os.path.join(SCENES_DIR, tb['file'])
    img = cv2_imread_utf8(p)
    if img is None:
        continue
    
    tw, th = tb['scale']
    img_resized = cv2.resize(img, (tw, th), interpolation=cv2.INTER_LANCZOS4)
    
    cx, cy = tb['pos']
    x1 = cx - tw // 2
    y1 = cy - th // 2
    x2 = x1 + tw
    y2 = y1 + th
    
    # 1. Đổ bóng 3D chân thực lên sàn nhà (Ambient Floor Shadow)
    shadow_pad = 28
    cv2.ellipse(hall, (cx, y2 - 8), (tw // 2 + shadow_pad, 55), 0, 0, 360, (8, 10, 15), -1)
    
    # 2. Tạo viền ánh sáng vàng ấm hòa quyện với đèn phòng (Light Bloom)
    cv2.rectangle(hall, (x1 - 6, y1 - 6), (x2 + 6, y2 + 6), tb['glow_color'], 4, cv2.LINE_AA)
    
    # Dán bàn vào không gian phòng tiệc
    # Cắt xén an toàn nếu tràn mép
    sx1 = max(0, x1)
    sy1 = max(0, y1)
    sx2 = min(W, x2)
    sy2 = min(H, y2)
    
    crop_x1 = sx1 - x1
    crop_y1 = sy1 - y1
    crop_x2 = crop_x1 + (sx2 - sx1)
    crop_y2 = crop_y1 + (sy2 - sy1)
    
    hall[sy1:sy2, sx1:sx2] = img_resized[crop_y1:crop_y2, crop_x1:crop_x2]

# Chuyển sang PIL để vẽ chữ tiêu đề và nhãn bảng tên sang trọng
pil_img = Image.fromarray(cv2.cvtColor(hall, cv2.COLOR_BGR2RGB))
draw = ImageDraw.Draw(pil_img)

# Banner tiêu đề đỉnh cao
header_h = 130
draw.rectangle([(0, 0), (W, header_h)], fill=(10, 15, 28, 240))
draw.line([(0, header_h), (W, header_h)], fill=(245, 158, 11), width=4)

main_title = "🍻 ĐẠI TIỆC CÔNG TY MBC 2026 - TOÀN CẢNH PHÒNG NHẬU 5 BÀN LIÊN HOÀN 🍻"
sub_title = "HỘI TỤ TOÀN THỂ NHÂN SỰ • BÀN VUÔNG 6 GHẾ • 5 TÌNH HUỐNG VUI NHỘN TRONG CÙNG KHÔNG GIAN ĐẠI TIỆC"

draw.text((W // 2, 42), main_title, font=get_font(52, bold=True), fill=(251, 191, 36), anchor="mm")
draw.text((W // 2, 95), sub_title, font=get_font(26, bold=False), fill=(226, 232, 240), anchor="mm")

# Vẽ nhãn tên bàn mạ vàng sang trọng dưới mỗi bàn tiệc
label_font = get_font(28, bold=True)
for idx in draw_order:
    tb = tables[idx]
    cx, cy = tb['pos']
    tw, th = tb['scale']
    y2 = cy + th // 2
    
    label_text = tb['title']
    bbox = draw.textbbox((cx, y2 + 22), label_text, font=label_font, anchor="mm")
    pad_x, pad_y = 20, 8
    pill_box = [(bbox[0] - pad_x, bbox[1] - pad_y), (bbox[2] + pad_x, bbox[3] + pad_y)]
    
    # Nền nhãn màu đen viền vàng sang trọng
    draw.rounded_rectangle(pill_box, radius=12, fill=(15, 23, 42), outline=(245, 158, 11), width=3)
    draw.text((cx, y2 + 22), label_text, font=label_font, fill=(255, 255, 255), anchor="mm")

# Lưu ảnh chất lượng cao 4K
pil_img.save(OUTPUT_PATH, quality=96)
print(f"SUCCESS: Đã tạo ảnh phòng nhậu toàn cảnh 5 bàn: {OUTPUT_PATH}")
print(f"Dung lượng file: {os.path.getsize(OUTPUT_PATH)} bytes")
