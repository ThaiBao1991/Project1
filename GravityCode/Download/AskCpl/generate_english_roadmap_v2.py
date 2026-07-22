# generate_english_roadmap_v2.py
import os

OUTPUT_FILEPATH = r"c:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\roadmap_english_2500_v2.md"

UNIT_DAYS = 7

def get_level_info(day_num):
    if day_num <= 200:
        return ("🟢", "Vỡ lòng/Pre-A1 — 30-45 phút", "pre_a1")
    elif day_num <= 550:
        return ("🟡", "Cơ bản/A1-A2 — 30-45 phút", "a1a2")
    elif day_num <= 950:
        return ("🟠", "Trung cấp/B1 — 30-45 phút", "b1")
    elif day_num <= 1450:
        return ("🟠", "Thượng cấp/B2 — 30-45 phút", "b2")
    elif day_num <= 2000:
        return ("🔴", "Cao cấp/C1-C2 — 30-45 phút", "c1c2")
    else:
        return ("🟣", "Bản địa/Near-Native — 30-45 phút", "native")

UNITS_PRE_A1 = [
    ("Gia đình & Người thân", "To be: am/is/are — Giới thiệu", "mother, father, sister, brother..."),
    ("Màu sắc & Hình dạng", "Adjectives: Tính từ mô tả", "red, blue, green..."),
    ("Số đếm & Thời gian", "Question Words", "one to twenty, Monday..."),
    ("Thời tiết & Mùa", "Simple Present: It is...", "sunny, rainy, cloudy..."),
    ("Đồ vật trong nhà", "There is / There are", "table, chair, bed..."),
    ("Thức ăn & Đồ uống", "Have / Has", "rice, bread, soup..."),
    ("Giao thông & Địa điểm", "Prepositions of Place", "bus, car, bicycle..."),
    ("Nghề nghiệp & Công việc", "Simple Present", "teacher, doctor..."),
    ("Cơ thể người & Sức khỏe", "Have got", "head, eyes, ears..."),
    ("Sở thích & Hoạt động", "Adverbs of Frequency", "read, watch, play..."),
    ("Mua sắm & Giá cả", "How much is it?", "shop, market, buy..."),
    ("Cảm xúc & Trạng thái", "Pronouns", "happy, sad, angry..."),
    ("Phát âm: Vowels", "Nouns: Singular & Plural", "IPA practice: /ɪ/ vs /iː/..."),
    ("Phát âm: Consonants", "Articles: a / an / the", "IPA practice: /θ/ vs /ð/..."),
    ("Du lịch & Khách sạn", "Can / Can't", "hotel, room, check in..."),
    ("Nhà hàng & Đặt món", "Imperatives", "menu, order, waiter..."),
    ("Phòng khám & Thuốc", "Should / Shouldn't", "doctor, nurse, medicine..."),
    ("Thiên nhiên & Động vật", "Simple Past: was/were", "forest, ocean, river..."),
    ("Giáo dục & Trường học", "Present Continuous", "school, teacher, student..."),
    ("Công nghệ cơ bản", "Simple Past: Regular verbs", "computer, phone..."),
    ("Lễ hội & Sự kiện", "Going to", "birthday, party, celebrate..."),
    ("Mô tả ngoại hình", "Adjective Order", "tall, short, slim..."),
    ("Phương hướng", "Question Words", "left, right, straight..."),
    ("Tổng ôn Pre-A1", "Review Phase 1", "Review"),
]

UNITS_A1A2 = [
    ("Du lịch & Đặt vé", "Simple Past + Past Continuous", "book, ticket, flight..."),
    ("Sở thích & Thể thao", "Present Perfect", "football, basketball..."),
    ("Mua sắm & Thời trang", "Comparative & Superlative", "clothes, fashion..."),
    ("Công việc & Phỏng vấn", "Modal Verbs: must/have to", "interview, resume..."),
    ("Nhà & Thuê nhà", "There is/are + Some/Any", "apartment, landlord..."),
    ("Nhà hàng", "Future will", "cuisine, recipe..."),
    ("Sức khỏe", "Gerunds & Infinitives", "diet, exercise..."),
    ("Công nghệ & MXH", "Passive Voice cơ bản", "social media, post..."),
    ("Môi trường", "Conditional 1", "climate change, pollution..."),
    ("Giải trí & Phim", "Reported Speech cơ bản", "movie, series..."),
    ("Mối quan hệ", "Question Tags", "friendship, relationship..."),
    ("Du lịch nội địa", "Present Perfect vs Simple Past", "resort, tour..."),
    ("Giáo dục", "Relative Clauses", "university, degree..."),
    ("Tài chính cá nhân", "Modal Verbs: might/could/would", "budget, savings..."),
    ("Thành phố", "Phrasal Verbs cơ bản", "city center, suburb..."),
    ("Nghề nghiệp", "So / Neither", "career, profession..."),
    ("Văn hóa ẩm thực", "Countable vs Uncountable", "specialty, cuisine..."),
    ("Thể thao", "Past Continuous", "match, score..."),
    ("Xã hội", "Passive Voice thì quá khứ", "protest, movement..."),
    ("Kỹ năng giao tiếp", "Conditional 2", "argument, persuade..."),
    ("Sức khỏe tâm thần", "Noun Clauses", "anxiety, depression..."),
    ("Tương lai", "Future Perfect", "artificial intelligence..."),
    ("Nấu ăn", "Gerunds as Subject", "recipe, chop..."),
    ("Gia đình", "Possessive Pronouns", "relationship, tradition..."),
    ("Tổng ôn A1-A2", "Review A1-A2", "Review"),
]

UNITS_B1 = [
    ("Môi trường", "Present Perfect Continuous", "sustainability..."),
    ("Khởi nghiệp", "Past Perfect", "entrepreneur..."),
    ("Khoa học", "Past Perfect Continuous", "hypothesis..."),
    ("Bất bình đẳng", "Future Perfect", "inequality..."),
    ("Tâm lý học", "Conditional 2 + Wish", "behavior..."),
    ("Văn hóa", "Participle Clauses", "culture, identity..."),
    ("Y tế", "Causative", "diagnosis..."),
    ("Giáo dục", "Wish + If only", "curriculum..."),
    ("Công nghệ & Quyền riêng tư", "Modal Verbs for Deduction", "data privacy..."),
    ("Kinh tế học", "Inversion", "inflation..."),
    ("Truyền thông", "Cleft Sentences", "journalism..."),
    ("Phượt", "Noun Clauses", "backpacker..."),
    ("Lối sống lành mạnh", "Ellipsis & Substitution", "fitness..."),
    ("Kiến trúc", "So/Such...that", "architecture..."),
    ("Luật pháp", "Conjunctions", "law, rights..."),
    ("Nghệ thuật", "Advanced Relative Clauses", "painting..."),
    ("Đầu tư", "Past Continuous", "stock market..."),
    ("Biến đổi khí hậu", "Passive Voice nâng cao", "global warming..."),
    ("Ngôn ngữ học", "Reported Speech nâng cao", "linguistics..."),
    ("Khởi nghiệp Tech", "Conditional 3", "venture capital..."),
    ("Tổng ôn B1", "Review B1", "Review"),
]

UNITS_B2 = [
    ("Chính sách công", "Advanced Conditionals", "policy..."),
    ("Tâm lý xã hội", "Subjunctive Mood", "conformity..."),
    ("Triết học", "Advanced Passives", "ethics..."),
    ("Kinh tế vĩ mô", "Nominalization", "macroeconomics..."),
    ("Khoa học & Tech", "Advanced Relative Clauses", "biotechnology..."),
    ("Truyền thông", "Fronting", "propaganda..."),
    ("Sức khỏe cộng đồng", "Ellipsis nâng cao", "epidemiology..."),
    ("Văn học", "Hedging Language", "narrative..."),
    ("Kinh doanh quốc tế", "Advanced Concession", "globalization..."),
    ("Lịch sử", "Cohesion & Coherence", "colonialism..."),
    ("Khởi nghiệp", "Register", "business model..."),
    ("Ngôn ngữ học ứng dụng", "Discourse Markers", "pragmatics..."),
    ("Công nghệ xanh", "Intensifiers", "carbon capture..."),
    ("Tâm lý học nhận thức", "Collocation", "cognitive load..."),
    ("Nghệ thuật", "Advanced Phrasal Verbs", "contemporary art..."),
    ("Tổng ôn B2", "Review B2", "Review"),
]

UNITS_C1C2 = [
    ("Triết học ngôn ngữ", "Advanced Inversion", "semiotics..."),
    ("Khoa học nhận thức & AI", "Cleft Sentences nâng cao", "machine learning..."),
    ("Kinh tế học hành vi", "Complex Nominalization", "behavioral economics..."),
    ("Viết luận", "Ellipsis & Substitution nâng cao", "thesis statement..."),
    ("Giáo dục toàn cầu", "Advanced Hedging", "educational equity..."),
    ("Văn học & Phong cách", "Discourse Analysis", "literary criticism..."),
    ("Đạo đức công nghệ", "Pragmatics", "algorithmic bias..."),
    ("Kinh tế học quốc tế", "Register shifts", "comparative advantage..."),
    ("Khoa học vật liệu", "Advanced Conditional Structures", "nanomaterials..."),
    ("Tâm lý học lâm sàng", "Stylistic Devices", "psychotherapy..."),
    ("Quan hệ quốc tế", "Complex Sentence Structures", "geopolitics..."),
    ("Văn học cổ điển", "Syntax Variation", "Shakespeare..."),
    ("Tổng ôn C1-C2", "Review C1-C2", "Review"),
]

UNITS_NATIVE = [
    ("Slang Mỹ", "Native Fluency Focus", "lit, vibe..."),
    ("Slang Anh", "Accent Mastery", "chuffed..."),
    ("Hài hước", "Stand-up Comedy Structure", "irony, sarcasm..."),
    ("Văn học Orwell", "Advanced Literary Analysis", "dystopia..."),
    ("Podcast", "Transcription & Critical Listening", "narrative journalism..."),
    ("Thương thuyết", "Business English", "pitch deck..."),
    ("Thuyết trình", "Public Speaking Techniques", "hook, thesis..."),
    ("Viết học thuật", "Academic Writing", "abstract..."),
    ("Phân tích phim", "Cultural Competence", "subtext..."),
    ("Tổng ôn Native", "Near-Native Mastery Review", "Review"),
]

def build_roadmap_v2():
    roadmap = {}
    day = 1

    def add_unit(units_list, phase_name, start_day, end_day):
        nonlocal day
        unit_in_phase = 0
        while day <= end_day:
            unit_data = units_list[unit_in_phase % len(units_list)]
            vocab_topic, grammar_point, vocab_hint = unit_data
            unit_num_global = (day - start_day) // UNIT_DAYS + 1

            for day_in_unit in range(1, UNIT_DAYS + 1):
                if day > end_day:
                    break
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

    add_unit(UNITS_PRE_A1, "Phase 1: Vỡ lòng & Nền tảng Phát âm (Day 1-200)", 1, 200)
    add_unit(UNITS_A1A2, "Phase 2: A1-A2 & Giao tiếp Cơ bản (Day 201-550)", 201, 550)
    add_unit(UNITS_B1, "Phase 3: B1 & Tiếng Anh Trung cấp (Day 551-950)", 551, 950)
    add_unit(UNITS_B2, "Phase 4: B2 & Tiếng Anh Thượng cấp (Day 951-1450)", 951, 1450)
    add_unit(UNITS_C1C2, "Phase 5: C1-C2 & Học thuật Cao cấp (Day 1451-2000)", 1451, 2000)
    add_unit(UNITS_NATIVE, "Phase 6: Near-Native & Chuyên gia (Day 2001-2500)", 2001, 2500)

    return roadmap

def get_day_title_and_prompt(day_num, data):
    day_in_unit = data["day_in_unit"]
    vocab_topic = data["vocab_topic"]
    grammar_point = data["grammar_point"]
    vocab_hint = data["vocab_hint"]
    phase = data["phase"]
    unit_num = data["unit_num"]
    emoji, label, lvl_code = get_level_info(day_num)

    day_roles = {
        1: ("Vocab Foundation", "📚"),
        2: ("Grammar Deep Dive", "📐"),
        3: ("Pronunciation Drill", "🎙️"),
        4: ("Reading Immersion", "📖"),
        5: ("Listening Immersion", "🎧"),
        6: ("Speaking Practice", "💬"),
        7: ("Review & Mini Test", "✅"),
    }
    role_name, role_emoji = day_roles[day_in_unit]
    title = f"[Unit {unit_num}·Day {day_in_unit}/7] {role_emoji} {role_name} — Chủ đề: {vocab_topic}"

    if day_in_unit == 1:
        prompt = f"Đóng vai Gia sư tiếng Anh. Hôm nay là Day {day_num} — Ngày 1/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\n1. Hãy dạy 15-20 từ vựng cốt lõi về '{vocab_topic}'.\n- Gợi ý: {vocab_hint}.\n- Phải có định nghĩa, IPA, ví dụ thực tế.\n\n2. Dạy điểm ngữ pháp: {grammar_point}.\n⚠️ Bắt buộc dùng từ vựng vừa dạy ở mục 1 làm ví dụ cho phần ngữ pháp này."
    elif day_in_unit == 2:
        prompt = f"Đóng vai Gia sư tiếng Anh. Hôm nay là Day {day_num} — Ngày 2/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nDạy chuyên sâu ngữ pháp: {grammar_point}.\n⚠️ Bắt buộc: Tất cả ví dụ và bài tập thực hành phải nhúng từ vựng chủ đề '{vocab_topic}' đã học hôm qua. Đưa ra bài tập sửa lỗi thường gặp của người Việt (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
    elif day_in_unit == 3:
        prompt = f"Đóng vai Gia sư tiếng Anh. Hôm nay là Day {day_num} — Ngày 3/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nLuyện phát âm chuyên sâu dựa trên các từ vựng chủ đề '{vocab_topic}'. Chỉ ra các lỗi phát âm (IPA) người Việt hay mắc (ví dụ thiếu âm đuôi, đọc sai âm tiết). Cung cấp 5 câu shadowing có nhúng từ vựng này."
    elif day_in_unit == 4:
        prompt = f"Đóng vai Gia sư tiếng Anh. Hôm nay là Day {day_num} — Ngày 4/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nCung cấp 1 bài đọc (150-250 từ) về '{vocab_topic}' có chứa TỰ NHIÊN ít nhất 10 từ vựng cốt lõi của Unit này. Sau đó đưa ra 3 câu hỏi đọc hiểu và 1 câu hỏi tư duy (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
    elif day_in_unit == 5:
        prompt = f"Đóng vai Gia sư tiếng Anh. Hôm nay là Day {day_num} — Ngày 5/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nTạo 1 script bài nghe (hội thoại hoặc podcast) về '{vocab_topic}', nhúng ít nhất 10 từ vựng Unit. Đánh dấu các âm nối (connected speech) hoặc âm lướt. Kèm 3 câu hỏi bài tập nghe (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
    elif day_in_unit == 6:
        prompt = f"Đóng vai Gia sư tiếng Anh. Hôm nay là Day {day_num} — Ngày 6/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nCung cấp 3 tình huống giao tiếp mẫu (Role-play) dạng đoạn hội thoại hoàn chỉnh (song ngữ Anh-Việt) về chủ đề '{vocab_topic}'. Trong đó bắt buộc áp dụng ngữ pháp {grammar_point} và từ vựng Unit này để tôi tự luyện nói (Shadowing)."
    else:
        prompt = f"Đóng vai Gia sư tiếng Anh. Hôm nay là Day {day_num} — Ngày 7/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nÔn tập tổng hợp Unit {unit_num} (Chủ đề: {vocab_topic}, Ngữ pháp: {grammar_point}). Hãy tổng kết nhanh lại, sau đó cho 1 bài test nhỏ 4 phần (Từ vựng, Ngữ pháp, Đọc, Viết) xoay quanh chủ đề này (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."

    return title, prompt, emoji, label, lvl_code

def generate_markdown_v2(roadmap_data):
    total = len(roadmap_data)
    md_lines = [
        "# 🇬🇧 Lộ Trình Học Tiếng Anh – 2500 Ngày V2 (Unit-based Learning)",
        "",
        "> ⚠️ **V2 — Unit-based Learning**: Mỗi 7 ngày = 1 Unit học sâu theo 1 chủ đề.",
        "> Từ vựng cốt lõi học ở Ngày 1 sẽ xuất hiện xuyên suốt trong bài Đọc, Nghe, Nói của cả tuần.",
        "",
        "> **Quy tắc Roadmap Markdown:** Mỗi ngày bắt đầu bằng `## Day X`. Yêu cầu gửi AI được đặt dưới `**Prompt:**`. Bài tập tự luyện đặt dưới `**Bài tập:**`",
        ""
    ]

    for day_num in range(1, total + 1):
        if day_num not in roadmap_data:
            continue
        data = roadmap_data[day_num]
        title, prompt, emoji, label, lvl_code = get_day_title_and_prompt(day_num, data)
        unit_num = data["unit_num"]
        day_in_unit = data["day_in_unit"]

        md_lines.append(f"## Day {day_num} — {title}")
        md_lines.append("**Prompt:**")
        md_lines.append(prompt)
        md_lines.append("")
        md_lines.append("**Bài tập:**")
        md_lines.append(f"⏱️ **Thời gian:** {label}")
        md_lines.append(f"📌 **Unit {unit_num} | Ngày {day_in_unit}/7 | Chủ đề:** {data['vocab_topic']}")
        md_lines.append(f"💻 **Tự luyện:** Hoàn thành bài tập do AI giao, nộp lại để được chấm điểm.")
        md_lines.append("")
        md_lines.append(f"**Tags:** #english_v2 #day{day_num} #{lvl_code} #unit{unit_num}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    with open(OUTPUT_FILEPATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"✅ Done! V2 generated: {OUTPUT_FILEPATH}")

if __name__ == "__main__":
    data = build_roadmap_v2()
    generate_markdown_v2(data)
