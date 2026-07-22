# -*- coding: utf-8 -*-
"""
Sinh Lo Trinh SIEU CHI TIET cho nhom chu de: Thien & Chanh niem, Thoi mien tri lieu,
Mentalism, Dao giao, Yoga Patanjali, Phat giao Thien dinh & Luc thong.
Moi chu de con (khong lan man, khong trung lap) duoc tach rieng va ap dung
Chu Ky 15 Ngay chuan (tuong tu chuan IT/Lap trinh trong SKILL.md, duoc dieu chinh
lai cho phu hop voi noi dung tri thuc/thuc hanh tam linh - triet hoc - tam ly).
"""
import re

# ---------------------------------------------------------------------------
# 1. 15 FOCUS AREA CHUAN CHO MOI CHU DE (dieu chinh rieng cho nhom chu de nay)
# ---------------------------------------------------------------------------
FOCUS = [
    ("Core Concept",
     "Tong quan, dinh nghia, nguon goc va boi canh hinh thanh cua chu de; hinh dung toan canh truoc khi di sau."),
    ("Lich Su & Nhan Vat Chu Chot",
     "Dong lich su hinh thanh, phat trien; cac nhan vat/tac gia then chot gan lien voi chu de."),
    ("Deep Dive Ly Thuyet Nen Tang",
     "Dao sau triet ly/ly thuyet cot loi dung sau chu de, giai thich logic va y nghia sau xa."),
    ("Van Ban Goc & Trich Dan Kinh Dien",
     "Phan tich cac doan van ban goc/kinh dien lien quan (dich nghia, giai thich thuat ngu), tranh dien giai sai lech."),
    ("Ky Thuat & Phuong Phap Thuc Hanh",
     "Cac buoc thuc hanh cu the, chi tiet tung thao tac de ap dung chu de vao thuc te."),
    ("Co Che Khoa Hoc / Tam Ly Hoc",
     "Giai thich duoi goc do khoa hoc than kinh/tam ly hoc (neu co nghien cuu) tai sao ky thuat nay co tac dung."),
    ("Sai Lam Thuong Gap & Cach Khac Phuc",
     "Cac hieu lam/sai lam pho bien khi tiep can chu de nay va cach dieu chinh cho dung."),
    ("So Sanh & Doi Chieu Truong Phai",
     "So sanh chu de voi cac truong phai/phuong phap khac co lien quan hoac de nham lan."),
    ("Ung Dung Thuc Te Doi Song",
     "Cach ap dung chu de vao doi song hang ngay, cong viec, hoac giai quyet van de cu the."),
    ("Dao Duc, Gioi Han & Canh Bao",
     "Ranh gioi dao duc, rui ro tiem an, va nhung gioi han can ton trong khi thuc hanh/ap dung chu de."),
    ("Nhan Vat/Truong Phai Tieu Bieu Chuyen Sau",
     "Phan tich chuyen sau mot nhan vat/truong phai/tac pham tieu bieu nhat lien quan truc tiep toi chu de."),
    ("Tu Thuc Hanh Tai Tao Tu Dau",
     "Tu trai nghiem/thuc hanh lai toan bo tien trinh tu con so 0, khong dua vao tai lieu co san, de hieu ban chat."),
    ("Mini-Project: Chuan Bi",
     "Len ke hoach, xac dinh muc tieu va chuan bi moi thu can thiet de thuc hanh chu de trong mot du an nho hoan chinh."),
    ("Mini-Project: Thuc Hien",
     "Trien khai thuc hanh du an nho, ghi chu lai qua trinh va nhung gi quan sat duoc."),
    ("Mini-Project: Hoan Thien & Tong Ket",
     "Tong ket du an nho, rut kinh nghiem, doi chieu voi muc tieu ban dau va dinh huong buoc tiep theo."),
]
# Cac ngay trong chu ky 15 ngay can canh bao "khong tuong tac" (de/quiz/trich dan/mini-project)
WARN_POSITIONS = {4, 7, 13, 14, 15}
WARN_TEXT = "(⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu.)"

# ---------------------------------------------------------------------------
# 2. DANH SACH PHASE + 66 CHU DE CON DA TACH THEO YEU CAU (khong lan man, khong trung lap)
# ---------------------------------------------------------------------------
PHASES = [
(1, "Thien & Chanh Niem", "thienchanhniem", [
    "MBSR - Mindfulness-Based Stress Reduction: chuong trinh goc cua Jon Kabat-Zinn",
    "Body Scan - Thien quet co the",
    "Thien hoi tho (Anapana co ban ung dung the tuc)",
    "Thien hanh (Walking Meditation)",
    "Mindful Eating - An trong chanh niem",
    "Metta - Thien Tam Tu (Loving-Kindness Meditation)",
    "MBCT - Mindfulness-Based Cognitive Therapy (tri lieu nhan thuc dua tren chanh niem)",
    "Thich Nhat Hanh va phuong phap Chanh Niem ung dung doi song",
    "Lang Mai va mo hinh tang than tu tap chanh niem",
    "Khoa hoc than kinh ve chanh niem (neuroplasticity, vo nao truoc tran, giam cortisol)",
    "Chanh niem cong so (Mindfulness at Work)",
    "RAIN - ky thuat nhan dien va om ap cam xuc (Recognize, Allow, Investigate, Nurture)",
    "Chanh niem so (Digital Mindfulness) - quan he lanh manh voi man hinh/mang xa hoi",
    "Chanh niem nuoi day con (Mindful Parenting)",
]),
(2, "Thoi Mien Tri Lieu", "thoimien", [
    "Lich su thoi mien: tu Mesmer (Animal Magnetism) den Braid (dat ten Hypnosis)",
    "Milton Erickson va truong phai thoi mien gian tiep hien dai",
    "Co che Trance: trang thai y thuc thay doi la gi, dien ra nhu the nao",
    "Ky thuat dan nhap (Induction Techniques) trong thoi mien",
    "Tu thoi mien (Self-Hypnosis): quy trinh va ung dung ca nhan",
    "Thoi mien giam dau (Hypnoanalgesia) - co so va ung dung lam sang",
    "Thoi mien ho tro cai thuoc la",
    "Thoi mien giam lo au va cang thang",
    "Phan biet thoi mien san khau (Stage Hypnosis) va thoi mien lam sang (Clinical Hypnosis)",
    "Con duong dao tao va chung chi hanh nghe thoi mien tri lieu",
]),
(3, "Mentalism", "mentalism", [
    "Lich su Mentalism: tu ao thuat gia the ky 19 den mentalist hien dai",
    "Cold Reading - ky thuat doc nguoi khong can thong tin truoc",
    "Barnum Effect (Hieu ung Forer) - vi sao loi noi chung chung nghe rat 'dung'",
    "Ngon ngu co the va vi bieu cam (micro-expressions) trong doc vi",
    "Hieu ung Ideomotor va hien tuong 'Clever Hans'",
    "Ky thuat ghi nho (Memory Techniques) ung dung trong trinh dien mentalism",
    "Xac suat va thong ke ung dung trong cac man 'doan' cua mentalist",
    "Thuyet phuc tam ly va dan dat lua chon (Forcing, Suggestion)",
    "Dao duc nghe mentalism: ranh gioi giua giai tri va loi dung long tin",
    "Phan biet mentalism giai tri chan chinh va cac hinh thuc lua dao gia danh tam linh",
]),
(4, "Dao Giao", "daogiao", [
    "Dao Duc Kinh - Phan 1 (Dao Kinh, chuong 1-37): ban chat cua Dao",
    "Dao Duc Kinh - Phan 2 (Duc Kinh, chuong 38-81): Duc va cach song thuan theo Dao",
    "Nam Hoa Kinh (Trang Tu) - tong quan tu tuong va but phap ngu ngon",
    "Giac mong buom (Trang Chu mong hoa buom) - y nghia triet hoc ve thuc tai va ban nga",
    "Am Duong - nguyen ly nen tang cua vu tru quan Dao giao",
    "Ngu Hanh - Kim Moc Thuy Hoa Tho va quy luat sinh khac",
    "Vo Vi - tu tuong 'hanh dong khong cuong cau' va ung dung xu the",
    "Tham Dong Khe - tac pham nen tang cua Dao giao luyen dan (Ngoai dan)",
    "Tinh Menh Khue Chi - kinh dien ve tu luyen Noi dan (tu tuong Song Tu Tinh Menh)",
    "Khi cong - nen tang ly thuyet va cac truong phai luyen khi chinh",
    "Bat Tien - phan tich su that lich su va lop huyen thoai hoa qua thoi gian",
    "Anh huong cua Dao giao len Dong y (kinh lac, duong sinh, am duong ngu hanh trong y hoc)",
]),
(5, "Yoga Patanjali", "yogapatanjali", [
    "Nen tang triet hoc Samkhya lam co so cho he thong Yoga Sutras",
    "Chuong 1 - Samadhi Pada: dinh nghia Yoga va cac cap do Samadhi",
    "Chuong 2 (phan dau) - Sadhana Pada: Kriya Yoga va nhom Yama - Niyama - Asana - Pranayama",
    "Chuong 2 (phan sau) - Pratyahara: thu nhiep giac quan va cau noi vao dinh",
    "Chuong 3 - Vibhuti Pada: Dharana - Dhyana - Samyama va cac Siddhi (thanh tuu sieu nhien)",
    "Chuong 4 - Kaivalya Pada: con duong giai thoat toi thuong",
    "Siddhi trong Yoga Sutras: liet ke chi tiet va quan diem canh bao cua chinh Patanjali",
    "Lich su Yoga truoc Patanjali (Veda, Upanishad va cac mam mong so khai)",
    "Lich su Yoga sau Patanjali (Hatha Yoga, su du nhap va bien doi o phuong Tay)",
    "Yoga co dien (Raja Yoga theo Patanjali) doi chieu Yoga hien dai (the duc/thuong mai hoa)",
]),
(6, "Phat Giao Thien Dinh & Luc Thong", "phatgiaothiendinh", [
    "Tu Niem Xu - nen tang thuc hanh chanh niem trong kinh dien Phat giao",
    "Anapanasati - kinh Quan Niem Hoi Tho, 16 buoc thuc hanh",
    "Samatha - thien Chi (dinh tam, an chi)",
    "Vipassana - thien Quan (tue giac, thay ro ban chat vo thuong-kho-vo nga)",
    "Cuu Thu De Dinh - Tu Thien Sac Gioi, Tu Khong Vo Sac Dinh va Diet Tho Tuong Dinh",
    "Luc Thong - sau nang luc sieu nhien duoc kinh dien de cap",
    "Loi Phat day ve than thong: thai do, gioi han va canh bao lam dung",
    "Trung Dao - nguyen tac can bang, tranh cuc doan trong tu tap",
    "Cac truong phai thien Phat giao (Nam truyen Theravada, Bac truyen, Thien tong Zen)",
    "So sanh he thong thien Phat giao voi Chanh niem the tuc (MBSR va cac ung dung lam sang hien dai)",
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
SHORT_SLUG_BY_PHASE = {num: slug for num, _, slug, _ in PHASES}

def build_entry(global_day, phase_num, phase_name, topic, day_in_cycle):
    label, desc = FOCUS[day_in_cycle - 1]
    fslug = full_slug(topic)
    header = f"## Day {global_day} — [{phase_name}] {topic} (Ngay {day_in_cycle}/15: {label})"
    lines = [header, "**Prompt:**"]
    lines.append(f"Day {global_day} trong lo trinh Thien - Thoi Mien - Mentalism - Dao Giao - Yoga - Phat Giao SIEU CHI TIET ({TOTAL_DAYS} ngay).")
    lines.append(f"Chu de: [Phase {phase_num} - {phase_name}] — {topic}.")
    lines.append(f"Trong tam hom nay (Ngay {day_in_cycle}/15 cua chu de nay): **{label}**.")
    lines.append(desc)
    lines.append("Trinh do hien tai: Xem cac ngay truoc trong chu de nay de biet nguoi hoc dang o dau.")
    lines.append("")
    lines.append("Yeu cau day hoc (30-60 phut):")
    lines.append("1. GIAI THICH TRONG TAM: Giai thich dung vao khia canh duoc yeu cau hom nay, khong lan man sang phan khac.")
    lines.append("2. VI DU/DAN CHUNG CU THE: Trich dan/vi du/huong dan thuc hanh chi tiet tung buoc, co can cu ro rang (kinh dien, nghien cuu, hoac nguon uy tin).")
    lines.append("3. AP DUNG THUC TE: Khia canh nay giup ich the nao trong doi song, tu tap, hoac hieu biet ca nhan.")
    lines.append("")
    if day_in_cycle in WARN_POSITIONS:
        lines.append(WARN_TEXT)
        lines.append("")
    lines.append("**Bài tập:**")
    lines.append(f"- Bài 1 (Cơ bản): Tóm tắt lại đúng trọng tâm [{label}] vừa học về chủ đề {topic}.")
    lines.append(f"- Bài 2 (Trung cấp): Đặt 2-3 câu hỏi phản biện/đào sâu về [{label}] và tự trả lời dựa trên nội dung đã học.")
    lines.append(f"- Bài 3 (Nâng cao): Áp dụng hoặc liên hệ [{label}] vào một tình huống thực tế của bản thân.")
    lines.append("")
    short_slug = SHORT_SLUG_BY_PHASE[phase_num]
    lines.append(f"**Tags:** #tamlinh #day{global_day} #{short_slug} #{fslug}")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)

def main():
    out_path = "/mnt/user-data/outputs/roadmap_thien_thoimien_mentalism_daogiao_yoga_phatgiao.md"
    header_md = []
    header_md.append(f"# Thien - Thoi Mien - Mentalism - Dao Giao - Yoga Patanjali - Phat Giao Thien Dinh — Lo Trinh {TOTAL_DAYS} Ngay ({TOTAL_TOPICS} Chu De x 15 Ngay/Chu De)")
    header_md.append("> Muc tieu: Moi CHU DE CON THUC CHAT (vi du: MBSR, Body Scan, Cold Reading, Dao Duc Kinh, Vibhuti Pada, Tu Niem Xu...) duoc tach thanh MOT chu de rieng bang, moi chu de di het Chu Ky 15 Ngay chuan (Core Concept -> Lich su -> Deep Dive ly thuyet -> Van ban goc -> Ky thuat thuc hanh -> Co che khoa hoc/tam ly -> Sai lam thuong gap -> So sanh truong phai -> Ung dung thuc te -> Dao duc & gioi han -> Nhan vat/truong phai tieu bieu -> Tu thuc hanh tai tao -> Mini-Project 1/2/3).")
    header_md.append(f"> Ap dung cho 6 nhom noi dung: (1) Thien & Chanh niem ({len(PHASES[0][3])} chu de), (2) Thoi mien tri lieu ({len(PHASES[1][3])} chu de), (3) Mentalism ({len(PHASES[2][3])} chu de), (4) Dao giao ({len(PHASES[3][3])} chu de), (5) Yoga Patanjali ({len(PHASES[4][3])} chu de), (6) Phat giao Thien dinh & Luc thong ({len(PHASES[5][3])} chu de).")
    header_md.append("> Thoi luong: 30-60 phut/ngay.")
    header_md.append(f"> Tong: {TOTAL_TOPICS} chu de x 15 ngay = {TOTAL_DAYS} ngay.")
    header_md.append("")
    header_md.append("> Luu y quan trong: Cac noi dung ve thoi mien, thien dinh chuyen sau, hoac 'than thong/sieu nhien' (Siddhi, Luc Thong...) chi mang tinh tim hieu tri thuc - lich su - triet hoc, KHONG thay the tu van/dieu tri cua bac si tam ly, chuyen gia suc khoe tam than hoac giao tho co tham quyen. Phan 'Dao duc, Gioi han & Canh bao' o moi chu de can duoc doc ky truoc khi thuc hanh bat ky ky thuat nao lien quan den trang thai y thuc thay doi.")
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
