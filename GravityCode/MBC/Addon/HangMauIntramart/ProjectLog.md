# NHẬT KÝ DỰ ÁN & HƯỚNG DẪN KIẾN TRÚC (Project Log & Architecture Guide)
**Tên dự án:** HangMauIntramart (Auto Tool Intramart Edge Extension)
*Quy tắc bắt buộc: Bất kỳ AI hay Developer nào khi tiếp nhận dự án này đều phải đọc toàn bộ nội dung file này trước khi tiến hành sửa đổi mã nguồn.*

---

## 1. MỤC TIÊU DỰ ÁN
Tự động hóa toàn bộ quá trình Duyệt nhanh trên hệ thống nội bộ Intramart thông qua một Extension cài trên trình duyệt Edge.
Tool phải có khả năng tự nhận diện danh sách bảng, tự click nút chọn tất cả, tự bấm "Process continuously" và liên tục lặp lại quá trình click nút "Duyệt nhanh" trên màn hình popup/frame mới tải lại cho đến khi hết dữ liệu.

---

## 2. KIẾN TRÚC ADDON HIỆN TẠI (Cách hệ thống hoạt động)
Hệ thống Intramart là một hệ thống doanh nghiệp (Enterprise) cực kỳ phức tạp với tường lửa CSP (Content Security Policy) khắt khe và hệ thống Frame lồng nhau chồng chéo. Kiến trúc Extension được thiết kế đặc biệt để xuyên thủng các rào cản này:

- **`popup.html` & `popup.js`**: Giao diện người dùng. Có nút Start/Stop, có một cửa sổ console nền đen chữ xanh để in log theo thời gian thực (Step-by-step), và bộ đếm số lần xử lý. 
  - Giao tiếp: Gửi lệnh Start qua `chrome.tabs.sendMessage` và nhận log qua `chrome.runtime.onMessage`.
  
- **`content.js`**: "Sứ giả" được tiêm vào cửa sổ gốc (Top Window). 
  - **Lưu ý quan trọng**: Tuyệt đối không dùng `all_frames: true` để chạy code tự động trong `content.js`, vì khi frame `IM_MAIN` chuyển trang, script sẽ bị "khai tử" (Killed) làm đứt chuỗi logic.
  - Nhiệm vụ: Lắng nghe lệnh Start từ Popup, sau đó ra lệnh cho `background.js` thực thi mã vào MAIN world. Đồng thời, nó lắng nghe `window.postMessage` (các log gửi từ mã MAIN world) để đẩy ngược về Popup.

- **`background.js` (Trái tim của Addon)**: Chứa toàn bộ đoạn mã logic Tự động hóa (`autoIntramart`).
  - **Tư duy lách CSP (Quan trọng):** Intramart chặn mọi thẻ `<script>` nội tuyến (inline script). Do đó, `background.js` phải dùng API `chrome.scripting.executeScript` với thuộc tính **`world: 'MAIN'`** và **`frameIds: [0]`** để bơm trực tiếp logic vào không gian nhớ của Top Window. Bằng cách này, mã hoạt động y hệt như khi dán vào F12 Console, không bị chặn bởi tường lửa và không bị chết khi frame con tải lại.

---

## 3. TƯ DUY XỬ LÝ & BƯỚC THỰC HIỆN DÀNH CHO BẢO TRÌ TƯƠNG LAI
Nếu trong tương lai hệ thống Intramart thay đổi giao diện hoặc có lỗi, hãy tuân theo luồng suy nghĩ sau:

1. **Test trước trên F12:** 
   - Hãy trích xuất nội dung của hàm `getInjectedAutomationCode()` trong `background.js` (bỏ đi phần bọc async) và chạy thử trực tiếp trên Tab Console (F12) của Top Window. Nếu code chạy tốt ở F12 thì chắc chắn sẽ chạy tốt trên Addon.
2. **Luôn bắt DOM từ Top Window vào:** 
   - Không được dùng `document.getElementById` trực tiếp vì mã đang chạy ở cửa sổ gốc, không phải trong frame. Luôn phải thông qua hàm `getMainFrame()` để thọc tay vào lấy `frame.document`.
3. **Cơ chế chờ tải (Wait & Check):** 
   - Không bao giờ dùng `setTimeout` mù quáng. Intramart xử lý khá chậm. Sau mỗi click, hãy tạo một vòng lặp `for` và delay ngắn (500ms) để liên tục kiểm tra `readyState === 'complete'` của frame, giúp tool chạy ở tốc độ tối ưu nhất (không quá nhanh để bị văng, không quá chậm để lãng phí thời gian).
4. **Quản lý biến bộ nhớ (Tránh kẹt trạng thái):**
   - Đảm bảo biến `window.__intramart_running` được gán = `true` khi bắt đầu và phải được reset về `false` khi kết thúc hoặc có yêu cầu Stop. Tuyệt đối không tạo lệnh chặn `return` nếu biến này `true` ở bước khởi động của `background.js` (vì nếu phiên trước đó bị lỗi đứng máy, cờ này sẽ vĩnh viễn là `true` khiến lần Start sau bị liệt cứng).

---

## 4. LỊCH SỬ CÁC LỖI ĐÃ GIẢI QUYẾT (Tránh đi vào vết xe đổ)
1. **Lỗi Frame Reload bị đứt chuỗi:** 
   - *Biểu hiện:* Bấm nút xong sang màn hình duyệt thì tool tự dừng không chạy tiếp.
   - *Nguyên nhân:* Code cũ chạy trong Isolated Frame. Khi Frame đổi URL, trình duyệt tự hủy mã.
   - *Giải pháp:* Chuyển vùng hoạt động lên Top Window, lấy móc câu (DOM pointer) chọc xuống Frame.
2. **Lỗi CSP (Content Security Policy) `inline script violates...`:**
   - *Biểu hiện:* Code văng lỗi đỏ lòm ở dòng tạo `document.createElement('script')`.
   - *Giải pháp:* Không nhúng thẻ `<script>`, gọi `chrome.scripting.executeScript({world: 'MAIN'})`.
3. **Lỗi liệt nút Start / Đứng hình sau khi báo "Khởi động thành công":**
   - *Nguyên nhân 1:* Cờ `window.__intramart_running` bị kẹt `true` từ một lần lỗi trước. (Giải pháp: Luôn ép chạy mới khi ấn Start).
   - *Nguyên nhân 2:* Khai báo biến trỏ vào một phần tử (button) không có thật trên `popup.html`, khiến JS văng TypeError ngầm và làm hỏng toàn bộ luồng sự kiện. (Giải pháp: Kiểm tra kỹ ID DOM trước khi `addEventListener`).
4. **Lỗi `Attempting to use a disconnected port object`:**
   - *Biểu hiện:* Để Addon một lúc, quay lại ấn thì văng lỗi trên, popup không chạy.
   - *Nguyên nhân:* Service Worker của Chrome Manifest V3 tự động "ngủ đông" (Sleep) sau 30 giây không hoạt động, khiến các luồng `port.postMessage` bị đứt rỗng.
   - *Giải pháp:* Đổi từ kết nối dài hạn sang kết nối một chiều `chrome.runtime.sendMessage()`. Cơ chế này tự động "đánh thức" Service Worker nếu nó đang ngủ.

---

## 5. CÁC TÍNH NĂNG ĐỀ XUẤT NÂNG CẤP THÊM (TODO)
- Thêm cơ chế Auto-Recovery: Tự động tải lại trang gốc (F5) nếu tool phát hiện frame bị kẹt loading quá 30 giây.
- Bổ sung tùy chọn chọn khoảng thời gian trễ (Delay time) cho từng loại mạng ngay trên giao diện Popup.
- Lưu lại lịch sử toàn bộ Log ra file dạng `.txt` để gửi cho dev kiểm tra khi có báo cáo lỗi.

5. **L?i Edge bop b?ng thong (Throttling) khi tab b? che khu?t ho?c thu nh?:**
   *Bi?u hi?n:* B?t Tool r?i chuy?n sang dung Word/Excel, Tool t? ??ng ch?y r?t ch?m ho?c b? ?ong b?ng (Pause) do c? ch? Sleeping Tabs c?a Edge.
   *Gi?i phap:* Dung m?o **Silent Audio Hack**. Kh?i t?o m?t Web Audio API phat ra am thanh cam (Volume = 0) lien t?c. Trinh duy?t s? l?m t??ng Tab ?ang phat nh?c/phim nen s? cho phep no ch?y v?i 100% t?c ?? trong background (y h?t nh? Spotify Web).

---
## 6. CAC TINH N?NG M?I B? SUNG G?N NH?T
1. **Tuy ch?nh th?i gian Tr? (Delay):** Them o nh?p s? giay tren Popup. Gia tr? nay ???c truy?n xuyen t? \popup.js\ -> \content.js\ -> \ackground.js\ va ??a vao lam tham s? \delaySeconds\ cho ham n?i suy. Giup ng??i dung linh ho?t t?ng gi?m t?c ?? tuy theo ?? gi?t lag c?a server.
2. **Nut L?u Log (Export Log):** B? sung nut \?? L?u Log\ tren Popup. Khi ?n, tool t? ??ng thu th?p toan b? cac th? div log, nen thanh file \intramart_log_YYYYMMDD_HHMM.txt\ va t?i xu?ng may, r?t h?u ich ?? g?i cho dev ki?m tra.
3. **C?nh bao ch?ng k?t (Auto-Recovery Warning):** Vong l?p ch? t?i frame ?a ???c nang gi?i h?n ki?m tra len 30 giay (60 vong l?p 500ms). N?u qua 30 giay ma frame v?n ch?t, tool s? thoat vong l?p va bao l?i ?? yeu c?u ng??i dung F5, tranh vi?c Tool b? treo ?o mai mai.
