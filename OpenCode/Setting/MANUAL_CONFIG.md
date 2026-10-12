# Hướng Dẫn Cấu Hình Thủ Công OpenCode (Manual Config Guide)

Tài liệu này mô tả cách chỉnh sửa cấu hình OpenCode bằng tay (không qua CLI) để tùy biến model, rules, skills, plugins, MCP.

---

## 🚀 Quick Start: GUI Config Manager

**App Python có sẵn tại:** `C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\OpenCode\Setting\OpencodeConfigManager\`

**Chạy:** Double-click `run.bat` hoặc `python src/main.py`

**Tính năng:**
- 🤖 **Models tab**: Xem tất cả model, lọc free/paid/vision, test model, set default
- 🎯 **Skills tab**: Xem skill đã cài, thêm folder skill, tạo skill mới, xem SKILL.md
- 📋 **Rules tab**: Chỉnh sửa AGENTS.md, xem workflow_rules.md
- 🔑 **API Keys tab**: Thêm/xóa/test API key cho Google, OpenRouter, DeepSeek, Groq...
- 📚 **Guide tab**: Hướng dẫn chi tiết free models cho từng provider

---

## 1. File cấu hình chính: `opencode.json`

**Vị trí:** `C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\opencode.json`

**Cấu trúc:**
```json
{
  "$schema": "https://opencode.ai/config.json",
  "providers": ["opencode"],           // Danh sách provider được phép
  "model": "opencode/gemini-3.8-flash", // Model mặc định (provider/model)
  "agent": {
    "rules": "path/to/AGENTS.md",       // File rules toàn cục
    "skills": "path/to/skills.json",    // File trỏ đến thư mục skills
    "plugins": "path/to/plugins.json",  // File trỏ đến thư mục plugins
    "mcp": "path/to/mcp_config.json"    // File MCP servers
  }
}
```

### Các trường có thể sửa:

| Trường | Mô tả | Ví dụ giá trị |
|--------|-------|---------------|
| `providers` | Mảng provider cho phép | `["opencode"]`, `["opencode", "google", "openrouter"]` |
| `model` | Model mặc định (format: `provider/model-id`) | `opencode/gemini-3.8-flash`, `opencode/gpt-5` |
| `agent.rules` | Đường dẫn tuyệt đối file AGENTS.md | `C:/Users/.../AGENTS.md` |
| `agent.skills` | Đường dẫn tuyệt đối file skills.json | `C:/Users/.../skills.json` |
| `agent.plugins` | Đường dẫn tuyệt đối file plugins.json | `C:/Users/.../plugins.json` |
| `agent.mcp` | Đường dẫn tuyệt đối file mcp_config.json | `C:/Users/.../mcp_config.json` |

---

## 2. File AGENTS.md - Quy tắc làm việc

**Vị trí:** `C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\OpenCode\Setting\.opencode\AGENTS.md`

**Cách chỉnh:**
- Mở file bằng notepad/VS Code
- Thêm/sửa/xóa các section: Core Principles, Gate 1, Gate 2, Encoding rules, Gemini Safe rules
- Mỗi dự án có thể tạo AGENTS.md riêng và trỏ trong `opencode.json`

---

## 3. File skills.json - Quản lý Skills

**Vị trí:** `C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\OpenCode\Setting\.opencode\skills.json`

**Cấu trúc:**
```json
{
  "entries": [
    { "path": "C:/Users/.../skills" },           // Thư mục local
    { "path": "https://github.com/user/repo" }   // Hoặc GitHub repo
  ]
}
```

**Thêm skill mới thủ công:**
1. Tạo thư mục skill: `C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\OpenCode\Setting\.opencode\skills\ten-skill\`
2. Tạo file `SKILL.md` bên trong (theo format skill)
3. Thêm entry vào `skills.json` nếu muốn trỏ đến thư mục cha chứa nhiều skill

---

## 4. File plugins.json - Quản lý Plugins

**Vị trí:** `C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\OpenCode\Setting\.opencode\plugins.json`

**Cấu trúc:** Giống `skills.json`, trỏ đến thư mục chứa plugin (mỗi plugin có `plugin.json`)

---

## 5. File mcp_config.json - MCP Servers

**Vị trí:** `C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\OpenCode\Setting\.opencode\mcp_config.json`

**Cấu trúc:**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "xxx" }
    }
  }
}
```

---

## 6. Thư mục rules/

**Vị trí:** `C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\OpenCode\Setting\.opencode\rules\`

- Chứa các file `.md` quy tắc bổ sung
- Được load tự động khi agent khởi động
- Có thể tạo file mới: `coding_style.md`, `git_rules.md`, v.v.

---

## 7. Thay đổi Model (đổi model free khác)

**Cách 1: Sửa `opencode.json`**
```json
"model": "opencode/gemini-3.7-flash"
```

**Cách 2: Chạy CLI tạm**
```bash
opencode -m opencode/gemini-3.5-flash
```

**Danh sách model free vision (xem bằng `opencode models`):**
- `opencode/gemini-3.8-flash` ⭐ (mới nhất)
- `opencode/gemini-3.7-flash`
- `opencode/gemini-3.6-flash`
- `opencode/gemini-3.5-flash`
- `opencode/gemini-3-flash`
- `opencode/deepseek-v4-flash-vision-exp`
- `opencode/gemini-3.1-pro`

---

## 8. Thêm Provider (Google, OpenRouter, v.v.)

**Bước 1: Login provider**
```bash
opencode providers login google
opencode providers login openrouter
```

**Bước 2: Cập nhật `opencode.json`**
```json
"providers": ["opencode", "google", "openrouter"]
```

**Bước 3: Chọn model của provider đó**
```json
"model": "google/gemini-3.8-flash"
```
Hoặc chạy: `opencode -m google/gemini-3.8-flash`

---

## 9. Tạo Skill Mới (Template)

**Vị trí:** `C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\OpenCode\Setting\.opencode\skills\ten-skill\SKILL.md`

**Template tối thiểu:**
```markdown
# Skill: ten-skill

# Mô tả ngắn gọn skill này làm gì

## Trigger
Khi nào skill được kích hoạt (ví dụ: "khi user hỏi về X", "khi thấy file Y")

## Workflow
1. Bước 1
2. Bước 2

## References
- File/script tham khảo
```

---

## 10. Sync sang dự án khác

Copy toàn bộ folder `OpenCode/Setting/.opencode/` sang dự án mới, sau đó cập nhật đường dẫn trong `opencode.json` của dự án đó.

---

## 11. Các lệnh CLI hữu ích

| Lệnh | Mô tả |
|------|-------|
| `opencode models` | Xem tất cả model khả dụng |
| `opencode providers list` | Xem provider đã login |
| `opencode providers login <name>` | Login provider mới |
| `opencode providers logout <name>` | Logout provider |
| `opencode -m <model>` | Chạy với model cụ thể |
| `opencode --pure` | Chạy không load plugin/skill ngoại |
| `opencode agent` | Quản lý agent |

---

## 12. Troubleshooting

**Model không load được skill/rules:**
- Kiểm tra đường dẫn tuyệt đối trong `opencode.json` (phải dùng `/` không phải `\`)
- Đảm bảo file JSON hợp lệ (không có trailing comma)

**Provider không hiện model:**
- Chạy `opencode providers logout <name>` rồi `login` lại
- Kiểm tra API key trong `%LOCALAPPDATA%\opencode\auth.json`

**Skill không hoạt động:**
- Kiểm tra `skills.json` trỏ đúng thư mục cha (chứa nhiều folder skill)
- Mỗi skill phải có file `SKILL.md` ở root của folder skill

---

*Cập nhật: 11/10/2026 - Tạo từ cấu hình Antigravity*