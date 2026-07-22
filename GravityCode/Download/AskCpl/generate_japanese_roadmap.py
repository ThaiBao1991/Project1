# Generate Japanese Roadmap - 2500 Days (Zero to Native)
# Mỗi Day = 1 đơn vị nội dung, thời gian học cố định 30-45 phút/ngày
# Tổng 2500 ngày ~ 7 năm học liên tục để đạt trình độ Native/Chuyên gia

import os

filepath = r"c:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\roadmap_japanese_1000.md"

def get_time(day_num):
    """Trả về (emoji, label thời gian, lvl_code) — Luôn cố định 30-45 phút/ngày."""
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
        return ("🟣", "Bản địa/Chuyên gia — 30-45 phút", "native")

def build_roadmap():
    roadmap = {}
    day = 1

    def add_day(title, phase, level):
        nonlocal day
        roadmap[day] = (title, phase, level)
        day += 1

    # ==============================================================
    # PHASE 1: JLPT N5 & Nhập môn (Day 1 - 250)
    # ==============================================================
    phase1 = "Phase 1: JLPT N5 & Nhập môn (Day 1 - 250)"

    # Days 1-22: Hiragana, Katakana, Phát âm (giãn ra để học kỹ)
    hira_kata = [
        "Bảng chữ Hiragana: Hàng A (あ い う え お)",
        "Bảng chữ Hiragana: Hàng Ka, Sa (か き く け こ、さ し す せ そ)",
        "Bảng chữ Hiragana: Hàng Ta, Na (た ち つ て と、な に ぬ ね の)",
        "Bảng chữ Hiragana: Hàng Ha, Ma (は ひ ふ へ ほ、ま み む め も)",
        "Bảng chữ Hiragana: Hàng Ya, Ra, Wa, N (や ゆ よ、ら り る れ ろ、わ を ん)",
        "Hiragana: Âm đục (Dakuten) — が行, ざ行, だ行, ば行",
        "Hiragana: Âm bán đục (Handakuten) — ぱ行",
        "Hiragana: Âm ghép (Yōon) — きゃ, しゅ, ちょ... (36 âm)",
        "Hiragana: Âm ngắt (促音 っ) & Trường âm (長音 ー)",
        "Luyện đọc/viết Hiragana toàn bộ — Bài tập đọc câu đơn giản",
        "Bảng chữ Katakana: Hàng A, Ka, Sa (ア行, カ行, サ行)",
        "Bảng chữ Katakana: Hàng Ta, Na, Ha (タ行, ナ行, ハ行)",
        "Bảng chữ Katakana: Hàng Ma, Ya, Ra, Wa, N (マ行, ヤ行, ラ行, ワ行, ン)",
        "Katakana: Âm đục, Âm bán đục, Âm ghép, Trường âm (ー)",
        "Luyện đọc/viết Katakana toàn bộ — Đọc từ ngoại lai (ゲーム, コーヒー...)",
        "Quy tắc phát âm: Trọng âm Pitch Accent cơ bản (高低型)",
        "Từ vựng nhập môn: Chào hỏi & Lịch sự (挨拶 — Aisatsu)",
        "Từ vựng nhập môn: Số đếm 1-100 và cách đọc",
        "Từ vựng nhập môn: Ngày tháng năm, Thứ trong tuần",
        "Giới thiệu bản thân (自己紹介 — Jikoshoukai) bằng Tiếng Nhật",
        "Kanji cơ bản nhóm 1: 日 月 火 水 木 金 土 (Các ngày trong tuần)",
        "Kanji cơ bản nhóm 2: 一 二 三 四 五 六 七 八 九 十 百 千 万",
    ]
    for t in hira_kata:
        add_day(t, phase1, "n5")

    # Day 23-250: N5 Loop (7 loại bài xen kẽ)
    n5_grammar = [
        "N1 は N2 です — Khẳng định cơ bản (A là B)",
        "N1 は N2 じゃありません — Phủ định (A không phải B)",
        "Câu hỏi với trợ từ か — N1 は N2 ですか?",
        "Đại từ chỉ thị: これ (cái này), それ (cái đó), あれ (cái kia)",
        "Trợ từ sở hữu の — A の B (B của A)",
        "Đại từ chỉ địa điểm: ここ, そこ, あそこ (Chỗ này, chỗ đó, chỗ kia)",
        "Động từ dạng Masu: Khẳng định (〜ます) & Phủ định (〜ません)",
        "Trợ từ thời gian に & địa điểm hành động で",
        "Động từ di chuyển (行く, 来る, 帰る) + Trợ từ へ",
        "Trợ từ phương tiện で & người cùng làm と",
        "Ngoại động từ & Trợ từ を",
        "Mời rủ: 〜ませんか (Làm... không?) / 〜ましょう (Hãy cùng làm!)",
        "Tính từ đuôi NA (静かな, 親切な...) — Chia ở thể khẳng định/phủ định",
        "Tính từ đuôi I (大きい, 小さい...) — Chia ở thể khẳng định/phủ định",
        "So sánh hơn: N1 は N2 より 〜 (A hơn B)",
        "So sánh nhất: 〜の中で、N が 一番 〜 (... nhất trong...)",
        "Số đếm vật, người, tầng, tuổi — Lượng từ 個, 本, 枚, 人, 歳",
        "Lượng từ chỉ tần suất: 毎日, 時々, あまり〜ない",
        "Động từ Thể TE — Cách chia (Group 1, 2, 3)",
        "Cấu trúc đang làm gì: 〜ています (Trạng thái / Thói quen)",
        "Yêu cầu ai làm gì: 〜てください",
        "Xin phép: 〜てもいいですか / Cấm: 〜てはいけません",
        "Nối câu bằng Thể TE: て → và rồi (顔を洗って、朝ご飯を食べます)",
        "Động từ Thể NAI — Cách chia & Xin đừng: 〜ないでください",
        "Phải làm gì: 〜なければなりません / 〜ないといけません",
        "Thể từ điển (辞書形) — Cách chia & Có thể: 〜ことができます",
        "Sở thích: 趣味は 〜ことです (Sở thích của tôi là...)",
        "Trước khi làm gì: 〜前に、〜 (Trước khi V, làm B)",
        "Thể TA (〜た) — Cách chia: Đã từng (〜たことがあります)",
        "Làm nhiều việc: 〜たり、〜たりします",
        "Thể thông thường (Plain form) — Tổng hợp",
        "Tôi nghĩ rằng: 〜と思います",
        "Mệnh đề bổ nghĩa cho danh từ (Relative Clause cơ bản)",
        "Cho/Nhận: あげる (cho), もらう (nhận), くれる (ai cho mình)",
        "Câu điều kiện: 〜たら (Nếu làm... thì...) & 〜と",
    ]
    vocab_n5_topics = [
        "Gia đình (家族 — 父, 母, 兄, 姉...)",
        "Thời gian: Giờ, Phút, Ngày, Tháng",
        "Đồ vật xung quanh (本, テーブル, 電話, かばん...)",
        "Địa điểm (学校, 駅, 病院, スーパー...)",
        "Màu sắc và Hình dạng (赤, 青, 丸い, 大きい...)",
        "Động từ hằng ngày (食べる, 飲む, 起きる, 寝る...)",
        "Tính từ tính cách (優しい, 面白い, 静か, 親切...)",
        "Cơ thể người (頭, 目, 手, 足...)",
        "Giao thông (電車, バス, タクシー, 歩いて...)",
        "Ăn uống: Gọi món ở nhà hàng Nhật cơ bản",
    ]

    cycle_idx = 0
    while day <= 250:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(n5_grammar)
            add_day(f"Ngữ pháp N5: {n5_grammar[gram_idx]}", phase1, "n5")
        elif mod == 1:
            voc_idx = (cycle_idx // 7) % len(vocab_n5_topics)
            add_day(f"Từ vựng N5: Chủ đề {vocab_n5_topics[voc_idx]}", phase1, "n5")
        elif mod == 2:
            add_day(f"Kanji N5: 5 chữ Kanji cơ bản (Âm On/Kun/Bộ thủ/Mnemonic) nhóm {(cycle_idx // 7) + 1}", phase1, "n5")
        elif mod == 3:
            add_day(f"Đọc hiểu N5: Đoạn văn ngắn áp dụng {n5_grammar[(cycle_idx // 7) % len(n5_grammar)]}", phase1, "n5")
        elif mod == 4:
            add_day("Nghe hiểu N5: Hội thoại đời sống chậm & rõ — Luyện nhận diện âm Nhật", phase1, "n5")
        elif mod == 5:
            add_day("Giao tiếp N5: Shadowing (Nhại giọng) tình huống thực tế", phase1, "n5")
        else:  # mod == 6
            add_day("Ôn tập tổng hợp N5: Dịch xuôi/ngược Việt-Nhật & Mini test", phase1, "n5")
        cycle_idx += 1

    # ==============================================================
    # PHASE 2: JLPT N4 & Giao tiếp cơ bản (Day 251 - 600)
    # ==============================================================
    phase2 = "Phase 2: JLPT N4 & Giao tiếp cơ bản (Day 251 - 600)"
    n4_grammar = [
        "Vừa làm A vừa làm B: 〜ながら (Ăn cơm vừa xem TV)",
        "Đang làm dở / Kết quả còn tồn tại: 〜ています (nâng cao)",
        "Lỡ làm / Hoàn thành hết: 〜てしまいます (Ăn hết mất rồi!)",
        "Chuẩn bị trước: 〜ておきます (Làm sẵn để sau dùng)",
        "Dự định làm: 〜つもりです (Tôi dự định...)",
        "Kế hoạch đã lên: 〜予定です (Theo kế hoạch, sẽ...)",
        "Lời khuyên: 〜ほうがいいです (Nên làm... hơn)",
        "Suy đoán lịch sự: 〜でしょう (Chắc là...)",
        "Khả năng: 〜かもしれません (Có thể là...)",
        "Thể Mệnh lệnh: 〜ろ / 〜なさい (Làm đi! — khẩu ngữ mạnh)",
        "Giải thích, Định nghĩa: 〜という意味です (Có nghĩa là...)",
        "Truyền đạt lời ai: 〜と言っていました (Anh ấy nói rằng...)",
        "Làm xong rồi mới: 〜てから (Sau khi làm A, mới làm B)",
        "Câu điều kiện 〜ば (Nếu A thì B — điều kiện thuần túy)",
        "Câu điều kiện 〜なら (Nếu thực sự là A thì...)",
        "Mục đích: 〜ように (Để có thể...)",
        "Trở nên: 〜ようになります (Bây giờ đã có thể...)",
        "Bị động (受身形): Cách chia & Bị ai làm gì",
        "Bị động trong hoàn cảnh khó chịu: 雨に降られた",
        "Sai khiến (使役形): Cách chia & Ý nghĩa",
        "Xin phép làm gì (Sai khiến khiêm nhường): 〜させていただけませんか",
        "Bị động Sai khiến (使役受身形): Bị bắt phải làm",
        "Tôn kính ngữ (尊敬語): お/ご + 動詞, いらっしゃる, おっしゃる...",
        "Khiêm nhường ngữ (謙譲語): まいる, おる, いただく...",
        "Vẻ bề ngoài: 〜そうです (Trông có vẻ...) — tiếp xúc trực tiếp",
        "Quá mức: 〜すぎます (Quá... đến mức)",
        "Dễ / Khó: 〜やすい / 〜にくい (Dễ làm / Khó làm)",
        "Quyết định: 〜にします / 〜ことにします",
    ]
    vocab_n4_topics = [
        "Công việc part-time (アルバイト — バイト)",
        "Du lịch: Ở khách sạn & Tham quan",
        "Mua sắm: Quần áo & Đặt hàng online",
        "Sức khỏe: Ở bệnh viện & Kê đơn thuốc",
        "Thời tiết nâng cao & Dự báo",
        "Máy móc & Gia dụng (エアコン, 洗濯機...)",
        "Sở thích nâng cao (読書, 旅行, 料理, 写真...)",
        "Cảm xúc & Phản ứng (驚く, 感動する, 安心する...)",
        "Thiên nhiên & Môi trường (山, 川, 海, 森...)",
        "Cuộc sống hàng ngày: Thói quen buổi sáng & tối",
    ]

    cycle_idx = 0
    while day <= 600:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(n4_grammar)
            add_day(f"Ngữ pháp N4: {n4_grammar[gram_idx]}", phase2, "n4")
        elif mod == 1:
            voc_idx = (cycle_idx // 7) % len(vocab_n4_topics)
            add_day(f"Từ vựng N4: Chủ đề {vocab_n4_topics[voc_idx]}", phase2, "n4")
        elif mod == 2:
            add_day(f"Kanji N4: 5 chữ Kanji cấp N4 (Âm On/Kun/Từ ghép/Mnemonic) nhóm {(cycle_idx // 7) + 1}", phase2, "n4")
        elif mod == 3:
            add_day("Đọc hiểu N4: Thư từ, email, tin nhắn thông báo ngắn", phase2, "n4")
        elif mod == 4:
            add_day("Nghe hiểu N4: Thông báo ở ga tàu, siêu thị & Dặn dò của người trên", phase2, "n4")
        elif mod == 5:
            add_day("Giao tiếp N4: Xin lỗi, Nhờ vả, Xin phép một cách lịch sự", phase2, "n4")
        else:  # mod == 6
            add_day("Ôn tập N4: Bài test mini Ngữ pháp + Từ vựng + Kanji", phase2, "n4")
        cycle_idx += 1

    # ==============================================================
    # PHASE 3: JLPT N3 & Tiếng Nhật Trung cấp (Day 601 - 1000)
    # ==============================================================
    phase3 = "Phase 3: JLPT N3 & Tiếng Nhật Trung cấp (Day 601 - 1000)"
    n3_grammar = [
        "Về việc...: 〜について (Về...) / 〜に関して (Liên quan đến...)",
        "Đối với...: 〜にとって (Đối với ai) / 〜に対して (Đối mặt với...)",
        "Theo như...: 〜によって (Do / Bởi) / 〜によると (Theo nguồn tin...)",
        "Mặc dù...: 〜のに (Đáng lẽ phải... nhưng lại...) — Không như kỳ vọng",
        "Mặc dù... (tính cách): 〜くせに (Đã biết... mà vẫn...)",
        "Đầy rẫy: 〜だらけ / Toàn là: 〜ばかり",
        "Giống như là: 〜みたい / 〜らしい (khách quan) / 〜っぽい (có vẻ)",
        "Đang lúc: 〜最中 (đúng lúc đang...) / 〜ところ (vừa làm xong / sắp làm)",
        "Vừa mới: 〜たばかり / 〜たところ (vừa xong ngay lúc này)",
        "Ngay khi: 〜とたん (vừa... đã ngay lập tức) / 〜次第 (ngay khi xong)",
        "Không cần: 〜ことはない (Không cần phải lo...)",
        "Chắc chắn là: 〜に違いない / 〜はずだ (theo lẽ thường thì...)",
        "Không thể nào: 〜わけがない / 〜はずがない (không thể nào...)",
        "Chỉ còn cách: 〜しかない (chỉ còn mỗi cách là...)",
        "Tiện thể: 〜ついでに (Tiện thể đang làm A, cũng làm B)",
        "Nhân cơ hội: 〜をきっかけに (Lấy sự kiện X làm bàn đạp)",
        "Bao gồm cảm xúc: 〜を込めて (Gửi gắm vào đó...)",
        "Đương nhiên: 〜に決まっている (Đương nhiên là như vậy)",
        "Dù A mà B: 〜にもかかわらず (Dù có... mà vẫn...)",
        "Số lượng lớn: 〜にわたって (Kéo dài / Trải rộng...)",
    ]

    cycle_idx = 0
    while day <= 1000:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(n3_grammar)
            add_day(f"Ngữ pháp N3: {n3_grammar[gram_idx]}", phase3, "n3")
        elif mod == 1:
            add_day(f"Từ vựng N3: Collocations (Cụm từ đi chung) phổ biến nhóm {(cycle_idx // 7) + 1}", phase3, "n3")
        elif mod == 2:
            add_day(f"Kanji N3: Phân biệt Kanji dễ nhầm & Từ ghép Jukugo (2-3 chữ) nhóm {(cycle_idx // 7) + 1}", phase3, "n3")
        elif mod == 3:
            add_day("Đọc hiểu N3: Skimming ý chính bài báo ngắn / tạp chí dễ", phase3, "n3")
        elif mod == 4:
            add_day("Nghe hiểu N3: Hội thoại có Suisoku (Phỏng đoán ý người nói) ẩn ý", phase3, "n3")
        elif mod == 5:
            add_day("Giao tiếp N3: Keigo (Kính ngữ) trong môi trường quán ăn, baito", phase3, "n3")
        else:  # mod == 6
            add_day("Ôn tập N3: Viết đoạn văn ngắn + Sửa lỗi sai phổ biến người Việt", phase3, "n3")
        cycle_idx += 1

    # ==============================================================
    # PHASE 4: JLPT N2 & Tiếng Nhật Công sở (Day 1001 - 1500)
    # ==============================================================
    phase4 = "Phase 4: JLPT N2 & Tiếng Nhật Công sở (Day 1001 - 1500)"
    n2_grammar = [
        "〜あげく — Sau cùng / Kết quả xấu sau một quá trình dài",
        "〜あまり — Vì quá... đến mức (cảm xúc mạnh)",
        "〜以上(は) — Đã... thì (trách nhiệm / tất yếu)",
        "〜一方(で) — Trong khi đó, mặt khác (tương phản)",
        "〜上で — Sau khi làm A / Trên nền tảng A",
        "〜おかげで / 〜せいで — Nhờ / Tại (kết quả tốt / xấu)",
        "〜恐れがある — Có nguy cơ / Sợ rằng sẽ...",
        "〜限り — Chừng nào còn / Trong phạm vi",
        "〜がち — Hay / Thường bị / Có xu hướng bị",
        "〜からいうと — Xét theo / Nhìn từ góc độ",
        "〜からして — Ngay cả / Chỉ riêng... đã cho thấy",
        "〜きり — Chỉ / Từ đó không... nữa",
        "〜ことだから — Vì đây là A, nên (không có gì lạ)",
        "〜ざるを得ない — Không thể không... (bị bắt buộc)",
        "〜次第だ — Tùy thuộc vào... / Lý do là...",
        "〜っこない — Không thể nào (mạnh hơn はずない)",
        "〜つつある — Đang dần dần... (tiến trình đang diễn ra)",
        "〜て以来 — Từ khi... đến nay (kể từ đó)",
        "〜ということだ — Nghe nói / Có nghĩa là",
        "〜どころではない — Không phải lúc để... (bận quá)",
        "〜ないことには — Nếu không làm A thì không thể làm B",
        "〜に越したことはない — Càng... càng tốt (không gì bằng)",
        "〜にすぎない — Chỉ không hơn không kém / Chỉ là...",
        "〜に相違ない — Chắc chắn là (văn viết trang trọng)",
        "〜にかけては — Về mặt / Về lĩnh vực... (thế mạnh)",
        "〜にこたえて — Đáp lại / Hồi đáp yêu cầu",
        "〜に沿って — Dọc theo / Theo đúng (hướng/phương châm)",
        "〜をもって — Bằng / Kể từ (chính thức, văn bản)",
    ]

    cycle_idx = 0
    while day <= 1500:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(n2_grammar)
            add_day(f"Ngữ pháp N2: Cấu trúc {n2_grammar[gram_idx]} — Nuance & Ứng dụng", phase4, "n2")
        elif mod == 1:
            add_day(f"Từ vựng N2: Kinh tế / Xã hội / Công sở nhóm {(cycle_idx // 7) + 1}", phase4, "n2")
        elif mod == 2:
            add_day(f"Kanji N2: Phân tích Hán tự khó qua Bộ thủ & Onyomi nhóm {(cycle_idx // 7) + 1}", phase4, "n2")
        elif mod == 3:
            add_day("Đọc hiểu N2: Scanning văn bản triết lý / nghị luận / luận điểm", phase4, "n2")
        elif mod == 4:
            add_day("Nghe hiểu N2: Bản tin thời sự tốc độ vừa & Phân tích nội dung", phase4, "n2")
        elif mod == 5:
            add_day("Business Japanese: Viết Email thương mại chuẩn (Kính ngữ nâng cao)", phase4, "n2")
        else:  # mod == 6
            add_day("Giao tiếp N2: Phản biện & Đưa ra ý kiến trong cuộc họp", phase4, "n2")
        cycle_idx += 1

    # ==============================================================
    # PHASE 5: JLPT N1 & Học thuật / Văn học (Day 1501 - 2000)
    # ==============================================================
    phase5 = "Phase 5: JLPT N1 & Học thuật / Văn học (Day 1501 - 2000)"
    n1_grammar = [
        "〜いかんによっては — Tùy thuộc vào / Dựa trên (rất trang trọng)",
        "〜をおいて(ほかに)ない — Ngoài... ra không ai/cái nào khác",
        "〜ともなく / 〜ともなしに — Làm gì đó không chủ tâm",
        "〜を皮切りに — Bắt đầu từ / Lấy... làm điểm khởi đầu",
        "〜ならではの — Đặc trưng riêng của / Chỉ... mới có",
        "〜に足る / 〜に足りない — Xứng đáng / Không đáng",
        "〜べからず — Nghiêm cấm (văn cổ, thông báo)",
        "〜まじき — Không nên / Không được phép làm (văn trang trọng)",
        "〜なしに(は) — Không có... không thể (điều kiện tất yếu)",
        "〜ことなく — Mà không... / Không một lần nào",
        "〜ものを — Đáng lẽ ra... nhưng (nuối tiếc, trách cứ)",
        "〜が最後 — Một khi đã... thì chắc chắn (tiêu cực)",
        "〜んがために — Để đạt được / Vì mục đích... (văn viết)",
        "〜までもない — Không cần thiết phải đến mức...",
    ]

    cycle_idx = 0
    while day <= 2000:
        mod = cycle_idx % 6
        if mod == 0:
            gram_idx = (cycle_idx // 6) % len(n1_grammar)
            add_day(f"Ngữ pháp N1: {n1_grammar[gram_idx]} — Văn viết & Cổ ngữ", phase5, "n1")
        elif mod == 1:
            add_day(f"Từ vựng N1: Thành ngữ (慣用句 Kanyouku) & Tứ tự thành ngữ (四字熟語) nhóm {(cycle_idx // 6) + 1}", phase5, "n1")
        elif mod == 2:
            add_day(f"Kanji N1: Hán tự độ khó cao, ít dùng hằng ngày nhóm {(cycle_idx // 6) + 1}", phase5, "n1")
        elif mod == 3:
            add_day("Đọc hiểu N1: Phân tích bài báo Yomiuri / Asahi Shimbun — Xác định luận điểm chính", phase5, "n1")
        elif mod == 4:
            add_day("Nghe hiểu N1: Bản tin thời sự nhanh & Hội thoại tốc độ bản địa", phase5, "n1")
        else:  # mod == 5
            add_day("Dịch thuật N1: Dịch tài liệu Kỹ thuật / Hợp đồng kinh tế Việt-Nhật", phase5, "n1")
        cycle_idx += 1

    # ==============================================================
    # PHASE 6: Native & Chuyên gia (Day 2001 - 2500)
    # ==============================================================
    phase6 = "Phase 6: Native & Chuyên gia (Day 2001 - 2500)"
    expert_topics = [
        "Yojijukugo (四字熟語 — Tứ tự thục ngữ) phổ biến trong đời sống",
        "Tiếng lóng Nhật (スラング) & Văn hóa Pop (Anime/Manga/Game)",
        "Từ vựng Chuyên ngành IT: Lập trình, AI, Mạng (プログラミング, AI, ネット...)",
        "Từ vựng Chuyên ngành Business: Tài chính, Kế toán, Quản lý",
        "Từ vựng Chuyên ngành Y tế & Điều dưỡng (看護, 診断, 処置...)",
        "Đọc Văn học Nhật: Natsume Soseki (夏目漱石) — 坊っちゃん",
        "Đọc Văn học Nhật: Haruki Murakami (村上春樹) — Văn phong hiện đại",
        "Keigo cấp cao: Kính ngữ dùng khi tiếp Khách hàng VIP",
        "Pitch Accent (Trọng âm) nâng cao & Giọng địa phương Kansai-ben cơ bản",
        "Kỹ năng Thuyết trình (Presentation) chuyên nghiệp bằng Tiếng Nhật",
        "Dịch Cabin & Phiên dịch nói: Kỹ năng Ghi chú (Note-taking)",
        "Văn hóa Nhật Bản: Cấu trúc xã hội, Nghi lễ, Tết Oshōgatsu...",
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
        "# 🗾 Lộ Trình Học Tiếng Nhật – 2500 Ngày (Từ Zero Đến Native / Chuyên Gia)",
        "",
        "> ⚠️ **Lưu ý quan trọng về thời gian thực tế**: Tiếng Nhật được FSI xếp vào nhóm ngôn ngữ khó nhất với người nói tiếng Việt (Hiragana, Katakana, Kanji, và hệ thống Kính ngữ phức tạp),",
        "> để đạt N1 cần khoảng **3.000-4.000 giờ** học tập, và thêm **1.000-2.000 giờ** immersion để đạt mức gần Native.",
        "> Với 30-45 phút/ngày (~0.6 giờ), thực tế sẽ mất khoảng **12-15 năm** để hoàn thành toàn bộ nội dung.",
        "> 2500 'Day' trong file này là số **ĐƠN VỊ NỘI DUNG** (content units), không phải số ngày dương lịch.",
        "> Ở Phase N2 trở lên, bạn có thể cần 2-4 ngày thực tế cho 1 'Day' để ôn lại, tra từ và thực hành — hoàn toàn bình thường.",
        "> Muốn rút ngắn: tăng lên 60-90 phút/ngày. Trình độ Native luôn là quá trình immersion liên tục.",
        "",
        "> **Ký hiệu:** 🟢 Vỡ lòng/N5 | 🟡 N4 | 🟠 N3-N2 | 🔴 N1 | 🟣 Bản địa — Tất cả đều dùng nhịp 30-45 phút/ngày.",
        "",
        "> **Mục tiêu**: Học Tiếng Nhật chuẩn sư phạm từ Bảng chữ cái đến JLPT N1 và Cao cấp chuyên ngành.",
        "> **Phạm vi**: 6 Phase, 2500 ngày, bao phủ Ngữ pháp, Từ vựng, Kanji, Nghe, Đọc, Kính ngữ (Keigo) và Chuyên ngành.",
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
        md_lines.append(f"Đóng vai trò là Gia sư tiếng Nhật cấp cao (Native Teacher). Hôm nay là Day {day_num}: {title}.")
        md_lines.append(f"Giai đoạn: {phase}. Trình độ mục tiêu: {lvl_code.upper()}.")
        md_lines.append(f"Hôm qua chúng ta đã học: {prev_topic}.")
        md_lines.append("")
        md_lines.append("YÊU CẦU DẠY HỌC (Tùy theo loại bài — chỉ 30-45 phút, đừng quá tải):")
        md_lines.append("1. NẾU LÀ TỪ VỰNG/KANJI: Cung cấp Âm On/Kun, Bộ thủ, câu chuyện ghi nhớ (Mnemonic), và 3 từ ghép phổ biến nhất. Kèm Pitch Accent (Trọng âm) nếu có thể.")
        md_lines.append("2. NẾU LÀ NGỮ PHÁP: Cung cấp Cấu trúc, Cách chia, Ý nghĩa, Sắc thái (Nuance — dùng khi nào, với ai), và 3 câu ví dụ (Kanji + Hiragana + Romaji + Dịch Việt).")
        md_lines.append("3. NẾU LÀ ĐỌC/NGHE/GIAO TIẾP: Đưa ra một đoạn hội thoại/đoạn văn mẫu (100-200 chữ) đúng trình độ, có từ vựng liên quan.")
        md_lines.append("4. CHỈ RA LỖI SAI PHỔ BIẾN (BẮT BUỘC): Người Việt Nam thường mắc lỗi gì khi học phần này (ví dụ: nhầm trợ từ, quên phủ định, Keigo sai)? Cách khắc phục?")
        md_lines.append("")
        md_lines.append("BÀI TẬP THỰC HÀNH (Vừa vặn 30-45 phút):")
        md_lines.append("Giao cho tôi 3-5 câu bài tập (Dịch / Điền từ / Sửa lỗi) để tôi làm ngay bây giờ. Hãy chờ tôi trả lời để chấm điểm!")
        md_lines.append("")
        md_lines.append("**Bài tập:**")
        md_lines.append(f"⏱️ **Thời gian:** {label}")
        md_lines.append(f"📌 **Chủ đề hôm nay:** {title}")
        md_lines.append(f"🔗 **Ôn lại ngày trước:** {prev_topic}")
        md_lines.append("💻 **Tự thực hành:** Hoàn thành 3-5 câu bài tập do AI cung cấp ở trên và nộp lại để được chấm điểm.")
        md_lines.append("")
        md_lines.append(f"**Tags:** #japanese #day{day_num} #{lvl_code}")
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
    print(f"   Phase 1 (N5):     Day 1   - 250")
    print(f"   Phase 2 (N4):     Day 251 - 600")
    print(f"   Phase 3 (N3):     Day 601 - 1000")
    print(f"   Phase 4 (N2):     Day 1001- 1500")
    print(f"   Phase 5 (N1):     Day 1501- 2000")
    print(f"   Phase 6 (Native): Day 2001- 2500")
