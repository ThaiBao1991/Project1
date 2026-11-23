# Làm việc từ xa & các lựa chọn miễn phí (19/11/2026)

Tài liệu này trả lời câu hỏi: *với khối lượng file lớn như hiện nay, làm sao
vận hành VocabularyApp từ xa, và có dịch vụ miễn phí nào tiện hơn GitHub không?*

Số liệu đều đo thật trên máy ngày 19/11/2026, không phải ước lượng.

---

## 1. Cái gì thực sự lớn?

| Thành phần | Dung lượng thật | Có phải "mang theo" khi làm từ xa? |
|---|---:|---|
| Code + lịch sử repo `Project1` | 5,36 GB (GitHub báo) | **Không** — clone nông `--depth 1` chỉ ~200 MB |
| `web/` (bản Pages) | 340,0 MB / **20.189 file** | Không — deploy tự động |
| Media zips trên `VocabularyData` | 2,40 GB / 234 gói | Không — mỗi gói chỉ 8–9 MB, upload qua API |
| `course.json` 8 khóa | 445 MB | **Có** — nguồn nội dung |
| `data/media/index.json` | 149 MB | **Có** — manifest `ref → file` |
| Checkpoint pipeline | ~840 MB | **Có** — biết ngày nào đã xong |
| `data/media` gốc + `data/audio` cache | 6,4 GB | Không — dựng lại được từ zip + TTS |

⇒ Phần **state** cần backup chỉ ~1,4 GB; nén còn khoảng **500–600 MB**.

Điểm quan trọng: job không "đẩy 7 GB mỗi lần". Nó chỉ upload **gói zip mới**
(~8 MB) qua Git Data API, không clone repo media. Nút thắt thật sự là
**máy chạy pipeline**, không phải dung lượng mạng.

---

## 2. Bảng dịch vụ miễn phí (kiểm tra 19/11/2026)

| Dịch vụ | Hạn mức miễn phí | Cần thẻ? | Phù hợp |
|---|---|---|---|
| **GitHub Pages** | 1 GB site, ~100 GB băng thông/tháng (mềm) | Không | App (đang dùng, 340 MB) |
| **GitHub repo** | khuyến nghị < 5 GB, 100 MB/file, 2 GB/push | Không | Code + media zips (đang dùng) |
| **GitHub Releases** | 2 GB/asset | Không | Backup lạnh — **không CORS** nên không phục vụ trực tiếp |
| **Cloudflare R2** | 10 GB-month, 1M Class A, 10M Class B, **egress 0đ** | Có | Media (7 GB vừa đủ) |
| **Cloudflare Pages** | static không giới hạn request, **20.000 file/site**, 25 MiB/file, 500 build/tháng | Không | App — nhưng `web/` đã **20.189 file**, vượt nhẹ |
| **Hugging Face** | public best-effort, **private 100 GB**, CDN, CORS OK (đã test) | Không | Backup state; có thể chứa media |
| **Oracle Cloud Always Free** | 2 OCPU/12 GB ARM, 200 GB đĩa, 10 TB egress/tháng | Có | Chạy pipeline 24/7 |
| **Backblaze B2** | 10 GB, 1 GB/ngày tải free, egress free qua Cloudflare | Có | Ít lợi thế hơn R2 |
| **Netlify / Vercel** | ~100 GB băng thông | Không | Không hợp media 7 GB |
| **Internet Archive** | Miễn phí, chậm, không SLA | Không | Backup lạnh |
| **Git LFS** | 1 GB storage + 1 GB/tháng băng thông | Không | **Không đủ** |

Kiểm tra CORS thật ngày 19/11:

```
HF resolve   HTTP 200  ACAO=https://example.com   (phản chiếu Origin)
GitHub raw   HTTP 200  ACAO=*
GitHub Pages HTTP 200  ACAO=*
```

---

## 3. Ba kiến trúc

### A. 0 đồng, không cần thẻ (nên bắt đầu)

- **App:** giữ GitHub Pages như hiện tại.
- **Media:** giữ `VocabularyData`; khi vượt 5 GB thì tách **2 repo × 4 khóa**
  (~3,5 GB/repo) hoặc **8 repo × 1 khóa** (~900 MB/repo).
  `tools/upload_media_api.py` đã có `--repo`, chỉ cần vòng lặp theo khóa và
  thêm `base` cho từng khóa trong `media/index.json`.
- **Backup state:** Hugging Face **private dataset** (100 GB free, không cần
  thẻ). Nén `course.json` + `media/index.json` + checkpoint ≈ 500–600 MB.
- **Compute:** PC hiện tại + `fill_lite`/`finalize_lite`. Muốn điều khiển từ xa
  thì dùng **Tailscale + RDP/SSH** hoặc Chrome Remote Desktop.
- **Ưu:** không thẻ, không đổi app, không rủi ro.
- **Nhược:** PC phải bật.

### B. Tiện nhất nếu có thẻ: Cloudflare R2

- Media → bucket R2; `mediaRawBase` trỏ thẳng R2; egress **0 đồng**.
- 10 GB free đủ cho ~7 GB media khi đủ 8 khóa.
- CORS: policy cho phép `GET/HEAD` từ `https://thaibao1991.github.io`.
- Truy cập public:
  - **Custom domain** (tốt nhất, cần tên miền),
  - **Worker + `*.workers.dev`** (free 100.000 request/ngày, không cần tên miền),
  - `r2.dev` chỉ nên dùng để test (bị rate-limit).
- **Không chuyển app sang Cloudflare Pages**: `web/` đang 20.189 file, vượt
  hạn mức 20.000 file/site của gói free.
- Phải sửa: `web/data-config.js` (`mediaRawBase`) + `tools/upload_media_api.py`
  (thêm backend R2, hoặc dùng `boto3`/`aws s3` CLI).
- **Ưu:** một URL, không lo 5 GB, tải nhanh, không tốn băng thông.
- **Nhược:** cần thẻ; phải tạo bucket + API token; cần test CORS thật.

### C. PC tắt vẫn chạy: Oracle Cloud Always Free

- VM ARM 2 OCPU / 12 GB RAM, 200 GB đĩa, 10 TB egress/tháng.
- Cần port khi chạy Linux:
  - `psutil.BELOW_NORMAL_PRIORITY_CLASS` chỉ có trên Windows → bọc
    `if os.name == "nt"` trước khi dùng.
  - Cài Python 3.14 + `ffmpeg` + `edge-tts`; chạy dưới `systemd` hoặc `tmux`.
- **Cảnh báo:** Oracle thu hồi instance idle sau 7 ngày (CPU/network/RAM thấp);
  capacity A1 hay hết; bắt buộc thẻ.
- **Ưu:** 24/7 thật, không phụ thuộc PC.
- **Nhược:** dựng mất 1–2 ngày; khác hệ điều hành.

---

## 4. Vì sao không chọn mấy chỗ khác

| Dịch vụ | Lý do loại |
|---|---|
| Google Drive / Dropbox | Link tải có quota, **không CORS** → app không tải media được |
| Telegram | Không phải static hosting, không CORS |
| Kaggle | Tải dataset cần đăng nhập |
| GitLab / Codeberg | Hạn mức thấp hơn, không có lợi thế so với GitHub |
| GitHub Actions | Free cho repo public nhưng 6 giờ/job, phải upload/download state, workflow dễ bị tắt sau 60 ngày idle |
| Codespaces / Cloud Shell | Tự stop khi idle, đĩa nhỏ, không chạy nhiều ngày |

---

## 5. Đề xuất thứ tự

1. **Hôm nay:** giữ nguyên job; backup state lên **Hugging Face private**
   (không cần thẻ). Script `tools/backup_state.py` sẽ viết khi có token HF.
2. **Khi media > 5 GB hoặc gặp `HTTP 403` từ raw:** tách repo 2× hoặc chuyển R2.
3. **Khi cần PC tắt:** dựng Oracle Cloud.
4. **Luôn:** rotate 197 key trong `GravityCode/Download/AskCpl/settings.json`;
   không đưa token vào repo, URL hay log.

---

## 6. Checklist kiểm chứng sau khi đổi nguồn

- [ ] `python -X utf8 tools/verify_online.py` → **9/9 PASS**
- [ ] `curl -I <url-zip-mới>` → `200` + `access-control-allow-origin`
- [ ] Điện thoại mở một ngày có media mới → ảnh + audio hiển thị
- [ ] `git ls-remote` repo mới → đúng commit
- [ ] `git remote -v`, `.git/config`, log **không** chứa token
- [ ] `data/index.json` vẫn đủ 8 khóa sau khi merge
