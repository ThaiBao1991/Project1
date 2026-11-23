# PIPELINE RUNBOOK — VocabularyApp (đọc file này trước khi làm bất cứ gì)

Cập nhật: **20/11/2026 19:05** · Người cập nhật: phiên làm việc OpenCode
Đây là tài liệu "cầm tay chỉ việc": đọc 5 phút là hiểu dự án, biết lệnh nào để kiểm tra,
biết lỗi nào đã gặp và sửa thế nào. Không thay thế `projectLog.md` (lịch sử chi tiết)
nhưng thay thế việc phải đọc 190 KB log.

---

## 0. Thứ tự đọc tài liệu

1. **File này** — cách vận hành, lệnh, sự cố.
2. `projectLog.md` — đọc **phần cuối** để biết việc mới nhất.
3. `docs/AUDIT_WORKFLOW.md` — tiêu chí PASS và lệnh audit.
4. `docs/UPGRADE_PLAN.md` — roadmap UI/tính năng (P0…).
5. `docs/ONLINE_PHONE.md` — cách app chạy trên điện thoại (localStorage, offline).

---

## 1. Bức tranh trong 1 phút

- App học từ vựng **8 ngôn ngữ × 2.520 ngày** (~20.160 ngày nội dung).
- **Nội dung chữ: đã đủ 8/8 khóa** (mẫu câu, câu thông dụng, ngữ pháp, hội thoại, quiz).
- **Media (ảnh + audio): xong 5 khóa** (Nhật, Trung, Anh, Hàn, Tây Ban Nha) — đã upload và đã xoá local.
  3 khóa còn lại đang bù dần: Đức → Pháp → Nga.
- Web tĩnh deploy lên **GitHub Pages** (`https://thaibao1991.github.io/Project1/`).
- Media nằm ở **repo riêng** `ThaiBao1991/VocabularyData`, tải qua
  `https://raw.githubusercontent.com/ThaiBao1991/VocabularyData/main/media/<dir>/mNN.zip`.
  **Không phải GitHub Releases** (release API trả 404 là bình thường).
- Dữ liệu nặng (media/audio/ai_courses) nằm ở **D:\VocabularyAppData**, nối vào project
  bằng **junction** (`data/media`, `data/audio`, `data/ai_courses`).

---

## 2. Bản đồ đường dẫn

| Đường dẫn | Vai trò | Ghi chú |
|---|---|---|
| `GravityCode/VocabularyApp/` | thư mục app | mọi lệnh chạy tại đây |
| `data/media/<slug>/dNNNN/` | ảnh + audio từng ngày | junction → `D:\VocabularyAppData\media` |
| `data/audio/<slug>/` | cache TTS | junction → `D:\VocabularyAppData\audio` |
| `data/ai_courses/<slug>/course.json` | nội dung khóa học | junction → `D:\VocabularyAppData\ai_courses` |
| `data/logs/` | log + **bản sao** state | không phải nguồn duy nhất nữa |
| `D:\VocabularyAppData\state\` | **state chính** (`finalize_done.json`, `cleanup_done_media.json`, …) | có `history/` 30 bản |
| `D:\VocabularyAppData\state\locks\` | **lock tiến trình** (`pipeline_daemon`, `fill_remaining`, …) | không đặt ở `data/logs` vì hay bị xoá |
| `web/data/<slug>/index.json` | manifest ngày cho web | **junction → `D:\VocabularyAppData\web_data`**; phải đủ 2.520 ngày mới cleanup |
| `web/data/<slug>/day/NNNN.json` | dữ liệu 1 ngày cho web | có `media_map` |
| `publish/<slug>/media/*.zip` | gói media tạm để upload | **junction → `D:\VocabularyAppData\publish`** (tránh đầy C:); xoá sau finalize |
| `tools/` | toàn bộ pipeline | xem bảng mục 5 |

---

## 3. Trạng thái hiện tại (20/11/2026 19:04)

| Khóa | Media local | Trạng thái |
|---|---:|---|
| Nhật | 0/2.520 | ✅ đã upload + deploy (local đã dọn) |
| Trung | 0/2.520 | ✅ đã upload + enrich + deploy |
| Anh | 0/2.520 | ✅ đã upload + deploy (audio 32 kbps) |
| **Hàn** | 0/2.520 | ✅ upload 85 gói 21/11 21:05 (commit `93220ee4`), local đã dọn |
| **Tây Ban Nha** | 0/2.520 | ✅ upload 85 gói 23/11 01:54 (commit `2d928f32`), local đã dọn |
| **Đức** | **1.023/2.520** | đang chạy |
| Pháp / Nga | 600/2.520 | chờ |

- Còn **5.337 ngày** media → khoảng **2,6 ngày** (85 ngày/giờ).
- Xem nhanh: `python -X utf8 tools\progress.py`.

### 3.1. Hiệu năng trang học (tối ưu 23/11)

- Web ưu tiên file tĩnh `web/data/<slug>/index.json` + `day/<n>.json` ở **cả local**,
  chỉ fallback API. Đo thật: đổi khóa lần đầu **~0,45 s** (index 432 KB), lần sau
  **1–2 ms**; mở 1 ngày **~50 ms** lần đầu, **1–2 ms** khi đã cache.
- `bridge_server` đọc được `course.json.gz` (Nhật/Trung) và cache **LRU 3 khóa**
  (trước: 1 khóa ⇒ đổi qua lại parse lại 87–101 MB, 1,2–2,1 s/lần).
- Ô ngày **không còn kẹt disabled**: timeout 10 s, tự mở khóa khi lỗi/rỗng.
- Đĩa lúc ghi (21/11 20:15): **C: 3,86 GB** · **D: 23,4 GB** trống.
  → C: thấp vì `pagefile.sys` 22,5 GB + `hiberfil.sys` 2,9 GB trên ổ 7,3 GB RAM;
  pipeline tự dừng khi C: < 2 GB (xem sự cố #5).
- Process đang chạy (kiểm tra bằng lệnh ở mục 6):
  `fill_remaining_after_chinese.py` → `fill_lite.py --lang tiếng_hàn_quốc` →
  `ai.pipeline ... --from-day …`, kèm `finalize_lite.py --watch` và
  `cleanup_done_media.py --watch`.

---

## 4. Luồng logic chuẩn

```
        ┌─────────────────────────────────────────────────────────────┐
        │ 1. FILL (bù media)                                          │
        │    fill_remaining_after_chinese.py                          │
        │      └─ fill_lite.py --lang <slug> --min-free-gb 2.0        │
        │           └─ ai.pipeline --stages images,audio,media_verify │
        │                └─ ghi data/media/<slug>/dNNNN + index.json  │
        │    Lặp đến khi days_done(slug) == 2520                      │
        └───────────────────────────┬─────────────────────────────────┘
                                    │ đủ 2.520 ngày
                                    ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 2. FINALIZE (finalize_lite.py, chạy --watch hoặc --once)     │
        │    a. shrink_audio.py   48/64 → 32 kbps mono (bỏ qua nếu    │
        │       SKIP_SHRINK=1)                                        │
        │    b. publish_online.py --pack --lang <slug>                │
        │       → publish/<slug>/media/mNN.zip (85 gói)               │
        │    c. upload_media_api.py --lang <slug>                     │
        │       → commit lên repo VocabularyData (chỉ gói đổi)        │
        │    d. publish_online.py --pages  (copy web/data)            │
        │    e. deploy_pages.py            (push nhánh gh-pages)      │
        │    → statefile: finalize_done[slug] = done                  │
        └───────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 3. CLEANUP (cleanup_done_media.py --watch)                  │
        │    chỉ xoá khi: publish/<slug> đã xong + web/data đủ 2.520  │
        │    xoá: data/media/<slug>, data/audio/<slug>,              │
        │         data/ai_courses/<slug>/_pipeline                   │
        │    → statefile: cleanup_done_media[slug] = {freed_mb}      │
        └───────────────────────────┬─────────────────────────────────┘
                                    ▼
        ┌─────────────────────────────────────────────────────────────┐
        │ 4. KIỂM TRA (tuỳ chọn nhưng nên chạy sau mỗi khóa)          │
        │    verify_online.py   → 9/9 PASS                            │
        │    audit_all.py       → 0 FAIL                              │
        └─────────────────────────────────────────────────────────────┘
```

Nguyên tắc: **mỗi bước idempotent** — chạy lại không sinh dữ liệu trùng, không upload
lặp gói không đổi (upload so SHA git-blob), media đã có thì bỏ qua.

---

## 4.1. Daemon giữ pipeline sống (từ 21/11)

`tools/pipeline_daemon.py` là **một tiến trình duy nhất** giữ 3 job nền:

```
pipeline_daemon.py  (lock: pipeline_daemon.lock)
  ├─ fill_remaining_after_chinese.py   (lock: fill_remaining.lock)
  ├─ finalize_lite.py --watch          (lock: finalize_watch.lock)
  └─ cleanup_done_media.py --watch     (lock: cleanup_watch.lock)
```

**Mọi lock nằm ở `D:\VocabularyAppData\state\locks\`** (không phải `data/logs` —
thư mục đó từng bị xoá ngoài ý muốn, làm mất tác dụng chống trùng).

- Con chết ⇒ tự bật lại (backoff 60→600 giây, không spam log).
- Con thoát ngay mã 0 ⇒ hiểu là "đã có bản chạy tay giữ khoá" ⇒ thử lại sau 5 phút.
- `finalize` chỉ chạy 1 lượt tại 1 thời điểm (`finalize_run.lock`) nên watcher và
  chạy tay không bao giờ pack/upload trùng.
- C: < 2,5 GB ⇒ tự chạy `cleanup_done_media --once` + `cleanup_temp.py` (10 phút/lần).
- Trạng thái: `data/logs/pipeline_status.json`; log con: `data/logs/daemon_<tên>.log`
  (tự xoay khi > 10 MB).

Lệnh:

```powershell
python -X utf8 tools\pipeline_daemon.py --status
python -X utf8 tools\pipeline_daemon.py                 # chạy nền
python -X utf8 tools\pipeline_daemon.py --stop
python -X utf8 tools\pipeline_daemon.py --install-startup    # tự chạy khi đăng nhập
python -X utf8 tools\pipeline_daemon.py --uninstall-startup
```

Test: `python -X utf8 tools\test_proc_lock.py` và `tools\test_pipeline_daemon.py`.

---

## 5. Bảng công cụ

| Tool | Việc | Chạy khi nào |
|---|---|---|
| `tools/fill_remaining_after_chinese.py` | supervisor bù media lần lượt 6 khóa, retry, chờ đĩa | chạy nền 1 lần |
| `tools/fill_lite.py` | bù media 1 khóa, RAM trần, workers=1, resume theo `first_missing` | do supervisor gọi |
| `tools/finalize_lite.py` | pack → upload → pages → deploy; `--watch` tự bắt khóa đủ 2.520 | chạy nền |
| `tools/cleanup_done_media.py` | xoá media local sau khi upload xong | chạy nền |
| `tools/shrink_audio.py` | nén MP3 32 kbps, giữ nguyên tên/ref | trong finalize |
| `tools/publish_online.py` | `--pack` tạo zip; `--pages` copy web/data | trong finalize |
| `tools/upload_media_api.py` | đẩy zip lên repo `VocabularyData` (chỉ gói đổi) | trong finalize |
| `tools/deploy_pages.py` | push `web/` lên `gh-pages`, dọn temp | trong finalize |
| `tools/verify_online.py` | kiểm tra Pages + raw media (9 mục) | sau mỗi khóa |
| `tools/audit_all.py` | audit tiến độ/nội dung/media/dung lượng/git | trước khi báo xong |
| `tools/statefile.py` | state 2 bản + history, hợp nhất theo `at` | được import bởi các tool trên |
| `tools/push_master.py` | push `master` bằng header auth (không hỏi mật khẩu) | sau khi commit |
| `tools/test_statefile.py` | test kho state (10 case) | khi sửa statefile |
| `tools/pipeline_daemon.py` | giữ 3 job nền luôn sống, tự restart, disk guard, tự chạy khi đăng nhập | chạy nền 1 lần |
| `tools/progress.py` | in tiến độ + tốc độ + ETA + đĩa + trạng thái daemon (chỉ đọc) | bất cứ lúc nào |
| `tools/proc_lock.py` | khoá 1 tiến trình theo tên (PID + lock rác) | import bởi các tool |

---

## 6. Lệnh kiểm tra nhanh (copy-paste nguyên khối)

```powershell
cd "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp"
$env:PYTHONIOENCODING='utf-8'; chcp 65001 > $null

# 1) Tiến độ media + đĩa + state
python -X utf8 -c "import os,sys,shutil; sys.path.insert(0,'tools'); import statefile; m='data/media'; [print(f'{s:22}', sum(1 for d in os.listdir(os.path.join(m,s)) if os.path.isdir(os.path.join(m,d)) and os.listdir(os.path.join(m,d))) if os.path.isdir(os.path.join(m,s)) else 0, '/2520') for s in ['tiếng_nhật','tiếng_anh','tiếng_hàn_quốc','tiếng_nga','tiếng_pháp','tiếng_tây_ban_nha','tiếng_đức','tiếng_trung']]; print('C/D free GB:', round(shutil.disk_usage('C:\\').free/1e9,1), round(shutil.disk_usage('D:\\').free/1e9,1)); print('finalize:', sorted(statefile.load('finalize_done.json'))); print('cleanup:', sorted(statefile.load('cleanup_done_media.json')))"

# 2) Process đang chạy
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Select-Object ProcessId, @{n='Cmd';e={$_.CommandLine}} | Format-Table -Wrap -AutoSize

# 3) Log mới nhất
Get-Content data\logs\fill_remaining.log -Tail 5
Get-Content data\logs\finalize_lite.log -Tail 10
Get-Content data\logs\cleanup_done_media.log -Tail 5

# 4) Kiểm tra online / audit
python -X utf8 tools\verify_online.py
python -X utf8 tools\audit_all.py --no-online --no-tests
```

Git:
```powershell
cd "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1"
git status --porcelain -- "GravityCode/VocabularyApp"
git -c user.name="Thai Bao" -c user.email="thaibao1991dn@gmail.com" commit -m "..."
python -X utf8 GravityCode\VocabularyApp\tools\push_master.py
```

---

## 7. Quy trình thường ngày (5 phút)

1. Chạy khối lệnh mục 6 → ghi lại số ngày từng khóa.
2. Nếu **một khóa vừa đủ 2.520** mà state chưa `done`:
   - Kiểm tra audio đã 32 kbps chưa (nếu vừa `shrink_audio` xong thì đặt `SKIP_SHRINK=1`).
   - `python -X utf8 tools\finalize_lite.py --once --lang "<slug>"` (job nền, 10–30 phút).
3. Sau finalize: `verify_online.py` phải 9/9; xem `cleanup_done_media.log` xác nhận đã xoá.
4. Chạy `audit_all.py --no-online --no-tests` nếu vừa sửa code/nội dung.
5. Cập nhật `projectLog.md` (mục mới ở cuối) + commit + push.

---

## 8. Sự cố & cách xử lý

| # | Triệu chứng | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|---|
| 1 | `finalize_done.json` / `cleanup_done_media.json` mất | file bị xoá ngoài ý muốn (dọn worktree, tool ngoài) | `statefile` tự hợp nhất từ `D:\VocabularyAppData\state`; nếu cả 2 mất, khôi phục tay bằng `statefile.save(...)` với mốc đã upload |
| 2 | `fill_lite.log` chỉ còn 1 dòng, log finalize biến mất | log bị rút/xoá ngoài ý muốn | **Không dựa vào log nữa**: finalize quét trực tiếp `data/media/<slug>` |
| 3 | `finalize` đứng rất lâu ở `shrink_audio.py` | quét lại 50–100k file dù phần lớn đã 32 kbps | kiểm tra bitrate vài ngày; nếu đã nén thì `SKIP_SHRINK=1` rồi chạy lại |
| 4 | Upload báo 404 với `releases/tags/...` | media nằm ở **raw repo**, không phải Releases | dùng `upload_media_api.py`; kiểm tra bằng HEAD `raw.githubusercontent.com/.../m01.zip` |
| 5 | C: tụt nhanh, pipeline sắp dừng | temp/publish/cache trên C:, hoặc tiến trình khác | chạy cleanup, xoá `publish/<slug>`, `tools/cleanup_temp.py`, kiểm tra `%TEMP%` |
| 6 | Pipeline bị kill RAM | workers quá cao / model lớn | giữ `--workers 1`, RAM trần trong `fill_lite` (700 MB) |
| 7 | `đã có fill_lite chạy (PID …) — thoát` | lock `data/fill_lite.lock` còn PID cũ | kiểm tra PID còn sống không; nếu chết thì xoá lock |
| 8 | Deploy treo / hỏi mật khẩu | thiếu token/header auth | dùng `push_master.py` / `deploy_pages.py` (đã dùng `http.extraheader`), không nhúng token vào URL |
| 9 | Console hiện `?` / mojibake | thiếu UTF-8 | `chcp 65001`, `$env:PYTHONIOENCODING='utf-8'`, `python -X utf8`; **file vẫn UTF-8**, chỉ console sai |
| 10 | `ai.pipeline` không tăng ngày | hết quota/thời gian chờ, `--from-day` cũ | xem log pipeline; supervisor tự retry, hoặc chạy lại với `--from-day <ngày thiếu đầu>` |
| 11 | Task `VocabularyApp-CheckDone` báo lỗi `2147942402` (0x80070002 = file not found) | `Execute` bị cắt tại dấu cách: `C:\...\Project\Python\Python` + phần còn lại nằm trong `Arguments` | **Đã xoá task ngày 20/11/2026** (chỉ là thông báo, không ảnh hưởng pipeline). Muốn có lại thì tạo task chạy `cmd.exe /c "<đường dẫn>\tools\check_done_task.cmd"`, hoặc chạy tay `python -X utf8 tools\check_done.py` |
| 12 | Nhiều khóa bù media **cùng lúc**, C: tụt nhanh | `ai_watchdog` gọi `fill_media --jobs 4` song song và không thấy lock của supervisor (`fill_lite.lock`, `fill_remaining.lock`) | Đã sửa 21/11: `fill_media` bỏ khóa đã upload; watchdog coi 3 lock là "busy" và chạy `--jobs 1 --workers 1` |
| 13 | Lock trong `data/logs` biến mất, `--status` báo daemon không chạy dù process còn sống | cùng hiện tượng xoá file ngoài ý muốn như `*_done.json` | Đã chuyển lock sang `D:\VocabularyAppData\state\locks`; daemon tự tạo lại lock mỗi vòng; `--status` đọc thêm PID trong `pipeline_status.json` |

---

## 9. Lỗi mình đã từng làm (bài học, đừng lặp lại)

1. **Chạy finalize khi chưa rõ state** → `shrink_audio` quét lại 56k file, mất ~13 phút vô ích.
   → Luôn kiểm tra state + bitrate trước; dùng `SKIP_SHRINK=1` khi đã nén riêng.
2. **Xoá worktree khi watcher đang chạy nền** → watcher/state biến mất, phải khởi động lại.
   → Dừng process trước, xoá worktree sau; state nay đã có 2 bản.
3. **Khôi phục state bằng tay 2 lần** trước khi làm `statefile.py`.
   → Giờ chỉ cần `statefile.load/save`, không sửa JSON trực tiếp.
4. **Tưởng media ở GitHub Releases** → kiểm tra 404, mất thời gian.
   → Media ở raw repo `VocabularyData`; release API 404 là bình thường.
5. **Log cleanup ghi "0,0 MB"** vì đo dung lượng **sau** khi xoá.
   → Đã sửa: đo trước, log sau.
6. **Upload bản thiếu** sẽ phải pack/upload lại toàn bộ khi đủ 2.520.
   → Quy tắc: chỉ finalize khi `days_done == 2520`.
7. **Chạy 2 supervisor song song** → hai tiến trình tranh lock/ghi log.
   → Luôn `Get-CimInstance ... | Stop-Process` trước khi start lại.
8. **Dùng `Select-String` đọc log UTF-8** → mojibake, dễ kết luận sai.
   → Dùng `python -X utf8` để đọc/parse log.
9. **Quên rằng `data/` bị `.gitignore`** → state không nằm trong git, không khôi phục bằng checkout được.
   → Đó là lý do phải có state 2 bản ngoài repo.
10. **Để watchdog chạy song song với supervisor** (21/11): `ai_watchdog` gọi
    `fill_media --jobs 4` cho cả 8 khóa, không thấy lock của `fill_lite`/supervisor
    ⇒ 4 khóa bù cùng lúc, tiếng Anh bị bù lại 99 ngày, C: tụt còn 3,9 GB.
    → Đã sửa: `fill_media` bỏ khóa đã upload; watchdog đọc cả 3 lock, chạy 1 job.

---

## 10. Quy tắc bất biến (invariants)

- **Không upload/finalize khi khóa chưa đủ 2.520 ngày.**
- **Không di chuyển/đổi junction** `data/media`, `data/audio`, `data/ai_courses` khi pipeline đang chạy.
- **Không commit** `MyTiktokDownload`, `Game`, `gemini_keys.json` hay thay đổi không liên quan.
- Git identity: **Thai Bao / thaibao1991dn@gmail.com**; push bằng `push_master.py`.
- Chỉ xoá media local khi: `finalize_done[slug] == done` **và** `web/data/<slug>/index.json` đủ 2.520 ngày.
- Mọi ghi JSON: atomic (tmp + `os.replace`); state qua `statefile.save`.
- Không báo "xong" nếu chưa chạy test thật và chưa cập nhật `projectLog.md`.
- Không tạo worktree trong `C:`; nếu cần thì đặt ở `D:/opencode-worktrees`.

---

## 11. Việc còn lại (theo thứ tự)

1. **Đức** (1.023/2.520) → tự finalize/upload/deploy → cleanup.
2. **Pháp** → **Nga** (cùng quy trình).
3. Sau mỗi khóa: `verify_online.py` (9/9) + ghi `projectLog.md`.
4. Khi media xong toàn bộ: làm P0 UI theo `docs/UPGRADE_PLAN.md`
   (Settings, Progress dashboard, chọn ngày nâng cao, lịch sử quiz).
5. Việc treo: rotate 197 key lộ trong `GravityCode/Download/AskCpl/settings.json`.

---

## 11.1. Tạm dừng / chạy lại toàn bộ

Dừng (không xoá dữ liệu, không mất tiến độ):

```powershell
python -X utf8 tools\pipeline_daemon.py --stop
python -X utf8 tools\pipeline_daemon.py --uninstall-startup   # bỏ tự chạy khi đăng nhập
python -X utf8 tools\pipeline_daemon.py --status               # phải ghi "KHÔNG chạy"
```

Chạy lại: xem `docs/PAUSE_STATE.md` (mốc tiến độ + lệnh + ngày thiếu đầu tiên).
Tóm tắt: `--install-startup` rồi `python -X utf8 tools\pipeline_daemon.py`.

---

## 12. Checklist trước khi báo "xong"

- [ ] `python -m py_compile` các file vừa sửa.
- [ ] Chạy thật luồng liên quan (không chỉ đọc code).
- [ ] `verify_online.py` 9/9 (nếu có đụng web/media).
- [ ] `audit_all.py` 0 FAIL (nếu đụng nội dung/media).
- [ ] `git status` chỉ có file thuộc phạm vi.
- [ ] `projectLog.md` có mục mới (ngày giờ, việc làm, số liệu thật).
- [ ] Commit + `push_master.py` nếu được yêu cầu.
