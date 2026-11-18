# Học trên điện thoại — kiến trúc, giới hạn, cách vận hành

> Cập nhật: 17/11/2026. Áp dụng cho repo `ThaiBao1991/Project1` (nhánh `master` + `gh-pages`).

## 1. Vì sao KHÔNG push thẳng dữ liệu lên git

Đo thật ngày 17/11/2026:

| Thành phần | Kích thước | Giới hạn GitHub |
|---|---|---|
| `data/ai_courses/<khóa>/course.json` | 8 file × 51–59 MB = **442,7 MB** | file > **100 MB bị chặn** push |
| `data/media/` | **211.549 file / 2.626,7 MB** | repo khuyến nghị < 1 GB, cảnh báo > 5 GB |
| `data/media/index.json` | **103,4 MB** | > 100 MB ⇒ **bị chặn** |
| Toàn bộ `data/` | ~476.546 file / **7.377 MB** | — |

⇒ Nếu commit trực tiếp: push thất bại (index.json 103 MB), repo phình > 10 GB,
`git clone` không dùng nổi trên điện thoại.

## 2. Kiến trúc 3 tầng đang dùng

```
┌──────────────────────────── ĐIỆN THOẠI ────────────────────────────┐
│  PWA (web/index.html)                                              │
│   • nội dung:  data/<khóa>/index.json + day/<n>.json   (~14 KB/ngày)│
│   • media:     gói .zip 30 ngày  (m01..m85, ~8–10 MB/gói)           │
│   • tiến độ:   localStorage (SRS SM-2 rút gọn)                     │
└───────────────┬──────────────────────────┬─────────────────────────┘
                │ HTTPS                    │ HTTPS (CORS)
        ┌───────▼────────┐        ┌────────▼─────────────┐
        │ GitHub Pages   │        │ GitHub Releases      │
        │ nhánh gh-pages │        │ 1 release / khóa     │
        │ ~360 MB, 20k file│      │ 85 asset, ~2,6 GB    │
        └────────────────┘        └──────────────────────┘
```

- **Pages** phục vụ app + nội dung từng ngày. Mỗi ngày ~14 KB (nội dung) +
  `media_map` (ref → đường dẫn file) ⇒ mở ngày rất nhanh, không tải 55 MB.
- **Releases** chứa media đóng gói theo **30 ngày** (`m01.zip` … `m85.zip`).
  Điện thoại chỉ tải gói của tháng đang học (~8–10 MB), giải nén **ngay trong
  trình duyệt** bằng `DecompressionStream` (không cần thư viện ngoài).
- **Tiến độ** nằm trên máy (localStorage), không cần server, không tốn băng thông.
  Đánh đổi: máy tính và điện thoại **không tự đồng bộ** tiến độ với nhau.

## 3. Vì sao dùng `api.github.com` để tải asset

Đo thật: `https://github.com/<repo>/releases/download/<tag>/m01.zip` bị **CORS
chặn** (`No 'Access-Control-Allow-Origin'`) khi fetch từ trình duyệt.
Cách đúng:

1. `GET https://api.github.com/repos/<repo>/releases/tags/<tag>` (có CORS) → lấy `asset.id`.
2. `GET https://api.github.com/repos/<repo>/releases/assets/<id>` với header
   `Accept: application/octet-stream` → nhận bytes.

## 4. Giới hạn cần biết (2026)

| Kênh | Giới hạn | Ta dùng |
|---|---|---|
| Git push | file ≤ 100 MB | mọi file Pages ≤ 60 MB |
| Repo | khuyến nghị < 1 GB, cảnh báo > 5 GB | repo hiện ~5,9 GB (lịch sử cũ) |
| Pages site | ≤ 1 GB, 100 GB/tháng (soft) | ~360 MB |
| Release asset | ≤ 2 GiB/file, không giới hạn tổng | 85 file × ~10 MB |
| API GitHub (không token) | 60 request/giờ/IP | 1 request/release (cache RAM) |

Nếu sau này cần nhanh hơn / nhiều người dùng hơn: chuyển media sang
Hugging Face Dataset hoặc Cloudflare R2 — chỉ cần sửa `web/data-config.js`
(`releases` → URL khác) và `tools/publish_online.py`, không phải sửa app.

## 5. Quy trình cập nhật (1 lệnh)

```powershell
cd GravityCode\VocabularyApp
python -X utf8 tools\publish_online.py --pack --all     # tách ngày + nén media
python -X utf8 tools\publish_online.py --upload --all   # đẩy media lên Releases
python -X utf8 tools\publish_online.py --pages          # copy vào web/data
python -X utf8 tools\deploy_pages.py                    # push nhánh gh-pages + bật Pages
python -X utf8 tools\verify_online.py                   # kiểm tra thật (8 tầng)
```

- `--pack --lang <slug>` / `--upload --lang <slug>`: chỉ 1 khóa.
- `--no-zip`: chỉ tách ngày (thử nhanh).
- Upload **idempotent**: asset đã có thì bỏ qua; gói 0 byte bị bỏ qua.
- Khi media được bù thêm, đổi `--tag data-<slug>-v2` (GitHub không cho trùng tên
  asset trong cùng release) rồi sửa `web/data-config.js`.

## 6. Sự cố đã gặp & cách xử lý

| Triệu chứng | Nguyên nhân | Xử lý |
|---|---|---|
| `POST /releases/{id}/assets` → **404** | endpoint `api.github.com` không nhận upload cho repo này | dùng **`uploads.github.com`** |
| `GET /releases/tags/<tag>` trả bản **rỗng** | GitHub cho phép nhiều draft trùng tag | liệt kê `/releases`, chọn bản nhiều asset nhất, xoá bản rỗng |
| `UnicodeEncodeError` khi tạo release | tag chứa tiếng Việt | tag **ASCII**: `tiếng_nhật` → `data-tieng-nhat-v1` |
| Fetch zip bị **CORS** | `github.com/.../releases/download` không có CORS | tải qua `api.github.com` + `Accept: application/octet-stream` |
| Trang trắng / "Chưa có khóa học AI" | `ensureCourseLoaded` chạy khi `currentLanguage` rỗng | guard + nạp lại khi đổi ngôn ngữ |
| Sửa JS mà điện thoại vẫn chạy bản cũ | service worker cache-first | SW dùng **network-first** cho html/js/css |

## 7. Bảo mật & token GitHub

- `web/data/` là **sản phẩm build** (gitignore ở `master`), chỉ tồn tại trên
  nhánh `gh-pages`; nội dung học không chứa key/token.
- `data/` (media gốc, log, settings) **không commit**.
- Token GitHub **không** nằm trong repo. Thứ tự đọc của `tools/gh_token.py`:
  1. `$env:GITHUB_TOKEN`
  2. `%LOCALAPPDATA%\VocabularyApp\github_token.txt`
  3. `settings.json` (nếu có)
  4. `git credential fill` **chế độ không tương tác** (15 giây, không bật hộp thoại)
- Lưu token 1 lần (không hỏi lại):
  ```powershell
  powershell -ExecutionPolicy Bypass -File tools\save_gh_token.ps1
  # hoặc nếu chưa có credential:
  powershell -ExecutionPolicy Bypass -File tools\save_gh_token.ps1 -Token "ghp_..."
  ```
  > Sự cố 17/11/2026: mỗi lần upload gọi `git credential fill` ⇒ Git Credential
  > Manager bật hộp thoại đăng nhập GitHub liên tục. Nay tool chỉ đọc token đã
  > lưu, tuyệt đối không bật hộp thoại.
- Repo `ThaiBao1991/VocabularyData` chứa media (public) — **không** chứa token.
- **Push git (18/11/2026):** không còn nhúng token vào URL. `deploy_pages.py`
  và `upload_media_repo.py` xác thực bằng header
  `http.https://github.com/.extraheader` (biến môi trường), đăng nhập đúng
  tài khoản **ThaiBao1991**; commit lấy `user.name/user.email` từ git config
  (`Thai Bao <thaibao1991dn@gmail.com>`). Token không nằm trong URL,
  `.git/config` hay argv.
- Push `master` (tránh GCM bật hộp thoại): `python -X utf8 tools\push_master.py`.
- Repo `ThaiBao1991/Project1` đang **public** và còn lộ 197 key trong
  `GravityCode/Download/AskCpl/settings.json` ⇒ nên chuyển private hoặc thu hồi
  key (việc này chưa làm).

## 8. Trạng thái nội dung & media (đo lúc 00:05 19/11/2026)

**Nội dung chữ: ĐỦ 100% ở cả 8 khóa** — 2.520 ngày/khóa, 25.200–25.389 từ,
0 ngày thiếu từ / thiếu hội thoại / thiếu quiz (audit `course.json`).

**Media (ảnh + audio) — job nhẹ đang bù tuần tự tới hết 2.520 ngày:**

| Khóa | Ngày có media | Ghi chú |
|---|---:|---|
| Tiếng Nhật | **2.520 / 2.520** | 85 gói, commit `5a801263`, `verify_online.py` 9/9 PASS |
| Tiếng Trung | 1.194 / 2.520 | đang chạy (ưu tiên 2), còn 1.326 ngày |
| Tiếng Anh | 1.214 / 2.520 | chờ, còn 1.306 ngày |
| Tiếng Hàn | 1.156 / 2.520 | chờ, còn 1.364 ngày |
| Tiếng Tây Ban Nha | 926 / 2.520 | chờ, còn 1.594 ngày |
| Tiếng Đức | 600 / 2.520 | chờ, còn 1.920 ngày |
| Tiếng Pháp | 600 / 2.520 | chờ, còn 1.920 ngày |
| Tiếng Nga | 600 / 2.520 | chờ, còn 1.920 ngày |

- **Ảnh hiện là placeholder** 512×512 (thẻ chữ cái đầu, ~604 B/ảnh): tầng
  `dict` (Wikimedia) bị HTTP 429 hàng loạt, còn Gemini image free tier
  `limit: 0`. **Audio TTS là thật** (từ / nghĩa / hội thoại). Muốn ảnh minh hoạ
  thật phải bật Gemini có billing hoặc tầng Web AI qua Chrome addon.
- Khóa nào đủ 2.520 ngày thì `tools/finalize_lite.py` tự động:
  `publish_online.py --pack` → `upload_media_api.py` → `publish_online.py --pages`
  → `deploy_pages.py` → xoá `publish/<khóa>`. Không cần canh tay.
- Trong lúc media chưa đủ, **nội dung chữ vẫn học bình thường**; ngày chưa có
  media chỉ không hiện ảnh/audio (không lỗi).

## 9. Chế độ nhẹ & tự động hoá (18/11/2026)

- `tools/fill_lite.py`: **1 khóa × 1 luồng**, RAM trần 700 MB (vượt → kill và
  chạy lại, checkpoint theo ngày nên không mất tiến độ), ưu tiên Below Normal,
  dừng khi đĩa < 6 GB. Đo thật khóa Nhật (31 ngày thiếu): **32 phút, RAM đỉnh
  443 MB, 0 lần kill** — máy vẫn mượt.
- `tools/finalize_lite.py --watch`: canh `data/logs/fill_lite.log`; khóa nào
  đủ 2.520 ngày thì tự chạy 4 bước nặng rồi xoá gói tạm. Trạng thái ở
  `data/logs/finalize_done.json` (không làm lại).
- `tools/upload_media_api.py`: đẩy media bằng GitHub **Git Data API**, không
  clone. Lần chạy thật đầu tiên (Nhật): 43 gói mới/đổi · 782 MB · 276 giây,
  commit `5a801263`.

## 10. Sự cố 19/11/2026 — kẹt "Đang tải Ngày …"

**Triệu chứng:** chọn ngày 2509 (Nhật) → màn hình đứng ở
`⏳ Đang tải Ngày 2509…` mãi, không render nội dung.

**Nguyên nhân:** `web/script.js` gọi `(g.common_mistakes || []).map(...)`,
nhưng `grammar[].common_mistakes` trong dữ liệu là **chuỗi** ở **69.964 mục**
trên cả 8 khóa. Gọi `.map()` trên chuỗi ⇒
`TypeError: (g.common_mistakes || []).map is not a function` ⇒ hàm render dừng
trước khi ghi HTML, nên dòng "Đang tải…" còn nguyên. **Không phải** lỗi mạng,
ZIP hay GitHub rate limit (`m84.zip` vẫn hợp lệ: 8.914.512 B / 930 entry, có
`d2509`).

**Đã sửa:**
- Chuẩn hoá `common_mistakes` về mảng (chuỗi → `[chuỗi]`); render chuỗi bằng
  `⚠️`, object bằng `❌/✅` như cũ.
- Bọc `renderCourseDay` bằng `try/catch` → lỗi dữ liệu hiện
  "⚠ Không hiển thị được Ngày …" thay vì treo vô hạn.
- Guard `(q.options || [])` cho quiz; `examples` chỉ map khi là mảng.
- `sw.js`: `VERSION` `vocab-v3` → `vocab-v4`.

**Kiểm chứng thật (local + Pages):** Nhật 2509/2519/2520/1, Anh 2509,
Trung 1861, Hàn 1156 → render **0,3–2,5 giây**, 0 lỗi console;
`verify_online.py` **9/9 PASS**.

