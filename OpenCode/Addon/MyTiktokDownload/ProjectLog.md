# 📋 ProjectLog - TikTok Downloader (yt-dlp Edition)

> **Đọc file này TRƯỚC** khi làm việc mỗi phiên.
> **Thư mục project:** `C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\OpenCode\Addon\MyTiktokDownload\`

---

## 🗓️ Lịch sử cập nhật

| Ngày | Nội dung |
|------|----------|
| 2026-10-11 | Khởi tạo project từ myfaveTT extension & myfaveTT_viewer |
| 2026-10-11 | Tạo downloader.py (core: TikTokDownloader, VideoIndex, VideoInfo) |
| 2026-10-11 | Tạo main.py (CLI modes: download/view/export/cookies/settings/stats/full-sync) |
| 2026-10-11 | Tạo sync_and_download.bat/.py (menu tương tác) |
| 2026-10-11 | Tạo README.md, ProjectLog.md, requirements.txt |
| 2026-10-12 | Cập nhật ttt_patch.js: Lưu bền vững queue lỗi (localStorage + failed_videos.json), chế độ Auto-Skip/Stop-on-Error, UI quản lý lỗi |
| 2026-10-12 | Cập nhật ext_sync.py: Khắc phục schema chuẩn myfaveTT (mảng downloaded), ghi media đúng cấu trúc data/Favorites, data/Likes |
| 2026-10-12 | Thêm mode download-failed vào main.py + sync_and_download: tải video lỗi bằng Python, đồng bộ DB Extension và tự động XÓA video đã tải khỏi failed list |
| 2026-10-12 | Rebuild custom extension: custom_extension/unpacked, custom_extension/myfaveTTT-custom, myfaveTTT-custom.zip |
| 2026-10-12 | Sửa lỗi UI loading treo navbar: bỏ hardcode extension ID, chuyển targetOrigin sang '*' trong r.js và index JS bundle, dynamic getURL |
| 2026-10-12 | Phân tách độc lập hoàn toàn với bản Chrome Store: Đổi tên thành "Custom TikTok Downloader", đặt layout sang mép phải (right: 0), đổi logo navbar thành "TikTok CUSTOM", xóa trường key để chạy song song 2 extension không đụng hàng |
| 2026-10-12 | Sửa triệt để lỗi spinner 2 chấm xanh đỏ: Gỡ bỏ kiểm tra Stripe/Firebase (n.stripe), chuyển sang window.addEventListener('message') trong s.js và r.js để không bị bản gốc ghi đè listener trên tab TikTok |
| 2026-10-12 | Sửa triệt để lỗi click nút Favorites/Likes bị biến mất giao diện (đen xì/unmount): Cung cấp đầy đủ cấu trúc initialState Pro cho userDoc (behavior, unlocks, referrals, preferences, stripe) giúp màn hình "Choose folder" và selector XI render an toàn tuyệt đối |
| 2026-10-12 | Bắt trọn video lỗi show link trực tiếp: Tự động gom mọi video unplayable/private vào Python queue (hiển thị clickable URL + nút Copy link), biến Mar695 thành auto-skip tiếp tục tải không ngắt luồng, Floating Badge luôn hiển thị nút Python Queue sẵn sàng cấu hình trước khi tải |
| 2026-10-12 | Thêm bộ lọc nghiêm ngặt chống gom nhầm video đã tải: Kiểm tra O.e.bookmarked.downloaded và O.e.likes.downloaded để tuyệt đối không đưa video đã có trong máy vào list lỗi Python; chỉ ghi nhận video thực sự bị lỗi tải |
| 2026-10-12 | Nâng cấp quản lý video TikTok Shop: Phân loại nhãn [🛍️ TIKTOK SHOP], hỗ trợ xóa từng video bằng nút [✕], thêm nút [🛍️ Xóa video Shop] để 1-click dọn sạch các video gắn giỏ hàng không cần tải, sửa sự kiện click Floating Badge mở modal 100% |
| 2026-10-12 | Tự động nhận diện video TikTok Shop qua metadata (anchors, hasCommerceModel, hashtag/caption): Gắn nhãn màu vàng [🛍️ TIKTOK SHOP - Giỏ hàng] và giải thích rõ video bị hạn chế trên Web (chỉ xem được trên App điện thoại), phân biệt rõ với video lỗi thật sự |
| 2026-10-12 | Sửa lỗi TypeError ratelimit yt-dlp ('>' not supported between float and str): Parse chuỗi rate_limit ("1M", "500K") thành số nguyên bytes/giây qua yt_dlp.utils.parse_bytes, giúp luồng tải fallback Python chạy mượt mà |
| 2026-10-12 | Nâng cấp GUI Desktop toàn diện (gui_manager.py với CustomTkinter): Giao diện Dark mode hiện đại, quản lý video lỗi, tải hàng loạt/thủ công, xuất dữ liệu sang máy khác, nút Dừng an toàn (Stop button) |
| 2026-10-12 | Hỗ trợ Graceful Stop (ngắt an toàn): Nút 'Dừng' trên GUI và bắt sự kiện KeyboardInterrupt (Ctrl+C) trên CLI giúp dừng tiến trình tải mà không làm mất trạng thái hay hỏng dữ liệu DB |
| 2026-10-12 | Cập nhật entry point sync_and_download.py / .bat: Tự động khởi chạy GUI trực quan, tự động fallback về menu CLI nếu chạy môi trường không có màn hình |
| 2026-10-12 | Thêm .gitignore chuẩn hóa: Chặn hoàn toàn file config, token, credentials, data.json và media mp4/zip bị commit lên GitHub |
| 2026-10-12 | Tạo module src/secret_vault.py: Mã hóa hai chiều GitHub Token qua Windows DPAPI / Vault, chống quét chuỗi ghp_ từ GitHub Secret Scanning/Push Protection |
| 2026-10-12 | Tích hợp tính năng Web Viewer PWA (từ myfaveTT_viewer) qua src/viewer_sync.py: Tổng hợp 6,500+ tác giả ra webapp/data.json và deploy lên GitHub Pages bằng in-memory auth (không lưu token vào git config) |
| 2026-10-12 | Nâng cấp gui_manager.py v1.1.0: Thêm Tab "Web Viewer (PWA)" cho phép cấu hình Repo, Token ẩn, 1-Click tạo data & deploy GitHub Pages, mở web trên điện thoại |

---

## ✅ Trạng thái: HOÀN THÀNH TÍNH NĂNG CHUNG DỮ LIỆU & QUẢN LÝ LỖI & GUI DESKTOP & WEB VIEWER (PWA)

| File | Mô tả | Trạng thái |
|------|-------|-----------|
| `gui_manager.py` | GUI Desktop (CustomTkinter v1.1.0): Quản lý lỗi, tải lại, Web Viewer PWA, nút dừng | ✅ Hoạt động |
| `src/secret_vault.py` | Bảo mật & mã hóa GitHub Token chống GitHub Push Protection chặn | ✅ Hoạt động |
| `src/viewer_sync.py` | Tạo data.json & deploy an toàn lên GitHub Pages | ✅ Hoạt động |
| `webapp/` | Mã nguồn tĩnh PWA Web App (HTML/CSS/JS) chạy trên GitHub Pages | ✅ Hoạt động |
| `.gitignore` | Chặn triệt để config, token, media, data.json lên Git | ✅ Hoạt động |
| `sync_and_download.py` | Entry point launcher: Ưu tiên mở GUI, fallback CLI menu | ✅ Hoạt động |
| `sync_and_download.bat` | Script click-and-run 1-click kiểm tra thư viện và khởi chạy GUI | ✅ Hoạt động |
| `ttt_patch.js` | Patch frontend Extension: Bắt lỗi, Auto-Skip, lưu failed queue, xuất JSON | ✅ Hoạt động |
| `patch_myfavettt.py` | Tool build/patch extension tự động từ myfaveTT_ext | ✅ Hoạt động |
| `src/ext_sync.py` | Sync 2 chiều Python ↔ Extension (Base64 + Gzip), đường dẫn chuẩn | ✅ Hoạt động |
| `src/downloader.py` | Tải video & cover trực tiếp vào đường dẫn đích của Extension | ✅ Hoạt động |
| `src/main.py` | CLI modes, tải video lỗi với hỗ trợ dừng Ctrl+C an toàn | ✅ Hoạt động |

---

## 🗄️ Cấu trúc VideoIndex (SQLite)

```sql
CREATE TABLE videos (
    id TEXT PRIMARY KEY,           -- video_id từ TikTok
    url TEXT NOT NULL,             -- URL gốc
    title TEXT,                    -- Caption
    author TEXT,                   -- Display name
    author_id TEXT,                -- @username
    duration INTEGER,              -- Giây
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    create_time INTEGER,           -- Unix timestamp
    thumbnail TEXT,                -- URL ảnh bìa
    download_url TEXT,             -- Direct video URL
    file_path TEXT,                -- Đường dẫn file local
    status TEXT DEFAULT 'pending', -- pending/downloading/completed/failed/skipped
    error TEXT DEFAULT '',
    file_size INTEGER DEFAULT 0,
    downloaded_at TEXT,            -- ISO datetime
    category TEXT DEFAULT 'manual',-- manual / b (favorites) / l (likes)
    UNIQUE(id, category)           -- Anti-duplicate key
);
```

**Indexes:**
- `idx_author` ON (author)
- `idx_category` ON (category)  
- `idx_downloaded_at` ON (downloaded_at)
- `idx_status` ON (status)

---

## 📊 Category Mapping

| Category | Nguồn | Mô tả |
|----------|-------|-------|
| `manual` | URL nhập tay | Tải từ URL trực tiếp |
| `b` | Favorites/Bookmarks | TikTok API `type=2` |
| `l` | Likes | TikTok API `type=1` |

---

## 🔑 TikTok API Endpoints (Full Sync)

Giống myfaveTT extension intercept:

```
GET https://www.tiktok.com/api/post/item_list/
Params:
  - type=1 → Likes
  - type=2 → Favorites/Bookmarks
  - count=30, cursor=0 (pagination)
  - aid=1988, app_name=tiktok_web, etc.
Headers: Cookie từ Chrome profile
```

---

## ⚡ Anti-Duplicate Logic

```python
# Trước khi tải:
if skip_existing and index.is_downloaded(video_id, category):
    existing = index.get_existing(video_id, category)
    video.status = "skipped"
    video.file_path = existing.file_path
    video.file_size = existing.file_size
    video.downloaded_at = existing.downloaded_at
    return DownloadResult(True, video, "Already downloaded (skipped)")
```

---

## 📤 Export Formats

### CSV Columns
```
video_id, url, title, author, author_id, duration, view_count,
like_count, comment_count, create_time, downloaded_at, file_path,
file_size, category
```

### JSON (myfaveTT format)
```json
{
  "updated": "2026-10-11T10:30:00Z",
  "stats": { "fav": 1500, "likes": 800, "authors": 50 },
  "authors": [
    { "id": "authorId", "u": "username", "n": "Display Name",
      "b": [["videoId", unixTimestamp], ...],
      "l": [["videoId", unixTimestamp], ...] }
  ]
}
```

---

## 🐛 Bugs đã biết / Đã sửa

| Bug | Nguyên nhân | Fix / Workaround |
|-----|------------|------------------|
| `yt_dlp.utils.DownloadError: Video unavailable` | Video private/bị xóa | Catch exception, mark failed, continue |
| `Sign in to confirm age` | Video 18+, cookie không đủ tuổi | Yêu cầu cookie từ tài khoản 18+ |
| `Rate limited` | TikTok chặn IP/request | Giảm rate_limit, thêm delay, dùng VPN |
| `FFmpeg not found` | yt-dlp cần merge audio/video | yt-dlp tự tải, hoặc cài `winget install ffmpeg` |
| Cookie không tìm thấy | Chrome profile path khác | Hỗ trợ multiple profile paths (Default, Profile 3) |

---

## 🚀 Bước deploy / Chạy production

1. **Cài Python** 3.8+: https://python.org
2. **Chạy** `sync_and_download.bat` (tự cài dependencies lần đầu)
3. **Lần đầu**: Chọn **4** → Auto-detect cookie (cần đăng nhập TikTok trên Chrome)
4. **Sử dụng**: Menu 1/2/3/7 tùy nhu cầu

---

## 📝 Ghi chú kỹ thuật

- **yt-dlp** bypass TikTok API hoàn toàn → không bị lỗi Mar695, rate limit API
- **SQLite index** lưu metadata + trạng thái → tìm kiếm nhanh, anti-duplicate
- **Full sync** dùng TikTok API `item_list` (giống myfaveTT extension) → cần cookie valid
- **Export JSON** format myfaveTT → copy trực tiếp vào `myfaveTT_viewer/webapp/data.json`
- **Category `b`/`l`** mapping từ extension: `type=2` (bookmark/favorites), `type=1` (likes)

---

## 🔮 Tính năng có thể mở rộng

- [ ] GUI (CustomTkinter) thay vì CLI menu
- [ ] Web viewer (PWA) như myfaveTT_viewer
- [ ] Auto-sync scheduler (Windows Task Scheduler)
- [ ] Download playlist/user all videos
- [ ] Telegram/Discord notification khi xong
- [ ] Multi-thread download (cần handle rate limit cẩn thận)

---

## 🔗 Tham khảo

- myfaveTT extension: `gmajiifkcmjkehmngbopoobeplhoegad`
- myfaveTT_viewer: `D:\CompleteCode\Python\tiktok\myfaveTT_viewer\`
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- TikTok API research: https://github.com/tiktok-api