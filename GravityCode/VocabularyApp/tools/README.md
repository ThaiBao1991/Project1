# tools/ — Script chẩn đoán & kiểm chứng

Các script dùng để **đo** hiện trạng thật và **chống hồi quy**. Không script nào
ghi vào khóa học nếu không có `--dry-run` (trừ khi ghi rõ trong mô tả).

## Kiểm chứng (chạy trước khi báo cáo "xong")

| Script | Việc | Kỳ vọng |
|---|---|---|
| `verify_p0_fixes.py` | Tái hiện 14 lỗi P0 đã sửa | **14/14 PASS** |
| `verify_no_rewrite.py` | Chứng minh `get_course()` KHÔNG ghi lại 8 file `course.json` (135 MB) | `RESULT: PASS` |
| `../test_ai_rich.py` | 79 unit test (thêm `--slow` cho section [11]) | `Results: 79 passed, 0 failed` |
| `../verify_all_native_courses.py` | 27 check 7 vòng | `27 PASSED, 0 FAILED` |

## Chẩn đoán hiện trạng

| Script | Việc |
|---|---|
| `diag_gemini_keys.py` | Phân loại 90 key Gemini: OK / chết (service account deleted) / 403 denied |
| `diag_list_models.py` | Liệt kê model Gemini còn sống + `supportedGenerationMethods` |
| `diag_image_gemini.py` | Thử sinh ảnh bằng Gemini native image, in lỗi thật (metric/limit) |
| `diag_image_gemini2.py` | Thử model ảnh chưa test + **Gemini TTS** nhiều voice |
| `diag_image_models.py` | Liệt kê & thử từng model ảnh, báo `limit: 0` nếu bị chặn |
| `diag_free_image.py` | Thử nguồn ảnh miễn phí (Openverse / Wikipedia / Wiktionary) + voice Gemini TTS |
| `diag_evidence.py` | 7 nhóm kiểm tra cho module dẫn chứng (fetch/verify/cache/AI/attach) |
| `diag_srs.py` | Mô phỏng 20 từ học 30 ngày + 15 phép kiểm tra edge-case SM-2 |

## Bảo trì dữ liệu

| Script | Việc | Cảnh báo |
|---|---|---|
| `link_media_refs.py` | Gắn lại `image_ref`/`audio_ref` cho các ngày đã render (khớp theo tên file) | `--dry-run` để xem trước |
| `replace_placeholders.py` | Đánh dấu ngày có ảnh placeholder để pipeline sinh lại ảnh thật | `--dry-run` để xem trước |

## Sinh tự động

| Lệnh | Sinh file |
|---|---|
| `python -m ai.paths --export-js` | `web/paths.js` (bảng slug từ `ai/paths.py`) |
