---
name: "Generate Roadmap"
description: "Use this skill when the user asks to create, edit, extend, or optimize a learning Roadmap file (language learning: English/Japanese/Chinese/Korean, or any other domain: IT/programming, music, business, sports, etc.) or the Python generator scripts (generate_*_roadmap.py). Covers auto-detecting difficulty and choosing cycle length (10/15/20/25-30 day cycles) when the user doesn't know the domain well, duplicate-topic and duplicate-content prevention across roadmaps via topics_registry.md, coverage-completeness checks against real-world curricula/certifications, prerequisite ordering, spaced cumulative review, a final Capstone for pro-level mastery, Non-Interactive prompt rules, Markdown parsing format for the AskCpl-style addon, and verification/encoding checks. Trigger on mentions of 'roadmap', 'lộ trình', 'sinh roadmap', 'generate_*_roadmap.py', 'chu kỳ 15 ngày' / '25 ngày', 'trùng lặp topic', 'đầy đủ nội dung', or requests to add new topics/days to an existing roadmap file."
---

# Workflow Tạo Lộ Trình (Roadmap)

Khi nhận được yêu cầu tạo hoặc cập nhật Roadmap, bạn phải thực hiện nghiêm ngặt theo quy trình sau:

1. **Phân tích yêu cầu**: Xác định thời gian học mỗi ngày (vd: 30-45 phút) và Phase. **Số ngày và độ khó KHÔNG bắt buộc người dùng phải tự biết** — nếu người dùng không chỉ định rõ, agent PHẢI tự chấm điểm độ khó bằng quy trình ở Mục 6 (Tự động xác định độ khó) rồi chọn chu kỳ tương ứng, và trình bày lại lựa chọn + lý do cho người dùng duyệt trước khi sinh roadmap.
2. **Kiểm tra trùng lặp trước khi viết**: Đối chiếu topic sắp tạo với `topics_registry.md` (xem Mục 7) để chắc chắn topic/sub-topic này chưa từng được tạo ở roadmap khác.
3. **Kiểm tra độ phủ & sắp xếp thứ tự**: Đối chiếu danh sách topic với 1 nguồn tham chiếu uy tín ngoài đời (Mục 8.1), gán `prerequisites` và sắp xếp topo (Mục 8.2), chèn Review Day định kỳ và Capstone cuối roadmap (Mục 8.3, 9.4).
4. **Viết Script sinh tự động**: TUYỆT ĐỐI KHÔNG tự viết tay/gõ phím toàn bộ file Markdown lộ trình vì nó quá dài. Bắt buộc phải viết một file Python (vd: `generate_[topic]_roadmap.py`) chứa logic vòng lặp để sinh text, tuân theo cấu trúc dữ liệu đầu vào ở Mục 7.2. **ĐẶC BIỆT LƯU Ý**: Mọi prompt sinh ra trong file script PHẢI có câu lệnh ép AI trả lời bằng tiếng Việt (ví dụ: `YÊU CẦU BẮT BUỘC: LUÔN TRẢ LỜI BẰNG TIẾNG VIỆT`), trừ khi người dùng chỉ định ngôn ngữ khác.
5. **Thực thi (Run)**: Chạy script đó để tạo file `.md`. (Lưu ý: Khi chạy trên Windows, phải thiết lập `$env:PYTHONIOENCODING="utf-8"` trước khi gọi lệnh `python` để tránh lỗi Unicode Console).
6. **Kiểm duyệt (Verify) — BẮT BUỘC đếm số, không chỉ đọc lướt**: Viết một script/đoạn kiểm tra nhanh (hoặc đếm bằng regex) để xác nhận:
   - Tổng số `## Day X` khớp đúng số ngày yêu cầu, KHÔNG thiếu/trùng Day nào (so khớp dãy số liên tục).
   - Số lượng `**Prompt:**`, `**Bài tập:**`, `**Tags:**` đều bằng đúng tổng số Day (mỗi Day phải đủ 3 khối).
   - Nếu roadmap có yêu cầu Non-Interactive Warning (Mục 4): đếm đúng số Day cần chèn cảnh báo đã được chèn đủ, đúng vị trí (thường là các Day thực hành/test).
   - Mở file bằng UTF-8 và rà soát nhanh các dấu hiệu lỗi encoding kinh điển: chuỗi mojibake như `Ã`, `â€`, `Â` xuất hiện thay cho dấu tiếng Việt/ký tự đặc biệt — đây là dấu hiệu file bị lỗi encode giống lỗi đã từng gặp ở `session.json` (Giai đoạn 45 trong ProjectLog).
   - Ghi lại kích thước file (`file size`) — nếu phình bất thường so với số Day (ví dụ vài chục MB cho vài nghìn Day) thì khả năng cao có lỗi lặp/nhân bản nội dung.
   - **Chạy dedup check** (Mục 7.3) trên toàn bộ nội dung vừa sinh, và cập nhật `topics_registry.md`.
   - **Xác nhận có Review Day định kỳ và Capstone cuối roadmap** (Mục 8.3, 9.4) nếu roadmap đủ dài/đủ Phase để yêu cầu.

---

## 1. Chuẩn Định Dạng File Markdown (Parsing Standard)
Để Add-on có thể cắt chuỗi chính xác bằng Regex, file `.md` đầu ra BẮT BUỘC phải tuân thủ format:

```markdown
## Day X — Tiêu đề bài học
**Prompt:**
Nội dung lệnh gửi AI... (Add-on sẽ copy mọi thứ từ dưới chữ "Prompt:" cho đến khi gặp từ khóa chặn).

**Bài tập:**
- Bài 1
- Bài 2

**Tags:** #tag
```
*(Từ khóa chặn thường là `**Bài tập:**` hoặc `**Tags:**` hoặc một tiêu đề `## Day` mới)*

---

## 2. Quy Tắc Thiết Kế Roadmap V2 (Học Ngôn ngữ: Anh, Nhật, Trung, Hàn)
Đối với lộ trình ngôn ngữ phiên bản 2, cấu trúc bắt buộc là **7 ngày / 1 Unit**:
- **Day 1 (Vocab Foundation):** Dạy 15-20 từ vựng cốt lõi + 1 điểm ngữ pháp. Lấy từ vựng làm ví dụ ngữ pháp.
- **Day 2 (Grammar Deep Dive):** Dạy sâu ngữ pháp. Bài tập thực hành bắt buộc phải nhúng từ vựng của Day 1.
- **Day 3 (Pronunciation/Kanji):** Luyện phát âm / chữ viết, dựa trên từ vựng Unit.
- **Day 4 (Reading Immersion):** 1 bài đọc nhúng tự nhiên từ vựng & ngữ pháp. Có câu hỏi đọc hiểu.
- **Day 5 (Listening Immersion):** 1 Script nghe nhúng từ vựng Unit. Có câu hỏi bài nghe.
- **Day 6 (Speaking Practice):** Hội thoại mẫu hoàn chỉnh (song ngữ) để luyện Shadowing.
- **Day 7 (Review & Mini Test):** Bài test tổng hợp toàn Unit.

---

## 3. Quy Tắc Thiết Kế Roadmap Theo Độ Khó (Áp dụng cho MỌI lĩnh vực, không riêng IT)

### 3.1 Bảng phân bậc độ dài chu kỳ theo độ khó/độ rộng chủ đề

Không phải chủ đề nào cũng xứng đáng 15 ngày như nhau — dùng bảng dưới để chọn chu kỳ phù hợp trước khi sinh roadmap. Thực tế dự án đã từng dùng cả chu kỳ 15 và 25 ngày tùy độ phức tạp (xem ProjectLog Giai đoạn 33: các Phần Design Patterns/Testing/CI-CD/Open Source/Interview dùng chu kỳ dài hơn). Bảng này áp dụng chung cho IT, âm nhạc, kinh doanh, thể thao, nghệ thuật... không riêng lập trình — chỉ khác ở tên gọi từng ngày (xem Mục 3.4).

| Chu kỳ | Khi nào dùng | Ví dụ IT | Ví dụ lĩnh vực khác |
|---|---|---|---|
| **10 ngày (Lite)** | Kỹ năng/chủ đề hẹp, không cần chiều sâu kiến trúc/hệ thống riêng | 1 thư viện nhỏ (`dotenv`, `argparse`) | 1 kỹ thuật đàn cụ thể (fingerstyle cơ bản), 1 món ăn/kỹ thuật nấu |
| **15 ngày (Standard)** — mặc định | Chủ đề core, đủ rộng để cần lý thuyết + thực hành + sản phẩm nhỏ | Đa số ngôn ngữ lập trình, framework cỡ vừa | 1 nhạc cụ ở trình độ nhập môn, 1 kỹ năng kinh doanh (Sales cơ bản) |
| **20 ngày (Extended)** | Độ phức tạp trung-cao, cần thêm khía cạnh an toàn/mở rộng/nhiều case | Networking, Database internals, Concurrency nâng cao | Nhạc lý nâng cao + hòa âm, Chiến lược Marketing tổng thể |
| **25–30 ngày (Ultimate)** | Mảng lớn/liên ngành, nhiều case study thực tế, không gói gọn trong 1 sản phẩm | Distributed Systems, ML framework, Game Engine | Sáng tác & hòa âm phối khí, Xây dựng mô hình kinh doanh từ 0, Chuẩn bị thi đấu thể thao chuyên nghiệp |

**Cấu trúc 10 ngày (Lite):** rút gọn từ chuẩn 15 ngày — giữ Core Concept, Syntax, Deep Dive, Error Handling, Performance, Testing, Interview Prep, rồi gộp 3 ngày cuối thành Mini-Project (Setup + Core Logic → Complete → Review & Refactor).

**Cấu trúc 20 ngày (Extended):** giữ nguyên 12 ngày lý thuyết/thực hành đầu của chuẩn 15 ngày, chèn thêm **Security & Common Vulnerabilities** (sau Architecture) và **Concurrency/Scalability** (sau Testing), rồi mở rộng phần Mini-Project từ 3 ngày lên 6 ngày (Ý tưởng & Setup → Core Logic 1 → Core Logic 2 → Integration & Testing → Deploy/CI-CD → Refactor & Review tổng kết).

**Cấu trúc 25–30 ngày (Ultimate):** như bản 20 ngày, cộng thêm 1-2 case study hệ thống thực tế (đọc/phân tích kiến trúc một dự án lớn trong ngành), và tách Mini-Project thành 2-3 dự án nhỏ độc lập thay vì 1 dự án duy nhất, để bao phủ nhiều khía cạnh của mảng kiến thức rộng.

*(Lưu ý: Mọi prompt thực hành/bài test ở các ngày Mini-Project/Interview đều phải áp dụng Quy tắc Tối thượng "Không Tương Tác" ở Mục 4 bên dưới để cấm AI code giải sẵn hoặc tạo trắc nghiệm).*

### 3.2 Cấu trúc 15 ngày chuẩn mực (mặc định)

Khác với học ngoại ngữ, lập trình đòi hỏi sự kết hợp giữa lý thuyết, thực hành, tối ưu, bảo mật, và kiến trúc hệ thống. Để tạo ra một **giáo trình hoàn hảo, toàn diện tuyệt đối**, không được phép cắt xén nội dung. Chủ đề IT ở mức Standard sẽ được quy chuẩn thành **Chu kỳ 15 Ngày (15-Day Ultimate Mastery Cycle)**. Mỗi chủ đề sẽ nhận chính xác 15 ngày để trải qua 15 bước mài giũa:

**Cấu trúc 15 ngày chuẩn mực (Áp dụng 1 ngày = 1 Focus Area):**
1. **Day 1 (Core Concept):** Tổng quan cơ bản, cài đặt, và ví dụ "Hello World".
2. **Day 2 (Syntax):** Cú pháp nền tảng, các tham số phổ biến.
3. **Day 3 (Deep Dive):** Kiến trúc bên dưới, luồng thực thi (execution flow), memory.
4. **Day 4 (Advanced Methods):** Các tính năng nâng cao, phương thức ít người biết.
5. **Day 5 (Error Handling):** Xử lý lỗi, Edge Cases (Trường hợp dị biệt).
6. **Day 6 (Performance):** Tối ưu hiệu suất, Clean Code, tốc độ/bộ nhớ.
7. **Day 7 (Architecture):** Kiến trúc & Design Patterns áp dụng.
8. **Day 8 (Testing):** Testing & Debugging (Unit Test, Integration Test).
9. **Day 9 (Integration):** Tích hợp với các công cụ/thư viện khác.
10. **Day 10 (Open Source):** Phân tích mã nguồn mở của các dự án lớn.
11. **Day 11 (Interview Prep):** Bộ câu hỏi phỏng vấn thực tế.
12. **Day 12 (Reinvent the wheel):** Tự code lại công nghệ từ con số 0 để hiểu bản chất.
13. **Day 13 (Mini-Project 1):** Lên ý tưởng, cấu trúc thư mục, setup.
14. **Day 14 (Mini-Project 2):** Triển khai core logic (Xử lý nghiệp vụ chính).
15. **Day 15 (Mini-Project 3):** Hoàn thiện, thuật toán và Refactor.

*(Lưu ý: Mọi prompt thực hành/bài test ở Day 13, 14, 15 đều phải áp dụng Quy tắc Tối thượng "Không Tương Tác" bên dưới để cấm AI code giải sẵn hoặc tạo trắc nghiệm).*

### 3.3 Ánh xạ Template sang lĩnh vực khác (không phải IT/lập trình)

Cấu trúc 15 bước ở Mục 3.2 là khung tổng quát — chỉ cần đổi TÊN theo lĩnh vực, LOGIC giữ nguyên:

| # | Tên IT | Tên tổng quát (mọi lĩnh vực) |
|---|---|---|
| 1 | Core Concept | Tổng quan & nền tảng |
| 2 | Syntax | Yếu tố cơ bản / "ngữ pháp" của kỹ năng |
| 3 | Deep Dive | Nguyên lý/cơ chế bên dưới |
| 4 | Advanced Methods | Kỹ thuật nâng cao, ít người biết |
| 5 | Error Handling | Lỗi thường gặp & cách khắc phục |
| 6 | Performance | Tối ưu hiệu quả/thời gian/công sức |
| 7 | Architecture | Cấu trúc tổng thể & nguyên tắc thiết kế |
| 8 | Testing | Tự đánh giá / luyện tập có phản hồi |
| 9 | Integration | Kết hợp với kỹ năng/công cụ liên quan |
| 10 | Open Source | Case study thực tế từ chuyên gia/người giỏi trong ngành |
| 11 | Interview Prep | Chuẩn bị đánh giá/thi/phỏng vấn/biểu diễn |
| 12 | Reinvent the wheel | Tự làm lại từ đầu để hiểu bản chất |
| 13-15 | Mini-Project | Sản phẩm/bài luyện tập hoàn chỉnh cuối Unit |

Ví dụ áp dụng cho "Học Guitar Fingerstyle" (15 ngày): Day 1 Tổng quan kỹ thuật fingerstyle → Day 5 Lỗi bấm dây thường gặp → Day 10 Phân tích cách chơi của nghệ sĩ nổi tiếng → Day 13-15 Tự tập hoàn chỉnh 1 bài.




---

## 4. Quy Tắc Tối Thượng: KHÔNG TƯƠNG TÁC (Non-Interactive)
Khi tạo Prompt cho người dùng gửi AI, câu lệnh PHẢI ép AI xuất kết quả **hoàn chỉnh một chiều**. Tránh việc AI (đặc biệt là Gemini) tưởng người dùng đang muốn chơi đố vui và tự động bật giao diện trắc nghiệm chờ click.
- ❌ **Sai:** "Đặt câu hỏi và chờ người dùng trả lời" / "Hãy chấm điểm cho tôi".
- ✅ **Đúng (Bắt buộc dùng cho các bài test/bài tập ở Day 2, 4, 5, 7):**
  > `(⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)`

---

## 5. Quy Tắc File & Encoding
- Tất cả các file `.py` và `.md` sinh ra PHẢI ghi với `encoding="utf-8"`.
- Không sử dụng các lệnh PowerShell string replace (như `-replace`) cho nội dung tiếng Việt vì môi trường Windows CP1252 sẽ gây lỗi mất dấu chữ Quốc ngữ/Kanji. Hãy dùng Python hoặc thay thế trực tiếp trên file gốc.

---

## 6. Tự động xác định độ khó & số ngày (Auto-Detect Difficulty)

Người dùng có thể KHÔNG biết trước lĩnh vực đó khó hay dễ — đây là việc của agent, không phải người dùng. Khi không được chỉ định rõ, agent chấm điểm theo 5 tiêu chí sau, mỗi tiêu chí 1-3 điểm:

| Tiêu chí | 1 điểm | 2 điểm | 3 điểm |
|---|---|---|---|
| **Độ rộng** (số nhánh con thực sự khác biệt) | 1-2 nhánh | 3-5 nhánh | 6+ nhánh |
| **Độ sâu** (thời gian thực tế để thành thạo, theo chuẩn ngành) | Vài tuần | Vài tháng | Nhiều năm/có chứng chỉ chuyên môn |
| **Tiền đề** (cần bao nhiêu kiến thức nền trước khi học được) | Không cần gì | Cần 1-2 kỹ năng nền | Cần chuỗi kiến thức nền dài |
| **Tỷ trọng lý thuyết/thực hành** | Chủ yếu thao tác đơn giản | Cân bằng lý thuyết-thực hành | Lý thuyết phức tạp + thực hành đa dạng |
| **Tính liên ngành** | Đơn ngành | Giao 2 ngành | Giao 3+ ngành |

**Cách chấm điểm khi agent không rành lĩnh vực đó:** dùng web search để tra cứu nhanh — ví dụ tìm "how long to learn X to proficiency", "curriculum outline for X course", "X for beginners roadmap" — để có cơ sở khách quan thay vì đoán. Đây là bước bắt buộc nếu agent không tự tin về độ khó thực tế của chủ đề.

**Quy đổi tổng điểm → chu kỳ:**
- 5-7 điểm → **10 ngày (Lite)**
- 8-10 điểm → **15 ngày (Standard)**
- 11-12 điểm → **20 ngày (Extended)**
- 13-15 điểm → **25-30 ngày (Ultimate)**

Sau khi tự chấm, agent PHẢI trình bày ngắn gọn: điểm từng tiêu chí + chu kỳ chọn + lý do, để người dùng duyệt trước khi sinh roadmap (không tự ý chọn xong sinh luôn).

---

## 7. Chống Trùng Lặp Nội Dung (Duplicate Prevention)

### 7.1 Rủi ro trùng lặp thực tế
- **Trùng cấp topic**: cùng 1 chủ đề bị đưa vào 2 roadmap khác nhau (hoặc 2 Phase trong cùng roadmap) do không ai theo dõi danh sách topic đã tạo.
- **Trùng cấp nội dung trong 1 topic**: lỗi logic vòng lặp trong script (vd: index bị lặp, biến topic không cập nhật đúng vị trí) khiến 2 Day khác nhau ra cùng nội dung.
- **Trùng khi mở rộng roadmap cũ** (giống tình huống Giai đoạn 33 — thêm 270 Day mới cho C++): dễ vô tình chọn lại topic đã có ở Phase trước đó.

### 7.2 Bắt buộc: Script phải nhận Input dạng dữ liệu có cấu trúc

Script sinh KHÔNG được viết nội dung tự do lẫn với logic vòng lặp một cách rời rạc. Phải tách riêng phần dữ liệu topic thành cấu trúc rõ ràng ở đầu file (list/dict), ví dụ:

```python
TOPICS = [
    {"id": "cpp_coroutines", "title": "Coroutine internals tự viết", "keywords": ["coroutine", "co_await", "generator"]},
    {"id": "cpp_mmap", "title": "Memory-mapped files (mmap)", "keywords": ["mmap", "virtual memory"]},
    # ...
]
```
Cấu trúc này giúp: (a) dễ đối chiếu trùng lặp bằng code trước khi sinh, (b) dễ audit lại sau này, (c) tách biệt rõ "danh sách nội dung" khỏi "logic format Markdown".

### 7.3 Quy trình chống trùng bắt buộc

1. **Trước khi sinh**: đối chiếu từng `title`/`keywords` trong `TOPICS` với file `topics_registry.md` ở root project (danh sách tổng hợp mọi topic từng tạo, qua mọi roadmap). Nếu trùng khớp chính xác hoặc gần giống (na ná tên/keywords overlap cao) → cảnh báo người dùng trước khi tiếp tục, không tự ý bỏ qua.
2. **Sau khi sinh**: chạy dedup check bằng code — so sánh từng cặp **tiêu đề `## Day X — Tiêu đề` VÀ nội dung `**Prompt:**`** trong toàn bộ file `.md` vừa tạo (và cả các roadmap cũ nếu có) bằng `difflib.SequenceMatcher` hoặc so khớp tập từ khóa; ngưỡng tương đồng > 70% (dù tiêu đề khác nhau) thì gắn cờ để người dùng xem lại — tiêu đề khác nhau không đồng nghĩa nội dung khác nhau.
3. **Cập nhật `topics_registry.md`**: thêm các topic vừa tạo vào registry (id, title, roadmap file, ngày tạo) để lần sau đối chiếu.

`topics_registry.md` là file dùng chung cho MỌI roadmap trong workspace — không tạo registry riêng theo từng roadmap, để đối chiếu chéo được toàn bộ dự án.

---

## 8. Đảm bảo Độ Đầy Đủ & Chuẩn "Pro" (Coverage & Mastery Completeness)

Dedup (Mục 7) chỉ ngăn TRÙNG — không đảm bảo ĐỦ và không đảm bảo học xong thì giỏi thật. 4 cơ chế bắt buộc dưới đây giải quyết phần đó.

### 8.1 Kiểm tra độ phủ so với chuẩn ngành thực tế (bắt buộc, trước khi chốt danh sách topic)

Trước khi viết `TOPICS` cuối cùng, agent PHẢI web search để đối chiếu với ít nhất 1 nguồn tham chiếu uy tín, ví dụ: outline chứng chỉ chính thức của ngành ("X certification exam objectives"), curriculum đại học ("X university course syllabus"), hoặc roadmap cộng đồng đã được kiểm chứng rộng rãi (vd: roadmap.sh cho IT). Sau đó lập bảng đối chiếu: mỗi mảng lớn trong nguồn tham chiếu ↔ topic tương ứng trong roadmap đang xây. Nếu có mảng bị thiếu, PHẢI hoặc (a) bổ sung topic, hoặc (b) nói rõ với người dùng lý do cố tình bỏ qua (vd: ngoài phạm vi yêu cầu). Không được tự ý bỏ sót trong im lặng.

### 8.2 Thứ tự tiên quyết (Prerequisite Ordering)

Trong cấu trúc dữ liệu `TOPICS` (Mục 7.2), thêm field `prerequisites`:
```python
{"id": "cpp_coroutines", "title": "...", "keywords": [...], "prerequisites": ["cpp_templates", "cpp_move_semantics"]}
```
Trước khi gán số Day, script phải **sắp xếp topo (topological sort)** theo `prerequisites` — topic nào bị phụ thuộc phải đứng trước topic phụ thuộc nó trong roadmap. Không xếp Day theo thứ tự nghĩ ra tùy hứng.

### 8.3 Ôn tập định kỳ chống quên (Spaced Cumulative Review)

Với roadmap dài (vài trăm-vài nghìn Day), cứ sau mỗi **5 topic** (tức mỗi 75 Day ở chu kỳ Standard) chèn thêm **1 "Cumulative Review Day"** ngoài chu kỳ chuẩn: tổng hợp câu hỏi/bài tập rút từ 5 topic gần nhất, buộc người học phải nối kiến thức cũ với kiến thức mới thay vì học xong quên luôn. Đây là Day bổ sung, không tính vào chu kỳ 10/15/20/25-30 của từng topic.

### 8.4 Capstone tổng kết toàn Roadmap (bắt buộc với roadmap từ 2 Phase trở lên)

Ở cuối TOÀN BỘ roadmap (không phải cuối từng topic), phải có 1 khối **Capstone** riêng — độ dài tối thiểu bằng 1 chu kỳ Ultimate (25-30 Day) — yêu cầu người học kết hợp kiến thức từ NHIỀU topic/Phase khác nhau vào 1 sản phẩm/tình huống thực tế duy nhất (không phải lặp lại mini-project của từng topic). Đây là bước phân biệt "học hết danh sách bài" với "làm được việc thật ở trình độ pro" — nếu thiếu bước này, roadmap chỉ chứng minh đã đọc qua, chưa chứng minh tổng hợp được.

---

## 9. Ghi chú phạm vi

Skill này chỉ chứa kiến thức kỹ thuật về thiết kế/sinh Roadmap (cấu trúc chu kỳ, format parsing, quy tắc Non-Interactive, chống trùng lặp, đảm bảo độ đầy đủ/chuẩn pro, encoding). Quy trình làm việc chung (đọc `ProjectLog.md` trước, xin duyệt plan, cập nhật log sau khi hoàn thành...) được quản lý tập trung trong `AGENTS.md` / `GEMINI.md` ở cấp workspace/global, không lặp lại ở đây.
