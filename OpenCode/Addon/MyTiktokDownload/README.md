# 🎵 TikTok Downloader (yt-dlp Edition)

**Tải video TikTok bằng yt-dlp** — Bypass hoàn toàn TikTok API, không bị lỗi `Error @ Mar695` hay `some component in the tiktok server is temporarily unstable`.

Hệ thống quản lý video có **SQLite index**, **tìm kiếm**, **xuất CSV/JSON**, **tránh trùng lặp** — tương tự cấu trúc myfaveTT_viewer.

---

## ✨ Tính năng chính

| Tính năng | Mô tả |
|-----------|-------|
| 📥 **Download** | Tải video từ URL (hàng loạt), resume, progress bar |
| 🔍 **Index & Search** | SQLite database, tìm theo từ khóa/tác giả/category/status |
| 🚫 **Anti-duplicate** | Tự động bỏ qua video đã tải (so sánh video_id + category) |
| 📤 **Export** | CSV / JSON (format giống myfaveTT) |
| 🔑 **Auto-cookie** | Lấy cookie TikTok từ Chrome profile tự động |
| 🚀 **Full Sync** | Fetch Likes/Favorites từ TikTok API + tải xuống (cần cookie) |
| 📊 **Stats** | Thống kê theo category, tác giả, dung lượng |
| ⚙️ **Configurable** | Rate limit, retries, output folder, skip existing |

---

## 🚀 Cài đặt & Chạy

### Yêu cầu
- Python 3.8+
- FFmpeg (yt-dlp sẽ tự tải nếu thiếu)
- Chrome/Edge đã đăng nhập TikTok (để lấy cookie)

### Chạy
```bash
# Double-click:
sync_and_download.bat

# Hoặc:
python sync_and_download.py
```

---

## 📖 Hướng dẫn sử dụng

### Menu chính (khi chạy `sync_and_download.bat`):
```
========================================
TikTok Downloader - Sync & Download
========================================

  1. 📥 Download video(s) from URLs
  2. 🔍 Search / View downloaded videos
  3. 📤 Export to CSV / JSON
  4. 🔑 Auto-detect TikTok cookies from Chrome
  5. ⚙️  Settings
  6. 📊 Show statistics
  7. 🚀 Full sync: Fetch Likes/Favorites + Download
  0. Exit
```

---

### 1. 📥 Download video từ URLs
- Chọn **1** → Nhập URLs (mỗi dòng 1 link)
- Hỗ trợ: `tiktok.com/@user/video/123`, `vm.tiktok.com/abc`, `vt.tiktok.com/xyz`
- Tự động bỏ qua video đã tải (tránh trùng)

### 2. 🔍 Search / View videos
- Chọn **2** → Tìm theo từ khóa, tác giả, category (manual/likes/favorites), status
- Xem danh sách có phân trang, hiển thị size, ngày tải

### 3. 📤 Export dữ liệu
- Chọn **3** → Chọn CSV hoặc JSON
- **JSON format myfaveTT**: Tương thích với myfaveTT_viewer
- **CSV**: Dễ mở Excel, phân tích

### 4. 🔑 Auto-detect Cookie (QUAN TRỌNG)
- Chọn **4** → Tự tìm cookie TikTok từ Chrome profile
- **Yêu cầu**: Đã đăng nhập TikTok trên Chrome
- Cookie lưu vào `settings.json` + export `cookies_tiktok.txt` (Netscape format)

### 5. ⚙️ Settings
- Output folder, Rate limit (1M/500K), Retries, Skip existing, Subfolder per author

### 6. 📊 Statistics
- Tổng video, thành công/thất bại/bỏ qua, dung lượng, số tác giả, theo category

### 7. 🚀 Full Sync (LIKES + FAVORITES)
- **Cần cookie** (chạy mode 4 trước)
- Fetch từ TikTok API `api/post/item_list/` (giống myfaveTT extension)
- Tải xuống tất cả Likes + Favorites một lần

---

## 📂 Cấu trúc thư mục

```
MyTiktokDownload/
├── sync_and_download.bat      ← CHẠY FILE NÀY (menu chính)
├── sync_and_download.py       ← Entry point Python
├── README.md                  ← File này
├── ProjectLog.md              ← Ghi chú kỹ thuật
├── settings.json              ← Cài đặt (tự tạo)
├── cookies_tiktok.txt         ← Cookie Netscape format (tự tạo)
├── requirements.txt
├── src/
│   ├── downloader.py          ← Core: TikTokDownloader, VideoIndex, VideoInfo
│   └── main.py                ← CLI modes: download/view/export/cookies/settings/stats/full-sync
└── downloads/                 ← Thư mục output (tự tạo)
    ├── video_index.db         ← SQLite index
    ├── @author1/
    │   ├── video1.mp4
    │   ├── video1.jpg
    │   └── video1.info.json
    └── @author2/
        └── ...
```

---

## 🛡️ Anti-duplicate (Tránh tải trùng)

Hệ thống **tự động kiểm tra** trước khi tải:
1. So sánh `video_id` + `category` trong SQLite index
2. Nếu đã có `status = completed` → **Skip** (hiển thị ⏭️)
3. Chỉ tải video mới hoặc video failed

> 💡 `category`: `manual` (URL thủ công), `l` (Likes), `b` (Favorites/Bookmarks)

---

## 📤 Export Format

### CSV (mở Excel)
```csv
video_id,url,title,author,author_id,duration,view_count,like_count,comment_count,create_time,downloaded_at,file_path,file_size,category
```

### JSON (format myfaveTT)
```json
{
  "updated": "2026-10-11T10:30:00Z",
  "stats": { "fav": 1500, "likes": 800, "authors": 50 },
  "authors": [
    {
      "id": "authorId",
      "u": "username",
      "n": "Display Name",
      "b": [["videoId", unixTimestamp], ...],
      "l": [["videoId", unixTimestamp], ...]
    }
  ]
}
```
> Tương thích để copy vào `myfaveTT_viewer/webapp/data.json`

---

## 🔧 Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| `Video unavailable` | Video private/đã xóa | Không thể tải |
| `Sign in to confirm age` | Video 18+ | Cookie phải từ tài khoản 18+ |
| `Rate limited` | TikTok chặn IP | Giảm Rate Limit về 500K, bật VPN |
| `FFmpeg not found` | Thiếu FFmpeg | yt-dlp tự tải, hoặc `winget install ffmpeg` |
| `No cookie found` | Chưa đăng nhập TikTok trên Chrome | Đăng nhập → chạy mode 4 lại |

---

## 💡 Tips & Best Practices

1. **Rate Limit**: Để `1M` (1MB/s) bình thường, giảm `500K` nếu bị chặn
2. **Cookie**: Đăng nhập TikTok trên Chrome → chạy mode 4 → tự động lấy
3. **Video 18+**: Cookie phải từ tài khoản đã verify 18+
4. **Private video**: Không thể tải (cần quyền truy cập)
4. **Backup**: Copy `downloads/video_index.db` và `settings.json` định kỳ

---

## 📜 License

MIT — Free to use, modify, distribute.

---

**Built with:** Python, yt-dlp, CustomTkinter, SQLite  
**Inspired by:** myfaveTT extension & myfaveTT_viewer  
**Bypasses:** TikTok API restrictions, Mar695 error, rate limiting