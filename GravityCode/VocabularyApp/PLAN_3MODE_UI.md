# PLAN — 3 NÚT CHẾ ĐỘ PHẢI THAY ĐỔI GÌ ĐÓ THẬT SỰ (sửa lỗi "bấm không thấy gì")

## Nguyên nhân thật (đã kiểm trong code)
1. `_load_mode()` ghi vào `fc_word`/`fc_back` — thuộc `flash_frame` — nhưng khi nguồn
   = "Khóa học AI" thì `flash_frame.pack_forget()` → widget đang ẩn, ghi cũng vô dụng.
2. `_load_mode()` dùng `self._current_day` (không tồn tại → luôn ngày 1) + đọc lại
   file JSON thay vì dùng `self._current_lesson` / `_get_day_lesson(_selected_day_num())`.
3. Hội thoại chưa có panel nghe (từng lượt / cả bài / tới lui) — chỉ có text.

## Phương án
B1. `_load_mode(mode)` làm lại:
   - Nếu đang ở nguồn tự học/SRS → tự chuyển sang "Khóa học AI" (cb_source + _on_source_change).
   - Set `self._study_mode` ∈ {full, vocab, grammar, dialogue}.
   - Render vào `lesson_text` (widget ĐANG HIỂN THỊ) chứ không phải flashcard ẩn.
   - Thêm nút 📑 "Tất cả" để quay về xem đầy đủ bài.
B2. Tách `_render_lesson_text` thành 4 section: `_section_vocab/_section_patterns/
   _section_common/_section_grammar/_section_dialogue`; mode lọc section nào hiển thị.
   - vocab → chỉ từ vựng (media strip ảnh ở trên vẫn hiện → có hình).
   - grammar → mẫu câu + câu thông dụng + ngữ pháp.
   - dialogue → kịch bản hội thoại.
B3. Panel HỘI THOẠI (`dlg_player`, nằm giữa media strip và ô nội dung, chỉ hiện khi
   chọn 🎧): danh sách lượt clickable, nút ▶️ từng lượt, ▶️ Nghe cả bài (tuần tự,
   chờ hết audio mới sang lượt), ⏮️/⏭️ chuyển lượt, ⏹ Dừng, highlight lượt đang phát.
B4. Test thật: py_compile + `tools/test_3mode.py` (gọi method không cần GUI, assert
   section theo mode + số lượt hội thoại) → commit.

## Tiêu chí nghiệm thu
- Bấm 📚 → ô nội dung chỉ còn TỪ VỰNG (+ ảnh media strip trên).
- Bấm 📖 → chỉ còn mẫu câu + ngữ pháp.
- Bấm 🎧 → kịch bản hội thoại + panel nghe (▶ từng lượt, cả bài, ⏮⏭⏹).
- Bấm 📑 Tất cả → hiện đủ bài như cũ.
- Đổi ngày → panel hội thoại tự theo ngày mới; không crash.
