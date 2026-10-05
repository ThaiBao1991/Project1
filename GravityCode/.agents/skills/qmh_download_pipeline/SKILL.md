---
name: qmh_download_pipeline
description: >
  Hướng dẫn đầy đủ về cách tải video từ các trang thuộc gia đình qmh (qmh.lat, qmh.hair, qmh.mom, v.v.)
  bao gồm cấu trúc API, pipeline tải, các chiến lược fallback, DNS bypass và cách thêm site mới.
---

# QMH Video Download Pipeline

## Tổng quan

Các trang qmh.* (qmh.lat, qmh.hair, qmh.mom, ...) là Single Page App Angular.
**Không cần browser/Selenium** — tất cả dùng REST API.

---

## Cấu trúc API (2026-07 CONFIRMED)

### qmh.lat / qmh.mom / qmh.asia / ...
| Endpoint | Mô tả |
|---|---|
| `GET /api/video?page=N&limit=10` | Danh sách video (10/trang) |
| `GET /api/video/{id}` | Chi tiết video (có `sourceM3u8Url`) |

### qmh.hair (API backend mới từ 2026-07)
| Endpoint | Mô tả |
|---|---|
| `GET https://api.s3hubqmh.online/api/video?page=N&limit=10` | Danh sách |
| `GET https://api.s3hubqmh.online/api/video/{id}` | Chi tiết |

**Cấu trúc JSON response giống nhau hoàn toàn.**

---

## Pipeline tải video (S0 — iOS Manifest, ưu tiên nhất)

```
1. Gọi API detail: GET {api_base}/video/{id}
   → nhận: sourceM3u8Url = "/public/m3u8/{hash}.m3u8"

2. Build URL embed player:
   url = embed_player_base + sourceM3u8Url
   → vd: "https://quaymanhinh.online/public/m3u8/abc123.m3u8"

3. Gọi iOS manifest proxy:
   GET {embed_player_base}/api/v1/tiktok/proxy/ios-manifest
       ?url={url_encoded}
   Headers: User-Agent iPhone, Referer: {embed_player_base}/
   → Trả về m3u8 SẠCH từ TikTok CDN (p16-sg.tiktokcdn.com)

4. Tải đa luồng các segment:
   - Dùng concurrent.futures, max_workers=5
   - Mỗi segment: nếu bắt đầu bằng b'\x89PNG' → cắt bỏ tới IEND+8
   - Ghép nối thành .ts

5. Convert: ffprobe kiểm tra codec → ffmpeg convert sang .mp4
   - h264/hevc: copy thẳng (nhanh)
   - mpeg2video/mpeg4: re-encode libx264 (chậm hơn nhưng tương thích)

6. Validate magic bytes: tránh Cloudflare restriction video (mpeg2video 640x480)
```

---

## Thứ tự chiến lược (DEFAULT_STRATEGY_ORDER)

| Ưu tiên | Strategy | Mô tả |
|---|---|---|
| 1 | `strategy_ios_manifest` (S0) | iOS manifest + PNG bypass — **tốt nhất** |
| 2 | `strategy_cdn_m3u8_ytdlp` (S_CDN) | CDN m3u8 + yt-dlp |
| 3 | `strategy_ytdlp_mp4` (S2) | CDN mp4 trực tiếp |
| 4 | `strategy_auto_cdn_mp4` (S4) | Tự tìm CDN mp4 |
| 5 | `strategy_requests_mp4` (S6) | Raw stream mp4 |
| 6 | `strategy_ytdlp_m3u8` (S1) | CDN m3u8 mặc định |
| 7 | `strategy_auto_cdn_m3u8` (S3) | Tự tìm CDN m3u8 |
| 8 | `strategy_cdn_png_m3u8` (S3_5) | PNG bypass từ CDN |
| 9 | `strategy_ytdlp_embed_m3u8` (S0_1) | yt-dlp sourceM3u8Url |
| 10 | `strategy_ytdlp_ios_manifest` (S0_2) | yt-dlp ios manifest |
| 11 | `strategy_api_detail` (S5) | API cdnHlsUrl/backblazeUrl |
| 12 | `strategy_selenium_extract_m3u8` (S6_5) | Browser intercept |
| 13 | `strategy_selenium_capture` (S7) | MediaRecorder (chót) |

---

## Vấn đề đã biết & cách xử lý

### 1. DNS Spoofing (ISP Việt Nam)
quaymanhinh.online bị nhà mạng trả về 127.0.0.1 → bypass bằng hardcode Cloudflare IP:
```python
# Trong strategies.py
if host == "quaymanhinh.online":
    return [(AF_INET, SOCK_STREAM, 6, '', ("104.21.41.98", port))]
```

### 2. FFmpeg lỗi với tên file tiếng Việt (Windows)
→ Đổi tên TS sang ASCII tạm (`_tmp_{uuid}.ts`) trước khi gọi FFmpeg, sau đó rename lại.

### 3. Cloudflare Restriction Video (mpeg2video 640x480)
→ `_probe_hls_segment()` kiểm tra segment đầu tiên trước khi tải.
→ `_validate_video_file()` kiểm tra magic bytes + ffprobe sau khi tải.
→ Nếu phát hiện → xóa file, return False, thử strategy tiếp theo.

### 4. Segment PNG-encrypted
Các segment TikTok CDN có header PNG giả (1x1 pixel). Cách xử lý:
```python
if content.startswith(b'\x89PNG\r\n\x1a\n'):
    iend = content.find(b'IEND')
    if iend != -1:
        content = content[iend + 8:]  # Cắt bỏ PNG header
```

---

## Cách thêm site mới (kế thừa qmh.lat)

### Qua config.json (không cần code):
```json
"site_aliases": {
  "qmh.newsite": {
    "base_site": "qmh.lat",
    "display_name": "QMH NewSite",
    "site_url": "https://qmh.newsite",
    "api_base": "https://qmh.newsite/api",
    "embed_player_base": "https://quaymanhinh.online",
    "cdn_bases": ["https://video.s3viphub.shop", "https://cdn.qmh.lat"]
  }
}
```

### Lưu ý quan trọng về variants.py
`_make_variant_class()` PHẢI truyền `embed_player_base` khi tạo dynamic class,
nếu không site mới sẽ dùng embed player sai (bug đã fix 2026-07).

---

## Custom Sites (do AI cấu hình tự động)

Nếu trang web có kiến trúc hoàn toàn lạ (HTML/JSON tùy chỉnh), AI sẽ sinh ra cấu hình kiểu:
```json
"viet69.be": {
  "type": "html",
  "list_item_selector": ".item-video",
  "title_selector": ".entry-title a",
  "link_selector": ".entry-title a",
  "download_strategy": "sniffer",
  "site_type": "custom"
}
```
**Tính năng thông minh:**
- Trình trích xuất `GenericSite` tự động ưu tiên lấy `href` cho `link_selector` dù AI quên khai báo `@href`.
- Downloader tự động bật luồng bắt link `sniff_m3u8` cho bất kỳ site nào cấu hình `download_strategy: sniffer`, mở trình duyệt thật để vượt qua Cloudflare và truyền link nội bộ vào `yt-dlp`.

---

## CDN Bases theo site

| Site | CDN chính | API |
|---|---|---|
| qmh.lat, qmh.mom, qmh.asia... | `video.s3viphub.shop` | `{domain}/api` |
| qmh.hair (từ 2026-07) | `video.s3hubqmh.online` | `api.s3hubqmh.online/api` |

---

## Files quan trọng

| File | Vai trò |
|---|---|
| `sites/qmh_lat/plugin.py` | Plugin chính: gọi API, parse JSON |
| `sites/qmh_lat/strategies.py` | Tất cả chiến lược tải |
| `sites/qmh_lat/variants.py` | Tạo class động cho site alias |
| `core/downloader.py` | Multi-strategy runner + validate |
| `config.json` | Site aliases + CDN config |
| `PROJECT_MEMORY.md` | Toàn bộ context dự án |
