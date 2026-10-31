# Nhật Ký Dự Án Tổng Hợp (Master ProjectLog) — GravityCode

Tài liệu nhật ký trung tâm theo dõi kiến trúc, kho kỹ năng/quy tắc dùng chung và lịch sử nâng cấp hệ thống của toàn bộ thư mục `GravityCode`.

---

## 2026-10-28 — Thiết Lập Kho Trung Tâm `SKILL_RULE` & Cơ Chế Đồng Bộ Kỹ Năng / Quy Chuẩn Toàn Cục

### 1. Bối Cảnh & Mục Tiêu
- Toàn bộ thư mục `GravityCode` bao gồm 18 dự án con (từ desktop GUI, crawler, AI learning pipeline, Chrome extension đến công cụ doanh nghiệp ERP/Intramart).
- Trước đây, nhiều kỹ năng và quy tắc đắt giá bị phân tán rải rác trong từng dự án con (ví dụ: `vocab_ai_media` trong `VocabularyApp`, tính tọa độ PDF trong `StampByAntigravity`, xuất Excel XML trong `QuanLyCongViecNhom`, vượt CSP iframe trong `HangMauIntramart`).
- Thư mục `.agents/skills` tại `GravityCode` từng có lỗi lặp lồng thư mục `skills/skills`.
- **Mục tiêu**: Xây dựng kho lưu trữ tập trung `SKILL_RULE`, chuẩn hóa toàn bộ 18 Kỹ năng (Skills) và 9 Quy tắc (Rules), thiết lập công cụ đồng bộ 2 chiều `sync_skills_rules.py` tự động xuất ra `~/.gemini/config/` (Global) và `.agents/` (Workspace).

---

### 2. Các Thành Phần Đã Triển Khai

#### A. Kho Trung Tâm `SKILL_RULE/`
- **`SKILL_RULE/README.md`**: Bản đồ tra cứu toàn diện, hướng dẫn thao tác và phân loại chi tiết.
- **`SKILL_RULE/sync_skills_rules.py`**: Công cụ CLI hỗ trợ:
  * `--push-all`: Đẩy toàn bộ Skills & Rules tới `~/.gemini/config/` và `GravityCode/.agents/`.
  * `--check`: Báo cáo tình trạng đồng bộ và độ phủ giữa các tầng.
  * `--harvest`: Tự động quét và thu hoạch Skill/Rule mới từ các subproject con.
- **Thư mục Kỹ Năng (`SKILL_RULE/skills/` — 24 Skills)**:
  * 14 skills kế thừa: `.system`, `add_host_checklist`, `ai_firewall_proxy_relay`, `antigravity_ide_ext_dev`, `chrome_ext_offline_decouple`, `copilot_addon_dev`, `customtkinter_perf_ui`, `fb_media_downloader`, `gemini_api_key_handling`, `generate_roadmap`, `openclaw-fb-addon-check`, `pypack_exe_builder`, `python_auto_install`, `qmh_download_pipeline`.
  * 6 skills bộ công cụ hệ thống: `imagegen`, `openai-docs`, `plugin-creator`, `review-agent`, `skill-creator`, `skill-installer`.
  * 1 skill thu hoạch từ `VocabularyApp`: `vocab_ai_media`.
  * 3 skills mới đóng gói từ dự án: `pdf_coordinate_stamping`, `enterprise_intramart_automation`, `web_gantt_excel_exporter`.
- **Thư mục Quy Chuẩn (`SKILL_RULE/rules/` — 10 Rules)**:
  * `workflow_rules.md`: Bổ sung Nguyên tắc 6 về Protocol Đồng Bộ.
  * `encoding_rules.md`: Chuẩn mã hóa 2 chiều Base64 & Unicode UTF-8.
  * `gemini_api_policy.md`: Xoay vòng theo cụm account, 1h cooldown, Anti-ban delay.
  * `python_desktop_standards.md`: CustomTkinter + ttk.Treeview zero-lag UI.
  * `chrome_extension_standards.md`: Manifest V3, tab messaging, React simulated click.
  * `vocab_ai_content_rules.md`: Schema additive-only, 3-layer curriculum, FSI profiling.
  * `pdf_precision_standards.md`: Hệ tọa độ vector PDF points (72 pt/inch) vs Canvas pixels.
  * `enterprise_addon_standards.md`: Vượt bảo mật CSP khắt khe, lồng đa tầng iframe `all_frames`.
  * `skill_rule_sync_protocol.md`: Protocol bắt buộc thu hoạch & sync kỹ năng toàn cục.
  * `AI_RULES.md`: Quy tắc làm việc trung lập cho các công cụ AI coding (Codex, Gemini, Claude).

---

### 3. Cập Nhật Quy Chuẩn Toàn Cục (Rules Update)
Đã cập nhật mục `## 6. Quy Tắc Thu Hoạch & Đồng Bộ Kỹ Năng / Quy Chuẩn` vào:
- `GravityCode\.agents\AGENTS.md`
- `GravityCode\.agents\GEMINI.md`
- `C:\Users\12953 Bao\.gemini\config\AGENTS.md`
- `C:\Users\12953 Bao\.gemini\config\GEMINI.md`

Tất cả các AI khi làm việc trên máy tính này trong tương lai đều sẽ tuân thủ nguyên tắc:
**"Khi tạo hoặc sửa Skill/Rule trong bất kỳ dự án nào $\rightarrow$ Cập nhật `SKILL_RULE` $\rightarrow$ Chạy `sync_skills_rules.py --push-all`."**


---

## 2026-10-28 (Bổ sung) — Nâng Cấp Quy Tắc Tự Động Hoá 100% & Giao Diện Quản Trị `SkillRuleApp.py`

### 1. Bối Cảnh & Quyết Định Thiết Kế
- Người dùng chỉ thị:
  1. Cập nhật quy tắc bắt buộc AI phải **TỰ ĐỘNG** lưu skill/rule mới vào `SKILL_RULE` và **TỰ ĐỘNG** chạy `--push-all` trước khi kết thúc task, không để người dùng phải làm thủ công.
  2. Xây dựng giao diện Desktop trực quan (CustomTkinter) để người dùng có thể tra cứu, xem trước Markdown và kích hoạt đồng bộ 1-chạm.

### 2. Các Nâng Cấp Đã Thực Hiện
- **Quy tắc Tự Động Hoá (Autonomous Auto-Sync)**:
  * Đã bổ sung **Mục 8 vào Checklist Gate 2 (Post-Code / Definition of Done)**:
    `8. [ ] Tự Động Lưu & Push-All Skill/Rule: Nếu có kỹ thuật mới, bài học kiến trúc đắt giá, hoặc sửa đổi/tạo mới Skill hay Rule, Agent BẮT BUỘC TỰ ĐỘNG lưu trực tiếp vào GravityCode\SKILL_RULE\ và TỰ ĐỘNG chạy lệnh sync --push-all trước khi kết thúc task.`
  * Đã đồng bộ Điều 6 mới vào:
    - `GravityCode\.agents\AGENTS.md` & `GEMINI.md`
    - `C:\Users\12953 Bao\.gemini\config\AGENTS.md` & `GEMINI.md`
    - `SKILL_RULE\rules\workflow_rules.md` & `skill_rule_sync_protocol.md`
- **Giao Diện Desktop `SkillRuleApp.py`**:
  * Viết bằng CustomTkinter theo chuẩn `customtkinter_perf_ui` và bảng màu Catppuccin Mocha.
  * Tích hợp:
    - Bảng Treeview Dark Mode hiển thị trạng thái đồng bộ 2 tầng (Global vs WS).
    - Bộ lọc danh mục (Tất cả, Skills, Rules) và ô tìm kiếm siêu tốc.
    - Khung xem trước Markdown chuẩn Consolas, có nút Copy và Mở File Ngoài.
    - Các nút 1-chạm: `[🚀 ĐỒNG BỘ TẤT CẢ (Push-All)]`, `[🔍 QUÉT THU HOẠCH (Harvest)]`, `[➕ THÊM MỚI]`, `[📁 MỞ THƯ MỤC]`.
    - Xử lý đa luồng (`threading.Thread` + `queue.Queue`), giao diện luôn mượt 60fps không giật đơ.
  * Tạo file launcher tiện dụng `Run_SkillRuleHub.bat`.
