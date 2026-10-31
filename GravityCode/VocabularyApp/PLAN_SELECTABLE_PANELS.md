# PLAN — Panel chọn được (Từ vựng/Ngữ pháp) + Log xoay key AI + Đối chiếu GitHub

> 2026-10-31 · Branch `fix/ai-course-content-20261030`

## 0. Kết quả đối chiếu (đã kiểm tra thật)

| Tính năng | Branch (worktree) | master local | GitHub |
|---|---|---|---|
| 3 nút chế độ 📚📖🎧 + `_load_mode` thực | ✅ | ❌ | ❌ |
| Panel hội thoại (`_sync_dlg_panel`, nghe từng lượt) | ✅ | ❌ | ❌ |
| TTS song ngữ JP→VI (`tts_bilingual_mode`) | ✅ | ❌ | ❌ |
| Free-tier TTL 24h, pool.sync giữ cooldown | ✅ | ✅ | ✅ |
| Border crash fix, vocab-fill, quiz 142 câu | ✅ | ❌ | ❌ |
| Panel từ vựng list chọn được (mục A) | ❌ → làm | ❌ | ❌ |
| Panel ngữ pháp click → chi tiết (mục B) | ❌ → làm | ❌ | ❌ |
| Log "đang dùng key account nào" (mục C) | ❌ → làm | ❌ | ❌ |

→ **Kết luận: GitHub và bản Desktop đều CHƯA có đủ tính năng.** Branch có tất cả nhưng
chưa push. Sau khi xong mục A/B/C: merge branch → master (giải quyết 6 file conflict),
push GitHub, bản Desktop chỉ cần `git pull`.

## A. Panel từ vựng dạng danh sách chọn được (thay dải thẻ ngang)

**Yêu cầu:** 10 từ = 10 dòng chọn được — mỗi dòng: thumbnail + từ + **nghĩa tiếng Việt**;
click vào dòng → mở chi tiết (MediaViewerDialog sẵn có: ảnh 384×384, reading, ví dụ, ←/→,
phát âm). Dải thẻ ngang (`media_strip`) thấy không cần thiết → thay bằng panel dọc.

**Thiết kế (sửa `StudyTab` trong VocabApp.py):**
1. `cleft` (~dòng 3495): thay `CTkScrollableFrame(horizontal)` bằng
   `self.vocab_panel = CTkScrollableFrame(cleft, orientation="vertical")` —
   GIỮ tên biến `self.media_strip` → không phải sửa 4214/4220 và các caller
   `_play_seq`/`_stop_play_seq`/`_media_ring`/`_update_media_cover`.
2. `_render_media_strip(lesson)` → đổi tên thành `_render_vocab_panel(lesson)`
   (cập nhật 2 điểm gọi). Mỗi dòng 1 từ:
   - khung `CTkFrame` full-width (height ~56), `fg_color=C["card2"]`,
   - `[thumb 44×44] [word (jp_font bold) + reading nhỏ] [nghĩa_vi] [▶]`
   - thumbnail: tái dùng logic `_card_is_real_image` + word-card fallback (code sẵn, thu nhỏ 96→44).
   - click chuột trái → `_open_media_viewer(i)` (viewer sẵn có, đang mở bằng nút 📖).
   - `_play_vocab(it)` giữ nguyên cho nút ▶.
3. `_media_ring(idx)`: highlight dòng ĐANG PHÁT bằng `fg_color` (accent) thay vì
   `border_color="transparent"` (bug ValueError cũ). `_media_cards` = {idx: row_frame}.
4. Badge cover (`_update_media_cover`) + 🔊 Nghe cả ngày: GIỮ NGUYÊN, chạy trên list mới.

## B. Panel ngữ pháp dạng danh sách click → chi tiết

**Yêu cầu:** ngữ pháp cũng liệt kê ra các dòng, click vào là thấy chi tiết hóa.

**Thiết kế:**
1. Vùng nội dung panel chuyển theo chế độ:
   - mode 📚 → panel từ vựng (mục A); mode 📖 → panel ngữ pháp; mode 📑 → từ vựng (mặc định).
   - `_load_mode` gọi `_render_vocab_panel` hoặc `_render_grammar_panel` theo mode.
2. `_render_grammar_panel(lesson)`: liệt kê `sentence_patterns` + `grammar` của ngày:
   - mỗi dòng: `[STT] [cấu trúc JP] [nghĩa VI]`, click → `GrammarDetailDialog`.
3. `GrammarDetailDialog(ctk.CTkToplevel)` (lớp mới, cạnh `MediaViewerDialog`):
   - tiêu đề cấu trúc + reading, giải thích (`explanation`), danh sách ví dụ
     (JP + VI, nút 🔊 phát TTS từng ví dụ), `common_mistakes`, mini-quiz 1 câu nếu có.
   - phím ←/→ chuyển cấu trúc khác trong ngày, Esc đóng — đồng bộ UX với MediaViewerDialog.

## C. Log AI đang dùng key/account nào (dễ nhìn bằng mắt)

**Yêu cầu:** khi AI sinh nội dung, log hiện rõ **account + key nào** đang được dùng
để theo dõi việc xoay vòng, tránh 1 account bị dùng liên tục.

**Thiết kế (`api/gemini_safe.py`):**
1. `GeminiCoordinator.request()` (~dòng 990, sau khi `pool.pick` được key):
   ```python
   if email != self._last_email_used:
       self._last_email_used = email
       self._log(f"🔄 Chuyển sang account: {email} (key #{key_idx}/{total})")
   ```
   chỉ hiện khi ĐỔI account (không spam mỗi request); lần đầu tiên hiện
   `🔑 Dùng key của: {email}`.
2. `request_image()` (~dòng 1245): tương tự — log khi đổi account ở luồng ảnh.
3. Định dạng log (đọc được bằng mắt): `🔑 [3/9] user@gmail.com · model=gemini-2.5-flash`.
   `warn_account_health` (dòng 222) + các dòng fail hiện có `[acct]` GIỮ NGUYÊN.
4. Log đi vào `CourseGenerationDialog.log_box` sẵn có (log_fn đã nối sẵn
   pipeline → coordinator → dialog).

## D. Đồng bộ GitHub + bản Desktop

1. **Push branch** lên GitHub (`git push -u origin fix/ai-course-content-20261030`).
2. **Merge branch → master**, giải quyết 6 file conflict
   (VocabApp.py, course_generator.py, pipeline.py, gemini_safe.py, database.py,
   projectLog.md): master thêm `tts_selfbuilt.py`, `USAGE_GUIDE.md`, database
   ±12 dòng — **giữ cả 2 phía** (feature branch + file mới master).
3. Chạy regression trước khi push master: `python test_ai_rich.py` (85/85),
   `tools/test_3mode.py` (mở rộng test A/B/C), py_compile.
4. **Bản Desktop** (`…\Project1`): `git pull` (đang behind 1 commit origin) +
   merge → nhận đủ tính năng. Không sửa tay file trên Desktop.
5. Bảng feature so sánh cuối cùng trong report.

## File sửa

| File | Thay đổi |
|---|---|
| `VocabApp.py` | `media_strip`→panel dọc; `_render_vocab_panel`, `_render_grammar_panel`, `GrammarDetailDialog`, `_media_ring` fg_color |
| `api/gemini_safe.py` | `_last_email_used` + log đổi account trong `request`/`request_image` |
| `tools/test_3mode.py` | +test: panel vocab/grammar render, dialog grammar, log rotation |
| `docs/UPGRADE_17.md`, `projectLog.md` | ghi nhận A/B/C/D |

## Rủi ro / ràng buộc

- **Merge master→branch trước khi làm A/B/C** để conflict chỉ xảy ra 1 lần, code mới
  nằm trên nền đã hợp nhất.
- Không phá viewer cũ: `MediaViewerDialog`, ▶ `_play_vocab`, seq nghe cả ngày, badge cover.
- Tuyệt đối không bịa từ vựng: panel chỉ render dữ liệu lesson thật.
- Log chỉ hiện đổi account (không hiện mỗi request) → log_box không tràn.
