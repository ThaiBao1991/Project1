# -*- coding: utf-8 -*-
import os
import json

base_dir = os.path.dirname(__file__)
html_file = os.path.join(base_dir, 'SlideShow_TiecNhau.html')

tables_data = [
  {
    'name': '⭐ BÀN 1: BÀN VIP LÃNH ĐẠO (BÀN VUÔNG TRUNG TÂM)',
    'vip': True,
    'seats': [
      {
        'mnv': '00043', 'name': 'TRẦN NGUYÊN BÌNH', 'role': '👑 GIÁM ĐỐC (CHỦ TIỆC)', 'img': '00043_TRAN_NGUYEN_BINH.jpeg', 'leader': True,
        'action': 'Tay cầm ly bia vàng bọt tuyết ngắm nghía và nghiêng đầu cười đĩnh đạc làm chủ bữa tiệc.',
        'thought': 'Vui là chính, mình anh lo hết 👑'
      },
      {
        'mnv': '10630', 'name': 'TRẦN THẾ VŨ', 'role': '🔥 TRƯỞNG PHÒNG', 'img': '10630_TRẦN_THẾ_VŨ.jpeg', 'leader': True,
        'action': 'Đứng bật dậy một chân gác nhẹ lên ghế, một tay giơ cao chai bia hô vang dõng dạc: "1 - 2 - 3... ZÔ 100%!"',
        'thought': 'Khí thế hôm nay phải ngút trời, anh em phòng mình nhậu là phải nhất nhì công ty!'
      },
      {
        'mnv': '10091', 'name': 'NGUYỄN THANH TÂN', 'role': '🙌 TỔ PHÓ (TP)', 'img': '10091_NGUYỄN_THANH_TÂN.jpeg', 'leader': True,
        'action': 'Hai tay nâng vại bia to bự hướng về Giám đốc Bình, người hơi cúi cung kính, nụ cười hết nấc.',
        'thought': 'Giám đốc Bình nói vậy mời Giám đốc 1 ly! 🍻'
      },
      {
        'mnv': '12333', 'name': 'NGUYỄN TẤN SỸ', 'role': '🍻 SANG KÍNH CẨN MỜI SẾP', 'img': '12333_NGUYỄN_TẤN_SỸ.jpeg', 'leader': True,
        'action': 'Cầm ly bia hiên ngang bước sang bàn VIP, hai tay nâng ly kính cẩn chúc mừng Giám đốc Bình và hai sếp Vũ, Tân.',
        'thought': 'Cơ hội vàng ngàn năm có một để thể hiện bản lĩnh tửu lượng trước mặt Giám đốc Bình và các Sếp!'
      },
      {
        'mnv': '10863', 'name': 'ĐỖ TẤN LÂM', 'role': 'GIAO LƯU NGOẠI GIAO', 'img': '10863_ĐỖ_TẤN_LÂM.jpeg', 'leader': False,
        'action': 'Đứng tựa mép bàn VIP, ngoái cổ sang bàn số 4 bên cạnh, giơ ly bia vẫy vẫy mời chào rôm rả.',
        'thought': 'Phải kéo nhóm 4 sang cụng ly với Giám đốc Bình cho không khí nóng lên mới được!'
      },
      {
        'mnv': '10883', 'name': 'LÊ KHẮC HÀ GIANG', 'role': 'TIẾP TẾ LỬA BÀN VIP', 'img': '10883_LÊ_KHẮC_HÀ_GIANG.jpeg', 'leader': False,
        'action': 'Bưng đĩa tôm mực nướng bốc khói nghi ngút tiếp mồi cho các sếp bàn VIP, tay kia làm động tác bắn tim.',
        'thought': 'Mồi bàn VIP vơi nhanh quá, mình đi tiếp tế thế này các sếp khen chu đáo là cái chắc!'
      }
    ]
  },
  {
    'name': '🍗 BÀN 2: THỰC THẦN & THẦY BÓI HUYỀN BÍ',
    'vip': False,
    'seats': [
      {
        'mnv': '12953', 'name': 'PHAN THANH THÁI BẢO', 'role': '🍗 TÍN ĐỒ ĐÙI GÀ', 'img': '12953_PHAN_THANH_THÁI_BẢO.jpeg', 'leader': True,
        'action': 'Hai mắt hình trái tim lấp lánh, miệng chảy nước miếng, tay ôm chặt chiếc đùi gà nướng bự chảng.',
        'thought': 'Mồi ngon hè... Mấy ông cứ tranh nhau uống đi, một mình tôi ôm trọn cái đùi gà này là ấm bụng nhất trần đời!'
      },
      {
        'mnv': '13011', 'name': 'LÊ CAO THANH', 'role': '🔮 THẦY BÓI TIỆC NHẬU', 'img': '13011_LÊ_CAO_THANH.jpeg', 'leader': False,
        'action': 'Đeo kính râm đen, mắt lim dim làm bộ cao nhân đắc đạo, nắm chặt tay Mai Thảo phán chỉ tay thần sầu.',
        'thought': 'Nhìn bàn tay này là biết số hưởng rồi, nhưng lát nữa tiền tính bill bàn này thì chắc chắn là em chịu nha Thảo!'
      },
      {
        'mnv': '51727', 'name': 'MAI THỊ THANH THẢO', 'role': '😱 THÂN CHỦ SỐC', 'img': '51727_MAI_THỊ_THANH_THẢO.jpeg', 'leader': False,
        'action': 'Mắt mở to tròn xoe, tay che miệng há hốc kinh ngạc khi đưa tay cho thầy bói Lê Cao Thanh xem.',
        'thought': 'Trời ơi thầy Thanh phán chuẩn dữ dội, hồi chiều vừa lén mua sắm online hết nửa tháng lương!'
      },
      {
        'mnv': '11466', 'name': 'NGUYỄN QUANG THẢO', 'role': '🤔 TRIẾT GIA NHẬU', 'img': '11466_NGUYỄN_QUANG_THẢO.jpeg', 'leader': False,
        'action': 'Ngồi chống cằm một tay tạo dáng Người suy tư, mắt nhìn xa xăm giữa tiếng hò reo zô ầm ĩ.',
        'thought': 'Uống bia thế này tối về ngứa kiếm ai gãi đây...? 🤔'
      },
      {
        'mnv': '11533', 'name': 'TRƯƠNG TẤN VŨ', 'role': '😂 CƯỜI VỠ BỤNG', 'img': '11533_TRƯƠNG_TẤN_VŨ.jpeg', 'leader': False,
        'action': 'Cười nắc nẻ ôm bụng, tay cầm ly bia giơ sang trêu cặp đôi bói toán Lê Cao Thanh & Mai Thảo.',
        'thought': 'Xem bói chỉ tay giữa bàn nhậu, kiểu này lát nữa thầy bói Thanh bị bắt bao nguyên chầu là cái chắc!'
      },
      {
        'mnv': '49500', 'name': 'TRẦN THỊ HỒNG ÁNH', 'role': '📱 TIKTOKER BẮT TREND', 'img': '49500_TRẦN_THỊ_HỒNG_ÁNH.jpeg', 'leader': False,
        'action': 'Bật camera trước quay clip TikTok bắt trọn biểu cảm ăn đùi gà của Thái Bảo và quẻ bói của thầy Thanh.',
        'thought': 'Quay lại quả clip đắt giá này, mai đăng lên nhóm Zalo công ty thì bao cười cả tuần!'
      }
    ]
  },
  {
    'name': '💃 BÀN 3: NHÓM 1 - HỘI CHỊ EM RẠNG RỠ & SELFIE',
    'vip': False,
    'seats': [
      {
        'mnv': '20023', 'name': 'PHAN THỤC PHƯƠNG', 'role': '💃 RẠNG RỠ TỎA SÁNG', 'img': '20023_PHAN_THỤC_PHƯƠNG.jpeg', 'leader': True,
        'action': 'Đứng dậy giơ cao ly bia bọt tuyết cười rạng rỡ như đóng quảng cáo bia Heineken.',
        'thought': 'Đã lên đồ đi tiệc là phải rực rỡ nhất quán, 1-2-3 Zô hết mình rồi mai tính tiếp!'
      },
      {
        'mnv': '20433', 'name': 'BÙI THỊ THU THUỶ', 'role': '🌸 TẠO DÁNG NÀNG THƠ', 'img': '20433_BÙI_THỊ_THU_THUỶ.jpeg', 'leader': False,
        'action': 'Hai tay chống cằm tạo dáng bông hoa nở bên cạnh đĩa ốc hương, cười duyên chụp ảnh.',
        'thought': 'Mặt mình góc này lên hình thon gọn quá nè, lát nhớ nhắc con Hương gửi ảnh gốc liền nha!'
      },
      {
        'mnv': '20474', 'name': 'NGUYỄN THỊ TỚI', 'role': '🍤 CHUYÊN GIA SĂN MỒI', 'img': '20474_NGUYỄN_THỊ_TỚI.jpeg', 'leader': False,
        'action': 'Cầm đũa chỉ trỏ đĩa mực trứng chiên mắm, mắt lia khắp bàn tiệc tìm món độc lạ tiếp theo.',
        'thought': 'Bia thì nhấp môi cho có không khí thôi, còn mồi ngon thì nhất định không được để sót miếng nào!'
      },
      {
        'mnv': '23169', 'name': 'HOÀNG THỊ THANH HƯƠNG', 'role': '📸 NHIẾP ẢNH GIA BÀN TIỆC', 'img': '23169_HOÀNG_THỊ_THANH_HƯƠNG.jpeg', 'leader': False,
        'action': 'Cầm smartphone giơ cao 45 độ, miệng liên tục hô "1, 2, 3 chu môi nào!" chụp liền 50 tấm ảnh nhóm.',
        'thought': 'Chụp 50 tấm chắc chọn được 1 tấm đẹp nhất đăng Facebook câu ngàn like cho coi!'
      },
      {
        'mnv': '45055', 'name': 'TRẦN THỊ THANH THỦY', 'role': '✌️ HOA KHÔI TẠO DÁNG', 'img': '45055_TRẦN_THỊ_THANH_THỦY.jpeg', 'leader': False,
        'action': 'Nghiêng đầu tạo dáng chữ V bên má, nụ cười tỏa nắng, tay cầm lon bia Saigon ướp lạnh.',
        'thought': 'Uống ít mà vui nhiều, giữ gìn nhan sắc để mai còn làm hoa khôi công ty chứ lị!'
      },
      {
        'mnv': '52795', 'name': 'TRƯƠNG THỊ ÁNH QUANG', 'role': '🥂 GIAO LƯU NHIỆT THÀNH', 'img': '52795_TRƯƠNG_THỊ_ÁNH_QUANG.jpeg', 'leader': False,
        'action': 'Cầm ly bia quay sang cụng giao lưu với bàn VIP, nụ cười tươi tắn tự tin.',
        'thought': 'Giao lưu với sếp một ly chúc công ty năm nay thưởng Tết gấp ba cho anh em phấn khởi!'
      }
    ]
  },
  {
    'name': '🍨 BÀN 4: NHÓM 4 & ĐẠI BẢN DOANH SỮA CHUA',
    'vip': False,
    'seats': [
      {
        'mnv': '20301', 'name': 'LÊ THỊ THU LIỄU', 'role': '🍨 NỮ DOANH NHÂN SỮA CHUA', 'img': '20301_LÊ_THỊ_THU_LIỄU.jpeg', 'leader': True,
        'action': 'Tay cầm đũa gắp miếng mực nướng đưa lên miệng nhưng dừng lại giữa chừng, mắt chớp chớp suy tư trầm ngâm.',
        'thought': 'Không biết chi nhánh sữa chua thứ 2 của mình hôm nay bán được mấy trăm hộp nhỉ, tí phải mở app kiểm tra doanh thu mới yên tâm nhậu tiếp!'
      },
      {
        'mnv': '12498', 'name': 'NGUYỄN PHƯỚC HUY', 'role': '🦐 NAM NHI GA-LĂNG BÓC TÔM', 'img': '12498_NGUYỄN_PHƯỚC_HUY.jpeg', 'leader': False,
        'action': 'Ga-lăng bóc đĩa tôm nướng đầy ắp chia đều cho các chị em phụ nữ trên bàn, mồ hôi nhễ nhại nhưng cười rất tươi.',
        'thought': 'Phận làm nam nhi duy nhất bàn chị em, bóc tôm mỏi tay nhưng đổi lại được chị em rót bia đầy tràn!'
      },
      {
        'mnv': '20122', 'name': 'NGUYỄN THỊ KIỀU OANH', 'role': '👏 CÂY VĂN NGHỆ KHUẤY ĐỘNG', 'img': '20122_NGUYỄN_THỊ_KIỀU_OANH.jpeg', 'leader': False,
        'action': 'Vỗ tay đều đặn theo nhịp zô, nụ cười rạng rỡ khuấy động phong trào bàn chị em.',
        'thought': 'Cứ vỗ tay cổ vũ thật to, lát nữa mấy anh bàn VIP qua mời là chị em mình không ngán ly nào!'
      },
      {
        'mnv': '20709', 'name': 'HOÀNG THỊ SAU', 'role': '🍻 TỬU LƯỢNG KHÔNG LONG ĐỀN', 'img': '20709_HOÀNG_THỊ_SAU.jpeg', 'leader': False,
        'action': 'Cầm vại bia cụng thật kêu với người bên cạnh, bọt bia bắn tung tóe đầy phấn khích.',
        'thought': 'Đã cầm ly lên là phải uống cạn đáy cốc, phong cách của Sau là không bao giờ để bia long đền!'
      },
      {
        'mnv': '23866', 'name': 'NGUYỄN THỊ MAI DUYÊN', 'role': '🍉 ĐỆ NHẤT MÁ LÚM TRÁI CÂY', 'img': '23866_NGUYỄN_THỊ_MAI_DUYÊN.jpeg', 'leader': False,
        'action': 'Nụ cười má lúm đồng tiền duyên dáng, tay bưng đĩa dưa hấu tráng miệng mời cả bàn giải nhiệt.',
        'thought': 'Uống bia xong ăn miếng dưa hấu mát lịm này thì tỉnh táo ngay, lát còn quẩy hiệp 2 tăng 3!'
      },
      {
        'mnv': '34873', 'name': 'NGUYỄN THỊ NGUYÊN LỘC', 'role': '🧊 TỔ TRƯỞNG HẬU CẦN ĐÁ VIÊN', 'img': '34873_NGUYỄN_THỊ_NGUYÊN_LỘC.jpeg', 'leader': False,
        'action': 'Đang nhanh nhẹn phân phát khăn ướt và gắp đá viên bỏ vào ly bia cho từng người trong bàn.',
        'thought': 'Hậu cần chu đáo số 1 là đây, bia phải mát lạnh uống mới đã cái nư!'
      }
    ]
  },
  {
    'name': '🎤 BÀN 5: BAN NHẠC CÂY NHÀ LÁ VƯỜN & NGHỆ THUẬT RÓT BIA',
    'vip': False,
    'seats': [
      {
        'mnv': '12690', 'name': 'TRẦN TRUNG HIẾU', 'role': '🎤 CA SĨ HIT BOLERO', 'img': '12690_TRÂN_TRUNG_HIÊU.jpeg', 'leader': True,
        'action': 'Cầm micro bằng cả hai tay, mắt nhắm nghiền phiêu nốt cao bài hit bolero chào mừng đại tiệc.',
        'thought': 'Đam mê ca hát cháy bỏng từ nhỏ, hôm nay có bia vào giọng mình ấm như ca sĩ Đan Trường vậy!'
      },
      {
        'mnv': '52270', 'name': 'NGUYỄN THỊ HẰNG', 'role': '💃 TRƯỞNG NHÓM FAN CUỒNG', 'img': '52270_NGUYỄN_THỊ_HẰNG.jpeg', 'leader': False,
        'action': 'Cầm hai chiếc khăn giấy trắng vẫy vẫy múa phụ họa uốn lượn theo nhịp hát của ca sĩ Hiếu.',
        'thought': 'Làm fan cuồng cổ vũ nhiệt tình thế này, lát nữa anh Hiếu phải mời mình một ly bia cảm ơn nha!'
      },
      {
        'mnv': '52401', 'name': 'HỒ NGUYỄN TỐ NGUYÊN', 'role': '🥁 TAY TRỐNG BÁT ĐŨA', 'img': '52401_HỒ_NGUYỄN_TỐ_NGUYÊN.jpeg', 'leader': False,
        'action': 'Cầm hai chiếc đũa gõ nhịp chan chát vào miệng bát làm trống phụ họa cho ban nhạc bàn 5.',
        'thought': 'Tùng cắc tùng cắc, beat này hơi bị cháy, bàn mình quẩy xôm nhất cái quán nhậu này rồi!'
      },
      {
        'mnv': '24040', 'name': 'VÕ THỊ PHƯƠNG THẢO', 'role': '🎵 KHUẤY ĐỘNG GIAI ĐIỆU', 'img': '24040_VÕ_THỊ_PHƯƠNG_THẢO.jpeg', 'leader': False,
        'action': 'Lắc lư theo điệu nhạc, một tay cầm ly bia sóng sánh, một tay giơ ngón tay cái cổ vũ bàn 5.',
        'thought': 'Nhạc hay bia ngon bạn hiền, tinh thần công ty hôm nay đúng là đỉnh nóc kịch trần bay phấp phới!'
      },
      {
        'mnv': '11481', 'name': 'PHẠM HỒNG VIỆT', 'role': '🍺 NGHỆ SĨ RÓT BIA BỌT TUYẾT', 'img': '11481_PHẠM_HỒNG_VIỆT.jpeg', 'leader': False,
        'action': 'Đứng nghiêng người rót bia điêu luyện từ trên cao xuống ly, canh đúng chuẩn tỉ lệ 7 phần bia 3 phần bọt.',
        'thought': 'Nghệ thuật rót bia đỉnh cao này phải luyện chục năm mới được, bọt mịn như kem tuyết!'
      },
      {
        'mnv': 'GIAOLUU5', 'name': 'GHẾ GIAO LƯU NHẠC HỘI', 'role': '🎉 KHÁN GIẢ GIAO DUYÊN', 'img': '', 'leader': False,
        'action': 'Cầm ly bia đứng nhún nhảy cùng ban nhạc bàn 5, hát vang bài ca kết đoàn.',
        'thought': 'Vui quá là vui, tí nữa phải lên hát song ca bài Tàu Anh Qua Núi mới chịu!'
      }
    ]
  },
  {
    'name': '🛡️ BÀN 6: BIỆT ĐỘI BẤT TỬ 100% (TRỤ CỘT TỚI SÁNG)',
    'vip': False,
    'seats': [
      {
        'mnv': '20434', 'name': 'TRẦN THỊ KIM THỦY', 'role': '👑 NỮ TƯỚNG TỬU LƯỢNG', 'img': '20434_TRẦN_THỊ_KIM_THỦY.jpeg', 'leader': True,
        'action': 'Nữ tướng oai phong, một tay chống hông, một tay nâng vại bia không hề nao núng trước phái nam.',
        'thought': 'Đừng nghĩ chị em phụ nữ không biết uống, bàn 6 hôm nay tôi chấp hết các đấng mày râu!'
      },
      {
        'mnv': '13038', 'name': 'TRẦN VĂN LONG', 'role': '🦾 CHIẾN THẦN THÉP', 'img': '13038_TRẦN_VĂN_LONG.jpeg', 'leader': False,
        'action': 'Tay khoác vai đồng đội, tay kia giơ nắm đấm hô hào quyết tâm chiến đấu tới giọt bia cuối cùng.',
        'thought': 'Đã ngồi bàn 6 là tinh thần thép, không say không về, ai trốn về sớm phạt 1 két!'
      },
      {
        'mnv': '13044', 'name': 'HỒ VĂN THƯỜNG', 'role': '🍾 KỶ LỤC GIA ĐẾM VỎ CHAI', 'img': '13044_HỒ_VĂN_THƯỜNG.jpeg', 'leader': False,
        'action': 'Ngồi đếm hàng vỏ chai bia rỗng xếp dài dưới chân bàn với nụ cười cực kỳ đắc chí và tự hào.',
        'thought': 'Mới xếp được có 3 hàng vỏ chai thôi mà, tối nay phải lập kỷ lục Guinness quán nhậu này mới chịu!'
      },
      {
        'mnv': '13075', 'name': 'NGÔ ĐÌNH MINH THÀNH', 'role': '😄 TỬU NHIỆT KHÔNG NGỪNG NGHỈ', 'img': '13075_NGÔ_ĐÌNH_MINH_THÀNH.jpeg', 'leader': False,
        'action': 'Lấy vạt áo lau mồ hôi trên trán cười toe toét, mắt vẫn sáng rực đầy năng lượng chiến đấu.',
        'thought': 'Nóng quá nhưng mà vui quá trời! Em vẫn còn tỉnh queo nha anh Long ơi, rót tiếp đi!'
      },
      {
        'mnv': 'GIAOLUU6A', 'name': 'GHẾ TIẾP TẾ CHIẾN TRƯỜNG', 'role': '🛡️ HỎA LỰC TIẾP VIỆN', 'img': '', 'leader': False,
        'action': 'Bê nguyên thùng bia ướp lạnh sang chi viện hỏa lực cho bàn 6.',
        'thought': 'Thấy bàn 6 sung sức quá nên mang thêm vũ khí bia mát lạnh sang chi viện!'
      },
      {
        'mnv': 'GIAOLUU6B', 'name': 'GHẾ TỔNG KẾT VÔ ĐỊCH', 'role': '🏆 ĐẠI DIỆN TRANH CUP', 'img': '', 'leader': False,
        'action': 'Cụng ly tổng kết bàn 6 giữ vững ngai vàng bất tử tửu lượng của công ty.',
        'thought': 'Bàn 6 chuẩn bị lên bục nhận giải Bàn Tiệc Vô Địch Đại Hội Bia MBC 2026!'
      }
    ]
  }
]

# Interactive pins definition for each slide:
slide_pins_data = {
  0: [
    { 'x': 51, 'y': 42, 'name': 'Sếp Bình (Chủ Tiệc)', 'img': '00043_TRAN_NGUYEN_BINH.jpeg', 'quote': 'Mừng tiệc BHCL, vui là chính, mình anh lo hết! 👑' },
    { 'x': 41, 'y': 49, 'name': 'TP Tân', 'img': '10091_NGUYỄN_THANH_TÂN.jpeg', 'quote': 'Giám đốc Bình nói vậy mời Giám đốc 1 ly! 🍻' },
    { 'x': 61, 'y': 46, 'name': 'Sếp Vũ (TP)', 'img': '10630_TRẦN_THẾ_VŨ.jpeg', 'quote': '1 - 2 - 3... ZÔ 100%! 🔥' },
    { 'x': 67, 'y': 66, 'name': 'GL Lâm', 'img': '10863_ĐỖ_TẤN_LÂM.jpeg', 'quote': 'Cụng ly nhiệt tình cùng các sếp!' },
    { 'x': 10, 'y': 60, 'name': 'Thái Bảo (Bàn 2)', 'img': '12953_PHAN_THANH_THÁI_BẢO.jpeg', 'quote': 'Mồi ngon hè... ôm trọn cái đùi gà! 🍗' },
    { 'x': 82, 'y': 64, 'name': 'Hội Bolero & Chị Em', 'img': '12690_TRÂN_TRUNG_HIÊU.jpeg', 'quote': 'Hát vang mừng tiệc BHCL! 🎤' }
  ],
  1: [
    { 'x': 50, 'y': 44, 'name': 'Sếp Bình (GĐ)', 'img': '00043_TRAN_NGUYEN_BINH.jpeg', 'quote': 'Vui là chính, mình anh lo hết 👑' },
    { 'x': 33, 'y': 46, 'name': 'TP Tân', 'img': '10091_NGUYỄN_THANH_TÂN.jpeg', 'quote': 'Giám đốc Bình nói vậy mời Giám đốc 1 ly! 🍻' },
    { 'x': 70, 'y': 30, 'name': 'Sếp Vũ (TP)', 'img': '10630_TRẦN_THẾ_VŨ.jpeg', 'quote': '1 - 2 - 3... ZÔ 100%! 🔥' },
    { 'x': 72, 'y': 52, 'name': 'Tấn Lâm', 'img': '10863_ĐỖ_TẤN_LÂM.jpeg', 'quote': 'Kéo nhóm 4 sang cụng ly nào!' },
    { 'x': 89, 'y': 50, 'name': 'Hà Giang', 'img': '10883_LÊ_KHẮC_HÀ_GIANG.jpeg', 'quote': 'Tiếp tế mồi bốc khói bắn tim! ❤️' },
    { 'x': 19, 'y': 52, 'name': 'Tấn Sỹ', 'img': '12333_NGUYỄN_TẤN_SỸ.jpeg', 'quote': 'Em mời các anh vài ly! 🍻' }
  ],
  2: [
    { 'x': 23, 'y': 46, 'name': 'Thái Bảo', 'img': '12953_PHAN_THANH_THÁI_BẢO.jpeg', 'quote': 'Mồi ngon hè... ôm trọn cái đùi gà! 🍗' },
    { 'x': 52, 'y': 44, 'name': 'Quang Thảo', 'img': '11466_NGUYỄN_QUANG_THẢO.jpeg', 'quote': 'Tối về ngứa kiếm ai gãi đây...? 🤔' },
    { 'x': 86, 'y': 46, 'name': 'Lê Cao Thanh', 'img': '13011_LÊ_CAO_THANH.jpeg', 'quote': 'Số hưởng rồi, lát bill em chịu nha Thảo! 🔮' },
    { 'x': 71, 'y': 48, 'name': 'Mai Thảo', 'img': '51727_MAI_THỊ_THANH_THẢO.jpeg', 'quote': 'Trời ơi thầy phán chuẩn dữ dội! 😱' },
    { 'x': 8, 'y': 40, 'name': 'Tấn Vũ', 'img': '11533_TRƯƠNG_TẤN_VŨ.jpeg', 'quote': 'Thầy bói Thanh bị bắt bao chầu chắc! 😂' },
    { 'x': 95, 'y': 40, 'name': 'Hồng Ánh', 'img': '49500_TRẦN_THỊ_HỒNG_ÁNH.jpeg', 'quote': 'Quay clip TikTok bao cười cả tuần! 📱' }
  ],
  3: [
    { 'x': 45, 'y': 30, 'name': 'Thục Phương', 'img': '20023_PHAN_THỤC_PHƯƠNG.jpeg', 'quote': 'Lên đồ rực rỡ, zô hết mình! 💃' },
    { 'x': 78, 'y': 46, 'name': 'Thanh Hương', 'img': '23169_HOÀNG_THỊ_THANH_HƯƠNG.jpeg', 'quote': '1, 2, 3 chu môi nào... 50 tấm ảnh! 📸' },
    { 'x': 62, 'y': 53, 'name': 'Thu Thủy (Bùi)', 'img': '20433_BÙI_THỊ_THU_THUỶ.jpeg', 'quote': 'Tạo dáng bông hoa nàng thơ! 🌸' },
    { 'x': 54, 'y': 53, 'name': 'Nguyễn Thị Tới', 'img': '20474_NGUYỄN_THỊ_TỚI.jpeg', 'quote': 'Mồi ngon không để sót miếng nào! 🍤' },
    { 'x': 31, 'y': 53, 'name': 'Thanh Thủy (Trần)', 'img': '45055_TRẦN_THỊ_THANH_THỦY.jpeg', 'quote': 'Tạo dáng chữ V, hoa khôi công ty! ✌️' },
    { 'x': 18, 'y': 56, 'name': 'Ánh Quang', 'img': '52795_TRƯƠNG_THỊ_ÁNH_QUANG.jpeg', 'quote': 'Cụng với sếp chúc thưởng Tết gấp 3! 🥂' }
  ],
  4: [
    { 'x': 34, 'y': 52, 'name': 'Thu Liễu', 'img': '20301_LÊ_THỊ_THU_LIỄU.jpeg', 'quote': 'Chi nhánh sữa chua 2 bán mấy trăm hộp nhỉ...? 🍦' },
    { 'x': 66, 'y': 38, 'name': 'Phước Huy', 'img': '12498_NGUYỄN_PHƯỚC_HUY.jpeg', 'quote': 'Bóc tôm mỏi tay đổi lại bia đầy tràn! 🦐' },
    { 'x': 45, 'y': 48, 'name': 'Kiều Oanh', 'img': '20122_NGUYỄN_THỊ_KIỀU_OANH.jpeg', 'quote': 'Vỗ tay thật to, không ngán ly nào! 👏' },
    { 'x': 56, 'y': 48, 'name': 'Hoàng Sau', 'img': '20709_HOÀNG_THỊ_SAU.jpeg', 'quote': 'Không bao giờ để bia long đền! 🍻' },
    { 'x': 85, 'y': 50, 'name': 'Mai Duyên', 'img': '23866_NGUYỄN_THỊ_MAI_DUYÊN.jpeg', 'quote': 'Dưa hấu mát lịm giải nhiệt tăng 3! 🍉' },
    { 'x': 94, 'y': 52, 'name': 'Nguyên Lộc', 'img': '34873_NGUYỄN_THỊ_NGUYÊN_LỘC.jpeg', 'quote': 'Đá viên mát lạnh đã cái nư! 🧊' }
  ],
  5: [
    { 'x': 49, 'y': 38, 'name': 'Trung Hiếu', 'img': '12690_TRÂN_TRUNG_HIÊU.jpeg', 'quote': 'Giọng ấm phiêu bolero cháy máy! 🎤' },
    { 'x': 68, 'y': 48, 'name': 'Hồng Việt', 'img': '11481_PHẠM_HỒNG_VIỆT.jpeg', 'quote': 'Nghệ thuật rót bia tỉ lệ 7:3! 🍺' },
    { 'x': 14, 'y': 56, 'name': 'Phương Thảo', 'img': '24040_VÕ_THỊ_PHƯƠNG_THẢO.jpeg', 'quote': 'Đệm guitar rộn ràng đại tiệc! 🎵' },
    { 'x': 34, 'y': 52, 'name': 'Tố Nguyên', 'img': '52401_HỒ_NGUYỄN_TỐ_NGUYÊN.jpeg', 'quote': 'Gõ đũa bát làm trống beat cháy! 🥁' },
    { 'x': 20, 'y': 38, 'name': 'Nguyễn Thị Hằng', 'img': '52270_NGUYỄN_THỊ_HẰNG.jpeg', 'quote': 'Vẫy khăn giấy múa phụ họa ca sĩ! 💃' },
    { 'x': 89, 'y': 48, 'name': 'Giao Lưu Bàn 5', 'img': '', 'quote': 'Nâng ly chúc mừng ban nhạc tiệc vui! 🍻' }
  ],
  6: [
    { 'x': 51, 'y': 38, 'name': 'Kim Thủy', 'img': '20434_TRẦN_THỊ_KIM_THỦY.jpeg', 'quote': 'Chấp hết các đấng mày râu! 👑' },
    { 'x': 68, 'y': 42, 'name': 'Trần Văn Long', 'img': '13038_TRẦN_VĂN_LONG.jpeg', 'quote': 'Không say không về! 🦾' },
    { 'x': 29, 'y': 58, 'name': 'Hồ Văn Thường', 'img': '13044_HỒ_VĂN_THƯỜNG.jpeg', 'quote': 'Kỷ lục Guinness 3 hàng vỏ chai! 🍾' },
    { 'x': 77, 'y': 58, 'name': 'Minh Thành', 'img': '13075_NGÔ_ĐÌNH_MINH_THÀNH.jpeg', 'quote': 'Vẫn còn tỉnh queo, rót tiếp đi! 😄' },
    { 'x': 16, 'y': 46, 'name': 'Tiếp Tế Hỏa Lực', 'img': '', 'quote': 'Chi viện thùng bia mát lạnh! 🛡️' },
    { 'x': 86, 'y': 38, 'name': 'Đại Diện Tranh Cúp', 'img': '', 'quote': 'Vô địch Đại Hội Bia MBC 2026! 🏆' }
  ]
}

def render_seat(seat):
    leader_cls = 'leader' if seat.get('leader') else ''
    img_html = ''
    if seat['img']:
        img_html = f'<div class="avatar-wrapper"><img src="extracted_faces/{seat["img"]}" alt="{seat["name"]}"></div>'
    else:
        img_html = '<div class="avatar-wrapper" style="display:flex;align-items:center;justify-content:center;font-size:2rem;background:#334155;">🍻</div>'

    return f'''
          <div class="seat-box {leader_cls}">
            {img_html}
            <div class="seat-name">{seat['name']}</div>
            <div class="seat-role">{seat['role']}</div>
            <div class="seat-action">{seat['action']}</div>
            <div class="thought-bubble">💭 <strong>Suy nghĩ:</strong> "{seat['thought']}"</div>
          </div>
    '''

def render_table(t):
    vip_cls = 'vip' if t.get('vip') else ''
    badge = '⭐ BÀN TRỌNG TÂM LÃNH ĐẠO' if t.get('vip') else 'BÀN VUÔNG 6 GHẾ'
    seats_html = '\n'.join([render_seat(s) for s in t['seats']])
    return f'''
      <div class="table-card {vip_cls}">
        <div class="table-header">
          <div class="table-title">{t['name']}</div>
          <span class="table-badge">{badge}</span>
        </div>
        <div class="seats-grid">
          {seats_html}
        </div>
      </div>
    '''

tables_html = '\n'.join([render_table(t) for t in tables_data])
tables_json = json.dumps(tables_data, ensure_ascii=False)
pins_json = json.dumps(slide_pins_data, ensure_ascii=False)

html_content = f'''<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🍻 ĐẠI TIỆC NHẬU MBC 2026 - SLIDE SHOW & SƠ ĐỒ 6 BÀN VUÔNG 🍻</title>
  <style>
    :root {{
      --primary: #f59e0b;
      --primary-dark: #b45309;
      --accent: #ef4444;
      --bg: #0f172a;
      --card-bg: rgba(30, 41, 59, 0.85);
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }}
    body {{
      background: radial-gradient(circle at top, #1e293b, #0f172a 80%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
    }}
    header {{
      padding: 16px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid rgba(245, 158, 11, 0.3);
      position: sticky;
      top: 0;
      z-index: 50;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 1.3rem;
      font-weight: 800;
      background: linear-gradient(135deg, #fbbf24, #f97316);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .nav-tabs {{
      display: flex;
      gap: 8px;
      background: rgba(30, 41, 59, 0.7);
      padding: 4px;
      border-radius: 12px;
      border: 1px solid rgba(255,255,255,0.08);
    }}
    .tab-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 8px 18px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .tab-btn.active, .tab-btn:hover {{
      background: var(--primary);
      color: #000;
      box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
    }}
    main {{
      flex: 1;
      max-width: 1400px;
      width: 100%;
      margin: 0 auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
    }}
    /* SLIDE SHOW */
    .slide-viewer {{
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 9;
      background: #000;
      border-radius: 20px;
      overflow: hidden;
      box-shadow: 0 20px 50px rgba(0,0,0,0.6), 0 0 30px rgba(245, 158, 11, 0.15);
      border: 2px solid rgba(245, 158, 11, 0.4);
    }}
    .slide-img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.5s ease;
    }}
    .slide-overlay {{
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: linear-gradient(to top, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.6) 60%, transparent 100%);
      padding: 30px 40px;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      z-index: 20;
      pointer-events: none;
    }}
    .slide-caption h2 {{
      font-size: 2rem;
      color: #fbbf24;
      text-shadow: 0 2px 10px rgba(0,0,0,0.8);
      margin-bottom: 6px;
    }}
    .slide-caption p {{
      font-size: 1.15rem;
      color: #f1f5f9;
      text-shadow: 0 1px 6px rgba(0,0,0,0.8);
      max-width: 900px;
      line-height: 1.4;
    }}
    .slide-controls {{
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      width: 100%;
      display: flex;
      justify-content: space-between;
      padding: 0 20px;
      pointer-events: none;
      z-index: 30;
    }}
    .ctrl-btn {{
      pointer-events: auto;
      width: 54px;
      height: 54px;
      border-radius: 50%;
      background: rgba(15, 23, 42, 0.75);
      border: 1px solid rgba(245, 158, 11, 0.5);
      color: #fff;
      font-size: 1.5rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      backdrop-filter: blur(8px);
      transition: all 0.2s;
    }}
    .ctrl-btn:hover {{
      background: var(--primary);
      color: #000;
      transform: scale(1.1);
    }}

    /* PINS LAYER ON SLIDE */
    .pins-layer {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 25;
      transition: opacity 0.3s;
    }}
    .pin-badge {{
      position: absolute;
      transform: translate(-50%, -100%);
      pointer-events: auto;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
    }}
    .pin-badge:hover {{
      transform: translate(-50%, -110%) scale(1.15);
      z-index: 40;
    }}
    .pin-avatar {{
      width: 54px;
      height: 54px;
      border-radius: 50%;
      border: 2.5px solid #fbbf24;
      box-shadow: 0 4px 15px rgba(0,0,0,0.8), 0 0 12px rgba(251, 191, 36, 0.6);
      object-fit: cover;
      background: #1e293b;
      margin-bottom: 4px;
    }}
    .pin-bubble {{
      background: rgba(15, 23, 42, 0.92);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(251, 191, 36, 0.6);
      border-radius: 12px;
      padding: 6px 12px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.6);
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      white-space: nowrap;
    }}
    .pin-name {{
      font-weight: 800;
      color: #fbbf24;
      font-size: 0.82rem;
    }}
    .pin-quote {{
      color: #f1f5f9;
      font-size: 0.75rem;
      max-width: 170px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}

    /* TOGGLE PINS BUTTON */
    .pin-toggle-btn {{
      position: absolute;
      top: 18px;
      right: 18px;
      z-index: 35;
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(245, 158, 11, 0.6);
      color: #fbbf24;
      padding: 8px 16px;
      border-radius: 20px;
      font-weight: 700;
      font-size: 0.85rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }}
    .pin-toggle-btn:hover {{
      background: var(--primary);
      color: #000;
      transform: scale(1.05);
    }}

    /* THUMBNAILS */
    .thumbnails {{
      display: flex;
      gap: 12px;
      margin-top: 16px;
      overflow-x: auto;
      padding: 8px 4px;
    }}
    .thumb {{
      flex: 0 0 140px;
      aspect-ratio: 16 / 9;
      border-radius: 10px;
      overflow: hidden;
      cursor: pointer;
      border: 2px solid transparent;
      opacity: 0.6;
      transition: all 0.2s;
    }}
    .thumb img {{ width: 100%; height: 100%; object-fit: cover; }}
    .thumb.active, .thumb:hover {{
      opacity: 1;
      border-color: var(--primary);
      transform: translateY(-2px);
    }}

    /* INTERACTIVE PEOPLE & THOUGHTS DECK */
    .slide-deck-container {{
      margin-top: 24px;
      background: var(--card-bg);
      border-radius: 20px;
      padding: 24px;
      border: 1px solid rgba(245, 158, 11, 0.3);
      backdrop-filter: blur(12px);
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .deck-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }}
    .deck-title {{
      font-size: 1.35rem;
      font-weight: 800;
      color: #fbbf24;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .deck-hint {{
      font-size: 0.85rem;
      color: var(--text-muted);
    }}
    .deck-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 18px;
    }}
    .deck-card {{
      background: rgba(15, 23, 42, 0.85);
      border-radius: 16px;
      padding: 16px;
      border: 1px solid rgba(255,255,255,0.08);
      display: flex;
      gap: 16px;
      transition: all 0.25s;
    }}
    .deck-card:hover {{
      transform: translateY(-4px);
      border-color: #fbbf24;
      box-shadow: 0 10px 25px rgba(245, 158, 11, 0.2);
    }}
    .deck-card.leader {{
      border: 1.5px solid rgba(251, 191, 36, 0.5);
      background: linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(70, 36, 12, 0.4));
    }}
    .deck-avatar-box {{
      width: 76px;
      height: 76px;
      border-radius: 50%;
      border: 2.5px solid #fbbf24;
      overflow: hidden;
      flex-shrink: 0;
      box-shadow: 0 4px 14px rgba(0,0,0,0.6);
      background: #1e293b;
    }}
    .deck-avatar-box img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
    }}
    .deck-content {{
      display: flex;
      flex-direction: column;
      gap: 5px;
      flex: 1;
    }}
    .deck-name {{
      font-size: 1.05rem;
      font-weight: 800;
      color: #fbbf24;
    }}
    .deck-role {{
      font-size: 0.75rem;
      font-weight: 700;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .deck-action {{
      font-size: 0.85rem;
      color: #cbd5e1;
      line-height: 1.35;
    }}
    .deck-thought {{
      background: rgba(245, 158, 11, 0.12);
      border-left: 3px solid #fbbf24;
      padding: 8px 12px;
      border-radius: 0 8px 8px 0;
      font-size: 0.85rem;
      color: #fef08a;
      font-style: italic;
      line-height: 1.35;
      margin-top: 4px;
    }}

    /* TABLES VIEW */
    .tables-view {{
      display: none;
      flex-direction: column;
      gap: 32px;
    }}
    .table-card {{
      background: var(--card-bg);
      border-radius: 18px;
      padding: 24px;
      border: 1px solid rgba(245, 158, 11, 0.25);
      backdrop-filter: blur(10px);
    }}
    .table-card.vip {{
      border: 2px solid #fbbf24;
      background: linear-gradient(145deg, rgba(30, 41, 59, 0.95), rgba(70, 36, 12, 0.85));
      box-shadow: 0 12px 35px rgba(251, 191, 36, 0.18);
    }}
    .table-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      border-bottom: 1px solid rgba(255,255,255,0.12);
      padding-bottom: 12px;
    }}
    .table-title {{
      font-size: 1.35rem;
      font-weight: 800;
      color: #fbbf24;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .table-badge {{
      background: rgba(245, 158, 11, 0.2);
      border: 1px solid #fbbf24;
      color: #fbbf24;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.8rem;
      font-weight: 700;
      letter-spacing: 0.5px;
    }}
    .seats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 16px;
    }}
    .seat-box {{
      background: rgba(15, 23, 42, 0.85);
      border-radius: 14px;
      padding: 14px;
      border: 1px solid rgba(255,255,255,0.08);
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      transition: all 0.25s;
    }}
    .seat-box:hover {{
      transform: translateY(-4px);
      border-color: var(--primary);
      box-shadow: 0 10px 24px rgba(0,0,0,0.5);
    }}
    .seat-box.leader {{
      border: 1px solid rgba(245, 158, 11, 0.6);
      background: linear-gradient(to bottom, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95));
    }}
    .avatar-wrapper {{
      width: 80px;
      height: 80px;
      border-radius: 50%;
      overflow: hidden;
      margin-bottom: 12px;
      border: 2px solid var(--primary);
      box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }}
    .avatar-wrapper img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
    }}
    .seat-name {{
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 4px;
    }}
    .seat-role {{
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--primary);
      text-transform: uppercase;
      margin-bottom: 10px;
    }}
    .seat-action {{
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-bottom: 10px;
      line-height: 1.35;
      text-align: left;
      width: 100%;
    }}
    .thought-bubble {{
      background: rgba(245, 158, 11, 0.15);
      border-left: 3px solid var(--primary);
      padding: 8px 10px;
      border-radius: 0 8px 8px 0;
      font-size: 0.8rem;
      color: #fef08a;
      font-style: italic;
      line-height: 1.35;
      text-align: left;
      width: 100%;
      margin-top: auto;
    }}
    .cheer-btn {{
      background: linear-gradient(135deg, #f59e0b, #ea580c);
      color: #000;
      border: none;
      font-weight: 800;
      font-size: 1rem;
      padding: 10px 24px;
      border-radius: 30px;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
      transition: all 0.2s;
    }}
    .cheer-btn:hover {{
      transform: scale(1.05);
      box-shadow: 0 6px 20px rgba(245, 158, 11, 0.6);
    }}
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <span>🍻</span>
      <span>ĐẠI TIỆC NHẬU MBC 2026</span>
    </div>
    <div class="nav-tabs">
      <button class="tab-btn active" onclick="switchView('slides')">🎬 Trình Chiếu Slides</button>
      <button class="tab-btn" onclick="switchView('tables')">🪑 Sơ Đồ 6 Bàn Vuông (33 Nhân Sự)</button>
    </div>
    <button class="cheer-btn" onclick="cheerSound()">🍻 1-2-3 ZÔ!</button>
  </header>

  <main>
    <!-- VIEW 1: SLIDES -->
    <div id="slidesView">
      <div class="slide-viewer">
        <img id="currentSlideImg" class="slide-img" src="generated_scenes/phong_tiec_toan_canh_5_ban.jpg" alt="Slide">
        
        <!-- Interactive On-Image Face Pins -->
        <div id="pinsLayer" class="pins-layer"></div>

        <!-- Toggle Pins Button -->
        <button class="pin-toggle-btn" onclick="togglePins()">
          <span id="pinToggleIcon">🏷️</span> <span id="pinToggleText">Ẩn Ghim Mặt & Lời Thoại</span>
        </button>

        <div class="slide-overlay">
          <div class="slide-caption">
            <h2 id="slideTitle">🏛️ PHÒNG NHẬU TOÀN CẢNH 5 BÀN LIÊN HOÀN 🎉</h2>
            <p id="slideDesc">Bức tranh toàn cảnh không gian phòng tiệc đại tiệc công ty MBC 2026 với 5 bàn vuông liên hoàn trong cùng một khán phòng: Bàn VIP lãnh đạo ở trung tâm, Bàn thực thần đùi gà & thầy bói, Bàn hội chị em selfie, Bàn sữa chua & bóc tôm, Bàn ban nhạc bolero & rót bia bọt tuyết!</p>
          </div>
        </div>
        <div class="slide-controls">
          <button class="ctrl-btn" onclick="prevSlide()">❮</button>
          <button class="ctrl-btn" onclick="nextSlide()">❯</button>
        </div>
      </div>

      <div class="thumbnails" id="thumbsContainer"></div>

      <!-- INTERACTIVE ACTIVE TABLE MEMBERS & THOUGHTS -->
      <div class="slide-deck-container">
        <div class="deck-header">
          <div class="deck-title" id="deckTitle">
            👑 THÀNH VIÊN BÀN TIỆC & SUY NGHĨ HÓM HỈNH
          </div>
          <div class="deck-hint">
            💡 Mỗi thành viên đều có hành động và suy nghĩ độc đáo ứng với nhân vật trên bàn!
          </div>
        </div>
        <div class="deck-grid" id="deckGrid">
          <!-- Populated per slide -->
        </div>
      </div>
    </div>

    <!-- VIEW 2: 6 TABLES LAYOUT -->
    <div id="tablesView" class="tables-view">
      {tables_html}
    </div>
  </main>

  <script>
    const tablesData = {tables_json};
    const slidePinsData = {pins_json};

    const slides = [
      {{
        src: 'generated_scenes/phong_tiec_toan_canh_5_ban.jpg',
        title: '🏛️ PHÒNG NHẬU TOÀN CẢNH 5 BÀN LIÊN HOÀN 🎉',
        desc: 'Bức tranh toàn cảnh không gian phòng tiệc đại tiệc công ty MBC 2026 với 5 bàn vuông liên hoàn trong cùng một khán phòng: Bàn VIP lãnh đạo ở trung tâm, Bàn thực thần đùi gà & thầy bói, Bàn hội chị em selfie, Bàn sữa chua & bóc tôm, Bàn ban nhạc bolero & rót bia bọt tuyết!'
      }},
      {{
        src: 'generated_scenes/slide_ban1_vip.jpg',
        title: '1. BÀN VIP LÃNH ĐẠO & TẤN SỸ QUA MỜI SẾP 👑',
        desc: 'Giám đốc Bình nâng ly khai tiệc "Công ty bao trọn gói", Trưởng phòng Vũ đứng hô "1-2-3 Zô", TP Tân kính cẩn dâng vại bia to bự, và Tấn Sỹ hiên ngang sang chúc 3 sếp 100%!'
      }},
      {{
        src: 'generated_scenes/slide_ban2_thucthan.jpg',
        title: '2. THỰC THẦN ĐÙI GÀ & THẦY BÓI TIỆC NHẬU 🍗🔮',
        desc: 'Thái Bảo mắt trái tim ôm đùi gà "Mồi ngon hè", Thầy Thanh phán chỉ tay bắt Mai Thảo bao chầu bia, Quang Thảo băn khoăn "Tối về ngứa kiếm ai gãi đây?", cùng Tấn Vũ cười vỡ bụng và Hồng Ánh quay clip TikTok!'
      }},
      {{
        src: 'generated_scenes/slide_ban3_chiem.jpg',
        title: '3. NHÓM 1 - HỘI CHỊ EM RẠNG RỠ & SELFIE SỐNG ẢO 💃🥂',
        desc: 'Dàn người đẹp rạng rỡ tỏa sáng, tạo dáng bông hoa, chọn mồi ngon và chụp ảnh selfie 45 độ lưu giữ khoảnh khắc thanh xuân rực rỡ.'
      }},
      {{
        src: 'generated_scenes/slide_ban4_suachua.jpg',
        title: '4. NỮ DOANH NHÂN SỮA CHUA & ANH CHÀNG BÓC TÔM 🍨🦐',
        desc: 'Thu Liễu vừa gắp mực vừa suy tư doanh thu chi nhánh sữa chua thứ 2, Phước Huy mồ hôi nhễ nhại bóc tôm phục vụ chị em, Hoàng Sau cụng ly không long đền!'
      }},
      {{
        src: 'generated_scenes/slide_ban5_bolero.jpg',
        title: '5. BAN NHẠC BOLERO & TUYỆT ĐỈNH RÓT BIA 🎤🍺',
        desc: 'Ca sĩ Hiếu phiêu bolero nốt cao cháy máy, fan cuồng múa khăn giấy, Tố Nguyên gõ đũa bát làm trống và Hồng Việt rót bia bọt tuyết 7 phần bia 3 phần bọt!'
      }},
      {{
        src: 'generated_scenes/slide_ban6_battu.jpg',
        title: '6. BIỆT ĐỘI BẤT TỬ 100% & KỶ LỤC GIA ĐẾM VỎ CHAI 🦾🍾',
        desc: 'Nữ tướng Kim Thủy một mình chấp hết bàn tiệc, anh Long giơ nắm đấm quyết tâm, anh Thường đếm 3 hàng vỏ chai chuẩn bị lập kỷ lục Guinness!'
      }}
    ];

    let currentIdx = 0;
    let pinsVisible = true;

    function togglePins() {{
      pinsVisible = !pinsVisible;
      const layer = document.getElementById('pinsLayer');
      layer.style.opacity = pinsVisible ? '1' : '0';
      layer.style.pointerEvents = pinsVisible ? 'auto' : 'none';
      document.getElementById('pinToggleText').textContent = pinsVisible ? 'Ẩn Ghim Mặt & Lời Thoại' : 'Hiện Ghim Mặt & Lời Thoại';
    }}

    function renderPins(idx) {{
      const layer = document.getElementById('pinsLayer');
      const pins = slidePinsData[idx] || [];
      layer.innerHTML = pins.map(p => {{
        const avatarHtml = p.img 
          ? `<img src="extracted_faces/${{p.img}}" class="pin-avatar" alt="${{p.name}}">`
          : `<div class="pin-avatar" style="display:flex;align-items:center;justify-content:center;font-size:1.5rem;">🍻</div>`;
        return `
          <div class="pin-badge" style="left: ${{p.x}}%; top: ${{p.y}}%;" onclick="highlightCard('${{p.name}}')">
            ${{avatarHtml}}
            <div class="pin-bubble">
              <span class="pin-name">${{p.name}}</span>
              <span class="pin-quote">${{p.quote}}</span>
            </div>
          </div>
        `;
      }}).join('');
    }}

    function highlightCard(name) {{
      const cards = document.querySelectorAll('.deck-card');
      cards.forEach(c => {{
        if (c.dataset.name && name.includes(c.dataset.name)) {{
          c.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
          c.style.borderColor = '#ef4444';
          c.style.transform = 'scale(1.05)';
          setTimeout(() => {{
            c.style.borderColor = '';
            c.style.transform = '';
          }}, 1800);
        }}
      }});
    }}

    function renderDeck(idx) {{
      const titleEl = document.getElementById('deckTitle');
      const gridEl = document.getElementById('deckGrid');

      if (idx === 0) {{
        titleEl.innerHTML = '🏛️ CÁC BÀN TIỆC TIÊU BIỂU TRONG PHÒNG NHẬU 5 BÀN';
        const highlights = [
          {{ table: '⭐ BÀN 1: VIP LÃNH ĐẠO', name: 'TRẦN NGUYÊN BÌNH', role: '👑 GIÁM ĐỐC', img: '00043_TRAN_NGUYEN_BINH.jpeg', thought: 'Hôm nay anh em vui là chính, hóa đơn cứ để đấy công ty lo, miễn mai đi làm đúng giờ là được!' }},
          {{ table: '🍗 BÀN 2: THỰC THẦN', name: 'PHAN THANH THÁI BẢO', role: '🍗 TÍN ĐỒ ĐÙI GÀ', img: '12953_PHAN_THANH_THÁI_BẢO.jpeg', thought: 'Mồi ngon hè... Mấy ông cứ tranh nhau uống đi, một mình tôi ôm trọn cái đùi gà này là ấm bụng nhất trần đời!' }},
          {{ table: '💃 BÀN 3: HỘI CHỊ EM', name: 'HOÀNG THỊ THANH HƯƠNG', role: '📸 NHIẾP ẢNH GIA', img: '23169_HOÀNG_THỊ_THANH_HƯƠNG.jpeg', thought: 'Chụp 50 tấm chắc chọn được 1 tấm đẹp nhất đăng Facebook câu ngàn like cho coi!' }},
          {{ table: '🍨 BÀN 4: SỮA CHUA', name: 'LÊ THỊ THU LIỄU', role: '🍨 NỮ DOANH NHÂN', img: '20301_LÊ_THỊ_THU_LIỄU.jpeg', thought: 'Không biết chi nhánh sữa chua thứ 2 của mình hôm nay bán được mấy trăm hộp nhỉ, tí phải mở app xem mới yên tâm!' }},
          {{ table: '🎤 BÀN 5: BOLERO', name: 'TRẦN TRUNG HIẾU', role: '🎤 CA SĨ BOLERO', img: '12690_TRÂN_TRUNG_HIÊU.jpeg', thought: 'Đam mê ca hát cháy bỏng từ nhỏ, hôm nay có bia vào giọng mình ấm như ca sĩ Đan Trường vậy!' }}
        ];
        gridEl.innerHTML = highlights.map(h => `
          <div class="deck-card leader" data-name="${{h.name}}">
            <div class="deck-avatar-box">
              <img src="extracted_faces/${{h.img}}" alt="${{h.name}}">
            </div>
            <div class="deck-content">
              <div class="deck-role" style="color:#fbbf24;">${{h.table}}</div>
              <div class="deck-name">${{h.name}} <span style="font-size:0.8rem;color:#cbd5e1;">(${{h.role}})</span></div>
              <div class="deck-thought">💭 <strong>Suy nghĩ:</strong> "${{h.thought}}"</div>
            </div>
          </div>
        `).join('');
      }} else {{
        const table = tablesData[idx - 1];
        if (table) {{
          titleEl.innerHTML = `🪑 ${{table.name}} — NHÂN SỰ & SUY NGHĨ ĐẶC SẮC`;
          gridEl.innerHTML = table.seats.map(s => {{
            const avatarHtml = s.img 
              ? `<img src="extracted_faces/${{s.img}}" alt="${{s.name}}">`
              : `<div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:2rem;">🍻</div>`;
            const leaderClass = s.leader ? 'leader' : '';
            return `
              <div class="deck-card ${{leaderClass}}" data-name="${{s.name}}">
                <div class="deck-avatar-box">
                  ${{avatarHtml}}
                </div>
                <div class="deck-content">
                  <div class="deck-name">${{s.name}}</div>
                  <div class="deck-role">${{s.role}}</div>
                  <div class="deck-action">🎭 <strong>Hành động:</strong> ${{s.action}}</div>
                  <div class="deck-thought">💭 <strong>Suy nghĩ:</strong> "${{s.thought}}"</div>
                </div>
              </div>
            `;
          }}).join('');
        }}
      }}
    }}

    function renderThumbs() {{
      const container = document.getElementById('thumbsContainer');
      container.innerHTML = slides.map((s, i) => `
        <div class="thumb ${{i === currentIdx ? 'active' : ''}}" onclick="goToSlide(${{i}})">
          <img src="${{s.src}}" alt="${{s.title}}">
        </div>
      `).join('');
    }}

    function showSlide(idx) {{
      currentIdx = (idx + slides.length) % slides.length;
      const s = slides[currentIdx];
      document.getElementById('currentSlideImg').src = s.src;
      document.getElementById('slideTitle').textContent = s.title;
      document.getElementById('slideDesc').textContent = s.desc;
      renderThumbs();
      renderPins(currentIdx);
      renderDeck(currentIdx);
    }}

    function nextSlide() {{ showSlide(currentIdx + 1); }}
    function prevSlide() {{ showSlide(currentIdx - 1); }}
    function goToSlide(i) {{ showSlide(i); }}

    function switchView(mode) {{
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      if (mode === 'slides') {{
        document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
        document.getElementById('slidesView').style.display = 'block';
        document.getElementById('tablesView').style.display = 'none';
      }} else {{
        document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
        document.getElementById('slidesView').style.display = 'none';
        document.getElementById('tablesView').style.display = 'flex';
      }}
    }}

    window.addEventListener('keydown', (e) => {{
      if (e.key === 'ArrowRight' || e.key === 'Space') nextSlide();
      if (e.key === 'ArrowLeft') prevSlide();
    }});

    function cheerSound() {{
      try {{
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(2400, now);
        osc.frequency.exponentialRampToValueAtTime(800, now + 0.3);
        gain.gain.setValueAtTime(0.3, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.5);
        alert('🍻 1 - 2 - 3... ZÔ 100%!!! CHÚC BAN LÃNH ĐẠO VÀ ANH EM VUI VẺ!');
      }} catch (e) {{
        alert('🍻 1 - 2 - 3... ZÔ 100%!!!');
      }}
    }}

    // Init
    showSlide(0);
  </script>
</body>
</html>
'''

with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"SUCCESS: Generated {html_file} with interactive pins, real face avatars, and active employee thoughts deck!")
