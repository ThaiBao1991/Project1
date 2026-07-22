# Generate Chinese Roadmap - 2500 Days (Zero to Native)
# Mỗi Day = 1 đơn vị nội dung, thời gian học cố định 30-45 phút/ngày
# Tổng 2500 ngày ~ 7 năm học liên tục để đạt trình độ Native/Chuyên gia

import os

filepath = r"c:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\roadmap_chinese_1000.md"

def get_time(day_num):
    """Trả về (emoji, label thời gian, lvl_code) — Luôn cố định 30-45 phút/ngày."""
    if day_num <= 250:
        return ("🟢", "Vỡ lòng/HSK1 — 30-45 phút", "hsk1")
    elif day_num <= 600:
        return ("🟡", "Cơ bản/HSK2 — 30-45 phút", "hsk2")
    elif day_num <= 1000:
        return ("🟠", "Trung cấp/HSK3 — 30-45 phút", "hsk3")
    elif day_num <= 1500:
        return ("🟠", "Cao cấp/HSK4 — 30-45 phút", "hsk4")
    elif day_num <= 2000:
        return ("🔴", "Học thuật/HSK5-6 — 30-45 phút", "hsk56")
    else:
        return ("🟣", "Bản địa/Chuyên gia — 30-45 phút", "native")

def build_roadmap():
    roadmap = {}
    day = 1

    def add_day(title, phase, level):
        nonlocal day
        roadmap[day] = (title, phase, level)
        day += 1

    # ==============================================================
    # PHASE 1: HSK1 & Nhập môn (Day 1 - 250)
    # ==============================================================
    phase1 = "Phase 1: HSK1 & Nhập môn (Day 1 - 250)"

    # Days 1-20: Pinyin & Nét chữ (giãn ra so với bản cũ)
    pinyin_hanzi = [
        "Pinyin: Thanh mẫu cơ bản (b p m f, d t n l)",
        "Pinyin: Thanh mẫu nhóm 2 (g k h)",
        "Pinyin: Thanh mẫu nhóm 3 (j q x)",
        "Pinyin: Thanh mẫu khó nhóm 1 (z c s)",
        "Pinyin: Thanh mẫu khó nhóm 2 (zh ch sh r)",
        "Pinyin: Vận mẫu đơn (a o e i u ü)",
        "Pinyin: Vận mẫu kép (ai ei ui ao ou iu)",
        "Pinyin: Vận mẫu kép phần 2 (ie üe er)",
        "Pinyin: Vận mẫu mũi ngắn (an en in un ün)",
        "Pinyin: Vận mẫu mũi dài (ang eng ing ong)",
        "Thanh điệu: 4 thanh cơ bản (1-2-3-4) & Bí quyết phát âm không bị ngọng",
        "Thanh điệu: Thanh trung tính (Khinh thanh) & Cách nhận diện",
        "Quy tắc biến điệu: 2 thanh 3 liên tiếp",
        "Quy tắc biến điệu của 一 (yī) và 不 (bù)",
        "Âm cuốn lưỡi (Erhua/Nhi hóa) — Giọng Bắc Kinh",
        "Luyện đọc Pinyin tổng hợp — Bài tập tự đọc câu",
        "Chữ Hán: 8 Nét cơ bản và Quy tắc Bút thuận",
        "Chữ Hán: Cấu tạo chữ (Tượng hình, Chỉ sự, Hội ý, Hình thanh)",
        "Chữ Hán: 10 Bộ thủ cốt lõi (Nhân 人, Tâm 心, Thủy 水, Hỏa 火, Mộc 木...)",
        "Từ vựng nhập môn: Chào hỏi và Tạm biệt (Nǐ hǎo, Zàijiàn) & Giới thiệu bản thân ngắn",
    ]
    for t in pinyin_hanzi:
        add_day(t, phase1, "hsk1")

    # Day 21-250: HSK1 Loop (chu kỳ 7: ngữ pháp → từ vựng → hán tự → đọc → nghe → giao tiếp → ôn tập)
    hsk1_grammar = [
        "Câu chữ 是 (shì) — Khẳng định và Phủ định",
        "Câu hỏi với 吗 (ma) — Nghi vấn đuôi câu",
        "Đại từ nghi vấn: 谁 (shéi), 什么 (shénme), 哪儿 (nǎr)",
        "Sở hữu với trợ từ 的 (de) — A的B = B của A",
        "Câu chữ 有 (yǒu) — Sở hữu và Tồn tại",
        "Động từ năng nguyện: 会 (huì) — Có thể (đã học)",
        "Động từ năng nguyện: 能 (néng) — Có thể (hoàn cảnh cho phép)",
        "Trợ từ ngữ khí 呢 (ne) — Còn ... thì sao?",
        "Câu hỏi lựa chọn 还是 (háishi) — Hay là?",
        "Đại từ chỉ định 这 (zhè) / 那 (nà) — Cái này / Cái kia",
        "Số đếm 1-100 và cách nói Tuổi (岁 suì)",
        "Cách nói Giờ (时 shí, 分 fēn) và Ngày tháng năm",
        "Trạng từ phủ định 没 (méi) và 不 (bù) — Phân biệt",
        "Động từ 想 (xiǎng) — Muốn / Nghĩ",
        "Động từ 要 (yào) — Cần / Sẽ",
        "Cấu trúc: 在 (zài) + Địa điểm + Động từ — Đang ở đâu làm gì",
        "Cấu trúc di chuyển: 去 (qù) + Địa điểm + Động từ",
        "Trạng từ mức độ: 很 (hěn) — Rất, 太 (tài) — Quá",
        "Cách nói Tiền tệ và Mua sắm (Duōshao qián? — Bao nhiêu tiền?)",
        "Câu cầu khiến: 请 (qǐng) — Xin mời / Làm ơn",
        "Lượng từ: Số từ + Lượng từ (个 gè, 本 běn, 张 zhāng) + Danh từ",
        "Phương hướng cơ bản: 上 (shàng), 下 (xià), 前 (qián), 后 (hòu), 左 (zuǒ), 右 (yòu)",
    ]
    vocab_hsk1 = [
        "Gia đình (爸爸, 妈妈, 哥哥...)",
        "Trường học (学校, 老师, 学生, 书...)",
        "Nghề nghiệp (医生, 工人, 学生, 司机...)",
        "Quốc gia & Ngôn ngữ (中国, 越南, 汉语, 英语...)",
        "Đồ ăn thức uống (米饭, 面条, 水, 茶...)",
        "Trái cây & Thực phẩm (苹果, 香蕉, 肉, 蔬菜...)",
        "Màu sắc (红色, 蓝色, 黄色, 白色, 黑色...)",
        "Đồ vật trong nhà (桌子, 椅子, 书包, 手机...)",
        "Thời tiết (晴天, 下雨, 冷, 热, 风...)",
        "Động vật & Thú cưng (猫, 狗, 鱼, 鸟...)",
        "Thời gian: Các thứ trong tuần và Các tháng trong năm",
        "Nơi chốn: Nhà, Trường, Siêu thị, Bệnh viện",
    ]

    cycle_idx = 0
    while day <= 250:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(hsk1_grammar)
            add_day(f"Ngữ pháp HSK1: {hsk1_grammar[gram_idx]}", phase1, "hsk1")
        elif mod == 1:
            voc_idx = (cycle_idx // 7) % len(vocab_hsk1)
            add_day(f"Từ vựng HSK1: Chủ đề {vocab_hsk1[voc_idx]}", phase1, "hsk1")
        elif mod == 2:
            add_day(f"Chữ Hán HSK1: Phân tích & Mnemonic 5 chữ cơ bản nhóm {(cycle_idx // 7) + 1}", phase1, "hsk1")
        elif mod == 3:
            add_day(f"Đọc hiểu HSK1: Đoạn văn ngắn áp dụng {hsk1_grammar[(cycle_idx // 7) % len(hsk1_grammar)]}", phase1, "hsk1")
        elif mod == 4:
            add_day("Nghe hiểu HSK1: Hội thoại chậm & Nhận diện thanh điệu", phase1, "hsk1")
        elif mod == 5:
            add_day("Giao tiếp HSK1: Phản xạ hỏi-đáp và Sửa lỗi phát âm người Việt", phase1, "hsk1")
        else:  # mod == 6
            add_day("Ôn tập tổng hợp HSK1: Dịch xuôi/ngược Việt-Trung các câu đã học", phase1, "hsk1")
        cycle_idx += 1

    # ==============================================================
    # PHASE 2: HSK2 & Giao tiếp cơ bản (Day 251 - 600)
    # ==============================================================
    phase2 = "Phase 2: HSK2 & Giao tiếp cơ bản (Day 251 - 600)"
    hsk2_grammar = [
        "Câu kiêm ngữ: 请 (qǐng), 让 (ràng), 叫 (jiào) — Mời/Bảo ai làm gì",
        "Bổ ngữ trình độ với 得 (de) — Làm gì GIỎI đến mức nào",
        "Động từ năng nguyện: 可以 (kěyǐ) — Được phép",
        "Động từ năng nguyện: 应该 (yīnggāi) — Nên làm",
        "Trợ từ động thái 了 (le) — Biểu thị hoàn thành hành động",
        "Trợ từ động thái 着 (zhe) — Trạng thái tiếp diễn",
        "Trợ từ động thái 过 (guò) — Từng có trải nghiệm",
        "Câu so sánh cơ bản với 比 (bǐ) — A比B + Tính từ",
        "Câu so sánh đảo: 没有 (méiyǒu) — A không bằng B",
        "Cấu trúc 虽然...但是... — Tuy...nhưng...",
        "Cấu trúc 因为...所以... — Bởi vì...cho nên...",
        "Câu hỏi phản vấn: 不是...吗? — Chẳng phải là...sao?",
        "Khoảng cách: 离 (lí) + Địa điểm + 远/近",
        "Câu chữ 把 (bǎ) cơ bản — Bổ ngữ kết quả",
        "Phân biệt 刚 (gāng) và 刚才 (gāngcái) — Vừa xong / Vừa rồi",
        "Phân biệt 一点儿 và 有一点儿",
        "Đại từ 每 (měi) — Mỗi",
        "Cấu trúc 除了...以外 — Ngoài...ra",
        "Bổ ngữ kết quả: Động từ + 好, 完, 见, 到",
        "Hỏi về số lượng: 多少 (duōshao) và 几 (jǐ)",
    ]
    vocab_hsk2 = [
        "Sở thích & Thể thao (踢足球, 游泳, 打篮球...)",
        "Khám bệnh & Sức khỏe (发烧, 头痛, 医院, 药...)",
        "Du lịch & Giao thông (飞机, 高铁, 地铁, 出租车...)",
        "Mua sắm & Mặc cả (便宜, 贵, 打折, 收据...)",
        "Cảm xúc & Tâm trạng (高兴, 难过, 担心, 生气...)",
        "Tại nhà hàng: Gọi món và Thanh toán",
        "Công việc hằng ngày (早上, 起床, 上班, 下班...)",
        "Giao dịch ngân hàng cơ bản (存钱, 取钱, 转账...)",
        "Thời tiết nâng cao & Bốn mùa",
        "Miêu tả ngoại hình & Tính cách người",
    ]

    cycle_idx = 0
    while day <= 600:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(hsk2_grammar)
            add_day(f"Ngữ pháp HSK2: {hsk2_grammar[gram_idx]}", phase2, "hsk2")
        elif mod == 1:
            voc_idx = (cycle_idx // 7) % len(vocab_hsk2)
            add_day(f"Từ vựng HSK2: Chủ đề {vocab_hsk2[voc_idx]}", phase2, "hsk2")
        elif mod == 2:
            add_day(f"Chữ Hán HSK2: Học 5 chữ Hán, Mnemonic & Từ ghép nhóm {(cycle_idx // 7) + 1}", phase2, "hsk2")
        elif mod == 3:
            add_day("Đọc hiểu HSK2: Đọc email, tin nhắn WeChat, thông báo đơn giản", phase2, "hsk2")
        elif mod == 4:
            add_day("Nghe hiểu HSK2: Nghe thông báo ở ga tàu, siêu thị, bệnh viện", phase2, "hsk2")
        elif mod == 5:
            add_day("Giao tiếp HSK2: Shadowing tình huống đời sống (Mua sắm, Hỏi đường...)", phase2, "hsk2")
        else:  # mod == 6
            add_day("Ôn tập HSK2: Bài test mini Ngữ pháp + Từ vựng + Hán tự", phase2, "hsk2")
        cycle_idx += 1

    # ==============================================================
    # PHASE 3: HSK3 & Tiếng Trung Trung cấp (Day 601 - 1000)
    # ==============================================================
    phase3 = "Phase 3: HSK3 & Tiếng Trung Trung cấp (Day 601 - 1000)"
    hsk3_grammar = [
        "Bổ ngữ kết quả: Động từ + 好, 完, 见, 到, 懂",
        "Bổ ngữ phương hướng đơn: Động từ + 来 (lái) / 去 (qù)",
        "Bổ ngữ phương hướng kép: 起来, 下去, 出来, 进去, 回来...",
        "Bổ ngữ khả năng: Động từ + 得/不 + Bổ ngữ kết quả",
        "Câu chữ 被 (bèi) — Câu bị động",
        "Câu chữ 把 (bǎ) nâng cao — Nhấn mạnh kết quả hành động",
        "Cấu trúc 只要...就... — Chỉ cần...thì...",
        "Cấu trúc 只有...才... — Chỉ có...mới...",
        "Cấu trúc 哪怕...也... — Cho dù...cũng...",
        "Cấu trúc 越...越... — Càng...càng...",
        "Phân biệt 的, 得, 地 — Ba chữ 'de' trong tiếng Trung",
        "Lặp lại Động từ (VV) và Tính từ (AA) — Ý nghĩa & Cách dùng",
        "Câu tồn tại: Địa điểm + 有/是/动词着",
        "Cấu trúc nhấn mạnh 是...的 (shì...de)",
        "Câu cảm thán: 多 (duō) + Tính từ + 啊!",
        "Phân biệt Trạng từ thời gian: 已经, 曾经, 刚, 就",
        "Cấu trúc điều kiện: 如果...就... — Nếu...thì...",
        "Biểu đạt kết quả không mong muốn: 结果, 最后, 没想到",
    ]

    cycle_idx = 0
    while day <= 1000:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(hsk3_grammar)
            add_day(f"Ngữ pháp HSK3: {hsk3_grammar[gram_idx]}", phase3, "hsk3")
        elif mod == 1:
            add_day(f"Từ vựng HSK3: Cụm từ cố định (Collocations) thường gặp nhóm {(cycle_idx // 7) + 1}", phase3, "hsk3")
        elif mod == 2:
            add_day(f"Chữ Hán HSK3: Phân biệt các chữ dễ nhầm (Hình cận tự) nhóm {(cycle_idx // 7) + 1}", phase3, "hsk3")
        elif mod == 3:
            add_day("Đọc hiểu HSK3: Mẩu truyện ngắn, tin tức đơn giản & Bài tập hỏi đáp", phase3, "hsk3")
        elif mod == 4:
            add_day("Nghe hiểu HSK3: Hội thoại có Idiom/Lóng cơ bản, tốc độ vừa", phase3, "hsk3")
        elif mod == 5:
            add_day("Dịch thuật HSK3: Dịch xuôi/ngược Việt-Trung câu phức tạp", phase3, "hsk3")
        else:  # mod == 6
            add_day("Ôn tập HSK3: Viết đoạn văn ngắn 50-80 chữ về chủ đề tự chọn", phase3, "hsk3")
        cycle_idx += 1

    # ==============================================================
    # PHASE 4: HSK4 & Công sở / Chuyên ngành cơ bản (Day 1001 - 1500)
    # ==============================================================
    phase4 = "Phase 4: HSK4 & Công sở / Chuyên ngành cơ bản (Day 1001 - 1500)"
    hsk4_grammar = [
        "Phân biệt 尽管...还是... và 虽然...但是...",
        "Cấu trúc 无论...都... — Bất luận...đều...",
        "Cấu trúc 既然...就... — Đã...thì...",
        "Cấu trúc 即使...也... — Cho dù...cũng...",
        "Phân biệt từ đồng nghĩa: 了解 vs 知道 — Hiểu biết vs Biết",
        "Phân biệt từ đồng nghĩa: 以为 vs 认为 — Tưởng là vs Cho rằng",
        "Phân biệt từ đồng nghĩa: 帮忙 vs 帮助 — Giúp đỡ (informal vs formal)",
        "Phân biệt từ đồng nghĩa: 发现 vs 发明 — Phát hiện vs Phát minh",
        "Phó từ tần suất: 往往 vs 常常 vs 总是 — Luôn luôn / Thường xuyên",
        "Đại từ thời gian: 本来 vs 原来 vs 后来 — Vốn dĩ / Hóa ra / Sau đó",
        "Cấu trúc chuyển nhượng: 不管...也... — Dù thế nào cũng...",
        "Văn phong lịch sự: 请问, 麻烦您, 不好意思trong email",
        "Biểu đạt quan điểm: 我认为, 在我看来, 就我个人而言",
        "Cấu trúc 之所以...是因为... —Ở chỗ...là vì...",
        "Trạng từ nhấn mạnh: 恰恰, 偏偏, 竟然, 居然",
    ]
    vocab_hsk4_topics = [
        "Từ vựng Văn phòng (开会, 汇报, 方案, 项目...)",
        "Từ vựng Kinh tế / Tài chính (合同, 利润, 市场, 竞争...)",
        "Từ vựng Công nghệ (人工智能, 软件, 数据, 网络...)",
        "Từ vựng Pháp lý / Hành chính (申请, 签证, 合法, 规定...)",
        "Thành ngữ 4 chữ (Chengyu) thông dụng nhóm 1",
        "Thành ngữ 4 chữ (Chengyu) thông dụng nhóm 2",
        "Từ vựng Y tế & Điều dưỡng (症状, 诊断, 处方, 住院...)",
        "Từ vựng Giáo dục & Học thuật (论文, 研究, 考试, 毕业...)",
        "Từ vựng Truyền thông & Mạng xã hội (直播, 评论, 转发, 热搜...)",
        "Từ vựng Du lịch & Nhập khẩu thương mại",
    ]

    cycle_idx = 0
    while day <= 1500:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(hsk4_grammar)
            add_day(f"Ngữ pháp HSK4: {hsk4_grammar[gram_idx]}", phase4, "hsk4")
        elif mod == 1:
            voc_idx = (cycle_idx // 7) % len(vocab_hsk4_topics)
            add_day(f"Từ vựng HSK4: {vocab_hsk4_topics[voc_idx]} nhóm {(cycle_idx // 7) // len(vocab_hsk4_topics) + 1}", phase4, "hsk4")
        elif mod == 2:
            add_day(f"Chữ Hán HSK4: Cấu tạo từ ghép 3-4 chữ & Từ viết tắt nhóm {(cycle_idx // 7) + 1}", phase4, "hsk4")
        elif mod == 3:
            add_day("Đọc hiểu HSK4: Bài luận ngắn, văn bản triết lý & Phân tích ý chính", phase4, "hsk4")
        elif mod == 4:
            add_day("Nghe hiểu HSK4: Tin tức, Phỏng vấn, Talkshow tốc độ trung bình", phase4, "hsk4")
        elif mod == 5:
            add_day("Giao tiếp HSK4: Viết Email thương mại chuẩn & Trao đổi qua WeChat", phase4, "hsk4")
        else:  # mod == 6
            add_day("Ôn tập HSK4: Bài kiểm tra tổng hợp Ngữ pháp + Từ vựng + Dịch thuật", phase4, "hsk4")
        cycle_idx += 1

    # ==============================================================
    # PHASE 5: HSK5-6 & Học thuật / Văn viết (Day 1501 - 2000)
    # ==============================================================
    phase5 = "Phase 5: HSK5-6 & Học thuật / Văn viết (Day 1501 - 2000)"
    hsk56_grammar = [
        "Cấu trúc Văn viết trang trọng (书面语): 关于...的问题 — Về vấn đề...",
        "Cấu trúc 书面语: 对于...来说 — Đối với...mà nói",
        "Cấu trúc 书面语: 通过...的方式 — Thông qua phương thức...",
        "Cấu trúc 书面语: 随着...的发展 — Theo sự phát triển của...",
        "Cấu trúc 书面语: 在...的基础上 — Trên cơ sở của...",
        "Cấu trúc 书面语: 尽管如此 — Mặc dù vậy",
        "Cấu trúc 书面语: 从...角度来看 — Nhìn từ góc độ...",
        "Cấu trúc 书面语: 综上所述 — Tóm lại những điều trên",
        "Thành ngữ 4 chữ HSK5-6 nhóm 1: Phân tích nghĩa gốc & nghĩa bóng",
        "Thành ngữ 4 chữ HSK5-6 nhóm 2: Ứng dụng trong văn viết",
        "Thành ngữ 4 chữ HSK5-6 nhóm 3: Phân biệt thành ngữ tương đồng",
        "Từ Hán Việt thường gặp trong tiếng Trung học thuật nhóm 1",
        "Từ Hán Việt thường gặp trong tiếng Trung học thuật nhóm 2",
    ]

    cycle_idx = 0
    while day <= 2000:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(hsk56_grammar)
            add_day(f"Ngữ pháp HSK5-6: {hsk56_grammar[gram_idx]}", phase5, "hsk56")
        elif mod == 1:
            add_day(f"Từ vựng HSK5-6: Từ trừu tượng & Nghĩa bóng nhóm {(cycle_idx // 7) + 1}", phase5, "hsk56")
        elif mod == 2:
            add_day(f"Thành ngữ (Chengyu): Học & Phân tích 3 câu thành ngữ nâng cao nhóm {(cycle_idx // 7) + 1}", phase5, "hsk56")
        elif mod == 3:
            add_day("Đọc hiểu HSK5-6: Phân tích bài báo Baidu News, Xinhua, bình luận xã hội", phase5, "hsk56")
        elif mod == 4:
            add_day("Nghe hiểu HSK5-6: Thời sự nhanh, Podcast bản địa tốc độ cao", phase5, "hsk56")
        elif mod == 5:
            add_day("Dịch thuật HSK5-6: Dịch tài liệu Hợp đồng, Kỹ thuật, Y tế Việt-Trung", phase5, "hsk56")
        else:  # mod == 6
            add_day("Viết luận HSK5-6: Viết đoạn luận 100-150 chữ về một vấn đề xã hội", phase5, "hsk56")
        cycle_idx += 1

    # ==============================================================
    # PHASE 6: Native & Chuyên gia (Day 2001 - 2500)
    # ==============================================================
    phase6 = "Phase 6: Native & Chuyên gia (Day 2001 - 2500)"
    expert_topics = [
        "Tiếng lóng mạng Trung Quốc (网络流行语) cực trend — 绝绝子, 躺平, 内卷...",
        "Tiếng Trung Thương Mại: Kỹ năng Nhập hàng Taobao / 1688",
        "Tiếng Trung Thương Mại: Đàm phán và Ký kết Hợp đồng thực tế",
        "Tiếng Trung Chuyên ngành IT (人工智能, 大数据, 云计算, 编程...)",
        "Tiếng Trung Chuyên ngành Y tế & Điều dưỡng (护理, 处置, 病历...)",
        "Đọc tiểu thuyết mạng: Tiên hiệp / Ngôn tình / Đô thị (văn phong thực tế)",
        "Phương ngữ Bắc Kinh: Erhua nặng & Từ đặc trưng vùng",
        "Phương ngữ Quảng Đông: Nhận biết âm Cantonese so với Phổ thông",
        "Kỹ năng Thuyết trình (Presentation) chuyên nghiệp bằng Tiếng Trung",
        "Dịch Cabin & Phiên dịch nói: Kỹ năng Ghi chú (Note-taking)",
        "Văn hóa Trung Hoa: Tứ Đại Danh Tác và Điển tích thường dùng",
        "Lịch sử & Chính trị: Từ vựng cốt lõi để đọc hiểu tin tức thời sự",
    ]

    cycle_idx = 0
    while day <= 2500:
        topic_idx = cycle_idx % len(expert_topics)
        batch = (cycle_idx // len(expert_topics)) + 1
        add_day(f"Mastery: {expert_topics[topic_idx]} — Bài {batch}", phase6, "native")
        cycle_idx += 1

    return roadmap


def generate_markdown(roadmap_data):
    total = len(roadmap_data)
    md_lines = [
        "# 🀄 Lộ Trình Học Tiếng Trung – 2500 Ngày (Từ Pinyin Đến Native / Chuyên Gia)",
        "",
        "> ⚠️ **Lưu ý quan trọng về thời gian thực tế**: Tiếng Trung thuộc nhóm ngôn ngữ khó nhất với người Việt (hệ thống thanh điệu, chữ Hán phức tạp),",
        "> để đạt HSK6 cần khoảng **2.200-2.500 giờ** học tập tập trung, và thêm **1.000-1.500 giờ** immersion để đạt mức Native.",
        "> Với 30-45 phút/ngày (~0.6 giờ), thực tế sẽ mất khoảng **10-12 năm** để hoàn thành toàn bộ nội dung.",
        "> 2500 'Day' trong file này là số **ĐƠN VỊ NỘI DUNG** (content units), không phải số ngày dương lịch.",
        "> Ở Phase HSK4 trở lên, bạn có thể cần 2-3 ngày thực tế cho 1 'Day' để ôn lại và thực hành — hoàn toàn bình thường.",
        "> Muốn rút ngắn: tăng lên 60-90 phút/ngày. Trình độ Native luôn là quá trình immersion liên tục.",
        "",
        "> **Ký hiệu:** 🟢 HSK1 | 🟡 HSK2 | 🟠 HSK3-4 | 🔴 HSK5-6 | 🟣 Bản địa — Tất cả đều dùng nhịp 30-45 phút/ngày.",
        "",
        "> **Mục tiêu**: Học Tiếng Trung chuẩn sư phạm từ Bảng Pinyin đến cấp độ HSK6 và Cao cấp chuyên ngành.",
        "> **Phạm vi**: 6 Phase, 2500 ngày, bao phủ Pinyin, Ngữ pháp, Từ vựng, Chữ Hán, Nghe, Đọc, và Chuyên ngành.",
        "",
    ]

    for day_num in range(1, total + 1):
        if day_num not in roadmap_data:
            continue

        title, phase, level = roadmap_data[day_num]
        emoji, label, lvl_code = get_time(day_num)
        prev_topic = "Bắt đầu hành trình" if day_num == 1 else roadmap_data[day_num - 1][0]

        md_lines.append(f"## Day {day_num} — {title} ({emoji} {label})")
        md_lines.append("**Prompt:**")
        md_lines.append(f"Đóng vai trò là Gia sư tiếng Trung cấp cao (Native Teacher). Hôm nay là Day {day_num}: {title}.")
        md_lines.append(f"Giai đoạn: {phase}. Trình độ mục tiêu: {lvl_code.upper()}.")
        md_lines.append(f"Hôm qua chúng ta đã học: {prev_topic}.")
        md_lines.append("")
        md_lines.append("YÊU CẦU DẠY HỌC (Áp dụng theo thể loại bài — chỉ 30-45 phút):")
        md_lines.append("1. NẾU LÀ TỪ VỰNG / CHỮ HÁN: Phân tích cấu tạo chữ (Bộ thủ + Âm phù), cung cấp Mnemonic (câu chuyện ghi nhớ chữ Hán). Bắt buộc có Pinyin chuẩn và 3 từ ghép thực tế.")
        md_lines.append("2. NẾU LÀ NGỮ PHÁP: Cung cấp Cấu trúc, Cách dùng (Nuance ngữ cảnh), và 3 câu ví dụ (Chữ Hán + Pinyin + Dịch nghĩa Việt).")
        md_lines.append("3. NẾU LÀ ĐỌC/NGHE/GIAO TIẾP: Cung cấp đoạn hội thoại/đoạn văn mẫu (100-200 chữ) đúng trình độ.")
        md_lines.append("4. LỖI SAI CỦA NGƯỜI VIỆT (BẮT BUỘC): Chỉ ra người Việt Nam thường sai gì khi học phần này (VD: Lỗi phát âm thanh điệu, nói ngược ngữ pháp tiếng Việt, dùng nhầm từ đồng nghĩa). Cách khắc phục?")
        md_lines.append("")
        md_lines.append("BÀI TẬP THỰC HÀNH (Vừa vặn 30-45 phút):")
        md_lines.append("Giao cho tôi 3-5 câu bài tập để tôi tự làm. Chờ tôi làm xong rồi mới chấm điểm và sửa lỗi Pinyin/Chữ Hán cho tôi.")
        md_lines.append("")
        md_lines.append("**Bài tập:**")
        md_lines.append(f"⏱️ **Thời gian:** {label}")
        md_lines.append(f"📌 **Chủ đề hôm nay:** {title}")
        md_lines.append(f"🔗 **Ôn lại ngày trước:** {prev_topic}")
        md_lines.append("💻 **Tự thực hành:** Hoàn thành 3-5 câu bài tập do AI cung cấp ở trên và nộp lại để được chấm điểm.")
        md_lines.append("")
        md_lines.append(f"**Tags:** #chinese #day{day_num} #{lvl_code}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    with open(filepath, 'w', encoding='utf-8') as mf:
        mf.write('\n'.join(md_lines))


if __name__ == '__main__':
    data = build_roadmap()
    generate_markdown(data)
    print(f"✅ Generated: {filepath}")
    print(f"📊 Tổng số ngày: {len(data)}")
    print(f"   Phase 1 (HSK1):   Day 1   - 250")
    print(f"   Phase 2 (HSK2):   Day 251 - 600")
    print(f"   Phase 3 (HSK3):   Day 601 - 1000")
    print(f"   Phase 4 (HSK4):   Day 1001- 1500")
    print(f"   Phase 5 (HSK5-6): Day 1501- 2000")
    print(f"   Phase 6 (Native): Day 2001- 2500")
