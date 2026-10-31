# Development Workflow Rules

## Core Principles
1. **KI First**: Always review all Knowledge Items before starting any new task.
2. **ProjectLog.md**: Read before work, update immediately after any significant change.
3. **Gate 1 (Pre-Code Checklist)**:
   - Read ProjectLog & KIs.
   - List exact files created/modified/deleted.
   - Propose plan and wait for explicit user approval ("ok", "go", "approved").
   - Define self-verification strategy.
   - ⛔ NEVER code or modify files without explicit approval.
4. **Gate 2 (Post-Code Checklist / Definition of Done)**:
   - [ ] Build/run/syntax check PASS.
   - [ ] Real flow verified.
   - [ ] Regression checked.
   - [ ] Edge cases investigated (empty, null, unicode, negative, timeout).
   - [ ] Clean debug output and temporary files.
   - [ ] Honest truth reporting (no guessing).
   - [ ] ProjectLog updated.
   - [ ] ⚡ **Auto-Save & Push-All Skill/Rule**: Nếu phiên làm việc có kỹ thuật mới, kiến trúc đắt giá, hoặc sửa đổi/tạo mới Skill hay Rule, Agent BẮT BUỘC TỰ ĐỘNG lưu trực tiếp vào `SKILL_RULE/skills/` hoặc `SKILL_RULE/rules/` và TỰ ĐỘNG chạy `python sync_skills_rules.py --push-all` trước khi kết thúc task. Không để user phải làm thủ công.
5. **No Silent Scope Creep**: Stop and ask if touching outside approved scope.
6. **Skill & Rule Harvesting & Sync Protocol (Tự Động 100%)**:
   - Khi hoàn thành giải pháp cho một vấn đề kỹ thuật khó, một bài học kiến trúc đắt giá, hoặc tạo mới/sửa đổi Skill hay Rule trong bất kỳ dự án nào:
   - BẮT BUỘC TỰ ĐỘNG cập nhật vào kho trung tâm `GravityCode/SKILL_RULE/skills/` hoặc `GravityCode/SKILL_RULE/rules/`.
   - BẮT BUỘC TỰ ĐỘNG chạy lệnh `python "C:\Users\12953 Bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\SKILL_RULE\sync_skills_rules.py" --push-all` để đồng bộ ngay lập tức ra toàn cục máy tính `~/.gemini/config/` và workspace `.agents/`.
   - Tuyệt đối không để kiến thức/kỹ năng mới bị cô lập riêng lẻ ở dự án con và không đợi người dùng nhắc.
