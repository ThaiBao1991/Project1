# -*- coding: utf-8 -*-
"""
Sinh Lo Trinh Nau An SIEU CHI TIET - tach tung bien the mon (ca, ga, heo, bo, hai san...)
thanh 1 chu de rieng, ap dung Chu Ky 15 Ngay chuan cho TOAN BO nen am thuc
(Viet Nam theo tung loai dam, Chau A tung quoc gia, Chau Au tung quoc gia,
Lam banh, So che chuyen sau, Rau cu & Chay, Len men & Bao quan, Do uong, Dinh duong, Capstone).
"""
import re

# ---------------------------------------------------------------------------
# 1. 15 FOCUS AREA CHUAN CHO MOI CHU DE (giu nguyen template goc, khong doi)
# ---------------------------------------------------------------------------
FOCUS = [
    ("Core Concept",
     "Tong quan ve mon/ky thuat, nguon goc, nguyen lieu chinh can co, va hinh dung toan bo quy trinh tu dau den cuoi."),
    ("Ky Thuat Co Ban",
     "Cac buoc thao tac co ban nhat de lam duoc mon/ky thuat nay, tung buoc mot, khong bo qua chi tiet nao."),
    ("Deep Dive Khoa Hoc Nau An",
     "Giai thich khoa hoc thuc pham dang sau (vi du: phan ung Maillard, ho hoa tinh bot, bien tinh protein, vai tro cua nhiet do/pH) va tai sao ky thuat nay tao ra huong vi/ket cau do."),
    ("Ky Thuat Nang Cao",
     "Bien tau nang cao, ky thuat kieu nha hang/dau bep chuyen nghiep ap dung cho mon/ky thuat nay."),
    ("Xu Ly Su Co",
     "Cac loi thuong gap khi lam mon nay (chay, man/nhat, tach nuoc, chai, tanh...) va cach khac phuc tung loi cu the."),
    ("Toi Uu Huong Vi & Trinh Bay",
     "Cach can chinh gia vi cho vua khau vi, toi uu mau sac/trinh bay dia an bat mat."),
    ("Dung Cu Chuyen Dung",
     "Cac dung cu/thiet bi bep chuyen dung phu hop nhat cho mon/ky thuat nay va cach dung dung cach."),
    ("Kiem Tra Chat Luong & Nem Chuan",
     "Tieu chuan de biet mon an da dat (do chin, do dam, ket cau, do tuoi cua nguyen lieu) va cach tu danh gia mon minh lam."),
    ("Nau So Luong Lon",
     "Cach dieu chinh cong thuc/ky thuat khi nau cho nhieu nguoi hoac cho tiec, luu y ve thoi gian va nhiet do."),
    ("Bien The Vung Mien & Lich Su Mon An",
     "Cac bien the theo vung mien/gia dinh/quoc gia khac nhau va boi canh lich su/van hoa cua mon an."),
    ("Bien Tau Hien Dai & Fusion",
     "Cac cach bien tau hien dai hoac ket hop (fusion) voi phong cach am thuc khac dua tren nen tang mon goc."),
    ("Tu Lam Lai Tu Nguyen Lieu Tho Nhat",
     "Huong dan tu lam lai mon/thanh phan nay tu nguyen lieu tho nhat co the (vi du: tu so che nguyen con, tu ep nuoc cot, khong dung san pham che bien san) de hieu ban chat."),
    ("Mini-Project: Chuan Bi",
     "Len ke hoach thuc don, chuan bi nguyen lieu va dung cu cho mot bua an hoan chinh ap dung chu de nay."),
    ("Mini-Project: Thuc Hien",
     "Trien khai nau cac mon chinh trong ke hoach, xu ly cac buoc quan trong nhat dung luc."),
    ("Mini-Project: Hoan Thien",
     "Hoan thien trinh bay, nem lai va dieu chinh, rut kinh nghiem cho lan nau sau."),
]
WARN_POSITIONS = {5, 8}  # ngay trong chu ky 15 ngay co canh bao "khong tuong tac"
WARN_TEXT = "(⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu.)"

# ---------------------------------------------------------------------------
# 2. DANH SACH PHASE + CHU DE DA DUOC TACH CHI TIET THEO TUNG BIEN THE MON
#    (short_slug lay dung theo file goc; full topics moi la phan mo rong)
# ---------------------------------------------------------------------------
PHASES = [
(1, "Ky Thuat Nen Tang", "nentang", [
    "Dao va ky thuat cat: cac loai dao, cach cam dao, kieu cat (julienne, brunoise, chiffonade)",
    "Nhiet do & phuong phap nau: chien, xao, luoc, hap, nuong, ham, ky thuat kiem soat lua",
    "Gia vi co ban & can bang huong vi: ngot, man, chua, cay, dang, umami",
    "Ky thuat chon lua nguyen lieu tuoi ngon: thit, ca, rau cu tai cho/sieu thi",
    "Trinh bay mon an (plating) co ban va nguyen tac thi giac",
    "Nuoc sot bechamel nen tang kieu Phap",
    "Nuoc sot veloute nen tang kieu Phap",
    "Nuoc sot espagnole nen tang kieu Phap",
    "Nuoc sot hollandaise nen tang kieu Phap",
    "Nuoc sot tomate (ca chua) nen tang kieu Phap",
    "Nuoc dung ga (chicken stock) nen tang",
    "Nuoc dung heo nen tang",
    "Nuoc dung bo (beef stock) nen tang",
    "Nuoc dung rau cu (vegetable stock) nen tang",
]),
(2, "Cac Mon Ca Viet Nam", "monca", [
    "Ca loc kho to","Ca bong kho to","Ca tre kho to","Ca basa kho to",
    "Canh chua ca loc","Canh chua ca dieu hong","Canh chua ca keo",
    "Ca chien gion","Ca chien xu","Ca chien sa ot","Ca chien mam",
    "Ca hap gung hanh","Ca hap bia","Ca hap xi dau","Ca hap kieu Hong Kong",
    "Ca nuong muoi ot","Ca nuong giay bac","Ca nuong trui","Ca nuong moi",
    "Lau ca keo","Lau ca lang","Lau mam mien Tay",
    "Cha ca La Vong","Cha ca thac lac","Cha ca vien",
    "Goi ca trich","Goi ca mai","Mam ca linh","Mam ca sac",
    "Ca thu kho","Ca ngu kho","Ca bop nau canh",
    "Ca lang dac san vung mien","Ca anh vu dac san vung mien","Ca chinh dac san vung mien",
]),
(3, "Cac Mon Thit Heo Viet Nam", "monheo", [
    "Thit kho tau","Thit kho trung","Thit kho nuoc dua",
    "Thit luoc cham mam tom","Thit luoc cham mam nem","Thit luoc cham nuoc mam gung",
    "Thit heo nuong sa","Thit heo nuong mat ong","Thit heo nuong rieng me",
    "Suon nuong","Suon xao chua ngot","Suon rim man ngot",
    "Nem hai san (cha gio/nem ran)","Nem chay (cha gio/nem ran)","Nem vuong Hai Phong",
    "Gio lua","Gio thu","Cha que","Cha com",
    "Bun cha Ha Noi","Bun thit nuong","Mi xiu mai",
    "Long heo luoc/xao","Gan heo","Tim heo cat xao",
    "Thit dong ngay Tet",
    "Thit ba chi quay","Heo quay gion bi",
]),
(4, "Cac Mon Thit Ga Viet Nam", "monga", [
    "Ga luoc va ky thuat chat ga chuan",
    "Ga kho gung","Ga kho sa ot","Ga kho nghe",
    "Ga nuong mat ong","Ga nuong muoi ot","Ga nuong la chanh","Ga nuong than",
    "Ga chien nuoc mam","Ga chien gion kieu Han-Viet","Ga chien bo toi",
    "Chao ga","Sup ga ngo (giai cam)",
    "Goi ga xe phay","Goi ga bap cai","Goi ga hoa chuoi",
    "Mien ga","Bun ga","Pho ga",
    "Com ga Hoi An","Com ga xoi mo","Com ga kieu Hai Nam",
]),
(5, "Cac Mon Thit Bo Viet Nam", "monbo", [
    "Bo kho kieu Viet Nam","Bo luc lac",
    "Bo xao sa ot","Bo xao rau muong","Bo xao can toi",
    "Bo nuong la lot","Bo nuong vi","Bo nuong ngoi",
    "Pho bo chi tiet chuyen sau (nuoc dung trong, gia vi bi quyet)",
    "Bun bo Hue chi tiet chuyen sau",
    "Bo bit tet kieu Viet","Cac mon Au hoa kieu Viet tu thit bo",
]),
(6, "Hai San Khac Viet Nam", "haisankhac", [
    "Tom rang me","Tom nuong muoi ot","Tom chien gion",
    "Cua rang me","Cua hap bia","Lau cua dong",
    "Muc xao","Muc nuong sa te","Muc hap gung",
    "Oc luoc sa","Oc xao me","Cac loai nuoc cham oc",
    "Ngheu hap sa","So huyet nuong mo hanh",
]),
(7, "Canh & Sup Viet Nam", "canhsup", [
    "Canh chua tom","Canh chua bong so dua",
    "Canh rau mua xuan","Canh rau mua he","Canh rau mua thu","Canh rau mua dong",
    "Sup cua","Sup ga ngo kieu nha hang",
]),
(8, "Mon Nuoc Mi Bun Dac San Vung Mien", "monnuoc", [
    "Pho Bac chi tiet chuyen sau (nuoc dung, banh pho, gia vi bi truyen)",
    "Bun rieu","Bun dau mam tom",
    "Mi Quang",
    "Hu tieu Nam Vang","Hu tieu mien Nam",
    "Bun mam mien Tay",
    "Cao lau Hoi An",
]),
(9, "Banh Man & Cuon Viet Nam", "banhmancuon", [
    "Goi cuon","Nem cuon","Cac mon cuon Viet Nam khac",
    "Banh xeo","Banh khot",
    "Banh cuon","Banh uot",
]),
(10, "Mon Chay Viet Nam", "monchay", [
    "Mon chay kho","Mon chay xao","Canh chay",
    "Gio chay","Ga chay (tu dau nanh/mi can)","Cha chay (tu dau nanh/mi can)",
]),
(11, "Am Thuc Trung Hoa", "trunghoa", [
    "Ha cao (dimsum)","Xiu mai (dimsum)","Banh bao Trung Hoa (dimsum)",
    "Vit quay Bac Kinh","Cac mon quay khac kieu Trung Hoa",
    "Mi xao gion kieu Trung","Com chien Duong Chau",
    "Lau Tu Xuyen cay","Mapo tofu","Kung pao chicken",
    "Sup vi ca kieu Trung Hoa","Canh trung ca chua kieu Trung Hoa",
    "Ca hap kieu Quang Dong","Suon hap dau den kieu Quang Dong",
    "Char siu (xa xiu)","Thit quay kieu Quang Dong (khac xa xiu)",
    "Xiaolongbao","Cac loai mi ke Trung Hoa khac",
]),
(12, "Am Thuc Nhat Ban", "nhatban", [
    "Sushi co ban","Sashimi co ban",
    "Ramen tonkotsu","Ramen shoyu","Ramen miso","Ramen shio",
    "Tempura",
    "Oyakodon","Katsudon","Gyudon",
    "Udon","Soba",
    "Teriyaki","Mon nuong kieu Nhat khac (yakimono)",
    "Yakitori","Karaage",
    "Wagashi","Mochi","Dorayaki",
]),
(13, "Am Thuc Han Quoc", "hanquoc", [
    "Kim chi bap cai","Kim chi cu cai","Kim chi dua leo",
    "Bibimbap","Banchan",
    "Tteokbokki","Mon an vat duong pho Han Quoc khac",
    "Samgyeopsal","Bulgogi",
    "Ga ran Han Quoc (Korean fried chicken)",
    "Kimchi jjigae","Sundubu jjigae",
    "Japchae","Mon mien Han Quoc khac",
]),
(14, "Am Thuc Thai Lan", "thailan", [
    "Tom yum","Cac loai canh chua Thai khac",
    "Pad Thai","Mi xao Thai khac",
    "Green curry Thai","Red curry Thai","Yellow curry Thai",
    "Som tam (goi du du Thai)","Larb",
    "Xoi xoai Thai","Trang mieng Thai khac",
    "Satay","Ga nuong Thai",
]),
(15, "Am Thuc An Do", "andoo", [
    "Cari An Do co ban va gia vi masala",
    "Butter chicken","Ga tandoori",
    "Biryani","Com An Do khac",
    "Banh naan","Cac loai banh mi An Do khac",
    "Dal (dau An Do)","Mon chay An Do khac",
]),
(16, "Am Thuc Y", "amthucy", [
    "Pasta sauce carbonara","Pasta sauce bolognese","Pasta sauce aglio olio","Pasta sauce pesto",
    "Pizza Napoli","Cac loai pizza khac",
    "Risotto",
    "Lasagna","Mon nuong lo kieu Y khac",
    "Tiramisu","Trang mieng Y khac",
    "Antipasti","Salad kieu Y",
]),
(17, "Am Thuc Phap", "amthucphap", [
    "Coq au vin","Boeuf bourguignon",
    "Quiche","Crepe",
    "Soupe a l'oignon","Cac loai sup Phap khac",
    "Ratatouille","Rau cu kieu Phap khac",
    "Nuoc sot beurre blanc (ky thuat sot Phap nang cao)","Ky thuat reduction (ky thuat sot Phap nang cao)",
]),
(18, "Dia Trung Hai & Chau Au Khac", "chauaukhac", [
    "Moussaka (Hy Lap)","Souvlaki (Hy Lap)","Tzatziki (Hy Lap)",
    "Paella (Tay Ban Nha)","Tapas (Tay Ban Nha)","Gazpacho (Tay Ban Nha)",
    "Schnitzel (Duc)","Xuc xich Duc","Banh Duc (banh ngot kieu Duc)",
    "Burger (Anh-My)","BBQ kieu Anh-My","Mac and cheese (Anh-My)",
    "Taco (Mexico)","Burrito (Mexico)","Guacamole (Mexico)",
]),
(19, "Banh Mi (Bread)", "banhminen", [
    "Banh mi baguette kieu Phap/Viet",
    "Sandwich bread","Banh mi gia dinh",
    "Sourdough (men banh mi tu nhien)",
    "Banh naan (banh dep khong men)","Cac loai banh dep khong men khac",
    "Banh bao (mon bot hap kieu A Dong)","Cac mon bot hap kieu A Dong khac",
]),
(20, "Banh Ngot Co Ban", "banhngot", [
    "Cake nen tang vanilla","Cake nen tang chocolate","Cake nen tang red velvet",
    "Cheesecake",
    "Cookie cac loai",
    "Muffin","Cupcake",
    "Banh kem sinh nhat va ky thuat trang tri",
]),
(21, "Banh Phap Cao Cap", "banhphapcaocap", [
    "Eclair (choux)","Profiterole (choux)",
    "Croissant (puff pastry)","Mille-feuille (puff pastry)",
    "Macaron",
    "Tart kieu Phap","Pie kieu Phap",
]),
(22, "Chocolate & Keo", "chocolatekeo", [
    "Tempering chocolate dung ky thuat",
    "Pralines","Truffles (chocolate)",
    "Keo dua truyen thong Viet Nam","Keo lac truyen thong Viet Nam",
]),
(23, "So Che Thit Chuyen Sau", "sochethit", [
    "So che ga nguyen con chuyen nghiep",
    "So che heo nguyen con/mieng lon",
    "So che bo: cac phan thit va cach dung tung phan",
    "Ky thuat lang xuong ca (fish filleting)",
]),
(24, "So Che Hai San Chuyen Sau", "sochehaisan", [
    "So che tom cua chuyen nghiep",
    "So che muc va bach tuoc",
    "Ky thuat nuong/grill hai san chuyen sau kieu nha hang",
]),
(25, "Rau Cu & Nguyen Lieu Chay", "raucuchay", [
    "Ky thuat che bien rau cu giu toi da dinh duong",
    "Dau hu (tofu) cac cach che bien",
    "Nam huong","Nam kim cham","Nam dui ga",
    "Seitan","Cac loai protein thuc vat khac",
    "Salad & rau song trang tri chuyen sau",
]),
(26, "Len Men & Bao Quan", "lenmen", [
    "Kim chi chuyen sau (ky thuat len men)","Dua muoi chuyen sau",
    "Nuoc mam tu lam tai nha","Mam cac loai tu lam tai nha",
    "Tuong tu lam","Xi dau tu lam","Chao tu lam",
    "Sourdough starter & men banh mi tu nhien chuyen sau",
    "Kombucha","Cac loai do uong len men khac",
    "Bao quan thuc pham: dong lanh","Bao quan thuc pham: say kho","Bao quan thuc pham: dong hop",
]),
(27, "Do Uong & Pha Che", "phache", [
    "Ca phe phin Viet Nam","Bac xiu","Ca phe sua da",
    "Espresso","Cappuccino","Latte","Pour over","Cold brew",
    "Tra Viet Nam","Tra sua",
    "Sinh to trai cay","Nuoc ep trai cay/rau cu",
    "Che dau xanh/dau do","Che chuoi/khoai mon","Che troi nuoc/che thap cam",
    "Nuoc mia","Tra da","Sam bo luong",
]),
(28, "Dinh Duong & Thuc Don", "dinhduong", [
    "Dinh duong co ban ap dung vao nau an hang ngay",
    "Len thuc don can bang cho tuan/thang cho gia dinh",
    "Nau an linh hoat theo so thich/che do an dac biet (khong thay the tu van y te)",
    "Meal prep: chuan bi thuc an san cho ca tuan",
]),
(29, "Capstone Nau An", "capstonenauan", [
    "Capstone 1: Len thuc don va nau mot bua tiec hoan chinh nhieu mon",
    "Capstone 2: Tu lam tu dau mot chuoi nguyen lieu (vi du: tu nhao bot mi den to mi hoan chinh)",
    "Capstone 3: To chuc mot bua tiec theo chu de am thuc mot quoc gia cu the",
    "Capstone 4: Xay dung thuc don Fusion ca nhan ket hop Viet Nam va quoc te",
    "Capstone 5: Tong hop toan bo - xay dung phong cach nau an ca nhan dai han",
]),
]

def full_slug(name: str) -> str:
    s = name.lower()
    s = s.replace("&", "and")
    s = re.sub(r"[()\.,'/]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    return s

TOTAL_TOPICS = sum(len(topics) for _, _, _, topics in PHASES)
TOTAL_DAYS = TOTAL_TOPICS * 15

def build_entry(global_day, phase_num, phase_name, topic, day_in_cycle):
    label, desc = FOCUS[day_in_cycle - 1]
    fslug = full_slug(phase_name)
    header = f"## Day {global_day} — [{phase_name}] {topic} (Ngay {day_in_cycle}/15: {label})"
    lines = [header, "**Prompt:**"]
    lines.append(f"Day {global_day} trong lo trinh Nau An Sieu Chi Tiet Toan Dien ({TOTAL_DAYS} ngay).")
    lines.append(f"Chu de: [Phase {phase_num} - {phase_name}] — {topic}.")
    lines.append(f"Trong tam hom nay (Ngay {day_in_cycle}/15 cua chu de nay): **{label}**.")
    lines.append(desc)
    lines.append("Trinh do hien tai: Xem cac ngay truoc trong chu de nay de biet nguoi hoc dang o dau.")
    lines.append("")
    lines.append("Yeu cau day hoc (30-60 phut):")
    lines.append("1. GIAI THICH TRONG TAM: Giai thich dung vao khia canh duoc yeu cau hom nay, khong lan man sang phan khac.")
    lines.append("2. VI DU/CONG THUC CU THE: Cong thuc/huong dan chi tiet tung buoc, co ty le nguyen lieu ro rang.")
    lines.append("3. AP DUNG THUC TE: Khia canh nay giup ich the nao khi nau an hang ngay hoac cho dip dac biet.")
    lines.append("")
    if day_in_cycle in WARN_POSITIONS:
        lines.append(WARN_TEXT)
        lines.append("")
    lines.append("**Bài tập:**")
    lines.append(f"- Bài 1 (Cơ bản): Thực hành lại [{label}] theo đúng công thức/hướng dẫn cho món {topic}.")
    lines.append(f"- Bài 2 (Trung cấp): Thử biến tấu nguyên liệu hoặc gia vị cho [{label}].")
    lines.append(f"- Bài 3 (Nâng cao): Áp dụng [{label}] vào một bữa ăn thực tế cho gia đình/bạn bè.")
    lines.append("")
    short_slug = SHORT_SLUG_BY_PHASE[phase_num]
    lines.append(f"**Tags:** #nauan #day{global_day} #{short_slug} #{fslug}")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)

SHORT_SLUG_BY_PHASE = {num: slug for num, _, slug, _ in PHASES}

def main():
    out_path = "/mnt/user-data/outputs/roadmap_nau_an_sieu_chi_tiet.md"
    header_md = []
    header_md.append(f"# Nau An Sieu Chi Tiet Toan Dien — Lo Trinh {TOTAL_DAYS} Ngay ({TOTAL_TOPICS} Chu De x 15 Ngay/Chu De)")
    header_md.append(f"> Muc tieu: Moi BIEN THE MON CU THE (vi du: ca loc kho to, ca bong kho to, ga nuong mat ong, bo luc lac...) duoc tach thanh MOT chu de rieng bang, moi chu de di het Chu Ky 15 Ngay chuan (Core Concept -> Ky thuat co ban -> Deep Dive khoa hoc -> Nang cao -> Xu ly su co -> Toi uu -> Dung cu -> Kiem tra chat luong -> Nau so luong lon -> Bien the vung mien -> Bien tau hien dai -> Tu lam tu dau -> Mini-Project 1/2/3). Ap dung cho TOAN BO nen am thuc: nen tang, Am thuc Viet Nam theo tung loai dam (ca, heo, ga, bo, hai san), Am thuc Chau A tung quoc gia (Trung, Nhat, Han, Thai, An Do), Am thuc Chau Au tung quoc gia (Y, Phap, Hy Lap, Tay Ban Nha, Duc, My, Mexico), Lam banh (banh mi, banh ngot, banh Phap cao cap, chocolate), So che chuyen sau, Rau cu & Chay, Len men & Bao quan, Do uong & Pha che, Dinh duong & Thuc don.")
    header_md.append("> Thoi luong: 30-60 phut/ngay.")
    header_md.append(f"> Tong: {TOTAL_TOPICS} chu de x 15 ngay = {TOTAL_DAYS} ngay.")
    header_md.append("")
    header_md.append("> Luu y: Phan 'Dinh duong & Thuc don' chi mang tinh tham khao thong thuong, khong thay the tu van cua bac si/chuyen gia dinh duong, dac biet neu ban co benh ly hoac che do an dac biet.")
    header_md.append("")

    entries = []
    global_day = 0
    for phase_num, phase_name, short_slug, topics in PHASES:
        for topic in topics:
            for day_in_cycle in range(1, 16):
                global_day += 1
                entries.append(build_entry(global_day, phase_num, phase_name, topic, day_in_cycle))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(header_md))
        f.write("\n")
        f.write("\n".join(entries))

    print("TOTAL_TOPICS:", TOTAL_TOPICS)
    print("TOTAL_DAYS:", TOTAL_DAYS)
    print("Wrote:", out_path)

if __name__ == "__main__":
    main()
