# generate_chinese_roadmap_v2.py
import os

OUTPUT_FILEPATH = r"c:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\roadmap_chinese_2500_v2.md"
UNIT_DAYS = 7

def get_level_info(day_num):
    if day_num <= 200:
        return ("🟢", "Vỡ lòng/HSK1 — 30-45 phút", "hsk1")
    elif day_num <= 400:
        return ("🟡", "Cơ bản/HSK2 — 30-45 phút", "hsk2")
    elif day_num <= 650:
        return ("🟠", "Trung cấp/HSK3 — 30-45 phút", "hsk3")
    elif day_num <= 1000:
        return ("🟠", "Trung cao cấp/HSK4 — 30-45 phút", "hsk4")
    elif day_num <= 1500:
        return ("🔴", "Cao cấp/HSK5 — 30-45 phút", "hsk5")
    elif day_num <= 2000:
        return ("🔴", "Chuyên gia/HSK6 — 30-45 phút", "hsk6")
    else:
        return ("🟣", "Bản địa/Native — 30-45 phút", "native")

UNITS_HSK1 = [
    ("Gia đình & Chào hỏi", "Đại từ nhân xưng & 是", "我, 你, 他, 家, 爸爸..."),
    ("Quốc gia & Ngôn ngữ", "Câu hỏi ma 吗", "中国, 越南, 汉语..."),
    ("Đồ vật & Đếm số", "Lượng từ 个, 本", "一, 二, 书, 桌子..."),
    ("Thời gian & Ngày tháng", "Câu chữ 有", "今天, 明天, 月, 号..."),
    ("Mua sắm cơ bản", "Từ để hỏi 多少 / 几", "钱, 买, 苹果, 水..."),
    ("Ăn uống & Nhà hàng", "Động từ năng nguyện 想 / 要", "吃, 喝, 米饭, 菜..."),
    ("Địa điểm & Phương hướng", "Giới từ 在", "学校, 医院, 前面..."),
    ("Giao thông & Đi lại", "Động từ 去, 来", "坐, 出租车, 飞机..."),
    ("Thời tiết", "Trạng từ 很, 太", "冷, 热, 下雨, 天气..."),
    ("Hoạt động hằng ngày", "Trợ từ động thái 了 (Cơ bản)", "睡觉, 看, 电影, 工作..."),
    ("Tổng ôn HSK1", "Ôn tập HSK1", "Review")
]

UNITS_HSK2 = [
    ("Màu sắc & Quần áo", "Câu chữ 的", "红, 黑, 衣服, 穿..."),
    ("Sức khỏe & Cơ thể", "Động từ năng nguyện 觉得 / 能", "生病, 药, 休息..."),
    ("Sở thích & Thể thao", "Câu hỏi 为为什么", "打篮球, 跑步, 喜欢..."),
    ("Giao tiếp điện thoại", "Trợ từ ngữ khí 吧", "喂, 手机, 告诉..."),
    ("Phòng ốc & Nội thất", "Câu chữ 比 (So sánh cơ bản)", "房间, 门, 左边..."),
    ("Dự định & Tương lai", "Động từ năng nguyện 可以 / 会", "准备, 旅游, 帮助..."),
    ("Giao dịch & Dịch vụ", "Bổ ngữ kết quả (懂, 完)", "服务员, 懂, 错..."),
    ("Công việc & Học tập", "Đang làm gì (正在 / 在)", "上班, 考试, 问题..."),
    ("Cảm xúc & Trạng thái", "Trợ từ 呢 (nhấn mạnh)", "高兴, 累, 快乐..."),
    ("Du lịch & Phương tiện", "Trợ từ 过 (đã từng)", "火车站, 远, 近..."),
    ("Tổng ôn HSK2", "Ôn tập HSK2", "Review")
]

UNITS_HSK3 = [
    ("Mối quan hệ", "Câu chữ 把", "同事, 邻居, 客人..."),
    ("Thành phố & Môi trường", "Câu chữ 被", "城市, 环境, 树..."),
    ("Giáo dục & Thi cử", "Bổ ngữ xu hướng kép", "校长, 成绩, 解决..."),
    ("Văn hóa truyền thống", "Câu phức 因为...所以...", "节日, 历史, 习惯..."),
    ("Công sở & Hội họp", "Câu phức 虽然...但是...", "会议, 经理, 要求..."),
    ("Internet & Truyền thông", "Cấu trúc 越来越...", "上网, 新闻, 节目..."),
    ("Tài chính & Mua sắm", "Bổ ngữ khả năng", "信用卡, 极了, 质量..."),
    ("Nghệ thuật & Đời sống", "Câu phức 只有...才...", "音乐, 爱好, 发现..."),
    ("Giao tiếp xã hội", "Câu phức 如果...就...", "影响, 关系, 了解..."),
    ("Tính cách & Đánh giá", "Bổ ngữ trạng thái", "聪明, 努力, 热情..."),
    ("Tổng ôn HSK3", "Ôn tập HSK3", "Review")
]

UNITS_HSK4 = [
    ("Kinh tế & Thương mại", "Cấu trúc 即使...也...", "经济, 价格, 降低..."),
    ("Xã hội & Luật pháp", "Cấu trúc 无论...都...", "法律, 责任, 保护..."),
    ("Khoa học & Kỹ thuật", "Cấu trúc 既然...就...", "科学, 技术, 发明..."),
    ("Tâm lý & Tư duy", "Cấu trúc 哪怕...也...", "判断, 态度, 引起..."),
    ("Giao tiếp nâng cao", "Cấu trúc 至于...", "究竟, 顺便, 毕竟..."),
    ("Giáo dục & Quan điểm", "Từ nối 从而 / 因此", "教育, 基础, 否则..."),
    ("Y tế & Sức khỏe", "Cấu trúc 不仅...而且...", "健康, 效果, 坚持..."),
    ("Nghệ thuật & Văn học", "Cấu trúc 连...都...", "艺术, 浪漫, 精彩..."),
    ("Môi trường tự nhiên", "Câu phản vấn", "地球, 污染, 气候..."),
    ("Kỹ năng mềm", "Thành ngữ HSK4 cơ bản", "马虎, 重点, 积累..."),
    ("Tổng ôn HSK4", "Ôn tập HSK4", "Review")
]

UNITS_HSK5 = [
    ("Kinh doanh & Quản lý", "Từ vựng sắc thái trang trọng", "企业, 投资, 利润..."),
    ("Chính trị & Xã hội", "Cấu trúc 毫不...", "政策, 权利, 矛盾..."),
    ("Triết học & Suy ngẫm", "Thành ngữ HSK5", "本质, 逻辑, 智慧..."),
    ("Thương mại quốc tế", "Trạng từ chỉ phạm vi", "贸易, 进口, 汇率..."),
    ("Văn học & Lịch sử", "Từ ghép nghĩa bóng", "王朝, 经典, 传说..."),
    ("Công nghệ & Đổi mới", "Câu ghép chính phụ phức", "创新, 虚拟, 程序..."),
    ("Tâm lý xã hội", "Ngữ pháp 固然...但是...", "心理, 现象, 歧视..."),
    ("Y học & Gen", "Từ chuyên ngành cơ bản", "基因, 病毒, 临床..."),
    ("Kiến trúc & Nghệ thuật", "Biểu đạt trừu tượng", "风格, 欣赏, 审美..."),
    ("Tổng ôn HSK5", "Ôn tập HSK5", "Review")
]

UNITS_HSK6_NATIVE = [
    ("Kinh tế vĩ mô & Tài chính", "Phân tích HSK6", "通货膨胀, 垄断..."),
    ("Pháp lý & Tòa án", "Văn bản hành chính", "诉讼, 宪法, 制裁..."),
    ("Văn ngôn văn (Cổ văn)", "Chiết tự & Cổ ngữ", "之, 乎, 者, 也..."),
    ("Ngôn ngữ mạng & Slang", "Từ lóng giới trẻ Trung Quốc", "绝了, 躺平, 内卷..."),
    ("Thành ngữ Nâng cao (Chengyu)", "Điển cố điển tích", "画蛇添足, 破釜沉舟..."),
    ("Báo chí & Tin tức", "Văn phong tin tức", "据悉, 截至, 旨在..."),
    ("Thương thuyết doanh nghiệp", "Kỹ năng đàm phán", "妥协, 共赢, 战略..."),
    ("Tổng ôn Cao cấp", "Mastery Review", "Review")
]

def build_roadmap_v2():
    roadmap = {}
    day = 1

    # Days 1-22: Pinyin & Basic strokes
    pinyin_hanzi = [
        "Pinyin: Vận mẫu đơn (a, o, e, i, u, ü)",
        "Pinyin: Thanh điệu (4 thanh) & Quy tắc biến điệu",
        "Pinyin: Thanh mẫu (b, p, m, f, d, t, n, l)",
        "Pinyin: Thanh mẫu (g, k, h, j, q, x)",
        "Pinyin: Thanh mẫu (zh, ch, sh, r, z, c, s)",
        "Pinyin: Vận mẫu kép (ai, ei, ao, ou...)",
        "Pinyin: Vận mẫu mũi (an, en, in, ang, eng, ing, ong)",
        "Pinyin: Tổng ôn & Luyện nghe Pinyin",
        "Chữ Hán: Nét cơ bản (Ngang, Sổ, Phẩy, Mác...)",
        "Chữ Hán: Nét phái sinh",
        "Chữ Hán: Quy tắc bút thuận (Trái trước phải sau...)",
        "Chữ Hán: 20 Bộ thủ thường gặp nhất",
        "Chữ Hán: Các bộ thủ chỉ ý nghĩa (Nhân, Thủy, Mộc...)",
        "Chữ Hán: Lục thư (Tượng hình, Chỉ sự, Hội ý, Hình thanh)",
        "Từ vựng nhập môn: Số đếm 1-100",
        "Từ vựng nhập môn: Chào hỏi (Ni hao)",
        "Từ vựng nhập môn: Xưng hô (Tôi, Bạn, Anh ấy)",
        "Từ vựng nhập môn: Các thứ trong tuần",
        "Luyện gõ Pinyin trên điện thoại/máy tính",
        "Ôn tập Nhập môn 1",
        "Ôn tập Nhập môn 2",
        "Bài test Nhập môn"
    ]

    for t in pinyin_hanzi:
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

    add_unit(UNITS_HSK1, "Phase 1: HSK1 (Day 23-200)", 23, 200)
    add_unit(UNITS_HSK2, "Phase 2: HSK2 (Day 201-400)", 201, 400)
    add_unit(UNITS_HSK3, "Phase 3: HSK3 (Day 401-650)", 401, 650)
    add_unit(UNITS_HSK4, "Phase 4: HSK4 (Day 651-1000)", 651, 1000)
    add_unit(UNITS_HSK5, "Phase 5: HSK5 (Day 1001-1500)", 1001, 1500)
    add_unit(UNITS_HSK6_NATIVE, "Phase 6: HSK6 & Native (Day 1501-2500)", 1501, 2500)

    return roadmap

def get_day_title_and_prompt(day_num, data):
    if "intro_title" in data:
        emoji, label, lvl_code = get_level_info(day_num)
        title = data["intro_title"]
        prompt = f"Đóng vai Gia sư Tiếng Trung. Hôm nay là Day {day_num} — {title}. Trình độ: Nhập môn.\n\nHãy dạy nội dung: {title}. Cung cấp bài tập thực hành (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
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
        3: ("Hanzi & Pinyin", "⛩️"),
        4: ("Reading Immersion", "📖"),
        5: ("Listening Immersion", "🎧"),
        6: ("Speaking Practice", "💬"),
        7: ("Review & Mini Test", "✅"),
    }
    role_name, role_emoji = day_roles[day_in_unit]
    title = f"Day {day_num} — [Unit {unit_num}·Day {day_in_unit}/7] {role_emoji} {role_name} — {vocab_topic}"

    if day_in_unit == 1:
        prompt = f"Đóng vai Gia sư Tiếng Trung. Hôm nay là Day {day_num} — Ngày 1/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\n1. Hãy dạy 15-20 từ vựng cốt lõi về '{vocab_topic}'.\n- Gợi ý: {vocab_hint}.\n- Phải có Chữ Hán, Pinyin, Hán Việt, định nghĩa và ví dụ thực tế.\n\n2. Dạy điểm ngữ pháp: {grammar_point}.\n⚠️ Bắt buộc dùng từ vựng vừa dạy làm ví dụ cho phần ngữ pháp này."
    elif day_in_unit == 2:
        prompt = f"Đóng vai Gia sư Tiếng Trung. Hôm nay là Day {day_num} — Ngày 2/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nDạy chuyên sâu ngữ pháp: {grammar_point}.\n⚠️ Bắt buộc: Tất cả ví dụ và bài tập thực hành phải nhúng từ vựng chủ đề '{vocab_topic}' đã học hôm qua. Đưa ra bài tập phân biệt ngữ pháp hoặc sắp xếp câu (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu).|"
    elif day_in_unit == 3:
        prompt = f"Đóng vai Gia sư Tiếng Trung. Hôm nay là Day {day_num} — Ngày 3/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nDạy 5-7 chữ Hán liên quan đến chủ đề '{vocab_topic}'. Phân tích bộ thủ, Lục thư và câu chuyện ghi nhớ (Mnemonic). Chỉ ra lỗi phát âm Pinyin hoặc lỗi biến điệu mà người Việt hay mắc."
    elif day_in_unit == 4:
        prompt = f"Đóng vai Gia sư Tiếng Trung. Hôm nay là Day {day_num} — Ngày 4/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nCung cấp 1 bài đọc (150-250 chữ) về '{vocab_topic}' có chứa TỰ NHIÊN ngữ pháp {grammar_point} và từ vựng Unit này (Chỉ ghi chữ Hán, không ghi Pinyin trong bài đọc chính). Đưa ra 3 câu hỏi đọc hiểu (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
    elif day_in_unit == 5:
        prompt = f"Đóng vai Gia sư Tiếng Trung. Hôm nay là Day {day_num} — Ngày 5/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nTạo 1 script bài nghe (hội thoại/podcast) về '{vocab_topic}', nhúng từ vựng Unit. Nhấn mạnh vào ngữ điệu và các từ khẩu ngữ đặc trưng. Kèm 3 câu hỏi bài tập nghe (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."
    elif day_in_unit == 6:
        prompt = f"Đóng vai Gia sư Tiếng Trung. Hôm nay là Day {day_num} — Ngày 6/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nCung cấp 3 tình huống giao tiếp mẫu (Role-play) dạng đoạn hội thoại hoàn chỉnh (song ngữ Trung-Việt, có Pinyin) về chủ đề '{vocab_topic}'. Trong đó bắt buộc áp dụng ngữ pháp {grammar_point} và từ vựng Unit này để tôi tự luyện nói (Shadowing)."
    else:
        prompt = f"Đóng vai Gia sư Tiếng Trung. Hôm nay là Day {day_num} — Ngày 7/7 Unit {unit_num}. Trình độ: {lvl_code.upper()}\n\nÔn tập tổng hợp Unit {unit_num} (Chủ đề: {vocab_topic}, Ngữ pháp: {grammar_point}). Cho 1 bài test HSK mini gồm 4 phần (Từ vựng, Chữ Hán, Ngữ pháp, Đọc) (⚠️ QUAN TRỌNG: TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ câu hỏi VÀ ĐÁP ÁN CHI TIẾT CÙNG LÚC để tôi tự đọc và đối chiếu)."

    return title, prompt, emoji, label, lvl_code

def generate_markdown_v2(roadmap_data):
    total = len(roadmap_data)
    md_lines = [
        "# 🇨🇳 Lộ Trình Học Tiếng Trung – 2500 Ngày V2 (Unit-based Learning)",
        "",
        "> ⚠️ **V2 — Unit-based Learning**: Mỗi 7 ngày = 1 Unit học sâu theo 1 chủ đề.",
        "> Tích hợp học từ vựng, ngữ pháp, chữ Hán xoay quanh cùng một văn cảnh giúp nhớ lâu hơn.",
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
            md_lines.append(f"**Tags:** #chinese_v2 #day{day_num} #{lvl_code} #unit{data['unit_num']}")
        else:
            md_lines.append(f"**Tags:** #chinese_v2 #day{day_num} #{lvl_code} #intro")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    with open(OUTPUT_FILEPATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"✅ Done! V2 generated: {OUTPUT_FILEPATH}")

if __name__ == "__main__":
    data = build_roadmap_v2()
    generate_markdown_v2(data)
