# myfaveTTT Custom (Stop on Error) - Cai dat & Su dung

Ban custom cua myfaveTT, chay song song voi ban goc. Tu dung tai video loi,
hien box loi (ma loi + link video + nut Copy link), khong tu bo qua video loi.

## 1. Go ban hong cu (bat buoc)

Neu truoc do da Load unpacked ban custom hong:
1. Mo `chrome://extensions/`
2. Xoa (Remove) ban "myfaveTTT Custom" cu
3. Tat Chrome han (de service worker cu giai phong)

## 2. Cai ban moi

1. Mo `chrome://extensions/`
2. Bat **Developer mode** (goc tren phai)
3. **Load unpacked** -> chon 1 trong 2 thu muc (noi dung giong het nhau):
   - `custom_extension/unpacked`
   - `custom_extension/myfaveTTT-custom`
4. Kiem tra: ten `myfaveTTT Custom (Stop on Error)`, version `1.12.70.1`,
   ID khac voi ban store `myfaveTT`

## 3. Test nhanh (2 phut)

1. Mo `https://www.tiktok.com/` (dang nhap tai khoan TikTok)
2. Sidebar mau trang hien ben trai, rong 390px
3. Bam icon extension tren toolbar -> phai mo tab TikTok moi
   (neu khong mo: mo DevTools (F12) -> Console xem loi, chup man hinh gui lai)
4. Trong sidebar: mo tab Favorites/Likes, bam Download
5. Neu co video loi: box thong bao hien o goc phai gom:
   - Che do **"Tu dong bo qua loi & gom vao list Python" (Auto-Skip)**: Neu bat, extension se khong dung ma tu dong ghi nhan video loi va tai tiep cac video khac.
   - Thong tin video loi: Ma loi, author, link, title.
   - Nut **Bo qua & Gom vao Python** / **Tiep tuc**.
   - Nut **Tai file failed_videos.json** / **Copy All**.
   - Nut **Tu don video xong**: Tu dong doi chieu voi database va xoa cac video ma Python da tai xong!

## 4. Workflow tai video loi bang Python (Dung chung 100% du lieu)

1. Khi dang tai bang Extension:
   - Neu bat `Auto-Skip`: Extension tu gom toan bo video loi vao `failed_videos.json` va tiep tuc tai cac video con lai.
   - Neu de mac dinh (Stop on error): Co the bam **"Bo qua & Gom vao Python"** de chay tiep.
2. Chay tool Python:
   - Double-click `sync_and_download.bat` -> Chon **1** (Tải danh sách video lỗi từ Extension).
   - Hoac qua command line:
     `python src/main.py --mode download-failed`
3. Tool Python se:
   - Tu dong doc `failed_videos.json`.
   - Dung `yt-dlp` tai file `.mp4` va anh cover `.jpg` vao dung thu muc cua Extension (`data/Favorites/...`, `data/Likes/...`).
   - Ghi cap nhat vao database Extension (`db_videos.js`, `db_bookmarked.js`, `db_likes.js`, `db_authors.js`).
   - **Tu dong XOA cac video da tai thanh cong khoi `failed_videos.json`**.
4. Khi mo lai Extension:
   - Extension doc database thay video da nam trong danh sach `downloaded` -> **Bo qua, khong bao gio tai lai**.
   - Tren box thong bao cua Extension: Bam **"Tu don video xong"** de dong bo lam sach giao dien.

## 5. Luu y

- Khong bat 2 ban (myfaveTT goc + myfaveTTT custom) tren CUNG 1 tab TikTok cung luc.
- Toan bo video va metadata duoc luu truc tiep theo cay thu muc archive (`data/Favorites`, `data/Likes`, `data/.appdata`), Python va Extension hoan toan dung chung 1 kho du lieu duy nhat.
- Muon build lai extension tu source goc: chay `python patch_myfavettt.py`.
