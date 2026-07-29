# General Rules

- **KI First**: Always review all Knowledge Items (KI) before starting any new conversation or task. If no KI exists yet, say so explicitly instead of skipping this step silently.
- **ProjectLog.md**: Always read `ProjectLog.md` before starting, to understand current context (what was done, what's in progress, known issues). ALWAYS update `ProjectLog.md` immediately after any significant change — do not batch updates for later.
- **Strict Plan Before Code**: Always propose an implementation plan (files to touch, approach, risks) before writing or modifying any code. You MUST wait for explicit user approval (e.g. "ok", "go", "approved") before proceeding. Do NOT interpret silence, a related question, or a vague reply as approval.
- **No Silent Scope Creep**: If while working you discover the task needs to touch files/areas not in the approved plan, STOP and ask before proceeding, unless it's a trivial one-line fix directly required to make the approved change work.
- **Cleanup Temporary Files**: Always proactively delete temporary files, scratch scripts, or test data files immediately after they are no longer needed to keep the workspace clean.

---

## ⚠️ Checklist Bắt Buộc TRƯỚC Khi Code (Gate 1 — Pre-Code)

Trước khi viết/sửa **bất kỳ** dòng code nào, tôi phải trả lời rõ ràng (không được bỏ qua bước nào):

1. [ ] Tôi đã đọc `ProjectLog.md` và các KI liên quan chưa?
2. [ ] Tôi đã liệt kê chính xác danh sách file sẽ bị tạo/sửa/xoá chưa?
3. [ ] Tôi đã trình bày plan (mô tả ngắn gọn cách làm + rủi ro nếu có) và nhận được "ok" rõ ràng từ user chưa?
4. [ ] Tôi đã xác định cách sẽ tự verify kết quả sau khi code xong (chạy gì, kiểm tra gì) chưa?

⛔ Nếu bất kỳ mục nào ở trên là "chưa", KHÔNG được code, sửa file, hay chạy lệnh sửa đổi.

---

## ⚠️ Checklist Bắt Buộc SAU Khi Code (Gate 2 — Post-Code / Definition of Done)

Sau khi viết code xong, task KHÔNG được coi là hoàn thành cho đến khi tất cả các mục sau đều ✅:

1. [ ] **Build/Run check**: Đã chạy build hoặc chạy thử ứng dụng, không có lỗi compile/runtime.
2. [ ] **Test lại chức năng vừa sửa**: Đã tự thực hiện (hoặc mô phỏng) đúng luồng người dùng sẽ dùng, xác nhận kết quả đúng như mong đợi.
3. [ ] **Rà soát lỗi liên quan (regression check)**: Đã kiểm tra các phần code khác có gọi/phụ thuộc vào phần vừa sửa — đảm bảo không phá vỡ chức năng cũ.
4. [ ] **Rà soát edge case**: Đã tự đặt câu hỏi "trường hợp nào có thể làm hỏng đoạn code này?" (input rỗng, null, unicode, số âm, timeout, race condition, v.v.) và xử lý hoặc ít nhất ghi chú rõ nếu chưa xử lý.
5. [ ] **Không còn console.log/debug code thừa**, không còn TODO không rõ nghĩa.
6. [ ] **Báo cáo kết quả test cho user**: Trước khi nói "xong", tôi PHẢI trình bày rõ:
   - Đã test cái gì, bằng cách nào (lệnh chạy, thao tác thực hiện).
   - Kết quả thực tế thu được (không phải suy đoán).
   - Có vấn đề/giới hạn nào còn tồn đọng không.
7. [ ] **Cập nhật `ProjectLog.md`** phản ánh đúng trạng thái mới.

⛔ KHÔNG được tuyên bố "hoàn thành"/"done"/"xong" nếu chưa đi qua đủ 7 mục trên. Nếu có bước nào không thể tự verify được (ví dụ cần UI thật để xem), phải nói rõ "chưa verify được X, cần user tự kiểm tra".

---

## Nguyên tắc "Không đoán, chỉ báo cáo sự thật"

- Không được nói "chắc là đã sửa xong" hoặc "có lẽ hoạt động đúng" — chỉ báo cáo dựa trên kết quả đã thực sự chạy/kiểm tra.
- Nếu không chắc chắn, phải nói rõ mình không chắc và đề xuất cách kiểm chứng.

---

## ⚠️ Quy tắc VÀNG về Mã Hóa (Encoding) Base64

Tuyệt đối lưu ý khi lưu trữ và truyền tải dữ liệu JSON (đặc biệt là dữ liệu có chứa ký hiệu Unicode, tiếng Việt, file markdown):

1. **LUÔN LUÔN DÙNG MÃ HÓA 2 CHIỀU ĐỒNG BỘ:**
   - Khi mã hóa lưu trữ (Save): `btoa(unescape(encodeURIComponent(JSON.stringify(obj))))`
   - Khi giải mã đọc ra (Load): `JSON.parse(decodeURIComponent(escape(atob(str))))`
2. **Hậu quả nếu bỏ quên `decodeURIComponent`:** Nếu chỉ dùng `atob(...)` để giải nén nhưng thiếu `decodeURIComponent`, chuỗi byte UTF-8 sẽ bị hiểu nhầm thành ký tự Latin-1. Nếu lặp lại việc lưu/đọc trong vòng lặp (ví dụ Auto-Resume reload trang), dung lượng ký tự sẽ **nhân đôi liên tục theo cấp số nhân**, khiến file JSON phình to từ vài MB lên hàng chục MB, gây nghẽn RAM, treo máy, và sập luồng gửi tin nhắn IPC của Chrome.
3. **Bắt buộc**: bất kỳ đoạn code nào dùng `btoa`/`atob` phải được kiểm tra chéo với quy tắc này trong Gate 2 (mục edge case) trước khi báo hoàn thành.
