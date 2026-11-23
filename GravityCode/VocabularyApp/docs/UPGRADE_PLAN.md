# Phương án kiểm tra & nâng cấp Vocabulary App

Cập nhật: 19/11/2026

## 1. Baseline hiện tại

| Hạng mục | Số đo |
|---|---:|
| Nội dung | 8 khóa × 2.520 ngày |
| Audit nội dung | **0 FAIL** |
| Mẫu câu / câu thông dụng / ngữ pháp / hội thoại | tối thiểu 4 / 5 / 2 / 1 mỗi ngày |
| Quiz | 3 ngữ pháp + 3 câu thông dụng + 8 từ vựng + 2 mẫu câu |
| Template cũ / câu sai hệ chữ | **0 / 0** |
| Tiếng Anh | IPA **97,6%**, 0 chữ Hàn/Trung, 0 từ tục |
| Tiếng Nhật | 46 Hiragana + 46 Katakana |
| Lighthouse | **Accessibility 100 · Best Practices 100 · SEO 100** |
| Đổi ngôn ngữ trong khóa học | **68 ms local**, ~130 ms Pages |
| Render lõi 1 ngày | **6 ms** |
| Render phần còn lại | ~268 ms (idle) |
| Bấm ←/→ sau prefetch | ~20 ms |
| `web/data` | 0,58 GB |
| `data/media` | 2,07 GB (MP3 1,80 GB) |
| `data/ai_courses` | 1,06 GB |
| Repo `VocabularyData` | 2,82 GB |
| Repo `Project1` | 5,48 GB ⚠️ gần ngưỡng 5 GB |
| Media | Nhật/Trung 2.520 ✅; Anh 1.270, Hàn 1.156, Tây 926, Nga/Pháp/Đức 600 |

## 2. Khung quyết định

Mỗi tính năng chấm:

- **Giá trị học tập** 1–5.
- **Công sức** S (≤1 ngày), M (2–4 ngày), L (>1 tuần).
- **Rủi ro** thấp/trung/cao.
- **Chi phí dữ liệu** (thêm bao nhiêu KB/ngày hoặc GB media).

Chỉ làm khi:
- Giá trị ≥ 4, công sức ≤ M, rủi ro thấp/trung; hoặc
- Giá trị 5, công sức L nhưng có thể làm từng phần.

## 3. Bảng ưu tiên

| Tính năng | Giá trị | Công sức | Rủi ro | Quyết định |
|---|---:|---|---|---|
| **Settings**: cỡ chữ, theme sáng/tối, tốc độ audio, giọng đọc, giảm chuyển động | 5 | S | Thấp | **Làm ngay** |
| **Progress dashboard**: streak, lịch tháng, ngày đã học, điểm quiz | 5 | M | Thấp | **Làm ngay** |
| **Chọn ngày nâng cao**: modal tìm theo tiêu đề, ngày đã học, gần đây | 4 | M | Thấp | **Làm ngay** |
| **Lịch sử quiz + câu sai** | 4 | S | Thấp | **Làm ngay** |
| **Cache từ vựng bằng IndexedDB** | 4 | M | Thấp | Nên làm |
| **Tải offline tháng hiện tại** (nút tải + tiến độ) | 5 | M | Trung | Nên làm |
| **Quiz nghe / điền từ / gõ đáp án** | 5 | L | Trung | Nên làm từng phần |
| **Đưa câu quiz sai vào SRS** | 5 | M | Thấp | Nên làm |
| **Ghi chú / bookmark từng từ, từng ngày** | 4 | M | Thấp | Nên làm |
| **Export/Import tiến độ JSON** | 4 | S | Thấp | Nên làm |
| **Luyện phát âm**: ghi âm, nghe lại, so sánh | 4 | M | Trung | Cân nhắc |
| **Grammar/Pattern Index** toàn khóa | 4 | M | Thấp | Nên làm |
| **Bảng chữ cái Hàn / Nga** | 4 | S | Thấp | Nên làm |
| **IPA/phiên âm cho khóa khác** | 4 | M | Trung | Cân nhắc |
| **Nén audio Opus 24k** | 3 | M | Trung (Safari) | Cân nhắc |
| **Nén lại media Trung/Nhật đã upload** | 3 | L | Trung | Cân nhắc |
| **Gzip manifest / bỏ field JSON rỗng** | 2 | S | Thấp | Chỉ khi cần |
| **Squash history `gh-pages`** | 3 | M | Cao | Chỉ khi repo > 5 GB |
| **Tách web data / R2** | 4 | L | Trung | Khi repo > 4,5–5 GB |
| **Cloud sync 2 chiều** | 2 | L | Cao | **Không làm** |
| **AI chat/gia sư trên điện thoại** | 3 | L | Cao (quota) | **Không làm** |
| **Video bài giảng** | 2 | L | Cao (dung lượng) | **Không làm** |
| **Social/leaderboard** | 1 | L | Cao (server) | **Không làm** |
| **Rewrite React/Vue** | 1 | L | Cao | **Không làm** |

## 4. Nhóm P0 — làm trong 1–2 tuần

### 4.1. Settings
- Cỡ chữ: 90 / 100 / 110 / 120%.
- Theme: tối (mặc định), sáng, theo hệ thống.
- Tốc độ audio: 0,75× / 1× / 1,25×.
- Giọng đọc: chọn voice của `speechSynthesis` theo ngôn ngữ.
- Giảm chuyển động.
- Lưu `localStorage` key `vocabapp_settings_v1`.
- Test: reload giữ setting; Lighthouse vẫn 100; audio đổi tốc độ đúng.

### 4.2. Progress dashboard
Dữ liệu đã có:
- `vocabapp_ai_progress_<khóa>`: `completed_days`, `quiz_scores`, `last_day`.
- `vocab_srs_v1_<khóa>`.
Hiển thị:
- Streak ngày học.
- Lịch 30 ngày gần nhất (màu theo số ngày hoàn thành).
- Tổng ngày đã học / 2.520.
- Điểm quiz trung bình, cao nhất.
- Nút “Học tiếp ngày X”.
- Test: inject dữ liệu giả, kiểm tra số liệu; reload giữ nguyên.

### 4.3. Chọn ngày nâng cao
- Modal “Chọn ngày”:
  - Ô tìm theo tiêu đề ngày.
  - Tab: Tất cả / Đã học / Chưa học / Gần đây.
  - 20 ngày gần nhất.
- Dùng `index.json` (2.520 tiêu đề, ~100 KB) tải lazy khi mở modal.
- Vẫn giữ ô nhập nhanh hiện tại.
- Test: tìm “2509”, “kinh doanh”, chọn đúng; đóng/mở không tải lại.

### 4.4. Lịch sử quiz + câu sai
- Lưu `quiz_history` theo ngày: điểm, thời gian, danh sách câu sai.
- Trang “Kết quả học tập” trong progress dashboard.
- Nút “Luyện lại câu sai”.
- Test: làm quiz sai 3 câu → lịch sử ghi 3; luyện lại đúng.

### 4.5. Tối ưu list view
- Cache `vocabularies` đã parse vào **IndexedDB** theo `(slug, version)`.
- Lần đầu vẫn tải 5–7 MB; lần sau đọc IDB < 300 ms.
- Có thể chia file từ vựng thành 4–6 chunk nếu cần first paint < 1 s.
- Mục tiêu: list first render < 1,5 s (4G), lần sau < 300 ms.
- Test: xoá IDB → đo; reload → đo; đổi ngôn ngữ qua lại.

### 4.6. Tải offline tháng hiện tại
- Nút “Tải offline tháng này” trong course header.
- Tải gói `mXX.zip` của tháng hiện tại, giải nén/cache vào CacheStorage.
- Hiện tiến độ, dung lượng; cho xoá.
- Kiểm tra offline thật: DevTools Offline → mở ngày trong tháng đã tải.
- Test: tải tháng 84, tắt mạng, mở ngày 2509.

## 5. Nhóm P1 — 2–4 tuần

### 5.1. Quiz đa dạng
- Nghe audio → chọn nghĩa.
- Điền từ vào chỗ trống.
- Gõ đáp án (so khớp chuẩn hoá).
- Giữ quiz trắc nghiệm cũ.
- Cần kiểm tra dữ liệu: audio/meaning có sẵn; không cần AI.

### 5.2. Câu sai → SRS
- Khi nộp quiz, đưa từ/câu sai vào queue SRS của ngày.
- Ôn tập ưu tiên câu sai.
- Tránh trùng với SRS từ vựng hiện có.

### 5.3. Ghi chú / bookmark
- Lưu theo `slug + day + word`.
- Hiện icon bookmark cạnh từng từ, ghi chú ngắn.
- Trang “Đã lưu” trong dashboard.

### 5.4. Export/Import tiến độ
- Xuất JSON: progress, SRS, settings, bookmarks.
- Nhập: kiểm tra version, merge/overwrite có xác nhận.
- Dùng để chuyển máy, không phải cloud sync.

### 5.5. Grammar/Pattern Index
- Tổng hợp `grammar` + `sentence_patterns` 8 khóa.
- Tìm theo mẫu/cấu trúc, lọc theo cấp N5→N1.
- Link tới ngày chứa mẫu.

### 5.6. Bảng chữ cái Hàn/Nga
- Hangul 40 âm cơ bản + batchim.
- Cyrillic 33 chữ + phiên âm.
- Dùng lại component `alphabet` của Nhật.

## 6. Nhóm P2 — chỉ khi cần

- **Opus 24k**: giảm thêm 25–35% audio; test Safari/iPhone trước.
- **Nén lại media Trung/Nhật đã upload**: tải gói cũ → nén → upload; giảm ~0,4–0,6 GB remote.
- **Gzip manifest**: giảm ~140 MB local; không giảm repo GitHub.
- **Squash `gh-pages`**: giảm mạnh repo `Project1`; force-push, cần backup + xác nhận.
- **R2/tách repo web data**: khi `Project1` > 5 GB hoặc `VocabularyData` > 4,5 GB.

## 7. Kế hoạch kiểm thử

### 7.1. Tự động
```powershell
python -X utf8 tools\test_web_contract.py
python -X utf8 tools\test_content_quality.py
python -X utf8 tools\audit_all.py
python -X utf8 tools\verify_online.py
```

### 7.2. Performance budget
| Chỉ số | Mục tiêu |
|---|---:|
| Đổi ngôn ngữ trong course | ≤ 300 ms |
| Render lõi 1 ngày | ≤ 100 ms |
| Render đầy đủ 1 ngày | ≤ 800 ms |
| List first render (4G) | ≤ 1,5 s |
| List lần sau (IDB) | ≤ 300 ms |
| TTI trang đầu (4G) | ≤ 2,5 s |
| JS heap | ≤ 120 MB |
| 1 file ngày | ≤ 80 KB |
| `web/data` | ≤ 800 MB |
| LCP mobile | ≤ 2,5 s |

### 7.3. Thiết bị
- iPhone Safari 16/17.
- Android Chrome máy yếu (RAM 3–4 GB).
- Desktop Chrome/Edge.
- Chế độ offline.
- Màn hình 360×640, 390×844, 768, 1280.

### 7.4. Accessibility
- Lighthouse ≥ 98 (hiện 100).
- Keyboard-only: tab, enter, escape modal.
- Screen reader: select ngôn ngữ, ngày, quiz.
- Contrast, focus ring, `prefers-reduced-motion`.

### 7.5. Regression checklist
- Đổi ngôn ngữ Anh ↔ Trung ↔ Nhật.
- Nhập ngày, ←/→, reload nhớ ngày.
- Quiz, audio, ảnh, SRS, luyện viết.
- Offline mở ngày đã cache.
- Không lỗi console.
- `sw.js` version mới.

### 7.6. Rollback
- Lỗi UI: revert commit + deploy lại.
- Lỗi cache: tăng `sw.js` version.
- Lỗi dữ liệu: dùng `course.json` gốc/overlay; không xoá media đã upload.

## 8. Thứ tự triển khai đề xuất

1. **Settings + Progress dashboard + Quiz history** (tuần 1).
2. **Chọn ngày nâng cao + IndexedDB list cache** (tuần 1–2).
3. **Tải offline tháng + Quiz nghe/điền từ** (tuần 2–3).
4. **Câu sai → SRS + bookmark/notes + Export/Import** (tuần 3–4).
5. **Grammar index + bảng chữ cái Hàn/Nga** (tuần 4).
6. Chỉ sau đó mới xét Opus/R2/squash history.

## 9. KPI thành công

- Giảm thời gian mở list lần 2 xuống < 300 ms.
- 100% ngày học có thể mở offline sau khi bấm tải tháng.
- Tăng số ngày hoàn thành/quiz làm lại (đo local, không gửi server).
- Giữ Lighthouse 100 và audit 0 FAIL.
- `web/data` < 800 MB; `VocabularyData` < 4,5 GB; `Project1` < 5 GB.

## 10. Kết luận

**Nên làm ngay:** Settings, Progress dashboard, chọn ngày nâng cao, lịch sử quiz, cache từ vựng, offline tháng.

**Nên làm tiếp:** quiz nghe/điền từ, câu sai → SRS, bookmark/notes, export/import, grammar index, bảng chữ cái Hàn/Nga.

**Không nên làm:** cloud sync 2 chiều, AI chat trên điện thoại, video, social, rewrite framework.

**Chỉ làm khi có nhu cầu rõ:** Opus 24k, nén lại media đã upload, squash history, R2.
