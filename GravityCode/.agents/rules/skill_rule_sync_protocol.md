# Skill & Rule Harvesting and Synchronization Protocol

Áp dụng toàn cục cho tất cả AI Coding Assistant (Antigravity, Gemini, Codex, Claude) và các dự án phát triển trên máy tính này.

---

## 1. Nguyên Tắc Cốt Lõi: "Tự Động Thu Hoạch, Lan Tỏa Toàn Cục"

Mọi kiến thức, quy chuẩn, kỹ thuật giải quyết bài toán khó hoặc bài học kinh nghiệm rút ra từ một dự án đơn lẻ **KHÔNG ĐƯỢC PHÉP BỊ BỎ QUÊN HOẶC CÔ LẬP** trong dự án đó.

- **Kho Lưu Trữ Gốc (Source of Truth)**: `GravityCode\SKILL_RULE\`
  - `SKILL_RULE\skills\<skill_name>\SKILL.md`: Chứa các kỹ năng chuyên biệt có thể tái sử dụng.
  - `SKILL_RULE\rules\<rule_name>.md`: Chứa các quy chuẩn, tiêu chuẩn kỹ thuật bắt buộc tuân thủ.
- **Điểm Thực Thi Của AI (Runtime Discovery Targets)**:
  1. `C:\Users\12953 Bao\.gemini\config\` (Tầng Global — tự động nạp cho mọi phiên làm việc).
  2. `GravityCode\.agents\` (Tầng Workspace — tự động nạp khi mở thư mục cha).

---

## 2. Quy Trình Bắt Buộc TỰ ĐỘNG Của Agent (Autonomous Auto-Harvest & Auto-Push)

Agent **tuyệt đối không để người dùng phải tự sao chép hay chạy lệnh sync thủ công**. Mỗi khi hoàn thành một tính năng phức tạp, sửa lỗi kiến trúc, hoặc tạo mới/sửa đổi Skill hay Rule:

### Bước 1: Agent Tự Động Đóng Gói Vào `SKILL_RULE`
- **Nếu là Kỹ Năng (Skill)**:
  Agent tự động tạo/sửa thư mục `SKILL_RULE/skills/<skill_name>/` với file `SKILL.md` (có đầy đủ YAML frontmatter: `name`, `description`).
- **Nếu là Quy Tắc (Rule)**:
  Agent tự động tạo/sửa file `SKILL_RULE/rules/<rule_name>.md` chuẩn Markdown.

### Bước 2: Agent Tự Động Kích Hoạt Lệnh Đồng Bộ
Trước khi báo cáo hoàn thành nhiệm vụ, Agent **bắt buộc tự động chạy**:
```bash
python "C:\Users\12953 Bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\SKILL_RULE\sync_skills_rules.py" --push-all
```
Lệnh này sẽ tự động:
1. Đẩy các Skill & Rule mới sang `C:\Users\12953 Bao\.gemini\config\` (Global).
2. Đẩy các Skill & Rule mới sang `GravityCode\.agents\` (Workspace).
3. Đảm bảo toàn bộ 100% các dự án khác trên máy tính đều lập tức thừa hưởng kỹ năng mới.

### Bước 3: Cập Nhật Nhật Ký Dự Án (`ProjectLog.md`)
Ghi nhận rõ ràng: Đã đúc kết kỹ năng `<tên_skill>` hoặc quy chuẩn `<tên_rule>` và đã tự động đồng bộ thành công vào `SKILL_RULE`.

---

## 3. Lệnh Kiểm Tra Toàn Vẹn Định Kỳ
Agent hoặc người dùng có thể chạy:
```bash
python "C:\Users\12953 Bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\SKILL_RULE\sync_skills_rules.py" --check
```
Hoặc dùng `--harvest` để tự động rà soát xem có subproject nào có file skill/rule cũ chưa được gom về trung tâm.
