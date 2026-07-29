# ProjectLog: MBC_IntramartSignal

## Mô tả
Addon giúp người dùng xác định chính xác con dấu đang lệch bao nhiêu (tính bằng PDF Points theo trục X và Y) khi xem trước văn bản trình ký trên hệ thống Intramart. Từ đó hướng dẫn người dùng điều chỉnh Row Height trong Excel để file PDF xuất ra khớp chính xác tọa độ con dấu trên Server — không phụ thuộc kích thước màn hình.

## Quá trình phát triển

### Tiếp cận 1 – CSS Override (THẤT BẠI)
Dùng `position: absolute/fixed` cố định phần tử DOM của con dấu. Thất bại vì con dấu được render bên trong thẻ `<embed type="application/pdf">`, không thể can thiệp DOM.

### Tiếp cận 2 – Dịch chuyển PDF (BỎ)
Dùng `pdf-lib` dịch chuyển toàn bộ nội dung trang PDF theo `(deltaX, deltaY)`. Bị loại vì làm hỏng bố cục PDF (lề bị cắt, bảng biểu sai lệch) và các con dấu ký tiếp theo bị trượt lũy tiến.

### Tiếp cận 3 – Thước Đo Ma Thuật ✅ (Đang áp dụng)
**Nguyên lý:** Không sửa PDF, chỉ đo và báo cáo cho người dùng. Dùng `pdf.js` render bản Xem trước lên Canvas trong Modal. Người dùng click 2 điểm (con dấu đang đóng sai → vòng ESIGN HERE đích đến). Addon tính `deltaX` và `deltaY` theo PDF Points rồi thông báo:
- Chiều dọc (Y): Cần cộng/trừ bao nhiêu points vào Row Height của dòng trong Excel.
- Chiều ngang (X): Cần tăng/giảm độ rộng cột trong Excel.

**Điểm mạnh:** Không hỏng PDF, mọi người ký đều hưởng lợi, fix đúng gốc rễ vấn đề.

## Khó khăn / Điểm cần lưu ý
- Tọa độ Y của Canvas (hướng xuống) và PDF (hướng lên) ngược nhau → phải đảo dấu `deltaY`.
- Canvas có thể bị CSS scale (do `max-width: 100%`) → phải nhân với `cssScaleX/cssScaleY` khi lấy tọa độ click.
- Thư viện `pdf.js` cần khai báo Worker path qua `chrome.runtime.getURL('libs/pdf.worker.min.js')`.
- 1 PDF Point ≈ 1 đơn vị Row Height trong Excel (hệ đo dùng Points).

## Trạng thái hiện tại
- ✅ Giao diện Modal 2 bước: chọn file mẫu → Scale và Upload
- ✅ Đọc kích thước PDF (MediaBox) của cả 2 file, hiển thị chênh lệch ΔX, ΔY
- ✅ Scale toàn bộ file user về đúng kích thước file mẫu (không hỏng bố cục)
- ✅ Phân tích Content Margins bằng Pixel Scan (100% chính xác, không biến dạng file gốc)
- ✅ **Mới:** Tự động quy đổi sai lệch ra `cm` và `inch` để hướng dẫn người dùng sửa cấu hình Margin/Scaling trực tiếp trong Excel.
- ✅ Checkbox tùy chọn: tự động che dòng đường dẫn file Excel (header/footer) bằng hình chữ nhật trắng 22pts
