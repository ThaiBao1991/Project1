# google-ultra

Google One có offer dùng thử miễn phí 12 tháng cho AI Ultra, không trang nào hiển thị cả, chỉ có trong giá trị trả về của thư viện thanh toán Play (BillingClient). Script này nối «tra offer → mở trang thanh toán Play → xác nhận 0 đồng → mở gói» thành một lệnh duy nhất.

Nguyên lý là mượn chính tiến trình của Google One để gọi BillingClient, không cần Xposed, không cần sửa APK.

## Nhận được gì

Nhận được là **Ultra 5x, 20TB, 12 tháng $0**, hủy trước khi hết hạn thì không mất tiền. Sau khi mở, trang đăng ký Play sẽ ghi «Sắp bị trừ 2027-11-17 US$99.99/tháng», đó là giá sau khi hết dùng thử, không phải trừ ngay bây giờ.

Gói 30TB (20x) cũng tra được offer, nhưng khi thanh toán Play sẽ kiểm tra lại lần nữa, đa số tài khoản sẽ hiện «Bạn không đủ điều kiện dùng thử miễn phí». Script này sẽ không bấm vào gói đó.

## Cần gì

Một điện thoại Android đã root, cắm USB vào máy tính. Magisk, KernelSU, APatch đều được, giả lập cũng được.

Máy tính cần Python 3.9 trở lên, cộng thêm hai gói:

```bash
pip3 install frida
```

adb thì lấy trong platform-tools của Android SDK. Cài xong, chạy `adb devices` thấy điện thoại là được. Chưa cài bao giờ thì trên Mac chạy `brew install android-platform-tools`, trên Windows tải gói platform-tools về, giải nén rồi thêm thư mục đó vào PATH.

Trên điện thoại bật «Tùy chọn nhà phát triển → Gỡ lỗi USB», cắm vào rồi bấm cho phép trong hộp thoại hiện lên.

## Cách dùng

Tự kiểm tra môi trường trước một lượt, nó sẽ kiểm tra thiết bị, root, frida-server, đẩy module thanh toán, tiện tay tắt luôn proxy và Clash nào đang chặn mạng của Play:

```bash
python3 ultra0.py --check
```

Toàn xanh là chạy tài khoản được rồi.

Tài khoản viết vào một file văn bản, mỗi dòng một tài khoản, các trường cách nhau bằng bốn dấu gạch ngang:

```
email----mật khẩu----email khôi phục----khóa 2FA----số thẻ----ngày hết hạn----CVC----chủ thẻ----mã bưu chính
```

Mấy mục sau để trống cũng được. Tài khoản mới mua thường không có 2FA thì để trống:

```
abc123@gmail.com----mypassword----
```

Có thẻ thì:

```
abc123@gmail.com----mypassword--------4242424242424242----10/29----326----ZHANG SAN----97201
```

Địa chỉ không điền sẽ mặc định dùng `123 Main St, Portland, OR 97201`, Oregon được miễn thuế tiêu thụ.

Chạy:

```bash
python3 ultra0.py accounts.txt
```

Chạy một tài khoản cũng được:

```bash
python3 ultra0.py --account "abc@gmail.com:mật khẩu:khóa 2FA"
```

Muốn xem kết quả thì mở trang đăng ký để đối chiếu:

```
Cửa hàng Play → ảnh đại diện → Thanh toán và gói đăng ký → Gói đăng ký
```

## Bên trong nó làm gì

1. Thêm tài khoản vào điện thoại (chưa có thì thêm, có rồi thì bỏ qua)
2. Chuyển tài khoản Play. Chuyển xong nhất định phải đọc lại từ bảng ảnh đại diện để đối chiếu, không khớp thì thoát ngay, không chạy sang tài khoản khác
3. Khởi động Google One, dùng Frida gắn vào, dùng `DexClassLoader` để tải module thanh toán
4. `queryProductDetailsAsync` tra `g1.play.20tb`, lấy về 5 offer
5. Chọn offer có thời gian miễn phí dài nhất (`eft-12month`, P1Y), gọi `launchBillingFlow` ở luồng chính
6. Canh trang thanh toán. Thấy giá là 0 hoặc «Dùng thử miễn phí 12 tháng» mới bấm đăng ký; thấy «không đủ điều kiện dùng thử miễn phí» thì đóng lại, tuyệt đối không bấm
7. Play đôi khi yêu cầu nhập lại mật khẩu, script tự điền
8. Mở trang đăng ký để đối chiếu, kết quả ghi vào `ultra0-report/`

## Khi thất bại thì ra sao

**Tài khoản không đủ điều kiện.** Play sẽ báo «Bạn không đủ điều kiện dùng thử miễn phí, tuy vậy bạn vẫn có thể đăng ký». Một tài khoản cơ bản chỉ có một cơ hội: dùng thử một khi đã bắt đầu, dù chưa xác nhận, offer cũng sẽ biến mất. Vì vậy đừng lấy tài khoản chính ra thử.

**Không có phương thức thanh toán.** Đăng ký bắt buộc phải có thẻ. Trang thêm thẻ của Play là WebView, adb không điền vào được, script sẽ dừng lại và nhắc bạn điền xong trên điện thoại rồi bấm Enter. Mỗi thiết bị chỉ cần gắn tay một lần, sau đó mọi tài khoản dùng chung thẻ đó.

**Tài khoản Play chưa chuyển qua.** Script sẽ in ra tài khoản đang thực sự đăng nhập rồi thoát. Lúc này chuyển tay trong Play rồi chạy lại kèm `--no-switch`, để nó chỉ kiểm tra mà không thử chuyển nữa:

```bash
python3 ultra0.py accounts.txt --no-switch
```

**Trang thanh toán không hiện lên.** Chạy lại một lần. Hai lần liên tiếp đều không hiện thì kiểm tra mạng của thiết bị: `settings get global http_proxy`, không phải `null` thì xóa đi; VPN kiểu Clash sẽ chiếm DNS, cũng làm Play không kết nối được.

## Một số tham số

```bash
--plan 5x      # chỉ mở 20TB
--plan 20x     # chỉ tra 30TB (đa số tài khoản không lấy được dùng thử)
--plan auto    # mặc định, tra cả hai gói, chọn gói miễn phí dài nhất
--no-add       # tài khoản đã có trên điện thoại, bỏ qua bước thêm tài khoản
--no-switch    # không tự chuyển tài khoản, chỉ kiểm tra tài khoản hiện tại
```

## Vài lưu ý

Thử xong nhớ vào Play hủy gói đăng ký, nếu không đến hạn sẽ bị trừ $99.99.

Script chỉ chạy trên máy của bạn, tài khoản, mật khẩu và số thẻ không ra mạng, cũng không tải lên đâu cả. File báo cáo nằm trong `ultra0-report/`, trong đó có chi tiết offer và kết quả từng bước.

Đoạn code này chỉ tận dụng việc «phía client lấy được offer dùng thử» trong quy trình thanh toán của Play, không sửa bất kỳ dữ liệu nào phía máy chủ.

## Trao đổi

Có vấn đề thì vào nhóm Telegram hỏi: https://t.me/VQD_SHARE (@VQD_SHARE).

<img src="assets/telegram-group.png" width="320" alt="Mã QR nhóm Telegram @VQD_SHARE">
