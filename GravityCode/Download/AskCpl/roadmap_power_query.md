# Power Query Tutor — Roadmap 90 Ngày
<!--
  FORMAT CHUẨN CHO ADDON ĐỌC:
  - Mỗi bài bắt đầu bằng: ## Day N — Tiêu đề
  - Nội dung gửi AI nằm trong block: **Prompt:**
  - Kết thúc block Prompt khi gặp **Bài tập:** hoặc **Tags:**
  - Tags để phân loại/tìm kiếm
-->

---

## Day 1 — Pipeline & M Code cơ bản

**Prompt:**
Dạy tôi Power Query Day 1. Chủ đề hôm nay: Pipeline là gì trong Power Query (mỗi bước = 1 transformation), cấu trúc M code chuẩn `let ... in`, cách load data từ bảng Excel có cột Date/Line/Result, đổi kiểu dữ liệu (date, text, number), filter cơ bản. Cho ví dụ code M thực tế từng bước. Kết thúc cho 3 bài tập từ dễ đến khó.

**Bài tập:**
- Bài 1 (Cơ bản): Load bảng Date/Line/Result, đổi Date→date, Line→text
- Bài 2 (Trung cấp): Lọc Result = "NG"
- Bài 3 (Nâng nhẹ): Load + đổi kiểu + lọc OK + Rename step thành CleanData, FilteredOK

**Tags:** #foundation #pipeline #mcode #load #filter

---

## Day 2 — Filter & Transform thực chiến

**Prompt:**
Dạy tôi Power Query Day 2. Chủ đề: Filter nâng hơn (nhiều điều kiện AND/OR), Remove columns, Rename columns, Reorder columns, Change type hàng loạt. Dùng bảng Date/Line/Result/Qty. Cho code M thực tế từng bước. Kết thúc cho 3 bài tập từ dễ đến khó.

**Bài tập:**
- Bài 1: Filter Result=OK AND Qty>10
- Bài 2: Remove cột thừa, rename cột "Line" → "LineCode"
- Bài 3: Kết hợp filter, rename, reorder, đổi kiểu tất cả trong 1 query

**Tags:** #filter #transform #columns

---

## Day 3 — Add Column & Conditional Logic

**Prompt:**
Dạy tôi Power Query Day 3. Chủ đề: Thêm cột mới (AddColumn), cột điều kiện (if/then/else trong M), cột từ phép tính (Qty * Price), cột từ text (Text.Upper, Text.Combine). Bảng có cột Date/Line/Result/Qty/Price. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Thêm cột "Status" = if Result="OK" then "Pass" else "Fail"
- Bài 2: Thêm cột "Revenue" = Qty * Price
- Bài 3: Thêm cột "Label" = LineCode & " - " & Status

**Tags:** #addcolumn #conditional #calculation

---

## Day 4 — Group By & Aggregate

**Prompt:**
Dạy tôi Power Query Day 4. Chủ đề: Group By (nhóm dữ liệu), các hàm aggregate (Sum, Count, Average, Min, Max), Group nhiều cột, Group + tính nhiều chỉ số cùng lúc. Bảng Date/Line/Result/Qty. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Group by Line, tính tổng Qty
- Bài 2: Group by Date + Line, đếm số lượng OK và NG
- Bài 3: Group by Date, tính TotalQty, NGQty, NGRate = NGQty/TotalQty

**Tags:** #groupby #aggregate #summary

---

## Day 5 — Sort, Rank & Top N

**Prompt:**
Dạy tôi Power Query Day 5. Chủ đề: Sort (Table.Sort), Rank (thêm cột số thứ tự), Top N rows (Table.FirstN, Table.LastN), lọc Top N theo nhóm. Bảng Date/Line/NGQty/NGRate. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Sort NGRate giảm dần
- Bài 2: Lấy Top 3 Line có NG nhiều nhất
- Bài 3: Top 1 Line NG nhiều nhất mỗi ngày (group + sort + first)

**Tags:** #sort #rank #topn

---

## Day 6 — Merge (Join) Queries

**Prompt:**
Dạy tôi Power Query Day 6. Chủ đề: Merge Queries (join 2 bảng), các kiểu join (Left Outer, Inner, Full, Anti), mở rộng cột sau merge, join nhiều cột. Bảng 1: Date/LineCode/NGQty. Bảng 2: LineCode/LineName/Department. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Left join lấy LineName từ bảng 2
- Bài 2: Inner join — chỉ lấy Line có trong cả 2 bảng
- Bài 3: Anti join — tìm Line có NG nhưng không có trong danh sách

**Tags:** #merge #join #lookup

---

## Day 7 — Append & Union Queries

**Prompt:**
Dạy tôi Power Query Day 7. Chủ đề: Append Queries (gộp nhiều bảng theo hàng), union bảng cùng cấu trúc, union bảng khác cột (xử lý null), thêm cột nguồn để biết data từ đâu. Bảng tháng 1 và tháng 2 cùng cấu trúc. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Append 2 bảng cùng cấu trúc
- Bài 2: Append 3 bảng + thêm cột "Month" = "Jan/Feb/Mar"
- Bài 3: Append bảng khác số cột, xử lý null

**Tags:** #append #union #combine

---

## Day 8 — Pivot & Unpivot

**Prompt:**
Dạy tôi Power Query Day 8. Chủ đề: Pivot (chuyển hàng thành cột, Table.Pivot), Unpivot (chuyển cột thành hàng, Table.Unpivot), Unpivot Other Columns. Bảng chéo Line vs tháng với giá trị NGQty. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Unpivot bảng wide (Jan/Feb/Mar) thành tall (Month/Value)
- Bài 2: Pivot ngược lại
- Bài 3: Unpivot → Group → Pivot lại thành báo cáo tổng

**Tags:** #pivot #unpivot #reshape

---

## Day 9 — Text Functions & String Manipulation

**Prompt:**
Dạy tôi Power Query Day 9. Chủ đề: Các hàm Text trong M (Text.Upper, Text.Lower, Text.Trim, Text.Split, Text.Contains, Text.StartsWith, Text.Length, Text.Middle, Text.Replace, Text.Combine). Bảng có cột LineCode dạng "L001-A-2024". Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Tách LineCode "L001-A-2024" thành 3 cột (ID/Zone/Year)
- Bài 2: Chuẩn hóa text (trim, upper, xóa khoảng trắng thừa)
- Bài 3: Kiểm tra và lọc dòng có LineCode bắt đầu bằng "L0"

**Tags:** #text #string #manipulation

---

## Day 10 — Date & Time Functions

**Prompt:**
Dạy tôi Power Query Day 10. Chủ đề: Các hàm Date trong M (Date.Year, Date.Month, Date.Day, Date.DayOfWeek, Date.AddDays, Duration giữa 2 ngày, chuyển đổi text → date). Bảng có cột Date/StartTime/EndTime. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Tách Date thành Year, Month, Day, WeekDay
- Bài 2: Tính thời gian xử lý = EndTime - StartTime (phút)
- Bài 3: Lọc dữ liệu của tuần hiện tại và tháng trước

**Tags:** #date #time #datetime

---

## Day 11 — Number Functions & Math

**Prompt:**
Dạy tôi Power Query Day 11. Chủ đề: Các hàm Number trong M (Number.Round, Number.Abs, Number.Mod, Int64.From, Number.From, phần trăm, làm tròn thông minh). Bảng NGRate (số thực). Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Round NGRate 2 chữ số thập phân, chuyển sang %
- Bài 2: Làm tròn về bội số 5 gần nhất
- Bài 3: Tính z-score đơn giản (deviation từ mean)

**Tags:** #number #math #rounding

---

## Day 12 — Null & Error Handling cơ bản

**Prompt:**
Dạy tôi Power Query Day 12. Chủ đề: Xử lý null (Value.Is, if ... = null then), thay null bằng giá trị mặc định, loại bỏ dòng null, xử lý lỗi cơ bản (try...otherwise). Bảng có nhiều null và lỗi kiểu dữ liệu. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Thay null trong cột Qty bằng 0
- Bài 2: Xóa dòng có bất kỳ null nào
- Bài 3: try đổi kiểu text→number, otherwise 0

**Tags:** #null #error #tryotherwise

---

## Day 13 — List Operations

**Prompt:**
Dạy tôi Power Query Day 13. Chủ đề: List trong M ({1,2,3}), List.Contains, List.Sum, List.Max, List.Min, List.Count, List.Distinct, List.Sort, List.Transform, List.Select, dùng List để lookup đa giá trị. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Lọc bảng với danh sách Line được phép = {"L001","L002","L003"}
- Bài 2: Tổng hợp unique values từ cột
- Bài 3: Dùng List.Transform để áp dụng function lên list

**Tags:** #list #collection #functional

---

## Day 14 — Record Operations

**Prompt:**
Dạy tôi Power Query Day 14. Chủ đề: Record trong M ([Field1=val1, Field2=val2]), Record.Field, Record.FieldNames, Record.ToList, Record.FromList, chuyển đổi Row ↔ Record, dùng Record để build row động. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Lấy giá trị từ Record bằng tên field động
- Bài 2: Chuyển 1 row bảng thành Record, thêm field mới
- Bài 3: Build lookup record từ bảng và dùng để map giá trị

**Tags:** #record #row #metadata

---

## Day 15 — Mini Project #1: Ôn tập Day 1–14

**Prompt:**
Dạy tôi Power Query Day 15 — ôn tập tổng hợp Day 1–14. Cho tôi 1 mini project: Có 2 file Excel (dữ liệu inspection tháng 1 và tháng 2), mỗi file gồm bảng Data (Date/LineCode/LensType/Result/Qty) và bảng Lines (LineCode/LineName). Yêu cầu: Append 2 tháng, join tên Line, tính NGRate mỗi Line mỗi tháng, Top 3 Line NG nhất, thêm flag "Critical" nếu NGRate > 5%. Output 1 bảng báo cáo hoàn chỉnh.

**Bài tập:**
- Bài 1: Build query từng bước theo yêu cầu trên
- Bài 2: Thêm cột Month Name (January/February)
- Bài 3: Thêm cột RankByMonth (rank NGRate trong tháng đó)

**Tags:** #review #miniproject #milestone

---

## Day 16 — Query Folding: Khái niệm & Kiểm tra

**Prompt:**
Dạy tôi Power Query Day 16. Chủ đề: Query Folding là gì (chuyển transformation thành native query ở nguồn — SQL, OData...), tại sao quan trọng (performance), cách kiểm tra "View Native Query", dấu hiệu nhận biết step có/không fold, các bước thường KHÔNG fold được. Ví dụ với SQL Server source. Cho code M thực tế. Kết thúc cho 3 bài tập quan sát.

**Bài tập:**
- Bài 1: Kiểm tra query hiện tại xem bao nhiêu bước fold
- Bài 2: Thêm 1 Custom Column và xem folding có bị break không
- Bài 3: Sắp xếp lại thứ tự step để giữ folding lâu nhất

**Tags:** #queryfolding #performance #optimization

---

## Day 17 — Table.Buffer & List.Buffer

**Prompt:**
Dạy tôi Power Query Day 17. Chủ đề: Table.Buffer và List.Buffer — khi nào dùng, khi nào KHÔNG nên dùng, tác động lên memory và performance, ví dụ query tự join lại chính nó (self-join) cần buffer, sự khác nhau giữa buffer và cache. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Query có self-reference — test có/không buffer
- Bài 2: Đo thời gian query với Table.Buffer vs không
- Bài 3: Nhận biết khi nào query bị evaluate nhiều lần

**Tags:** #buffer #memory #performance

---

## Day 18 — Parameters & Dynamic Source

**Prompt:**
Dạy tôi Power Query Day 18. Chủ đề: Power Query Parameters — tạo parameter (text, number, date, list), dùng parameter trong query (source path, filter value), thay đổi parameter không cần sửa code, template parameter. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Tạo parameter "FolderPath", dùng trong Folder.Files
- Bài 2: Parameter "FilterDate", lọc dữ liệu từ ngày đó trở đi
- Bài 3: Parameter "TargetLine", lọc báo cáo theo line được chọn

**Tags:** #parameters #dynamic #automation

---

## Day 19 — Custom Functions (P1): Cú pháp & Cơ bản

**Prompt:**
Dạy tôi Power Query Day 19. Chủ đề: Viết Custom Function trong M — cú pháp `(param) => expression`, function nhiều tham số, function trả về value/list/table, gọi function trong query, lưu function thành query riêng để tái dùng. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Viết `fnNGRate = (ok, ng) => ng / (ok + ng)`
- Bài 2: Viết `fnCleanCode = (code) => Text.Upper(Text.Trim(code))`
- Bài 3: Áp dụng function lên cột bằng Table.AddColumn

**Tags:** #customfunction #reusable #functional

---

## Day 20 — Custom Functions (P2): Optional Params & Table Input

**Prompt:**
Dạy tôi Power Query Day 20. Chủ đề: Optional parameters trong function (`optional param as type`), function documentation (metadata), function nhận Table làm input, function trả về Table, function xử lý lỗi nội bộ. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Function với optional threshold (mặc định 5%)
- Bài 2: Function nhận bảng → trả về bảng đã clean
- Bài 3: Function tính top N với N là parameter

**Tags:** #customfunction #optional #advanced

---

## Day 21 — Error Handling Nâng cao

**Prompt:**
Dạy tôi Power Query Day 21. Chủ đề: Error handling nâng cao trong M — `try...otherwise` phức tạp, `Value.ReplaceErrors`, bắt lỗi theo cột, `Error.Record`, tạo cột "IsValid" kiểm tra dữ liệu, validate schema đầu vào. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Thêm cột "ParsedDate" = try đổi text→date otherwise null
- Bài 2: Thêm cột "IsValid" = kiểm tra tất cả required field có null không
- Bài 3: Build validation report — đếm lỗi theo cột

**Tags:** #errorhandling #validation #robust

---

## Day 22 — Folder.Files & Combine Binaries

**Prompt:**
Dạy tôi Power Query Day 22. Chủ đề: Load tất cả file Excel/CSV trong 1 thư mục (Folder.Files), Combine Binaries tự động, xử lý file khác tên sheet, thêm cột tên file vào data, lọc file theo tên/ngày tạo. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Load tất cả .xlsx trong folder, gộp lại
- Bài 2: Thêm cột "FileName" để biết data từ file nào
- Bài 3: Chỉ load file có tên bắt đầu bằng "Report_2024"

**Tags:** #folder #combinefiles #automation

---

## Day 23 — Multi-Sheet & Dynamic Sheet

**Prompt:**
Dạy tôi Power Query Day 23. Chủ đề: Load nhiều sheet từ 1 file Excel, load sheet theo tên động (parameter), load tất cả sheet và gộp lại, xử lý sheet có format khác nhau. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Load sheet "Jan" và "Feb", append lại
- Bài 2: Load tất cả sheet có tên bắt đầu bằng "Data_"
- Bài 3: Parameter chọn sheet name, query load đúng sheet đó

**Tags:** #multisheet #dynamic #excel

---

## Day 24 — Web Data & URL Source

**Prompt:**
Dạy tôi Power Query Day 24. Chủ đề: Load từ URL (Web.Contents), parse HTML table từ website, load CSV/JSON từ URL công khai, xử lý header và authentication cơ bản (API key trong URL). Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Load CSV từ GitHub raw URL
- Bài 2: Load JSON từ API công khai (ví dụ: tỷ giá ngoại tệ)
- Bài 3: Parse HTML table từ trang web tĩnh

**Tags:** #web #url #api #import

---

## Day 25 — Reference Query & Query Tree

**Prompt:**
Dạy tôi Power Query Day 25. Chủ đề: Reference Query (tham chiếu query khác), tại sao dùng Reference thay vì Duplicate, xây dựng query hierarchy (base → transform → report), join dữ liệu từ 2 nguồn khác nhau. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Base query từ Excel, Reference tạo 2 báo cáo khác nhau
- Bài 2: Join bảng master từ SharePoint với data từ file local
- Bài 3: Query tree: Source → Clean → Filter → Report1 + Report2

**Tags:** #reference #querytree #architecture

---

## Day 26 — Type System & Schema Validation

**Prompt:**
Dạy tôi Power Query Day 26. Chủ đề: Type system trong M — primitive types, structured types, định nghĩa custom type `type table [Col1=text, Col2=number]`, Table.Schema, kiểm tra và enforce schema đầu vào, thêm metadata vào type. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Định nghĩa custom type cho bảng inspection
- Bài 2: Viết function validate table có đúng schema không
- Bài 3: Thêm metadata (DisplayName, Description) vào cột

**Tags:** #types #schema #metadata

---

## Day 27 — Performance Pattern: Limit Data Early

**Prompt:**
Dạy tôi Power Query Day 27. Chủ đề: Pattern "Limit Data Early" — tại sao filter và remove column phải là BƯỚC ĐẦU TIÊN, tác động của vị trí step lên memory và speed, anti-pattern thường gặp, cách refactor query hiện có để tối ưu. Cho code M trước/sau. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Refactor query — đưa filter lên đầu
- Bài 2: Remove cột không cần ngay sau Source
- Bài 3: So sánh query "bad" vs "good" — giải thích tại sao

**Tags:** #performance #pattern #optimization #bestpractice

---

## Day 28 — Practical: Báo cáo NG/OK Production

**Prompt:**
Dạy tôi Power Query Day 28 — bài thực hành sản xuất. Dữ liệu: Bảng inspection gồm Date/Shift/LineCode/LensType/Result/Qty/Inspector. Yêu cầu: Tính NGRate mỗi Line mỗi ngày, rank Line theo NG, thêm flag "High NG" (>5%), "Critical" (>10%), pivot theo Shift, tìm Inspector có NG nhiều nhất. Output hoàn chỉnh ready-to-report.

**Bài tập:**
- Bài 1: Build toàn bộ query theo yêu cầu trên
- Bài 2: Thêm cột "WeekNumber" và Group by Week
- Bài 3: Tạo "Summary Table" và "Detail Table" từ cùng 1 source

**Tags:** #practical #production #inspection #lens

---

## Day 29 — Advanced Merge: Fuzzy & Multiple Keys

**Prompt:**
Dạy tôi Power Query Day 29. Chủ đề: Fuzzy Matching trong Merge (tìm tên tương tự), Merge theo nhiều cột (composite key), Self-join (join bảng với chính nó), Anti-join nâng cao, xử lý nhiều-nhiều relationship. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Bài tập:**
- Bài 1: Fuzzy match tên line "L001" ≈ "l 001"
- Bài 2: Merge theo Date + LineCode + Shift (3 key)
- Bài 3: Self-join — so sánh ngày hiện tại với ngày trước

**Tags:** #merge #fuzzy #compositekey #selfjoin

---

## Day 30 — Mini Project #2: Foundation Complete

**Prompt:**
Dạy tôi Power Query Day 30 — tổng kết Foundation (Day 1–30). Mini project cuối: Hệ thống báo cáo hoàn chỉnh — Source: Folder chứa file Excel hàng tháng (Date/Line/LensType/Result/Qty/Price). Yêu cầu: Auto-load tất cả file, clean data, tính doanh thu + NGRate, Top 5 Line NG, pivot theo tháng, output 3 báo cáo: Summary/Detail/Alert(NGRate>5%). Dùng tất cả kỹ thuật Day 1–29.

**Bài tập:**
- Bài 1: Build toàn bộ pipeline từ Folder → 3 báo cáo
- Bài 2: Thêm parameter "MonthFilter" để lọc theo tháng
- Bài 3: Tối ưu query — đảm bảo filter early, buffer đúng chỗ

**Tags:** #review #miniproject #milestone #foundation-complete

---

## Day 31 — Query Folding Deep Dive

**Prompt:**
Dạy tôi Power Query Day 31. Chủ đề Query Folding nâng cao: Chuỗi folding, cách xem native query SQL, các transformation nào KHÔNG fold được (custom column, invoke function...), Folding Indicators trong Power BI, Native Database Query, folding với OData/SharePoint. Cho code M thực tế + ví dụ native SQL. Kết thúc cho 3 bài tập.

**Tags:** #queryfolding #sql #nativequery

---

## Day 32 — Parameters Nâng cao & Dynamic Query

**Prompt:**
Dạy tôi Power Query Day 32. Chủ đề: Parameters nâng cao — dùng trong M code trực tiếp, tạo query template, parameter list (dropdown), nạp parameter từ file config bên ngoài, kết hợp nhiều parameter trong 1 source string. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #parameters #dynamic #template

---

## Day 33 — Custom Function Library

**Prompt:**
Dạy tôi Power Query Day 33. Chủ đề: Xây dựng Function Library — tạo query nhóm "LIBRARY" chứa các function tái dùng: fnClean, fnValidate, fnNGRate, fnTopN, fnAddFlag, cách gọi function từ query khác, chia sẻ function giữa các report. Cho code M thực tế toàn bộ library. Kết thúc cho 3 bài tập.

**Tags:** #library #reusable #architecture

---

## Day 34 — Error Handling Framework

**Prompt:**
Dạy tôi Power Query Day 34. Chủ đề: Build Error Handling Framework — wrapper function xử lý lỗi nhất quán, log lỗi vào bảng riêng, Error.Record, phân loại lỗi (kiểu, format, missing), báo cáo data quality tự động. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #errorhandling #framework #dataquality

---

## Day 35 — Folder Auto-merge Nâng cao

**Prompt:**
Dạy tôi Power Query Day 35. Chủ đề: Folder merge nâng cao — xử lý file có format khác nhau trong cùng folder, filter file theo ngày modified, incremental load (chỉ load file mới hơn lastRefresh), xử lý file lỗi không crash toàn bộ query. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #folder #incremental #robust

---

## Day 36 — List.Accumulate & Functional Patterns

**Prompt:**
Dạy tôi Power Query Day 36. Chủ đề: List.Accumulate (tương đương reduce/fold), dùng để tính running total, build string, aggregate phức tạp, kết hợp với List.Transform và List.Select. So sánh với Group By khi nào dùng cái nào. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #listaccumulate #functional #reduce

---

## Day 37 — Table.TransformRows & Row-level Processing

**Prompt:**
Dạy tôi Power Query Day 37. Chủ đề: Table.TransformRows — xử lý từng row bằng function, tương đương map() trên table, so sánh với Table.AddColumn và Table.TransformColumns, khi nào hiệu quả hơn. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #transformrows #rowlevel #functional

---

## Day 38 — Recursion trong M

**Prompt:**
Dạy tôi Power Query Day 38. Chủ đề: Recursive functions trong M — cú pháp `@self`, ví dụ tính tổng đệ quy, duyệt cây phân cấp, xử lý JSON lồng nhiều tầng không biết trước độ sâu, giới hạn recursion. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #recursion #recursive #tree

---

## Day 39 — REST API Cơ bản

**Prompt:**
Dạy tôi Power Query Day 39. Chủ đề: Gọi REST API trong M — Web.Contents với options (Headers, Query, Content), GET request, parse JSON response, xử lý status code, authentication cơ bản (API key trong header). Dùng API công khai thực tế. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #api #rest #webcontent

---

## Day 40 — API Pagination

**Prompt:**
Dạy tôi Power Query Day 40. Chủ đề: Xử lý API có pagination — offset/limit pagination, cursor-based pagination, page-based pagination, dùng List.Generate để loop tự động qua tất cả trang cho đến hết, rate limiting. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #pagination #api #listgenerate

---

## Day 41 — JSON Nested Parsing

**Prompt:**
Dạy tôi Power Query Day 41. Chủ đề: Parse JSON phức tạp nhiều tầng — expand nested object, expand array trong object, flatten JSON hoàn toàn, xử lý JSON có schema không nhất quán (field có thể missing), kết hợp với recursion để flatten bất kỳ độ sâu nào. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #json #nested #parse #flatten

---

## Day 42 — OAuth2 & API Authentication

**Prompt:**
Dạy tôi Power Query Day 42. Chủ đề: Authentication trong Power Query — OAuth2 flow, Bearer token trong header, Basic auth, xử lý token expiry, lưu token an toàn (không hardcode). Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #oauth2 #authentication #security

---

## Day 43 — Query Diagnostics Tool

**Prompt:**
Dạy tôi Power Query Day 43. Chủ đề: Power BI Query Diagnostics — cách bật, đọc log output, hiểu các cột (StepName, Duration, RowsRead...), tìm bottleneck, so sánh trước/sau tối ưu, dùng diagnostics để debug query chậm. Hướng dẫn step-by-step thực tế. Kết thúc cho 3 bài tập quan sát.

**Tags:** #diagnostics #debugging #performance

---

## Day 44 — Lazy Evaluation & M Engine

**Prompt:**
Dạy tôi Power Query Day 44. Chủ đề: Lazy Evaluation trong M — M chỉ tính giá trị khi cần, tránh tính toán thừa, tại sao thứ tự step quan trọng, Environments và Scope, vòng lặp evaluation, tác động của Buffer lên lazy eval. Cho code M minh họa. Kết thúc cho 3 bài tập.

**Tags:** #lazyeval #engine #scope #evaluation

---

## Day 45 — Mini Project #3: API → Report Pipeline

**Prompt:**
Dạy tôi Power Query Day 45 — Mini Project #3. Build pipeline hoàn chỉnh: Lấy dữ liệu từ REST API (có pagination), combine với master data từ Excel, clean + transform, tính metrics, output báo cáo. Dùng tất cả kỹ thuật Day 31–44. Yêu cầu: Query phải có error handling, tất cả hardcode phải thay bằng parameter.

**Tags:** #miniproject #api #pipeline #milestone

---

## Day 46 — SharePoint & OneDrive Source

**Prompt:**
Dạy tôi Power Query Day 46. Chủ đề: Load file từ SharePoint/OneDrive — SharePoint.Files connector, load file theo URL SharePoint, auto-refresh từ SharePoint list, xử lý permission, load Excel từ OneDrive for Business, kết hợp với Folder merge. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #sharepoint #onedrive #cloud

---

## Day 47 — SQL Server & Stored Procedures

**Prompt:**
Dạy tôi Power Query Day 47. Chủ đề: Kết nối SQL Server trong Power Query — Sql.Database, gọi Stored Procedure có parameter, Native SQL Query (Value.NativeQuery), kiểm tra query folding với SQL source, xử lý connection string. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #sqlserver #storedprocedure #nativequery

---

## Day 48 — Dataflows Gen1 Cơ bản

**Prompt:**
Dạy tôi Power Query Day 48. Chủ đề: Power BI Dataflows Gen1 — Dataflow là gì, tạo Dataflow từ Power BI Service, publish transformation lên cloud, kết nối Desktop đến Dataflow, Computed Entity, lợi ích single source of truth. Hướng dẫn thực tế step by step. Kết thúc cho 3 bài tập.

**Tags:** #dataflows #cloud #reusable

---

## Day 49 — Incremental Refresh

**Prompt:**
Dạy tôi Power Query Day 49. Chủ đề: Incremental Refresh trong Power BI — tại sao cần, RangeStart/RangeEnd parameters (bắt buộc đặt tên đúng), cấu hình policy (lưu N năm, refresh M ngày), detect data changes, incremental với Dataflows. Cho code M thực tế + cấu hình. Kết thúc cho 3 bài tập.

**Tags:** #incrementalrefresh #performance #bigdata

---

## Day 50 — DirectQuery vs Import vs DirectLake

**Prompt:**
Dạy tôi Power Query Day 50. Chủ đề: So sánh sâu 3 chế độ — Import (load vào RAM), DirectQuery (query live), DirectLake (Fabric). Khi nào dùng cái nào, Hybrid Tables (Import lịch sử + DirectQuery real-time), trade-off performance vs freshness. Cho ví dụ thực tế. Kết thúc cho 3 bài tập phân tích.

**Tags:** #directquery #import #directlake #hybrid

---

## Day 51 — Dataflows Gen2 & Microsoft Fabric

**Prompt:**
Dạy tôi Power Query Day 51. Chủ đề: Dataflows Gen2 trong Microsoft Fabric — khác gì Gen1, tích hợp với Lakehouse/Warehouse, output destinations (Fabric Lakehouse, Azure SQL...), Spark-based processing. Hướng dẫn thực tế. Kết thúc cho 3 bài tập.

**Tags:** #dataflowsgen2 #fabric #lakehouse

---

## Day 52 — Azure Data Sources

**Prompt:**
Dạy tôi Power Query Day 52. Chủ đề: Kết nối Azure trong Power Query — Azure SQL Database, Azure Blob Storage, Azure Data Lake Storage Gen2, Azure Synapse Analytics, authentication với Azure AD/Service Principal. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #azure #cloud #adls #synapse

---

## Day 53 — Python Integration trong Power BI

**Prompt:**
Dạy tôi Power Query Day 53. Chủ đề: Tích hợp Python trong Power BI — Python script làm data source, Python trong Power Query transformation, dùng pandas/numpy trong query, giới hạn và lưu ý, setup môi trường. Cho code Python + M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #python #integration #pandas

---

## Day 54 — List.Generate: Advanced Looping

**Prompt:**
Dạy tôi Power Query Day 54. Chủ đề: List.Generate — tạo list bằng vòng lặp có điều kiện dừng, so sánh với recursion và List.Transform, dùng để: generate date range, loop API pages, generate hierarchical data, tạo rolling window. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #listgenerate #loop #advanced

---

## Day 55 — Expression.Evaluate & Dynamic Code

**Prompt:**
Dạy tôi Power Query Day 55. Chủ đề: Expression.Evaluate — chạy M code động từ text string, dùng để build query từ config file, dynamic column selection, meta-programming trong M, giới hạn và rủi ro bảo mật, Environment parameter. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #expressionevaluate #dynamic #metaprogramming

---

## Day 56 — Intrinsic Functions Mastery

**Prompt:**
Dạy tôi Power Query Day 56. Chủ đề: Các nhóm function ít dùng nhưng mạnh trong M — Splitter.* (tách string nâng cao), Combiner.* (ghép string), Comparer.* (so sánh custom), Value.* (type checking), Replacer.*. Cho code M thực tế cho từng nhóm. Kết thúc cho 3 bài tập.

**Tags:** #intrinsic #splitter #combiner #comparer

---

## Day 57 — Code Standards & Maintainability

**Prompt:**
Dạy tôi Power Query Day 57. Chủ đề: Viết M code dễ đọc và bảo trì — đặt tên step rõ ràng, comment trong M code bằng metadata, naming convention cho query/step/function, cấu trúc let...in tốt, tránh magic numbers. Cho code trước/sau refactor thực tế. Kết thúc cho 3 bài tập.

**Tags:** #standards #naming #maintainability #readability

---

## Day 58 — Version Control cho Power Query

**Prompt:**
Dạy tôi Power Query Day 58. Chủ đề: Version control M code — export .pq file, dùng Git để track thay đổi, công cụ pbi-tools để extract M từ .pbix, compare version, branching strategy cho Power BI project, review M code như review code thường. Hướng dẫn thực tế. Kết thúc cho 3 bài tập.

**Tags:** #versioncontrol #git #pbitools #devops

---

## Day 59 — Row-Level Security & Dynamic Filtering

**Prompt:**
Dạy tôi Power Query Day 59. Chủ đề: Row-Level Security liên quan Power Query — dynamic filtering theo user (USERNAME()), lấy permission table từ database, filter data source theo role, kết hợp RLS với parameter query, bảo mật data trong M. Cho code M + DAX thực tế. Kết thúc cho 3 bài tập.

**Tags:** #rls #security #dynamicfilter

---

## Day 60 — Mini Project #4: Enterprise ETL Design

**Prompt:**
Dạy tôi Power Query Day 60 — Mini Project #4. Thiết kế Enterprise ETL pipeline: Source (Azure SQL + Folder + API) → Staging layer (Dataflow) → Transform layer (function library) → Presentation layer (3 reports). Yêu cầu: incremental refresh, error handling, parameter-driven, documented. Bản vẽ kiến trúc + code M. Kết thúc cho 3 bài tập thiết kế.

**Tags:** #enterprise #etl #architecture #milestone

---

## Day 61 — On-Premises Data Gateway

**Prompt:**
Dạy tôi Power Query Day 61. Chủ đề: On-Premises Data Gateway — cài đặt, cấu hình, kết nối Power BI Service đến nguồn data local (SQL Server/file/folder), scheduled refresh qua gateway, troubleshoot lỗi gateway, Personal vs Standard gateway. Hướng dẫn thực tế. Kết thúc cho 3 bài tập.

**Tags:** #gateway #onpremises #refresh #scheduling

---

## Day 62 — Power Automate + Power BI Integration

**Prompt:**
Dạy tôi Power Query Day 62. Chủ đề: Tích hợp Power Automate với Power BI — trigger refresh từ Power Automate, refresh theo event (file mới upload lên SharePoint → trigger refresh), alert khi NGRate > threshold, export report tự động. Hướng dẫn thực tế. Kết thúc cho 3 bài tập.

**Tags:** #powerautomate #automation #trigger #alert

---

## Day 63 — Data Profiling & Quality Monitoring

**Prompt:**
Dạy tôi Power Query Day 63. Chủ đề: Data Profiling trong Power Query — Column Quality (% valid/error/empty), Column Distribution (histogram), Column Profile (min/max/distinct), build automated data quality report, tracking quality theo thời gian, alert khi quality giảm. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #profiling #dataquality #monitoring

---

## Day 64 — Advanced Diagnostics & Bottleneck Analysis

**Prompt:**
Dạy tôi Power Query Day 64. Chủ đề: Advanced Query Diagnostics — đọc detailed log (StartTime, ExclusiveDuration, Category), phân biệt "Mashup Engine" vs "Data Source" time, tìm bước chậm nhất, debug query bằng diagnostics, dùng Power BI Performance Analyzer song song. Hướng dẫn thực tế. Kết thúc cho 3 bài tập.

**Tags:** #diagnostics #bottleneck #advanced #performance

---

## Day 65 — Memory Management Chuyên sâu

**Prompt:**
Dạy tôi Power Query Day 65. Chủ đề: Quản lý memory trong Power Query — tại sao query tốn RAM, streaming vs buffered evaluation, tác động của join/expand lên memory, strategy giảm memory: column pruning sớm, avoid materialization, dùng Parquet thay CSV. Cho code M thực tế + đo lường. Kết thúc cho 3 bài tập.

**Tags:** #memory #streaming #optimization #advanced

---

## Day 66 — ETL Design Patterns: Medallion Architecture

**Prompt:**
Dạy tôi Power Query Day 66. Chủ đề: ETL Design Patterns — Medallion Architecture (Bronze/Silver/Gold), Staging/Transform/Serve layers, SCD (Slowly Changing Dimension) Type 1 & 2, Snapshot vs Incremental, khi nào dùng pattern nào. Cho code M thực tế cho từng pattern. Kết thúc cho 3 bài tập.

**Tags:** #etl #patterns #medallion #scd

---

## Day 67 — Parquet & Columnar Data

**Prompt:**
Dạy tôi Power Query Day 67. Chủ đề: Đọc Parquet file trong Power Query — tại sao Parquet nhanh hơn CSV (columnar, compressed), load từ local/Azure Data Lake/Fabric Lakehouse, predicate pushdown với Parquet, so sánh performance CSV vs Parquet cho dữ liệu lớn. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #parquet #columnar #performance #bigdata

---

## Day 68 — Fabric Lakehouse & Power Query

**Prompt:**
Dạy tôi Power Query Day 68. Chủ đề: Microsoft Fabric Lakehouse tích hợp Power Query — upload data vào Lakehouse, Dataflow Gen2 → Lakehouse, Power Query Desktop kết nối Lakehouse, Direct Lake semantic model, Shortcuts, OneLake. Hướng dẫn thực tế. Kết thúc cho 3 bài tập.

**Tags:** #fabric #lakehouse #onelake #directlake

---

## Day 69 — CI/CD cho Power BI Project

**Prompt:**
Dạy tôi Power Query Day 69. Chủ đề: CI/CD cho Power BI với Power Query — dùng pbi-tools extract M code, Azure DevOps pipeline tự động deploy .pbix, kiểm tra M code syntax trước deploy, environment (Dev/Test/Prod), Deployment Pipelines trong Power BI Premium. Hướng dẫn thực tế. Kết thúc cho 3 bài tập.

**Tags:** #cicd #devops #deployment #automation

---

## Day 70 — Security & Data Governance

**Prompt:**
Dạy tôi Power Query Day 70. Chủ đề: Bảo mật trong Power Query — tránh hardcode credentials, dùng Windows/Database/Key Vault authentication, Data Privacy Levels (Public/Organizational/Private) và tại sao quan trọng, preventing formula firewall error, sensitivity labels. Cho code M thực tế + checklist. Kết thúc cho 3 bài tập.

**Tags:** #security #governance #privacy #credentials

---

## Day 71 — Scalability: Handling Large Data

**Prompt:**
Dạy tôi Power Query Day 71. Chủ đề: Xử lý dữ liệu lớn (triệu rows) trong Power Query — chiến lược: aggregate at source, sampling, partition-aware filtering, dùng Summary Table + Detail Table, khi nào Power Query không đủ → chuyển sang Azure Data Factory. Cho quyết định framework thực tế. Kết thúc cho 3 bài tập.

**Tags:** #scalability #largedata #bigdata #limits

---

## Day 72 — Custom Connector Cơ bản

**Prompt:**
Dạy tôi Power Query Day 72. Chủ đề: Tạo Custom Data Connector cơ bản — cấu trúc file .pqx, định nghĩa Data Source Kind, authentication type, navigation table, publish connector, Power Query SDK. Cho code M + hướng dẫn cài đặt. Kết thúc cho 3 bài tập.

**Tags:** #customconnector #sdk #extension

---

## Day 73 — Custom Connector Nâng cao

**Prompt:**
Dạy tôi Power Query Day 73. Chủ đề: Custom Connector nâng cao — xử lý OAuth2 trong connector, retry logic, caching, navigation table phân cấp, unit testing connector. Cho code M thực tế + SDK. Kết thúc cho 3 bài tập.

**Tags:** #customconnector #advanced #oauth2

---

## Day 74 — GraphQL & Advanced API

**Prompt:**
Dạy tôi Power Query Day 74. Chủ đề: Xử lý GraphQL trong Power Query — gọi GraphQL endpoint (POST request với query body), parse response, xử lý variables, cursor pagination với GraphQL, so sánh REST vs GraphQL trong context Power Query. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #graphql #api #advanced #json

---

## Day 75 — Documentation Automation

**Prompt:**
Dạy tôi Power Query Day 75. Chủ đề: Tự động hóa tài liệu trong Power Query — dùng metadata M (`Value.Metadata`, `type ... meta [...]`) để embed documentation, tạo query tự động generate data dictionary, export schema sang Excel/Markdown, tài liệu hóa function library. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #documentation #metadata #automation

---

## Day 76 — Performance Benchmarking Framework

**Prompt:**
Dạy tôi Power Query Day 76. Chủ đề: Xây dựng framework đo performance query — tạo bảng benchmark (query name, rowcount, duration, timestamp), compare version cũ vs mới, tự động chạy benchmark sau mỗi thay đổi, report performance trend. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #benchmark #framework #measurement

---

## Day 77 — Data Validation Framework

**Prompt:**
Dạy tôi Power Query Day 77. Chủ đề: Build Data Validation Framework hoàn chỉnh — định nghĩa rules (not null, range, regex, foreign key), apply rules lên bảng, tạo Validation Report (Pass/Fail/Warning từng rule từng row), threshold alert, log validation results. Cho code M thực tế. Kết thúc cho 3 bài tập.

**Tags:** #validation #framework #dataquality #rules

---

## Day 78 — Team Collaboration & Workspace Organization

**Prompt:**
Dạy tôi Power Query Day 78. Chủ đề: Làm việc nhóm với Power Query — workspace tổ chức (Shared/Certified datasets), Dataflows làm tầng trung gian cho nhiều người, strategy khi 2 người cùng sửa query, review process cho M code, onboarding người mới. Cho best practice thực tế. Kết thúc cho 3 bài tập.

**Tags:** #teamwork #collaboration #governance

---

## Day 79 — M Language Specification Deep Read

**Prompt:**
Dạy tôi Power Query Day 79. Chủ đề: Đọc hiểu M Language Specification (tài liệu chính thức Microsoft) — grammar của M, operator precedence, function application rules, environment model, identifier rules, section documents, các phần ít ai đọc nhưng quan trọng. Tổng hợp kiến thức nền tảng ẩn. Kết thúc cho 3 bài tập tư duy.

**Tags:** #specification #theory #foundation #mspec

---

## Day 80 — Real-time Data Strategy 2025–2026

**Prompt:**
Dạy tôi Power Query Day 80. Chủ đề: Chiến lược data real-time trong 2025–2026 — Streaming trong Power BI đã bị retire, các alternative: DirectQuery (live), Direct Lake (Fabric), EventStream (Fabric), khi nào cần real-time thực sự vs near-real-time đủ dùng, architecture cho near-real-time. Cho phân tích case thực tế.

**Tags:** #realtime #streaming #directlake #eventstream

---

## Day 81 — Performance Optimization Master Review

**Prompt:**
Dạy tôi Power Query Day 81 — tổng kết tất cả kỹ thuật tối ưu performance từ Day 1–80. Tạo Performance Optimization Checklist đầy đủ: Query Folding (90%+ target), Buffer strategy, Column pruning early, Row filtering early, Join order, Source-side aggregation, Incremental Refresh, Parameter-driven filtering. Cho code M minh họa từng kỹ thuật.

**Tags:** #performance #optimization #checklist #mastery

---

## Day 82 — Monitoring & Alerting System

**Prompt:**
Dạy tôi Power Query Day 82. Chủ đề: Hệ thống monitoring cho Power Query pipeline — track refresh history, alert khi refresh fail (Power Automate), monitor data volume bất thường, log performance metrics, dashboard giám sát health của toàn bộ data pipeline. Hướng dẫn thực tế. Kết thúc cho 3 bài tập.

**Tags:** #monitoring #alerting #healthcheck #operations

---

## Day 83 — Case Study: Production System Thực Tế

**Prompt:**
Dạy tôi Power Query Day 83 — Case Study thực tế: Xây dựng hệ thống báo cáo inspection cho nhà máy sản xuất lens. Yêu cầu thực tế: 20 line sản xuất, dữ liệu CSV mỗi giờ, 500K rows/ngày, báo cáo: NGRate realtime (DirectQuery), weekly trend, lens type analysis, operator performance, alert khi NG vượt ngưỡng. Full architecture + M code.

**Tags:** #casestudy #inspection #production #realworld

---

## Day 84 — Building Power BI Report Templates

**Prompt:**
Dạy tôi Power Query Day 84. Chủ đề: Tạo Power BI Template (.pbit) với Power Query — tất cả parameters exposed, không chứa data, người dùng điền thông tin khi mở, kết hợp template với function library, share template trong team. Hướng dẫn thực tế step by step. Kết thúc cho 3 bài tập.

**Tags:** #template #pbit #sharing #team

---

## Day 85 — Portfolio & Code Refactoring

**Prompt:**
Dạy tôi Power Query Day 85. Chủ đề: Xây dựng portfolio Power Query chuyên nghiệp — refactor tất cả query cũ theo chuẩn (tên step, comment, error handling), viết README cho mỗi report, tạo data dictionary, ghi lại architecture decisions, chuẩn bị để demo cho team/management. Cho checklist và template thực tế.

**Tags:** #portfolio #documentation #professional

---

## Day 86 — Capstone Project (P1): Requirements & Design

**Prompt:**
Dạy tôi Power Query Day 86 — Capstone Project Phase 1: DESIGN. Tôi sẽ build end-to-end Data Platform cho nhà máy. Hướng dẫn tôi: (1) Thu thập requirements, (2) Thiết kế data model, (3) Chọn kiến trúc (Import/DirectQuery/Fabric), (4) Thiết kế Dataflow layers, (5) Vẽ sơ đồ kiến trúc. Output: Architecture Document hoàn chỉnh.

**Tags:** #capstone #design #architecture #requirements

---

## Day 87 — Capstone Project (P2): Build Pipeline

**Prompt:**
Dạy tôi Power Query Day 87 — Capstone Project Phase 2: BUILD. Dựa trên design Day 86, hướng dẫn tôi: (1) Build Dataflow (Bronze/Silver/Gold), (2) Viết function library tái dùng, (3) Setup parameters cho mọi environment, (4) Implement error handling toàn diện, (5) Build 3 semantic models (Summary/Detail/Alert). Cho code M đầy đủ.

**Tags:** #capstone #build #implementation #code

---

## Day 88 — Capstone Project (P3): Optimize & Test

**Prompt:**
Dạy tôi Power Query Day 88 — Capstone Project Phase 3: OPTIMIZE & TEST. Hướng dẫn tôi: (1) Chạy Query Diagnostics toàn bộ, (2) Fix bottleneck, (3) Đảm bảo 90%+ query folding, (4) Load test với dữ liệu lớn, (5) Test error scenarios (source down, schema change, null surge). Cho checklist kiểm tra thực tế. Output: Test report.

**Tags:** #capstone #optimize #test #qa

---

## Day 89 — Capstone Project (P4): Deploy & Document

**Prompt:**
Dạy tôi Power Query Day 89 — Capstone Project Phase 4: DOCUMENT & DEPLOY. Hướng dẫn tôi: (1) Viết README đầy đủ (architecture, dependencies, how to run), (2) Tạo Data Dictionary tự động từ metadata, (3) Setup scheduled refresh + gateway, (4) Deployment pipeline (Dev → Test → Prod), (5) Setup alerting. Cho template tài liệu thực tế.

**Tags:** #capstone #deploy #documentation #production

---

## Day 90 — Mastery Review & Next Steps

**Prompt:**
Dạy tôi Power Query Day 90 — Tổng kết hành trình 90 ngày. Hãy: (1) Review toàn bộ 90 chủ đề đã học, (2) Self-assessment theo chuẩn Microsoft Certified: Data Analyst Associate, (3) Đề xuất 5 chủ đề cần ôn thêm dựa trên những gì tôi còn yếu, (4) Lộ trình tiếp theo (Power BI DAX nâng cao? Azure Data Engineer? Fabric?), (5) Portfolio checklist cuối cùng. Output: Personal Development Plan.

**Tags:** #mastery #review #certification #nextlevel #complete

---
<!-- END OF ROADMAP — 90 Days Total -->
<!-- Day 01-30: FOUNDATION | Day 31-45: INTERMEDIATE | Day 46-60: ADVANCED | Day 61-90: EXPERT -->
<!-- Addon parse rule: split by "## Day ", get block until next "## Day " -->
<!-- Prompt block: từ "**Prompt:**" đến "**Bài tập:**" hoặc "**Tags:**" -->
