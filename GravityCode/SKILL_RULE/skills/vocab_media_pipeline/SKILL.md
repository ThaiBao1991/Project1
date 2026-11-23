---
name: vocab-media-pipeline
description: Operate and repair the VocabularyApp media pipeline (8 languages x 2520 days) — filling images/audio, finalizing (pack, upload to the VocabularyData repo, deploy GitHub Pages), cleaning local media, and recovering pipeline state. Use when running or debugging fill_lite, finalize_lite, cleanup_done_media, shrink_audio, publish_online, upload_media_api, deploy_pages, verify_online, audit_all, when media day counts stall, when state files (finalize_done.json, cleanup_done_media.json) disappear, when disk fills on C:, or when Pages/raw media return 404.
---

# VocabularyApp — Media Pipeline Operations

Skill này là bản rút gọn để **vận hành** pipeline media. Chi tiết đầy đủ (bảng lỗi,
lệnh kiểm tra, checklist) nằm ở `GravityCode/VocabularyApp/docs/PIPELINE_RUNBOOK.md`
— đọc file đó trước khi sửa code.

## 1. Khi nào dùng

- Cần biết tiến độ media từng khóa, khóa nào đã upload.
- Một khóa vừa đủ 2.520 ngày và cần finalize/upload/deploy.
- Pipeline dừng, ngày không tăng, đĩa C: tụt, RAM bị kill.
- `finalize_done.json` / `cleanup_done_media.json` mất.
- Media trên web 404, Pages chưa cập nhật.

## 2. Bất biến (không được vi phạm)

1. **Chỉ finalize khi `days_done(slug) == 2520`** — upload bản thiếu sẽ phải upload lại.
2. **Không di chuyển junction** `data/media`, `data/audio`, `data/ai_courses`
   (đang trỏ `D:\VocabularyAppData`) khi pipeline chạy.
3. **State đi qua `tools/statefile.py`**, không ghi tay vào `data/logs/*.json`.
   State có 2 bản: `D:\VocabularyAppData\state\` (chính) + `data/logs/` (sao).
4. **Không xoá media local** trước khi `finalize_done[slug] == done` và
   `web/data/<slug>/index.json` đủ 2.520.
5. Media public là **raw repo** `ThaiBao1991/VocabularyData/main/media/<dir>/mNN.zip`
   — không phải GitHub Releases (release API 404 là bình thường).
6. Mọi lệnh chạy tại `GravityCode/VocabularyApp` với `python -X utf8`.

## 3. Kiểm tra nhanh (đầu mỗi phiên)

```powershell
cd "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp"
$env:PYTHONIOENCODING='utf-8'; chcp 65001 > $null

python -X utf8 -c "import os,sys,shutil; sys.path.insert(0,'tools'); import statefile; m='data/media'; [print(f'{s:22}', sum(1 for d in os.listdir(os.path.join(m,s)) if os.path.isdir(os.path.join(m,d)) and os.listdir(os.path.join(m,d))) if os.path.isdir(os.path.join(m,s)) else 0, '/2520') for s in ['tiếng_nhật','tiếng_anh','tiếng_hàn_quốc','tiếng_nga','tiếng_pháp','tiếng_tây_ban_nha','tiếng_đức','tiếng_trung']]; print('C/D:', round(shutil.disk_usage('C:\\').free/1e9,1), round(shutil.disk_usage('D:\\').free/1e9,1)); print('finalize:', sorted(statefile.load('finalize_done.json'))); print('cleanup:', sorted(statefile.load('cleanup_done_media.json')))"

Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Select-Object ProcessId, @{n='Cmd';e={$_.CommandLine}} | Format-Table -Wrap -AutoSize
```

## 4. Luồng chuẩn

```
fill_remaining_after_chinese.py
  └─ fill_lite.py --lang <slug> --min-free-gb 2.0
       └─ ai.pipeline --stages images,audio,media_verify --from-day <thiếu đầu>
đủ 2520 → finalize_lite.py (watch hoặc --once --lang <slug>)
  ├─ shrink_audio.py (32 kbps)         [bỏ qua nếu SKIP_SHRINK=1]
  ├─ publish_online.py --pack
  ├─ upload_media_api.py  → VocabularyData (chỉ gói đổi)
  ├─ publish_online.py --pages
  └─ deploy_pages.py      → gh-pages
→ statefile: finalize_done[slug]=done
→ cleanup_done_media.py --watch: xoá media/audio/_pipeline local
→ verify_online.py (9/9) + audit_all.py
```

Lệnh thường dùng:

```powershell
# chạy nền toàn bộ hàng đợi
python -X utf8 tools\fill_remaining_after_chinese.py
python -X utf8 tools\finalize_lite.py --watch --interval 300
python -X utf8 tools\cleanup_done_media.py --watch --interval 300

# finalize 1 khóa đã nén audio riêng
$env:SKIP_SHRINK='1'; python -X utf8 tools\finalize_lite.py --once --lang "tiếng_hàn_quốc"

# kiểm tra
python -X utf8 tools\verify_online.py
python -X utf8 tools\audit_all.py --no-online --no-tests
```

## 5. Sự cố → xử lý

| Triệu chứng | Xử lý |
|---|---|
| State `*_done.json` mất | `statefile` tự hợp nhất từ `D:\VocabularyAppData\state`; nếu cả 2 mất thì `statefile.save(...)` với mốc đã upload |
| Log bị rút còn 1 dòng | Bỏ qua log: finalize tự quét `data/media/<slug>` tìm khóa đủ 2.520 |
| `shrink_audio` chạy rất lâu | Kiểm tra bitrate; nếu đã 32 kbps thì `SKIP_SHRINK=1` |
| Upload 404 (`releases/tags/...`) | Media ở raw repo — dùng `upload_media_api.py`, kiểm tra HEAD `raw.githubusercontent.com/.../m01.zip` |
| C: gần đầy (< 2 GB pipeline tự dừng) | `cleanup_done_media.py --once`, xoá `publish/<slug>`, `cleanup_temp.py` |
| `đã có fill_lite chạy (PID …)` | Kiểm tra PID còn sống; nếu stale thì xoá `data/fill_lite.lock` |
| RAM kill | `--workers 1`, giữ RAM trần 700 MB |
| Deploy treo/hỏi mật khẩu | Dùng `push_master.py` / `deploy_pages.py` (header auth) |
| Mojibake console | `chcp 65001` + `PYTHONIOENCODING=utf-8` + `python -X utf8` |

## 6. Trước khi báo xong

- `py_compile` file vừa sửa.
- Chạy thật luồng liên quan.
- `verify_online.py` 9/9 nếu đụng web/media.
- `audit_all.py` 0 FAIL nếu đụng nội dung.
- Cập nhật `projectLog.md` + commit đúng phạm vi (author Thai Bao), push bằng
  `tools/push_master.py`.

## 7. Đọc thêm

- `docs/PIPELINE_RUNBOOK.md` — runbook đầy đủ, lỗi đã từng làm.
- `docs/AUDIT_WORKFLOW.md` — tiêu chí PASS.
- `projectLog.md` — lịch sử (đọc phần cuối).
- `.agents/skills/vocab_ai_media/SKILL.md` — cách sinh ảnh/audio (fallback, quota).
