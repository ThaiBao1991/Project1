# Generate English Roadmap - 2500 Days (Zero to Native)
# Mỗi Day = 1 đơn vị nội dung, thời gian học cố định 30-45 phút/ngày
# Tổng 2500 ngày ~ 7 năm học liên tục để đạt trình độ C2 + Near-Native

filepath = r"c:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\roadmap_english_2500.md"

def get_time(day_num):
    """Trả về (emoji, label, lvl_code) — cố định 30-45 phút/ngày."""
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


def build_roadmap():
    roadmap = {}
    day = 1

    def add(title, phase, level):
        nonlocal day
        roadmap[day] = (title, phase, level)
        day += 1

    # ==========================================================
    # PHASE 1: Vỡ lòng & Nền tảng Phát âm (Day 1 - 200)
    # ==========================================================
    phase1 = "Phase 1: Vỡ lòng & Nền tảng Phát âm (Day 1 - 200)"

    # Day 1-20: Phát âm nền tảng — học kỹ ngay từ đầu
    foundation = [
        "Bảng chữ cái tiếng Anh: 26 chữ & Tên gọi chuẩn (Aa, Bb, Cc...)",
        "Hệ thống IPA cơ bản: Cách đọc ký hiệu phiên âm (vowels & consonants)",
        "Nguyên âm ngắn (Short Vowels): /ɪ/ /e/ /æ/ /ɒ/ /ʌ/ /ʊ/ — Phân biệt & Luyện tập",
        "Nguyên âm dài (Long Vowels): /iː/ /ɑː/ /ɔː/ /uː/ /ɜː/ — Phân biệt & Luyện tập",
        "Nguyên âm đôi (Diphthongs): /eɪ/ /aɪ/ /ɔɪ/ /əʊ/ /aʊ/ /ɪə/ /eə/ /ʊə/",
        "Phụ âm dễ nhầm nhóm 1: /p/ vs /b/, /t/ vs /d/, /k/ vs /g/ (Hữu thanh vs Vô thanh)",
        "Phụ âm khó nhóm 2: /θ/ và /ð/ (th-) — Điểm yếu điển hình của người Việt",
        "Phụ âm khó nhóm 3: /v/ vs /w/, /l/ vs /r/ — Lỗi phổ biến nhất của người Việt",
        "Phụ âm nhóm 4: /ʃ/ /ʒ/ /tʃ/ /dʒ/ (sh, measure, church, judge)",
        "Phụ âm cuối từ (Final Consonants): Cách phát âm đuôi -s, -ed, -t, -d, -n, -ng",
        "Word Stress (Trọng âm từ) cơ bản: Quy tắc nhấn âm trong từ 2-3 âm tiết",
        "Sentence Stress (Trọng âm câu): Từ nào nhấn, từ nào đọc nhẹ trong câu",
        "Connected Speech nhóm 1: Linking (Nối âm) — consonant + vowel (pick_it_up)",
        "Connected Speech nhóm 2: Elision (Nuốt âm) — next day → nex' day",
        "Connected Speech nhóm 3: Assimilation (Biến âm) — Did you → Didja",
        "Intonation (Ngữ điệu): Lên giọng câu hỏi Yes/No, Xuống giọng câu trần thuật",
        "Intonation nâng cao: Giọng điệu liệt kê, Nghi ngờ, Nhấn mạnh",
        "Schwa /ə/ — Âm trung tâm, âm phổ biến nhất tiếng Anh (a-lone, the, a, about)",
        "Weak Forms (Dạng yếu): and /ən/, can /kən/, was /wəz/, to /tə/ trong câu nói nhanh",
        "Tổng ôn phát âm: Bài tập đọc đoạn văn chuẩn IPA và sửa lỗi",
    ]
    for t in foundation:
        add(t, phase1, "pre_a1")

    # Day 21-200: Pre-A1 Loop (chu kỳ 7)
    pre_a1_grammar = [
        "To be: am / is / are — Khẳng định, Phủ định, Câu hỏi",
        "Nouns: Danh từ số ít và số nhiều (regular & irregular: man/men, child/children)",
        "Articles: a / an / the — Quy tắc dùng và những lỗi người Việt hay mắc",
        "Pronouns: I, you, he, she, it, we, they / me, him, her, us, them",
        "Possessives: my, your, his, her, its, our, their / mine, yours, his...",
        "Demonstratives: this, that, these, those",
        "There is / There are — Diễn tả sự tồn tại",
        "Have / Has — Sở hữu và thành ngữ have a look, have fun...",
        "Simple Present: Cách chia + Quy tắc thêm -s/-es (he works, she watches)",
        "Simple Present: Phủ định với don't / doesn't",
        "Simple Present: Câu hỏi với Do / Does",
        "Present Continuous: am/is/are + Ving — Đang làm gì lúc này",
        "Adjectives: Vị trí (before noun / after be) & Order (beautiful big house)",
        "Adverbs of Frequency: always, usually, often, sometimes, never + vị trí trong câu",
        "Prepositions of Place: in, on, at, under, next to, between, behind",
        "Prepositions of Time: at (3pm), on (Monday), in (January / 2024)",
        "Can / Can't — Khả năng và Xin phép cơ bản",
        "Imperatives: Open the door! / Don't run! — Câu mệnh lệnh",
        "Question Words: What, Where, When, Who, Why, How + Cách đặt câu hỏi",
        "Simple Past: was/were và Regular verbs (-ed)",
    ]
    vocab_pre_a1 = [
        "Gia đình & Bạn bè (family, friend, mother, father, brother, sister...)",
        "Màu sắc & Hình dạng (red, blue, round, square...)",
        "Số đếm 1-1000 & Số thứ tự (first, second, third...)",
        "Ngày/Tháng/Năm (Monday, January, morning, afternoon...)",
        "Thời tiết (sunny, rainy, cold, hot, windy, cloudy...)",
        "Đồ vật trong nhà (table, chair, bed, sofa, kitchen, bathroom...)",
        "Thức ăn & Đồ uống (apple, rice, water, coffee, sandwich...)",
        "Giao thông & Địa điểm (bus, car, school, hospital, park, supermarket...)",
        "Nghề nghiệp (teacher, doctor, student, engineer, police, chef...)",
        "Hoạt động hằng ngày (wake up, eat breakfast, go to work, sleep...)",
        "Cơ thể người (head, eyes, hands, legs, stomach...)",
        "Tính từ mô tả cơ bản (tall, short, big, small, young, old, happy, sad...)",
    ]
    pron_pre_a1 = [
        "Luyện phát âm: Đọc to 20 từ thông dụng có IPA (cat, dog, book, food...)",
        "Minimal Pairs nhóm 1: ship/sheep, bit/beat, full/fool — Phân biệt bằng tai",
        "Minimal Pairs nhóm 2: pan/ban, ten/den, cold/gold — Hữu thanh vs Vô thanh",
        "Luyện Word Stress: 2-syllable nouns (TAble, CARrot, DOCtor, STUdent)",
        "Luyện Word Stress: 2-syllable verbs (deCIDE, reLAX, beGIN, forGET)",
        "Shadowing cơ bản: Nhại giọng theo đoạn hội thoại chậm (30 giây)",
        "Luyện -s/-es cuối từ: /s/ (cats), /z/ (dogs), /ɪz/ (buses) — Phân biệt 3 loại",
        "Luyện -ed cuối từ: /t/ (walked), /d/ (played), /ɪd/ (started)",
    ]

    cycle_idx = 0
    while day <= 200:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(pre_a1_grammar)
            add(f"Ngữ pháp Pre-A1: {pre_a1_grammar[gram_idx]}", phase1, "pre_a1")
        elif mod == 1:
            voc_idx = (cycle_idx // 7) % len(vocab_pre_a1)
            add(f"Từ vựng Pre-A1: Chủ đề {vocab_pre_a1[voc_idx]}", phase1, "pre_a1")
        elif mod == 2:
            pron_idx = (cycle_idx // 7) % len(pron_pre_a1)
            add(f"Phát âm Pre-A1: {pron_pre_a1[pron_idx]}", phase1, "pre_a1")
        elif mod == 3:
            add(f"Đọc hiểu Pre-A1: Đoạn văn ngắn 50-80 từ với từ vựng đã học", phase1, "pre_a1")
        elif mod == 4:
            add("Nghe hiểu Pre-A1: Hội thoại chậm & rõ — Điền từ còn thiếu (Dictation mini)", phase1, "pre_a1")
        elif mod == 5:
            add("Giao tiếp Pre-A1: Shadowing + Role-play tình huống thực tế (Chào hỏi, Tự giới thiệu)", phase1, "pre_a1")
        else:
            add("Ôn tập tổng hợp Pre-A1: Mini test Ngữ pháp + Từ vựng + Phát âm", phase1, "pre_a1")
        cycle_idx += 1

    # ==========================================================
    # PHASE 2: A1-A2 & Giao tiếp Cơ bản (Day 201 - 550)
    # ==========================================================
    phase2 = "Phase 2: A1-A2 & Giao tiếp Cơ bản (Day 201 - 550)"
    a1a2_grammar = [
        "Simple Past: Irregular verbs (go/went, eat/ate, see/saw, buy/bought...)",
        "Simple Past: Phủ định với didn't & Câu hỏi với Did",
        "Past Continuous: was/were + Ving — Đang làm gì tại thời điểm quá khứ",
        "Simple Past vs Past Continuous: When I came in, she was reading",
        "Future với 'going to': Plans & Intentions (I'm going to study...)",
        "Future với 'will': Predictions & Spontaneous decisions",
        "Present Perfect: have/has + V3 — Trải nghiệm & Kết quả liên quan đến hiện tại",
        "Present Perfect vs Simple Past: I have seen / I saw (Phân biệt rõ ràng)",
        "Countable vs Uncountable Nouns: some/any, much/many, a lot of, a little/a few",
        "Comparatives: taller than, more interesting than, better than, worse than",
        "Superlatives: the tallest, the most interesting, the best, the worst",
        "Modal Verbs: should/shouldn't — Lời khuyên & Nên làm gì",
        "Modal Verbs: must/mustn't — Bắt buộc & Cấm đoán",
        "Modal Verbs: have to / don't have to — Phải làm / Không cần làm",
        "Modal Verbs: might / may — Khả năng trong tương lai",
        "Conditional 0: If + Present, Present (Scientific facts & General truths)",
        "Conditional 1: If + Present, will — Điều kiện có thể xảy ra trong tương lai",
        "Relative Clauses cơ bản: who, which, that (The man who lives next door...)",
        "Passive Voice cơ bản: is/are + made/written/spoken (English is spoken worldwide)",
        "Reported Speech cơ bản: She said (that) she was tired",
        "Gerunds vs Infinitives: enjoy swimming, want to swim, like to swim / like swimming",
        "Phrasal Verbs cơ bản (20 phổ biến nhất): look up, give up, turn on, find out...",
        "Question Tags: You're coming, aren't you? / It's cold, isn't it?",
        "So / Neither: 'I like coffee.' 'So do I.' / 'I don't.' 'Neither do I.'",
    ]
    vocab_a1a2 = [
        "Sở thích & Hoạt động giải trí (hobbies, sports, music, movies, reading...)",
        "Du lịch & Giao thông (airport, hotel, train station, book a ticket, passport...)",
        "Mua sắm & Trang phục (clothes, sizes, price, sale, try on, pay...)",
        "Sức khỏe & Cơ thể (headache, fever, medicine, doctor, prescription...)",
        "Công việc & Môi trường làm việc (office, meeting, boss, colleague, salary...)",
        "Nhà & Sinh hoạt (neighborhood, rent, landlord, furniture, bills...)",
        "Thực phẩm & Nhà hàng (menu, order, recipe, ingredients, vegetarian...)",
        "Mô tả người: Tính cách & Ngoại hình (generous, stubborn, curly hair, slim...)",
        "Cảm xúc & Trạng thái (excited, nervous, bored, relieved, frustrated...)",
        "Công nghệ cơ bản (smartphone, app, download, upload, password, WiFi...)",
        "Thiên nhiên & Môi trường (mountain, ocean, forest, pollution, recycle...)",
        "Giáo dục & Trường học (subject, grade, exam, scholarship, graduate...)",
    ]
    pron_a1a2 = [
        "Word Stress: 3-syllable words (reSTAUrant, unDERstand, POSsible)",
        "Word Stress: Prefix & Suffix ảnh hưởng đến trọng âm (-tion, -ic, -ity)",
        "Weak Forms nâng cao: for /fə/, from /frəm/, of /əv/, them /ðəm/",
        "Intonation: Câu hỏi Wh- xuống giọng vs câu hỏi Yes/No lên giọng",
        "Shadowing A1: Nhại theo podcast chậm — Ghi chép những âm mình sai",
        "Luyện Connected Speech: 'What are you doing?' → /ˈwɒtərjuˈduɪŋ/",
        "Stress trong câu: Nhấn vào NEW information, đọc nhẹ những từ đã biết",
        "Rhythm & Weak Forms trong câu dài: 'I would like a cup of tea' → /aɪdlaɪkəˈkʌpətiː/",
    ]

    cycle_idx = 0
    while day <= 550:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(a1a2_grammar)
            add(f"Ngữ pháp A1-A2: {a1a2_grammar[gram_idx]}", phase2, "a1a2")
        elif mod == 1:
            voc_idx = (cycle_idx // 7) % len(vocab_a1a2)
            add(f"Từ vựng A1-A2: Chủ đề {vocab_a1a2[voc_idx]}", phase2, "a1a2")
        elif mod == 2:
            pron_idx = (cycle_idx // 7) % len(pron_a1a2)
            add(f"Phát âm A1-A2: {pron_a1a2[pron_idx]}", phase2, "a1a2")
        elif mod == 3:
            add(f"Đọc hiểu A1-A2: Đoạn văn 100-150 từ (truyện ngắn, email, quảng cáo)", phase2, "a1a2")
        elif mod == 4:
            add("Nghe hiểu A1-A2: Hội thoại đời sống tốc độ thường — Trả lời câu hỏi nội dung", phase2, "a1a2")
        elif mod == 5:
            add("Giao tiếp A1-A2: Shadowing + Role-play (Ở siêu thị, Hỏi đường, Ở nhà hàng)", phase2, "a1a2")
        else:
            add("Ôn tập A1-A2: Viết đoạn văn ngắn 80-100 từ + Mini test Ngữ pháp", phase2, "a1a2")
        cycle_idx += 1

    # ==========================================================
    # PHASE 3: B1 & Tiếng Anh Trung cấp (Day 551 - 950)
    # ==========================================================
    phase3 = "Phase 3: B1 & Tiếng Anh Trung cấp (Day 551 - 950)"
    b1_grammar = [
        "Present Perfect Continuous: have/has been + Ving — Hành động kéo dài đến hiện tại",
        "Past Perfect: had + V3 — Hành động xảy ra trước một thời điểm trong quá khứ",
        "Past Perfect Continuous: had been + Ving — Tiếp diễn hoàn thành quá khứ",
        "Future Perfect: will have + V3 — Sẽ đã hoàn thành vào một thời điểm tương lai",
        "Conditional 2: If + Past Simple, would — Điều kiện không có thật ở hiện tại",
        "Conditional 3: If + Past Perfect, would have — Điều kiện không thể xảy ra (quá khứ)",
        "Mixed Conditionals: If I had studied, I would be a doctor now",
        "Passive Voice nâng cao: Past Passive, Future Passive, Perfect Passive",
        "Reported Speech nâng cao: backshift tenses, reported questions & commands",
        "Relative Clauses nâng cao: whose, where, when + Non-defining clauses",
        "Participle Clauses: Walking home, I saw an accident / Exhausted, she went to bed",
        "Causative: have/get something done (I had my hair cut / I got my car fixed)",
        "Wish & If only: I wish I knew / I wish I had studied / I wish it would stop raining",
        "Modal Verbs for Deduction: must be, can't be, might be (present & past)",
        "Inversion: Not only did he..., Rarely have I seen..., Hardly had she...",
        "Cleft Sentences: It was John who... / What I need is... — Nhấn mạnh thành phần",
        "Noun Clauses: I know that... / I wonder whether... / What he said was...",
        "Ellipsis & Substitution: 'Are you coming?' 'I hope so.' / 'I think so too.'",
        "So/Such ... that: It was so hot that... / Such a mess that...",
        "Conjunctions & Discourse Markers: however, nevertheless, furthermore, as a result",
    ]
    vocab_b1_topics = [
        "Collocations nhóm 1: make/do/have/take + Noun (make a mistake, do research...)",
        "Collocations nhóm 2: Verb + Preposition (agree with, depend on, look forward to...)",
        "Idioms nhóm 1: Cơ thể người (break a leg, pull someone's leg, cost an arm and a leg...)",
        "Idioms nhóm 2: Màu sắc (out of the blue, green with envy, once in a blue moon...)",
        "Từ vựng Môi trường & Xã hội (climate change, renewable energy, poverty, equality...)",
        "Từ vựng Kinh doanh cơ bản (profit, budget, invest, negotiate, deadline, client...)",
        "Word Families nhóm 1: decide → decision → decisive → indecisive",
        "Word Families nhóm 2: vary → variety → various → variation → variable",
        "Từ đồng nghĩa & Sắc thái: big/large/huge/enormous, angry/furious/irritated",
        "False Friends Việt-Anh: embarrassed ≠ bối rối, sensible ≠ nhạy cảm...",
        "Phrasal Verbs nâng cao nhóm 1: bring up, put off, carry out, set up...",
        "Phrasal Verbs nâng cao nhóm 2: go through, come across, look into, rule out...",
    ]
    pron_b1 = [
        "Word Stress: Các tiền tố & hậu tố thay đổi stress (-tion, -ity, -ic, pre-, re-)",
        "Reduced vowels và Schwa /ə/ trong các âm tiết không nhấn",
        "Shadowing B1: Nhại giọng TED Talk ngắn — Tập trung vào nhịp điệu & pause",
        "Accent Awareness: Phân biệt British vs American (water, dance, can't, schedule)",
        "Luyện Fluency: Kỹ thuật Thought Groups — Đọc câu theo từng nhóm ý nghĩa",
        "Linking Words và âm nối phức tạp trong câu dài (Did you eat it? → /dɪdjuːiːtɪt/)",
    ]

    cycle_idx = 0
    while day <= 950:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(b1_grammar)
            add(f"Ngữ pháp B1: {b1_grammar[gram_idx]}", phase3, "b1")
        elif mod == 1:
            voc_idx = (cycle_idx // 7) % len(vocab_b1_topics)
            add(f"Từ vựng B1: {vocab_b1_topics[voc_idx]}", phase3, "b1")
        elif mod == 2:
            pron_idx = (cycle_idx // 7) % len(pron_b1)
            add(f"Phát âm B1: {pron_b1[pron_idx]}", phase3, "b1")
        elif mod == 3:
            add(f"Đọc hiểu B1: Bài báo ngắn / Blog / Truyện 200-300 từ — Skimming & Scanning", phase3, "b1")
        elif mod == 4:
            add("Nghe hiểu B1: Podcast chủ đề đời sống — Note key words & Summary", phase3, "b1")
        elif mod == 5:
            add("Giao tiếp B1: Shadowing Ted Talk ngắn + Nói về quan điểm cá nhân 2-3 phút", phase3, "b1")
        else:
            add("Viết B1: Viết đoạn luận ngắn 150-200 từ (Email, Review, Ý kiến cá nhân)", phase3, "b1")
        cycle_idx += 1

    # ==========================================================
    # PHASE 4: B2 & Tiếng Anh Thượng cấp (Day 951 - 1450)
    # ==========================================================
    phase4 = "Phase 4: B2 & Tiếng Anh Thượng cấp (Day 951 - 1450)"
    b2_grammar = [
        "Advanced Conditionals: Were it not for... / Had I known... / Should you need...",
        "Subjunctive Mood: I suggest that he go / It's important that she be informed",
        "Advanced Passives: It is said that... / He is thought to be... / supposed to",
        "Nominalization: điều động từ thành danh từ (decide → decision, destroy → destruction)",
        "Advanced Relative Clauses: a situation in which... / the reason why... / all of whom",
        "Fronting & Topicalization: 'This problem I have solved.' / 'Rarely do we see...'",
        "Ellipsis nâng cao: bỏ thành phần đã hiểu mà không mất nghĩa",
        "Hedging Language: I would argue... / It could be said... / To some extent...",
        "Advanced Concession: Despite / Although / Even though / While / Whereas / Yet",
        "Cohesion & Coherence: Cách viết đoạn văn mạch lạc (topic sentence, evidence, wrap-up)",
        "Register: Formal vs Informal — Phân biệt khi nào dùng gì",
        "Discourse Markers học thuật: Furthermore, Moreover, Nevertheless, Consequently...",
        "Intensifiers & Downgraders: absolutely, utterly, somewhat, rather, fairly",
        "Collocation với Adjective + Preposition: interested in, aware of, similar to...",
        "Advanced Phrasal Verbs với nghĩa idiom: put up with, come to terms with...",
    ]
    vocab_b2 = [
        "Collocations học thuật: conduct research, draw conclusions, raise awareness...",
        "Idioms nâng cao nhóm 1: Hit the nail on the head, bite the bullet, back to square one",
        "Idioms nâng cao nhóm 2: Beat around the bush, spill the beans, the ball is in your court",
        "Từ vựng Xã hội & Chính trị (democracy, policy, amendment, lobbyist, referendum...)",
        "Từ vựng Kinh tế (inflation, GDP, recession, fiscal, monetary, deficit, surplus...)",
        "Từ vựng Khoa học & Công nghệ (algorithm, data, hypothesis, breakthrough, AI, biotech...)",
        "IELTS Vocabulary: Academic Word List (AWL) nhóm 1 (analyze, approach, concept...)",
        "IELTS Vocabulary: Academic Word List (AWL) nhóm 2 (derive, evaluate, factor...)",
        "Word Building nâng cao: Prefix (mis-, over-, under-, inter-, counter-) + nghĩa",
        "Connotation: Positive/Negative nuance (slim vs skinny, assertive vs aggressive)",
        "Binomials & Trinomials: black and white, give and take, cool, calm and collected",
        "Clichés & Overused Phrases — Và cách thay thế bằng ngôn ngữ tinh tế hơn",
    ]
    pron_b2 = [
        "Advanced Word Stress: Compound nouns vs Compound adjectives (BLACKbird vs black BIRD)",
        "Emphatic Stress: I said I WANT coffee, not tea / It's CRUCIAL you understand",
        "Shadowing B2: BBC News, CNN 3-4 phút — Bắt chước cả nhịp, pause, intonation",
        "Accent Reduction: Sửa lỗi phổ biến của người Việt (thêm âm cuối, nuốt âm cuối)",
        "Fluency Drills: Luyện nói không dừng 60 giây về một chủ đề tự chọn",
        "Spontaneous Speech: Kỹ thuật Filler Sounds chuẩn (well, you know, I mean, let me think)",
    ]

    cycle_idx = 0
    while day <= 1450:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(b2_grammar)
            add(f"Ngữ pháp B2: {b2_grammar[gram_idx]}", phase4, "b2")
        elif mod == 1:
            voc_idx = (cycle_idx // 7) % len(vocab_b2)
            add(f"Từ vựng B2: {vocab_b2[voc_idx]}", phase4, "b2")
        elif mod == 2:
            pron_idx = (cycle_idx // 7) % len(pron_b2)
            add(f"Phát âm B2: {pron_b2[pron_idx]}", phase4, "b2")
        elif mod == 3:
            add("Đọc hiểu B2: Bài báo The Guardian / BBC News 400-500 từ — Phân tích cấu trúc lập luận", phase4, "b2")
        elif mod == 4:
            add("Nghe hiểu B2: TED Talk 10 phút — Note-taking + Summarize bằng tiếng Anh", phase4, "b2")
        elif mod == 5:
            add("Giao tiếp B2: IELTS Speaking Part 2 simulation — Nói 2 phút về một chủ đề", phase4, "b2")
        else:
            add("Viết B2: IELTS Task 2 style — Luận điểm 250 từ (Opinion / Discussion / Problem-Solution)", phase4, "b2")
        cycle_idx += 1

    # ==========================================================
    # PHASE 5: C1-C2 & Học thuật / Tiếng Anh Cao cấp (Day 1451 - 2000)
    # ==========================================================
    phase5 = "Phase 5: C1-C2 & Học thuật / Tiếng Anh Cao cấp (Day 1451 - 2000)"
    c1c2_grammar = [
        "Advanced Inversion for Emphasis: Not until... / Only by... / Never have I...",
        "Cleft Sentences nâng cao: What surprised me... / The reason why... / It was not until...",
        "Complex Nominalization: điều động từ/tính từ thành danh từ trong văn học thuật",
        "Ellipsis & Substitution trong văn nói và văn viết nâng cao",
        "Advanced Hedging & Academic Tentativeness (văn khoa học)",
        "Discourse Analysis: Cách nhận diện coherence & cohesion trong bài viết",
        "Pragmatics: Implicature — Những gì không nói nhưng được hiểu (indirect speech acts)",
        "Register shifts: Chuyển đổi văn phong linh hoạt (very formal ↔ casual)",
        "Advanced Conditional Structures: Were I you... / Had they realized... / But for...",
        "Stylistic Devices: Metaphor, Simile, Irony, Sarcasm, Understatement, Hyperbole",
        "Complex Sentence Structures trong văn học thuật & báo chí",
        "Syntax Variation: Câu đơn/Câu phức/Câu ghép — Khi nào dùng loại nào?",
    ]
    vocab_c1c2 = [
        "Academic Word List (AWL) nhóm 3: assess, contract, define, establish...",
        "Academic Word List (AWL) nhóm 4: generate, indicate, involve, maintain...",
        "Vocabulary for Critical Thinking: refute, corroborate, substantiate, contradict...",
        "Legal & Political Vocabulary nâng cao (jurisdiction, precedent, amendment, statute...)",
        "Medical & Scientific Vocabulary (pathology, diagnosis, empirical, hypothesis...)",
        "Literary Vocabulary: plot, narrative, protagonist, allegory, motif, denouement...",
        "Advanced Collocations với danh từ trừu tượng (deep-seated, far-reaching, far-fetched...)",
        "Proverbs & Their Meanings: 'A stitch in time saves nine' — Nguồn gốc & Cách dùng",
        "Cultural References: Shakespeare idioms, Bible allusions trong tiếng Anh hiện đại",
        "Neologisms & Contemporary English: FOMO, gaslight, ghosting, cancel culture...",
    ]

    cycle_idx = 0
    while day <= 2000:
        mod = cycle_idx % 6
        if mod == 0:
            gram_idx = (cycle_idx // 6) % len(c1c2_grammar)
            add(f"Ngữ pháp C1-C2: {c1c2_grammar[gram_idx]}", phase5, "c1c2")
        elif mod == 1:
            voc_idx = (cycle_idx // 6) % len(vocab_c1c2)
            add(f"Từ vựng C1-C2: {vocab_c1c2[voc_idx]}", phase5, "c1c2")
        elif mod == 2:
            add("Đọc hiểu C1-C2: Bài báo The Economist / Scientific American — Phân tích tư tưởng tác giả", phase5, "c1c2")
        elif mod == 3:
            add("Nghe hiểu C1-C2: Podcast native speed (Freakonomics, This American Life) — Transcription spot check", phase5, "c1c2")
        elif mod == 4:
            add("Giao tiếp C1-C2: Debate & Argumentation — Phản biện có cấu trúc về chủ đề xã hội", phase5, "c1c2")
        else:
            add("Viết C1-C2: Academic Essay / Report / Research Abstract 300-400 từ — Tiêu chuẩn IELTS 7.5+", phase5, "c1c2")
        cycle_idx += 1

    # ==========================================================
    # PHASE 6: Native & Gần bản địa (Day 2001 - 2500)
    # ==========================================================
    phase6 = "Phase 6: Near-Native & Chuyên gia (Day 2001 - 2500)"
    native_topics = [
        "Slang & Informal English: lit, vibe, lowkey, slay, no cap, GOAT — Cách dùng đúng ngữ cảnh",
        "British Slang vs American Slang: chuffed / bummed, knackered / exhausted, loo / restroom",
        "Humor & Sarcasm trong tiếng Anh: Khi nào nên/không nên dùng",
        "Stand-up Comedy Analysis: Cấu trúc jokes, timing, punch lines — Hiểu hài người bản địa",
        "Văn học Anh: George Orwell (1984, Animal Farm) — Phân tích ngôn ngữ & phong cách",
        "Văn học Mỹ: Ernest Hemingway / F. Scott Fitzgerald — Short story analysis",
        "Podcast immersion: The Daily (NYT), Serial, Radiolab — Hiểu 100% không có phụ đề",
        "Movie & TV Show Analysis: Friends, The Crown, Breaking Bad — Ngôn ngữ theo bối cảnh",
        "Business English nâng cao: Pitching, Negotiation, Conference calls chuẩn native",
        "Academic Writing: Cách viết Research Paper, Abstract, Literature Review chuẩn journal",
        "Public Speaking & Presentation: Kỹ thuật Steve Jobs, TED Talk structure",
        "Accent Mastery: Chọn 1 accent (British/American/Australian) và luyện đến level 90%",
    ]

    cycle_idx = 0
    while day <= 2500:
        topic_idx = cycle_idx % len(native_topics)
        batch = (cycle_idx // len(native_topics)) + 1
        add(f"Native Mastery: {native_topics[topic_idx]} — Bài {batch}", phase6, "native")
        cycle_idx += 1

    return roadmap


def generate_markdown(roadmap_data):
    total = len(roadmap_data)
    md_lines = [
        "# 🇬🇧 Lộ Trình Học Tiếng Anh – 2500 Ngày (Từ Vỡ Lòng Đến C2 + Gần Bản Địa)",
        "",
        "> ⚠️ **Lưu ý quan trọng về thời gian thực tế**: Tiếng Anh dễ tiếp cận hơn tiếng Nhật/Trung với người Việt (bảng chữ Latin, tiếp xúc nhiều qua truyền thông),",
        "> nhưng để đạt C2 vẫn cần khoảng **1.500-1.800 giờ** học tập chất lượng, và thêm **500-800 giờ** immersion để gần như bản địa.",
        "> Với 30-45 phút/ngày (~0.6 giờ), thực tế sẽ mất khoảng **7-9 năm calendar time** để hoàn thành toàn bộ nội dung.",
        "> 2500 'Day' trong file này là số **ĐƠN VỊ NỘI DUNG** (content units) theo khung CEFR Pre-A1 → C2 → Native, không phải số ngày dương lịch.",
        "> Ở các Phase B2 trở lên, bạn có thể cần 2-3 ngày thực tế cho 1 'Day' để ôn lại và thực hành đủ — hoàn toàn bình thường.",
        "> Muốn rút ngắn xuống ~4-5 năm cho C2: tăng lên 60-90 phút/ngày. Native-level luôn là quá trình immersion liên tục.",
        "",
        "> **Ký hiệu:** 🟢 Pre-A1 | 🟡 A1-A2 | 🟠 B1-B2 | 🔴 C1-C2 | 🟣 Gần bản địa — Tất cả đều dùng nhịp 30-45 phút/ngày.",
        "",
        "> **Mục tiêu**: Học Tiếng Anh chuẩn sư phạm từ Phát âm IPA nền tảng đến C2 + Near-Native.",
        "> **Phạm vi**: 6 Phase, 2500 ngày, bao phủ Ngữ pháp, Từ vựng, Phát âm (IPA), Nghe, Đọc, Nói, Viết, Idioms, Collocations, IELTS & Chuyên ngành.",
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
        md_lines.append(f"Đóng vai trò là Gia sư tiếng Anh 1-kèm-1 (Native-level). Hôm nay là Day {day_num}: {title}.")
        md_lines.append(f"Giai đoạn: {phase}. Trình độ mục tiêu: {lvl_code.upper().replace('_', '-')}.")
        md_lines.append(f"Nội dung hôm qua: {prev_topic}.")
        md_lines.append("")
        md_lines.append("YÊU CẦU DẠY HỌC (Áp dụng theo thể loại bài — chỉ 30-45 phút, vừa đủ tiêu hoá):")
        md_lines.append("1. NẾU LÀ NGỮ PHÁP: Giải thích Cấu trúc + Quy tắc + Sắc thái (Nuance — khi nào dùng, khi nào KHÔNG dùng). Cho 3 ví dụ câu thực tế (có IPA phát âm từ khó) + 1 lỗi sai phổ biến của người Việt và cách tránh.")
        md_lines.append("2. NẾU LÀ TỪ VỰNG / COLLOCATION / IDIOM: Cho nghĩa chính xác + IPA + Ví dụ câu tự nhiên. Chỉ rõ sắc thái (formal/informal, British/American nếu khác). Cho 3-5 collocations hoặc từ liên quan.")
        md_lines.append("3. NẾU LÀ PHÁT ÂM: Mô tả cách đặt lưỡi/môi cụ thể + cho ký hiệu IPA đầy đủ. Cho 5 từ ví dụ theo âm đó. Chỉ ra lỗi phát âm điển hình của người Việt (do ảnh hưởng tiếng Việt) và drill cụ thể.")
        md_lines.append("4. NẾU LÀ ĐỌC/NGHE/NÓI/VIẾT: Cung cấp đoạn văn/hội thoại mẫu 100-200 từ đúng trình độ. Chú thích từ mới + IPA. Giao nhiệm vụ cụ thể (tóm tắt, trả lời câu hỏi, viết lại...)")
        md_lines.append("5. LỖI SAI PHỔ BIẾN CỦA NGƯỜI VIỆT (BẮT BUỘC): Chỉ ra 2-3 lỗi người Việt hay mắc khi học phần này (do ảnh hưởng từ cấu trúc tiếng Việt). Giải thích vì sao sai và cách sửa.")
        md_lines.append("")
        md_lines.append("BÀI TẬP THỰC HÀNH (Vừa vặn 30-45 phút, không quá tải):")
        md_lines.append("Giao cho tôi 3-5 câu bài tập phù hợp (Dịch / Điền từ / Sửa lỗi / Tự đặt câu). Chờ tôi làm xong rồi mới chấm điểm và giải thích chi tiết.")
        md_lines.append("")
        md_lines.append("**Bài tập:**")
        md_lines.append(f"⏱️ **Thời gian:** {label}")
        md_lines.append(f"📌 **Chủ đề hôm nay:** {title}")
        md_lines.append(f"🔗 **Ôn lại hôm qua:** {prev_topic}")
        md_lines.append("💻 **Tự luyện:** Hoàn thành 3-5 câu bài tập do AI giao ở trên, nộp lại để được chấm điểm & giải thích chi tiết.")
        md_lines.append("")
        md_lines.append(f"**Tags:** #english #day{day_num} #{lvl_code}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    with open(filepath, "w", encoding="utf-8") as mf:
        mf.write("\n".join(md_lines))


if __name__ == "__main__":
    data = build_roadmap()
    generate_markdown(data)
    print("Done! Generated: " + filepath)
    print("Total days: " + str(len(data)))
    print("  Phase 1 (Pre-A1):  Day 1    - 200")
    print("  Phase 2 (A1-A2):   Day 201  - 550")
    print("  Phase 3 (B1):      Day 551  - 950")
    print("  Phase 4 (B2):      Day 951  - 1450")
    print("  Phase 5 (C1-C2):   Day 1451 - 2000")
    print("  Phase 6 (Native):  Day 2001 - 2500")
