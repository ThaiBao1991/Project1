# Antigravity Global AI Working Rules & Guidelines

Áp dụng toàn cục cho tất cả các dự án và môi trường làm việc của Antigravity trên máy tính này.

---

## 1. Nguyên Tắc Cốt Lõi (Core Principles)

- **KI First**: Luôn rà soát Knowledge Items (KI) trước khi bắt đầu nhiệm vụ hoặc giải quyết vấn đề mới. Nếu chưa có KI, phải nêu rõ ràng thay vì im lặng bỏ qua.
- **ProjectLog.md**: Luôn đọc `ProjectLog.md` của dự án (nếu có) trước khi bắt đầu để nắm vững ngữ cảnh (những gì đã làm, đang làm dở, các lỗi đã biết). BẮT BUỘC cập nhật `ProjectLog.md` ngay sau mỗi thay đổi quan trọng — không dồn cập nhật để sau.
- **Kế Hoạch Trước Khi Code (Strict Plan Before Code)**: Luôn đề xuất kế hoạch thực hiện rõ ràng (danh sách file sẽ tạo/sửa/xóa, phương pháp tiếp cận, rủi ro) TRƯỚC KHI viết hoặc sửa bất kỳ dòng code nào. BẮT BUỘC chờ người dùng phản hồi xác nhận rõ ràng (ví dụ: "ok", "go", "approved") mới được thực thi. TUYỆT ĐỐI không coi sự im lặng hay câu hỏi làm sự phê duyệt.
- **Không Tự Ý Mở Rộng Phạm Vi (No Silent Scope Creep)**: Nếu trong quá trình làm việc phát hiện task cần đụng tới các file/khu vực ngoài kế hoạch đã duyệt, PHẢI DỪNG LẠI và hỏi ý kiến người dùng trước, trừ khi đó là sửa đổi 1 dòng bắt buộc trực tiếp để hoàn tất task.
- **Dọn Dẹp File Tạm (Cleanup Temporary Files)**: Proactively xóa ngay các file tạm thời, file nháp kiểm thử, dữ liệu test sau khi hoàn tất kiểm tra để giữ workspace luôn sạch sẽ.
- **Nguyên Tắc "Không Đoán, Chỉ Báo Cáo Sự Thật"**:
  - Tuyệt đối không nói "chắc là đã sửa xong" hay "có lẽ hoạt động đúng" — chỉ báo cáo dựa trên kết quả thực tế đã chạy/kiểm tra.
  - Nếu có phần chưa thể tự verify được (ví dụ cần người dùng xem giao diện hoặc xác thực tài khoản thực), phải nói rõ "Chưa verify được X, cần user kiểm tra".

---

## 2. ⚠️ Checklist Bắt Buộc TRƯỚC Khi Code (Gate 1 — Pre-Code)

Trước khi viết/sửa **bất kỳ** dòng code nào, Agent phải kiểm tra và xác nhận rõ ràng:

1. [ ] Tôi đã đọc `ProjectLog.md` và các KI liên quan chưa?
2. [ ] Tôi đã liệt kê chính xác danh sách file sẽ bị tạo/sửa/xoá chưa?
3. [ ] Tôi đã trình bày plan (mô tả ngắn gọn cách làm + rủi ro nếu có) và nhận được "ok" rõ ràng từ user chưa?
4. [ ] Tôi đã xác định cách sẽ tự verify kết quả sau khi code xong (chạy gì, kiểm tra gì) chưa?

⛔ **Nếu bất kỳ mục nào ở trên là "chưa", KHÔNG được code, sửa file, hay chạy lệnh sửa đổi.**

---

## 3. ⚠️ Checklist Bắt Buộc SAU Khi Code (Gate 2 — Post-Code / Definition of Done)

Sau khi viết code xong, task KHÔNG được coi là hoàn thành cho đến khi tất cả các mục sau đều đạt chuẩn:

1. [ ] **Build/Run check**: Đã chạy build hoặc syntax check (`python -m py_compile`, lint, type check), không có lỗi compile/runtime.
2. [ ] **Test lại chức năng vừa sửa**: Tự thực hiện (hoặc viết script mô phỏng) đúng luồng người dùng sẽ dùng, xác nhận kết quả đúng như mong đợi.
3. [ ] **Rà soát lỗi liên quan (Regression check)**: Kiểm tra các phần code khác có gọi/phụ thuộc vào phần vừa sửa — đảm bảo không phá vỡ chức năng cũ.
4. [ ] **Rà soát edge case**: Tự đặt câu hỏi "trường hợp nào có thể làm hỏng đoạn code này?" (input rỗng, null, unicode tiếng Việt, số âm, timeout, network error, race condition...) và xử lý chu đáo.
5. [ ] **Dọn sạch debug**: Không còn `console.log`, `print` rác thừa, không còn comment TODO vô nghĩa.
6. [ ] **Báo cáo kết quả kiểm tra trung thực**: Trình bày rõ đã test cái gì, bằng cách nào, kết quả thực tế ra sao và có giới hạn nào chưa test được.
7. [ ] **Cập nhật `ProjectLog.md`** phản ánh đúng trạng thái mới của dự án.

⛔ **KHÔNG được tuyên bố "xong / done" nếu chưa đi qua đủ 7 mục trên.**

---

## 4. ⚠️ Quy Tắc VÀNG về Mã Hóa (Encoding) Base64 & Unicode

Tuyệt đối lưu ý khi lưu trữ và truyền tải dữ liệu JSON (đặc biệt dữ liệu có chứa tiếng Việt, CJK, ký tự đặc biệt, markdown):

1. **LUÔN DÙNG MÃ HÓA 2 CHIỀU ĐỒNG BỘ:**
   - **Khi mã hóa lưu trữ (Save)**:
     `btoa(unescape(encodeURIComponent(JSON.stringify(obj))))`
   - **Khi giải mã đọc ra (Load)**:
     `JSON.parse(decodeURIComponent(escape(atob(str))))`
   - Hoặc sử dụng chuẩn hiện đại với `TextEncoder` & `TextDecoder` (Uint8Array) trong JavaScript:
     ```javascript
     const encodeBase64Utf8 = (str) => {
       const bytes = new TextEncoder().encode(str);
       let binary = "";
       for (let i = 0; i < bytes.length; i += 0x8000) {
         binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
       }
       return btoa(binary);
     };

     const decodeBase64Utf8 = (b64) => {
       const binary = atob(b64);
       const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
       return new TextDecoder().decode(bytes);
     };
     ```
2. **Cảnh báo thảm họa nếu thiếu `decodeURIComponent`:** Nếu chỉ dùng `atob(...)` thuần túy mà thiếu `decodeURIComponent`, chuỗi byte UTF-8 sẽ bị hiểu nhầm thành Latin-1. Trong vòng lặp lưu/đọc (như auto-save, reload trang), dung lượng dữ liệu sẽ **nhân đôi liên tục theo cấp số nhân**, làm phình to file từ vài KB lên hàng chục MB, gây cạn kiệt RAM, treo máy và sập luồng IPC.
3. **Python encoding**: Luôn dùng `encoding="utf-8"` khi mở file đọc/ghi và thiết lập `sys.stdout.reconfigure(encoding="utf-8")` trên môi trường Windows console.

---

## 5. Quy Tắc Gọi API Gemini An Toàn (Gemini Safe & Key Rotation)

- **Đa tài khoản & Xoay Key (Key Rotation)**: Luôn gom nhóm key theo account và xoay vòng key tự động khi gọi API.
- **Xử lý lỗi Quota 429 & 503**: Khi một key bị dính 429 (Resource Exhausted), đánh dấu tạm nghỉ (cooldown) cho account đó và lập tức chuyển sang account khác. Tuyệt đối không retry dồn dập vào cùng 1 key bị khóa.
- **Kỹ thuật Blind Fire**: Khi gặp lỗi auth hoặc rate limit, chuyển key dự phòng ngay tức khắc trong luồng nền mà không làm gián đoạn trải nghiệm người dùng.