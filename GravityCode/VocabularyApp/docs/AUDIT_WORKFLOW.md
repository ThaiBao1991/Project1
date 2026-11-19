# Quy trình kiểm toàn bộ & tối ưu dung lượng

Cập nhật: 19/11/2026

## 1. Lệnh kiểm tổng

```powershell
cd "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp"
python -X utf8 tools\audit_all.py
```

Kết quả:
- `docs/AUDIT_REPORT.md` — báo cáo đọc được.
- `data/logs/audit.json` — dữ liệu thô.
- Màn hình in `FAIL=… WARN=…`.

Kiểm nhanh (bỏ online/test, vẫn kiểm nội dung + dung lượng):

```powershell
python -X utf8 tools\audit_all.py --no-online --no-tests
```

## 2. Tiêu chí PASS

| Mục | Đạt khi |
|---|---|
| Nội dung | 8 khóa × 2.520 ngày; tối thiểu 4 mẫu câu, 5 câu thông dụng, 2 ngữ pháp, 1 hội thoại, 3 quiz ngữ pháp + 3 quiz thông dụng |
| Hệ chữ | 0 câu sai hệ chữ / 0 template `を 使います`, `は 何ですか` |
| Tiếng Anh | 0 chữ Hàn/Trung; IPA ≥ 97%; 0 từ tục; ngày 1 từ đơn giản |
| Tiếng Nhật | Ngày 1 đủ 46 Hiragana; ngày 2 đủ 46 Katakana |
| Media | `media_map` khớp manifest/overlay (sai lệch ≤ 10 ref mới đang fill) |
| Online | `verify_online.py` 9/9; `sw.js` đúng version |
| Test | `test_web_contract.py` PASS; `test_content_quality.py` PASS |
| Git | Không có file VocabularyApp chưa commit |

WARN chấp nhận được:
- Khóa còn thiếu media (đang fill).
- Audio còn > 32 kbps (đang nén).
- File tạm/rác > 0 (dọn trước khi pack).

## 3. Quy trình trước/sau deploy

1. `python -X utf8 tools\test_web_contract.py`
2. `python -X utf8 tools\test_content_quality.py`
3. `python -X utf8 tools\audit_all.py --no-tests` (audit đầy đủ)
4. Nếu FAIL nội dung: `python -X utf8 tools\enrich_course_content.py --lang <khóa>` → export → test lại.
5. Nếu FAIL media_map: `python -X utf8 tools\reconcile_manifest.py` → audit lại.
6. Deploy: `python -X utf8 tools\deploy_pages.py`.
7. Sau deploy: `python -X utf8 tools\verify_online.py` và audit lại.

## 4. Quy trình sau mỗi khóa đủ 2.520 ngày

`finalize_lite.py` tự:
1. `shrink_audio.py` — nén MP3 32 kbps mono (giữ nguyên tên/ref).
2. `publish_online.py --pack` — tạo 85 gói.
3. `upload_media_api.py` — upload `VocabularyData`.
4. `publish_online.py --pages` — cập nhật `web/data`.
5. `deploy_pages.py` — deploy Pages, tự dọn temp.
6. `cleanup_done_media.py` — xoá media local khóa đã upload.

## 5. Tối ưu dung lượng

### Đã làm
- **Chuyển dữ liệu lớn sang F:**: `data/media`, `data/audio`,
  `data/ai_courses` → `F:\VocabularyAppData`, tạo junction tại chỗ cũ.
  App/tool vẫn dùng đường dẫn cũ; C: được giải phóng ~3 GB, media tương lai
  không còn làm đầy C:.
- **MP3 48/64 → 32 kbps mono**: giảm ~31–50%; giữ nguyên filename/ref.
- **Dọn temp**: `deploy_pages.py` xoá `vocab_pages_*` cũ/read-only; đã giải phóng 2,05 GB.
- **Xoá temp manifest**: `data/media/index.json.tmp.*` (~395 MB).
- **Cleanup media local** sau finalize.
- **Overlay manifest**: `data/media/webmap_overlay.json` bù 76.767 ref web bị thiếu/sai ngày.
- **Gzip course.json** của Trung/Nhật (đã upload xong) để tiết kiệm ~140 MB.

### Có thể làm tiếp
| Cách | Tiết kiệm | Ghi chú |
|---|---:|---|
| Opus 24 kbps thay MP3 32 kbps | thêm ~25–35% audio | Safari cũ có thể không phát; cần test iPhone |
| Nén lại media Trung/Nhật đã upload | ~0,4–0,6 GB remote | phải tải gói cũ, giải nén, nén, upload lại |
| Gzip `data/media/index.json` | ~140 MB local | chỉ local; cần sửa tool đọc `.gz` |
| Bỏ field rỗng/trùng trong web JSON | ~20–35 MB | rủi ro thấp nhưng lợi ích nhỏ |
| Squash history `gh-pages` | có thể vài GB | force-push; cần xác nhận |
| Tách web data sang repo riêng/R2 | giảm Project1 | khi Project1 gần 5 GB |
| `git gc --prune=now` | tùy lịch sử | an toàn, không đổi nội dung |

### Ngưỡng cảnh báo
- `VocabularyData` > **4,5 GB** ⇒ chuẩn bị R2/tách repo.
- `Project1` > **5 GB** ⇒ xem xét squash `gh-pages` hoặc tách web data.
- Đĩa trống < **4 GB** ⇒ dừng fill, dọn temp/audio cache.

## 6. Kiểm tra định kỳ

- Sau mỗi khóa: audit nhanh + `verify_online`.
- Mỗi ngày: xem `data/logs/fill_lite.log`, `finalize_stdout.log`, `cleanup_done_media.log`.
- Mỗi tuần: `audit_all.py` đầy đủ + kiểm repo size API.
