# KẾ HOẠCH THÊM 3 CHẾ ĐỘ HỌC + TTS SONG NGỮ (Nhật → Vi)

## 1. Nội dung từng ngày (đã có) → chia 3 chế độ
- Từ vựng: vocab + image_ref + quiz_ab
- Ngữ pháp: sentence_patterns + common_sentences + grammar + quiz_cd
- Giao tiếp: dialogue[] (segment) + audio tracks

## 2. TTS song ngữ (Nhật trước → Vi sau)
- `ai/tts_config.py`: thêm `voice_for_bilingual(lang, mode="jp_first")`
- `pipeline_media.py`: `run_audio_stage`: tạo 2 track / từ (JP + VI explanation)
- Lưu vào `data/audio/tiếng_nhật/dXXXX/track_*.mp3`

## 3. Dialog segment + play control
- Mỗi `dialogue` có `turns[]`; thêm `segment_start/end`.
- GUI: click đoạn → play; nút « » trước/sau + phát cả bài.

## 4. GUI (VocabApp.py) — tối thiểu
- Tab/section: "Học từ" / "Ngữ pháp" / "Nghe hội thoại" (dùng nội dung đã có)
- Không cần viết lại toàn bộ; chỉ điều chỉnh render từ `course.json` + `media_manifest`.

## Thực hiện ngay
B1: Cấu hình TTS song ngữ trong `ttb_config.py` / `settings.json` (ai.tts_models: thêm `gemini-3.8-flash-tts` cho JP, `tts-vi` cho VI)
B2: Sửa `pipeline_media.py` audio: sinh 2 track / từ (JP first, VI second)
B3: Đánh dấu dialogue segment trong `course.json` cho ngày đã có
B4: Chạy `python -m ai.pipeline --stages audio,dialogue --from-day 1 --to-day 14 --allow-degraded`
B5: Kiểm tra `media/index.json` + `data/audio/` có file mới
