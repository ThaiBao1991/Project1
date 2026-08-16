# -*- coding: utf-8 -*-
"""
Generator: Thiên Công Khai Vật & Tái Thiết Văn Minh từ Số 0 (Reboot Civilization Tech Tree)
Lộ trình từ Sinh tồn Chiến tranh/Đồ đá đến Tự chủ chế tạo Máy tính & Chip bán dẫn từ cát.
Tuân thủ nghiêm ngặt SKILL.md: Cấu trúc 15-day cycle chuẩn, Prompt/Bài tập/Tags, Không tương tác, UTF-8.
"""

import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOPICS = []

def add(phase_num, phase_name, tag, title, note=""):
    TOPICS.append((phase_num, phase_name, tag, title, note))

# ============ PHASE 1: SINH TỒN CHIẾN TRANH & BẢO TỒN TRI THỨC ============
P = "Sinh Tồn Chiến Tranh & Bảo Tồn Tri Thức"; T = "sinhton_chientranh"
add(1, P, T, "Trú ẩn thảm họa & Gia cố hầm dã chiến: từ hầm trú bom, chống sập đến thông gió và che chắn bức xạ/bụi độc")
add(1, P, T, "Nước sạch khẩn cấp & Sơ cứu dã chiến: lọc lắng than cát tức thì, khử khuẩn nhiệt/hóa học và cầm máu khâu vết thương")
add(1, P, T, "Bảo tồn & Truyền thừa tri thức văn minh: lập thư viện khắc kim loại, vi phim (microfilm) và quy tắc lưu trữ chống thoái hóa")

# ============ PHASE 2: KỶ NGUYÊN ĐỒ ĐÁ & SINH TỒN NGUYÊN THỦY ============
P = "Kỷ Nguyên Đồ Đá & Sinh Tồn Nguyên Thủy"; T = "doda_nguyenthuy"
add(2, P, T, "Kỹ thuật tạo lửa nguyên thủy: từ cọ xát ma sát (bow drill, hand drill) đến đá lửa (flint & pyrite) và bùi nhùi giữ lửa")
add(2, P, T, "Chế tác công cụ đá đẽo & đá mài: ghè đá lửa (flintknapping), rìu đá mài tra cán gỗ và mũi lao/mũi tên đá")
add(2, P, T, "Vật liệu tự nhiên: bện dây thừng từ vỏ cây/gân thú, thuộc da thảo mộc và dựng lán trại chống chọi thời tiết")

# ============ PHASE 3: ĐỊNH CƯ, ĐỒ GỐM & NÔNG NGHIỆP TỰ CUNG ============
P = "Định Cư, Đồ Gốm & Nông Nghiệp Tự Cung"; T = "gom_nongnghiep"
add(3, P, T, "Làm gốm đất sét & Xây lò nung chịu nhiệt: từ nặn tay, bàn xoay đến lò gốm lửa nghịch đạt 1000 độ C")
add(3, P, T, "Trồng trọt & Canh tác lúa giống: tuyển chọn hạt giống, cải tạo đất, tưới tiêu và bảo vệ mùa màng")
add(3, P, T, "Khai thác muối biển & Bảo quản lương thực: cô đặc nước muối biển, ủ men, phơi khô và hun khói dự trữ dài hạn")

# ============ PHASE 4: THỜI KỲ KIM KHÍ (ĐỒ ĐỒNG & ĐỒ SẮT) ============
P = "Thời Kỳ Kim Khí (Đồng & Sắt)"; T = "luyenkim_dong_sat"
add(4, P, T, "Luyện đồng & Hợp kim đồng: từ quặng Malachite nung than củi đến đúc đồng thau/đồng thiếc (Bronze/Brass)")
add(4, P, T, "Luyện sắt sơ cấp (Lò Bloomery): nung quặng sắt với than củi, tạo sắt xốp (bloom) và đập rèn tách xỉ")
add(4, P, T, "Nghề rèn & Nhiệt luyện thép carbon: búa, đe, kìm rèn; quy trình trui tôi và ram thép để tạo lưỡi cắt sắc bén")

# ============ PHASE 5: HÓA CHẤT NỀN TẢNG, GIẤY & IN ẤN ============
P = "Hóa Chất Nền Tảng, Giấy & In Ấn"; T = "hoachat_giay_inan"
add(5, P, T, "Axit Sulfuric & Kiềm công nghiệp: sản xuất axit sulfuric từ quặng pyrit và xút (NaOH/KOH) từ tro than củi và vôi sống")
add(5, P, T, "Xà phòng, Cồn y tế & Keo dán: xà phòng hóa từ mỡ động vật/dầu thực vật, chưng cất cồn ethanol sát trùng và keo xương")
add(5, P, T, "Làm giấy rơm rạ/vỏ cây & In ấn khắc bản: nghiền bột giấy, xeo giấy khung tre và khắc ván gỗ in sách hàng loạt")

# ============ PHASE 6: ĐO LƯỜNG CHUẨN XÁC & CƠ KHÍ ĐỘNG LỰC ============
P = "Đo Lường Chuẩn Xác & Cơ Khí Động Lực"; T = "doluong_cokhi_hoinuoc"
add(6, P, T, "Chuẩn đo lường & Phương pháp 3 tấm mài phẳng: tạo mặt phẳng tuyệt đối (Whitworth 3-surface plate) và thước kẹp chính xác")
add(6, P, T, "Tiện ren ốc chuẩn xác & Máy công cụ sơ khai: máy tiện chân đạp, gia công trục vít dẫn và bánh răng cơ khí")
add(6, P, T, "Động cơ hơi nước & Nồi hơi áp suất cao: từ nguyên lý cỗ máy Newcomen đến động cơ hơi nước Watt có van điều tốc")

# ============ PHASE 7: KỶ NGUYÊN ĐIỆN TỪ HỌC & NĂNG LƯỢNG ============
P = "Kỷ Nguyên Điện Từ Học & Năng Lượng"; T = "dientu_nangluong"
add(7, P, T, "Pin hóa học & Kéo dây đồng bọc men: chế tạo pin ướt Volta/Daniell và kéo dây đồng bọc sơn cách điện")
add(7, P, T, "Máy phát điện Dynamo & Động cơ điện: nguyên lý cảm ứng điện từ Faraday, quấn rotor/stator và chỉnh lưu dòng điện")
add(7, P, T, "Điện báo Morse & Hệ thống truyền dẫn tín hiệu: rơ-le điện từ (Relay), đường truyền dây dẫn và mã hóa tín hiệu")

# ============ PHASE 8: KỸ THUẬT CHÂN KHÔNG & CỔNG LOGIC SƠ KHAI ============
P = "Kỹ Thuật Chân Không & Cổng Logic Sơ Khai"; T = "chankhong_logic_relay"
add(8, P, T, "Bơm hút chân không & Thổi bóng thủy tinh: chế tạo bơm chân không cơ khí và thổi bóng đèn thủy tinh hàn kín")
add(8, P, T, "Đèn điện tử 3 cực (Triode / Vacuum Tube): cực catot phát xạ nhiệt, lưới điều khiển và cực anot khuếch đại tín hiệu")
add(8, P, T, "Cổng Logic cơ bản bằng Relay & Đèn chân không: thiết kế mạch AND, OR, NOT, NAND, NOR không dùng vi mạch")

# ============ PHASE 9: TINH CHẾ SILIC & CÔNG NGHỆ BÁN DẪN ============
P = "Tinh Chế Silic & Công Nghệ Bán Dẫn"; T = "bandan_silic_wafer"
add(9, P, T, "Tinh chế Silic từ cát thạch anh: khử SiO2 thành Silicon luyện kim (MG-Si) đến Silic đa tinh thể siêu tinh khiết (EGS 9N)")
add(9, P, T, "Kéo đơn tinh thể (Czochralski) & Cắt lát Wafer: nung chảy Silic đơn tinh thể, kéo thỏi ingot và cắt mài lát wafer bóng gương")
add(9, P, T, "Quang khắc (Photolithography) & Chế tạo Transistor MOSFET: keo cản quang, mặt nạ tia UV, pha tạp (doping) và phủ kim loại tiếp xúc")

# ============ PHASE 10: CHẾ TẠO MÁY TÍNH & KHÔI PHỤC VĂN MINH ============
P = "Chế Tạo Máy Tính & Khôi Phục Văn Minh"; T = "maytinh_cpu_capstone"
add(10, P, T, "Thiết kế Bộ số học ALU & Mạch đếm Clock: ghép cổng logic thành bộ cộng 4-bit/8-bit và dao động thạch anh")
add(10, P, T, "Thiết kế Bộ nhớ RAM/ROM & Thanh ghi (Register): ma trận diode ROM, mạch chốt Flip-Flop và giải mã địa chỉ nhớ")
add(10, P, T, "Lắp ráp CPU 8-bit hoàn chỉnh & Nạp Machine Code: kiến trúc Bus dữ liệu, vi lệnh Control Logic và chạy chương trình máy tính đầu tiên")
add(10, P, T, "Capstone Tổng kết: Chuỗi cung ứng khép kín tái thiết văn minh từ Đồ đá đến Máy tính")

TOTAL_TOPICS = len(TOPICS)
TOTAL_DAYS = TOTAL_TOPICS * 15

# ============ 15-DAY MASTERY CYCLE ============
DAY_FOCUS = [
    ("Core Concept", "Tổng quan về chủ đề, bối cảnh lịch sử, nguyên liệu tối thiểu cần có và sơ đồ dòng chảy quy trình từ thô sơ đến hoàn thiện.", False),
    ("Kỹ Thuật Sơ Khai", "Kỹ thuật thủ công nền tảng nhất, các bước thao tác thực tế từng bước một với dụng cụ thô sơ có sẵn trong tự nhiên.", False),
    ("Deep Dive Khoa Học & Vật Liệu", "Giải thích bản chất khoa học bên dưới (phản ứng hóa học, cơ tính vật liệu, nhiệt động lực học, vật lý bán dẫn).", False),
    ("Kỹ Thuật Nâng Cao & Tinh Chế", "Các kỹ thuật gia truyền hoặc tối ưu nâng cao để đạt độ tinh khiết, độ cứng, hoặc hiệu suất cao hơn.", False),
    ("Xử Lý Sự Cố & An Toàn", "Các lỗi nguy hiểm thường gặp, nguyên nhân thất bại trong quá trình chế tạo và biện pháp an toàn/khắc phục.", True),
    ("Đo Lường & Kiểm Soát Chất Lượng", "Phương pháp tự kiểm tra chất lượng sản phẩm đầu ra (đo nhiệt độ, đo độ phẳng, kiểm tra độ tinh khiết, đo thông mạch).", True),
    ("Chế Tạo Công Cụ Phụ Trợ", "Cách tự chế tạo các đồ gá, khuôn đúc, dụng cụ kẹp hoặc thiết bị hỗ trợ cho bước chế tạo tiếp theo.", False),
    ("Tối Ưu Hiệu Suất & Tiết Kiệm Năng Lượng", "Cách tối ưu hóa nguyên liệu, tuần hoàn nhiệt năng/khí thải để giảm hao phí khi tài nguyên khan hiếm.", False),
    ("Mở Rộng Quy Mô & Chuỗi Cung Ứng", "Cách liên kết quy trình này với các ngành nghề xung quanh, tính toán nhân lực và nguồn cung nguyên liệu ổn định.", False),
    ("Lịch Sử Tiến Hóa Công Nghiệp", "Lịch sử các phát minh bước ngoặt của nhân loại trong lĩnh vực này và bài học rút ra cho quá trình tái thiết.", False),
    ("Quy Trình Công Nghiệp Tiên Tiến", "Đối chiếu với dây chuyền công nghiệp hiện đại tương ứng, nguyên lý hoạt động của máy móc tương lai cần vươn tới.", False),
    ("Tự Làm Lại Từ Đầu (From Scratch)", "Hướng dẫn thực chiến từng bước tự làm lại toàn bộ sản phẩm hoàn chỉnh từ con số 0 trong điều kiện mất hết văn minh.", False),
    ("Mini-Project: Thiết Kế & Chuẩn Bị", "Lên bản vẽ thiết kế, danh mục vật liệu và quy trình chế tạo cho dự án thực hành hoàn chỉnh của chủ đề này.", False),
    ("Mini-Project: Triển Khai Chế Tạo", "Các bước gia công, lắp ráp, xử lý nhiệt/hóa học/mạch điện của sản phẩm mini-project.", False),
    ("Mini-Project: Nghiệm Thu & Tích Hợp Tech-Tree", "Nghiệm thu sản phẩm, kiểm tra độ bền/chức năng và kết nối sản phẩm này làm công cụ đầu vào cho giai đoạn tiếp theo.", False),
]

NON_INTERACTIVE_NOTE = (
    "(⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. "
    "HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu.)"
)

def generate_roadmap(output_path=None):
    if not output_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(base_dir, "roadmap_thien_cong_khai_vat.md")

    out = []
    out.append(f"# Thiên Công Khai Vật & Tái Thiết Văn Minh từ Số 0 — Lộ Trình {TOTAL_DAYS} Ngày\n")
    out.append("> **Mục tiêu tối thượng**: Xây dựng cây công nghệ (Tech Tree) toàn diện để tái thiết nền văn minh nhân loại từ con số 0 sau thảm họa/chiến tranh, tiến hóa tuần tự qua 10 kỷ nguyên công nghệ: từ sinh tồn khẩn cấp, thời kỳ đồ đá, đồ gốm, đồ đồng, đồ sắt, hóa chất cơ bản, cơ khí chính xác/hơi nước, điện từ học, đèn chân không, công nghệ bán dẫn đến chế tạo hoàn chỉnh máy tính và CPU 8-bit từ cát.\n")
    out.append(f"> **Thời lượng**: 30-60 phút/ngày. Mỗi chủ đề tuân thủ nghiêm ngặt Chu Kỳ 15 Ngày (15-Day Mastery Cycle).\n")
    out.append(f"> **Quy mô**: {TOTAL_TOPICS} chủ đề x 15 ngày = {TOTAL_DAYS} ngày bài bản, liên tục.\n\n")

    day = 0
    for (phase_num, phase_name, tag, title, _note) in TOPICS:
        for i, (focus_name, focus_desc, needs_noninteractive) in enumerate(DAY_FOCUS, start=1):
            day += 1
            out.append(f"## Day {day} — [{phase_name}] {title} (Ngày {i}/15: {focus_name})\n")
            out.append("**Prompt:**\n")
            out.append(f"YÊU CẦU BẮT BUỘC: LUÔN TRẢ LỜI BẰNG TIẾNG VIỆT.\n")
            out.append(f"Day {day} trong lộ trình Thiên Công Khai Vật & Tái Thiết Văn Minh ({TOTAL_DAYS} ngày).\n")
            out.append(f"Chủ đề: [Phase {phase_num} - {phase_name}] — {title}.\n")
            out.append(f"Trọng tâm hôm nay (Ngày {i}/15 của chủ đề này): **{focus_name}**.\n")
            out.append(f"{focus_desc}\n")
            out.append("Trình độ hiện tại: Xem các ngày trước trong chuỗi cây công nghệ để đảm bảo không nhảy cóc tri thức.\n")
            out.append("\n")
            out.append("Yêu cầu nội dung giảng giải (30-60 phút học):\n")
            out.append("1. NGUYÊN LÝ & BẢN CHẤT: Giải thích chính xác cơ chế khoa học/kỹ thuật của trọng tâm hôm nay.\n")
            out.append("2. HƯỚNG DẪN THỰC CHIẾN TỪNG BƯỚC: Mô tả chi tiết danh mục vật liệu, công cụ cần có và thao tác thực hành như một cẩm nang kỹ thuật thực thụ.\n")
            out.append("3. TÍNH KHẢ THI VÀ LIÊN KẾT TECH-TREE: Khâu này kết nối thế nào với công nghệ trước đó và tạo tiền đề cho công nghệ tương lai nào.\n")
            if needs_noninteractive:
                out.append(f"\n{NON_INTERACTIVE_NOTE}\n")
            out.append("\n")
            out.append("**Bài tập:**\n")
            out.append(f"- Bài 1 (Cơ bản): Ghi nhớ và tóm tắt lại các bước then chốt của [{focus_name}] cho chủ đề {title}.\n")
            out.append(f"- Bài 2 (Thực nghiệm): Phân tích một phương án thay thế vật liệu trong điều kiện thiếu thốn tài nguyên cho [{focus_name}].\n")
            out.append(f"- Bài 3 (Tích hợp hệ thống): Vẽ sơ đồ dòng chảy vật liệu và công cụ để chuẩn bị cho giai đoạn công nghệ tiếp theo.\n")
            out.append("\n")
            safe_tag = phase_name.lower().replace(' ', '_').replace('&','and').replace(',','').replace('/','_').replace('-','_')
            out.append(f"**Tags:**\n#thiencongkhaivat #day{day} #{tag} #{safe_tag} #reboot_civilization\n")
            out.append("\n---\n\n")

    content = "".join(out)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Đã sinh thành công {day} ngày vào file: {output_path}")
    return day, output_path

if __name__ == "__main__":
    generate_roadmap()
