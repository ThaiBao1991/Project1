# ProjectLog — CreateImg: Tiệc Nhậu Vui Nhộn MBC

Dự án tạo bộ ảnh slide hài hước và kịch bản trình chiếu cho buổi tiệc nhậu công ty từ file Excel `DanhSachAnhBHCL.xlsm`.

---

## 📁 Cấu Trúc Thư Mục Dự Án

```
CreateImg/
├── DanhSachAnhBHCL.xlsm               # File Excel gốc (đã cập nhật 33 hành động & suy nghĩ hóm hỉnh)
├── DanhSachAnhBHCL_backup.xlsm        # File backup an toàn trước khi chỉnh sửa
├── extracted_faces/                    # 33 ảnh chân dung đã trích xuất chuẩn (MNV_HoTen.jpeg)
├── generated_scenes/                   # Kho ảnh slide đã render (tỉ lệ 16:9, Pixar 3D)
│   ├── dai_tiec_toan_canh_6_ban.jpg    # Poster đại cảnh 4K hội tụ toàn bộ 6 bàn vuông (33 nhân sự)
│   ├── slide_ban1_vip.jpg              # Slide Bàn 1: VIP Lãnh đạo & Tấn Sỹ sang mời
│   ├── slide_ban2_thucthan.jpg         # Slide Bàn 2: Thực thần đùi gà & Thầy bói tiệc nhậu
│   ├── slide_ban3_chiem.jpg            # Slide Bàn 3: Hội chị em rạng rỡ & selfie sống ảo
│   ├── slide_ban4_suachua.jpg          # Slide Bàn 4: Nữ doanh nhân sữa chua & anh bóc tôm
│   ├── slide_ban5_bolero.jpg           # Slide Bàn 5: Ban nhạc bolero & tuyệt đỉnh rót bia
│   ├── scene_template_ban_vuong_6nguoi.jpg # Slide Bàn 6: Biệt đội bất tử 100% & đếm vỏ chai
│   ├── scene1_binh_host.jpg            # Spotlight: Giám đốc Bình chủ tiệc
│   ├── scene2_thaibao_chicken.jpg      # Spotlight: Thái Bảo mê đùi gà
│   ├── scene3_thanh_thao_fortune.jpg   # Spotlight: Thầy bói Lê Cao Thanh & Mai Thảo
│   ├── scene4_tan_toast_director.jpg   # Spotlight: TP Tân kính sếp Bình
│   ├── scene5_thao_philosopher.jpg     # Spotlight: Triết gia nhậu Quang Thảo
│   └── scene6_group1_ladies.jpg        # Spotlight: Nhóm 1 chị em rạng rỡ
├── SlideShow_TiecNhau.html             # Giao diện trình chiếu tương tác (đầy đủ 6 bàn vuông & 33 nhân sự)
├── update_excel_actions.py             # Script tự động cập nhật hành động & suy nghĩ vào Excel
├── build_slideshow_html.py             # Script biên dịch giao diện trình chiếu HTML
└── ProjectLog.md                       # Tài liệu lưu trữ thông tin dự án (File này)
```

---

## 🪑 SƠ ĐỒ BÀN VUÔNG 6 NGƯỜI (ĐẦY ĐỦ 33 NHÂN SỰ)

> **Quy cách**: Kiểu bàn vuông, mỗi bàn chuẩn 6 ghế ngồi. Mỗi bàn tương ứng 1 slide trình chiếu đặc tả biểu cảm và hành động cá nhân hài hước của từng thành viên.

---

### ⭐ BÀN 1: BÀN VIP LÃNH ĐẠO (Tâm Điểm Slide 1)
*Vị trí bàn trung tâm, có sự góp mặt của Nguyễn Tấn Sỹ trực tiếp sang kính cẩn mời rượu 3 Sếp.*

| Vị trí | Họ Tên | Mã NV | Chức Vụ | Hành Động & Biểu Cảm Hài Hước | Suy Nghĩ Độc Đáo |
|---|---|---|---|---|---|
| **Đầu bàn (Chính diện)** | **TRẦN NGUYÊN BÌNH** | 00043 | Giám Đốc | Tay cầm ly bia vàng bọt tuyết ngắm nghía và nghiêng đầu cười đĩnh đạc làm chủ bữa tiệc. | *"Hôm nay anh em vui là chính, hóa đơn cứ để đấy công ty lo, miễn mai đi làm đúng giờ là được!"* |
| **Cạnh phải** | **TRẦN THẾ VŨ** | 10630 | Trưởng Phòng | Đứng bật dậy một chân gác nhẹ lên ghế, một tay giơ cao chai bia hô vang: *"1 - 2 - 3... ZÔ 100%!"* | *"Khí thế hôm nay phải ngút trời, anh em phòng mình nhậu là phải nhất nhì công ty!"* |
| **Cạnh trái** | **NGUYỄN THANH TÂN** | 10091 | TP (Tổ Phó/Phó Phòng) | Hai tay nâng vại bia to bự hướng về Giám đốc Bình, người hơi cúi cung kính, nụ cười hết nấc. | *"Kính Giám đốc Bình chén này trước, lát nữa mình sẽ đi từng bàn thị sát tửu lượng anh em!"* |
| **Bên cạnh sang mời** | **NGUYỄN TẤN SỸ** | 12333 | Nhân Viên | Cầm ly bia hiên ngang bước sang bàn VIP, hai tay nâng ly kính cẩn chúc mừng Giám đốc Bình và hai sếp Vũ, Tân. | *"Cơ hội vàng ngàn năm có một để thể hiện bản lĩnh tửu lượng trước mặt Giám đốc Bình và các Sếp!"* |
| **Đối diện góc phải** | **ĐỖ TẤN LÂM** | 10863 | Nhân Viên | Đứng tựa mép bàn VIP, ngoái cổ sang bàn số 4 bên cạnh, giơ ly bia vẫy vẫy mời chào rôm rả. | *"Phải kéo nhóm 4 sang cụng ly với Giám đốc Bình cho không khí nóng lên mới được!"* |
| **Đối diện góc trái** | **LÊ KHẮC HÀ GIANG** | 10883 | Nhân Viên | Bưng đĩa tôm mực nướng bốc khói nghi ngút tiếp mồi cho các sếp bàn VIP, tay kia làm động tác bắn tim. | *"Mồi bàn VIP vơi nhanh quá, mình đi tiếp tế thế này các sếp khen chu đáo là cái chắc!"* |

---

### 🍗 BÀN 2: THỰC THẦN & THẦY BÓI HUYỀN BÍ (Slide 2)
*Góc bàn hài hước nhất bữa tiệc: Sự kết hợp giữa đam mê ăn uống bất tận và thầy bói dạo.*

| Ghế | Họ Tên | Mã NV | Hành Động & Biểu Cảm Độc Đáo | Suy Nghĩ Độc Đáo |
|---|---|---|---|---|
| 1 | **PHAN THANH THÁI BẢO** | 12953 | Hai mắt hình trái tim lấp lánh, miệng chảy nước miếng, tay ôm chặt chiếc đùi gà nướng bự chảng. | *"Mồi ngon hè... Mấy ông cứ tranh nhau uống đi, một mình tôi ôm trọn cái đùi gà này là ấm bụng nhất trần đời!"* |
| 2 | **LÊ CAO THANH** | 13011 | Đeo kính râm đen, mắt lim dim làm bộ cao nhân đắc đạo, nắm chặt tay Mai Thảo phán chỉ tay thần sầu. | *"Nhìn bàn tay này là biết số hưởng rồi, nhưng lát nữa tiền tính bill bàn này thì chắc chắn là em chịu nha Thảo!"* |
| 3 | **MAI THỊ THANH THẢO** | 51727 | Mắt mở to tròn xoe, tay che miệng há hốc kinh ngạc khi đưa tay cho thầy bói Lê Cao Thanh xem. | *"Trời ơi thầy Thanh phán chuẩn dữ dội, hồi chiều vừa lén mua sắm online hết nửa tháng lương!"* |
| 4 | **NGUYỄN QUANG THẢO** | 11466 | Ngồi chống cằm một tay tạo dáng Người suy tư, mắt nhìn xa xăm giữa tiếng hò reo zô ầm ĩ. | *"Uống bia để quên đi âu lo, hay chính vì uống bia mà mai thức dậy quên mất ví tiền ở đâu...?"* |
| 5 | **TRƯƠNG TẤN VŨ** | 11533 | Cười nắc nẻ ôm bụng, tay cầm ly bia giơ sang bàn 2 trêu cặp đôi bói toán Lê Cao Thanh & Mai Thảo. | *"Xem bói chỉ tay giữa bàn nhậu, kiểu này lát nữa thầy bói Thanh bị bắt bao nguyên chầu là cái chắc!"* |
| 6 | **TRẦN THỊ HỒNG ÁNH** | 49500 | Bật camera trước quay clip TikTok bắt trọn biểu cảm ăn đùi gà của Thái Bảo và quẻ bói của thầy Thanh. | *"Quay lại quả clip đắt giá này, mai đăng lên nhóm Zalo công ty thì bao cười cả tuần!"* |

---

### 💃 BÀN 3: NHÓM 1 - HỘI CHỊ EM RẠNG RỠ & SELFIE (Slide 3)
*Bàn tiệc tràn ngập sắc màu, năng lượng tươi vui, vừa uống bia vừa check-in sống ảo.*

| Ghế | Họ Tên | Mã NV | Hành Động & Biểu Cảm Độc Đáo | Suy Nghĩ Độc Đáo |
|---|---|---|---|---|
| 1 | **PHAN THỤC PHƯƠNG** | 20023 | Đứng dậy giơ cao ly bia bọt tuyết cười rạng rỡ như đóng quảng cáo bia Heineken. | *"Đã lên đồ đi tiệc là phải rực rỡ nhất quán, 1-2-3 Zô hết mình rồi mai tính tiếp!"* |
| 2 | **BÙI THỊ THU THUỶ** | 20433 | Hai tay chống cằm tạo dáng bông hoa nở bên cạnh đĩa ốc hương, cười duyên chụp ảnh. | *"Mặt mình góc này lên hình thon gọn quá nè, lát nhớ nhắc con Hương gửi ảnh gốc liền nha!"* |
| 3 | **NGUYỄN THỊ TỚI** | 20474 | Cầm đũa chỉ trỏ đĩa mực trứng chiên mắm, mắt lia khắp bàn tiệc tìm món độc lạ tiếp theo. | *"Bia thì nhấp môi cho có không khí thôi, còn mồi ngon thì nhất định không được để sót miếng nào!"* |
| 4 | **HOÀNG THỊ THANH HƯƠNG** | 23169 | Cầm smartphone giơ cao 45 độ, miệng liên tục hô *"1, 2, 3 chu môi nào!"* chụp liền 50 tấm ảnh nhóm. | *"Chụp 50 tấm chắc chọn được 1 tấm đẹp nhất đăng Facebook câu ngàn like cho coi!"* |
| 5 | **TRẦN THỊ THANH THỦY** | 45055 | Nghiêng đầu tạo dáng chữ V bên má, nụ cười tỏa nắng, tay cầm lon bia Saigon ướp lạnh. | *"Uống ít mà vui nhiều, giữ gìn nhan sắc để mai còn làm hoa khôi công ty chứ lị!"* |
| 6 | **TRƯƠNG THỊ ÁNH QUANG** | 52795 | Cầm ly bia quay sang cụng giao lưu với bàn VIP, nụ cười tươi tắn tự tin. | *"Giao lưu với sếp một ly chúc công ty năm nay thưởng Tết gấp ba cho anh em phấn khởi!"* |

---

### 🍨 BÀN 4: NHÓM 4 & ĐẠI BẢN DOANH SỮA CHUA (Slide 4)
*Góc bàn nhậu của nữ doanh nhân sữa chua Thu Liễu và hội chị em cùng tay bóc tôm ga-lăng Phước Huy.*

| Ghế | Họ Tên | Mã NV | Hành Động & Biểu Cảm Độc Đáo | Suy Nghĩ Độc Đáo |
|---|---|---|---|---|
| 1 | **LÊ THỊ THU LIỄU** | 20301 | Tay cầm đũa gắp miếng mực nướng đưa lên miệng nhưng dừng lại giữa chừng, mắt chớp chớp suy tư trầm ngâm. | *"Không biết chi nhánh sữa chua thứ 2 của mình hôm nay bán được mấy trăm hộp nhỉ, tí phải mở app kiểm tra doanh thu mới yên tâm nhậu tiếp!"* |
| 2 | **NGUYỄN PHƯỚC HUY** | 12498 | Ga-lăng bóc đĩa tôm nướng đầy ắp chia đều cho các chị em phụ nữ trên bàn, mồ hôi nhễ nhại nhưng cười rất tươi. | *"Phận làm nam nhi duy nhất bàn chị em, bóc tôm mỏi tay nhưng đổi lại được chị em rót bia đầy tràn!"* |
| 3 | **NGUYỄN THỊ KIỀU OANH** | 20122 | Vỗ tay đều đặn theo nhịp zô, nụ cười rạng rỡ khuấy động phong trào bàn chị em. | *"Cứ vỗ tay cổ vũ thật to, lát nữa mấy anh bàn VIP qua mời là chị em mình không ngán ly nào!"* |
| 4 | **HOÀNG THỊ SAU** | 20709 | Cầm vại bia cụng thật kêu với người bên cạnh, bọt bia bắn tung tóe đầy phấn khích. | *"Đã cầm ly lên là phải uống cạn đáy cốc, phong cách của Sau là không bao giờ để bia long đền!"* |
| 5 | **NGUYỄN THỊ MAI DUYÊN** | 23866 | Nụ cười má lúm đồng tiền duyên dáng, tay bưng đĩa dưa hấu tráng miệng mời cả bàn giải nhiệt. | *"Uống bia xong ăn miếng dưa hấu mát lịm này thì tỉnh táo ngay, lát còn quẩy hiệp 2 tăng 3!"* |
| 6 | **NGUYỄN THỊ NGUYÊN LỘC** | 34873 | Đang nhanh nhẹn phân phát khăn ướt và gắp đá viên bỏ vào ly bia cho từng người trong bàn. | *"Hậu cần chu đáo số 1 là đây, bia phải mát lạnh uống mới đã cái nư!"* |

---

### 🎤 BÀN 5: BAN NHẠC CÂY NHÀ LÁ VƯỜN & NGHỆ THUẬT RÓT BIA (Slide 5)
*Góc văn nghệ bolero đỉnh cao kết hợp với tay rót bia bọt tuyết chuyên nghiệp.*

| Ghế | Họ Tên | Mã NV | Hành Động & Biểu Cảm Độc Đáo | Suy Nghĩ Độc Đáo |
|---|---|---|---|---|
| 1 | **TRẦN TRUNG HIẾU** | 12690 | Cầm micro bằng cả hai tay, mắt nhắm nghiền phiêu nốt cao bài hit bolero chào mừng đại tiệc. | *"Đam mê ca hát cháy bỏng từ nhỏ, hôm nay có bia vào giọng mình ấm như ca sĩ Đan Trường vậy!"* |
| 2 | **NGUYỄN THỊ HẰNG** | 52270 | Cầm hai chiếc khăn giấy trắng vẫy vẫy múa phụ họa uốn lượn theo nhịp hát của ca sĩ Hiếu. | *"Làm fan cuồng cổ vũ nhiệt tình thế này, lát nữa anh Hiếu phải mời mình một ly bia cảm ơn nha!"* |
| 3 | **HỒ NGUYỄN TỐ NGUYÊN** | 52401 | Cầm hai chiếc đũa gõ nhịp chan chát vào miệng bát làm trống phụ họa cho ban nhạc bàn 5. | *"Tùng cắc tùng cắc, beat này hơi bị cháy, bàn mình quẩy xôm nhất cái quán nhậu này rồi!"* |
| 4 | **VÕ THỊ PHƯƠNG THẢO** | 24040 | Lắc lư theo điệu nhạc, một tay cầm ly bia sóng sánh, một tay giơ ngón tay cái cổ vũ bàn 5. | *"Nhạc hay bia ngon bạn hiền, tinh thần công ty hôm nay đúng là đỉnh nóc kịch trần bay phấp phới!"* |
| 5 | **PHẠM HỒNG VIỆT** | 11481 | Đứng nghiêng người rót bia điêu luyện từ trên cao xuống ly, canh đúng chuẩn tỉ lệ 7 phần bia 3 phần bọt. | *"Nghệ thuật rót bia đỉnh cao này phải luyện chục năm mới được, bọt mịn như kem tuyết!"* |
| 6 | *(Ghế giao lưu nhạc hội)* | — | Cầm ly bia đứng nhún nhảy cùng ban nhạc bàn 5, hát vang bài ca kết đoàn. | *"Vui quá là vui, tí nữa phải lên hát song ca bài Tàu Anh Qua Núi mới chịu!"* |

---

### 🛡️ BÀN 6: BIỆT ĐỘI BẤT TỬ 100% (Slide 6)
*Bàn tiệc của các chiến thần trụ cột kiên cường đến giọt cuối cùng của bữa tiệc.*

| Ghế | Họ Tên | Mã NV | Hành Động & Biểu Cảm Độc Đáo | Suy Nghĩ Độc Đáo |
|---|---|---|---|---|
| 1 | **TRẦN THỊ KIM THỦY** | 20434 | Nữ tướng oai phong, một tay chống hông, một tay nâng vại bia không hề nao núng trước phái nam. | *"Đừng nghĩ chị em phụ nữ không biết uống, bàn 6 hôm nay tôi chấp hết các đấng mày râu!"* |
| 2 | **TRẦN VĂN LONG** | 13038 | Tay khoác vai đồng đội, tay kia giơ nắm đấm hô hào quyết tâm chiến đấu tới giọt bia cuối cùng. | *"Đã ngồi bàn 6 là tinh thần thép, không say không về, ai trốn về sớm phạt 1 két!"* |
| 3 | **HỒ VĂN THƯỜNG** | 13044 | Ngồi đếm hàng vỏ chai bia rỗng xếp dài dưới chân bàn với nụ cười cực kỳ đắc chí và tự hào. | *"Mới xếp được có 3 hàng vỏ chai thôi mà, tối nay phải lập kỷ lục Guinness quán nhậu này mới chịu!"* |
| 4 | **NGÔ ĐÌNH MINH THÀNH** | 13075 | Lấy vạt áo lau mồ hôi trên trán cười toe toét, mắt vẫn sáng rực đầy năng lượng chiến đấu. | *"Nóng quá nhưng mà vui quá trời! Em vẫn còn tỉnh queo nha anh Long ơi, rót tiếp đi!"* |
| 5 | *(Ghế chi viện hỏa lực)* | — | Bê nguyên thùng bia ướp lạnh sang chi viện hỏa lực cho bàn 6. | *"Thấy bàn 6 sung sức quá nên mang thêm vũ khí bia mát lạnh sang chi viện!"* |
| 6 | *(Ghế tổng kết tranh cúp)* | — | Cụng ly tổng kết bàn 6 giữ vững ngai vàng bất tử tửu lượng của công ty. | *"Bàn 6 chuẩn bị lên bục nhận giải Bàn Tiệc Vô Địch Đại Hội Bia MBC 2026!"* |

---

## 🎨 CẬP NHẬT RENDER THUẦN AI GIỮ NÉT MẶT THẬT (REFERENCE FACES)

- **Phương pháp thực hiện**: Sử dụng mô hình sinh ảnh AI cao cấp kết hợp ảnh chân dung gốc (`ImagePaths`) từ `extracted_faces/` làm tham chiếu nhân trắc học (mắt, mũi, cằm, kiểu tóc, nụ cười đặc trưng) sang phong cách Pixar 3D:
  1. **`slide_ban1_vip.jpg`**: Render AI với ảnh tham chiếu Sếp Bình (`00043`), Tấn Sỹ (`12333`), Sếp Vũ (`10630`). Sếp Bình đĩnh đạc không kính, tóc rẽ ngôi làm chủ bàn; Tấn Sỹ nâng ly với bóng thoại chuẩn *"Em mời các anh vài ly! 🍻"*; Sếp Vũ giơ chai bia hô hào.
  2. **`slide_ban2_thucthan.jpg`**: Render AI với ảnh tham chiếu Thái Bảo (`12953`), Quang Thảo (`11466`), Lê Cao Thanh (`13011`). Thái Bảo ôm đùi gà nướng bự chảng với bóng thoại *"Mồi ngon hè... 🍗"*; Mr. Quang Thảo ngồi chung bàn chống cằm suy tư *"Uống bia để quên, hay quên vì uống bia...? 🤔"*; Thầy bói Lê Cao Thanh đeo kính râm xem tay Mai Thảo.
  3. **`slide_ban3_chiem.jpg`**: Render AI với ảnh tham chiếu Thục Phương (`20023`), Thanh Hương (`23169`), Thu Thủy (`20433`). 6 chị em rạng rỡ, góc chụp selfie 45 độ, tạo dáng hoa nở, nâng ly chúc mừng, loại bỏ hoàn toàn chữ thừa.
  4. **`slide_ban4_suachua.jpg`**: Render AI với ảnh tham chiếu Thu Liễu (`20301`), Phước Huy (`12498`). Chị Liễu gắp mồi suy tư *"Chi nhánh sữa chua thứ 2 hôm nay bán được mấy trăm hộp nhỉ...? 🍦"*; Phước Huy ga-lăng bóc tôm phục vụ bàn tiệc.
  5. **`slide_ban5_bolero.jpg`**: Render AI với ảnh tham chiếu Trung Hiếu (`12690`), Hồng Việt (`11481`). Trung Hiếu hát bolero truyền cảm với nốt nhạc bay bổng; Hồng Việt rót bia bọt tuyết chuẩn tỷ lệ vàng 7:3.
  6. **`phong_tiec_toan_canh_5_ban.jpg`**: Render trực tiếp 1 bức tranh toàn cảnh đại tiệc góc rộng (Cinematic Wide-Angle 3D Pixar) tích hợp cả 5 bàn tiệc cùng diễn ra trong 1 không gian nhà hàng lộng lẫy đèn lồng và view thành phố về đêm.
- **Đồng bộ**: Đã cập nhật file `SlideShow_TiecNhau.html`, `build_slideshow_html.py`, `update_excel_actions.py`, `DanhSachAnhBHCL.xlsm`.

---

## 🏷️ TÍCH HỢP GHIM MẶT THẬT TƯƠNG TÁC & BẢNG SUY NGHĨ TỪNG NGƯỜI (SLIDESHOW V4)

1. **Ghim Khuôn Mặt Thật Tương Tác Trên Ảnh (On-Image Face Pins)**:
   - Tích hợp lớp hiển thị ghim điểm ảnh (`.pins-layer`) trực tiếp trên khung ảnh của từng slide.
   - Mỗi nhân vật đều có một chiếc ghim gồm **Avatar ảnh thẻ thật chất lượng cao** (viền vàng gold phát sáng) + **Tên nhân sự** + **Bóng thoại / Đám mây suy nghĩ đặc trưng** tương ứng ngay trên đầu nhân vật trong bức ảnh 3D.
   - Nút bấm **[🏷️ Ẩn / Hiện Ghim Mặt & Lời Thoại]** cho phép bật/tắt ghim tức thì.
   - Khi click vào ghim trên ảnh, trang web tự động cuộn xuống và làm nổi bật (highlight vàng/đỏ) thẻ của nhân sự đó bên dưới!

2. **Bảng Danh Sách Thành Viên & Suy Nghĩ Từng Người (Interactive People & Thoughts Deck)**:
   - Bố trí ngay dưới các ảnh thumbnail trong View trình chiếu slide.
   - Tự động thay đổi đồng bộ theo từng slide đang xem:
     - Slide 0: Hiển thị tiêu điểm của 5 bàn tiệc tiêu biểu trong đại sảnh.
     - Slide 1: Đầy đủ 6 nhân sự Bàn 1 VIP (Sếp Bình, Sếp Vũ, TP Tân, Tấn Sỹ, Tấn Lâm, Hà Giang) kèm ảnh thật, chức vụ, hành động và suy nghĩ độc quyền.
     - Slide 2: Đầy đủ 6 nhân sự Bàn 2 Thực thần (Thái Bảo, Lê Cao Thanh, Mai Thảo, Quang Thảo, Tấn Vũ, Hồng Ánh).
     - Slide 3, 4, 5, 6: Đầy đủ từng thành viên ứng với từng bàn tiệc.
   - Khung suy nghĩ được thiết kế dạng trích dẫn nổi bật (`💭 "..."`) với tông màu vàng hổ phách, chữ nghiêng sắc nét, đọc được ngay lập tức.

3. **Xác minh thực tế (Browser Subagent Verification)**:
   - Đã chạy kiểm tra tự động toàn bộ luồng hiển thị qua browser: Slide 0, Slide 1, Slide 2, chuyển tab, bấm Next/Prev, click thumbnail, hiển thị avatar thật và suy nghĩ từng người đều hoạt động mượt mà 100%.

---

## 🎨 HOÀN THIỆN BỘ ẢNH CHUẨN PHONG CÁCH COMIC BÀN 2 (ĐỦ 6 NGƯỜI RÕ MẶT MỖI BÀN)

Theo yêu cầu chuẩn hóa toàn bộ các slide theo phong cách hài hước, bóng thoại và suy nghĩ trực tiếp trong ảnh như `slide_ban2_thucthan.jpg` và đảm bảo **ĐỦ 6 THÀNH VIÊN HIỆN DIỆN RÕ RÀNG QUANH BÀN**:
1. **`slide_ban1_vip.jpg` (Đủ 6 người)**:
   - Sếp Bình (`00043`) đĩnh đạc không kính, tóc rẽ ngôi làm chủ bàn tiệc: `"Công ty lo, vui là chính! 👑"`.
   - TP Nguyễn Thanh Tân (`10091`) hai tay nâng vại bia to bự cười cung kính hướng về sếp Bình: `"Kính Giám đốc chén này trước! 🙌"`.
   - Sếp Vũ (`10630`) đứng bật dậy giơ cao chai bia hô hào: `"1 - 2 - 3... ZÔ 100%! 🔥"`.
   - Tấn Sỹ (`12333`) hai tay nâng ly bia kính chúc: `"Em mời các anh vài ly! 🍻"`.
   - Tấn Lâm (`10863`) tựa mép bàn ngoái cổ sang vẫy chào nhóm 4.
   - Hà Giang (`10883`) bưng đĩa tôm mực nướng bốc khói nghi ngút tiếp mồi cho các sếp.
2. **`slide_ban2_thucthan.jpg` (Đủ 6 người)**:
   - Thái Bảo (`12953`) mắt sao sáng rực ôm đùi gà nướng bự chảng chảy nước miếng: `"Mồi ngon hè... 🍗"`.
   - Mr. Quang Thảo (`11466`) chống cằm suy tư triết gia: `"Uống bia thế này tối về ngứa kiếm ai gãi đây...? 🤔"`.
   - Thầy bói Lê Cao Thanh (`13011`) đeo kính râm phán chỉ tay cho Mai Thảo: `"Lát bill em chịu nha Thảo! 🔮"`.
   - Mai Thảo (`51727`) hai tay che miệng kinh ngạc há hốc trước quẻ bói.
   - Tấn Vũ (`11533`) cười nắc nẻ ôm bụng nâng ly bia trêu cặp đôi bói toán.
   - Hồng Ánh (`49500`) giơ điện thoại quay clip TikTok bắt trọn biểu cảm cả bàn.
3. **`slide_ban3_chiem.jpg` (Đủ 6 chị em)**:
   - Thanh Hương (`23169`) giơ điện thoại góc 45 độ selfie: `"1, 2, 3 chu môi nào! 📸"`.
   - Thục Phương (`20023`) đứng dậy cười rạng rỡ nâng vại bia: `"Zô 100% hết mình! 💃"`.
   - Thu Thủy (`20433`) tạo dáng hoa nở bên má: `"Góc này mặt thon gọn ghê! 🌸"`.
   - Nguyễn Thị Tới (`20474`) cầm đũa gắp món mực trứng chiên mắm săn mồi: `"Mồi ngon không sót miếng nào! 🍤"`.
   - Thanh Thủy (`45055`) tạo dáng chữ V bên má hoa khôi.
   - Ánh Quang (`52795`) cụng bia chúc mừng sang bàn VIP.
4. **`slide_ban4_suachua.jpg` (Đủ 6 người)**:
   - Thu Liễu (`20301`) gắp mồi đưa lên miệng nhưng dừng giữa chừng mơ màng: `"Chi nhánh sữa chua thứ 2 hôm nay bán mấy trăm hộp nhỉ...? 🍦"`.
   - Phước Huy (`12498`) mồ hôi nhễ nhại cười tươi bóc đĩa tôm nướng phục vụ chị em: `"Bóc tôm phục vụ chị em! 🦐"`.
   - Hoàng Sau (`20709`) cụng bia dứt khoát: `"Không bao giờ để bia long đền! 🍻"`.
   - Kiều Oanh (`20122`) vỗ tay khuấy động phong trào; Mai Duyên (`23866`) bưng đĩa dưa hấu mát lịm; Nguyên Lộc (`34873`) nhanh nhẹn gắp đá viên và khăn ướt.
5. **`slide_ban5_bolero.jpg` (Đủ 6 người)**:
   - Trung Hiếu (`12690`) cầm micro nhắm nghiền mắt phiêu nốt cao kèm nốt nhạc: `"Giọng ấm phiêu bolero cháy máy! 🎤"`.
   - Hồng Việt (`11481`) nghiêng chai rót bia bọt tuyết chuẩn chỉnh: `"Nghệ thuật rót bia tỉ lệ 7:3! 🍺"`.
   - Phương Thảo (`24040`) cầm guitar đệm nhạc; Tố Nguyên (`52401`) gõ đũa bát làm trống; Nguyễn Thị Hằng (`52270`) vẫy khăn giấy múa phụ họa; Bạn bè cùng bàn zô 100%.
6. **`slide_ban6_battu.jpg` (Đủ 6 người)**:
   - Nữ tướng Kim Thủy (`20434`) tay chống hông nâng vại bia khổng lồ: `"Chấp hết các đấng mày râu! 👑"`.
   - Anh Long (`13038`) giơ nắm đấm khí thế: `"Không say không về! 🦾"`.
   - Anh Thường (`13044`) đắc ý chỉ xuống 3 hàng vỏ chai xanh xếp dài dưới gầm bàn: `"Kỷ lục Guinness 3 hàng vỏ chai! 🍾"`.
   - Minh Thành (`13075`) lấy vạt áo lau mồ hôi cười toe toét; Đồng đội bê thùng bia chi viện; Đại diện cụng ly tranh cúp vô địch.
- Đã đồng bộ toàn bộ ảnh mới và cập nhật suy nghĩ mới của Quang Thảo vào `SlideShow_TiecNhau.html`, `build_slideshow_html.py`, `update_excel_actions.py`, `DanhSachAnhBHCL.xlsm`.

---

## 🌟 TINH CHỈNH BÀN 1 VIP, ĐỒNG BỘ MÀU BÀN 3, 5, 6 & ĐẠI CẢNH 6 BÀN BHCL

1. **Bàn 1 VIP (`slide_ban1_vip.jpg`)**:
   - Giữ nguyên nét mặt chuẩn của Giám Đốc Bình và TP Thanh Tân.
   - Tinh chỉnh chuẩn nhân trắc học theo ảnh thẻ thật cho **Trần Thế Vũ** (`10630`, dáng đứng phong độ chững chạc, chân mày rậm chữ điền), **Đỗ Tấn Lâm** (`10863`, mặt tròn đầy đặn mắt sáng tươi cười), và **Lê Khắc Hà Giang** (`10883`, thanh tú tóc mái trẻ trung tiếp mồi).
   - Cập nhật đúng câu thoại yêu cầu:
     - 💭 Giám Đốc Bình: *"Vui là chính, mình anh lo hết 👑"*
     - 💬 TP Thanh Tân: *"Giám đốc Bình nói vậy mời Giám đốc 1 ly! 🍻"*

2. **Đồng Bộ Màu Bàn 3 & Bàn 6 Theo Chuẩn `slide_ban6_ver1.jpg`**:
   - **`slide_ban3_chiem.jpg`**: Đủ 6 chị em, đưa về tone màu ấm độ tương phản cao, bàn gỗ tự nhiên, đèn lồng và đèn dây lung linh, áo polo trắng viền xanh rực rỡ, khuôn mặt chuẩn theo ảnh thẻ gốc.
   - **`slide_ban6_battu.jpg`**: Đủ 6 thành viên, giữ trọn tone màu chuẩn và 3 hàng vỏ chai bia Guinness xanh mướt của `slide_ban6_ver1.jpg`.

3. **Bàn 5 Bolero (`slide_ban5_bolero.jpg`)**:
   - Render lại đồng bộ Pixar 3D ấm áp như Bàn 4, đủ 6 thành viên quanh bàn vuông.

4. **Toàn Cảnh 6 Bàn Vuông BHCL (`phong_tiec_toan_canh_6_ban.jpg`)**:
   - Render khung cảnh góc rộng phòng tiệc riêng ấm cúng chỉ có đúng 6 bàn vuông với backdrop *"MỪNG TIỆC BHCL"*.

5. **Hệ Thống Đã Được Đồng Bộ Toàn Diện**:
   - `DanhSachAnhBHCL.xlsm`: Đã cập nhật đủ 33 dòng hành động & suy nghĩ mới nhất.
   - `SlideShow_TiecNhau.html` & `build_slideshow_html.py`: Đã cập nhật tọa độ ghim và hiển thị tương tác.
