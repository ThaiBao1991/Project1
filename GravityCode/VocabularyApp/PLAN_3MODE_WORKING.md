# PLAN CHI TIẾT — NÚT 3 CHẾ ĐỘ PHẢI CHẠY THẬT (không chỉ hiển thị)

Bước 1 (ngay): _load_mode phải TẢI nội dung từ pipeline, không chỉ gửi tin nhắn.
- vocab → load course.json vocab cho ngày đang chọn; hiển thị thẻ từ + ảnh
- grammar → load sentence_patterns/common_sentences/grammar; hiển thị ví dụ câu + ngữ pháp
- dialogue → load dialogue[] từ checkpoint; hiển thị kịch bản + nút phát từng đoạn

Bước 2: Quiz phải sinh trước (đã chỉ lệnh)
- python -m ai.pipeline --stages quiz_ab,quiz_cd --from-day 1 --to-day 14

Bước 3: Audio segment
- pipeline_media đã hỗ trợ tuple (JP,VI); cần GUI thêm nút ▶️/⏸️/⏮️/⏭️ cho từng đoạn hội thoại
- Cần thêm vào StudyTab: frame dialogue + button segment play

Bước 4: Kiểm tra chạy thực
- Click mỗi nút → phải thấy nội dung thật (không trống)
- Trắc nghiệm phải xuất hiện câu hỏi
- Âm thanh song ngữ phải phát được (JP rồi VI)

Bước 5: Commit khi tất cả xanh
