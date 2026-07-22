# -*- coding: utf-8 -*-
# Generator: Thien Cong Khai Vat & Che Tao Moi Thu - Roadmap 15-Day Cycle
# Tuan thu SKILL.md: Generate Roadmap (format Prompt/Bai tap/Tags, khong tuong tac, utf-8)

TOPICS = []
def add(phase_num, phase_name, tag, title, note=""):
    TOPICS.append((phase_num, phase_name, tag, title, note))

# ============ PHASE 1: NONG NGHIEP & LUONG THUC ============
P="Nong Nghiep & Luong Thuc"; T="nongnghiep"
add(1,P,T,"Trong lua va xu ly gao: tu gia gao bang tay/coi da den may xay xat cong nghiep")
add(1,P,T,"Lam muoi: tu phoi nuoc bien thu cong den nha may muoi cong nghiep")
add(1,P,T,"Ep dau thuc vat: tu ep thu cong bang coi/ban ep den may ep dau cong nghiep va chiet xuat dung moi")
add(1,P,T,"U men & len men thuc pham: ruou, giam, tuong - tu thu cong den len men cong nghiep co kiem soat")
add(1,P,T,"Bao quan thuc pham: phoi kho, uop muoi truyen thong den dong hop/dong lanh cong nghiep")

# ============ PHASE 2: DET MAY & SOI ============
P="Det May & Soi"; T="detmay"
add(2,P,T,"Keo soi: tu xa quay tay (to tam, bong) den may keo soi cong nghiep (spinning jenny, spinning mule)")
add(2,P,T,"Det vai: tu khung det tay den may det co khi va may det tu dong Jacquard")
add(2,P,T,"Nhuom vai: tu thuoc nhuom tu nhien (thuc vat, khoang chat) den thuoc nhuom tong hop cong nghiep")
add(2,P,T,"May mac: tu may tay den may may cong nghiep va day chuyen san xuat hang loat")

# ============ PHASE 3: GIAY & IN AN (trong tam vi du nguoi dung) ============
P="Giay & In An"; T="giayvainan"
add(3,P,T,"Lam giay thu cong: nguyen ly bot giay tu vo cay/gio, xeo giay bang khung tre")
add(3,P,T,"Cong nghiep hoa giay: may nghien bot go, quy trinh Kraft, may xeo giay Fourdrinier hien dai")
add(3,P,T,"In an: tu khac go, in typeset chi bao den in offset va in ky thuat so cong nghiep")

# ============ PHASE 4: LUYEN KIM & GIA CONG KIM LOAI ============
P="Luyen Kim & Gia Cong Kim Loai"; T="luyenkim"
add(4,P,T,"Luyen dong: tu quang dong den dong nguyen chat bang lo nung thu cong")
add(4,P,T,"Luyen sat & thep: lo bloomery co dai den lo cao Bessemer va lo dien ho quang hien dai")
add(4,P,T,"Ren kim loai: ren tay bang bua de den may ren va may dap cong nghiep")
add(4,P,T,"Duc kim loai: duc khuon cat thu cong den duc ap luc va duc lien tuc cong nghiep")
add(4,P,T,"Gia cong co khi hien dai: tien, phay, han - tu may cong cu tay den may CNC")

# ============ PHASE 5: GOM SU & VAT LIEU XAY DUNG ============
P="Gom Su & Vat Lieu Xay Dung"; T="gomsu"
add(5,P,T,"Lam gom: nan tay va ban xoay den lo nung cong nghiep va gom su ky thuat")
add(5,P,T,"Lam gach ngoi: dat set nung thu cong den lo gach tuynel cong nghiep lien tuc")
add(5,P,T,"Xi mang & be tong: voi toi truyen thong den xi mang Portland va be tong cot thep cong nghiep")
add(5,P,T,"Thuy tinh: thoi thuy tinh bang tay den may san xuat thuy tinh float glass hien dai")

# ============ PHASE 6: MOC & CHE TAC GO ============
P="Moc & Che Tac Go"; T="moc"
add(6,P,T,"Moc co ban: dung cu tay, mong go, ghep noi khong dung dinh")
add(6,P,T,"Moc nang cao: may cua, may bao co khi den may CNC go cong nghiep")

# ============ PHASE 7: DIEN & DIEN TU CO BAN ============
P="Dien & Dien Tu Co Ban"; T="dien"
add(7,P,T,"Mach dien co ban: pin, day dan, cong tac - tu pin Volta den dong co dien DC dau tien")
add(7,P,T,"Dien tu co ban: diode, transistor, mach khuech dai va mach logic don gian")
add(7,P,T,"Che tao ban dan tong quan: tu silicon tinh khiet den vi mach - quy trinh san xuat chip cong nghiep")

# ============ PHASE 8: HOA CHAT & VAT LIEU TONG HOP ============
P="Hoa Chat & Vat Lieu Tong Hop"; T="hoachat"
add(8,P,T,"Xa phong & chat tay rua: xa phong thu cong tu mo/dau den san xuat cong nghiep")
add(8,P,T,"Chat ket dinh & keo: keo tu nhien (nhua cay, xuong) den keo tong hop cong nghiep")
add(8,P,T,"Nhua & polymer: tu cao su tu nhien den nhua tong hop va quy trinh polymer hoa cong nghiep")

# ============ PHASE 9: NANG LUONG ============
P="Nang Luong"; T="nangluong"
add(9,P,T,"Nang luong nuoc & gio: coi xay nuoc/gio co dai den turbine thuy dien va dien gio hien dai")
add(9,P,T,"Dong co hoi nuoc: nguyen ly va lich su cong nghiep hoa tu dong co Watt")
add(9,P,T,"Dong co dot trong co ban: nguyen ly 4 ky va lich su phat trien dong co hien dai")

# ============ PHASE 10: CAPSTONE - TONG HOP CHE TAO ============
P="Capstone - Tong Hop Che Tao"; T="capstone"
add(10,P,T,"Capstone 1: Tu nguyen lieu tho den san pham hoan chinh - chuoi cung ung co dai (vi du: tu cay gai/bong ra tam vai)")
add(10,P,T,"Capstone 2: Tu thiet ke mot xuong che tao mini ket hop go, kim loai va dien co ban")
add(10,P,T,"Capstone 3: Tong ket toan bo lo trinh - lap ke hoach ca nhan ve nang luc 'tu chu che tao' tu dau")

TOTAL_TOPICS = len(TOPICS)
TOTAL_DAYS = TOTAL_TOPICS * 15
print("TOTAL TOPICS:", TOTAL_TOPICS)
print("TOTAL DAYS:", TOTAL_DAYS)

# ============ 15-DAY STANDARD STRUCTURE (adapted cho che tao/thu cong) ============
DAY_FOCUS = [
    ("Core Concept", "Tong quan ve chu de, nguyen lieu can co, boi canh lich su (co lien he Thien Cong Khai Vat neu phu hop), va vi du don gian nhat de hinh dung toan bo quy trinh.", False),
    ("Ky Thuat Co Ban", "Ky thuat thu cong nen tang nhat, dung cu toi thieu can co, cac buoc thao tac co ban tung dong mot.", False),
    ("Deep Dive Khoa Hoc", "Giai thich khoa hoc/vat lieu hoc dang sau quy trinh (vi du: phan ung hoa hoc, cau truc vat lieu, tai sao ky thuat nay hieu qua).", False),
    ("Ky Thuat Nang Cao Truyen Thong", "Cac bien the ky thuat nang cao theo vung mien/thoi ky khac nhau, thu thuat cua nghe nhan truyen thong.", False),
    ("Xu Ly Su Co", "Cac loi thuong gap trong qua trinh lam va cach khac phuc tung loi cu the.", True),
    ("Toi Uu Chat Luong", "Cach toi uu chat luong thanh pham, tang nang suat, giam hao phi nguyen lieu.", False),
    ("Thiet Ke Cong Cu/Xuong", "Thiet ke cong cu ho tro hoac bo tri khong gian xuong lam viec toi uu cho quy trinh nay.", False),
    ("Kiem Tra Chat Luong", "Cac tieu chuan va phuong phap kiem tra chat luong san pham dau ra.", True),
    ("Mo Rong Quy Mo", "Cach mo rong tu lam thu cong don le len quy mo xuong nho (workshop scale), can nhac ve nhan luc/thiet bi.", False),
    ("Lich Su Cong Nghiep Hoa", "Lich su cac phat minh may moc mang tinh buoc ngoat da co gioi hoa quy trinh nay, boi canh Cach mang Cong nghiep.", False),
    ("Quy Trinh Cong Nghiep Hien Dai & May Moc", "Ten cu the cac loai may moc/day chuyen san xuat cong nghiep hien dai dang dung cho quy trinh nay, nguyen ly hoat dong cua chung.", False),
    ("Tu Lam Lai Tu Dau", "Huong dan tu tay lam lai toan bo quy trinh voi dung cu toi thieu nhat, khong phu thuoc may moc, de hieu ban chat cot loi.", False),
    ("Mini-Project: Chuan Bi", "Len ke hoach, chuan bi nguyen lieu va dung cu cho mot du an thuc hanh hoan chinh ap dung chu de nay.", False),
    ("Mini-Project: Thuc Hien", "Trien khai cac buoc chinh cua du an thuc hanh, xu ly nghiep vu/thao tac cot loi.", False),
    ("Mini-Project: Hoan Thien", "Hoan thien san pham, danh gia ket qua, va de xuat cai tien cho lan lam sau.", False),
]

NON_INTERACTIVE_NOTE = (
    "(⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. "
    "HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu.)"
)

out = []
out.append(f"# Thien Cong Khai Vat & Che Tao Moi Thu — Lo Trinh {TOTAL_DAYS} Ngay ({TOTAL_TOPICS} Chu De x 15 Ngay/Chu De)\n")
out.append("> Muc tieu: Xay dung nen tang tu duy che tao tien cong nghiep (lay cam hung tu Thien Cong Khai Vat) roi cai tien dan tung buoc len quy trinh co gioi hoa/cong nghiep hoa hien dai, bao phu nong nghiep, det may, giay/in an, luyen kim, gom su, moc, dien tu, hoa chat, nang luong.\n")
out.append("> Thoi luong: 30-60 phut/ngay. Moi chu de theo dung Chu Ky 15 Ngay chuan (Core Concept -> Ky thuat -> Deep Dive -> Nang cao -> Xu ly su co -> Toi uu -> Thiet ke cong cu -> Kiem tra chat luong -> Mo rong quy mo -> Lich su cong nghiep hoa -> Quy trinh may moc hien dai -> Tu lam lai tu dau -> Mini-Project 1/2/3).\n")
out.append(f"> Tong: {TOTAL_TOPICS} chu de x 15 ngay = {TOTAL_DAYS} ngay.\n")
out.append("\n> Luu y an toan: Lo trinh khong bao gom cac quy trinh che tao vu khi, chat no, hoac hoa chat nguy hiem (thuoc sung, chat no...) du day la cac chu de xuat hien trong lich su cong nghe — phan nay chi nen tim hieu qua sach lich su, khong nam trong lo trinh thuc hanh nay.\n")
out.append("\n")

day = 0
for (phase_num, phase_name, tag, title, _note) in TOPICS:
    for i, (focus_name, focus_desc, needs_noninteractive) in enumerate(DAY_FOCUS, start=1):
        day += 1
        out.append(f"## Day {day} — [{phase_name}] {title} (Ngay {i}/15: {focus_name})\n")
        out.append("**Prompt:**\n")
        out.append(f"Day {day} trong lo trinh Thien Cong Khai Vat & Che Tao Moi Thu ({TOTAL_DAYS} ngay).\n")
        out.append(f"Chu de: [Phase {phase_num} - {phase_name}] — {title}.\n")
        out.append(f"Trong tam hom nay (Ngay {i}/15 cua chu de nay): **{focus_name}**.\n")
        out.append(f"{focus_desc}\n")
        out.append("Trinh do hien tai: Xem cac ngay truoc trong chu de nay de biet nguoi hoc dang o dau.\n")
        out.append("\n")
        out.append("Yeu cau day hoc (30-60 phut):\n")
        out.append("1. GIAI THICH TRONG TAM: Giai thich dung vao khia canh duoc yeu cau hom nay, khong lan man sang phan khac.\n")
        out.append("2. VI DU/MINH HOA CU THE: Mo ta chi tiet, tung buoc, nhu dang huong dan thuc hanh that.\n")
        out.append("3. AP DUNG THUC TE: Khia canh nay lien quan the nao den viec 'tu chu che tao' hoac quy trinh cong nghiep thuc te.\n")
        if needs_noninteractive:
            out.append(f"\n{NON_INTERACTIVE_NOTE}\n")
        out.append("\n")
        out.append("**Bài tập:**\n")
        out.append(f"- Bài 1 (Cơ bản): Ghi lại/mô tả lại các bước cơ bản của [{focus_name}] cho chủ đề {title}.\n")
        out.append(f"- Bài 2 (Trung cấp): Thử áp dụng hoặc mở rộng [{focus_name}] với một biến thể nguyên liệu/hoàn cảnh khác.\n")
        out.append(f"- Bài 3 (Nâng cao): Đối chiếu [{focus_name}] với quy trình công nghiệp hiện đại tương ứng (nếu có).\n")
        out.append("\n")
        safe_tag = phase_name.lower().replace(' ', '_').replace('&','and').replace(',','').replace('/','_').replace('-','_')
        out.append(f"**Tags:** #thiencongkhaivat #day{day} #{tag} #{safe_tag}\n")
        out.append("\n---\n\n")

with open("/mnt/user-data/outputs/roadmap_thien_cong_khai_vat.md", "w", encoding="utf-8") as f:
    f.write("".join(out))

print("DONE")
