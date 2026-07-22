# generate_japanese_roadmap_v2.py
import os

OUTPUT_FILEPATH = r"c:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\roadmap_japanese_2500_v2.md"
UNIT_DAYS = 7

def get_level_info(day_num):
    if day_num <= 250:
        return ("🟢", "Vỡ lòng/N5 — 30-45 phút", "n5")
    elif day_num <= 600:
        return ("🟡", "Cơ bản/N4 — 30-45 phút", "n4")
    elif day_num <= 1000:
        return ("🟠", "Trung cấp/N3 — 30-45 phút", "n3")
    elif day_num <= 1500:
        return ("🟠", "Thượng cấp/N2 — 30-45 phút", "n2")
    elif day_num <= 2000:
        return ("🔴", "Cao cấp/N1 — 30-45 phút", "n1")
    else:
        return ("🟣", "Bản địa/Native — 30-45 phút", "native")

UNITS_N5 = [
    ("Gia đình & Bản thân", "N1 は N2 です (Giới thiệu)", "家族, 私, 父, 母..."),
    ("Màu sắc & Hình dạng", "Tính từ đuôi い/な cơ bản", "赤, 青, 白, 丸い..."),
    ("Số đếm & Thời gian", "Từ để hỏi (何, いつ)", "一, 二, 時間, 月..."),
    ("Đồ vật trong nhà", "これ/それ/あれ", "机, 椅子, テレビ..."),
    ("Thức ăn & Đồ uống", "Động từ dạng ます", "食べる, 飲む, 水..."),
    ("Giao thông & Địa điểm", "Trợ từ に, で, へ", "電車, 車, 駅, 行く..."),
    ("Sở thích & Hoạt động", "Trợ từ を", "本, 映画, 見る, 読む..."),
    ("Mua sắm & Giá cả", "いくらですか", "買う, 店, お金..."),
    ("Tồn tại", "あります / います", "猫, 犬, 公園, ある..."),
    ("Lời mời & Đề nghị", "～ましょう / ～ませんか", "一緒, 行く, 食べる..."),
    ("Thời tiết", "Quá khứ của Tính từ", "天気, 晴れ, 雨..."),
    ("Du lịch & Khách sạn", "Thể て (Đang làm gì)", "ホテル, 泊まる, 旅行..."),
    ("Sức khỏe & Cơ thể", "～たいです (Muốn làm gì)", "痛い, 頭, 手, 薬..."),
    ("Phương hướng", "Từ chỉ vị trí (上, 下, 前)", "右, 左, 道..."),
    ("Lễ hội Nhật Bản", "Động từ Thể た (Đã từng)", "祭り, 桜, 花見..."),
    ("Tổng ôn N5", "Ôn tập tổng hợp N5", "Review")
]

UNITS_N4 = [
    ("Du lịch & Đặt vé", "Thể Khả năng (可能形)", "予約, 切符, 飛行機..."),
    ("Giao tiếp hằng ngày", "Thể Ý định (意向形)", "計画, 思う, 準備..."),
    ("Công việc part-time", "Thể Mệnh lệnh & Cấm chỉ", "アルバイト, 働く, 禁止..."),
    ("Nhà & Thuê nhà", "～ほうがいい (Nên/Không nên)", "アパート, 借りる, 家賃..."),
    ("Cho & Nhận", "あげる / もらう / くれる", "プレゼント, 渡す, 受け取る..."),
    ("Dự định & Kế hoạch", "～つもりです", "将来, 予定, 会議..."),
    ("Sức khỏe & Bệnh viện", "～ば (Câu điều kiện ば)", "病院, 医者, 治る..."),
    ("Công nghệ cơ bản", "Thể Bị động (受身形)", "パソコン, スマホ, 壊れる..."),
    ("Môi trường", "～てしまう (Lỡ/Hoàn thành)", "ゴミ, 捨てる, 環境..."),
    ("Giao tiếp xã hội", "Thể Sai khiến (使役形)", "社長, 意見, 話す..."),
    ("Truyền đạt thông tin", "～そうです (Nghe nói)", "ニュース, 天気予報, 事故..."),
    ("Thói quen", "～ようにしています", "運動, 毎日, 習慣..."),
    ("Tổng ôn N4", "Ôn tập tổng hợp N4", "Review")
]

UNITS_N3 = [
    ("Công sở & Công ty", "Kính ngữ cơ bản (Tôn kính ngữ)", "敬語, 上司, 面接..."),
    ("Công sở & Giao dịch", "Khiêm nhường ngữ", "取引先, 参る, 拝見する..."),
    ("Mối quan hệ", "～おかげで / ～せいで", "友達, 恋人, 関係..."),
    ("Giáo dục & Đại học", "～について / ～に関して", "大学, 論文, 教授..."),
    ("Tài chính cá nhân", "～かわりに", "貯金, 節約, 投資..."),
    ("Thành phố & Xã hội", "～たびに", "都会, 田舎, 変化..."),
    ("Nghề nghiệp & Ước mơ", "～はずがない", "職業, 夢, 努力..."),
    ("Văn hóa & Ẩm thực", "～うちに", "和食, 文化, 経験..."),
    ("Thể thao & Giải trí", "～最中に", "試合, 応援, 選手..."),
    ("Cảm xúc & Tâm lý", "～てたまらない", "感動, 寂しい, 嬉しい..."),
    ("Môi trường & Rác thải", "～だらけ", "リサイクル, 汚染, 地球..."),
    ("Giao tiếp & Mạng xã hội", "～っぽい", "SNS, 情報, 共有..."),
    ("Tổng ôn N3", "Ôn tập tổng hợp N3", "Review")
]

UNITS_N2 = [
    ("Kinh tế & Kinh doanh", "～に際して / ～にあたって", "景気, 経営, 利益..."),
    ("Chính trị & Xã hội", "～を問わず", "選挙, 政策, 権利..."),
    ("Khoa học & Kỹ thuật", "～にかかわらず", "技術, 開発, 実験..."),
    ("Tâm lý học", "～からいうと / ～から見ると", "心理, 感情, 影響..."),
    ("Nghệ thuật & Kiến trúc", "～にほかならない", "作品, 建築, 展覧会..."),
    ("Luật pháp & Tội phạm", "～ざるを得ない", "法律, 裁判, 犯罪..."),
    ("Y tế & Dịch bệnh", "～つつある", "治療, 症状, 医療..."),
    ("Môi trường & Biến đổi", "～に伴って / ～とともに", "温暖化, 対策, 現象..."),
    ("Giáo dục & Tư duy", "～っこない", "思考, 制度, 評価..."),
    ("Lịch sử & Truyền thống", "～を通じて", "歴史, 伝統, 時代..."),
    ("Văn học & Ngôn ngữ", "～一方だ", "表現, 文学, 翻訳..."),
    ("Tổng ôn N2", "Ôn tập tổng hợp N2", "Review")
]

UNITS_N1 = [
    ("Kinh tế vĩ mô", "～いかんによらず", "マクロ経済, 金融緩和..."),
    ("Triết học & Tư tưởng", "～と相まって", "哲学, 概念, 倫理..."),
    ("Ngoại giao & Quốc tế", "～を皮切りに", "外交, 条約, 紛争..."),
    ("Công nghệ tương lai", "～きらいがある", "人工知能, イノベーション..."),
    ("Văn hóa đại chúng", "～がてら", "ポップカルチャー, 消費..."),
    ("Y học lâm sàng", "～にかまけて", "臨床, 免疫, 遺伝子..."),
    ("Kinh tế học hành vi", "～にもまして", "行動経済学, バイアス..."),
    ("Pháp lý quốc tế", "～たところで", "国際法, 規制, 訴訟..."),
    ("Tổng ôn N1", "Ôn tập tổng hợp N1", "Review")
]

UNITS_NATIVE = [
    ("Tiếng lóng & Gen Z", "Từ vựng giới trẻ", "エモい, 草, 映える..."),
    ("Kính ngữ nâng cao", "Email doanh nghiệp chuẩn", "ご査収の程, 何卒..."),
    ("Thành ngữ & Yojijukugo", "四字熟語", "一期一会, 自業自得..."),
    ("Văn hóa doanh nghiệp", "Báo cáo, Liên lạc, Bàn bạc", "報連相 (ホウレンソウ)..."),
    ("Phương ngữ (Kansai-ben)", "Kansai-ben cơ bản", "なんでやねん, ほんま..."),
    ("Thuyết trình chuyên nghiệp", "Kỹ năng Present", "プレゼン, 質疑応答..."),
    ("Tin tức & Báo chí", "Đọc báo Yomiuri/Asahi", "社説, コラム..."),
    ("Văn học cận đại", "Đọc Natsume Soseki", "吾輩は猫である..."),
    ("Tổng ôn Native", "Native Mastery Review", "Review")
]

def build_roadmap_v2():
    roadmap = {}
    day = 1

    # Days 1-22: Hiragana & Katakana Intro
    hira_kata = [
        "Hiragana: あ-お, か-こ", "Hiragana: さ-そ, た-と", "Hiragana: な-の, は-ほ",
        "Hiragana: ま-も, や-よ, ら-ろ, わ-を-ん", "Hiragana: Âm đục, Âm ghép",
        "Katakana: ア-オ, カ-コ", "Katakana: サ-ソ, タ-ト", "Katakana: ナ-ノ, ハ-ホ",
        "Katakana: マ-モ, ヤ-ヨ, ラ-ロ, ワ-ヲ-ン", "Katakana: Âm ngoại lai, Trường âm",
        "Quy tắc phát âm, Pitch Accent", "Từ vựng: Chào hỏi (Aisatsu)",
        "Từ vựng: Số đếm 1-100", "Từ vựng: Ngày tháng năm", "Giới thiệu bản thân (Jikoshoukai)",
        "Kanji cơ bản: Ngày trong tuần", "Kanji cơ bản: Số đếm", "Ôn tập Nhập môn 1",
        "Ôn tập Nhập môn 2", "Ôn tập Nhập môn 3", "Bài kiểm tra cuối khóa Nhập môn",
        "Định hướng học JLPT N5"
    ]
    for t in hira_kata:
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

    add_unit(UNITS_N5, "Phase 1: N5 (Day 23-250)", 23, 250)
    add_unit(UNITS_N4, "Phase 2: N4 (Day 251-600)", 251, 600)
    add_unit(UNITS_N3, "Phase 3: N3 (Day 601-1000)", 601, 1000)
    add_unit(UNITS_N2, "Phase 4: N2 (Day 1001-1500)", 1001, 1500)
    add_unit(UNITS_N1, "Phase 5: N1 (Day 1501-2000)", 1501, 2000)
    add_unit(UNITS_NATIVE, "Phase 6: Native (Day 2001-2500)", 2001, 2500)

    return roadmap

def get_day_title_and_prompt(day_num, data):
    if "intro_title" in data:
        emoji, label, lvl_code = get_level_info(day_num)
        title = data["intro_title"]
        prompt = f"Đóng vai Gia sư tiếng Nhật. Hôm nay là Day {day_num} — {title}. Trình độ: Nhập môn.\n\nHãy dạy nội dung: {title}. Cung cấp bài tập thực hành (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
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
        3: ("Kanji & Pronunciation", "⛩️"),
        4: ("Reading Immersion", "📖"),
        5: ("Listening Immersion", "🎧"),
        6: ("Speaking Practice", "💬"),
        7: ("Review & Mini Test", "✅"),
    }
    role_name, role_emoji = day_roles[day_in_unit]
    title = f"Day {day_num} — [Unit {unit_num}·Day {day_in_unit}/7] {role_emoji} {role_name} — {vocab_topic}"

    if day_in_unit == 1:
        prompt = f"Đóng vai Gia sư tiếng Nhật. Hôm nay là Day {day_num} — Ngày 1/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\n1. Hãy dạy 15-20 từ vựng cốt lõi về '{vocab_topic}'.\n- Gợi ý: {vocab_hint}.\n- Phải có Kanji, Hiragana (Furigana), Romaji, Hán Việt và ví dụ thực tế.\n\n2. Dạy điểm ngữ pháp: {grammar_point}.\n⚠️ Bắt buộc dùng từ vựng vừa dạy làm ví dụ cho phần ngữ pháp này."
    elif day_in_unit == 2:
        prompt = f"Đóng vai Gia sư tiếng Nhật. Hôm nay là Day {day_num} — Ngày 2/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nDạy chuyên sâu ngữ pháp: {grammar_point}.\n⚠️ Bắt buộc: Tất cả ví dụ và bài tập thực hành phải nhúng từ vựng chủ đề '{vocab_topic}' đã học hôm qua. Đưa ra bài tập phân biệt với các mẫu ngữ pháp dễ nhầm (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
    elif day_in_unit == 3:
        prompt = f"Đóng vai Gia sư tiếng Nhật. Hôm nay là Day {day_num} — Ngày 3/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nDạy 5-7 chữ Kanji liên quan đến chủ đề '{vocab_topic}'. Phân tích bộ thủ, Âm On, Âm Kun, và mẹo nhớ (Mnemonic). Đồng thời chỉ ra quy tắc Pitch Accent (trọng âm) cho các từ vựng này."
    elif day_in_unit == 4:
        prompt = f"Đóng vai Gia sư tiếng Nhật. Hôm nay là Day {day_num} — Ngày 4/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nCung cấp 1 bài đọc (150-250 chữ) về '{vocab_topic}' có chứa TỰ NHIÊN ngữ pháp {grammar_point} và Kanji Unit này. Sau đó đưa ra 3 câu hỏi đọc hiểu (kiểu JLPT) (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
    elif day_in_unit == 5:
        prompt = f"Đóng vai Gia sư tiếng Nhật. Hôm nay là Day {day_num} — Ngày 5/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nTạo 1 script bài nghe (hội thoại/podcast) về '{vocab_topic}', nhúng từ vựng Unit. Đánh dấu các chỗ rút gọn âm, nuốt âm đặc trưng của người Nhật. Kèm 3 câu hỏi bài tập nghe (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
    elif day_in_unit == 6:
        prompt = f"Đóng vai Gia sư tiếng Nhật. Hôm nay là Day {day_num} — Ngày 6/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nCung cấp 3 tình huống giao tiếp mẫu (Role-play) dạng đoạn hội thoại hoàn chỉnh (song ngữ Nhật-Việt) về chủ đề '{vocab_topic}'. Trong đó bắt buộc áp dụng ngữ pháp {grammar_point} và từ vựng Unit này để tôi tự luyện nói (Shadowing)."
    else:
        prompt = f"Đóng vai Gia sư tiếng Nhật. Hôm nay là Day {day_num} — Ngày 7/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nÔn tập tổng hợp Unit {unit_num} (Chủ đề: {vocab_topic}, Ngữ pháp: {grammar_point}). Cho 1 bài test JLPT mini gồm 4 phần (Từ vựng, Kanji, Ngữ pháp, Đọc) (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."

    return title, prompt, emoji, label, lvl_code

def generate_markdown_v2(roadmap_data):
    total = len(roadmap_data)
    md_lines = [
        "# 🇯🇵 Lộ Trình Học Tiếng Nhật – 2500 Ngày V2 (Unit-based Learning)",
        "",
        "> ⚠️ **V2 — Unit-based Learning**: Mỗi 7 ngày = 1 Unit học sâu theo 1 chủ đề.",
        "> Tích hợp học từ vựng, ngữ pháp, Kanji xoay quanh cùng một văn cảnh giúp nhớ lâu hơn.",
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
            md_lines.append(f"**Tags:** #japanese_v2 #day{day_num} #{lvl_code} #unit{data['unit_num']}")
        else:
            md_lines.append(f"**Tags:** #japanese_v2 #day{day_num} #{lvl_code} #intro")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    with open(OUTPUT_FILEPATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"✅ Done! V2 generated: {OUTPUT_FILEPATH}")

if __name__ == "__main__":
    data = build_roadmap_v2()
    generate_markdown_v2(data)
