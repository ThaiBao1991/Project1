# Roadmap: Hệ thống Bóc tách Knowledge Map Toàn bộ Dữ liệu Sango Heroes 7 (Tam Quốc Quần Anh Truyện 7)

## Day 1 — Tướng Ngụy Lô 1: Tào Tháo & Dòng Họ Tào, Hạ Hầu - Schema & Parsing
**Prompt:**
Trình bày tài liệu bách khoa toàn thư về thiết kế JSON Schema và bóc tách dữ liệu 15 tướng dòng họ Tào & Hạ Hầu (Tào Tháo, Tào Phi, Tào Trực, Tào Duệ, Tào Chương, Tào Nhân, Tào Hồng, Tào Thuần, Tào Chân, Tào Sảng, Hạ Hầu Đôn, Hạ Hầu Uyên, Hạ Hầu Thượng, Hạ Hầu Bá, Hạ Hầu Uy). Yêu cầu bắt buộc: Xuất dữ liệu hoàn toàn dưới dạng BẢNG MARKDOWN nghiêm ngặt (gồm bảng Schema thuộc tính Võ, Trí, Skill ẩn, Combo và bảng danh mục 15 tướng sau khi chuyển đổi bảng mã Big5/GBK sang UTF-8). TUYỆT ĐỐI KHÔNG dùng văn xuôi, không giải thích dài dòng hay viết văn phong giáo viên. KHÔNG dùng tiêu đề bắt đầu bằng '## Day'.

**Bài tập:**
- Xây dựng JSON Schema mẫu định nghĩa các trường chỉ số Võ, Trí, Skill ẩn, Combo cho tướng phe Ngụy.
- Lập bảng chuyển đổi mã tự động giải mã font Big5/GBK sang UTF-8 cho 15 tướng họ Tào và Hạ Hầu.
- Trích xuất và điền đầy đủ dữ liệu thuộc tính của Tào Tháo và Hạ Hầu Đôn vào bảng cấu trúc.

**Tags:**
#sango_heroes_7 #tuong_nguy #tao_thao #ha_hau_don #big5_encoding #json_schema

---

## Day 2 — Tướng Ngụy Lô 2: Ngũ Tử Lương Tướng & Mãnh Tướng - Automated Parsing
**Prompt:**
Trình bày tài liệu kỹ thuật bóc tách và kiểm tra tính toàn vẹn tham chiếu (Foreign Key Integrity) cho 15 mãnh tướng Ngũ Tử Lương Tướng & Mãnh Tướng (Trương Liêu, Từ Hoảng, Trương Cáp, Nhạc Tiến, Vu Cấm, Điển Vi, Hứa Chử, Bàng Đức, Văn Sính, Lý Điển, Hạo Chiêu, Hứa Định, Điền Trù, Trương Tú, Sầm Cung). Yêu cầu bắt buộc: Trình bày toàn bộ nội dung dưới dạng BẢNG MARKDOWN chi tiết thể hiện logic Python script parse file .INI/.PAK và bảng mapping Foreign Key giữa ID tướng với ID kỹ năng. KHÔNG viết văn xuôi hay lý thuyết tổng quát. KHÔNG dùng tiêu đề '## Day'.

**Bài tập:**
- Viết cấu trúc bảng mapping Foreign Key nối ID tướng Trương Liêu, Điển Vi với bảng ID Kỹ năng võ tướng.
- Mô tả thuật toán tự động giải mã file cấu hình .INI/.PAK dưới dạng bảng các bước thực thi Python.
- Lập bảng dữ liệu chuẩn hóa của 15 mãnh tướng bao gồm chỉ số Võ, Trí và ID kỹ năng tương ứng.

**Tags:**
#sango_heroes_7 #truong_liao #dien_vi #hua_chu #python_parser #foreign_key_integrity

---

## Day 3 — Tướng Ngụy Lô 3: Mưu Sĩ & Quân Sư Phe Ngụy - Data Validation
**Prompt:**
Trình bày quy trình Data Validation và xử lý dữ liệu null/rác cho 15 mưu sĩ và quân sư phe Ngụy (Tuân Úc, Tuân Du, Giả Hủ, Trình Dục, Quách Gia, Lưu Diệp, Mãn Sủng, Trần Quần, Chung Dao, Hứa Du, Huỳnh Kỷ, Hy Chí Tài, Dương Tu, Tưởng Tế, Quách Đồ). Yêu cầu bắt buộc: Xuất toàn bộ kết quả dưới dạng BẢNG MARKDOWN (gồm Bảng Quy tắc Validation Data Pipeline và Bảng Chỉ số Võ, Trí, Năng lực ẩn chuẩn hóa của 15 mưu sĩ). KHÔNG viết văn xuôi, KHÔNG giảng giải lý thuyết, KHÔNG dùng tiêu đề dạng '## Day'.

**Bài tập:**
- Thiết lập bảng quy tắc Data Validation phát hiện các giá trị null/rác trong chỉ số Trí và Năng lực ẩn của Quách Gia, Tuân Úc.
- Xây dựng bảng dữ liệu JSON chuẩn hóa cho 15 mưu sĩ Ngụy sau khi lọc sạch dữ liệu.
- Lập bảng so sánh chỉ số Trí và Quân sư kỹ của Giả Hủ, Trình Dục, Quách Đồ.

**Tags:**
#sango_heroes_7 #quach_gia #tuan_uc #gia_hu #data_validation #data_pipeline

---

## Day 4 — Tướng Ngụy Lô 4: Phe Tư Mã & Tướng Hậu Kỳ - Graph Relation Mapping
**Prompt:**
Trình bày mô hình Knowledge Graph Schema và kỹ thuật giải mã Hex/ID ẩn cho 15 tướng phe Tư Mã & Hậu kỳ (Tư Mã Ý, Tư Mã Sư, Tư Mã Chiêu, Tư Mã Vọng, Đặng Ngải, Chung Hội, Gia Cát Đán, Quách Hoài, Tôn Lễ, Vương Sương, Văn Khâm, Văn Ương, Trần Thái, Lỗ Chi, Quách Nữ Vương). Yêu cầu bắt buộc: Thể hiện nội dung duy nhất qua các BẢNG MARKDOWN (gồm Bảng Relational Mapping thực thể Thần thuộc/Thân tộc/Combo và Bảng Giải mã Hex/ID kỹ năng hợp thể). KHÔNG sử dụng văn phong giáo viên hay lời dẫn văn xuôi. KHÔNG dùng tiêu đề '## Day'.

**Bài tập:**
- Lập bảng định nghĩa mối quan hệ Relational Mapping giữa Tư Mã Ý, Tư Mã Sư, Tư Mã Chiêu và Đặng Ngải trong Knowledge Graph.
- Xây dựng bảng giải mã các mã Hex/ID ẩn tương ứng với kỹ năng combo hậu kỳ của Chung Hội và Văn Ương.
- Điền đầy đủ thông tin chỉ số và skill ẩn của 15 tướng hậu kỳ vào bảng dữ liệu cấu trúc.

**Tags:**
#sango_heroes_7 #tu_ma_y #dang_ngai #chung_hoi #knowledge_graph #relational_mapping

---

## Day 5 — Tướng Ngụy Lô 5: Nữ Tướng & Chư Tướng Phụ - Deduplication & Export
**Prompt:**
Trình bày quy trình Deduplication (khử trùng lặp) và đóng gói CSDL cho 15 nữ tướng và phụ tướng phe Ngụy (Biện Thị, Chân Mật, Tào Tiết, Hạ Hầu Kiều, Tào Huỳnh, Tào Tụ, Tào Tỉnh, Chu Lĩnh, Trương Ký, Vương Thiết, Tào Ứng, Hạ Hầu Hòa, Hạ Hầu Huệ, Quách Dịch, Tiêu Xung). Yêu cầu bắt buộc: Xuất toàn bộ báo cáo dưới dạng BẢNG MARKDOWN nghiêm ngặt (gồm Bảng đối soát Deduplication cross-check file config vs ingame và Bảng cấu trúc CSDL JSON/SQLite xuất bản của 75 tướng Ngụy). KHÔNG dùng văn xuôi, KHÔNG có dòng '## Day'.

**Bài tập:**
- Lập bảng cross-check kiểm thử trùng lặp (Deduplication) giữa file config gốc và dữ liệu ingame của Chân Mật, Biện Thị.
- Viết bảng mô tả Schema SQLite/JSON đóng gói toàn bộ CSDL 75 tướng Ngụy.
- Tổng hợp bảng thông số hoàn chỉnh cho 15 nữ tướng và tướng phụ phe Ngụy.

**Tags:**
#sango_heroes_7 #chan_mat #bien_thi #nu_tuong_nguy #deduplication #database_export

---

## Day 6 — Tướng Ngụy Lô 6: Hàng Tướng & Chư Hầu Quy Thuận Tào Ngụy
**Prompt:**
Trình bày tài liệu bóc tách và kiểm tra tính toàn vẹn khóa ngoại bằng Pydantic cho 12 hàng tướng quy thuận Tào Ngụy (Trương Cáp, Bàng Đức, Trương Tú, Giả Hủ, Hứa Du, Ngưu Kim, Khương Duy, Trương Lỗ, Vương Bình, Trương Tiên, Lục Khang, Hồ Sơ). Yêu cầu bắt buộc: Trình bày hoàn toàn bằng BẢNG MARKDOWN (gồm Bảng chuyển mã Big5->UTF-8 tên tướng, Bảng tham chiếu Skill ID khóa ngoại và Bảng Pydantic Data Validation). TUYỆT ĐỐI KHÔNG dùng văn xuôi, không giải thích rườm rà. KHÔNG tạo tiêu đề bắt đầu bằng '## Day'.

**Bài tập:**
- Xây dựng bảng Pydantic Data Validation kiểm tra tính đúng đắn của thuộc tính Võ, Trí cho Khương Duy, Trương Cáp.
- Lập bảng đối soát Foreign Key kết nối ID của 12 hàng tướng với bảng Skill ID kỹ năng võ tướng.
- Xuất bảng dữ liệu chuẩn hóa Big5 sang UTF-8 cho toàn bộ 12 hàng tướng quy thuận.

**Tags:**
#hang_tuong_nguy #sango_heroes_7 #chi_so_tuong #ky_nang_an #chuyen_ma_big5_utf8 #data_validation

---

## Day 7 — Tướng Ngụy Lô 7: Chư Tướng Trấn Thủ Biên Ải Tây Bắc Ngụy
**Prompt:**
Trình bày quy trình ánh xạ quan hệ (Relational Mapping) thành trì và khử trùng lặp (Deduplication) cho 12 tướng trấn thủ biên ải Tây Bắc Ngụy (Quách Hoài, Trần Thái, Đặng Ngai, Chung Hội, Điền Dự, Khiên Hoàn, Vương Hùng, Tô Tắc, Bàng Hội, Vương Song, Trương Ký, Táo Chi). Yêu cầu bắt buộc: Sử dụng duy nhất các BẢNG MARKDOWN để biểu diễn (gồm Bảng Relational Mapping ID Tướng - ID Thành Trì, Bảng phân loại chỉ số bản Vanilla v1.2 vs Mod, và Bảng kết quả Deduplication). KHÔNG dùng văn xuôi hay văn phong giảng dạy. KHÔNG chứa dòng '## Day'.

**Bài tập:**
- Lập bảng Relational Mapping nối ID tướng Quách Hoài, Đặng Ngai với ID các thành trì trấn thủ biên giới Tây Bắc.
- Xây dựng bảng so sánh biến thể chỉ số Võ, Trí của 12 tướng giữa phiên bản Vanilla v1.2 và bản Mod.
- Chạy logic Deduplication và lập bảng báo cáo xác minh tính duy nhất của dữ liệu tướng biên ải.

**Tags:**
#tuong_bien_ai #quach_hoai #dang_ngai #sango_heroes_7 #relational_mapping #deduplication

---

## Day 8 — Tướng Ngụy Lô 8: Văn Quan & Tướng Nội Chính Phe Ngụy
**Prompt:**
Trình bày thiết kế Graph Schema cho Quân sư kỹ và quy trình JSON Schema Verification cho 12 văn quan nội chính Ngụy (Chung Dao, Hoa Hâm, Vương Lãng, Trần Quần, Cao Nhu, Mao Giới, Thôi Diễm, Quốc Uyên, Đằng Chi, Giả Sung, Vi Quán, Lưu Diệp). Yêu cầu bắt buộc: Xuất nội dung dưới dạng BẢNG MARKDOWN nghiêm ngặt (gồm Bảng Node/Edge trong Knowledge Graph Schema cho Quân sư kỹ, Bảng xử lý thuộc tính Null/khuyết thiếu và Bảng JSON Schema Verification). TUYỆT ĐỐI KHÔNG dùng văn xuôi hay thuyết minh. KHÔNG có tiêu đề '## Day'.

**Bài tập:**
- Lập bảng định nghĩa Node và Edge trong Knowledge Graph biểu diễn Quân sư kỹ của Trần Quần, Chung Dao, Lưu Diệp.
- Xây dựng bảng quy tắc JSON Schema Verification nhằm gán giá trị mặc định cho thuộc tính ẩn bị khuyết thiếu.
- Tổng hợp bảng thuộc tính nội chính, Võ, Trí chuẩn hóa của 12 văn quan phe Ngụy.

**Tags:**
#van_quan_nguy #tran_quan #chung_dao #sango_heroes_7 #knowledge_graph_schema #json_schema_verification

---

## Day 9 — Tướng Ngụy Lô 9: Tuyệt Kỹ Hợp Thể & Combo Đội Hình Ngụy
**Prompt:**
Xây dựng bách khoa toàn thư trích xuất chi tiết 10 cặp combo kỹ năng tướng Ngụy và mô hình hóa mối quan hệ kích hoạt Tuyệt kỹ hợp thể trong đồ thị tri thức (Graph Database Neo4j/RDF Schema). Yêu cầu đảm bảo 100% ID tướng tham gia combo tồn tại và khớp chính xác với CSDL Tướng. Trình bày toàn bộ nội dung hoàn toàn bằng BẢNG MARKDOWN, tuyệt đối không sử dụng văn xuôi hay văn phong giáo viên.

**Bài tập:**
- Bóc tách thông số sát thương, năng lượng và hiệu ứng kích hoạt của 10 cặp combo kỹ năng tướng Ngụy.
- Xây dựng sơ đồ quan hệ Graph Edge cho các cặp tướng kích hoạt Tuyệt kỹ hợp thể trong đồ thị tri thức Neo4j.
- Thực hiện quy trình kiểm thử Automated Data Validation để đảm bảo 100% ID tướng tham gia combo tồn tại và khớp chính xác với CSDL Tướng.

**Tags:**
#sango_heroes_7 #combo_nguy #graph_database #neo4j #data_validation

---

## Day 10 — Tướng Ngụy Lô 10: Tướng Chỉ Huy Hổ Báo Kỵ & Binh Chủng
**Prompt:**
Tạo bách khoa toàn thư trích xuất chi tiết 12 tướng thống lĩnh binh chủng Ngụy bao gồm: Tào Thuần, Tào Chân, Tào Sảng, Hạ Hầu Thượng, Hứa Định, Điển Mãn, Tào Sương, Lương Tập, Hạ Hầu Bá, Trương Cầu, Tào Huấn, Tào Hy và kết nối cây tiến hóa Hổ Báo Kỵ. Thực hiện đóng gói hoàn chỉnh dữ liệu toàn bộ Tướng Ngụy vào Data Pipeline. Yêu cầu xuất kết quả duy nhất dưới dạng BẢNG MARKDOWN, tuyệt đối không dùng văn xuôi.

**Bài tập:**
- Lập bảng trích xuất chỉ số Võ, Trí và kỹ năng phụ trợ của 12 tướng chỉ huy binh chủng Ngụy.
- Xây dựng cây tiến hóa binh chủng Hổ Báo Kỵ kết nối trực tiếp với ID của từng tướng chỉ huy.
- Thiết kế script ETL Data Pipeline bằng Python Pandas để làm sạch, tổng hợp và đóng gói toàn bộ dữ liệu Tướng Ngụy.

**Tags:**
#sango_heroes_7 #ho_bao_ky #tao_thuan #etl_pipeline #data_extraction

---

## Day 11 — Tướng Thục Lô 1: Lưu Bị & Ngũ Hổ Tướng Phe Thục
**Prompt:**
Trích xuất bách khoa toàn thư dữ liệu 11 tướng Thục bao gồm: Lưu Bị, Quan Vũ, Trương Phi, Triệu Vân, Mã Siêu, Hoàng Trung, Lưu Thiền, Lưu Phong, Lưu Vĩnh, Lưu Lý, Lưu Kham. Tiến hành giải mã và chuyển đổi hoàn tất bảng mã Big5 sang UTF-8 không đứt vỡ font, đồng thời xác minh tính đầy đủ của thuộc tính ẩn và chỉ số Võ, Trí. Trình bày hoàn toàn bằng BẢNG MARKDOWN, tuyệt đối không dùng văn xuôi.

**Bài tập:**
- Giải mã và chuyển đổi tệp dữ liệu cấu hình General.ini từ bảng mã Big5 sang UTF-8 cho 11 tướng thuộc phe Thục.
- Trích xuất chi tiết chỉ số Võ, Trí, Tướng quân kỹ và các thuộc tính năng lực ẩn của danh sách 11 tướng.
- Kiểm tra và validate cấu trúc dữ liệu trích xuất theo định dạng JSON Schema chuẩn.

**Tags:**
#sango_heroes_7 #luu_bi #ngu_ho_tuong #big5_encoding #data_extraction

---

## Day 12 — Tướng Thục Lô 2: Gia Cát Lượng & Mưu Sĩ Quan Sự Phe Thục
**Prompt:**
Tạo dữ liệu bách khoa toàn thư bóc tách chi tiết 12 mưu sĩ Thục bao gồm: Gia Cát Lượng, Bàng Thống, Pháp Chính, Từ Thứ, Tưởng Uyển, Phí Y, Đổng Hòa, Mã Lương, Mã Tốc, Y Tịch, Giản Ung, Tôn Càn. Đảm bảo tính toàn vẹn tham chiếu (FK Integrity) giữa Quân Sư Kỹ và ID Tướng. Yêu cầu trình bày 100% bằng BẢNG MARKDOWN, không dùng văn xuôi.

**Bài tập:**
- Bóc tách chỉ số Võ, Trí, danh mục Quân sư kỹ và các kỹ năng ẩn chiến trường của 12 mưu sĩ Thục.
- Chạy script Data Integrity Checker nhằm đảm bảo tính toàn vẹn tham chiếu khóa ngoại giữa Quân Sư Kỹ và ID Tướng.
- Chuẩn hóa dữ liệu, phát hiện và xử lý triệt để các thuộc tính bị trùng lặp hoặc bỏ sót.

**Tags:**
#gia_cat_luong #bang_thong #mou_si_thuc #fk_integrity #sango_heroes_7

---

## Day 13 — Tướng Thục Lô 3: Khương Duy & Chư Tướng Hậu Kỳ Bắc Phạt
**Prompt:**
Trích xuất bách khoa toàn thư dữ liệu chuẩn hóa 12 tướng Bắc Phạt bao gồm: Khương Duy, Ngô Ý, Ngô Ban, Đặng Chi, Trương Dực, Trương Niệm, Liêu Hóa, Vương Bình, Mã Trung, Hướng Sủng, La Hiến, Hoàng Sùng. Yêu cầu phân biệt rõ ràng chỉ số phiên bản game gốc (Vanilla) và các bản Mod mở rộng. Trình bày toàn bộ thông tin dưới dạng BẢNG MARKDOWN, tuyệt đối không dùng văn xuôi.

**Bài tập:**
- Trích xuất chỉ số Võ, Trí và thuộc tính ẩn của 12 tướng Bắc Phạt từ tệp cấu hình game Sango Heroes 7.
- Thực hiện Data Normalization để làm sạch tên gọi và loại bỏ toàn bộ ký tự rác do lỗi mã hóa font.
- So sánh và lập bảng đối chiếu chỉ số tướng giữa phiên bản game gốc (Vanilla) và các bản Mod mở rộng.

**Tags:**
#khuong_duy #bac_phat #data_normalization #vanilla_vs_mod #sango_heroes_7

---

## Day 14 — Tướng Thục Lô 4: Nữ Tướng & Thân Tộc Mãnh Tướng Phe Thục
**Prompt:**
Xây dựng bách khoa toàn thư bóc tách dữ liệu 11 tướng Thục gồm: Hoàng Nguyệt Anh, Tôn Thượng Hương, Trương Tinh Thái, Quan Ngân Bình, Bào Tam Nương, Quan Bình, Quan Hưng, Trương Bao, Mã Đái, Nghiêm Nhan, Ngụy Diên. Xác định chính xác ID quan hệ thân tộc/huyết thống giữa các thực thể tướng. Bắt buộc trình bày bằng BẢNG MARKDOWN, tuyệt đối không dùng văn xuôi.

**Bài tập:**
- Trích xuất thuộc tính đặc thù, chỉ số Võ, Trí và kỹ năng ẩn của 11 nữ tướng và thân tộc mãnh tướng Thục.
- Xây dựng bảng Relational Mapping Sheet xác định ID quan hệ thân tộc/huyết thống giữa các thực thể tướng.
- Validate tính đầy đủ và hợp lệ của toàn bộ các trường dữ liệu theo JSON Schema.

**Tags:**
#hoang_nguyet_anh #quan_ngan_binh #nu_tuong_thuc #entity_relationship #sango_heroes_7

---

## Day 15 — Tướng Thục Lô 5: Tuyệt Kỹ Hợp Thể & Combo Đội Hình Phe Thục
**Prompt:**
Trích xuất bách khoa toàn thư và mô hình hóa đồ thị tri thức (Graph Schema Mapping) cho 10 tuyệt kỹ hợp thể và combo: Đào Viên Kết Nghĩa, Long Phượng Hòa Minh, Ngũ Hổ Phá Địch, Thần Sương Hợp Bích, Quan Hưng Trương Bao Hợp Kích, Triệu Vân Ngụy Diên Combo, Trần Đáo, Mã Vận Lộc, Đặng Lương, Lưu Ba. Hoàn thành bảng ánh xạ mối quan hệ N-N giữa danh sách Võ Tướng và Tuyệt Kỹ Hợp Thể. Trình bày kết quả 100% bằng BẢNG MARKDOWN, không dùng văn xuôi.

**Bài tập:**
- Trích xuất điều kiện kích hoạt, tham số sát thương và hiệu ứng chi tiết của 10 tuyệt kỹ hợp thể và combo.
- Mô hình hóa bảng ánh xạ quan hệ N-N giữa Võ Tướng và Tuyệt Kỹ Hợp Thể trong Neo4j/JSON-LD Mapping.
- Thực hiện Cross-validation kiểm tra đối chiếu dữ liệu ID tướng tham chiếu từ kết quả Day 11 đến Day 14.

**Tags:**
#dao_vien_ket_nghia #combo_thuc #graph_schema #tuyet_ky_hop_the #cross_validation

---

## Day 16 — Tướng Thục Lô 6: Chư Tướng Ích Châu & Quan Viên Trấn Thủ Hán Trung
**Prompt:**
Tạo bách khoa toàn thư bóc tách dữ liệu chi tiết 16 tướng Ích Châu & Hán Trung: Nghiêm Nhan, Ngô Ý, Ngô Ban, Lý Nghiêm, Đặng Chi, Phí Y, Đổng Hòa, Lưu Ba, Lã Nghĩa, Dương Hồng, Mã Huống, Vương Bình, Trương Niệm, Ngụy Diên, Trương Dực, Trương Dĩ. Chuẩn hóa bảng mã Big5 sang UTF-8, khắc phục trùng lặp dữ liệu và xác minh Foreign Key với ID tướng gốc. Bắt buộc trình bày dưới dạng BẢNG MARKDOWN, không dùng văn xuôi.

**Bài tập:**
- Bóc tách chỉ số Võ, Trí và thuộc tính ẩn của 16 tướng Ích Châu & Hán Trung từ file INI gốc.
- Chuyển đổi bảng mã Big5/GBK sang UTF-8 và làm sạch ký tự rác lỗi font.
- Xác minh tính toàn vẹn khóa ngoại (Foreign Key Integrity) giữa ID tướng gốc và các bảng dữ liệu kỹ năng liên quan.

**Tags:**
#tuong_ich_chau #han_trung #big5_to_utf8 #foreign_key #sango_heroes_7

---

## Day 17 — Tướng Thục Lô 7: Tướng Lĩnh Nam Trung & Thổ Hào Quy Thuận Phe Thục
**Prompt:**
Trích xuất và lập bảng dữ liệu thuộc tính cho các thực thể Nam Trung & Thổ Hào: Mạnh Hoạch, Chúc Dung, Mộc Lộc Đại Vương, Ngột Đột Cốt, Đái Lai Động Chủ, Mang Nha Trường, Kim Hoàn Tam Kết, A Hội Nam, Đổng Trà Na, Lữ Khải, Trương Dực, Mã Trung, Quan Sách, Hoa Mạn, Vương Hàng. Yêu cầu: Xuất kết quả dưới dạng BẢNG MARKDOWN nghiêm ngặt (chứa các cột: ID, Tên Tướng, Chỉ Số Võ, Chỉ Số Trí, Kỹ Năng Ẩn, Binh Chủng Đặc Chủng, Bảng Mã Gốc, Trạng Thái Khử Trùng Lặp). Thực hiện chuyển đổi bảng mã Big5/GBK sang UTF-8, khử trùng lặp thực thể (như Trương Dực) và kiểm tra Data Integrity. TUYỆT ĐỐI KHÔNG sử dụng văn xuôi, không dùng văn phong giáo viên, không thêm dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Viết script Python giải mã GBK/Big5 sang UTF-8 cho file dữ liệu Sango Heroes 7.
- Thực hiện khử trùng lặp dữ liệu ID cho tướng Trương Dực giữa Lô 6 và Lô 7.

**Tags:**
#TươngNamTrung #MạnhHoạch #ChúcDung #SangoHeroes7 #Deduplication #DataValidation

---

## Day 18 — Tướng Thục Lô 8: Văn Quan Nội Chính & Tướng Hậu Cần Phe Thục
**Prompt:**
Trích xuất dữ liệu và thiết lập bảng cho nhóm Văn Quan & Hậu Cần Thục: Mã Lương, Mã Túc, Tưởng Uyển, Phí Y, Đổng Doãn, Tiêu Chu, Trần Chấn, Chu Thương, Vương Phủ, Triệu Lũy, Y Tịch, Tôn Càn, Giản Ung, Mi Chúc, Mi Phương. Yêu cầu: Trả về BẢNG MARKDOWN nghiêm ngặt (gồm các cột: ID, Tên Tướng, Chỉ Số Võ, Chỉ Số Trí, Quân Sư Kỹ, Năng Lực Hậu Cần, Chuẩn Bậc Chuẩn Hóa 1NF/2NF/3NF). Kiểm tra tính toàn vẹn 1NF/2NF/3NF, khử trùng lặp (Phí Y), mã hóa chuẩn UTF-8 và validate bằng JSON Schema. TUYỆT ĐỐI KHÔNG viết văn xuôi, không có lời dẫn giáo viên, không dùng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Xây dựng JSON Schema để validate dữ liệu văn quan Thục.
- Kiểm tra và chuẩn hóa bảng dữ liệu hậu cần Thục đạt chuẩn dạng chuẩn 3NF.

**Tags:**
#VănQuanThục #NộiChính #TướngHậuCần #SangoHeroes7 #DataNormalization #JSONSchema

---

## Day 19 — Tướng Ngô Lô 1: Tôn Kiên, Tôn Sách, Tôn Quyền & Tôn Thị Hoàng Tộc
**Prompt:**
Bóc tách dữ liệu chi tiết cho 16 thực thể Tôn Thị Hoàng Tộc: Tôn Kiên, Tôn Sách, Tôn Quyền, Tôn Tĩnh, Tôn Du, Tôn Kiều, Tôn Hoàn, Tôn Đăng, Tôn Lượng, Tôn Hưu, Tôn Hạo, Tôn Chiêu, Tôn Trầm, Tôn Khuông, Tôn Dực, Tôn Lực. Yêu cầu: Xuất kết quả BẢNG MARKDOWN nghiêm ngặt (các cột: ID Tướng, Tên Tướng, Chỉ Số Võ, Chỉ Số Trí, Trung Thành, Danh Vọng, Quan Hệ Huyết Thống, Mã Bảng Mã). Chuẩn hóa thành công tên tướng từ Big5 sang UTF-8. TUYỆT ĐỐI KHÔNG trả về văn xuôi, không dùng lời thoại hướng dẫn, không dùng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Trích xuất file Setting.ini/General.ini phe Ngô bằng script chuyển đổi Big5 sang UTF-8.
- Thiết lập sơ đồ cây huyết thống Tôn Thị dựa trên dữ liệu ID.

**Tags:**
#TônKiên #TônSách #TônQuyền #TônThịHoàngTộc #Big5Encoding

---

## Day 20 — Tướng Ngô Lô 2: Tứ Đại Đô Đốc Chu Du, Lỗ Túc, Lữ Mông, Lục Tốn & Mưu Sĩ
**Prompt:**
Bóc tách dữ liệu 15 thực thể Tứ Đại Đô Đốc & Mưu Sĩ Đông Ngô: Chu Du, Lỗ Túc, Lữ Mông, Lục Tốn, Gia Cát Cẩn, Trương Chiêu, Trương Hoành, Cố Ung, Bộ Chất, Ngu Phiên, Chu Phường, Lục Kháng, Gia Cát Khác, Sầm Hôn, Nghiêm Bội. Yêu cầu: Xuất kết quả BẢNG MARKDOWN nghiêm ngặt (các cột: ID Tướng, Tên Tướng, Võ, Trí, Chính Trị, Skill Ẩn, Quân Sư Kỹ, Địa Bàn Khởi Đầu). Thực hiện Data Validation kiểm tra trùng lặp ID và thuộc tính Trí/Chính trị. TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không ghi heading bắt đầu bằng '## Day'.

**Bài tập:**
- Viết Python script validation kiểm tra tính duy nhất của ID các mưu sĩ Ngô.
- Định nghĩa Schema JSON kiểm thử thuộc tính Trí và Quân sư kỹ của Tứ Đại Đô Đốc.

**Tags:**
#ChuDu #LỗTúc #LữMông #LụcTốn #DataValidation

---

## Day 21 — Tướng Ngô Lô 3: Thái Sử Từ, Cam Ninh & Giang Đông Thập Nhị Hổ Thần
**Prompt:**
Trích xuất thuộc tính 15 thực thể Giang Đông Thập Nhị Hổ Thần và võ tướng phụ cận: Thái Sử Từ, Cam Ninh, Trình Phổ, Hoàng Cái, Hàn Đương, Chu Thái, Tưởng Khâm, Đinh Phụng, Từ Thịnh, Trần Vũ, Lăng Thống, Phan Chương, Đổng Tập, Phí Sạn, Chu Kiệt. Yêu cầu: Trả về BẢNG MARKDOWN nghiêm ngặt (cột: ID Tướng, Tên Võ Tướng, Võ, Trí, Tỷ Lệ Né Tránh, Danh Sách Skill Chiến Đấu, ID Võ Tướng Kỹ - FK). Kiểm tra tính toàn vẹn khóa ngoại (Foreign Key Integrity) giữa ID Tướng và ID Kỹ Năng. TUYỆT ĐỐI KHÔNG dùng văn xuôi hay lời giải thích, không dùng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Chạy script Python (Pydantic) kiểm tra ràng buộc Foreign Key giữa ID võ tướng và ID kỹ năng.
- Xây dựng bảng liên kết mối quan hệ phối hợp chiến đấu giữa Giang Đông Thập Nhị Hổ Thần.

**Tags:**
#TháiSửTừ #CamNinh #ThậpNhịHổThần #ChuThái #ForeignKeyIntegrity

---

## Day 22 — Tướng Ngô Lô 4: Nữ Tướng Đông Ngô & Chư Tướng Hậu Kỳ Phe Ngô
**Prompt:**
Bóc tách thuộc tính 15 thực thể Nữ Tướng & Chư Tướng Hậu Kỳ Ngô: Tôn Thượng Hương, Đại Kiều, Tiểu Kiều, Bộ Phu Nhân, Ngô Quốc Thái, Tôn Lỗ Ban, Tôn Lỗ Dục, Chu Cốc, Cố Đàm, Cố Thừa, Lục Cảnh, Ngô Cảnh, Chu Xuyện, Vạn Úc, Đồ Cừu. Yêu cầu: Trả về BẢNG MARKDOWN nghiêm ngặt (các cột: ID Tướng, Tên Tướng, Chỉ Số Võ, Chỉ Số Trí, Đặc Tính Ẩn, Mốc Thời Gian Xuất Hiện, Trạng Thái Data Cleaning). Xử lý và loại bỏ các giá trị null hoặc ID thiếu tài liệu (undocumented). TUYỆT ĐỐI KHÔNG viết văn xuôi hay văn phong giáo viên, không ghi heading bắt đầu bằng '## Day'.

**Bài tập:**
- Thực hiện quy trình Data Cleaning lọc các bản ghi null trong file config Nữ tướng Ngô.
- Gán nhãn mốc thời gian xuất hiện của từng tướng vào Knowledge Graph Schema.

**Tags:**
#NữTướngNgô #TônThượngHương #ĐạiKiều #TiểuKiều #DataCleaning

---

## Day 23 — Tướng Ngô Lô 5: Skill Combo Hợp Thể & Binh Chủng Thủy Quân Đông Ngô
**Prompt:**
Trích xuất 15 thực thể Combo Skill & Thủy Quân Đông Ngô: Skill Hoả Thiêu Xích Bích, Skill Thủy Thần Nộ Đào, Combo Tôn Sách Thái Sử Từ, Combo Chu Du Tiểu Kiều, Combo Tôn Quyền Lục Tốn, Thủy Quân, Lâu Thuyền, Mông Xung, Đẫn Luân Xung, Skill Hỏa Long Oanh, Combo Giang Đông Trụ Thạch, Skill Ẩn Chu Du, Skill Ẩn Cam Ninh, Skill Ẩn Thái Sử Từ, Skill Ẩn Lục Tốn. Yêu cầu: Định dạng BẢNG MARKDOWN nghiêm ngặt (cột: ID Thực Thể, Tên Skill/Combo/Binh Chủng, Sát Thương, Điều Kiện Kích Hoạt, Tướng Sở Hữu, Đặc Tính Thủy Quân, Relational Mapping ID). Đảm bảo liên kết thành công Relational Mapping. TUYỆT ĐỐI KHÔNG viết văn xuôi hay lời chào, không dùng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Xây dựng Relational Mapping nối các cặp tướng Ngô với Skill Combo tương ứng.
- Tổng hợp và chạy test suite kiểm thử toàn vẹn dữ liệu toàn bộ Phase Tướng Ngô.

**Tags:**
#ComboSkillNgô #ThủyQuân #XíchBích #LâuThuyền #RelationalMapping

---

## Day 24 — Tướng Ngô Lô 6: Văn Quan Nội Chính, Ngoại Giao & Tham Mưu Phe Ngô
**Prompt:**
Trích xuất và chuẩn hóa dữ liệu thực thể Văn quan Ngô gồm Trương Chiêu, Trương Hoành, Cố Ung, Gia Cát Cẩn, Bộ Chất. Yêu cầu: Trả về BẢNG MARKDOWN nghiêm ngặt (cột: ID Tướng, Tên Văn Quan, Chỉ Số Võ, Chỉ Số Trí, Skill Ẩn, Tham Số Nội Chính, Tham Số Ngoại Giao, Foreign Key Kỹ Năng). Xử lý dứt điểm lỗi font Big5 sang UTF-8, kiểm tra tính toàn vẹn Foreign Key với bảng kỹ năng và định nghĩa Schema JSON. TUYỆT ĐỐI KHÔNG dùng văn xuôi hay lời giải thích giáo viên, không dùng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Viết script Python giải mã mã hóa Big5 sang UTF-8 cho danh sách Văn quan Ngô.
- Kiểm tra ràng buộc Foreign Key giữa bảng Văn quan và bảng Quân sư kỹ trong JSON Schema.

**Tags:**
#tướngngô #vănquan #trươngchiêu #nộichính #big5encoding #jsonschema

---

## Day 25 — Tướng Ngô Lô 7: Hàng Tướng Quy Thuận & Chư Hầu Trấn Thủ Giang Đông
**Prompt:**
Hãy thực hiện trích xuất và ánh xạ dữ liệu nhóm Hàng Tướng & Chư Hầu Giang Đông gồm Lưu Do, Nghiêm Bạch Hổ, Vương Lãng vào CSDL Graph/Relational Schema. Đảm bảo kết quả đạt 100% thực thể không bị rác và vượt qua Pydantic schema validation. Trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Trích xuất các chỉ số Võ, Trí và Kỹ năng ẩn của Lưu Do, Nghiêm Bạch Hổ, Vương Lãng từ file cấu hình gốc.
- Viết kịch bản Pydantic Schema Validator để làm sạch các giá trị null/rác và chuẩn hóa tên thực thể.
- Thực hiện mapping liên kết phe phái ban đầu cho nhóm hàng tướng Giang Đông vào CSDL.

**Tags:**
#hang_tuong #luu_do #nghiem_bach_ho #pydantic_validation #graph_schema

---

## Day 26 — Tướng Ngô Lô 8: Chư Tướng Trấn Thủ Cận Biên & Bình Định Sơn Việt
**Prompt:**
Hãy bóc tách dữ liệu chư tướng bình định Sơn Việt gồm Lã Đái, Hà Tề, Toàn Tông và thiết lập quan hệ địa lý trấn thủ STATIONED_AT trong Knowledge Graph (Neo4j/Postgres). Xuất kết quả đúng định dạng liên kết Tướng - Thành Trì Trấn Thủ. Trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Trích xuất thuộc tính Võ, Trí và khả năng đặc biệt khi chinh phạt Sơn Việt của Lã Đái, Hà Tề, Toàn Tông.
- Thiết lập quan hệ STATIONED_AT giữa tướng trấn thủ và vùng đất biên giới trong Graph Schema.
- Xuất bảng tổng hợp liên kết Tướng - Thành Trì Trấn Thủ dưới dạng cấu trúc bảng dữ liệu chuẩn hóa.

**Tags:**
#tran_thu #son_viet #la_dai #ha_te #knowledge_graph

---

## Day 27 — Tướng Ngô Lô 9: Trang Bị Bảo Vật & Binh Khí Đặc Chủng Thủy Chiến Ngô
**Prompt:**
Hãy trích xuất và liên kết dữ liệu bảo vật, thủy chiến hạm phe Ngô gồm Cổ Điển Kiếm, Mông Xung, Lâu Thuyền vào Item Schema. Đảm bảo bảng trích xuất đầy đủ chỉ số và kiểm tra đúng Foreign Key reference với ID tướng sở hữu. Trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Trích xuất chỉ số thuộc tính của Cổ Điển Kiếm, Mông Xung, Lâu Thuyền từ các file Item.ini và Ship.ini.
- Ánh xạ hiệu ứng đặc biệt (tăng thủ thủy quân, vô hiệu thủy chiến) vào Item Schema.
- Chạy script kiểm tra ràng buộc Foreign Key giữa ID vật phẩm/chiến thuyền và ID tướng sở hữu ban đầu.

**Tags:**
#bao_vat_ngo #co_dien_kiem #mong_xung #lou_chuan #item_schema

---

## Day 28 — Tướng Ngô Lô 10: Mưu Sĩ Hậu Kỳ & Quân Sư Kỹ Đặc Biệt Phe Ngô
**Prompt:**
Hãy bóc tách, tổng hợp mưu sĩ hậu kỳ Ngô gồm Lục Kháng, Gia Cát Khác, hoàn thiện Knowledge Map phe Ngô và vượt qua các Unit Test kiểm tra trùng lặp/thiếu hụt dữ liệu để sẵn sàng đóng gói RESTful API. Trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Trích xuất chỉ số Võ, Trí và Quân sư kỹ đặc biệt của Lục Kháng, Gia Cát Khác.
- Viết Unit Test bằng Python kiểm tra tính thống nhất, chống trùng lặp (Deduplication) dữ liệu tướng Ngô.
- Đóng gói Knowledge Map toàn bộ phe Ngô thành định dạng JSON chuẩn bị cho RESTful API.

**Tags:**
#quan_su_ngo #luc_khang #gia_cat_khac #unit_test #etl_pipeline

---

## Day 29 — Tướng Quần Hùng Lô 1: Đổng Trác, Lữ Bố & Tây Lương - Trích Xuất & Chuẩn Hóa Bảng Mã Big5/GBK
**Prompt:**
Hãy trích xuất dữ liệu danh sách tướng phe Đổng Trác, Lữ Bố, Hoa Hùng, Trương Liêu và chuyển đổi thành công bảng mã font tiếng Trung từ Big5/GBK sang UTF-8 chuẩn xác. Trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Bóc tách chỉ số Võ, Trí và Skill ẩn của Đổng Trác, Lữ Bố, Hoa Hùng, Trương Liêu từ file INI/PAK gốc.
- Xây dựng script chuyển đổi encoding từ Big5/GBK sang UTF-8 không để hỏng ký tự tiếng Trung.
- Đối chiếu tính toàn vẹn ID tướng sau khi giải mã với bảng danh mục gốc của game.

**Tags:**
#quan_hung #dong_trac #lu_bo #encoding_utf8 #big5_gbk

---

## Day 30 — Tướng Quần Hùng Lô 2: Thế Lực Nhị Viên & Cross-Validation Dữ Liệu Quan Hệ
**Prompt:**
Hãy trích xuất tướng phe Viên Thiệu, Viên Thuật, Nhan Lương, Văn Xú và xây dựng quy tắc Cross-check kiểm tra tính toàn vẹn Foreign Key giữa ID Tướng và ID Phe phái trong CSDL. Trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Trích xuất thông số chỉ số và skill ẩn của các thực thể Viên Thiệu, Viên Thuật, Nhan Lương, Văn Xú.
- Viết kịch bản Validation kiểm tra tính hợp lệ của Foreign Key kết nối Tướng - Phe phái.
- Thực hiện khử trùng lặp (Deduplication) dữ liệu giữa các bản Mod và cấu hình Vanilla.

**Tags:**
#vien_thieu #vien_thuat #nhan_luong #van_xu #foreign_key_check

---

## Day 31 — Tướng Quần Hùng Lô 3: Khăn Vàng, Nam Man & Mô Hình Hóa Thuộc Tính Dị Tộc
**Prompt:**
Hãy định nghĩa thành công JSON Schema thuộc tính dị tộc cho Yêu thuật Khăn Vàng và Nam Man Tượng Binh, đồng thời trích xuất đầy đủ thông số Võ, Trí của Trương Giác, Mạnh Hoạch, Chúc Dung. Trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Mô hình hóa Schema thuộc tính dị tộc dành cho Yêu thuật Khăn Vàng và binh chủng Nam Man Tượng Binh.
- Trích xuất chỉ số Võ, Trí, nội tại dị tộc của Trương Giác, Mạnh Hoạch, Chúc Dung.
- Chuẩn hóa tên gọi và các thuộc tính phép thuật/dị tộc vào tập tin JSON Schema chuẩn.

**Tags:**
#truong_giac #manh_hoach #chuc_dung #khan_vang #json_schema

---

## Day 32 — Tướng Quần Hùng Lô 4: Các Chư Hầu Các Vùng & Thiết Lập Relational Graph Mapping
**Prompt:**
Hãy trích xuất bảng dữ liệu các chư hầu Công Tôn Toản, Mã Đằng, Lưu Biểu, Đào Khiêm, Trương Lỗ và tạo liên kết Relational Graph Mapping thể hiện mối quan hệ giữa Chư Hầu - Thành Trì Khởi Đầu - Binh Chủng. Trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Trích xuất chỉ số Võ, Trí của các chư hầu Công Tôn Toản, Mã Đằng, Lưu Biểu, Đào Khiêm, Trương Lỗ.
- Xây dựng sơ đồ Relational Mapping nối Chư Hầu với Thành trì khởi đầu và Lực lượng phụ thuộc.
- Làm sạch và khử trùng lặp dữ liệu chư hầu giữa các file save và file config hệ thống.

**Tags:**
#chu_hau #cong_ton_toan #ma_dang #luu_bieu #graph_mapping

---

## Day 33 — Tướng Quần Hùng Lô 5: Nữ Tướng, Skill Combo & Tích Hợp Knowledge Graph Quần Hùng
**Prompt:**
Trích xuất Nữ Tướng, Tuyệt Kỹ/Combo Hợp Thể và đóng gói Knowledge Graph toàn bộ Phase Quần Hùng bao gồm các thực thể: Điêu Thuyền, Lữ Linh Khởi, Trương Ninh, cùng các kỹ năng hợp thể Lữ Bố - Điêu Thuyền, Đổng Trác - Lữ Bố. Xuất file Knowledge Graph JSON đầy đủ liên kết Tướng - Skill Combo - Binh Chủng. YÊU CẦU BẮT BUỘC: Trả lời hoàn toàn dưới dạng BẢNG MARKDOWN nghiêm ngặt, tuyệt đối không dùng văn xuôi, không giải thích lý thuyết chung chung, không có lời chào hay văn phong giáo viên, không tạo header bắt đầu bằng '## Day'.

**Bài tập:**
- Bóc tách chỉ số và điều kiện kích hoạt tuyệt kỹ của Điêu Thuyền, Lữ Linh Khởi, Trương Ninh.
- Thiết lập quan hệ kích hoạt Kỹ Năng Hợp Thể cho cặp Lữ Bố - Điêu Thuyền và Đổng Trác - Lữ Bố trong Neo4j/JSONB.
- Validate JSON Schema toàn bộ Knowledge Graph Phase Quần Hùng và xuất dữ liệu hoàn chỉnh.

**Tags:**
#dieu_thuyen #nu_tuong #skill_combo #quan_hung #knowledge_graph #data_integration

---

## Day 34 — Tướng Quần Hùng Lô 6: Chư Tướng Liêu Đông & Thế Lực Bộc Phát Đông Bắc
**Prompt:**
Trích xuất và chuẩn hóa dữ liệu 20 tướng Liêu Đông & Đông Bắc: Công Tôn Độ, Công Tôn Khang, Công Tôn Cung, Công Tôn Uyên, Công Tôn Chi, Liễu Phụ, Vương Đằng, Tần Hứa, Bối Tái, Giáp Viện, Hàn Bân, Dương Tụ, Trương Đương, Vô Lại, Tào Cửu, Tôn Diêu, Chu Kính, Lưu Lăng, Doãn Lễ, Từ Vinh từ file config game. Chuyển đổi thành công bảng mã Big5/GBK sang UTF-8 và validate chỉ số Võ, Trí, Chỉ huy. YÊU CẦU BẮT BUỘC: Trả lời hoàn toàn bằng BẢNG MARKDOWN chuẩn hóa, không sử dụng văn xuôi hay văn phong hướng dẫn, không dùng header '## Day'.

**Bài tập:**
- Trích xuất chỉ số Võ, Trí, Chỉ huy và năng lực ẩn của 20 tướng Liêu Đông từ file INI/PAK.
- Viết script Python Pandas/Pydantic chuyển đổi toàn bộ danh xưng từ mã Big5/GBK sang UTF-8.
- Thực hiện Data Validation kiểm tra trùng lặp ID và tính toàn vẹn dữ liệu cho lô tướng Liêu Đông.

**Tags:**
#lieu_dong #cong_ton_do #dong_bac #quan_hung #big5_utf8

---

## Day 35 — Tướng Quần Hùng Lô 7: Tướng Lĩnh Tây Lương & Các Tộc Khương, Hung Nô
**Prompt:**
Trích xuất và chuẩn hóa danh mục tướng Tây Lương & Dị Tộc Khương, Hung Nô gồm 20 thực thể: Mã Đằng, Hàn Toại, Mã Thiết, Mã Hưu, Thành Nghi, Trương Hoành, Lương Hưng, Dương Thu, Ngân Cứ, Hồ Sa Tiên, Tiên Vu Phụ, Tiên Vu Ngân, Tốc Phụ Nhai, Khang Khải, Vu Phu La, Hô Trù Tuyền, Bàn Hòa, Trụ Kế, Khương Tụ, Liêu Lan. Xác minh Faction Mapping và ID liên kết chuẩn xác. YÊU CẦU BẮT BUỘC: Chỉ sử dụng BẢNG MARKDOWN để trình bày dữ liệu, không có văn xuôi, không có lời dẫn giáo viên, không tạo tiêu đề dạng '## Day'.

**Bài tập:**
- Bóc tách chỉ số gốc và kỹ năng ẩn của Mã Đằng, Hàn Toại và các thủ lĩnh dị tộc Khương, Hung Nô.
- Xây dựng Faction Mapping kết nối tướng Tây Lương với phe phái và chỉ số lòng trung thành ban đầu.
- Lập quy trình tự động quét rác dữ liệu, xử lý các giá trị Null và kiểm tra tính hợp lệ của ID tướng.

**Tags:**
#tay_luong #han_toai #hung_no #khuong_toc #faction_mapping

---

## Day 36 — Tướng Quần Hùng Lô 8: Mưu Sĩ & Tham Mưu Độc Lập Chư Hầu
**Prompt:**
Trích xuất chi tiết và xây dựng schema dữ liệu mưu sĩ Quần Hùng gồm 20 thực thể: Điền Phong, Thư Thụ, Hứa Du, Quách Đồ, Phùng Kỷ, Thẩm Phối, Lý Nho, Giả Hủ, Trần Cung, Tôn Càn, Doãn Phụ, Diêm Bộc, Dương Tùng, Hàn Dược, Chu Lập, Doãn Khải, Dương Hoành, Diêm Ung, Ngô Cốt, Vi Khang. Indexing ID và Validate JSON Schema cho chỉ số trí tuệ/quân sư kỹ. YÊU CẦU BẮT BUỘC: Trả kết quả DUY NHẤT dưới dạng BẢNG MARKDOWN, tuyệt đối không văn xuôi, không lời thoại hướng dẫn, không viết heading '## Day'.

**Bài tập:**
- Bóc tách chỉ số Trí, Võ, danh sách Quân Sư Kỹ của Điền Phong, Trần Cung, Giả Hủ và các mưu sĩ.
- Tạo cơ chế Indexing ID mưu sĩ phục vụ cho việc truy vấn Knowledge Graph.
- Thực hiện Cross-check xác minh tính nhất quán dữ liệu mưu sĩ giữa các file cấu hình gốc.

**Tags:**
#muu_si #dien_phong #tran_cung #gia_hu #indexing #json_schema

---

## Day 37 — Tướng Quần Hùng Lô 9: Thủ Lĩnh Dị Tộc Nam Man, Oa Quốc & Các Thủ Lĩnh Sơn Lâm
**Prompt:**
Trích xuất dữ liệu chuẩn hóa thủ lĩnh Dị Tộc Nam Man, Oa Quốc & Sơn Lâm gồm 20 thực thể: Ty Mi Hô, Nan Thăng Mễ, Đô Ma, Thinh Thố, Đái Lai Động Chủ, Mộc Lộc Đại Vương, Đột Cốt Hoạch, Mang Nha Trường, Kim Hoàn Tam Kết, A Cối Nam, Đổng Đồ Na, Tháp Đốn, Bối Tái, Phục Đa, Sa Mạc Kha, Thê Kha Nùng, Vu Độc, Quách Đại, Lưu Tôn, Tả Hiệu. Chuyển đổi mã hóa GBK/Big5 sang UTF-8 và kiểm tra Foreign Key Integrity. YÊU CẦU BẮT BUỘC: Trả về BẢNG MARKDOWN nghiêm ngặt, không dùng câu văn dẫn dắt hay lý thuyết suông, không viết heading bắt đầu bằng '## Day'.

**Bài tập:**
- Trích xuất chỉ số Võ, Trí, đặc tính kháng địa hình của Ty Mi Hô và các thủ lĩnh dị tộc Nam Man, Oa Quốc.
- Khắc phục triệt để lỗi mã hóa GBK/Big5 sang UTF-8 cho tên tướng dị tộc.
- Kiểm tra Foreign Key Integrity giữa danh sách thủ lĩnh dị tộc với các thành trì/địa bàn tương ứng.

**Tags:**
#di_toc #oa_quoc #ty_mi_ho #nam_man #foreign_key_integrity

---

## Day 38 — Tướng Quần Hùng Lô 10: Binh Chủng Đặc Chủng, Bảo Vật & Vũ Khí Quần Hùng
**Prompt:**
Trích xuất và liên kết dữ liệu Binh chủng đặc chủng & Bảo vật Quần Hùng: Đằng Giáp Binh, Voi Chiến, Thiết Kỵ Tây Lương, Khăn Vàng Binh, Man Binh, Tiên Phong Kỳ, Xích Thố Mã, Phương Thiên Họa Kích, Cổ Điển Nhị Kích, Thất Tinh Báu Kiếm, Thái Cực Phi Đao, Ngũ Hỏa Thần Diệm Phiến, Tru Tiên Kiếm, Hùng Hoàng Tửu, Truy Phong Bạch Hoàng, Hoàng Tinh Bổng, Thanh Long Nha, Hàn Băng Nhẫn, Thần Phong Cung, Phượng Hoàng Vũ. Thiết lập Relational Mapping giữa Tướng - Binh Chủng - Bảo Vật. YÊU CẦU BẮT BUỘC: Trình bày 100% bằng BẢNG MARKDOWN, cấm hoàn toàn văn xuôi hay văn phong giáo viên, cấm header '## Day'.

**Bài tập:**
- Trích xuất thuộc tính công thủ của Đằng Giáp Binh, Voi Chiến và chỉ số cộng thêm của Xích Thố Mã, Phương Thiên Họa Kích.
- Thiết lập Relational Mapping liên kết ID bảo vật/binh chủng với danh sách tướng sở hữu mặc định.
- Chạy Automated Data Validation kiểm tra trùng lặp ID và tính hợp lệ của thuộc tính vật phẩm/binh chủng.

**Tags:**
#binh_chung #bao_vat #xich_tho #phuong_thien #relational_mapping #data_validation

---

## Day 39 — Tướng Kinh Châu Lưu Biểu & Các Chư Hầu Độc Lập Giang Nam
**Prompt:**
Trích xuất chi tiết 14 thực thể Kinh Châu & Giang Nam: Lưu Biểu, Lưu Tông, Cai Mạo, Trương Vẫn, Hoàng Tổ, Văn Sính, Hàn Huyền, Kim Toàn, Triệu Phạm, Lưu Độ, Lưu Bàn, Hình Đạo Vinh, Khoái Lương, Khoái Việt. Xuất đủ 14 thực thể, chuẩn hóa bảng mã Big5/GBK sang UTF-8, mô hình hóa Graph Schema và kiểm tra Foreign Key Integrity. YÊU CẦU BẮT BUỘC: Trả về duy nhất BẢNG MARKDOWN chuẩn, không có văn xuôi, không giải thích dài dòng, không dùng heading '## Day'.

**Bài tập:**
- Trích xuất thuộc tính chỉ số và thế lực của Lưu Biểu, Hình Đạo Vinh và 12 thực thể Kinh Châu từ General.ini.
- Xây dựng Graph Schema thể hiện mối quan hệ giữa Tướng - Phe Phái - Thành Trì khu vực Kinh Châu & Giang Nam.
- Thực hiện kiểm tra tính toàn vẹn khóa ngoại (Foreign Key Integrity) và loại bỏ hoàn toàn rác dữ liệu.

**Tags:**
#kinh_chau #luu_bieu #hinh_dao_vinh #giang_nam #big5_to_utf8 #data_integrity

---

## Day 40 — Tướng Ích Châu Lưu Chương & Thế Lực Ngũ Đấu Mễ Đạo Trương Lỗ
**Prompt:**
Trích xuất chi tiết 14 thực thể Ích Châu & Hán Trung: Lưu Chương, Lưu Yên, Trương Lỗ, Nghiêm Nhan, Trương Nhiệm, Lý Nghiêm, Lăng Bao, Lưu Thuẫn, Đặng Hiền, Trương Vệ, Dương Tùng, Dương Bách, Ngô Ý, Trương Tùng. Giải mã tiếng Trung sang UTF-8, thiết lập Relational Mapping và chạy Data Integrity Check. YÊU CẦU BẮT BUỘC: Trả lời bằng BẢNG MARKDOWN nghiêm ngặt, không văn xuôi, không mở bài kết bài kiểu giáo viên, không tạo tiêu đề '## Day'.

**Bài tập:**
- Trích xuất chỉ số Võ, Trí, Danh tiếng của Lưu Chương, Trương Lỗ, Trương Nhiệm và chư tướng Ích Châu/Hán Trung.
- Xây dựng sơ đồ Relational Mapping giữa chư hầu Lưu Chương, Trương Lỗ với các tướng thuộc quyền.
- Chạy script Data Integrity Check kiểm tra tính tham chiếu ID tướng và lọc sạch trùng lặp dữ liệu.

**Tags:**
#luu_chuong #truong_lo #ich_chau #han_trung #relational_mapping #data_validation

---

## Day 41 — Đạo Sĩ, Tiên Nhân & Các Nhân Vật Ẩn Sĩ Kịch Bản Quần Hùng
**Prompt:**
Trình bày nội dung bách khoa toàn thư dưới dạng BẢNG MARKDOWN NGHIÊM NGẠC, TUYỆT ĐỐI KHÔNG DÙNG VĂN XUÔI HOẶC VĂN PHONG GIÁO VIÊN. Yêu cầu trích xuất chi tiết 12 nhân vật tiên nhân và ẩn sĩ bao gồm: Tả Từ, Vu Cát, Nam Hoa Lão Tiên, Quản Lộ, Hoa Đà, Tư Mã Huy, Hoàng Thừa Ngạn, Hứa Thiệu, Kiều Huyền, Kiều Công, Bàng Đức Công, Thủy Kính Tiên Sinh từ tệp dữ liệu General.ini. Đảm bảo bóc tách hoàn chỉnh 12 tiên nhân/ẩn sĩ cùng các chỉ số ẩn và kỹ năng đặc biệt, đồng thời hoàn thành liên kết Graph Nodes giữa Tiên nhân - Event trigger - Bảo vật truyền thuyết đúng chuẩn Schema JSON đã quy định.

**Bài tập:**
- Trích xuất chỉ số Võ, Trí và Hidden Flags của 12 nhân vật ẩn sĩ từ General.ini.
- Xây dựng Knowledge Graph Schema kết nối 12 tiên nhân với các sự kiện kích hoạt và bảo vật truyền thuyết.
- Thực hiện kiểm thử Normalization Check dữ liệu đầu ra và đóng gói vào Knowledge Map.

**Tags:**
#tien_nhan #ta_tu #vu_cat #an_si #hidden_flags #knowledge_graph

---

## Day 42 — Bóc Tách & Chuẩn Hóa Mã Font Big5/UTF-8 Nữ Tướng Độc Quyền & Nữ Tướng Ẩn Sĩ
**Prompt:**
Yêu cầu trình bày báo cáo kỹ thuật hoàn toàn bằng BẢNG MARKDOWN, KHÔNG Viết LỜI DẪN HAY VĂN XUÔI. Thực hiện trích xuất và xử lý bảng mã Big5 -> UTF-8 cho 15 nữ tướng: Điêu Thuyền, Chân Tốt, Đại Kiều, Tiểu Kiều, Tôn Thượng Hương, Hoàng Nguyệt Anh, Chúc Dung, Quan Ngân Bình, Bào Tam Nương, Trương Tinh Thái, Mã Vân Lộc, Vương Dị, Trương Xuân Hoa, Hạ Hầu Thị, Ngô Quốc Thái. Kết quả đầu ra phải tạo thành Bảng JSON/Markdown 15 nữ tướng chuẩn hóa font UTF-8 không lỗi hiển thị và vượt qua toàn bộ kiểm thử Data Validation đảm bảo tính toàn vẹn các trường thuộc tính.

**Bài tập:**
- Chạy script Python chardet/codecs chuyển đổi bảng mã Big5/GBK sang UTF-8 cho 15 nữ tướng.
- Bóc tách thuộc tính ẩn, duyên phận và quan hệ hôn nhân của danh sách nữ tướng.
- Viết test case Pydantic để kiểm tra tính hợp lệ của schema dữ liệu thuộc tính nữ tướng.

**Tags:**
#nu_tuong #tuong_an #sango_7 #big5_utf8 #data_integrity

---

## Day 43 — Bóc Tách Dữ Liệu Tướng Oa Quốc Nhật Bản & Thiết Kế Schema Đồ Thị Phe Phái
**Prompt:**
Hãy lập bảng tổng hợp bách khoa toàn thư DƯỚI DẠNG BẢNG MARKDOWN NGUYÊN BẢN, KHÔNG DÙNG CÁC ĐOẠN ĐẪN VĂN XUÔI. Thực hiện trích xuất 15 tướng Oa Quốc: Bỉ Tế Hô (Himiko), Y Dữ (Iyo), Kiến Ngự Danh Phương, Tức Trưởng Đái Cơ, Khuyển Thần, Quỷ Phòng, Tư Ma Bộc Bố, Nguyện Hương, Trữ Đô, Thái Cát, Y Chi Mỗ, Tô Ngã, Phú Thọ, Thần Cốc, Bạt Cửu và định nghĩa Graph Schema phe Oa Quốc. Phải xuất thành công File JSON 15 tướng Oa Quốc kèm mã ID thực thể chuẩn và mô hình hóa thành công schema đồ thị quan hệ giữa Himiko và chư tướng Oa Quốc.

**Bài tập:**
- Bóc tách ID ẩn, chỉ số Võ/Trí và kỹ năng triệu hoán độc quyền Oa Quốc từ file .INI.
- Xây dựng Graph Schema định nghĩa quan hệ phụ thuộc phe phái giữa Himiko và các tướng Oa Quốc.
- Xuất dữ liệu tướng Oa Quốc ra định dạng JSON kèm mã ID thực thể chuẩn hóa.

**Tags:**
#oa_quoc #himiko #nhat_ban #ngoai_toc #graph_schema

---

## Day 44 — Bóc Tách Thủ Lĩnh Dị Tộc Nam Man & Xây Dựng ETL Pipeline Tự Động Validation
**Prompt:**
Cung cấp bảng bóc tách dữ liệu BẰNG BẢNG MARKDOWN DUY NHẤT, KHÔNG CHỨA LỜI GIẢI THÍCH DẠNG VĂN XUÔI. Tiến hành trích xuất 15 thủ lĩnh Nam Man & Dị Tộc: Mạnh Hoạch, Mang Nha Trường, Đái Lai Động Chủ, Mộc Lộc Đại Vương, Đóa Tư Đại Vương, Ngột Đột Cốt, A Hội Nan, Kim Toàn, Đổng Đồ Na, Sa Mạn, Khảm Quý, Bích Tự, Mang Chiết, Ngũ Đột Đặc, Sơn Tôn và đưa vào Pipeline làm sạch dữ liệu. Đảm bảo xuất bảng dữ liệu Nam Man vượt qua toàn bộ unit test validation, khắc phục triệt để lỗi trùng lặp ID hoặc thiếu thuộc tính kháng địa hình/độc.

**Bài tập:**
- Bóc tách chỉ số chỉ huy Voi Chiến, Mây Độc và thuộc tính kháng độc của 15 thủ lĩnh Nam Man.
- Xây dựng ETL Pipeline làm sạch dữ liệu rác và chuẩn hóa tên gọi thủ lĩnh dị tộc.
- Thực hiện Unit Test Validation để phát hiện trùng lặp ID và thiếu thuộc tính địa hình.

**Tags:**
#nam_man #di_toc #ngot_dot_cot #etl_pipeline #data_validation

---

## Day 45 — Bóc Tách Tướng Thần Thoại, Tiên Nhân & Reverse Engineering Unpack File Binary
**Prompt:**
Định dạng toàn bộ nội dung dưới dạng BẢNG MARKDOWN TRUY VẤN DỮ LIỆU, KHÔNG DÙNG NGUYÊN LÝ VĂN XUÔI. Thực hiện trích xuất 15 nhân vật thần thoại & tiên nhân: Tả Từ, Vu Cát, Nam Hoa Lão Tiên, Quản Lộ, Trương Lương, Hạng Vũ, Càn Khôn Đạo Nhân, Bạch Hổ Giả, Thanh Long Giả, Chu Tước Giả, Huyền Vũ Giả, Hoàng Long, Tả Đạo Nhân, Mộc Ma, Cửu Thiên Huyền Nữ bằng phương pháp đọc Hex/Memory Offset. Đạt tiêu chuẩn đầu ra với Bảng dữ liệu 15 tiên nhân kèm danh sách ID thần thú triệu hoán và tài liệu ghi nhận Memory Offset / Struct Layout của tướng thần thoại.

**Bài tập:**
- Đọc Memory Offset/Hex trong file binary gốc để bóc tách chỉ số cực đại của các tướng thần thoại.
- Trích xuất danh sách ID thần thú triệu hoán và phép thuật Tứ Linh đi kèm.
- Lập tài liệu Struct Layout chi tiết cho nhóm nhân vật tiên nhân và thần thoại.

**Tags:**
#than_thoai #tien_nhan #ta_tu #hang_vu #reverse_engineering #hex_editing

---

## Day 46 — Bóc Tách Thần Tướng Phục Sinh & Tích Hợp Đồ Thị Tri Thức Knowledge Graph
**Prompt:**
Yêu cầu trình bày kết quả tích hợp theo BẢNG MARKDOWN DUY NHẤT, TUYỆT ĐỐI KHÔNG SỬ DỤNG VĂN XUÔI HOẶC LỜI BÀN LUẬN CỦA GIÁO VIÊN. Thực hiện trích xuất 15 thần tướng special: Hàn Tín, Anh Bố, Phàn Khoái, Tiêu Hà, Bành Việt, Chu Bột, Quán Anh, Khương Tử Nha, Bạch Khởi, Liêm Pha, Tần Thủy Hoàng, Thần Quan Vũ, Thần Triệu Vân, Thần Lữ Bố, Thần Gia Cát Lượng và tích hợp toàn bộ Phase vào Knowledge Graph. Hoàn thành trích xuất đầy đủ hệ số thuộc tính đặc biệt và nạp thành công dữ liệu Phase vào Knowledge Graph với 0 lỗi ràng buộc liên kết.

**Bài tập:**
- Trích xuất bộ kỹ năng Phục Sinh và các hệ số thuộc tính đặc biệt vượt ngưỡng của 15 thần tướng.
- Mô hình hóa điều kiện mở khóa thần tướng trong kịch bản Bát Quái / Phục Sinh.
- Nạp dữ liệu vào Neo4j/PostgreSQL JSONB và kiểm thử liên kết Tướng - Trang bị - Kỹ năng.

**Tags:**
#than_tuong #han_tin #bach_khoi #knowledge_graph #integration #neo4j

---

## Day 47 — Kỹ Năng & Chỉ Số Nữ Tướng Nhật Bản, Nam Man Độc Quyền
**Prompt:**
Yêu cầu trình bày dữ liệu dạng BẢNG MARKDOWN NGHIÊM NGẠC, KHÔNG CÓ BẤT KỲ VĂN XUÔI DẪN NHẮT NÀO. Trích xuất chi tiết và chuẩn hóa bảng mã (GBK/Big5 -> UTF-8) dữ liệu các nữ tướng Nhật Bản, Nam Man: Nữ Vương Himiko, Yosano, Iyo, A Hội Nhoát, Mãng Nha Trường, Thổ An Vương, Mộc Lộc Đại Vương, Mang Trung, Hoa Mạn, Nữ Vương Oda, Sanada, Tuyết Nữ, Sơn Khôi, Đái Lai Động Chủ. Kết quả phải đảm bảo đúng bảng Markdown và JSON Schema, không bỏ sót bất kỳ thực thể nào và đảm bảo dữ liệu tên, mô tả không bị lỗi font chữ.

**Bài tập:**
- Sử dụng công cụ chuyển đổi bảng mã GBK/Big5 sang UTF-8 cho toàn bộ tập dữ liệu nữ tướng ngoại tộc.
- Trích xuất chỉ số Võ, Trí, kỹ năng ẩn độc quyền của Nữ Vương Himiko, Oda, Sanada, Tuyết Nữ.
- Chuẩn hóa Schema JSON và chạy Data Validation xác minh dữ liệu làm sạch không bị lỗi mã hóa.

**Tags:**
#nu_tuong #nhat_ban #nam_man #chi_so #gbk_utf8 #data_validation

---

## Day 48 — Chỉ Số Tướng Thần Thoại Vô Diện & Ma Vương Kịch Bản
**Prompt:**
Nội dung bách khoa toàn thư phải được thể hiện DƯỚI DẠNG BẢNG MARKDOWN HOÀN CHỈNH, CẤM SỬ DỤNG VĂN XUÔI VÀ THÁI ĐỘ GIẢNG GIẢI. Bóc tách chỉ số, thuộc tính ẩn và xác minh tính toàn vẹn tham chiếu (Foreign Key Integrity) cho nhóm tướng Thần thoại, Ma vương: Hạng Vũ, Ngu Cơ, Lưu Bang, Hàn Tín, Bạch Khởi, Nhạc Phi, Tôn Tẫn, Cửu Thiên Huyền Nữ, Nam Hoa Lão Tiên, Tả Từ, Vu Cát, Tỳ Khưu Lão Nhân, Thần Long, Hoàng Long, Huyền Vũ. Yêu cầu hoàn thành bảng trích xuất đầy đủ chỉ số Võ, Trí, năng lực ẩn và Cross-check đảm bảo ID tướng khớp chính xác với hệ thống ID kỹ năng và trang bị đi kèm.

**Bài tập:**
- Bóc tách điều kiện xuất hiện, chỉ số Võ/Trí và năng lực ẩn của nhóm tướng Thần thoại/Ma vương.
- Viết script Python chạy Data Integrity Check để kiểm tra Foreign Key giữa ID tướng, ID kỹ năng và ID trang bị.
- Đóng gói toàn bộ tập dữ liệu thành các Graph Nodes hoàn chỉnh chuẩn bị cho Knowledge Map.

**Tags:**
#than_thoai #ma_vuong #vo_dien #tuong_an #data_integrity #foreign_key

---

## Day 49 — Bóc tách Binh chủng Bộ Binh & Thương Binh Tier 1-3 và Chuẩn hóa Encoding
**Prompt:**
Hãy lập BÁCH KHOA TOÀN THƯ kỹ thuật trình bày dưới dạng BẢNG MARKDOWN nghiêm ngặt (TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, KHÔNG viết dòng heading bắt đầu bằng '## Day') để trích xuất và chuẩn hóa bảng dữ liệu Bộ Binh & Thương Binh các cấp bao gồm 12 thực thể: Bộ Binh, Trảm Ma Binh, Thần Kiếm Binh, Thương Binh, Đại Thương Binh, Thần Thương Binh, Bộc Đao Binh, Trường Đao Binh, Thần Đao Binh, Đao Thuẫn Binh, Thuẫn Giáp Binh, Thần Thuẫn Binh từ file .INI game. Yêu cầu hiển thị đầy đủ thông số: ID, Tên thực thể, Mã hóa Big5/GBK sang UTF-8, Máu (HP), Tốc độ di chuyển, Tầm đánh, Ma trận khắc chế/bị khắc, Cấp tiến hóa Tier 1-3 và Data integrity validation (đạt 100%).

**Bài tập:**
- Viết Python script giải mã bảng mã Big5/GBK từ file config game Sango Heroes 7 sang UTF-8 cho 12 thực thể Bộ Binh và Thương Binh.
- Trích xuất các thuộc tính Máu, Tốc độ, Tầm đánh và định nghĩa điều kiện tiến hóa Tier 1-3 vào file JSON/Markdown.
- Thực hiện Unit Test kiểm tra tính toàn vẹn dữ liệu quan hệ khắc chế của 12 thực thể đảm bảo validation 100%.

**Tags:**
#bo_binh #thuong_binh #tien_hoa #chi_so_binh_chung #big5_utf8 #data_validation

---

## Day 50 — Bóc tách Binh chủng Kỵ Binh & Tượng Binh Tier 1-3 và Mapping Schema
**Prompt:**
Hãy lập BÁCH KHOA TOÀN THƯ kỹ thuật dưới dạng BẢNG MARKDOWN nghiêm ngặt (TUYỆT ĐỐI KHÔNG dùng văn xuôi, KHÔNG dùng văn phong giáo viên, KHÔNG viết dòng heading bắt đầu bằng '## Day') để trích xuất và chuẩn hóa dữ liệu Kỵ Binh & Tượng Binh gồm 12 thực thể: Kỵ Binh, Trùng Kỵ Binh, Tinh Anh Kỵ Binh, Tượng Binh, Cự Tượng Binh, Thần Tượng Binh, Nhông Binh, Mãnh Nhông Binh, Thần Nhông Binh, Hổ Báo Kỵ, Thiết Kỵ Binh, Thần Kỵ Binh. Yêu cầu bảng dữ liệu thể hiện các cột: ID, Tên binh chủng, Cấp Tier (1-3), Máu (HP), Tốc độ di chuyển, Tốc độ đánh, Hệ thống khắc chế (Kỵ vs Bộ/Cung), Điều kiện tiến hóa, và Schema validation (không thuộc tính null rác).

**Bài tập:**
- Viết script bóc tách dữ liệu Kỵ Binh & Tượng Binh từ file cấu hình game binary/INI.
- Xây dựng ma trận khắc chế chi tiết giữa Kỵ Binh vs Bộ Binh và Cung Binh.
- Sử dụng JSON Schema validator để kiểm thử dữ liệu 12 thực thể, loại bỏ các thuộc tính null hoặc rác.

**Tags:**
#ky_binh #tuong_binh #chi_so_binh_chung #tien_hoa #json_schema #matrix_khac_che

---

## Day 51 — Bóc tách Cung Binh & Khí Giới Tầm Xa Tier 1-3 và Kiểm thử Toàn vẹn
**Prompt:**
Hãy lập BÁCH KHOA TOÀN THƯ kỹ thuật trình bày hoàn toàn bằng BẢNG MARKDOWN (TUYỆT ĐỐI KHÔNG dùng văn xuôi hay lời dẫn giáo viên, KHÔNG viết dòng heading bắt đầu bằng '## Day') trích xuất dữ liệu Cung Binh & Khí Giới Tầm Xa cho 12 thực thể: Cung Binh, Cung Kỵ Binh, Tinh Anh Cung Binh, Nỏ Binh, Cự Nỏ Binh, Thần Nỏ Binh, Lang Cung Binh, Thần Cung Binh, Tiễn Lâu Xa, Mộc Thú, Hoàng Thiên Binh, Đầu Thạch Xa. Bảng phải chuẩn hóa các cột: ID, Tên thực thể, Tầm bắn, Sát thương base, Máu, Tốc độ, Cấp tiến hóa Tier 1-3, Foreign Key ID tiến hóa, và kết quả Cross-check ingame.

**Bài tập:**
- Xây dựng parser trích xuất các thông số Tầm bắn, Sát thương, Máu, Tốc độ của Cung Binh & Khí Giới Tầm Xa.
- Thực hiện chuẩn hóa dữ liệu (Data Normalization) và loại bỏ trùng lặp trong config file.
- Viết Unit Test kiểm tra Ràng buộc khóa ngoại (Foreign Key integrity) liên kết các cấp tiến hóa Tier 1-3.

**Tags:**
#cung_binh #no_binh #khi_gioi #tien_hoa_binh_chung #data_normalization #unit_test

---

## Day 52 — Bóc tách Binh chủng Đặc Biệt, Nữ Binh, Thủy Quân & Ninja Tier 1-3
**Prompt:**
Hãy lập BÁCH KHOA TOÀN THƯ kỹ thuật trình bày dưới dạng BẢNG MARKDOWN nghiêm ngặt (TUYỆT ĐỐI KHÔNG văn xuôi, KHÔNG văn phong hướng dẫn/giáo viên, KHÔNG viết dòng heading bắt đầu bằng '## Day') để trích xuất 12 thực thể Binh chủng Đặc Biệt, Nữ Binh, Thủy Quân & Ninja: Địch Kiếm Binh, Nữ Binh, Dụ Phong Nữ, Vũ Nữ, Thái Phong Vũ Nữ, Thủy Binh, Sương Hải Thủy Binh, Long Phượng Thủy Binh, Ninja, Thượng Cấp Ninja, Khỏa Giáp Binh, Đa Cực Binh. Bảng phải hiển thị rõ các cột: ID, Tên Việt hóa UTF-8, Máu, Tốc độ, Hệ số né tránh, Kỹ năng/Hiệu ứng ẩn (khống chế, di chuyển trên nước, tàng hình), Cấp tiến hóa, và trạng thái xử lý ID undocumented.

**Bài tập:**
- Xây dựng ETL pipeline Python để trích xuất thuộc tính của Nữ Binh, Thủy Quân và Ninja từ file unpacked config.
- Lập bảng phân tích chi tiết hiệu ứng kỹ năng đặc biệt và thuộc tính ẩn của Vũ Nữ, Ninja, Thủy Binh.
- Xử lý chuẩn hóa tên tiếng Việt UTF-8 và làm sạch toàn bộ ID ẩn không có tài liệu miêu tả.

**Tags:**
#nu_binh #vu_nu #thuy_binh #ninja #thuoc_tinh_an #etl_pipeline

---

## Day 53 — Bóc tách Binh chủng Dị Tộc, Quái Vật & Thần Binh Huyền Thoại và Tổng hợp Graph Data
**Prompt:**
Hãy lập BÁCH KHOA TOÀN THƯ kỹ thuật dạng BẢNG MARKDOWN nghiêm ngặt (TUYỆT ĐỐI KHÔNG văn xuôi, KHÔNG lời giảng giáo viên, KHÔNG viết dòng heading bắt đầu bằng '## Day') trích xuất Dị Tộc, Quái Vật & Thần Binh Huyền Thoại gồm 12 thực thể: Nam Man Tượng Binh, Oa Quốc Võ Sĩ, Hung Nô Kỵ Binh, Cốt Binh, Tử Linh Binh, Ma Tuệ Binh, Đồng Nhân, Mộc Nhân, Long Pháo Binh, Kỳ Lân Binh, Thần Long Binh, Phượng Hoàng Binh. Bảng bao gồm: ID, Tên thực thể, Loại (Dị Tộc/Quái Vật/Thần Binh), Máu, Tốc độ, Khắc chế đặc biệt, Thuộc tính sinh tồn, Cây tiến hóa, và Schema Knowledge Graph Nodes/Edges.

**Bài tập:**
- Trích xuất và kiểm thử toàn bộ chỉ số Máu, Tốc độ, Sát thương của 12 thực thể Dị Tộc, Quái Vật và Thần Binh.
- Thực hiện Data Validation trên tổng số 60 thực thể binh chủng đã trích xuất qua các ngày.
- Đóng gói dataset JSON Schema và thiết lập ma trận quan hệ cây tiến hóa để đưa vào Knowledge Graph DB.

**Tags:**
#di_toc #quai_vat #than_binh #chi_so_tien_hoa #knowledge_graph #data_validation

---

## Day 54 — Bóc tách & Chuẩn hóa Binh chủng Tier 1-2: Bộ Binh, Đao Binh & Thương Binh
**Prompt:**
Hãy lập BÁCH KHOA TOÀN THƯ kỹ thuật dưới dạng BẢNG MARKDOWN nghiêm ngặt (TUYỆT ĐỐI KHÔNG dùng văn xuôi, KHÔNG dùng văn phong giáo viên, KHÔNG viết dòng heading bắt đầu bằng '## Day') để bóc tách & chuẩn hóa Binh chủng Tier 1-2 thuộc các hệ Bộ Binh, Đao Binh, Thương Binh, Kiếm Binh, Thuẫn Binh. Bảng thể hiện các thuộc tính: Mã ID gốc, Mã Encoding Big5, Tên tiếng Việt UTF-8, Tier (1 hoặc 2), Máu (HP), Tốc độ di chuyển, Tốc độ đánh, Ma trận Khắc chế/Bị khắc, và Kết quả kiểm thử Pydantic/JSON Schema validation.

**Bài tập:**
- Trích xuất thuộc tính Máu, Tốc độ, Tốc đánh của các loại Bộ Binh/Đao/Thương/Thuẫn Tier 1-2 từ config INI.
- Viết hàm chuyển đổi bảng mã Big5/GBK sang UTF-8 không lỗi font cho các binh chủng Tier 1-2.
- Áp dụng Pydantic/JSON Schema validation kiểm tra tính đầy đủ của thuộc tính và ma trận khắc chế.

**Tags:**
#binh_chung #tien_hoa #bo_binh #tier_1_2 #big5_utf8

---

## Day 55 — Bóc tách & Chuẩn hóa Binh chủng Tier 1-2: Kỵ Binh, Cung Binh & Nỗ Binh
**Prompt:**
Hãy lập BÁCH KHOA TOÀN THƯ kỹ thuật trình bày hoàn toàn dạng BẢNG MARKDOWN (TUYỆT ĐỐI KHÔNG văn xuôi hay văn phong giảng dạy, KHÔNG viết dòng heading bắt đầu bằng '## Day') để trích xuất & chuẩn hóa Kỵ Binh, Cung Binh, Nỗ Binh Tier 1-2. Bảng gồm các cột: ID Binh chủng gốc, ID Binh chủng tiến hóa (Tier 2), Tên tiếng Việt UTF-8, Hệ binh chủng, Máu, Tốc độ di chuyển, Tầm bắn tầm xa, Hệ số khắc chế Kỵ vs Bộ, và Trạng thái kiểm tra ràng buộc Foreign Key integrity.

**Bài tập:**
- Xây dựng pipeline parse file INI trích xuất Máu, Tốc độ, Tầm bắn của Kỵ Binh, Cung Binh, Nỗ Binh Tier 1-2.
- Áp dụng quy tắc chuyển đổi bảng mã font Big5 và lập bảng ma trận khắc chế giữa Kỵ Binh và Bộ Binh.
- Kiểm tra ràng buộc Foreign Key integrity kết nối chính xác giữa ID Tier 1 và ID Tier 2.

**Tags:**
#binh_chung #ky_binh #cung_binh #tier_1_2 #foreign_key_validation

---

## Day 56 — Bóc tách & Chuẩn hóa Binh chủng Tier 3: Tinh Anh Cấp Cao & Thần Binh
**Prompt:**
Hãy lập BÁCH KHOA TOÀN THƯ kỹ thuật bằng BẢNG MARKDOWN nghiêm ngặt (TUYỆT ĐỐI KHÔNG văn xuôi, KHÔNG văn phong giáo viên, KHÔNG viết dòng heading bắt đầu bằng '## Day') bóc tách toàn bộ Binh chủng Tier 3 Tinh Anh Cấp Cao & Thần Binh (Thần Đao Binh, Thần Thương Binh, Long Kỵ Binh, Kiếm Thánh...). Bảng phải đầy đủ các cột: ID, Tên Binh chủng Tier 3, Điều kiện tiến hóa từ Tier 2, Máu, Tốc độ, Chỉ số Kháng phép, Sát thương đặc biệt, Kỹ năng/Thuộc tính kích hoạt ẩn, và Relational Schema mapping sang Knowledge Graph.

**Bài tập:**
- Trích xuất các chỉ số ẩn, Kháng phép, Sát thương đặc biệt của tất cả các binh chủng Tier 3 từ file game data.
- Phân tích logic và điều kiện tiến hóa từ Tier 2 lên Tier 3 cùng danh sách chiêu thức kích hoạt ẩn.
- Chuẩn hóa dữ liệu toàn bộ Tier 3 sang JSON/Relational Schema để nạp trực tiếp vào Knowledge Graph.

**Tags:**
#binh_chung_tier_3 #tinh_anh #than_binh #knowledge_graph_schema #thuoc_tinh_an

---

## Day 57 — Bóc tách & Chuẩn hóa Binh chủng Đặc biệt: Dị Tộc, Nữ Binh & Tượng Binh
**Prompt:**
Yêu cầu xuất dữ liệu Bách khoa toàn thư dưới dạng BẢNG MARKDOWN NGHIÊM NGẶT (tuyệt đối không dùng văn xuôi, không lời dẫn hay văn phong giáo viên, không tạo heading ## Day). Hãy thực hiện trích xuất và kiểm tra ma trận tương khắc, kỹ năng dị tộc, nữ binh, tượng binh, và xử lý dữ liệu khác biệt giữa các phiên bản Vanilla và Mod cho các thực thể cụ thể: Nữ Binh, Vũ Sĩ, Man Binh, Tượng Binh, Trùy Binh. Bảng dữ liệu phải chứa đầy đủ các chỉ số: Máu, Tốc di chuyển, Tấn công đặc biệt, Ma trận tương khắc riêng biệt với binh chủng thông thường, Kỹ năng đặc biệt, cùng đánh dấu rõ điểm khác biệt chỉ số giữa bản Mod và Vanilla để hoàn thành bảng Binh chủng đặc biệt không sót thực thể.

**Bài tập:**
- Trích xuất thông số Máu, Tốc di chuyển, Tấn công đặc biệt của Nữ Binh, Vũ Sĩ, Man Binh, Tượng Binh, Trùy Binh thành bảng Markdown.
- Lập ma trận tương khắc chi tiết giữa Dị Tộc, Tượng Binh với các binh chủng thông thường.
- Viết script Python kiểm tra và đánh dấu điểm khác biệt chỉ số giữa bản Vanilla và Mod.

**Tags:**
#ditooc #nubinh #tuongbinh #khacche #datanormalization

---

## Day 58 — Bóc tách Cơ Giới Công Thành & Sinh Vật Thần Thoại Triệu Hoán
**Prompt:**
Yêu cầu xuất dữ liệu Bách khoa toàn thư dưới dạng BẢNG MARKDOWN NGHIÊM NGẶT (tuyệt đối không dùng văn xuôi, không lời dẫn hay ngữ điệu giảng dạy, không viết heading ## Day). Hãy bóc tách toàn bộ chỉ số Cơ giới công thành và Thần thú triệu hoán, đóng gói dữ liệu binh chủng thành Data Pipeline hoàn chỉnh. Danh sách thực thể cần trích xuất gồm: Xung Xa, Đầu Thạch Xa, Mộc Nhân, Thiết Nhân, Hoàng Long, Bạch Hổ, Chu Tước, Huyền Vũ, Kỳ Lân. Bảng kết quả phải trình bày chính xác các cột: Máu, Sát thương công thành/diện rộng, Thuộc tính thần thú, Điều kiện triệu hoán, và Kết quả chạy thành công script Data Validation (Integrity Check) cho toàn bộ Phase Binh chủng.

**Bài tập:**
- Tạo bảng Markdown trích xuất chỉ số Máu, Sát thương công thành/diện rộng của Xung Xa, Đầu Thạch Xa, Mộc Nhân, Thiết Nhân.
- Trích xuất thuộc tính và điều kiện triệu hoán của 5 Thần thú: Hoàng Long, Bạch Hổ, Chu Tước, Huyền Vũ, Kỳ Lân.
- Xây dựng Data Pipeline script thực hiện Integrity Check cho toàn bộ dữ liệu binh chủng và xuất JSON/Markdown.

**Tags:**
#cogioi #congthanh #quaivat #trieuhoan #datapipeline #integritycheck

---

## Day 59 — Bóc Tách & Chuẩn Hóa Vũ Khí Kiếm & Đao Cấp Cao
**Prompt:**
Yêu cầu xuất Bách khoa toàn thư dưới dạng BẢNG MARKDOWN NGHIÊM NGẶT (không văn xuôi, không lời dẫn dắt, không tạo heading ## Day). Thực hiện trích xuất 14 Kiếm & Đao cấp cao từ file cấu hình game (.INI/.PAK), chuyển đổi 100% văn bản tiếng Trung từ bảng mã Big5/GBK sang UTF-8 không lỗi font và kiểm định cấu trúc qua Pydantic Schema. Bảng Markdown phải thống kê đầy đủ 14 vũ khí Kiếm & Đao cấp cao với các cột: Tên vũ khí (UTF-8), Chỉ số Võ, Chỉ số Trí, Thuộc tính, Năng lực ẩn, Mã hóa gốc (Big5/GBK) và Trạng thái kiểm định JSON Schema.

**Bài tập:**
- Trích xuất 14 Kiếm & Đao cấp cao từ file game và lập bảng chỉ số Võ, Trí, thuộc tính.
- Viết kịch bản Python (Pandas, ftfy) chuyển đổi bảng mã Big5/GBK sang UTF-8 cho tên và mô tả vũ khí.
- Định nghĩa Pydantic Schema và thực hiện validate dữ liệu JSON xuất ra.

**Tags:**
#vukhi #kiemdao #big5toutf8 #jsonschema #datavalidation

---

## Day 60 — Bóc Tách & Validation Thương & Kích Thần Binh
**Prompt:**
Yêu cầu xuất dữ liệu Bách khoa toàn thư dưới dạng BẢNG MARKDOWN NGHIÊM NGẶT (tuyệt đối không văn xuôi, không lời dẫn dắt hay giọng giáo viên, không tạo heading ## Day). Thực hiện bóc tách 14 Thương & Kích Thần Binh và kiểm thử kịch bản Automated Data Validation. Bảng Markdown bắt buộc hiển thị danh sách 14 Thương & Kích Thần Binh cùng các thông tin: Chỉ số Võ, Chỉ số Trí, Yêu cầu cấp độ trang bị, ID Kỹ năng đính kèm, Trạng thái kiểm tra toàn vẹn tham chiếu Foreign Key (với ID Võ tướng kỹ), và Báo cáo làm sạch dữ liệu rác/null trong thuộc tính ẩn.

**Bài tập:**
- Trích xuất dữ liệu 14 Thương & Kích Thần Binh gồm chỉ số Võ, Trí, Cấp độ yêu cầu và Kỹ năng đính kèm.
- Lập kịch bản Automated Data Validation bằng Python kiểm tra Foreign Key giữa ID vũ khí và ID kỹ năng.
- Xử lý làm sạch các thuộc tính ẩn bị null hoặc trùng lặp trong dữ liệu thương kích.

**Tags:**
#thuongkich #thanbinh #foreignkey #dataintegrity #datacleaning

---

## Day 61 — Bóc Tách Cung, Quạt, Trùy & Phủ Cấp Cao
**Prompt:**
Yêu cầu xuất dữ liệu Bách khoa toàn thư dưới dạng BẢNG MARKDOWN NGHIÊM NGẶT (tuyệt đối không văn xuôi, không dùng phong cách giảng dạy, không viết heading ## Day). Hãy trích xuất 14 Cung, Quạt, Trùy & Phủ cấp cao từ file cấu hình trang bị game Sango Heroes 7 và phân tích các tham số chưa từng công khai. Bảng dữ liệu Markdown cần tổng hợp đầy đủ 14 trang bị thuộc nhóm Cung, Quạt, Trùy & Phủ với các thông số: Chỉ số Võ, Chỉ số Trí, Tầm đánh (Attack Range), Tỷ lệ bạo kích ẩn, Hiệu ứng kỹ năng đính kèm và Mã ID ẩn (undocumented attributes) đã bóc tách từ Parser tự động.

**Bài tập:**
- Trích xuất chỉ số Võ, Trí, Tầm đánh và Năng lực ẩn của 14 Cung, Quạt, Trùy & Phủ cấp cao.
- Viết Parser tự động bóc tách hiệu ứng kỹ năng đính kèm và tỷ lệ bạo kích ẩn của trang bị.
- Mã hóa và chuẩn hóa các trường thuộc tính ẩn (undocumented attributes) vào JSON schema thống nhất.

**Tags:**
#cungquat #truyphu #attackrange #hiddenattributes #parser

---

## Day 62 — Bóc Tách & Relational Mapping Giáp Mão & Bào Kháp
**Prompt:**
Yêu cầu xuất dữ liệu Bách khoa toàn thư dưới dạng BẢNG MARKDOWN NGHIÊM NGẶT (không văn xuôi, không lời dẫn hay nhận xét, không tạo heading ## Day). Thực hiện trích xuất 14 Áo giáp & Mũ bào cao cấp từ file Armor/Helmet của Sango Heroes 7 và thiết kế ánh xạ quan hệ (Relational Mapping). Bảng dữ liệu Markdown phải liệt kê đủ 14 trang bị Giáp Mão & Bào Kháp kèm các thông tin: Chỉ số Võ, Chỉ số Trí, Chỉ số Phòng thủ, Tỷ lệ Né tránh, Điều kiện loại tướng/binh chủng sử dụng (Võ tướng/Quân sư) và Giá trị phòng thủ mặc định được gán cho các ô khuyết.

**Bài tập:**
- Trích xuất chỉ số Võ, Trí, Phòng thủ, Né tránh của 14 Áo giáp & Mũ bào cao cấp.
- Thiết kế bảng Relational Mapping thể hiện mối quan hệ giữa trang bị phòng thủ và phân loại tướng (Võ tướng/Quân sư).
- Xử lý chuẩn hóa dữ liệu bị khuyết và gán giá trị mặc định cho thuộc tính phòng thủ.

**Tags:**
#aogiap #mubao #phongthu #relationalmapping #schemadesign

---

## Day 63 — Bóc Tách Chiến Mã Thần Thoại & Bảo Vật Kịch Bản
**Prompt:**
Yêu cầu xuất Bách khoa toàn thư dưới dạng BẢNG MARKDOWN NGHIÊM NGẶT (tuyệt đối không dùng văn xuôi, không nhận xét hay dùng ngữ điệu giáo viên, không tạo heading ## Day). Trích xuất 14 Chiến mã & Bảo vật kịch bản, sau đó khử trùng lặp (Deduplication) và đóng gói toàn bộ Phase Trang bị (từ Day 59 đến Day 62). Bảng Markdown phải thể hiện danh sách 14 Chiến mã thần thoại & Bảo vật kịch bản với các thông số: Chỉ số Võ, Chỉ số Trí, Tốc độ di chuyển, Kỹ năng đặc biệt, Trạng thái chuẩn hóa quan hệ (1NF/2NF/3NF) và Kết quả nạp vào CSDL SQLite/JSON Knowledge Map.

**Bài tập:**
- Trích xuất chỉ số Võ, Trí, Tốc độ di chuyển và Kỹ năng đặc biệt của 14 Chiến mã & Bảo vật thần thoại.
- Thực hiện thuật toán khử trùng lặp (Deduplication) và chuẩn hóa dữ liệu Phase Trang bị đạt chuẩn 3NF.
- Nạp toàn bộ dữ liệu trang bị từ Day 59-63 vào Cơ sở dữ liệu SQLite và đóng gói Knowledge Map.

**Tags:**
#chienma #baovat #deduplication #sqlite #knowledgemap

---

## Day 64 — Bóc Tách Kiếm Đạo Thần Binh & Đoản Nhẫn Cấp Cuối
**Prompt:**
Yêu cầu xuất dữ liệu Bách khoa toàn thư dưới dạng BẢNG MARKDOWN NGHIÊM NGẶT (tuyệt đối không văn xuôi, không lời dẫn dắt hay phong cách giảng dạy, không tạo heading ## Day). Thực hiện bóc tách và chuyển đổi mã font Big5 sang UTF-8 cho các thực thể cụ thể: Hoàng Thiên Kiếm, Cửu Thiên Tuyền Cơ Kiếm, Ngược Thiên Kiếm, Thiên Thần Sát Đao, Chu Tước Đao, Viêm Nhai Đao, Ma Lăng Đao, Phượng Hoàng Kiếm, Bá Vương Đao, Lục Tiên Kiếm, Hư Không Kiếm, Thái Cực Kiếm, U Minh Đao, Long Mộc Đao, Thất Tinh Đao. Bảng dữ liệu Markdown phải liệt kê chính xác từng thực thể trên cùng các chỉ số: Võ, Trí, Năng lực ẩn, Tỷ lệ kích hoạt skill, ID đính kèm trong Item.ini và Kết quả kiểm thử Data Integrity Check trên Schema JSON.

**Bài tập:**
- Trích xuất chỉ số Võ, Trí và giải mã tên/mô tả từ Big5 sang UTF-8 cho 15 Thần binh (Hoàng Thiên Kiếm, Bá Vương Đao, Thất Tinh Đao...).
- Phân tích năng lực ẩn, tỷ lệ kích hoạt skill và ánh xạ ID của các vũ khí cấp cuối vào Schema JSON.
- Chạy kịch bản Data Integrity Check để validate toàn bộ chỉ số của 15 vũ khí huyền thoại.

**Tags:**
#kiemdao #thanbinh #sango7 #chisovukhi #Big5encoding #dataintegrity

---

## Day 65 — Bóc Tách Trường Binh Thần Thoại & Long Kích Bá Vương
**Prompt:**
Yêu cầu trích xuất dữ liệu chi tiết cho 15 thực thể trường binh thần thoại: Phương Thiên Họa Kích, Thanh Long Yển Nguyệt Đao, Trượng Bát Xà Thương, Bằng Tiêu Thương, Hoạt Long Thương, Tây Lương Sát Thương, Thần Sát Kích, Hàn Băng Xà Mộc Thương, Hổ Điêu Kích, Phá Quân Thương, Tử Điện Thương, Ngũ Lôi Kích, Bá Vương Nhược Thương, Cuồng Long Trượng, Cương Ma Kích từ file gốc Item.ini của Sango 7 bằng thư viện Python Pandas.

Tiêu chuẩn hoàn thành (Definition of Done):
1. Trình bày thông tin đúng bảng Markdown và cấu trúc JSON chuẩn hóa.
2. Tự động hóa kiểm tra Foreign Key liên kết giữa ID vũ khí và ID kỹ năng đính kèm.

Yêu cầu định dạng đầu ra: Trả về BẢNG MARKDOWN nghiêm ngặt gồm các cột (ID Vũ Khí, Tên Vũ Khí, Chỉ Số Võ/Trí, Tầm Đánh, ID Skill Đính Kèm, Trạng Thái Foreign Key Integrity). TUYỆT ĐỐI KHÔNG dùng văn xuôi hay diễn giải dài dòng, KHÔNG viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Viết script Python Pandas để bóc tách chỉ số Võ, Trí và Tầm đánh của 15 loại trường binh từ Item.ini.
- Xây dựng hàm kiểm thử tự động Foreign Key Integrity nhằm đảm bảo mọi ID kỹ năng gắn trên Phương Thiên Họa Kích, Thanh Long Yển Nguyệt Đao, Trượng Bát Xà Thương đều tồn tại trong danh mục Skill.

**Tags:**
#truong_binh #than_kich #xa_thuong #yen_nguyet_dao #foreign_key_integrity #schema_validation

---

## Day 66 — Bóc Tách Cung Quạt Bá Vương & Kỳ Môn Bảo Khí
**Prompt:**
Yêu cầu bóc tách và phân tích dữ liệu cho các thực thể Cung, Quạt, Trùy: Vạn Thiết Thần Cung, Bàn Long Trùy, Huyền Vũ Quạt, Tiên Nhân Phi Thư Quạt, Thái Cực Phi Tiên Quạt, Hỏa Thần Cung, Phá Thiên Báo Cung, Quỷ Lang Trùy, Ngũ Hành Tiên Quạt, U Mộc Quạt, Lôi Vương Trùy, Thiên Vũ Cung, Phá Ma Nỏ, Ngũ Sắc Quạt, Tụ Lôi Trùy.

Tiêu chuẩn hoàn thành (Definition of Done):
1. Xuất dữ liệu chuẩn JSON/Markdown đầy đủ các thực thể Cung/Quạt/Trùy.
2. Khử trùng lặp (Deduplication) và chuẩn hóa dữ liệu đạn đạo, triệu hồi.

Yêu cầu định dạng đầu ra: Trình bày kết quả dưới dạng BẢNG MARKDOWN duy nhất với các cột (Mã Vũ Khí, Tên Vũ Khí, Loại, Cộng Điểm Võ/Trí, Khai Báo Đạn Đạo/Triệu Hồi, Tỷ Lệ Choáng, Trạng Thái Deduplication). KHÔNG giải thích dông dài, KHÔNG viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Lập trình Python Data Pipeline giải mã thông số đạn đạo và hiệu ứng triệu hồi cho Vạn Thiết Thần Cung và Huyền Vũ Quạt.
- Thực hiện thuật toán khử trùng lặp (Deduplication) dữ liệu đạn đạo trên toàn bộ danh mục vũ khí Cung/Quạt/Trùy.

**Tags:**
#cung_no #quat_tien #ky_mon_truy #chi_so_vu_khi #deduplication #data_pipeline

---

## Day 67 — Bóc Tách Phòng Cụ Thần Giáp & Hoàng Kim Kháp Bào
**Prompt:**
Yêu cầu bóc tách chỉ số phòng ngự từ Armor.ini cho 15 phòng cụ: Long Lân Long Nguyệt Kháp, Hoàng Kim Thánh Giáp, Chu Tước Thần Bào, Huyền Vũ Thần Bào, Bạch Hổ Giáp, Man Vu Y, Thiên La Thần Bào, Ngô Vu Bào, Linh Sĩ Áo Khoác, Vĩnh Hằng Chi Mão, Cuồng Ma Bào, Bát Quái Ngũ Hành Giáp, Thái Cực Thần Bào, Xích Long Kháp, Tử Vân Y.

Tiêu chuẩn hoàn thành (Definition of Done):
1. Bảng dữ liệu Markdown/JSON hoàn chỉnh cho toàn bộ giáp và áo bào.
2. Xác minh tính toàn vẹn của chỉ số kháng phép, phòng thủ và cấp độ yêu cầu.

Yêu cầu định dạng đầu ra: Xuất BẢNG MARKDOWN chuẩn gồm các cột (ID Giáp, Tên Trang Bị, Điểm Phòng Thủ, Kháng Ma Pháp, Yêu Cầu Cấp Độ/Chức Danh, Phụ Trợ Ẩn, Kết Quả Validation). TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, KHÔNG viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Trích xuất chỉ số phòng thủ và kháng phép của Hoàng Kim Thánh Giáp, Chu Tước Thần Bào từ file Armor.ini bằng Python.
- Sử dụng JSON Schema Validator Tool để kiểm tra tính toàn vẹn Schema về điều kiện cấp độ mặc giáp.

**Tags:**
#than_giap #hoang_kim_khap #bao_khap #trang_bi_phong_ngu #json_schema #data_verification

---

## Day 68 — Bóc Tách Tọa Kỵ Danh Mã & Bảo Vật Độc Quyền
**Prompt:**
Yêu cầu bóc tách và xây dựng Relational Mapping cho 15 thực thể chiến mã và bảo vật: Xích Thố, Đích Lô, Tuyệt Ảnh, Trảo Hoàng Phi Điện, Long Mã, Kỳ Lân, Tử Sương Ngựa, Hoàng Kim Mã, Ngoạn Hổ, Bát Quái Kính, Mộc Ngưu Lưu Mã, Ngọc Tỷ Trấn Quốc, Truy Tinh Phù, Tôn Tử Binh Pháp, Thái Ất Mộc Mã.

Tiêu chuẩn hoàn thành (Definition of Done):
1. Hoàn thiện dữ liệu chiến mã và bảo vật dạng JSON/Markdown.
2. Xây dựng xong Relational Mapping giữa Tọa kỵ/Bảo vật với Tướng sở hữu vào Knowledge Graph.

Yêu cầu định dạng đầu ra: Trình bày dữ liệu dạng BẢNG MARKDOWN nghiêm ngặt gồm (Mã Bảo Vật/Ngựa, Tên Thực Thể, Loại, Tốc Độ/Chỉ Số Cộng, Kỹ Năng Chiến Trường Ẩn, ID Tướng Sở Hữu, Trạng Thái Mapping). KHÔNG dùng văn phong giảng dạy, KHÔNG viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Giải mã thuộc tính né tránh và tốc độ di chuyển của Xích Thố, Đích Lô, Tuyệt Ảnh từ Horse.ini.
- Thiết lập Relational Mapping liên kết Ngọc Tỷ Trấn Quốc và Tôn Tử Binh Pháp với danh tướng tương ứng trong Knowledge Graph.

**Tags:**
#toa_ky #danh_ma #bao_vat #ngoc_ty #knowledge_graph #relational_mapping

---

## Day 69 — Trích Xuất & Chuẩn Hóa Binh Khí Phụ Bản, Ngoại Truyện
**Prompt:**
Yêu cầu trích xuất, chuyển đổi mã hóa font và kiểm tra tính toàn vẹn Schema cho 15 binh khí phụ bản: Thần Sát Yển Nguyệt Đao, Hoàng Thần Lục Kiếm, Tử Thiết Thương, Quỷ Nhẫn Phủ, Ngũ Hành Tiên Quạt, Địa Sát Cung, Bàn Long Kích, Ngũ Hoàn Trùy, Nhật Nguyệt Đao, Xích Tiêu Thương, Thái Cực Kiếm, U Nhẫn Đoản Đao, Hàn Băng Thương, Phong Hoả Trùy, Bạch Ngân Kích.

Tiêu chuẩn hoàn thành (Definition of Done):
1. Xuất bảng dữ liệu đầy đủ 15 binh khí phụ bản theo định dạng JSON Schema chuẩn.
2. 100% dữ liệu tên và mô tả không bị lỗi font mã hóa.

Yêu cầu định dạng đầu ra: Đưa ra BẢNG MARKDOWN duy nhất có các cột (Mã Binh Khí, Tên Gốc, Tên UTF-8, Chỉ Số Võ/Trí, Cấp Độ Yêu Cầu, Lực Chiêu Thức, Schema Check Status). TUYỆT ĐỐI KHÔNG chứa văn xuôi hay lời dẫn, KHÔNG viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Viết script Python giải mã bảng mã Big5/GBK sang UTF-8 cho tên 15 binh khí phụ bản.
- Chạy JSON Schema Validator để kiểm thử tính toàn vẹn dữ liệu cho Thần Sát Yển Nguyệt Đao và Hoàng Thần Lục Kiếm.

**Tags:**
#trang_bi_phu #vu_khi_trung_cap #chuyen_doi_encoding #json_schema_validation

---

## Day 70 — Trích Xuất & Mô Hình Hóa Thần Dược, Binh Pháp & Tráp Bảo
**Prompt:**
Yêu cầu trích xuất dữ liệu và xây dựng mô hình quan hệ thực thể (Relational Mapping) trong Knowledge Graph cho 15 bảo vật: Mạnh Đức Binh Pháp, Tôn Tử Binh Pháp, Thất Tinh Bát Quái Đồ, Binh Pháp 24 Thiên, Thái Ất Mộc Phù, Kỳ Môn Độn Giáp, Cửu Chuyển Hoàn Thuốc, Cửu Long Bảo Tráp, Ngọc Tỷ Truyền Quốc, Thái Thượng Thần Đạn, Tây Dực Tuyết Liên, Linh Sơn Tiên Dược, Lôi Đình Ngọc Phù, Chu Tước Thần Châu, Huyền Vũ Linh Phù.

Tiêu chuẩn hoàn thành (Definition of Done):
1. Bảng dữ liệu JSON/Markdown hoàn chỉnh cho 15 bảo vật đặc biệt.
2. Xác định rõ mô hình ánh xạ mối quan hệ giữa Bảo vật và chỉ số Tướng/Quân sự.

Yêu cầu định dạng đầu ra: Xuất BẢNG MARKDOWN nghiêm ngặt gồm (Mã Pháp Bảo, Tên Pháp Bảo, Phân Loại Hiệu Ứng, Chỉ Số Cộng, Tỷ Lệ Kích Hoạt, Mô Hình Quan Hệ Entity). KHÔNG dùng văn phong lý thuyết hay diễn giải, KHÔNG viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Sử dụng thư viện Pydantic/Pandas trích xuất chỉ số cộng Võ/Trí và tỷ lệ kích hoạt của Cửu Chuyển Hoàn Thuốc và Ngọc Tỷ Truyền Quốc.
- Xây dựng sơ đồ Relational Mapping biểu diễn hiệu ứng buff diện rộng của Mạnh Đức Binh Pháp trong Graph Database.

**Tags:**
#binh_phap_than_duoc #phap_bao #relational_mapping #etl_pipeline

---

## Day 71 — Trích Xuất & Làm Sạch Dữ Liệu Giáp Mão, Bào Kháp
**Prompt:**
Yêu cầu bóc tách, xử lý dữ liệu khuyết thiếu/null và chuẩn hóa thuộc tính cho 15 phòng cụ: Bạch Ngân Giáp, Mạn Đột Uyển Giáp, Khổng Tước Bào, Tử Vân Kháp, Man Vương Thú Giáp, Kinh Mã Thắt Lưng, Hổ Đầu Bào Kháp, Huyền Thiết Khôi, Long Lân Mão, Phượng Cánh Mão, Ưng Nhãn Hộ Mộc, Thú Diện Tụ Giáp, Phán Quan Khôi, Nhã Lân Giáp, Xích Long Bào.

Tiêu chuẩn hoàn thành (Definition of Done):
1. Bảng dữ liệu chuẩn 15 phòng cụ giáp mũ không chứa giá trị null/rác.
2. Đạt kiểm thử tự động về định dạng kiểu dữ liệu (Data Type Checks).

Yêu cầu định dạng đầu ra: Trình bày BẢNG MARKDOWN duy nhất gồm các cột (Mã Phòng Cụ, Tên Giáp Mão, Phòng Thủ, Kháng Sát Thương, Điểm Võ/Trí, Kiểm Tra Null, Data Type Status). TUYỆT ĐỐI KHÔNG viết văn xuôi hay văn phong giáo viên, KHÔNG viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Viết script Python Data Cleaning để phát hiện và xử lý giá trị null trong các file Armor/Item .INI.
- Thực hiện Automated Data Type Checks cho 15 phòng cụ giáp mũ nhằm xác nhận tính hợp lệ trước khi mapping vào Knowledge Map.

**Tags:**
#phong_cu_giap_mao #bao_khap #data_cleaning #automated_validation

---

## Day 72 — Trích Xuất & Xây Dựng Graph Schema Tọa Kỵ, Dị Thú
**Prompt:**
Yêu cầu trích xuất dữ liệu và mô hình hóa liên kết đồ thị Tướng - Tọa kỵ cho 15 dị thú/danh mã: Xích Thỏ Mã, Đích Lô, Tuyệt Ảnh, Trảo Hoàng Phi Điện, Tử Điện Phù Vân, Thiết Sĩ Mã, Hỏa Long Thú, Bạch Ngốc Mã, Man Nhượng Ngưu, Hổ Báo Thú, Kim Mão Tuyết Mã, Bát Câu Danh Mã, Bạch Tượng, Kỳ Lân Thú, Hắc Tinh Ngựa.

Tiêu chuẩn hoàn thành (Definition of Done):
1. Bảng dữ liệu 15 tọa kỵ kèm chỉ số tốc độ di chuyển và buff ẩn.
2. Mô hình hóa thành công liên kết đồ thị giữa Tọa kỵ và Võ tướng đặc định.

Yêu cầu định dạng đầu ra: Xuất BẢNG MARKDOWN chuẩn hóa gồm các cột (ID Tọa Kỵ, Tên Chiến Mã/Dị Thú, Tốc Độ Di Chuyển, Skill/Buff Ẩn, Cấp Độ Yêu Cầu, Node Tướng Liên Kết, Graph Schema Status). KHÔNG dùng văn xuôi, KHÔNG viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Trích xuất tốc độ di chuyển, chỉ số Võ/Trí và kỹ năng ẩn của Xích Thỏ Mã, Đích Lô và Kỳ Lân Thú từ Horse.ini.
- Sử dụng NetworkX/Neo4j format để tạo Graph Schema thiết lập liên kết quan hệ giữa Tọa kỵ và Võ tướng sở hữu.

**Tags:**
#toa_ky_chien_ma #di_thu #graph_schema #knowledge_graph_mapping

---

## Day 73 — Trích Xuất & Đóng Gói CSDL Thần Binh Cực Hạn Cuối Game
**Prompt:**
Hãy tạo một bảng Bách khoa toàn thư kỹ thuật bóc tách dữ liệu cho 15 thần binh cuối game: Hiên Viên Kiếm, Cửu Thiên Huyền Nữ Kiếm, Hoàn Mỹ Nguyện Cung, Thần Thiết Phủ, Vô Nhai Quạt, Bá Vương Kim Kích, Hoàng Long Đao, Hỏa Tiêm Thương, Diệt Thế Trùy, Thái Cực Luyện Thần Kiếm, Tử Quang Đoản Nhẫn, Thiên Sát Thần Thương, Long Thần Tuyệt Phủ, Ngô Câu Bảo Đao, Tru Tiên Trận Cung. Yêu cầu chi tiết về: Chỉ số Võ/Trí cực hạn, tỷ lệ hút máu/chém hất, chiêu thức kích hoạt ẩn, và quy trình kiểm tra ràng buộc khóa ngoại (Foreign Key Integrity) để đóng gói thành file SQLite/JSON nhất quán. Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên. Không được thay thế bằng lý thuyết tổng quát. Không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Xây dựng script kiểm tra Foreign Key Integrity giữa ID 15 thần binh với bảng Skill ID và Hero ID.
- Thực hiện đóng gói toàn bộ bảng dữ liệu thần binh thành file CSDL SQLite và file JSON hoàn chỉnh.

**Tags:**
#than_binh_cuoi_game #vu_khi_cuc_han #foreign_key_integrity #database_packaging

---

## Day 74 — Trích Xuất & Chuẩn Hóa Đoản Binh Kiếm Đao Trung Cấp & Danh Môn
**Prompt:**
Hãy tạo bảng Bách khoa toàn thư hướng dẫn trích xuất và chuẩn hóa dữ liệu cho 12 đoản binh bao gồm Thanh Long Kiếm, Thất Tinh Kiếm và các kiếm đao danh môn. Yêu cầu mô tả các bước xử lý chuyển đổi bảng mã Big5/GBK sang UTF-8, làm sạch ký tự rác, trích xuất thuộc tính Võ, Trí, cấp độ yêu cầu, kỹ năng ẩn và map vào Knowledge Graph Schema. Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên. Không được thay thế bằng lý thuyết tổng quát. Không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Viết script Python giải mã file config Big5/GBK của đoản binh và xuất ra chuỗi UTF-8 chuẩn.
- Thiết lập cấu hình Knowledge Graph Schema mapping thuộc tính của Thanh Long Kiếm và Thất Tinh Kiếm.

**Tags:**
#doan_binh #kiemi_dao #chuyen_doi_bang_ma #sango_heroes_7 #data_cleaning

---

## Day 75 — Trích Xuất & Kiểm Thử Dữ Liệu Trường Binh Thương Kích & Đao Trụ
**Prompt:**
Hãy lập bảng Bách khoa toàn thư kỹ thuật trích xuất dữ liệu trường binh thương kích và đao trụ bao gồm Xà Mao, Phượng Tường Kích và 10 vũ khí cùng loại. Yêu cầu chi tiết các trường chỉ số Võ/Trí, điều kiện trang bị, kỹ năng ẩn, và phương pháp kiểm thử tính toàn vẹn tham chiếu khóa ngoại (Foreign Key Integrity) tới danh mục Skill Master Data. Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên. Không được thay thế bằng lý thuyết tổng quát. Không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Chạy script Data Validation Python để kiểm tra 100% Weapon Skill ID của Xà Mao và Phượng Tường Kích khớp với Skill Master Data.
- Chuyển đổi dữ liệu 12 trường binh đã xác minh thành định dạng JSON pipeline.

**Tags:**
#truong_binh #thuong_kich #foreign_key_integrity #ky_nang_an #sango_heroes_7

---

## Day 76 — Trích Xuất & Đối Chiếu Quạt Pháp Bảo & Binh Khí Mưu Sĩ
**Prompt:**
Hãy xây dựng bảng Bách khoa toàn thư đối chiếu chỉ số dữ liệu cho 12 quạt pháp bảo binh khí mưu sĩ bao gồm Ngũ Hành Phiến, Lôi Thần Phiến và các pháp bảo tương đương. Yêu cầu thể hiện bảng so sánh chỉ số Trí/Võ, cấp độ, hiệu ứng kích hoạt phép thuật giữa bản gốc Vanilla v1.22 và bản Mod mở rộng (Mod Remake). Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên. Không được thay thế bằng lý thuyết tổng quát. Không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Sử dụng công cụ Python Diff Data để phát hiện sự khác biệt chỉ số quạt pháp bảo giữa 2 bản config.
- Ghi nhận các thuộc tính kích hoạt phép thuật của Ngũ Hành Phiến và Lôi Thần Phiến vào Schema dữ liệu.

**Tags:**
#quat_phap_bao #muu_si #chi_so_tri #mod_vs_vanilla #sango_heroes_7

---

## Day 77 — Trích Xuất & Khử Trùng Lặp Trang Sức Phù Hiệu & Bảo Thạch
**Prompt:**
Hãy tạo bảng Bách khoa toàn thư về quy trình trích xuất và xử lý dữ liệu trang sức, phù hiệu bảo thạch bao gồm Long Lân Phù, Bạch Hổ Phù và 10 phụ kiện liên quan. Yêu cầu mô tả thuật toán khử trùng lặp dữ liệu (Deduplication), phương pháp xử lý các trường dữ liệu bị Null/rác, và cách nạp dữ liệu chuẩn hóa vào Knowledge Graph. Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên. Không được thay thế bằng lý thuyết tổng quát. Không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Viết script Pandas/Pydantic loại bỏ các bản ghi trùng lặp và làm sạch trường Null trong file config trang sức.
- Map hiệu ứng buff passive/active của Long Lân Phù và Bạch Hổ Phù vào CSDL Knowledge Graph.

**Tags:**
#trang_suc #bao_thach #phu_hieu #deduplication #data_cleaning

---

## Day 78 — Trích Xuất & Tích Hợp Tọa Kỵ Chiến Mã Dị Thú Vào API Schema
**Prompt:**
Hãy lập bảng Bách khoa toàn thư trích xuất chỉ số chiến mã, tọa kỵ dị thú bao gồm Xích Huyết Mã, Ô Vân Đạp Tuyết và 10 danh mã khác. Yêu cầu chi tiết các chỉ số tốc độ di chuyển, Võ/Trí cộng thêm, kỹ năng ẩn, cùng quy trình kiểm tra Automated Validation và đóng gói toàn bộ Data Phase Trang Bị thành JSON Schema phục vụ REST API. Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên. Không được thay thế bằng lý thuyết tổng quát. Không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Trích xuất trọn vẹn chỉ số và skill ẩn của Xích Huyết Mã và Ô Vân Đạp Tuyết.
- Đóng gói và validate toàn bộ JSON Schema của Phase Vũ Khí, Bảo Vật và Tọa Kỵ bằng công cụ JSON Schema Validator.

**Tags:**
#chien_ma #toa_ky #di_thu #data_validation #json_schema #sango_heroes_7

---

## Day 79 — Bóc Tách & Chuẩn Hóa Binh Khí Trùy Phủ & Nguyệt Nhận Cấp Tinh Anh
**Prompt:**
Hãy lập bảng Bách khoa toàn thư bóc tách dữ liệu 12 binh khí Trùy Phủ - Nguyệt Nhận cấp tinh anh: Cuồng Ngục Phủ, Khai Thiên Phủ, Truy Thần Trùy, Kim Cương Trùy, Nguyệt Nha Đao, Tam Gian Lưỡng Nhận Đao, Phá Sơn Phủ, Phá Không Trùy, Nhạc Nha Song Đao, Cửu Khúc Kiếm, Thiên Ma Trùy, Ngũ Độc Nha. Yêu cầu chi tiết về chỉ số Võ, Trí, tốc độ đánh, thuộc tính ẩn, quy trình chuyển đổi bảng mã Big5/GBK sang UTF-8 và xác minh khóa ngoại Foreign Key. Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên. Không được thay thế bằng lý thuyết tổng quát. Không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Viết script chuyển đổi bảng mã Big5/GBK cho file config chứa 12 binh khí Trùy Phủ - Nguyệt Nhận sang UTF-8.
- Thực hiện validate tham chiếu khóa ngoại giữa ID 12 binh khí với hệ thống kỹ năng và xuất ra file JSON chuẩn.

**Tags:**
#truy_phu #nguyet_nhan #big5_utf8_conversion #data_integrity #sango_heroes_7

---

## Day 80 — Bóc Tách & Tích Hợp Schema Pháp Bảo Thuật Sĩ & Tráp Bảo Thuật
**Prompt:**
Hãy tạo bảng Bách khoa toàn thư kiểm định và tích hợp dữ liệu 12 Bảo vật & Pháp bảo Thuật sĩ: Thái Ất Chân Kinh, Độn Môn Kíp Giáp, Kinh Lô Thư, Binh Pháp Tôn Tử, Tam Lược, Ngô Tử Binh Pháp, Mộc Ngưu Lưu Mã, Ngọc Tỷ Truyền Quốc, Cửu Nhị Thủy Kính, Thanh Nang Thư, Mộc Độc Phù, Kỳ Môn Độn Giáp. Yêu cầu trình bày chi tiết chỉ số Võ, Trí, kháng thuộc tính, năng lực ẩn, phương pháp kiểm định dữ liệu bằng Pydantic Schema và Relational Mapping vào Knowledge Graph. Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên. Không được thay thế bằng lý thuyết tổng quát. Không viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Xây dựng Pydantic Schema để validate toàn bộ cấu trúc thuộc tính của 12 bảo vật thuật sĩ.
- Thiết lập Relational Mapping liên kết điều kiện trang bị của Ngọc Tỷ Truyền Quốc và Thái Ất Chân Kinh với bảng Tướng trong Knowledge Graph.

**Tags:**
#phap_bao_thuat_si #bao_vat_tang_chi_so #schema_validation #knowledge_graph_mapping #sango_heroes_7

---

## Day 81 — Trích Xuất Chỉ Số Tiên Nhân, Đạo Sĩ & Các Nhân Vật Ẩn Sĩ Đặc Biệt
**Prompt:**
Hãy lập bảng bách khoa toàn thư chi tiết trích xuất chỉ số, vị trí xuất hiện và điều kiện chiêu mộ các Tiên nhân & Ẩn sĩ đặc biệt trong Sango Heroes 7 bao gồm: Nam Hoa Lão Tiên, Tả Từ, Vu Cát, Quản Lộ, Tư Mã Huy, Huỳnh Thừa Ngạn, Hứa Tử Tương, Đạo Tháp Tiên Vực, Mộc Lộc Đại Vương, Kiều Huyền, Lô Thực, Ngô Quận Lão Nhân, Hoa Đà, Bàng Đức Công, Biển Thước. Yêu cầu xử lý chuẩn xác bảng mã Big5/GBK sang UTF-8 không bị lỗi font tên nhân vật, kiểm tra toàn vẹn tham chiếu vị trí xuất hiện và điều kiện chiêu mộ, xuất đúng dạng bảng Markdown chuẩn hóa. Trả về kết quả NGUYÊN BẢN BẰNG BẢNG MARKDOWN, TUYỆT ĐỐI KHÔNG DÙNG VĂN XUÔI VÀ KHÔNG DÙNG VĂN PHONG GIÁO VIÊN.

**Bài tập:**
- Viết script Python giải mã chuỗi Big5/GBK chứa tên các Tiên nhân (Nam Hoa Lão Tiên, Tả Từ, Vu Cát) sang UTF-8.
- Thiết kế JSON Schema để lưu trữ thông tin chỉ số Võ, Trí, vị trí xuất hiện và điều kiện chiêu mộ của 15 ẩn sĩ.
- Thực hiện kiểm tra tính toàn vẹn tham chiếu vị trí xuất hiện của các ẩn sĩ trong bản đồ Sango 7.

**Tags:**
#tien_nhan #an_si #big5_encoding #sango7_extraction #data_validation

---

## Day 82 — Bóc Tách Bí Kíp Kỹ Năng Cấp Cao & Thuật Pháp Tuyệt Học
**Prompt:**
Hãy lập bảng bách khoa toàn thư chi tiết bóc tách các Bí kíp kỹ năng cấp cao & thuật pháp tuyệt học bao gồm: Bí Kíp Xích Bích Phong Bạo, Bí Kíp Thần Ma Nguyện, Bí Kíp Hoàng Thiên Đương Lập, Bí Kíp Bát Quái Trận, Bí Kíp Cuồng Nguyệt Trảm, Bí Kíp Thái Ất Chân Nhân, Bí Kíp Long Cuồng Vũ, Bí Kíp Hỏa Phượng Liêu Nguyên, Bí Kíp Sấm Sét Oanh Kích, Bí Kíp Phù Thủy Triệu Hoán, Bí Kíp Thiên Nhai Băng Phong, Bí Kíp Thần Y Cứu Thế. Yêu cầu xác minh toàn vẹn tham chiếu Foreign Key giữa ID bí kíp và Skill ID học được, trích xuất yêu cầu cấp độ/thuộc tính, nguồn gốc rớt đồ và vị trí thương nhân bán, không bỏ sót bất kỳ thực thể nào. Trả về kết quả NGUYÊN BẢN BẰNG BẢNG MARKDOWN, TUYỆT ĐỐI KHÔNG DÙNG VĂN XUÔI VÀ KHÔNG DÙNG VĂN PHONG GIÁO VIÊN.

**Bài tập:**
- Viết truy vấn SQLite kiểm tra ràng buộc Foreign Key giữa danh sách Bí kíp và CSDL Skill ID gốc.
- Xây dựng pipeline trích xuất tỷ lệ rớt đồ và vị trí bán thương nhân của Bí Kíp Xích Bích Phong Bạo và Bí Kíp Bát Quái Trận.
- Tạo file JSON Schema định nghĩa thuộc tính điều kiện sử dụng (cấp độ, võ lực, trí lực) cho thuật pháp tuyệt học.

**Tags:**
#bi_kip #ky_nang #thuat_phap #foreign_key_check #sango7

---

## Day 83 — Trích Xuất Vật Phẩm Nâng Cấp Binh Chủng & Binh Phù Chuyển Chiêu
**Prompt:**
Hãy lập bảng bách khoa toàn thư chi tiết trích xuất thông tin các vật phẩm nâng cấp binh chủng và binh phù bao gồm: Hổ Báo Kỵ Binh Phù, Tượng Binh Phù, Long Kỵ Phù, Mộc Nhan Binh Phù, Thần Đao Binh Phù, Thiên Cung Binh Phù, Lôi Đình Thần Sách, Liên Nỗ Binh Phù, Hung Nô Kỵ Phù, Nữ Binh Phù, Ninja Binh Phù, Thần Binh Nâng Cấp Phù, Đao Kỵ Tiến Hóa Thạch. Yêu cầu đảm bảo liên kết chính xác 100% giữa ID binh phù và ID binh chủng chuyển đổi, loại bỏ dữ liệu trùng lặp hoặc ID rác không tồn tại trong game, định dạng bảng Markdown chuẩn hóa. Trả về kết quả NGUYÊN BẢN BẰNG BẢNG MARKDOWN, TUYỆT ĐỐI KHÔNG DÙNG VĂN XUÔI VÀ KHÔNG DÙNG VĂN PHONG GIÁO VIÊN.

**Bài tập:**
- Viết hàm Python thực hiện Relational Mapping giữa ID binh phù và ID binh chủng đích.
- Lập kịch bản làm sạch dữ liệu loại bỏ các ID binh phù rác hoặc trùng lặp trong file INI.
- Trích xuất vị trí rương báu và tỷ lệ đánh rớt quái cho Hổ Báo Kỵ Binh Phù và Tượng Binh Phù.

**Tags:**
#binh_phu #nang_cap_binh_chung #chuyen_chieu #relational_mapping #sango7

---

## Day 84 — Bóc Tách Dược Phẩm Cực Tiêu & Vật Phẩm Tăng Chỉ Số Vĩnh Viễn
**Prompt:**
Hãy lập bảng bách khoa toàn thư chi tiết bóc tách thông số các dược phẩm cực tiêu và vật phẩm tăng chỉ số vĩnh viễn bao gồm: Cửu Chuyển Hoàn Danh Đan, Võ Lực Xà Đan, Trí Lực Thánh Thảo, Thần Thú Huyết Đan, Cửu Long Hoàn, Tam Tiên Trường Sinh Đan, Tuyết Sâm Ngàn Năm, Linh Chi Vạn Năm, Hà Thủ Ô Cổ Cụ, Sinh Mệnh Thạch Đan, Thần Lực Hoàn, Khí Huyết Đan. Yêu cầu xác thực kiểu dữ liệu số nguyên cho các chỉ số gia tăng vĩnh viễn (Võ, Trí, Thể lực, Nội lực), kiểm tra đầy đủ thuộc tính tiêu thụ, công thức chế tạo hoặc địa điểm mua, không bỏ sót thực thể nào. Trả về kết quả NGUYÊN BẢN BẰNG BẢNG MARKDOWN, TUYỆT ĐỐI KHÔNG DÙNG VĂN XUÔI VÀ KHÔNG DÙNG VĂN PHONG GIÁO VIÊN.

**Bài tập:**
- Xây dựng Pydantic Model để kiểm tra Data Validation kiểu dữ liệu số nguyên cho các chỉ số gia tăng vĩnh viễn.
- Trích xuất công thức chế tạo và địa điểm mua của Cửu Chuyển Hoàn Danh Đan và Tam Tiên Trường Sinh Đan.
- Tạo bảng ánh xạ thuộc tính tiêu thụ và giới hạn sử dụng của từng loại dược phẩm.

**Tags:**
#duoc_pham #tang_chi_so #vinh_vien #pydantic_validation #sango7

---

## Day 85 — Trích Xuất Khoáng Thạch Nâng Cấp & Đá Ép Trang Bị Cực Hạn
**Prompt:**
Hãy lập bảng bách khoa toàn thư chi tiết trích xuất khoáng thạch nâng cấp và đá ép trang bị cực hạn bao gồm: Huyền Thiết Cường Hoá, Thần Thiết Cổ Tự, Long Lân Thạch, Tuyết Tụ Thạch, Linh Mộc Thạch, Thái Cực Bối Thạch, Ma Tinh Ngọc, Thiên Không Thạch, Bí Thiết Khoáng, Tử Sâm Thạch, Bách Luyện Thần Thiết, Hỏa Tinh Thạch. Yêu cầu hoàn tất pipeline làm sạch dữ liệu, kiểm tra ràng buộc công thức ghép đồ, tổng hợp đầy đủ thuộc tính cộng thêm và tỷ lệ thành công vào Knowledge Map. Trả về kết quả NGUYÊN BẢN BẰNG BẢNG MARKDOWN, TUYỆT ĐỐI KHÔNG DÙNG VĂN XUÔI VÀ KHÔNG DÙNG VĂN PHONG GIÁO VIÊN.

**Bài tập:**
- Xây dựng ETL Pipeline bằng Python để làm sạch và chuẩn hóa dữ liệu khoáng thạch từ file game gốc.
- Viết logic kiểm định ràng buộc nguyên liệu đầu vào và sản phẩm đầu ra của công thức ép trang bị.
- Trích xuất thuộc tính cộng thêm phụ và tỷ lệ rèn thành công cho Thần Thiết Cổ Tự và Long Lân Thạch.

**Tags:**
#khoang_thach #da_ep_do #nang_cap_trang_bi #etl_pipeline #knowledge_map

---

## Day 86 — Bóc Tách Dược Liệu Quý, Bí Truyền Thuật Pháp & Tiên Nhân
**Prompt:**
Hãy lập bảng bách khoa toàn thư bóc tách chi tiết thông số các thực thể: Tả Từ, Nam Hoa Lão Tiên, Vu Cát, Lăng Không Sương, Cửu Chuyển Hoàn Dược, Thái Ất Chân Đan, Tuyệt Kỹ Bí Kíp - Cuồng Phong, Tuyệt Kỹ Bí Kíp - Ngũ Lôi, Linh Chi Vạn Năm, Tuyết Liên Hoa, Tiên Đan Tăng Võ Trí, Binh Phù Thần Kỵ, Binh Phù Hoàng Binh, Huyền Thiết Thạch, Thần Linh Cốt. Yêu cầu xử lý chuyển đổi bảng mã Big5/GBK sang UTF-8 không còn ký tự lỗi, xác minh tính toàn vẹn liên kết ID giữa bí kíp, dược liệu và hiệu ứng kỹ năng, trích xuất đầy đủ không bỏ sót dữ liệu. Trả về kết quả NGUYÊN BẢN BẰNG BẢNG MARKDOWN, TUYỆT ĐỐI KHÔNG DÙNG VĂN XUÔI VÀ KHÔNG DÙNG VĂN PHONG GIÁO VIÊN.

**Bài tập:**
- Viết script kiểm tra lỗi mã hóa font Big5/GBK trên toàn bộ tập dữ liệu 15 thực thể.
- Xây dựng ma trận liên kết ID giữa Bí kíp tuyệt kỹ và Hiệu ứng kỹ năng tương ứng trong CSDL.
- Xuất dữ liệu chuẩn hóa dạng JSON và bảng Markdown cho nhóm thực thể hỗn hợp bao gồm tiên nhân, bí kíp và dược liệu.

**Tags:**
#sango_heroes_7 #tien_nhan #bi_kip_ky_nang #duoc_lieu #data_integrity

---

## Day 87 — Trích Xuất Võ Tướng Kỹ Đao Kiếm & Trường Binh & Chuẩn Hóa Schema Kỹ Năng
**Prompt:**
Hãy lập bảng bách khoa toàn thư trích xuất chi tiết 15 Võ tướng kỹ nhóm Đao Kiếm và Trường Binh từ file .INI gốc của Sango 7. Yêu cầu giải mã bảng mã Big5 sang UTF-8, trích xuất các chỉ số MP tiêu hao, sát thương, diện tích ảnh hưởng, hiệu ứng khống chế, kiểm định Foreign Key Integrity đối với Tướng sở hữu, đạt chuẩn JSON Schema validation và không bỏ sót thực thể. Trả về kết quả NGUYÊN BẢN BẰNG BẢNG MARKDOWN, TUYỆT ĐỐI KHÔNG DÙNG VĂN XUÔI VÀ KHÔNG DÙNG VĂN PHONG GIÁO VIÊN.

**Bài tập:**
- Lập bảng trích xuất 15 Võ tướng kỹ Đao Kiếm/Trường Binh với đầy đủ chỉ số MP, sát thương và diện tích ảnh hưởng.
- Viết script kiểm tra Foreign Key Integrity kết nối giữa Skill ID kỹ năng và General ID sở hữu.
- Kiểm định dữ liệu bóc tách bằng JSON Schema Validator để đảm bảo tính đúng đắn cấu trúc.

**Tags:**
#vo_tuong_ky #dao_kiem #truong_binh #big5_encoding #json_schema

---

## Day 88 — Bóc Tách Võ Tướng Kỹ Cung Nỗ & Phép Thuật & Validation Dữ Liệu Sát Thương
**Prompt:**
Hãy lập bảng bách khoa toàn thư bóc tách chi tiết 15 Võ tướng kỹ nhóm Cung Nỗ và Phép Thuật Biến Hóa từ Sango 7. Yêu cầu xử lý rác dữ liệu (garbage code), làm sạch và validate qua Pydantic, không còn thuộc tính null hoặc lỗi encoding, kiểm tra phạm vi sát thương, thời gian hồi và thuộc tính nguyên tố. Trả về kết quả NGUYÊN BẢN BẰNG BẢNG MARKDOWN, TUYỆT ĐỐI KHÔNG DÙNG VĂN XUÔI VÀ KHÔNG DÙNG VĂN PHONG GIÁO VIÊN.

**Bài tập:**
- Xây dựng Pydantic Data Model kiểm tra điều kiện ranh giới sát thương và thời gian hồi chiêu cho kỹ năng phép thuật.
- Viết hàm Python lọc và xử lý các chuỗi rác dữ liệu (garbage code) trong thuộc tính mô tả kỹ năng.
- Trích xuất thuộc tính nguyên tố và phạm vi sát thương của 15 Võ tướng kỹ Cung Nỗ/Phép Thuật.

**Tags:**
#vo_tuong_ky #cung_no #phep_thuat #pydantic_validation #data_cleansing

---

## Day 89 — Trích Xuất Quân Sư Kỹ Điều Binh & Hồi Phục & Xây Dựng Relational Mapping
**Prompt:**
Trích xuất đầy đủ 15 Quân sư kỹ chiến thuật/trị liệu và thiết kế Relational Mapping liên kết giữa Quân Sư - Điều Kiện Kích Hoạt - Kỹ Năng dựa trên Sango 7 Stratagem Config File. Xác định rõ điều kiện Trí tuệ (INT) và Cấp độ tối thiểu. Yêu cầu đầu ra hoàn tất dưới dạng BẢNG MARKDOWN NGHIÊM NGẶT (gồm các cột: Mã_Kỹ_Năng, Tên_Quân_Sư_Kỹ, Loại_Hiệu_Ứng, MP_Tiêu_Hao, Điều_Kiện_INT, Cấp_Độ_Yêu_Cầu, Mô_Tả_Quan_Hệ_Relational_Mapping), KHÔNG dùng văn xuôi, KHÔNG giải thích lý thuyết chung chung, KHÔNG dùng tiêu đề '## Day'.

**Bài tập:**
- Đọc và phân tích file Sango 7 Stratagem Config File để trích xuất danh sách 15 Quân sư kỹ chiến thuật và trị liệu.
- Xác định ngưỡng chỉ số Trí tuệ (INT) và Cấp độ (Level) bắt buộc đối với tướng đóng vai trò Quân sư để kích hoạt từng kỹ năng.
- Xây dựng sơ đồ quan hệ Relational Mapping và ánh xạ bảng kỹ năng với bảng Quân sư trong Data Normalization Schema.
- Xuất dữ liệu hoàn chỉnh thành bảng Markdown đúng chuẩn định dạng yêu cầu.

**Tags:**
#quan_su_ky #phuc_binh #tri_lieu #relational_mapping #sango_7

---

## Day 90 — Bóc Tách Tuyệt Kỹ Hợp Thể & Mô Hình Hóa Đồ Thị Tương Tác (Graph Schema)
**Prompt:**
Bóc tách chi tiết 14 Tuyệt kỹ Hợp thể & Tình cảm kỹ trong Sango 7 Combo Skill Data và xây dựng Graph Schema (Neo4j) biểu diễn mối quan hệ kích hoạt Combo giữa các cặp Tướng. Yêu cầu liệt kê chính xác các thuộc tính: Tướng yêu cầu, tiêu hao MP, chỉ số Võ/Trí tối thiểu, và mô hình hóa quan hệ đồ thị (Nodes: Võ tướng, Edges: Kích hoạt Tuyệt kỹ). Xuất kết quả dưới dạng BẢNG MARKDOWN NGHIÊM NGẶT (gồm các cột: Mã_Combo, Tên_Tuyệt_Kỹ_Hợp_Thể, Danh_Sách_Tướng_Yêu_Cầu, MP_Tiêu_Hao, Yêu_Cầu_Võ_Trí, Edge_Label_Graph Schema, Ràng_Buộc_Toàn_Vẹn_ID), KHÔNG dùng văn xuôi hay văn phong giáo viên, KHÔNG có dòng '## Day'.

**Bài tập:**
- Trích xuất thông số 14 Tuyệt kỹ Hợp thể & Tình cảm kỹ từ Sango 7 Combo Skill Data.
- Thiết kế Graph DB Schema trên Neo4j xác định Nút (Node) Võ Tướng và Cạnh (Edge) kích hoạt Tuyệt kỹ Hợp thể.
- Viết script kiểm tra kịch bản ràng buộc toàn vẹn ID cặp tướng kích hoạt tuyệt kỹ.
- Đóng gói kết quả trích xuất vào bảng Markdown chuẩn cấu trúc Graph Schema.

**Tags:**
#tuyet_ky_hop_the #tinh_cam_ky #graph_schema #combo_skill #knowledge_graph #sango_7

---

## Day 91 — Bóc Tách Đặc Tính Ẩn Nội Tại & Đóng Gói Pipeline Data Normalization
**Prompt:**
Trích xuất 15 Đặc tính nội tại ẩn của võ tướng (Kiếm Vang, Bá Vương, Cương Thể, Y Thuật...) từ Sango 7 Trait/Passive Config và đóng gói Data Pipeline chuẩn hóa dữ liệu kỹ năng/đặc tính về dạng 3NF (3rd Normal Form). Yêu cầu xuất kết quả bằng BẢNG MARKDOWN NGHIÊM NGẶT (gồm các cột: Mã_Đặc_Tính, Tên_Đặc_Tính_Ẩn, Loại_Nội_Tại, Tỷ_Lệ_Kích_Hoạt, Tác_Dụng_Chỉ_Số, Quy_Tắc_Chuẩn_Hóa_3NF, Pipeline_Output_Status). TUYỆT ĐỐI KHÔNG dùng văn xuôi hay lý thuyết tổng quát, KHÔNG sử dụng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Trích xuất thông số 15 đặc tính ẩn/nội tại từ file Sango 7 Trait/Passive Config.
- Áp dụng các quy tắc chuẩn hóa dữ liệu 3NF (3rd Normal Form) để loại bỏ trùng lặp dữ liệu thuộc tính.
- Xây dựng Data Pipeline bằng Python Pandas để tự động làm sạch và xuất JSON Schema.
- Tổng hợp dữ liệu đã chuẩn hóa vào bảng Markdown đáp ứng định nghĩa hoàn thành.

**Tags:**
#dac_tinh_an #noi_tai #data_normalization #data_pipeline #sango_7

---

## Day 92 — Võ Tướng Kỹ Triệu Hoán & Biến Hóa Thiên Tai Cấp Cao
**Prompt:**
Bóc tách và giải mã toàn bộ danh mục Võ tướng kỹ triệu hoán & thiên tai cấp cao từ file config INI gốc: Thần Hoàng Phượng Hoàng, Cửu Châu Thần Long, Cuồng Phong Bão Tuyết, Địa Hỏa Ma Long, Hoàng Long Thiên Tương, Xích Luyện Hỏa Hồ, Băng Sương Long Cuồng, Phong Sương Băng Nhẫn, Thiên Lôi Lạc, Ngũ Phong Oanh Đỉnh, Thiên Hỏa Diệt Thế, U Minh Trầm Luân, Hỏa Đao Phẫn Nổ. Yêu cầu chuyển đổi mã Big5/GBK sang UTF-8, kiểm thử Skill ID, xác định chỉ số Võ/Trí yêu cầu, phạm vi và sát thương. Trả kết quả DUY NHẤT dưới dạng BẢNG MARKDOWN NGHIÊM NGẶT (gồm các cột: Skill_ID, Tên_Kỹ_Năng_UTF8, Yêu_Cầu_Võ_Trí, MP_Tiêu_Hao, Phạm_Vi_Sát_Thương, Năng_Lực_Ẩn, Trạng_Thái_Giải_Mã_Big5). KHÔNG dùng văn xuôi hay văn phong hướng dẫn.

**Bài tập:**
- Sử dụng bảng chuyển đổi Big5/GBK sang UTF-8 để giải mã tên và mô tả của 13 Võ tướng kỹ triệu hoán & thiên tai.
- Trích xuất các thông số sát thương, phạm vi tác động và năng lực ẩn từ file cấu hình game.
- Thực hiện kiểm thử tính toàn vẹn của Skill ID so với dữ liệu gốc.
- Điền đầy đủ thông tin vào bảng Markdown theo đúng danh mục thực thể đã liệt kê.

**Tags:**
#vo_tuong_ky #trieu_hoan #thien_tai #phep_thuat #big5_utf8 #data_validation

---

## Day 93 — Quân Sư Kỹ Trận Pháp Bẫy Hạc & Khống Chế Chiến Trường
**Prompt:**
Trích xuất đầy đủ các Quân sư kỹ trận pháp & khống chế chiến trường: Bát Trận Đồ, Tả Hữu Kiềm Chế, Hạm Đội Bát Kim, Hỗn Lộn Trận, Thập Diện Mai Phục, Ngự Địch Liệt Trận, Thù Địch Phân Hóa, Huyễn Khiếu Trận, Chuyển Yếu Thành Cường, Binh Khí Khống Chế, Phong Ma Trận, Ngự Ma Chi Thuật, Giải Trừ Binh Quyền. Xác định chính xác tiêu hao MP, tỷ lệ khống chế, hiệu ứng ẩn lên binh chủng và kiểm tra ràng buộc Foreign Key tới danh mục Quân sư. Kết xuất BẮT BUỘC dạng BẢNG MARKDOWN NGHIÊM NGẶT (gồm các cột: Mã_QSK, Tên_Quân_Sư_Kỹ, MP_Tiêu_Hao, Tỷ_Lệ_Khống_Chế, Hiệu_Ứng_Trận_Pháp_Ẩn, Foreign_Key_Check_Status). TUYỆT ĐỐI KHÔNG dùng văn xuôi, KHÔNG chứa heading '## Day'.

**Bài tập:**
- Trích xuất chỉ số MP, tỷ lệ khống chế và tác động chiến trường của 13 Quân sư kỹ trận pháp từ file cấu hình.
- Phân tích hiệu ứng ẩn của các trận pháp tác động lên từng binh chủng và võ tướng.
- Chạy kịch bản kiểm tra Foreign Key Check liên kết giữa mã kỹ năng và danh mục Quân sư bằng Python Pydantic.
- Tổng hợp dữ liệu trích xuất vào bảng Markdown nghiêm ngặt.

**Tags:**
#quan_su_ky #tran_phap #bay_hac #khong_che #foreign_key_check

---

## Day 94 — Tuyệt Kỹ Hợp Thể Danh Tướng & Võ Hiệp Liên Hoàn
**Prompt:**
Trích xuất chi tiết các Tuyệt kỹ hợp thể danh tướng & võ hiệp liên hoàn: Ngũ Hổ Phá Phong, Tứ Đại Đô Đốc Trận, Ngũ Tử Lương Tướng Kích, Long Sương Hổ Đấu, Thần Nhâm Tam Ma, Long Phượng Hòa Binh, Thất Tinh Đấu Trận, Tam Nguyện Liên Trọng, Bát Quái Kỳ Môn, Thái Cực Hoàng Long, Võ Thánh Bát Giáo, Phượng Hoàng Triều Dương. Xác định danh sách tướng bắt buộc, MP, sát thương thực tế và ánh xạ vào Knowledge Graph Schema (mối quan hệ N-N). Trả kết quả BẮT BUỘC bằng BẢNG MARKDOWN NGHIÊM NGẶT (gồm các cột: Mã_Combo, Tên_Tuyệt_Kỹ_Danh_Tướng, Danh_Sách_Tướng_Bắt_Buộc, MP_Yêu_Cầu, Sát_Thương_Thực_Tế, Graph_Mapping_Relation). TUYỆT ĐỐI KHÔNG dùng văn xuôi hay giải thích lý thuyết.

**Bài tập:**
- Trích xuất danh sách danh tướng bắt buộc và thông số kỹ năng từ Combo Skills Sango 7.
- Tính toán sát thương thực tế và vùng ảnh hưởng dựa trên thuật toán kỹ năng hợp thể.
- Ánh xạ quan hệ nhiều-nhiều (N-N) giữa các vị tướng và kỹ năng hợp thể vào Knowledge Graph Schema.
- Đóng gói kết quả trích xuất vào bảng Markdown chính xác theo yêu cầu.

**Tags:**
#tuyet_ky_hop_the #danh_tuong #combo_ky_nang #sango_7 #graph_schema

---

## Day 95 — Đặc Tính Nội Tại Kiếm Vang, Thuyết Phục & Hồi Phục Ẩn
**Prompt:**
Trích xuất và giải mã danh sách các đặc tính ẩn/nội tại võ tướng: Kiếm Vang, Thuyết Phục, Hồi Máu, Trảm Ma, Đao Pháp Bá Vương, Tiễn Thuật Tuyệt Luân, Thủy Chiến Tinh Anh, Hành Quân Thần Tốc, Bát Chiêu Kháng Cự, Binh Pháp Uy Nghiêm, Phản Phục Cương Cường, Thu Lục Binh Sĩ, Phi Cước. Xác định chính xác các mã ID ẩn không hiển thị trên UI game gốc, tỷ lệ kích hoạt và bonus thuộc tính. Trả kết quả DUY NHẤT dưới dạng BẢNG MARKDOWN NGHIÊM NGẶT (gồm các cột: ID_An, Tên_Đặc_Tính, Trạng_Thái_Hiển_Thị_UI, Tỷ_Lệ_Kích_Hoạt, Bonus_Thuộc_Tính, Định_Dạng_JSON_Schema). KHÔNG dùng văn xuôi hay văn phong giảng dạy, KHÔNG viết tiêu đề '## Day'.

**Bài tập:**
- Đọc file Trait INI và sử dụng bảng tra cứu ID ẩn để giải mã 13 đặc tính nội tại võ tướng.
- Xác định tỷ lệ kích hoạt, lượng hồi phục và các chỉ số cộng thêm ẩn của từng đặc tính.
- Chuẩn hóa cấu trúc dữ liệu trích xuất theo JSON Schema quy định.
- Điền toàn bộ thực thể bóc tách vào bảng Markdown chuẩn.

**Tags:**
#dac_tinh_an #noi_tai #kiem_vang #thuyet_phuc #hidden_trait #json_schema

---

## Day 96 — Quân Sư Kỹ Tăng Cường Chỉ Số, Chiêu Hàng & Trợ Chiến
**Prompt:**
Trích xuất danh mục Quân sư kỹ chiêu hàng & tăng chỉ số trợ chiến: Chiêu Hàng Cấp Cao, Khuyên Hàng Bá Vương, Khí Huyết Tăng Cường, Khí Huyết Đại Phục, Trí Lực Tăng Cường, Võ Lực Bào Hòa, Tinh Thần Cốt Lõi, Khuyến Học Tri Thức, Bạc Nhược Tương Đương, Cấp Tốc Hành Quân, Vũ Lực Kích Phát, Trí Huệ Bộc Phát. Trích xuất các hệ số buff/debuff, tỷ lệ chiêu hàng thành công và chạy quy trình Automated Data Validation & Deduplication cho toàn Phase Kỹ năng. Trả kết quả bằng BẢNG MARKDOWN NGHIÊM NGẶT (gồm các cột: Mã_QSK, Tên_Quân_Sư_Kỹ, Loại_Buff_Debuff, Tỷ_Lệ_Chiêu_Hang, Tác_Động_Trí_Lực_Quân_Sư, Data_Validation_Status, Deduplication_Check). TUYỆT ĐỐI KHÔNG dùng văn xuôi hay lời dẫn.

**Bài tập:**
- Trích xuất hệ số tác động và tỷ lệ chiêu hàng của 12 Quân sư kỹ từ cơ sở dữ liệu game.
- Phân tích mối liên hệ giữa chỉ số Trí lực của Quân sư và hiệu quả trợ chiến thực tế.
- Thực hiện kịch bản Automated Data Validation và khử trùng lặp (Deduplication) cho toàn bộ dữ liệu Phase Kỹ năng.
- Xuất bảng kết quả Markdown hoàn chỉnh đáp ứng Definition of Done.

**Tags:**
#quan_su_ky #chieu_hang #tang_chi_so #tro_chien #data_validation #deduplication

---

## Day 97 — Võ Tướng Kỹ Hệ Nguyên Tố Hỏa Lôi Băng & Chuẩn Hóa Dữ Liệu Sát Thương
**Prompt:**
Hãy lập Bách khoa toàn thư trích xuất dữ liệu cho '15 Võ tướng kỹ hệ nguyên tố' (Hỏa, Lôi, Băng) từ file config kỹ năng Sango Heroes 7 (.INI/.PAK). Thực hiện chuyển đổi mã hóa từ Big5/GBK sang UTF-8, làm sạch ký tự rác và validate tính hợp lệ của chỉ số tiêu hao MP, thời gian hồi và sát thương diện rộng. Trình bày kết quả TUYỆT ĐỐI dưới dạng BẢNG MARKDOWN nghiêm ngặt gồm các cột: Skill ID, Tên Kỹ Năng (UTF-8), Mã Gốc (Big5/GBK), Hệ Nguyên Tố, Tiêu Hao MP, Sát Thương Diện Rộng, Thời Gian Hồi (s), Trạng Thái Validation. TUYỆT ĐỐI KHÔNG dùng văn xuôi, không dùng văn phong giáo viên, không giải thích lý thuyết tổng quát.

**Bài tập:**
- Viết script Python sử dụng thư viện `codecs` hoặc `ftfy` để tự động scan và chuyển đổi toàn bộ chuỗi Big5/GBK sang UTF-8 trong file INI.
- Xây dựng quy tắc kiểm thử tự động (Data Integrity Check) kiểm tra điều kiện sát thương diện rộng > 0 và MP tiêu hao > 0 đối với 15 kỹ năng nguyên tố.

**Tags:**
#votuongky #nguyento #dientrong #satthuong #big5 #utf8

---

## Day 98 — Quân Sư Kỹ Hỗ Trợ Thủ Thành & Kiểm Thử Ràng Buộc Điều Kiện Thi Thiếp
**Prompt:**
Hãy tạo hệ thống Bách khoa toàn thư cho '15 Quân sư kỹ thủ thành' (gia cố thành trì, hồi phục quân sĩ) từ tệp cấu trúc dữ liệu game gốc. Yêu cầu liên kết điều kiện thi triển theo chỉ số Trí tuệ (INT) tối thiểu, kiểm tra tính toàn vẹn Foreign Key Integrity với bảng thuộc tính Võ Tướng và chạy JSON Schema Validator script để lọc dữ liệu rác/null. Trình bày BẮT BUỘC bằng BẢNG MARKDOWN nghiêm ngặt với các cột: Strategist Skill ID, Tên Quân Sư Kỹ, Chỉ Số Trí Tuệ Yêu Cầu, Phạm Vi Ảnh Hưởng, Hiệu Ứng Gia Cố/Hồi Phục, Foreign Key Status, Schema Validation Result. KHÔNG dùng văn xuôi, KHÔNG có lời dẫn hay giải thích của giáo viên.

**Bài tập:**
- Định nghĩa JSON Schema để ràng buộc thuộc tính `required_int` là số nguyên dương và `effect_range` không được nhận giá trị null.
- Viết script Python xác minh Foreign Key Integrity giữa danh sách ID Quân sư kỹ và ID Võ tướng sở hữu trong cơ sở dữ liệu.

**Tags:**
#quansuky #thuthanh #giaco #hoiphuc #schemavalidation

---

## Day 99 — Tuyệt Kỹ Hợp Thể Tình Duyên & Mô Hình Hóa Quan Hệ Đa Thực Thể
**Prompt:**
Hãy xây dựng Bách khoa toàn thư trích xuất '12 Tuyệt kỹ hợp thể tình duyên & chư thần' và lập bản đồ quan hệ (Relational Mapping) giữa các Võ tướng kích hoạt từ dữ liệu Sango 7. Yêu cầu bóc tách danh sách ID các tướng bắt buộc phối hợp, tính toán tiêu hao MP hợp thể và đảm bảo tính toàn vẹn tham chiếu (Foreign Key) giữa Tướng và Tuyệt kỹ. Trình bày BẮT BUỘC bằng BẢNG MARKDOWN nghiêm ngặt với các cột: Combo Skill ID, Tên Tuyệt Kỹ Hợp Thể, Danh Sách ID Tướng Yêu Cầu, Loại Hợp Thể (Tình Duyên/Chư Thần), Tiêu Hao MP, Sát Thương Cộng Hưởng, Foreign Key Reference Status. TUYỆT ĐỐI KHÔNG sử dụng văn xuôi, không bổ sung văn phong giảng dạy.

**Bài tập:**
- Thiết kế sơ đồ ERD (Entity-Relationship Diagram) thể hiện mối quan hệ N-M giữa bảng Võ Tướng và bảng Hợp Thể Kỹ.
- Viết truy vấn SQL/Script kiểm tra ràng buộc tham chiếu Foreign Key để đảm bảo không có ID tướng không tồn tại trong công thức hợp thể.

**Tags:**
#hoptheky #tinhduyen #tuongsinh #relationalmapping #foreignkey

---

## Day 100 — Đặc Tính Ẩn Danh Tướng Độc Quyền & Phân Tích Thuộc Tính Nội Tại Nâng Cao
**Prompt:**
Hãy lập Bách khoa toàn thư bóc tách '15 Đặc tính ẩn nội tại độc quyền' của danh tướng 8 phe từ file config đặc tính. Thực hiện làm sạch dữ liệu, bóc tách các chỉ số ẩn không hiển thị trên UI ingame và ánh xạ chính xác 100% ID đặc tính vào hồ sơ Danh tướng tương ứng sử dụng Pydantic Data Models. Trình bày BẮT BUỘC bằng BẢNG MARKDOWN nghiêm ngặt gồm các cột: Trait ID, Tên Đặc Tính Ẩn, Tướng Sở Hữu (Hero ID), Phe Phái, Chỉ Số Nội Tại Ẩn (Non-UI Stat), Tỷ Lệ Kích Hoạt Ẩn (%), Pydantic Mapping Status. TUYỆT ĐỐI KHÔNG dùng văn xuôi hay đoạn văn hướng dẫn.

**Bài tập:**
- Xây dựng Pydantic Model trong Python với các trường validation chặt chẽ cho thuộc tính ẩn của danh tướng.
- Viết hàm làm sạch dữ liệu text loại bỏ các ký tự điều khiển và ký tự rác từ file config đặc tính ẩn.

**Tags:**
#dactinhan #noitai #danhtuong #docquyen #datamapping

---

## Day 101 — Kỹ Năng Bá Vương Cấp Cuối & Đóng Gói ETL Pipeline Phase Kỹ Năng
**Prompt:**
Hãy tạo Bách khoa toàn thư tổng hợp '15 Tuyệt kỹ cấp cuối kịch bản thần thoại' (như Thiên Đạo Diệt Thế, Bá Vương Tàn Bạo...) và đóng gói Pipeline ETL tự động cho Phase Kỹ năng. Thực hiện quy trình khử trùng lặp (Deduplication) dữ liệu và xuất dataset chuẩn hóa đáp ứng Knowledge Graph Schema dưới dạng bảng. BẮT BUỘC xuất ra BẢNG MARKDOWN nghiêm ngặt gồm các cột: Ultimate Skill ID, Tên Kỹ Năng Bá Vương, Kịch Bản Xuất Hiện, Tiêu Hao MP, Chỉ Số Diệt Thế, Status Khử Trùng Lặp (Deduplicated), Knowledge Graph Schema Status. KHÔNG dùng văn xuôi, KHÔNG chứa câu thoại giáo viên.

**Bài tập:**
- Xây dựng ETL Pipeline bằng Python thực hiện Deduplication trên dataset kỹ năng dựa trên hash giá trị thuộc tính.
- Xuất toàn bộ dataset kỹ năng đã làm sạch ra định dạng JSON-LD phù hợp với tiêu chuẩn Knowledge Graph Schema.

**Tags:**
#kynangcapcuoi #bavuong #thanthoai #etlpipeline #deduplication

---

## Day 102 — Võ Tướng Kỹ Hệ Cạm Bẫy, Địa Đao & Ám Khí Sát Thương (Trích Xuất & Chuẩn Hóa Mã Font)
**Prompt:**
Hãy lập Bách khoa toàn thư bóc tách '12 kỹ năng cạm bẫy/ám khí' (bao gồm Bát Quái Đột Huyệt, Địa Lôi Đột Kích...). Trích xuất chỉ số Võ, Trí, MP tiêu hao, hiệu ứng cạm bẫy từ file game; chuyển đổi bảng mã font Big5/GBK sang UTF-8, loại bỏ ký tự rác và liên kết Skill ID với danh sách tướng sở hữu. Trình bày BẮT BUỘC bằng BẢNG MARKDOWN nghiêm ngặt với các cột: Skill ID, Tên Kỹ Năng (UTF-8), Chuỗi Mã Gốc (Big5/GBK), Yêu Cầu Võ/Trí, MP Tiêu Hao, Hiệu Ứng Bẫy/Ám Khí, Hero Skill Link Status. TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên.

**Bài tập:**
- Viết script Python giải mã các chuỗi byte Big5/GBK chứa thông tin kỹ năng cạm bẫy và ghi đè sang mã UTF-8 chuẩn.
- Tạo cấu trúc JSON lưu trữ 12 kỹ năng cạm bẫy/ám khí kèm danh sách tướng được phép thi triển.

**Tags:**
#votuongky #cambay #dialoi #amkhi #big5encoding

---

## Day 103 — Quân Sư Kỹ Phong Ấn, Giải Trừ Phép Thuật & Khống Chế Tuyệt Chiêu
**Prompt:**
Hãy tạo Bách khoa toàn thư trích xuất '12 quân sư kỹ phong ấn/giải trừ phép thuật' (phong ấn, triệt tiêu, giải trừ hiệu ứng khống chế). Phân tích điều kiện Trí tuệ (INT) tối thiểu để mở khóa và kiểm tra tính toàn vẹn tham chiếu Foreign Key với bảng chỉ số Trí tuệ của Võ Tướng. BẮT BUỘC trình bày bằng BẢNG MARKDOWN nghiêm ngặt gồm các cột: Skill ID, Tên Quân Sư Kỹ, Loại Hiệu Ứng (Phong Ấn/Giải Trừ), Chỉ Số INT Yêu Cầu, Phạm Vi Tác Dụng, Foreign Key Integrity Status, Validation Result. TUYỆT ĐỐI KHÔNG dùng văn xuôi hay lời giảng.

**Bài tập:**
- Viết script SQL/Python kiểm tra tính toàn vẹn Foreign Key giữa bảng `QuanSuKy` và bảng `ChiSoVoTuong` dựa trên trường `INT_requirement`.
- Lập script tự động phát hiện các bản ghi thiếu thông tin chỉ số Trí tuệ tối thiểu hoặc chứa giá trị âm.

**Tags:**
#quansuky #phongan #triettieu #khongche #datavalidation

---

## Day 104 — Tuyệt Kỹ Hợp Thể Nhóm Danh Tướng Tam Quốc Diễn Nghĩa
**Prompt:**
Hãy lập Bách khoa toàn thư mô hình hóa quan hệ N-M (Combination Mapping) cho '12 tuyệt kỹ hợp thể danh tướng Tam Quốc Diễn Nghĩa' (như Tam Anh Chiến Lữ Bố, Ngũ Hổ Phá Địch...). Trích xuất điều kiện danh tướng đồng thời ra trận, tính toán công thức sát thương cộng hưởng và tiêu hao MP hợp thể dưới dạng Graph Schema. Trình bày BẮT BUỘC bằng BẢNG MARKDOWN nghiêm ngặt với các cột: Combo Skill ID, Tên Tuyệt Kỹ Hợp Thể, Danh Sách Danh Tướng Yêu Cầu (Tam Anh/Ngũ Hổ...), Công Thức Sát Thương Cộng Hưởng, MP Tiêu Hao, Graph Schema Node Status. KHÔNG dùng văn xuôi, KHÔNG có lời dẫn hay nhận xét giáo viên.

**Bài tập:**
- Xây dựng sơ đồ Graph Schema (dạng JSON Graph) biểu diễn mối quan hệ đa-đa giữa các danh tướng và tuyệt kỹ hợp thể.
- Viết hàm Python tính toán sát thương cộng hưởng dựa trên tổng chỉ số Võ/Trí của các tướng tham gia kích hoạt kỹ năng.

**Tags:**
#tuyetkyhopthe #tamanh #nguho #danhtuong #graphschema

---

## Day 105 — Đặc Tính Nội Tại Thần Tốc, Né Tránh, Bạo Kích & Hút Máu
**Prompt:**
Yêu cầu thực hiện dự án: Trích xuất 12 đặc tính nội tại ẩn và chuẩn hóa kiểu dữ liệu chỉ số phần trăm kích hoạt (Float 0.0 - 1.0) cho Knowledge Map. Đảm bảo hoàn thành các tiêu chí (Definition of Done): Số hóa 12 đặc tính ẩn chiến đấu (Thần Tốc, Né Tránh, Bạo Kích, Hút Huyết...) cùng chỉ số kích hoạt vào CSDL; Chuẩn hóa dữ liệu tỷ lệ % né tránh/bạo kích/hút máu dạng Float [0.0 - 1.0]. Yêu cầu trình bày kết quả hoàn toàn bằng BẢNG MARKDOWN nghiêm ngặt, tuyệt đối không dùng văn xuôi, không sử dụng lời mở đầu hay văn phong giáo viên.

**Bài tập:**
- Trích xuất thông số 12 đặc tính ẩn nội tại và biểu diễn dưới dạng bảng Markdown chi tiết.
- Xây dựng phương thức chuẩn hóa dữ liệu tỷ lệ phần trăm bạo kích, né tránh, hút máu sang định dạng Float [0.0 - 1.0] trong CSDL.

**Tags:**
#dactinhan #noitai #baokich #hutmau #datanormalization

---

## Day 106 — Kỹ Năng Độc Quyền Tiên Nhân, Thần Thoại & Thủ Lĩnh Dị Tộc
**Prompt:**
Thực hiện nhiệm vụ: Trích xuất 12 kỹ năng thần thoại dị tộc và viết kịch bản Automated Data Validation kiểm tra trùng lặp/thiếu hụt cho toàn phase. Tiêu chuẩn nghiệm thu bao gồm: Trích xuất 12 kỹ năng thần thoại/dị tộc đặc biệt (Ma Vương Chi Nộ, Tiên Nhân Chi Lực...); Chạy thành công suite kiểm thử Data Validation cho toàn bộ Phase Kỹ năng. Kết quả phải xuất dưới dạng BẢNG MARKDOWN chính xác, không văn xuôi, không giải thích lý thuyết.

**Bài tập:**
- Lập bảng tổng hợp 12 kỹ năng thần thoại dị tộc bao gồm Ma Vương Chi Nộ, Tiên Nhân Chi Lực kèm theo thuộc tính ẩn và điều kiện thi triển.
- Viết kịch bản Automated Test Script kiểm tra trùng lặp ID và phát hiện thuộc tính thiếu hụt trên toàn bộ Phase Kỹ năng.

**Tags:**
#kynangthanthoai #tiennhan #ditoc #mavuong #automatedvalidation

---

## Day 107 — Võ Tướng Kỹ Hệ Đao Quạt & Kiểm Định Pydantic Schema Dữ Liệu Skill
**Prompt:**
Yêu cầu triển khai: Trích xuất chi tiết 15 võ tướng kỹ hệ đao quạt và xây dựng kịch bản Pydantic validation kiểm định dữ liệu. Đảm bảo đạt Definition of Done: Bảng Markdown bóc tách đủ 15 võ tướng kỹ hệ đao quạt không thiếu thực thể; Kịch bản Pydantic Schema xác minh tính toàn vẹn dữ liệu MP, Võ, Trí chạy không lỗi. Yêu cầu trả kết quả bằng BẢNG MARKDOWN nghiêm ngặt, tuyệt đối không dùng văn phong hướng dẫn hay văn xuôi.

**Bài tập:**
- Trích xuất và lập bảng thuộc tính chi tiết tiêu hao MP, yêu cầu Võ/Trí và sát thương của 15 võ tướng kỹ hệ đao quạt.
- Xây dựng Pydantic Model để validate kiểu dữ liệu và ràng buộc giá trị hợp lệ cho các thuộc tính kỹ năng MP, Võ, Trí.

**Tags:**
#votuongky #daoquat #pydantic #datavalidation #satthuong

---

## Day 108 — Quân Sư Kỹ Thời Tiết Địa Hình & Xây Dựng Ma Trận Tác Động Chiến Trường
**Prompt:**
Thực hiện dự án: Trích xuất 15 quân sư kỹ khí tượng/địa hình và mô hình hóa ma trận ảnh hưởng thời tiết đến tốc độ, sát thương. Đáp ứng tiêu chí nghiệm thu: Bảng bóc tách 15 quân sư kỹ thời tiết địa hình đúng định dạng; Ma trận JSON thể hiện hệ số tác động của từng kỹ năng khí tượng lên điều kiện chiến đấu. Trình bày hoàn toàn bằng BẢNG MARKDOWN, tuyệt đối không sử dụng văn xuôi hay câu từ dẫn dắt.

**Bài tập:**
- Bóc tách thuộc tính năng lực, MP tiêu hao và điều kiện kích hoạt của 15 quân sư kỹ thời tiết địa hình vào bảng Markdown.
- Thiết lập cấu trúc ma trận JSON mô hình hóa hệ số ảnh hưởng của các hiệu ứng khí tượng lên di chuyển và sát thương binh chủng.

**Tags:**
#quansuky #thoitiet #diahinh #matran #knowledgegraph

---

## Day 109 — Tuyệt Kỹ Hợp Thể Tri Kỷ & Ràng Buộc Khóa Ngoại (Foreign Key Integrity)
**Prompt:**
Thực hiện nhiệm vụ: Trích xuất 15 tuyệt kỹ hợp thể và viết script kiểm tra toàn vẹn tham chiếu Foreign Key tới danh sách Võ Tướng ID. Tiêu chí hoàn thành: Đủ bảng bóc tách 15 tuyệt kỹ hợp thể độc đáo không sót thực thể; Script kiểm định Foreign Key Integrity xác nhận 100% General ID yêu cầu đều tồn tại trong DB Tướng. Bắt buộc xuất kết quả dưới dạng BẢNG MARKDOWN nghiêm ngặt, không chứa văn xuôi.

**Bài tập:**
- Lập bảng trích xuất 15 tuyệt kỹ hợp thể gồm danh sách võ tướng yêu cầu, tiêu hao MP và phạm vi sát thương diện rộng.
- Phát triển script Python tự động kiểm định Foreign Key Integrity đối soát General ID tham gia hợp thể với CSDL Võ Tướng.

**Tags:**
#hoptheky #tinhduyen #foreignkey #dataintegrity #triky

---

## Day 110 — Đặc Tính Ẩn & Xử Lý Đối Soát Sai Lệch Chỉ Số Giữa Vanilla v1.2 Và Bản Mod
**Prompt:**
Yêu cầu thực hiện: Trích xuất 15 đặc tính ẩn nội tại và lập bảng so sánh sai lệch thuộc tính giữa bản Vanilla v1.20 và Mod Remake. Tiêu chuẩn nghiệm thu: Đủ bảng trích xuất 15 đặc tính ẩn nội tại chuẩn xác; Báo cáo Cross-check ghi nhận rõ khác biệt về chỉ số kháng/thống lĩnh giữa bản gốc và bản Mod. Xuất dữ liệu duy nhất bằng BẢNG MARKDOWN, không văn xuôi, không dùng lời giải thích.

**Bài tập:**
- Trích xuất chỉ số cộng thêm vĩnh viễn và điều kiện sở hữu của 15 đặc tính ẩn nội tại.
- Thực hiện cross-check dữ liệu kháng phép và thống lĩnh giữa Vanilla v1.20 và Mod Remake để lập bảng báo cáo sai lệch.

**Tags:**
#dactinhan #noitai #khangphep #crosscheck #modversioning

---

## Day 111 — Tuyệt Học Bá Vương Thượng Cổ & Tổng Hợp Knowledge Graph Kỹ Năng
**Prompt:**
Thực hiện công việc: Trích xuất 15 kỹ năng cực hạn thượng cổ và đóng gói toàn bộ dữ liệu phase kỹ năng thành Graph Schema (JSON-LD). Kết quả nghiệm thu bắt buộc: Bảng bóc tách 15 kỹ năng thượng cổ chuẩn xác; File JSON-LD hoàn chỉnh mô hình hóa mối quan hệ Tướng - Võ Tướng Kỹ - Quân Sư Kỹ - Hợp Thể Kỹ. Bắt buộc trả lời bằng BẢNG MARKDOWN, không dùng văn xuôi, không có thái độ giảng dạy.

**Bài tập:**
- Bóc tách dữ liệu 15 kỹ năng tuyệt học thượng cổ bá vương bao gồm sát thương bộc phá và điều kiện kích hoạt.
- Đóng gói toàn bộ Knowledge Map phase kỹ năng thành file định dạng JSON-LD Graph Schema thể hiện quan hệ Tướng và Kỹ Năng.

**Tags:**
#tuyethoc #bavuong #thuongco #jsonld #knowledgegraphschema

---

## Day 112 — Võ Tướng Kỹ Hệ Đao Kiếm & Thương Kích Cấp Cao
**Prompt:**
Triển khai dự án: Trích xuất chi tiết 12 Võ tướng kỹ hệ đao kiếm và thương kích cao cấp: Hoàng Long Thiên Tương, Cực Vũ Long Kích, Luân Hồi Sát, Phi Phong Trảm, Thần Thương Loạn Vũ, Đoạn Đạt Sát, Trầm Thập Nhị Kích, Thần Quyển Ba Trảm, Long Càn Trảm, Hắc Phong Thương, Tuyệt Mệnh Kích, Bát Phong Đao. Tiêu chuẩn nghiệm thu: Đúng bảng Markdown, không bỏ sót bất kỳ thực thể nào; Chuẩn hóa tên gọi qua mã hóa Big5 -> UTF-8 và validate chỉ số MP/sát thương. Trình bày hoàn toàn bằng BẢNG MARKDOWN nghiêm ngặt, tuyệt đối không văn xuôi.

**Bài tập:**
- Trích xuất thuộc tính Võ, Trí, tiêu hao MP và sát thương của đủ 12 kỹ năng: Hoàng Long Thiên Tương, Cực Vũ Long Kích, Luân Hồi Sát, Phi Phong Trảm, Thần Thương Loạn Vũ, Đoạn Đạt Sát, Trầm Thập Nhị Kích, Thần Quyển Ba Trảm, Long Càn Trảm, Hắc Phong Thương, Tuyệt Mệnh Kích, Bát Phong Đao.
- Thực hiện chuyển đổi mã hóa Big5/GBK sang UTF-8 cho tên kỹ năng và kiểm tra tính hợp lệ của các chỉ số MP/sát thương.

**Tags:**
#votuongky #daokiem #thuongkich #satthuong #big5toutf8

---

## Day 113 — Quân Sư Kỹ Bát Trận Đồ, Khống Chế Trận Thế & Giảm Sức Địch
**Prompt:**
Hãy lập bảng bóc tách chi tiết dữ liệu 12 Quân sư kỹ chuyên khống chế trận thế và giảm sức địch gồm: Bát Trận Đồ, Thái Cực Trận, Phân Thân Trận, Giảm Thương Sát, Phong Thuật Lô, Trầm Huyết Trận, Ngũ Hành Trận, Giảm Khí Tuyệt, Mãn Uy Bát Trận, Hóa Khí Thuật, Hoán Mệnh Trận, Tuyệt Khí Trận.

Yêu cầu kết quả đầu ra:
1. Bắt buộc xuất dưới dạng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không dùng lý thuyết tổng quát.
2. Cột trong bảng gồm: ID Kỹ Năng, Tên Quân Sư Kỹ, Tiêu Hao MP, Trí Tuệ Tối Thiểu, Phạm Vi Ảnh Hưởng, Hiệu Ứng Khống Chế/Giảm Khí, Trạng Thái Validation Schema.
3. Đáp ứng tiêu chí hoàn thành: 'Đúng bảng Markdown, không bỏ sót bất kỳ thực thể nào' và 'Dữ liệu được validate thành công theo JSON Schema chuẩn'.

**Bài tập:**
- Xây dựng JSON Schema để kiểm tra tính hợp lệ của chỉ số Trí Tuệ Tối Thiểu và Tiêu Hao MP cho 12 Quân sư kỹ khống chế.
- Viết script Python đọc cấu hình file game Sango 7 và trích xuất đúng 12 kỹ năng trên ra định dạng bảng Markdown.

**Tags:**
#quan_su_ky #bat_tran_do #khong_che #giam_khi #json_schema

---

## Day 114 — Tuyệt Kỹ Hợp Thể Nhóm Ba Tướng & Tứ Đại Hổ Tướng
**Prompt:**
Hãy thực hiện trích xuất dữ liệu và lập bảng cho 11 Tuyệt kỹ hợp thể nhóm 3-4 tướng huyền thoại bao gồm: Đào Viên Tam Kết, Ngũ Hổ Trảm, Giang Đông Tam Kiệt, Ngũ Tử Lương Tướng Kỹ, Tam Anh Chiến Lữ Bố, Ngân Hà Tuyệt Diệt, Tam Quốc Bá Vương Kỹ, Phượng Hoàng Ngũ Liên, Tứ Sĩ Liên Hoàn, Tam Tài Trận Kỹ, Ngũ Hành Liên Hoàn.

Yêu cầu đầu ra:
1. Đưa ra kết quả duy nhất dưới dạng BẢNG MARKDOWN nghiêm ngặt. TUYỆT ĐỐI KHÔNG giải thích bằng văn xuôi hay câu từ dẫn dắt của giáo viên.
2. Các cột bắt buộc: ID Tuyệt Kỹ, Tên Tuyệt Kỹ, Danh Sách ID Tướng Kích Hoạt, Yêu Cầu Chỉ Số Võ/Trí, Sát Thương/Hiệu Ứng Hỗ Trợ, Kiểm Tra Foreign Key Integrity.
3. Đảm bảo đạt tiêu chuẩn: 'Đúng bảng Markdown, không bỏ sót bất kỳ thực thể nào' và 'Đảm bảo tính toàn vẹn khóa ngoại (Foreign Key Integrity) giữa ID tướng và ID hợp kỹ'.

**Bài tập:**
- Viết script Python kiểm tra tính toàn vẹn khóa ngoại (Foreign Key Integrity) giữa ID võ tướng và danh sách ID yêu cầu của Tuyệt kỹ hợp thể.
- Tạo bảng mapping mối quan hệ N-N giữa danh sách 11 Tuyệt kỹ hợp thể và các vị tướng kích hoạt tương ứng.

**Tags:**
#tuyet_ky_hop_the #dao_vien_tam_ket #ngu_ho_tram #tam_anh #foreign_key_integrity

---

## Day 115 — Đặc Tính Nội Tại Pháp Thuật, Tâm Pháp Võ Ý & Kháng Sát Thương
**Prompt:**
Trích xuất và chuẩn hóa bảng dữ liệu cho 12 đặc tính ẩn nội tại về pháp thuật và tâm pháp võ ý: Thiền Định, Bát Nhã, Pháp Lực Nhị Bội, Thần Sức, Đoạn Thuật, Linh Thuật, Hộ Thể Thần Khí, Võ Ý Hóa Cực, Bất Động Tinh Thần, Kim Cương Bất Hoại, Cuồng Chiến, Bá Vũ.

Yêu cầu đầu ra:
1. Trả về kết quả hoàn toàn bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong hướng dẫn/giáo viên.
2. Cấu trúc bảng gồm: ID Đặc Tính, Tên Đặc Tính, Tỷ Lệ Kích Hoạt (%), Hệ Số Kháng Sát Thương/Hồi Phục, Tác Động Nội Tại, Quy Trình Deduplication (Đã Làm Sạch/Trùng).
3. Đảm bảo đáp ứng định nghĩa hoàn thành: 'Đúng bảng Markdown, không bỏ sót bất kỳ thực thể nào' và 'Làm sạch dữ liệu trùng lặp và xác minh hệ số cộng dồn đặc tính'.

**Bài tập:**
- Viết hàm Python Deduplication loại bỏ bản ghi đặc tính ẩn bị trùng lặp trong tập file config.
- Tính toán hệ số cộng dồn hiệu ứng nội tại của 'Thiền Định' và 'Pháp Lực Nhị Bội' khi trang bị cùng lúc.

**Tags:**
#dac_tinh_an #thien_dinh #bat_nha #phap_luc #deduplication

---

## Day 116 — Võ Tướng Kỹ & Quân Sư Kỹ Chuyên Trảm Thần Thú & Độc Bảo
**Prompt:**
Trích xuất dữ liệu kỹ năng chuyên biệt trảm thần thú và sự kiện thành bảng chuẩn hóa bao gồm 12 thực thể: Trảm Long Chiêu, Phù Long Trảm, Thần Thú Sát Kỹ, Phá Tiên Thuật, Hàng Long Phục Hổ Kỹ, Ma Diệt Trận, Thất Sát Trảm Tinh, Thất Tinh Đăng Minh, Trấn Ma Phù, Tinh Thuật Sát, Phá Thần Kích, Diệt Ma Trận.

Yêu cầu đầu ra:
1. Xuất dữ liệu BẢNG MARKDOWN nghiêm ngặt. TUYỆT ĐỐI KHÔNG có văn xuôi, lời mở đầu hay giải thích giáo điều.
2. Các cột trong bảng: ID Kỹ Năng, Tên Kỹ Năng, Sát Thương Thưởng Thần Thú/Ma Tướng, Tiêu Hao MP, Hiệu Ứng Sự Kiện, Node ID Knowledge Graph.
3. Đạt định nghĩa hoàn thành: 'Đúng bảng Markdown, không bỏ sót bất kỳ thực thể nào' và 'Mapping thành công mối quan hệ Kỹ Năng - Thần Thú vào Knowledge Graph Schema'.

**Bài tập:**
- Thiết kế Knowledge Graph Schema thể hiện mối quan hệ giữa Kỹ Năng Săn Thú và các loại Thần Thú (Thanh Long, Bạch Hổ, Chu Tước, Huyền Vũ).
- Viết truy vấn SPARQL/Cypher để lọc ra toàn bộ kỹ năng có thưởng sát thương lớn hơn 200% đối với Ma Tướng.

**Tags:**
#tram_long_chieu #than_thu_sat #san_thu_than #tran_ma_phu #knowledge_map_schema

---

## Day 117 — Bóc Tách & Chuẩn Hóa Dữ Liệu Võ Tướng Kỹ (Đao Pháp, Kiếm Khí & Bát Quái Cửu Cung)
**Prompt:**
Hãy trích xuất, giải mã font và chuẩn hóa dữ liệu cho 15 Võ Tướng Kỹ (thuộc nhóm Đao Pháp, Kiếm Khí, Bát Quái Cửu Cung) từ file cấu hình game.

Yêu cầu đầu ra:
1. Xuất dữ liệu theo dạng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay lối viết giảng giải.
2. Các cột trong bảng: Skill ID, Tên Võ Tướng Kỹ (UTF-8), Mã Gốc (Big5/GBK), Yêu Cầu Võ/Trí, Tiêu Tốn MP, Thời Gian Hồi Chiêu, Chỉ Số Sát Thương Ẩn, Tình Trạng Data Integrity.
3. Đảm bảo tuân thủ định nghĩa hoàn thành: 'Xuất 15 Võ Tướng Kỹ chuẩn JSON/Markdown mã UTF-8 không lỗi font' và 'Kiểm thử tính toàn vẹn dữ liệu (Data Integrity) không để trống sát thương và năng lực ẩn'.

**Bài tập:**
- Viết script Python sử dụng thư viện ftfy hoặc iconv để chuyển đổi bảng mã Big5 sang UTF-8 cho tên Võ tướng kỹ.
- Tạo script JSON Schema Validation nhằm phát hiện các bản ghi thiếu chỉ số sát thương hoặc tiêu hao MP.

**Tags:**
#vo_tuong_ky #dao_phap #kiem_khi #bat_quai #big5_encoding #json_schema

---

## Day 118 — Bóc Tách & Mô Hình Hóa Dữ Liệu Quân Sư Kỹ (Động Viên, Khóa Môn & Sĩ Khí)
**Prompt:**
Thực hiện bóc tách, làm sạch dữ liệu và lập bảng cho 15 Quân Sư Kỹ (nhóm Động Viên, Khóa Môn, Sĩ Khí).

Yêu cầu đầu ra:
1. Trình bày BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên.
2. Cấu trúc bảng gồm: ID Quân Sư Kỹ, Tên Quân Sư Kỹ, Trí Tuệ Tối Thiểu, Tiêu Tốn MP, Phạm Vi Tác Động, Hiệu Ứng Sĩ Khí/Khóa Môn, Trạng Thái Pydantic Cleaned, Foreign Key Integrity (Kỹ Năng - Binh Sĩ).
3. Đáp ứng định nghĩa hoàn thành: 'Bảng dữ liệu 15 Quân Sư Kỹ hoàn chỉnh với điều kiện Trí tuệ và năng lực ẩn' và 'Xác minh Foreign Key Integrity giữa Quân Sư Kỹ và hiệu ứng tác động binh sĩ'.

**Bài tập:**
- Xây dựng Pydantic Model trong Python để validate dữ liệu Quân sư kỹ từ file INI thô.
- Viết hàm kiểm tra toàn vẹn khóa ngoại (Foreign Key) kết nối giữa Quân sư kỹ và bảng trạng thái Sĩ khí binh sĩ.

**Tags:**
#quan_su_ky #si_khi #khoa_mon #dong_vien #etl_pipeline #pydantic

---

## Day 119 — Bóc Tách & Tích Hợp Đồ Thị Tuyệt Kỹ Hợp Thể & Đặc Tính Triệu Hóa
**Prompt:**
Bóc tách và tích hợp đồ thị dữ liệu cho 15 Tuyệt Kỹ Hợp Thể & Đặc Tính Triệu Hóa (bao gồm Sơn Hà Xã Tắc, Long Phụng Hòa Minh và các kỹ năng liên quan).

Yêu cầu đầu ra:
1. Kết quả phải là BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG chứa văn xuôi hay lời dẫn giải dông dài.
2. Bảng bao gồm các cột: ID Hợp Kỹ, Tên Hợp Kỹ/Đặc Tính, Danh Sách Tướng Yêu Cầu (Graph Node IDs), Điều Kiện Kích Hoạt Đa Tướng, Hiệu Ứng Triệu Hóa/Sát Thương, Graph Schema Status, API JSON Export Status.
3. Đảm bảo đạt tiêu chí hoàn thành: 'Xây dựng thành công đồ thị tri thức liên kết các Võ tướng điều kiện để thi triển Tuyệt kỹ hợp thể' và 'Đóng gói dữ liệu bóc tách thành JSON Schema sẵn sàng cho việc truy vấn API'.

**Bài tập:**
- Xây dựng truy vấn Neo4j/Cypher để biểu diễn mối quan hệ giữa danh sách Võ tướng và Tuyệt kỹ Sơn Hà Xã Tắc.
- Đóng gói dữ liệu 15 Tuyệt kỹ hợp thể thành JSON Schema chuẩn RESTful API.

**Tags:**
#tuyet_ky_hop_the #dac_tinh_trieu_hoa #son_ha_xa_tac #knowledge_graph #data_validation

---

## Day 120 — Bóc Tách & Chuẩn Hóa Tọa Độ Thành Trì Trung Nguyên (Game Data Parsing & Big5 Encoding)
**Prompt:**
Trích xuất, giải mã Big5/GBK và chuẩn hóa tọa độ cùng chỉ số phòng thủ của 15 thành trì/cửa ải Trung Nguyên (bao gồm Lạc Dương, Hứa Xương, Hổ Lao Quan,...).

Yêu cầu đầu ra:
1. Trả về BẢNG MARKDOWN nghiêm ngặt. TUYỆT ĐỐI KHÔNG dùng văn xuôi hay đoạn văn hướng dẫn.
2. Cột bảng gồm: ID Thành Trì, Tên Thành Trì/Cửa Ải (UTF-8), Tọa Độ X, Tọa Độ Y, Quy Mô/Cấp Độ, Chỉ Số Phòng Thủ, Quân Số Đồn Trú Mặc Định, Tuyến Đường Liên Kết, Data Integrity Check.
3. Đảm bảo đạt định nghĩa hoàn thành: 'Bảng JSON/Markdown đầy đủ 15 thành trì với tọa độ chuẩn hóa UTF-8' và 'Kiểm thử Data Integrity và mối quan hệ liên kết tuyến đường'.

**Bài tập:**
- Viết script giải mã tọa độ và chỉ số phòng thủ của Lạc Dương, Hứa Xương, Hổ Lao Quan từ file .INI mã hóa Big5 sang UTF-8.
- Xây dựng Graph Data Model kết nối tọa độ và các tuyến đường nối giữa 15 thành trì Trung Nguyên.

**Tags:**
#thanh_tri_trung_nguyen #ho_lao_quan #lac_duong #toa_do_ban_do #big5_decoding #json_schema

---

## Day 121 — Bóc Tách Dữ Liệu Bến Tàu & Thủy Lộ Giang Đông - Kinh Châu (Data Extraction & Validation)
**Prompt:**
Trích xuất và kiểm thử dữ liệu 15 bến tàu và thành trì thủy lộ bao gồm Kiến Nghiệp, Xích Bích, Giang Lăng từ file cấu hình game Sango Heroes 7. Hãy lập bảng dữ liệu chi tiết xác định tọa độ, độ sâu thủy lộ, khả năng đóng các chiến thuyền (Mông Xung, Tẩu Báo, Lâu Thuyền) và liên kết ID bến tàu với ID binh chủng thủy quân để xác minh tính toàn vẹn khóa ngoại (Foreign Key Integrity). Yêu cầu xuất kết quả theo định dạng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay lời giải thích dẫn dắt.

**Bài tập:**
- Trích xuất danh sách 15 bến tàu thủy lộ Giang Đông - Kinh Châu cùng tọa độ và đặc tính chiến thuyền
- Viết script Python Pandas kiểm tra Foreign Key Integrity giữa ID bến tàu và ID chiến thuyền
- Tổng hợp bảng Markdown dữ liệu bến tàu và tuyến đường thủy liên kết

**Tags:**
#ben_tau_xich_bich #kien_nghiep #giang_dong #thuy_lo_kinh_chau #data_validation #foreign_key_integrity

---

## Day 122 — Bóc Tách Tháp Thử Thách & Tiên Động Luân Hồi (Ontology Mapping & Event Data)
**Prompt:**
Trích xuất cấu trúc dữ liệu 12 tháp thử thách và tiên động bao gồm Bồng Lai, Tử Sương, Ngọc Hư Cung từ file cấu hình game. Lập bảng mô hình hóa mối quan hệ giữa tiên động với danh sách Boss tiên nhân (chỉ số HP/MP, kỹ năng), điều kiện kích hoạt, thời gian xuất hiện và phần thưởng rớt ra để xây dựng Knowledge Graph Schema. Yêu cầu xuất kết quả dưới dạng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên.

**Bài tập:**
- Bóc tách thuộc tính tọa độ ẩn, thời gian xuất hiện và điều kiện mở của 12 tháp thử thách / tiên động
- Trích xuất chỉ số HP/MP, kỹ năng của Boss tiên nhân và danh sách item rơi tương ứng
- Lập bảng Ontology Mapping kết nối Tiên nhân - Phần thưởng - Điều kiện kích hoạt

**Tags:**
#thap_thu_thach #bong_lai_tien_dao #tien_dong #tu_suong_tien_dong #ontology_mapping #knowledge_graph

---

## Day 123 — Bóc Tách Hang Động & Mộ Cổ Săn Thần Khí (Drop Rate Analysis & ETL Parsing)
**Prompt:**
Bóc tách dữ liệu 15 hang động và mộ cổ bao gồm Tần Hoàng Lăng, Chu Tước Cốc, Huyền Vũ Cung từ CSDL game. Lập bảng danh sách hang động, yêu cầu cấp độ/mật khẩu, Boss quái vật canh giữ và bảng tỷ lệ rớt bảo vật/thần khí (Drop Table) đã qua xử lý làm sạch dữ liệu null/rác bằng Python ETL script. Yêu cầu trả về BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG sử dụng văn xuôi hay đoạn văn giải thích.

**Bài tập:**
- Trích xuất tọa độ và điều kiện truy cập 15 hang động & mộ cổ
- Viết kịch bản Python ETL làm sạch bảng Drop Table rớt thần khí tại Tần Hoàng Lăng và Chu Tước Cốc
- Xuất bảng dữ liệu chuẩn hóa về Boss canh giữ và tỷ lệ rớt bảo vật

**Tags:**
#tan_hoang_lang #chu_tuoc_coc #huyen_vu_cung #san_than_khi #drop_table #etl_pipeline

---

## Day 124 — Bóc Tách Địa Điểm Ẩn Biên Thùy & Đảo Quốc Ngoại Bang (Graph Integration & Data Consolidation)
**Prompt:**
Trích xuất dữ liệu 14 địa điểm ẩn và doanh trại dị tộc bao gồm Nhật Bản Doanh, Hung Nô, Nam Man Đại Doanh. Lập bảng thông tin chi tiết về tọa độ, tướng dị tộc đồn trú, đặc sản ngoại bang và điều kiện giao thương để tích hợp vào Knowledge Map CSDL đồ thị toàn bộ Phase Bản đồ. Yêu cầu xuất kết quả bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giảng dạy.

**Bài tập:**
- Bóc tách danh sách 14 địa điểm ẩn ngoại bang cùng thông tin tướng đồn trú và đặc sản
- Kiểm tra tính nhất quán dữ liệu kết nối giữa thành trì, bến tàu, hang động và doanh trại dị tộc
- Tích hợp toàn bộ bản đồ vào CSDL Đồ thị Knowledge Map

**Tags:**
#dia_diem_an #bien_thuy #nhat_ban_doanh #nam_man_dai_doanh #knowledge_map #data_integration

---

## Day 125 — Bóc Tách Thành Trì & Cửa Ải Khu Vực Tây Bắc & Tây Lương
**Prompt:**
Trích xuất tọa độ bản đồ X-Y, độ phòng thủ, quái gác và tài nguyên của 15 thành trì và cửa ải khu vực Tây Bắc & Tây Lương (Trường An, Lạc Dương, Lương Châu, Đồng Quan, Hổ Lao Quan, Hàm Cốc Quan) từ file cấu hình .INI/.PAK. Tiến hành chuyển đổi mã font Big5/GBK sang UTF-8 và lập bảng mô hình hóa mối quan hệ địa lý giữa các thực thể. Yêu cầu trả về BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG chứa văn xuôi hay lời giải thích.

**Bài tập:**
- Viết script Python decode dữ liệu bản đồ từ bảng mã Big5/GBK sang UTF-8
- Bóc tách tọa độ X-Y và chỉ số phòng thủ của 15 thành trì/cửa ải khu vực Tây Bắc & Tây Lương
- Lập bảng kết nối vị trí địa lý giữa cửa ải Hổ Lao, Đồng Quan và các thành trì lân cận

**Tags:**
#truong_an #ho_lao_quan #tay_luong #toa_do_thanh_tri #big5_encoding #map_schema

---

## Day 126 — Bóc Tách Thành Trì & Cửa Ải Khu Vực Hà Bắc & Liêu Đông
**Prompt:**
Trích xuất tọa độ, đặc tính quân sự và tài nguyên của 15 thực thể thành trì và cửa ải Hà Bắc - Liêu Đông (Nghiệp Quận, Bình Nguyên, Tấn Dương, Tương Bình...). Xây dựng Data Pipeline kiểm thử bằng Pydantic Validator nhằm bảo đảm 100% tính toàn vẹn khóa ngoại (Foreign Key) giữa các cửa ải và thành trì liên quan. Yêu cầu xuất kết quả dưới dạng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi.

**Bài tập:**
- Trích xuất dữ liệu tọa độ, quái/bảo vật tại Nghiệp Quận, Bình Nguyên, Tấn Dương, Tương Bình
- Xây dựng Pydantic Validator kiểm tra ràng buộc khóa ngoại giữa cửa ải và thành trì Hà Bắc
- Tổng hợp bảng dữ liệu đã làm sạch và chuẩn hóa vào CSDL Đồ thị

**Tags:**
#ha_bac #liao_dong #nghiep_quan #cua_ai_ha_bac #data_pipeline #pydantic_validation

---

## Day 127 — Bóc Tách Thành Trì, Cửa Ải & Bến Tàu Khu Vực Ba Thục & Nam Trung
**Prompt:**
Trích xuất tọa độ, độ phòng thủ và mạng lưới giao thông thủy-bộ cho 15 thực thể thành trì, cửa ải và bến tàu khu vực Ba Thục & Nam Trung (Thành Đô, Giang Châu, Vân Nam, cửa ải Bạch Thủy, Giang Dầu, bến tàu Lạc Bàn, Chu Đề, Quả Khẩu). Lập bảng mô hình hóa mối liên kết địa lý và tích hợp vào Knowledge Graph Schema. Yêu cầu xuất kết quả bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay lối viết dẫn dắt.

**Bài tập:**
- Trích xuất tọa độ X-Y và thông tin phòng thủ các thành Thành Đô, Giang Châu, Vân Nam và cửa ải Bạch Thủy
- Mô hình hóa tuyến đường thủy kết nối các bến tàu Lạc Bàn, Chu Đề, Quả Khẩu
- Xây dựng bảng Spatial Mapping tích hợp mạng lưới Ba Thục - Nam Trung vào Knowledge Graph

**Tags:**
#ba_thuc #nam_trung #ben_tau_thuc #thanh_do #knowledge_graph #spatial_mapping

---

## Day 128 — Bóc Tách Hang Động, Mộ Cổ & Địa Điểm Ẩn Vùng Nam Man & Tây Vực
**Prompt:**
Trích xuất tọa độ kích hoạt, điều kiện mở khóa và bảng vật phẩm/thần khí rớt ra từ 15 địa điểm ẩn vùng Nam Man & Tây Vực (Mạn Động, Thú Thần Động, Độc Long Động, Mộ Cổ Vu Hàm...). Viết kịch bản Unit Test bằng Pytest kiểm định tính toàn vẹn tham chiếu 100% giữa Item ID rớt ra và CSDL trang bị. Yêu cầu trả về BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG có văn xuôi hay văn phong giáo viên.

**Bài tập:**
- Bóc tách tọa độ và điều kiện mở cửa Mạn Động, Thú Thần Động, Độc Long Động, Mộ Cổ Vu Hàm
- Trích xuất danh sách thần khí rơi cùng tỷ lệ rớt đồ từ file cấu hình sự kiện
- Viết test case Pytest xác minh 100% Item ID từ địa điểm ẩn tồn tại trong CSDL trang bị

**Tags:**
#man_dong #mo_co_nam_man #doc_long_dong #do_than_khi #unit_test_data #hidden_location_schema

---

## Day 129 — Bóc Tách Tiên Động, Tháp Thử Thách & Điểm Ẩn Rơi Thần Khí Vùng Biển Đảo
**Prompt:**
Yêu cầu xây dựng nội dung bách khoa toàn thư bóc tách dữ liệu Biển Đảo và Tiên Động trong Sango Heroes 7. Liệt kê và phân tích chi tiết các thực thể: Bồng Lai Tiên Động, Tam Hồn Tháp, Long Cung Thủy Phủ, Phù Tang Cung cùng đủ 15 thực thể biển đảo và tiên động, thiết lập quy trình đóng gói pipeline xuất RESTful API cho toàn bộ dữ liệu Bản Đồ. Yêu cầu trình bày hoàn toàn bằng BẢNG MARKDOWN nghiêm ngặt, tuyệt đối không dùng văn xuôi, không sử dụng văn phong giáo viên, không trình bày lý thuyết tổng quát, không chứa bất kỳ dòng tiêu đề nào bắt đầu bằng '## Day'.

**Bài tập:**
- Viết script Python trích xuất tọa độ và tỷ lệ rơi thần khí tại Bồng Lai Tiên Động và Tam Hồn Tháp.
- Xây dựng JSON Schema kiểm định đủ 15 thực thể biển đảo và đóng gói RESTful API.

**Tags:**
#bonglaitiendong #tamhonthap #longcungthuyphu #restful_api #sango7

---

## Day 130 — Bóc Tách & Chuẩn Hóa Dữ Liệu Tọa Độ Cửa Ải, Bến Tàu & Điểm Kiểm Soát Tuyến Đường Trận Đồ
**Prompt:**
Yêu cầu tạo nội dung bách khoa toàn thư về bóc tách và chuẩn hóa tọa độ cửa ải, bến tàu Tam Quốc. Phân tích chi tiết 15 cửa ải/bến tàu trọng điểm, tọa độ X, Y, quân đồn trú, thuộc tính phòng thủ, giải mã mã hóa Big5/GBK sang UTF-8 không lỗi font bằng Pydantic và Pandas, và nạp vào Spatial Graph Database. Yêu cầu xuất kết quả hoàn toàn dưới dạng BẢNG MARKDOWN nghiêm ngặt, tuyệt đối không dùng văn xuôi hay văn phong giáo viên, không giải thích lý thuyết chung chung, không viết tiêu đề '## Day'.

**Bài tập:**
- Viết script Python giải mã bảng mã Big5/GBK sang UTF-8 cho dữ liệu 15 cửa ải và bến tàu.
- Tạo kịch bản Data Integrity Check kiểm tra tọa độ (X, Y) và chuẩn hóa dữ liệu với Pydantic.

**Tags:**
#toado_cuagai #bentau_tamquoc #big5_utf8 #pydantic #spatial_graph

---

## Day 131 — Bóc Tách Cơ Chế Kinh Tế, Tài Chính & Thiết Kế Schema Dữ Liệu Kinh Tế Game
**Prompt:**
Yêu cầu lập bách khoa toàn thư bóc tách cơ chế kinh tế và tài chính game. Trích xuất và mô hình hóa dữ liệu từ Chợ, Mộ Cổ, Thu Thuế, Đấu Giá, Tế Lễ Chiêu Tài thành JSON Schema và CSDL quan hệ, xử lý chuyển đổi mã font Big5/GBK sang UTF-8 không lỗi font. Yêu cầu trình bày duy nhất bằng BẢNG MARKDOWN nghiêm ngặt, tuyệt đối không văn xuôi, không dùng lời giảng giáo viên, không đưa lý thuyết tổng quát, không chứa dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Thiết kế JSON Schema mô hình hóa các thực thể tài chính như Chợ, Mộ Cổ, Thu Thuế, Đấu Giá.
- Viết script làm sạch dữ liệu rác và mã hóa UTF-8 cho hệ thống kinh tế trong game.

**Tags:**
#kinh_te_game #json_schema #big5_utf8 #data_pipeline #sango7

---

## Day 132 — Trích Xuất Cơ Chế Bắt Tướng, Chiêu Hàng & Xây Dựng Knowledge Graph Mapping
**Prompt:**
Yêu cầu xây dựng bách khoa toàn thư bóc tách cơ chế bắt tướng và chiêu hàng. Phân tích mô hình Graph Schema (Node-Relationship) kết nối Tướng, Tù Binh, Tình Duyên, Mẹo Bắt Tướng bao gồm Bẫy Hạc Vong, Trụ Phược và Tỷ Lệ Chiêu Hàng, đồng thời kiểm tra Foreign Key Integrity. Bắt buộc xuất kết quả dưới dạng BẢNG MARKDOWN nghiêm ngặt, tuyệt đối không dùng văn xuôi hay văn phong giáo viên, không nêu lý thuyết tổng quát, không có dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Xây dựng Cypher script tạo Graph Schema biểu diễn mối quan hệ giữa Tướng, Bẫy Hạc Vong và Tỷ Lệ Chiêu Hàng.
- Viết kịch bản kiểm thử Foreign Key Integrity giữa ID Tướng và ID Tù Binh.

**Tags:**
#bat_tuong #chieu_hang #knowledge_graph #bay_hac_vong #cypher

---

## Day 133 — Bóc Tách Cơ Chế Ép Cấp, Cày EXP & Xây Dựng Logic Module Tính EXP Tự Động
**Prompt:**
Yêu cầu lập bách khoa toàn thư bóc tách cơ chế ép cấp và cày EXP. Phân tích chi tiết công thức tăng EXP từ Thủ Thành Cừu Sát, Hang Động Thần Thú, Ép Cấp Tướng Phụ, lập trình Module Python tính toán EXP/Level Up chuẩn 3NF và Pydantic validation. Bắt buộc trình bày bằng BẢNG MARKDOWN nghiêm ngặt, tuyệt đối không dùng văn xuôi, không dùng lời giảng sư phạm, không viết lý thuyết chung chung, không tạo tiêu đề '## Day'.

**Bài tập:**
- Xây dựng Module Python Pydantic tính toán EXP nhận được dựa trên công thức bóc tách.
- Viết các bài Unit Test kiểm định tính chính xác của công thức cày EXP so với ingame.

**Tags:**
#ep_cap #cay_exp #pydantic #unit_test #exp_calculator

---

## Day 134 — Bóc Tách Ảnh Hưởng Thời Tiết, Địa Hình & Xây Dựng Environment Modifier Matrix
**Prompt:**
Yêu cầu lập bách khoa toàn thư bóc tách ảnh hưởng thời tiết và địa hình. Xây dựng Environment Modifier Matrix cho các yếu tố Mưa, Tuyết, Phong, Đầm Lầy, Núi tác động tới binh chủng và kỹ năng, chuẩn hóa dữ liệu 3NF dạng JSON/CSV và xử lý các Undocumented IDs (ID ẩn). Yêu cầu trình bày hoàn toàn bằng BẢNG MARKDOWN nghiêm ngặt, tuyệt đối không dùng văn xuôi, không dùng văn phong giáo viên, không trình bày lý thuyết tổng quát, không chứa tiêu đề '## Day'.

**Bài tập:**
- Tạo ma trận Modifier Matrix dạng NumPy/Pandas thể hiện tác động của Tuyết và Đầm Lầy lên binh chủng.
- Viết kịch bản validation quét và unmask các Undocumented IDs thuộc hệ thống thời tiết.

**Tags:**
#thoi_tiet #dia_hinh #modifier_matrix #data_validation #undocumented_id

---

## Day 135 — Bóc Tách Sự Kiện Lịch Sử & Đóng Gói Full Knowledge Graph Pipeline Cho Phase
**Prompt:**
Yêu cầu tạo bách khoa toàn thư bóc tách các sự kiện lịch sử và biến cố. Chi tiết hóa điều kiện kích hoạt Event/Trigger Lịch Sử gồm Tam Cố Thảo Lư, Xích Bích, Thiên Tai, đóng gói Knowledge Graph Data Pipeline thành JSON-LD / Cypher Script và tích hợp RESTful API. Yêu cầu xuất kết quả hoàn toàn dưới dạng BẢNG MARKDOWN nghiêm ngặt, tuyệt đối không dùng văn xuôi, không văn phong giáo viên, không lý thuyết tổng quát, không có tiêu đề bắt đầu bằng '## Day'.

**Bài tập:**
- Mô hình hóa sự kiện Tam Cố Thảo Lư và Xích Bích bằng JSON Schema / Event-Driven State Machine.
- Viết pipeline xuất Knowledge Graph sang định dạng Cypher Script và đóng gói RESTful API.

**Tags:**
#su_kien_lich_su #tam_co_thao_lu #xich_bich #knowledge_graph #rest_api

---

## Day 136 — Kiếm Tiền Nhanh, Bán Đồ Cao Cấp & Khai Thác Mỏ Vàng (Xử Lý Bảng Mã Big5/GBK & Chuẩn Hóa Data)
**Prompt:**
Yêu cầu tạo bách khoa toàn thư bóc tách cơ chế giao thương và kinh tế. Trích xuất và chuẩn hóa mã font GBK/Big5 sang UTF-8 cho các thực thể: Hoàng Kim Thiềm Thừ, Bán Vũ Khí Cấp Cao, Thuế Thành Trì Lạc Dương, Thuế Thành Trì Hứa Xương, Giao Thương Chợ Kiến Nghiệp, Đấu Giá Bảo Vật, Thu Thập Kim Tiền, Đổi Binh Phù Lấy Tiền, Khai Thác Mỏ Vàng Thục Sơn, Bán Thuốc Tăng Chỉ Số, Điểm Mua Bán Tây Vực, Bán Đồ Hàng Cấp Thần, Khai Thác Báo Vật Mộ Cổ. Yêu cầu trình bày bằng BẢNG MARKDOWN nghiêm ngặt, tuyệt đối không dùng văn xuôi hay văn phong giáo viên, không nêu lý thuyết tổng quát, không viết tiêu đề '## Day'.

**Bài tập:**
- Viết kịch bản Python giải mã font GBK/Big5 sang UTF-8 cho danh sách thực thể kinh tế.
- Xây dựng bảng chuẩn hóa dữ liệu tài chính cho các thành trì Lạc Dương, Hứa Xương, Kiến Nghiệp.

**Tags:**
#hoang_kim_thiem_thu #mo_vang_thuc_son #lac_duong #big5_utf8 #giao_thuong

---

## Day 137 — Mẹo Lừa Bắt Tướng 100%, Chiêu Hàng Võ Tướng & Tù Binh (Xây Dựng Rule Validation)
**Prompt:**
Trình bày hệ thống Bách khoa toàn thư bóc tách cơ chế game và logic validation dữ liệu cho các mẹo bắt tướng và chiêu hàng. Yêu cầu trả lời BẮT BUỘC dưới dạng BẢNG MARKDOWN NGHIÊM NGẶT, KHÔNG sử dụng văn xuôi, KHÔNG dùng văn phong giáo viên, KHÔNG viết dòng heading '## Day'. Hãy phân tích chi tiết các thực thể và quy tắc trong dự án: 'Quân Sư Kỹ Bắt Tướng', 'Dùng Bẫy Hạc Dụ Tướng', 'Ép Tướng Vào Góc Bản Đồ', 'Dùng Quân Sư Kỹ Thuyết Phục', 'Bắt Tướng Lữ Bố', 'Bắt Tướng Quan Vũ', 'Bắt Tướng Gia Cát Lượng', 'Chiêu Hàng Tù Binh Trung Thành High', 'Dùng Bảo Vật Chiêu Tẩy', 'Chiêu Hàng Tướng Nhất Quyết Không Phục', 'Giảm Sĩ Khí Để Bắt Tướng', 'Độc Hành Bắt Tướng', 'Thủ Thuật Giữ Tù Binh Không Trốn'. Lập bộ quy tắc Pydantic Data Validation đảm bảo tính chính xác của tỷ lệ chiêu hàng và giữ tù binh.

**Bài tập:**
- Trích xuất tham số sĩ khí, trung thành và lập bảng Markdown cho 13 thực thể bắt tướng.
- Viết Schema Pydantic bằng Python kiểm định điều kiện tỷ lệ chiêu hàng tù binh.
- Thiết lập thuật toán kiểm tra logic không cho tù binh trốn thoát dựa vào bảo vật và vị trí.

**Tags:**
#bat_tuong #chieu_hang #pydantic #data_validation #logic_game

---

## Day 138 — Cơ Chế Ép Cấp, Cày EXP Siêu Tốc & Nâng Cấp Tướng (Xây Dựng Công Thức Ma Trận EXP)
**Prompt:**
Trình bày Bách khoa toàn thư về cơ chế ép cấp và ma trận công thức tính EXP trong game. Yêu cầu trả lời BẮT BUỘC bằng BẢNG MARKDOWN NGHIÊM NGẶT, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay lời giải thích văn tự, KHÔNG tạo tiêu đề '## Day'. Bảng dữ liệu phải phủ toàn bộ các thực thể: 'Đánh Hang Mộc Nhân Cày EXP', 'Đánh Tháp Thử Thách Cày Cấp', 'Dùng Bảo Vật Tăng EXP', 'Cày Level Với Đội Quân Lính Cát', 'Thủ Thuật Ép Cấp Tướng Trẻ', 'Ép Cấp Cho Mưu Sĩ', 'Cày Cấp Bằng Hợp Thể Kỹ', 'Đòn Sát Thương Diện Rộng Cày EXP', 'Cày Cấp Tại Thủy Động', 'Cày Cấp Tại Nam Man', 'Cày Cấp Tiên Động', 'Ép Cấp Tướng Mới Chiêu Mộ', 'Tối Ưu EXP Trận Đánh'. Xây dựng công thức toán học ma trận EXP cho truy vấn tự động.

**Bài tập:**
- Thống kê toàn bộ địa điểm cày EXP và hệ số thưởng vào bảng Markdown chuẩn.
- Viết script Python tính toán ma trận đường cong EXP từ cấp 1 đến cấp 99.
- Lập bảng quy đổi hệ số nhân kinh nghiệm khi sử dụng Bảo Vật Tăng EXP và Hợp Thể Kỹ.

**Tags:**
#ep_cap #cay_exp #ma_tran_exp #game_mechanics #python_script

---

## Day 139 — Ảnh Hưởng Thời Tiết, Địa Hình & Khí Tượng Trận Đồ (Mô Hình Hóa Đồ Thị Tương Tác)
**Prompt:**
Tổng hợp tài liệu Bách khoa toàn thư về mạng lưới tương tác giữa thời tiết và địa hình chiến trường. Yêu cầu xuất dữ liệu HOÀN TOÀN bằng BẢNG MARKDOWN, KHÔNG văn xuôi diễn giải, KHÔNG heading '## Day'. Lập ma trận thuộc tính cho các thực thể khí tượng và địa hình: 'Thời Tiết Mưa Rào', 'Thời Tiết Tuyết Rơi', 'Thời Tiết Sương Mù', 'Thời Tiết Nắng Bão', 'Địa Hình Tuyết Sơn', 'Địa Hình Đầm Lầy', 'Địa Hình Đồi Núi', 'Địa Hình Đồng Bằng', 'Địa Hình Sông Nước', 'Quân Sư Kỹ Hô Phong Hoán Vũ', 'Quân Sư Kỹ Đổi Khí Tượng', 'Giảm Tốc Độ Di Chuyển Do Lầy', 'Tăng Tốc Độ Khi Nắng', 'Giảm Tầm Nhìn Sương Mù', 'Tăng Sát Thương Hỏa Ký Khi Nắng'. Định nghĩa cấu trúc Graph Schema (Nodes & Edges) thể hiện tác động môi trường.

**Bài tập:**
- Xây dựng bảng Markdown ma trận tăng/giảm chỉ số di chuyển, tầm nhìn và sát thương.
- Thiết kế cấu trúc Graph Schema (JSON-LD / Neo4j Nodes & Edges) cho hệ thống thời tiết - địa hình.
- Truy vấn quan hệ giữa Quân Sư Kỹ Đổi Khí Tượng và hiệu ứng sát thương hỏa kỹ.

**Tags:**
#thoi_tiet #dia_hinh #graph_schema #knowledge_graph #chien_truong

---

## Day 140 — Sự Kiện Lịch Sử, Biến Cố Ngẫu Nhiên & Lễ Hội Vương Quốc (Xây Dựng REST API Tra Cứu)
**Prompt:**
Xây dựng Bách khoa toàn thư đóng gói chuỗi sự kiện lịch sử, biến cố ngẫu nhiên và lễ hội vương quốc dưới dạng REST API. Yêu cầu trả lời BẮT BUỘC bằng BẢNG MARKDOWN NGHIÊM NGẶT, KHÔNG văn xuôi, KHÔNG heading '## Day'. Trích xuất 100% dữ liệu thực thể: 'Sự Kiện Tam Cố Thảo Lư', 'Sự Kiện Trận Xích Bích', 'Sự Kiện Đào Viên Kết Nghĩa', 'Biến Cố Dịch Bệnh Thành Trì', 'Biến Cố Thiên Tai Lũ Lụt', 'Biến Cố Nông Dân Nổi Dậy', 'Lễ Hội Tấn Công Thần Thú', 'Sự Kiện Thương Nhân Ghé Thăm', 'Biến Cố Giặc Khăn Vàng Xuất Hiện', 'Sự Kiện Hoàng Đế Ban Thưởng', 'Lễ Hội Thi Võ Toàn Quốc', 'Lễ Hội Tác Chiến Dị Tộc', 'Biến Cố Tướng Lĩnh Phản Bội'. Cung cấp bảng thiết kế REST API Endpoint (FastAPI) trả về JSON Schema chuẩn.

**Bài tập:**
- Lập bảng Markdown quy định điều kiện kích hoạt, thời gian và phần thưởng của 13 sự kiện.
- Viết mô hình Pydantic Schema cho response của REST API tra cứu sự kiện.
- Xây dựng FastAPI Endpoint /api/v1/events/search hỗ trợ lọc theo loại sự kiện và biến cố.

**Tags:**
#su_kien_lich_su #bien_co #rest_api #fastapi #json_schema

---

## Day 141 — Bóc Tách Cơ Chế Tài Chính, Thu Thuế, Thương Mại & Cướp Bóc Bán Đồ
**Prompt:**
Trích xuất và thiết kế Bách khoa toàn thư cho cơ chế tài chính, thu thuế, thương mại và cướp bóc trong game từ tệp cấu hình .INI/BFI. Yêu cầu trả lời BẮT BUỘC bằng BẢNG MARKDOWN NGHIÊM NGẶT, KHÔNG văn xuôi, KHÔNG heading '## Day'. Tổng hợp bảng thuộc tính các thực thể kinh tế bao gồm 'Thuế', 'Giao Thương', 'Mỏ Vàng', 'Chợ Đen'. Mô tả quy trình mã hóa font từ Big5/GBK sang UTF-8 và thiết kế Data Pipeline lưu trữ vào Knowledge Graph Schema.

**Bài tập:**
- Tạo bảng Markdown trích xuất công thức tính thuế và tỷ lệ giao thương từ file cấu hình game.
- Viết hàm Python tự động chuyển đổi bảng mã ký tự Big5/GBK sang UTF-8 cho tên thực thể.
- Thiết kế Pydantic Schema và Data Pipeline đẩy dữ liệu tài chính đã chuẩn hóa vào Database.

**Tags:**
#tai_chinh #thu_thue #giao_thuong #encoding_big5 #data_pipeline

---

## Day 142 — Bóc Tách Mẹo Bắt Tướng 100%, Chiêu Hàng Tù Binh & Giảm Trung Thành
**Prompt:**
Bóc tách cơ chế bắt tướng 100%, chiêu hàng tù binh và giảm trung thành để đưa vào Bách khoa toàn thư. Yêu cầu BẮT BUỘC xuất ra BẢNG MARKDOWN NGHIÊM NGẶT, KHÔNG viết văn xuôi hay nhận xét, KHÔNG dùng heading '## Day'. Lập bảng công thức tính tỷ lệ chiêu hàng dựa trên Võ/Trí của quân sư, mức giảm trung thành mỗi lượt. Viết kịch bản Automated Data Validation (Unit Test) kiểm tra tính toàn vẹn dữ liệu (Data Integrity) ràng buộc mối quan hệ giữa ID Tướng và ID Tù binh.

**Bài tập:**
- Lập bảng Markdown chi tiết về các tham số giảm trung thành tù binh và tỷ lệ dụ địch thành công.
- Xây dựng bảng Relational Mapping nối chỉ số quân sư với xác suất chiêu hàng.
- Viết Unit Test bằng pytest kiểm tra ràng buộc khóa ngoại và tính hợp lệ của ID Tướng - ID Tù Binh.

**Tags:**
#bat_tuong #chieu_hang #data_integrity #unit_test #relational_mapping

---

## Day 143 — Bóc Tách Cơ Chế Ép Cấp, Cày EXP Solo Tiên Động & Tối Ưu Cấp Độ 99
**Prompt:**
Trích xuất cơ chế ép cấp, cày EXP solo Tiên Động và tối ưu cấp độ 99 thành dữ liệu Bách khoa toàn thư. Yêu cầu trả lời BẮT BUỘC bằng BẢNG MARKDOWN NGHIÊM NGẶT, KHÔNG văn xuôi, KHÔNG tiêu đề '## Day'. Lập bảng chi tiết điểm kinh nghiệm của các địa điểm cày cấp, bùa tăng EXP, quái Tiên Động, Tháp Thử Thách. Thực hiện kỹ thuật Reverse Engineering để mô hình hóa công thức tăng cấp 1-99 và thiết kế RESTful API endpoint trả về dữ liệu JSON đường cong EXP.

**Bài tập:**
- Tạo bảng Markdown thống kê chỉ số EXP thưởng tại Tiên Động, Tháp Thử Thách và các loại bùa.
- Lập thuật toán Python đảo ngược (Reverse Engineering) mô phỏng đường cong EXP từ level 1 tới 99.
- Xây dựng RESTful API endpoint tính toán lượng EXP còn thiếu để đạt level tối đa.

**Tags:**
#ep_cap #exp_solo #tien_dong #reverse_engineering #restful_api

---

## Day 144 — Bóc Tách Tác Động Thời Tiết Khí Tượng & Địa Hình Lên Chiến Trường
**Prompt:**
Bóc tách ma trận tác động thời tiết, khí tượng và địa hình lên chiến trường để xây dựng Knowledge Graph. Yêu cầu xuất kết quả BẮT BUỘC bằng BẢNG MARKDOWN NGHIÊM NGẶT, KHÔNG văn xuôi diễn giải, KHÔNG heading '## Day'. Lập bảng ma trận hệ số cộng/trừ sát thương Hỏa/Lôi hệ, tầm bắn cung binh và tốc độ di chuyển theo điều kiện môi trường. Xây dựng sơ đồ Graph Schema trên Neo4j/NetworkX thể hiện mối quan hệ liên kết giữa Thời tiết - Địa hình - Binh chủng/Kỹ năng.

**Bài tập:**
- Lập bảng Markdown ma trận biến số thời tiết/địa hình ảnh hưởng lên các binh chủng.
- Xây dựng script Python sử dụng NetworkX / Neo4j để khởi tạo Graph Schema cho dữ liệu khí tượng.
- Thực hiện Data Normalization làm sạch và loại bỏ các biến số trùng lặp trong dữ liệu chiến trường.

**Tags:**
#thoi_tiet #khi_tuong #dia_hinh #neo4j #data_normalization

---

## Day 145 — Bóc Tách Sự Kiện Lịch Sử Kịch Bản, Thiên Tai & Biến Cố Ngẫu Nhiên
**Prompt:**
Hãy lập Bách khoa toàn thư kỹ thuật về dự án: Trích xuất thực thể sự kiện kịch bản và xây dựng bộ công cụ trực quan hóa đồ thị tri thức (Knowledge Graph Visualization). Yêu cầu đạt Definition of Done: Bảng Markdown đầy đủ thực thể biến cố, thiên tai và sự kiện lịch sử cùng Giao diện D3.js/Cytoscape.js hiển thị mạng lưới điều kiện kích hoạt sự kiện. LƯU Ý BẮT BUỘC: Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không thay thế bằng lý thuyết tổng quát, KHÔNG dùng tiêu đề bắt đầu bằng '## Day'.

**Bài tập:**
- Xây dựng parser đọc cấu trúc điều kiện IF-THEN trong file kịch bản sự kiện.
- Tích hợp thư viện Cytoscape.js để biểu diễn sơ đồ đồ thị tri thức mạng lưới điều kiện kích hoạt.
- Xuất dữ liệu bảng Markdown chi tiết về các thực thể biến cố, thiên tai và sự kiện lịch sử.

**Tags:**
#knowledge_graph #cytoscape_js #d3_js #event_parser #visualization

---

## Day 146 — Bóc Tách & Chuẩn Hóa Data Cơ Chế Kinh Tế, Buôn Bán & Kiếm Vàng Đầu Game
**Prompt:**
Hãy lập Bách khoa toàn thư kỹ thuật cho dự án: Xây dựng ETL pipeline trích xuất & chuyển đổi mã font (Big5/GBK -> UTF-8) cho các thực thể kinh tế bao gồm Mỏ Kim Sạn, Chợ Lạc Dương, Chợ Thành Đô, Chợ Kiến Nghiệp, Thuyết Khách Buôn Tiền, Tráp Bảo Kim Ngân, Hoàng Kim Châu, Thái Cực Đồ, Vận Chuyển Lương Thảo, Quỹ Quốc Tố. Sản phẩm cần hoàn thành Definition of Done: Bảng dữ liệu JSON/Markdown hoàn chỉnh đã chuyển đổi mã sang UTF-8 không đứt lỗi font, vượt qua Data Validation passed (Kiểm tra tính hợp lệ không chứa chỉ số null hoặc âm ở tỷ giá kinh tế). LƯU Ý BẮT BUỘC: Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không sử dụng lý thuyết chung chung, không viết tiêu đề dạng '## Day'.

**Bài tập:**
- Viết script Python giải mã bảng mã Big5/GBK sang UTF-8 cho các file config kinh tế.
- Tạo Pydantic Schema kiểm tra tính toàn vẹn dữ liệu giao thương, đảm bảo không có chỉ số null hoặc âm.
- Trích xuất chỉ số Võ, Trí và quy tắc đấu giá, thu thuế Mùa Xuân cho các chợ và thuyết khách.

**Tags:**
#etl_pipeline #utf8_encoding #big5_gbk #data_validation #game_economy

---

## Day 147 — Phân Tích & Mô Hình Hóa Đồ Thị Chiêu Thuật Dụ Địch & Mẹo Bắt Tướng
**Prompt:**
Hãy lập Bách khoa toàn thư kỹ thuật về: Mô hình hóa Knowledge Graph Schema kết nối điều kiện bắt tướng (Quan Vũ, Trương Phi, Gia Cát Lượng, Chu Du, Tào Tháo, Lữ Bố, Triệu Vân) với công thức tính tỷ lệ chiêu hàng và giảm sĩ khí tù binh. Phải hoàn thành Definition of Done: Mô hình đồ thị thực thể (Tướng - Cửa Ải - Mẹo Bắt - Chiêu Hàng) xuất định dạng JSON và Unit Test viết bằng PyTest xác minh thuật toán tính tỷ lệ giam giữ và phục binh đánh chặn. LƯU Ý BẮT BUỘC: Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không dùng lý thuyết tổng quát, không tạo tiêu đề bắt đầu với '## Day'.

**Bài tập:**
- Thiết kế Knowledge Graph Schema kết nối Quan Vũ, Trương Phi, Gia Cát Lượng, Chu Du, Tào Tháo, Lữ Bố, Triệu Vân với tỷ lệ chiêu hàng.
- Xây dựng Unit Test bằng PyTest kiểm tra logic tính giảm sĩ khí tù binh và phục binh đánh chặn.
- Tạo Graph Mapping liên kết chiêu thức Bố Bẫy Đa Thành, Bức Hàng Cửa Ải với tỷ lệ thoát tù binh.

**Tags:**
#knowledge_graph #pytest #capture_mechanic #unit_test #graph_mapping

---

## Day 148 — Xây Dựng Pipeline Trích Xuất & Kiểm Thử Dữ Liệu Ép Cấp, Cày EXP Tiên Động
**Prompt:**
Hãy lập Bách khoa toàn thư kỹ thuật về dự án: Trích xuất & Validation dữ liệu hang động cày EXP (Động Hổ Cung, Tiên Động Luân Hồi, Mộ Cổ Tào Tháo, Tháp 99, Quỷ Vương Cốc) và thuật toán phân bổ EXP solo. Yêu cầu đạt Definition of Done: Bảng dữ liệu EXP hang động đạt chuẩn Foreign Key Integrity giữa ID quái và ID hang động cùng Script tự động deduplication loại bỏ dữ liệu trùng lặp trong danh sách bảo vật EXP. LƯU Ý BẮT BUỘC: Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không dùng lý thuyết tổng quát, KHÔNG viết dòng heading bắt đầu bằng '## Day'.

**Bài tập:**
- Trích xuất dữ liệu chỉ số quái vật và EXP các hang động Động Hổ Cung, Tiên Động Luân Hồi, Mộ Cổ Tào Tháo, Tháp 99, Quỷ Vương Cốc.
- Viết script kiểm tra Foreign Key Integrity giữa ID quái và ID hang động.
- Xây dựng kịch bản deduplication làm sạch danh sách bảo vật EXP.

**Tags:**
#data_validation #foreign_key #deduplication #exp_farming #pytest

---

## Day 149 — Lưu Trữ & Đánh Chỉ Mục (Indexing) Ma Trận Tương Tác Thời Tiết - Địa Hình
**Prompt:**
Hãy lập Bách khoa toàn thư kỹ thuật về cụm công việc: Số hóa ma trận hiệu ứng Thời Tiết (Bão Tuyết, Mưa Lớn, Sương Mù, Bão Cát) & Địa Hình (Đầm Lầy, Lĩnh Nam, Núi Cao) vào Database có Indexing tối ưu. Phải đáp ứng Definition of Done: Cơ sở dữ liệu ma trận thời tiết - địa hình phản hồi truy vấn dưới 5ms và Bảng ánh xạ hoàn chỉnh buff/debuff binh chủng thủy chiến và hỏa công phong hướng. LƯU Ý BẮT BUỘC: Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không thay bằng lý thuyết tổng quát, tuyệt đối không có heading bắt đầu bằng '## Day'.

**Bài tập:**
- Thiết kế PostgreSQL JSONB Schema lưu ma trận hiệu ứng của Bão Tuyết, Mưa Lớn, Đầm Lầy, Lĩnh Nam.
- Tạo Database Indexing tối ưu đảm bảo truy vấn ma trận thời tiết - địa hình dưới 5ms.
- Xây dựng bảng ánh xạ buff/debuff cho binh chủng thủy chiến và hỏa công phong hướng.

**Tags:**
#database_indexing #jsonb #postgresql #weather_terrain #query_optimization

---

## Day 150 — Đóng Gói Knowledge Map & Xây Dựng RESTful API Truy Truy Vấn Sự Kiện Lịch Sử
**Prompt:**
Hãy lập Bách khoa toàn thư kỹ thuật về dự án: Xây dựng RESTful API cho phép xuất và truy vấn toàn bộ hệ thống Sự kiện lịch sử (Xích Bích, Quan Độ), Thiên tai & Knowledge Map tổng thể của game. Phải đạt tiêu chuẩn Definition of Done: Endpoint API trả về đúng cấu trúc JSON Schema chuẩn hóa cho client khai thác và File JSON Knowledge Map toàn diện của Phase được xuất thành công và kiểm thử đạt 100%. LƯU Ý BẮT BUỘC: Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên, không trình bày lý thuyết chung chung, không viết tiêu đề '## Day'.

**Bài tập:**
- Xây dựng các RESTful API Endpoint bằng FastAPI phục vụ tra cứu sự kiện Xích Bích, Quan Độ.
- Đóng gói dữ liệu toàn bộ Phase thành file JSON Knowledge Map đạt chuẩn JSON Schema.
- Viết test suite kiểm thử 100% các endpoint API tra cứu sự kiện và thiên tai.

**Tags:**
#restful_api #fastapi #json_schema #knowledge_map #history_events

---
