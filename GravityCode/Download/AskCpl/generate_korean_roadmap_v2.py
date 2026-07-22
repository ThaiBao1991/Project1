# generate_korean_roadmap_v2.py
import os

OUTPUT_FILEPATH = r"c:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\roadmap_korean_2500_v2.md"
UNIT_DAYS = 7

def get_level_info(day_num):
    if day_num <= 250:
        return ("🟢", "Vỡ lòng/TOPIK 1 — 30-45 phút", "topik1")
    elif day_num <= 600:
        return ("🟡", "Cơ bản/TOPIK 2 — 30-45 phút", "topik2")
    elif day_num <= 1000:
        return ("🟠", "Trung cấp/TOPIK 3 — 30-45 phút", "topik3")
    elif day_num <= 1500:
        return ("🟠", "Trung cao cấp/TOPIK 4 — 30-45 phút", "topik4")
    elif day_num <= 2000:
        return ("🔴", "Cao cấp/TOPIK 5 — 30-45 phút", "topik5")
    elif day_num <= 2400:
        return ("🔴", "Chuyên gia/TOPIK 6 — 30-45 phút", "topik6")
    else:
        return ("🟣", "Bản địa/Native — 30-45 phút", "native")

UNITS_TOPIK1 = [
    ("Gia đình & Chào hỏi", "입니다 / 입니까?", "가족, 저, 네, 아니요..."),
    ("Đồ vật & Vị trí", "이/가 있습니다/없습니다", "책, 책상, 위, 아래..."),
    ("Thời gian & Số đếm (Hán)", "N은/는 N입니다", "오늘, 내일, 일, 이..."),
    ("Thời gian & Số đếm (Thuần)", "Từ chỉ thời gian (에)", "하나, 둘, 시, 분..."),
    ("Mua sắm & Ăn uống", "V/A -아/어요", "사다, 먹다, 마시다..."),
    ("Giao thông & Đi lại", "N을/를 V", "타다, 가다, 오다, 버스..."),
    ("Sở thích & Cuối tuần", "V-(으)ㄹ 거예요", "주말, 영화, 보다, 하다..."),
    ("Thời tiết", "A-습니다/ㅂ니다", "날씨, 좋다, 나쁘다..."),
    ("Tổng ôn TOPIK 1", "Ôn tập TOPIK 1", "Review")
]

UNITS_TOPIK2 = [
    ("Sức khỏe & Cơ thể", "V-고 싶다 (Muốn)", "아프다, 병원, 약..."),
    ("Lịch trình & Kế hoạch", "V-(으)ㄹ 수 있다/없다", "계획, 회의, 만나다..."),
    ("Kinh nghiệm", "V-아/어 봤다", "여행, 한복, 불고기..."),
    ("Lý do & Nguyên nhân", "A/V-아/어서", "늦다, 바쁘다, 그래서..."),
    ("Phòng ốc & Nhà cửa", "N에서 N까지", "방, 이사, 멀다..."),
    ("Mối quan hệ bạn bè", "V-고 (Và)", "친구, 사귀다, 약속..."),
    ("Yêu cầu & Mệnh lệnh", "V-(으)세요", "주다, 돕다, 기다리다..."),
    ("Đề nghị & Rủ rê", "V-(으)ㄹ까요?", "같이, 식당, 영화관..."),
    ("Tình trạng & Sự thay đổi", "A-아/어지다", "추워지다, 좋아지다..."),
    ("Tổng ôn TOPIK 2", "Ôn tập TOPIK 2", "Review")
]

UNITS_TOPIK3 = [
    ("Công sở & Công ty", "V-기 때문에", "회사, 출근, 퇴근, 서류..."),
    ("Văn hóa & Đời sống", "V-는지 알다/모르다", "전통, 예절, 한옥..."),
    ("Giải trí & Truyền thông", "V-(으)면서", "방송, 드라마, 연예인..."),
    ("Kinh tế & Mua sắm", "V-거나 / N(이)나", "할인, 영수증, 교환..."),
    ("Giáo dục & Đại học", "V-(으)면 좋겠다", "대학교, 전공, 등록금..."),
    ("Thể thao & Sức khỏe", "A/V-(으)ㄹ 텐데", "운동, 다이어트, 스트레스..."),
    ("Môi trường", "A/V-(으)ㄹ 뿐만 아니라", "환경, 오염, 쓰레기..."),
    ("Kỹ năng xã hội", "V-기 위해(서)", "인간관계, 대화, 성격..."),
    ("Tổng ôn TOPIK 3", "Ôn tập TOPIK 3", "Review")
]

UNITS_TOPIK4 = [
    ("Xã hội & Luật pháp", "V-다시피", "법, 규칙, 위반..."),
    ("Tâm lý & Suy nghĩ", "A/V-(으)ㄹ 리가 없다", "불안, 기대, 우울..."),
    ("Khoa học & Kỹ thuật", "N에 따라(서)", "기술, 발명, 스마트폰..."),
    ("Thương mại & Kinh doanh", "V-는 바람에", "수출, 수입, 계약..."),
    ("Văn học & Nghệ thuật", "A/V-(으)ㄴ/는 셈이다", "문학, 작가, 감상..."),
    ("Lịch sử & Truyền thống", "V-자마자", "역사, 유적지, 왕..."),
    ("Giáo dục & Đánh giá", "A/V-더라도", "평가, 목표, 향상..."),
    ("Y tế & Công cộng", "V-(으)ㄹ 뻔하다", "의료, 보험, 진료..."),
    ("Tổng ôn TOPIK 4", "Ôn tập TOPIK 4", "Review")
]

UNITS_TOPIK5 = [
    ("Kinh tế vĩ mô", "V-(으)로 말미암아", "거시경제, 인플레이션..."),
    ("Chính trị & Ngoại giao", "A/V-건만", "외교, 선거, 갈등..."),
    ("Triết học & Hiện tượng", "V-기 일쑤이다", "철학, 이념, 본질..."),
    ("Công nghệ sinh học", "V-는 한편", "유전자, 배양, 윤리..."),
    ("Tâm lý xã hội", "A/V-(으)ㄹ 지경이다", "군중심리, 차별, 소외..."),
    ("Báo chí & Dư luận", "V-기 십상이다", "보도, 여론, 편파..."),
    ("Thương mại quốc tế", "N에 비추어", "무역, 협정, 관세..."),
    ("Văn hóa đại chúng", "A/V-(으)련만", "대중문화, 한류, 파급력..."),
    ("Tổng ôn TOPIK 5", "Ôn tập TOPIK 5", "Review")
]

UNITS_TOPIK6_NATIVE = [
    ("Văn bản hành chính", "Ngữ pháp TOPIK 6", "기안서, 규정, 시행..."),
    ("Báo cáo chuyên sâu", "Cấu trúc luận văn", "분석, 통계, 입증..."),
    ("Tiếng lóng & Gen Z", "Từ lóng Hàn Quốc", "대박, 헐, 인싸..."),
    ("Quán dụng ngữ (Idioms)", "Quán dụng ngữ", "발이 넓다, 귀가 얇다..."),
    ("Bốn chữ Hán (Saja-seongea)", "사자성어", "일석이조, 동문서답..."),
    ("Tin tức thời sự", "Đọc tin tức", "보도자료, 성명, 앵커..."),
    ("Thương thuyết & Đàm phán", "Ngữ điệu doanh nghiệp", "절충, 타결, 전략..."),
    ("Tổng ôn Cao cấp", "Mastery Review", "Review")
]

def build_roadmap_v2():
    roadmap = {}
    day = 1

    # Days 1-22: Hangul Intro
    hangul_intro = [
        "Lịch sử Hangul & Nguyên âm đơn (ㅏ, ㅑ, ㅓ, ㅕ, ㅗ, ㅛ, ㅜ, ㅠ, ㅡ, ㅣ)",
        "Phụ âm cơ bản (ㄱ, ㄴ, ㄷ, ㄹ, ㅁ, ㅂ, ㅅ, ㅇ, ㅈ, ㅊ, ㅋ, ㅌ, ㅍ, ㅎ)",
        "Ghép âm: Phụ âm + Nguyên âm đơn (가, 나, 다...)",
        "Nguyên âm kép (ㅐ, ㅒ, ㅔ, ㅖ, ㅘ, ㅙ, ㅚ, ㅝ, ㅞ, ㅟ, ㅢ)",
        "Phụ âm căng (ㄲ, ㄸ, ㅃ, ㅆ, ㅉ)",
        "Ghép âm: Phụ âm căng & Phụ âm bật hơi + Nguyên âm kép",
        "Batchim (Phụ âm cuối) cơ bản (ㄱ, ㄴ, ㄷ, ㄹ, ㅁ, ㅂ, ㅇ)",
        "Batchim kép (ㄳ, ㄵ, ㄶ, ㄺ, ㄻ, ㄼ, ㄽ, ㄾ, ㄿ, ㅀ, ㅄ)",
        "Quy tắc phát âm: Nối âm (연음 법칙)",
        "Quy tắc phát âm: Biến âm cơ bản (Mũi hóa)",
        "Quy tắc phát âm: Trọng âm & Âm bật hơi hóa",
        "Luyện đọc Hangul: Đọc từ vựng cơ bản",
        "Luyện viết Hangul: Thứ tự nét bút",
        "Từ vựng nhập môn: Chào hỏi cơ bản (안녕하세요)",
        "Từ vựng nhập môn: Số đếm Thuần Hàn (하나, 둘, 셋)",
        "Từ vựng nhập môn: Số đếm Hán Hàn (일, 이, 삼)",
        "Từ vựng nhập môn: Ngày tháng, thứ trong tuần",
        "Từ vựng nhập môn: Giới thiệu bản thân",
        "Luyện gõ Hangul trên điện thoại/máy tính",
        "Ôn tập Nhập môn 1",
        "Ôn tập Nhập môn 2",
        "Bài test Nhập môn Hangul"
    ]

    for t in hangul_intro:
        roadmap[day] = {"intro_title": t, "phase": "Phase 0: Nhập môn (Day 1-22)"}
        day += 1

    def add_unit(units_list, phase_name, start_day, end_day):
        nonlocal day
        unit_in_phase = 0
        while day <= end_day:
            unit_data = units_list[unit_in_phase % len(units_list)]
            vocab_topic, grammar_point, vocab_hint = unit_data

            for day_in_unit in range(1, UNIT_DAYS + 1):
                if day > end_day: break
                roadmap[day] = {
                    "unit_num": unit_in_phase + 1,
                    "day_in_unit": day_in_unit,
                    "vocab_topic": vocab_topic,
                    "grammar_point": grammar_point,
                    "vocab_hint": vocab_hint,
                    "phase": phase_name,
                }
                day += 1
            unit_in_phase += 1

    add_unit(UNITS_TOPIK1, "Phase 1: TOPIK 1 (Day 23-250)", 23, 250)
    add_unit(UNITS_TOPIK2, "Phase 2: TOPIK 2 (Day 251-600)", 251, 600)
    add_unit(UNITS_TOPIK3, "Phase 3: TOPIK 3 (Day 601-1000)", 601, 1000)
    add_unit(UNITS_TOPIK4, "Phase 4: TOPIK 4 (Day 1001-1500)", 1001, 1500)
    add_unit(UNITS_TOPIK5, "Phase 5: TOPIK 5 (Day 1501-2000)", 1501, 2000)
    add_unit(UNITS_TOPIK6_NATIVE, "Phase 6: TOPIK 6 & Native (Day 2001-2500)", 2001, 2500)

    return roadmap

def get_day_title_and_prompt(day_num, data):
    if "intro_title" in data:
        emoji, label, lvl_code = get_level_info(day_num)
        title = data["intro_title"]
        prompt = f"Đóng vai Gia sư Tiếng Hàn. Hôm nay là Day {day_num} — {title}. Trình độ: Nhập môn.\n\nHãy dạy nội dung: {title}. Cung cấp bài tập thực hành (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
        return f"Day {day_num} — [Nhập môn] {title}", prompt, emoji, label, lvl_code

    day_in_unit = data["day_in_unit"]
    vocab_topic = data["vocab_topic"]
    grammar_point = data["grammar_point"]
    vocab_hint = data["vocab_hint"]
    unit_num = data["unit_num"]
    emoji, label, lvl_code = get_level_info(day_num)

    day_roles = {
        1: ("Vocab Foundation", "📚"),
        2: ("Grammar Deep Dive", "📐"),
        3: ("Pronunciation & Hanja", "⛩️"),
        4: ("Reading Immersion", "📖"),
        5: ("Listening Immersion", "🎧"),
        6: ("Speaking Practice", "💬"),
        7: ("Review & Mini Test", "✅"),
    }
    role_name, role_emoji = day_roles[day_in_unit]
    title = f"Day {day_num} — [Unit {unit_num}·Day {day_in_unit}/7] {role_emoji} {role_name} — {vocab_topic}"

    if day_in_unit == 1:
        prompt = f"Đóng vai Gia sư Tiếng Hàn. Hôm nay là Day {day_num} — Ngày 1/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\n1. Hãy dạy 15-20 từ vựng cốt lõi về '{vocab_topic}'.\n- Gợi ý: {vocab_hint}.\n- Phải có Hangeul, phiên âm chuẩn, Hán Hàn (nếu có), định nghĩa và ví dụ thực tế.\n\n2. Dạy điểm ngữ pháp: {grammar_point}.\n⚠️ Bắt buộc dùng từ vựng vừa dạy làm ví dụ cho phần ngữ pháp này."
    elif day_in_unit == 2:
        prompt = f"Đóng vai Gia sư Tiếng Hàn. Hôm nay là Day {day_num} — Ngày 2/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nDạy chuyên sâu ngữ pháp: {grammar_point}.\n⚠️ Bắt buộc: Tất cả ví dụ và bài tập thực hành phải nhúng từ vựng chủ đề '{vocab_topic}' đã học hôm qua. Đưa ra bài tập phân biệt ngữ pháp hoặc chia đuôi câu (아/어요, 습니다) (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
    elif day_in_unit == 3:
        prompt = f"Đóng vai Gia sư Tiếng Hàn. Hôm nay là Day {day_num} — Ngày 3/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nLuyện phát âm chuyên sâu dựa trên các từ vựng chủ đề '{vocab_topic}'. Chỉ ra quy tắc biến âm (nối âm, mũi hóa, bật hơi) cho các từ này. Mở rộng 3-5 gốc từ Hán Hàn (Hanja) liên quan."
    elif day_in_unit == 4:
        prompt = f"Đóng vai Gia sư Tiếng Hàn. Hôm nay là Day {day_num} — Ngày 4/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nCung cấp 1 bài đọc (150-250 chữ) về '{vocab_topic}' có chứa TỰ NHIÊN ngữ pháp {grammar_point} và từ vựng Unit này. Đưa ra 3 câu hỏi đọc hiểu (Kiểu TOPIK 읽기) (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
    elif day_in_unit == 5:
        prompt = f"Đóng vai Gia sư Tiếng Hàn. Hôm nay là Day {day_num} — Ngày 5/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nTạo 1 script bài nghe (hội thoại/podcast) về '{vocab_topic}', nhúng từ vựng Unit. Nhấn mạnh vào ngữ điệu và biểu hiện cảm xúc. Kèm 3 câu hỏi bài tập nghe (Kiểu TOPIK 듣기) (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
    elif day_in_unit == 6:
        prompt = f"Đóng vai Gia sư Tiếng Hàn. Hôm nay là Day {day_num} — Ngày 6/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nCung cấp 3 tình huống giao tiếp mẫu (Role-play) dạng đoạn hội thoại hoàn chỉnh (song ngữ Hàn-Việt) về chủ đề '{vocab_topic}'. Trong đó bắt buộc áp dụng ngữ pháp {grammar_point} và từ vựng Unit này để tôi tự luyện nói (Shadowing). Phân biệt rõ văn nói (반말) và văn lịch sự (존댓말)."
    else:
        prompt = f"Đóng vai Gia sư Tiếng Hàn. Hôm nay là Day {day_num} — Ngày 7/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nÔn tập tổng hợp Unit {unit_num} (Chủ đề: {vocab_topic}, Ngữ pháp: {grammar_point}). Cho 1 bài test TOPIK mini gồm 4 phần (Từ vựng, Ngữ pháp, Đọc, Viết) (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."

    return title, prompt, emoji, label, lvl_code

def generate_markdown_v2(roadmap_data):
    total = len(roadmap_data)
    md_lines = [
        "# 🇰🇷 Lộ Trình Học Tiếng Hàn – 2500 Ngày V2 (Unit-based Learning)",
        "",
        "> ⚠️ **V2 — Unit-based Learning**: Mỗi 7 ngày = 1 Unit học sâu theo 1 chủ đề.",
        "> Tích hợp học từ vựng, ngữ pháp xoay quanh cùng một văn cảnh giúp nhớ lâu hơn.",
        "",
        "> **Quy tắc Roadmap Markdown:** Mỗi ngày bắt đầu bằng `## Day X`. Yêu cầu gửi AI được đặt dưới `**Prompt:**`. Bài tập tự luyện đặt dưới `**Bài tập:**`",
        ""
    ]

    for day_num in range(1, total + 1):
        if day_num not in roadmap_data:
            continue
        data = roadmap_data[day_num]
        title, prompt, emoji, label, lvl_code = get_day_title_and_prompt(day_num, data)
        
        md_lines.append(f"## {title}")
        md_lines.append("**Prompt:**")
        md_lines.append(prompt)
        md_lines.append("")
        md_lines.append("**Bài tập:**")
        md_lines.append(f"⏱️ **Thời gian:** {label}")
        if "unit_num" in data:
            md_lines.append(f"📌 **Unit {data['unit_num']} | Ngày {data['day_in_unit']}/7 | Chủ đề:** {data['vocab_topic']}")
        md_lines.append(f"💻 **Tự luyện:** Hoàn thành bài tập do AI giao, nộp lại để được chấm điểm.")
        md_lines.append("")
        if "unit_num" in data:
            md_lines.append(f"**Tags:** #korean_v2 #day{day_num} #{lvl_code} #unit{data['unit_num']}")
        else:
            md_lines.append(f"**Tags:** #korean_v2 #day{day_num} #{lvl_code} #intro")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    with open(OUTPUT_FILEPATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"✅ Done! V2 generated: {OUTPUT_FILEPATH}")

if __name__ == "__main__":
    data = build_roadmap_v2()
    generate_markdown_v2(data)
