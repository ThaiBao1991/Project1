# 🚀 Power Query — Lộ trình Từ 0 → Expert (90 Ngày)

> **Mục tiêu**: Thành thạo Power Query & M Language ở mức chuyên nghiệp nhất hiện tại (2025–2026)  
> **Bạn đang ở**: Đã hoàn thành **Day 1–30** ✅

---

## 📍 Tổng quan 4 Giai đoạn

```
Giai đoạn 1 (Day 01–30)  : FOUNDATION     ✅ ĐÃ XONG
Giai đoạn 2 (Day 31–45)  : INTERMEDIATE   ← Tiếp theo
Giai đoạn 3 (Day 46–60)  : ADVANCED       
Giai đoạn 4 (Day 61–90)  : EXPERT/PRO     
```

---

## ✅ GIAI ĐOẠN 1 — FOUNDATION (Day 1–30) — ĐÃ HOÀN THÀNH

| Tuần | Chủ đề |
|------|--------|
| Tuần 1 | Pipeline, M code `let→in`, Load, Filter, Type |
| Tuần 2 | Transformation trung cấp |
| Tuần 3 | Kỹ thuật nâng nhẹ |
| Tuần 4 | Production level (Lens/NG Rate, Group By, Top N, Flag) |

**Kết quả sau giai đoạn 1**: Xử lý được dữ liệu thực tế, viết M code cơ bản.

---

## 🟡 GIAI ĐOẠN 2 — INTERMEDIATE (Day 31–45)

> **Mục tiêu**: Tự động hóa, tái sử dụng, xử lý nhiều nguồn dữ liệu

### Tuần 5 — Performance & Parameters (Day 31–35)

| Day | Chủ đề | Nội dung cụ thể |
|-----|--------|-----------------|
| 31 | **Query Folding (P1)** | Khái niệm, cách kiểm tra "View Native Query", tại sao quan trọng |
| 32 | **Query Folding (P2)** | Folding breaker là gì, thứ tự step ảnh hưởng thế nào |
| 33 | **Table.Buffer & List.Buffer** | Khi nào dùng, khi nào không, tác động memory |
| 34 | **Parameters (Tham số động)** | Tạo parameter, dùng trong query, thay đổi source động |
| 35 | **Dynamic Source Path** | File path, sheet name từ parameter, không hardcode |

### Tuần 6 — Custom Functions & Error Handling (Day 36–40)

| Day | Chủ đề | Nội dung cụ thể |
|-----|--------|-----------------|
| 36 | **Custom Function (P1)** | Tạo `fnCleanName`, `fnGetDate`, cú pháp `(x) => ...` |
| 37 | **Custom Function (P2)** | Function nhiều tham số, optional param, documentation |
| 38 | **Error Handling (P1)** | `try...otherwise`, bắt lỗi cột, null handling |
| 39 | **Error Handling (P2)** | `Value.ReplaceErrors`, validate dữ liệu đầu vào |
| 40 | **Function Library** | Tổ chức function vào "Queries" library tái dùng |

### Tuần 7 — Multi-Source & Folder Merge (Day 41–45)

| Day | Chủ đề | Nội dung cụ thể |
|-----|--------|-----------------|
| 41 | **Folder.Files** | Load tất cả file Excel trong 1 thư mục tự động |
| 42 | **Combine Binaries** | Merge nhiều file cùng cấu trúc thành 1 bảng |
| 43 | **Multi-sheet & Multi-table** | Load nhiều sheet, union lại |
| 44 | **Web Data (P1)** | Load từ URL, HTML table, CSV online |
| 45 | **Mini Project #2** | Tổng hợp dữ liệu từ nhiều file Excel báo cáo hàng tháng |

**Kết quả sau giai đoạn 2**: Viết query tự động, tái sử dụng code, merge nhiều nguồn.

---

## 🔴 GIAI ĐOẠN 3 — ADVANCED (Day 46–60)

> **Mục tiêu**: Viết M code như một lập trình viên — functional programming, recursion, architecture

### Tuần 8 — Functional Programming trong M (Day 46–50)

| Day | Chủ đề | Nội dung cụ thể |
|-----|--------|-----------------|
| 46 | **Type System sâu** | Custom type, `type table [Col1=text, Col2=number]`, metadata |
| 47 | **List.Accumulate** | Dùng như `reduce()` — cộng dồn, build string, aggregate |
| 48 | **List.Transform & Record.TransformFields** | Higher-order functions, map pattern |
| 49 | **Table.TransformRows** | Transform từng row bằng function, linh hoạt hơn AddColumn |
| 50 | **Recursion** | Hàm tự gọi lại, xử lý dữ liệu lồng nhau |

### Tuần 9 — API & JSON Advanced (Day 51–55)

| Day | Chủ đề | Nội dung cụ thể |
|-----|--------|-----------------|
| 51 | **REST API (P1)** | `Web.Contents`, headers, authentication basic |
| 52 | **REST API (P2)** | Pagination — loop qua nhiều trang API tự động |
| 53 | **JSON Nested (P1)** | Parse JSON phức tạp, `Record.Field`, `Table.ExpandRecordColumn` |
| 54 | **JSON Nested (P2)** | Flatten JSON nhiều tầng, xử lý array trong object |
| 55 | **OAuth2 & Token** | Xác thực OAuth2 trong M, refresh token |

### Tuần 10 — Performance Expert & Diagnostics (Day 56–60)

| Day | Chủ đề | Nội dung cụ thể |
|-----|--------|-----------------|
| 56 | **Query Diagnostics Tool** | Dùng Power BI Query Diagnostics, đọc log |
| 57 | **Lazy Evaluation** | Hiểu M evaluate như thế nào, tránh tính toán thừa |
| 58 | **Environment & Scope** | Biến môi trường, closure, variable scope trong M |
| 59 | **Optimization Patterns** | Filter early, remove columns sớm, tránh join phức tạp |
| 60 | **Mini Project #3** | Refactor 1 query GUI-heavy → code thuần, đo performance trước/sau |

**Kết quả sau giai đoạn 3**: Viết M code như developer, gọi API, tối ưu query thực sự.

---

## 🟣 GIAI ĐOẠN 4 — EXPERT / PROFESSIONAL (Day 61–90)

> **Mục tiêu**: Kiến trúc dữ liệu, tích hợp hệ thống, team-level solutions

### Tuần 11 — Architecture & Dataflows (Day 61–65)

| Day | Chủ đề | Nội dung cụ thể |
|-----|--------|-----------------|
| 61 | **Dataflows Gen1** | Power BI Dataflows — tạo, publish, reuse |
| 62 | **Dataflows Gen2 (Fabric)** | Microsoft Fabric Dataflow Gen2, Spark-based |
| 63 | **Centralized Data Layer** | Single source of truth — thiết kế reusable transformation layer |
| 64 | **Incremental Refresh** | Chỉ load data mới, không load lại toàn bộ |
| 65 | **DirectQuery vs Import** | Khi nào dùng cái nào, Hybrid Table |

### Tuần 12 — Advanced Source Connectors (Day 66–70)

| Day | Chủ đề | Nội dung cụ thể |
|-----|--------|-----------------|
| 66 | **SQL Server & Stored Proc** | Gọi stored procedure, native query, parametrize |
| 67 | **SharePoint & OneDrive** | Load file từ SharePoint, update tự động |
| 68 | **Azure Data Sources** | Azure SQL, Blob Storage, Data Lake |
| 69 | **Custom Connector (.pqx)** | Viết connector riêng bằng M (nâng cao) |
| 70 | **Python/R Integration** | Gọi Python script trong Power BI transformation |

### Tuần 13 — M Language Master (Day 71–75)

| Day | Chủ đề | Nội dung cụ thể |
|-----|--------|-----------------|
| 71 | **Section Documents** | Tổ chức M code thành section, module |
| 72 | **Expression.Evaluate** | Dynamic code evaluation trong M |
| 73 | **Intrinsic Functions Deep** | `Value.*`, `Splitter.*`, `Comparer.*`, `Combiner.*` |
| 74 | **Record & List Kung Fu** | Advanced manipulation, zip, transpose, reshape |
| 75 | **M Specification** | Đọc hiểu official M spec, grammar, BNF |

### Tuần 14 — Team & Enterprise Patterns (Day 76–80)

| Day | Chủ đề | Nội dung cụ thể |
|-----|--------|-----------------|
| 76 | **Code Review & Standards** | Đặt tên bước, comment M code, naming convention |
| 77 | **Version Control cho M** | Export `.pq` file, dùng Git với Power Query |
| 78 | **Deployment Pipelines** | Power BI CI/CD, publish workspace, environment |
| 79 | **Security & Row-Level Security** | RLS, dynamic query theo user |
| 80 | **Documentation Pattern** | Tự động gen document từ metadata |

### Tuần 15 — Real-World Systems (Day 81–85)

| Day | Chủ đề | Nội dung cụ thể |
|-----|--------|-----------------|
| 81 | **ETL Pipeline Design** | Staging → Transform → Load pattern |
| 82 | **Data Validation Framework** | Build schema validator bằng M |
| 83 | **Scheduling & Gateway** | On-premises data gateway, schedule refresh |
| 84 | **Alerting & Monitoring** | Power Automate + Power BI alert |
| 85 | **Real-time Data (DirectQuery)** | DirectQuery live connection, freshness trade-off |

### Tuần cuối — Capstone & Mastery (Day 86–90)

| Day | Chủ đề | Nội dung cụ thể |
|-----|--------|-----------------|
| 86 | **Capstone Project (P1)** | Design end-to-end: Source → Dataflow → Model → Report |
| 87 | **Capstone Project (P2)** | Build full pipeline tự động cho production |
| 88 | **Capstone Project (P3)** | Tối ưu, test, document toàn bộ solution |
| 89 | **Benchmark & Self-Eval** | Đo lại performance, so sánh Day 1 vs Day 89 |
| 90 | **Presentation & Portfolio** | Viết README, demo, đưa vào CV/portfolio |

**Kết quả sau giai đoạn 4**: Có thể thiết kế & triển khai hệ thống dữ liệu doanh nghiệp.

---

## 📊 Bảng Tổng Hợp Toàn Bộ Lộ trình

| Giai đoạn | Ngày | Level | Có thể làm gì |
|-----------|------|-------|---------------|
| Foundation | 1–30 | ⭐⭐ | Xử lý bảng Excel, lọc, tính toán, NG/OK |
| Intermediate | 31–45 | ⭐⭐⭐ | Auto-merge nhiều file, parameters, custom function |
| Advanced | 46–60 | ⭐⭐⭐⭐ | API, recursion, performance tuning, diagnostics |
| Expert | 61–90 | ⭐⭐⭐⭐⭐ | Enterprise ETL, Dataflows, Fabric, team solutions |

---

## 🎯 Chuẩn kỹ năng Expert 2025–2026

Theo **Microsoft & cộng đồng Power BI** hiện tại, "expert" phải đạt:

| Tiêu chí | Mục tiêu |
|----------|----------|
| Query Folding | 90%+ transformations phải fold được |
| Custom Functions | Build library tái dùng cho team |
| Error Handling | Không bao giờ query crash production |
| API/Web | Gọi được REST API pagination |
| Performance | Dùng Query Diagnostics để đo bottleneck |
| Architecture | Thiết kế Dataflow → Model → Report |
| M Mastery | Đọc được M spec, viết không dùng GUI |

---

## 💡 Tips học hiệu quả nhất

1. **Mỗi ngày 1 bài** — không nhảy cóc
2. **Luôn có bài tập thực hành** — dùng dữ liệu Nikon/Lens thực tế
3. **Refactor code cũ** — sau giai đoạn 3, quay lại Day 1–30 viết lại cho đẹp hơn
4. **Đọc thêm**: *"Power Query M Primer" — Ben Gribaudo* (miễn phí online)
5. **Cộng đồng**: Power BI Community, Reddit r/PowerBI, Stack Overflow

---

> 📌 **Kết luận**: Với **90 ngày** theo lộ trình này, bạn sẽ đạt mức chuyên nghiệp nhất hiện tại có thể — tương đương Data Engineer level trong hệ sinh thái Microsoft.  
> Bạn đã xong **30/90 ngày** rồi — còn **60 ngày** nữa! 💪

*Cập nhật: 28/06/2026 — Dựa trên Microsoft Power Query M Spec + Power BI Community Standards 2025–2026*
