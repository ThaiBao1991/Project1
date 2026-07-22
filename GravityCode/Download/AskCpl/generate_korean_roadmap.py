# Generate Korean Roadmap - 2500 Days (Zero to Native)
# Moi Day = 1 don vi noi dung, thoi gian hoc co dinh 30-45 phut/ngay
# Tong 2500 ngay ~ 7-9 nam hoc lien tuc de dat trinh do TOPIK6 + Near-Native

filepath = r"c:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\roadmap_korean_2500.md"

def get_time(day_num):
    """Tra ve (emoji, label, lvl_code) — co dinh 30-45 phut/ngay."""
    if day_num <= 200:
        return ("🟢", "Vo long/Hangul — 30-45 phut", "hangul")
    elif day_num <= 550:
        return ("🟡", "Co ban/TOPIK1-2 — 30-45 phut", "topik12")
    elif day_num <= 1000:
        return ("🟠", "Trung cap/TOPIK3 — 30-45 phut", "topik3")
    elif day_num <= 1500:
        return ("🟠", "Thuong cap/TOPIK4 — 30-45 phut", "topik4")
    elif day_num <= 2000:
        return ("🔴", "Cao cap/TOPIK5-6 — 30-45 phut", "topik56")
    else:
        return ("🟣", "Ban dia/Chuyen gia — 30-45 phut", "native")


def build_roadmap():
    roadmap = {}
    day = 1

    def add(title, phase, level):
        nonlocal day
        roadmap[day] = (title, phase, level)
        day += 1

    # ==========================================================
    # PHASE 1: Hangul & Phat am nen tang (Day 1 - 200)
    # ==========================================================
    phase1 = "Phase 1: Hangul & Nen tang Phat am (Day 1 - 200)"

    # Day 1-22: Hangul — hoc ky ngay tu dau
    hangul_foundation = [
        "Hangul: Cau tao chu Hangul — O (Block) = Am dau + Nguyen am + Am cuoi",
        "Hangul: 10 Nguyen am don co ban — a (a), ya (ya), eo (o), yeo (yo), o (o), yo (yo), u (u), yu (yu), eu (u), i (i)",
        "Hangul: 11 Nguyen am kep — ae, e, oe, wi, wa, wo, wae, we, ui, ya group",
        "Hangul: 14 Phu am co ban — g, n, d, r/l, m, b, s, silent, j, ch, k, t, p, h",
        "Hangul: 5 Phu am cang (Tensed consonants) — kk, tt, pp, ss, jj — DAC TRUNG kho nhat",
        "Hangul: 5 Phu am boc (Aspirated consonants) — k, t, p, ch, h — Phan biet Bi/Boc/Cang",
        "Hangul: Phu am cuoi (Batchim) don — Cach doc 7 loai am cuoi chuan: k, n, t, l, m, p, ng",
        "Hangul: Batchim kep — ss, nj, nh, lg, lm, lb, ls, lt, lp, lh — Quy tac doc",
        "Hangul: Quy tac phat am 1 — Lien am (Liaison): batchim + nguyen am lien tiep",
        "Hangul: Quy tac phat am 2 — Dong hoa (Assimilation): n+l, l+n, ng truoc g/k...",
        "Hangul: Quy tac phat am 3 — Tang cuong (Tensification): phu am sau am tat",
        "Hangul: Quy tac phat am 4 — Boc hoa (Aspiration): batchim h + phu am",
        "Hangul: Quy tac phat am 5 — Am tat cuoi, Thia am (Palatalisation)",
        "Luyen doc Hangul tong hop: doc 30 tu don pho bien + Chinh ta co ban",
        "Intonation tieng Han: Cau khang dinh / Cau hoi / Cam than — Nguoi Viet hay sai",
        "Am noi nhanh: Han quoc doc the nao khi noi binh thuong (khac viet)",
        "So dem thuan Han (일,이,삼...): 1-100 + Cach doc so phuc tap",
        "So dem thuan Han Quoc (하나,둘,셋...): 1-99 + Khi nao dung loai so dem nao",
        "Gio, ngay, thang, nam bang tieng Han — So dem + Don vi thoi gian",
        "Giao tiep khai pha: Xin chao, Cam on, Xin loi — Cach dung dung van canh",
        "Phat am tong on: Luyen doc doan van 50 tu co full Romanization va nghia Viet",
        "Hangul Typing: Cach go Hangul tren dien thoai / PC (ban phim tieng Han)",
    ]
    for t in hangul_foundation:
        add(t, phase1, "hangul")

    # Day 23-200: Loop chu ky 7
    pre_grammar = [
        "이다/아니다 — A la/khong phai la B + Cau khang dinh va phu dinh",
        "은/는 — Tro tu chu de: Phan biet voi 이/가 (tro tu chu ngu)",
        "이/가 — Tro tu chu ngu: Khi nao dung thay vi 은/는?",
        "을/를 — Tro tu tuc ngu: 밥을 먹다, 음악을 듣다",
        "에 — Tro tu dia diem (o, tai) va thoi gian (vao luc)",
        "에서 — Tro tu dia diem hanh dong dien ra (khac voi 에)",
        "로/으로 — Huong di / Phuong tien / Bang (cach)",
        "와/과, 하고, (이)랑 — Va / Cung voi (3 cach noi, muc do trang trong khac nhau)",
        "의 — So huu: 나의 가방 = Tui xach cua toi",
        "도 — Cung, nua: 나도 가요 = Toi cung di",
        "만 — Chi: 물만 마셔요 = Chi uong nuoc",
        "부터...까지 — Tu...den (thoi gian / dia diem)",
        "Dong tu: Chia the hinh thuc (Formal) vs the ban trang (Informal polite -아/어요)",
        "Dong tu: The phu dinh 안 + Dong tu / Tinh tu",
        "Dong tu: Cau hoi co/khong: Dong tu + 아요/어요? va Dong tu + 습니까?",
        "Tinh tu: Chia tinh tu nhu dong tu — 크다 → 커요 / 작다 → 작아요",
        "Dong tu the -고 싶다: Muon lam gi (dien dat uoc muon)",
        "The -고 싶어하다: Anh ay / Co ay muon... (noi ve uoc muon cua nguoi khac)",
        "The -고 싶다 phu dinh: 먹고 싶지 않아요 = Khong muon an",
        "The -ㄹ/을 거예요: Se / Du dinh lam gi trong tuong lai",
        "The -았/었어요: Da lam gi roi (qua khu hoan thanh)",
        "The -고 있어요: Dang lam gi (hien tai tep dien)",
        "Cau lenh / De nghi nhe nhang: -아/어 주세요",
        "The -ㄹ/을 수 있다/없다: Co the / Khong the lam duoc",
    ]
    vocab_pre = [
        "Gia dinh: 가족 — 아버지, 어머니, 형/오빠, 누나/언니, 남동생, 여동생",
        "Mau sac & Hinh dang — 빨간색, 파란색, 동그랗다, 네모나다",
        "Do an & Do uong Han Quoc — 김치찌개, 비빔밥, 삼겹살, 막걸리, 소주",
        "Giao thong & Dia diem — 지하철, 버스, 택시, 학교, 병원, 편의점",
        "Nghe nghiep — 선생님, 의사, 학생, 회사원, 요리사, 경찰관",
        "Hoat dong hang ngay — 일어나다, 밥 먹다, 출근하다, 퇴근하다, 자다",
        "Co the nguoi — 머리, 눈, 코, 입, 손, 발, 배",
        "Thoi tiet — 맑다, 흐리다, 비가 오다, 눈이 오다, 덥다, 춥다",
        "Canh xuc & Trang thai — 기쁘다, 슬프다, 피곤하다, 신나다, 화가 나다",
        "O truong / O cong ty — 수업, 시험, 회의, 보고서, 휴가, 출장",
        "Mua sam — 가격, 할인, 영수증, 교환, 환불, 계산",
        "Cong nghe co ban — 스마트폰, 앱, 인터넷, 비밀번호, 충전기",
    ]
    pron_pre = [
        "Luyen Batchim: Doc 20 tu co am cuoi khac nhau — Phan biet bang tai",
        "Lien am (Liaison): 먹어요 → [머거요], 입어요 → [이버요]",
        "Dong hoa: 한국 → [한국], 신라 → [실라] — Quy tac n+l, l+n",
        "Phu am Cang vs Boc vs Thuong: 가/카/까, 다/타/따, 바/파/빠 — Minimal pairs",
        "Shadowing co ban: Luyen nhai theo K-drama 30 giay — Chu y intonation Gak/Gak",
        "Lien am nang cao: 괜찮아요 → [괜차나요], 좋아요 → [조아요]",
        "Nhip dieu tieng Han: Danh trong am vao dau cum tu (Pitch trong tieng Han Seoul)",
        "Loi noi nhanh (Fast speech): 뭐해요? → /뭬요?/, 어디 가요? → /어디가요?/",
    ]

    cycle_idx = 0
    while day <= 200:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(pre_grammar)
            add("Ngu phap Hangul/Co ban: " + pre_grammar[gram_idx], phase1, "hangul")
        elif mod == 1:
            voc_idx = (cycle_idx // 7) % len(vocab_pre)
            add("Tu vung Nhat men: " + vocab_pre[voc_idx], phase1, "hangul")
        elif mod == 2:
            pron_idx = (cycle_idx // 7) % len(pron_pre)
            add("Phat am Hangul: " + pron_pre[pron_idx], phase1, "hangul")
        elif mod == 3:
            add("Doc hieu Vo long: Doan van 50-80 chu co Romanization va nghia Viet", phase1, "hangul")
        elif mod == 4:
            add("Nghe hieu Vo long: Hoi thoai cham & ro — Dien tu con thieu (Dictation mini)", phase1, "hangul")
        elif mod == 5:
            add("Giao tiep Vo long: Shadowing + Role-play (Chao hoi, Tu gioi thieu, Hoi duong)", phase1, "hangul")
        else:
            add("On tap tong hop Hangul: Mini test Ngu phap + Tu vung + Phat am co Romanization", phase1, "hangul")
        cycle_idx += 1

    # ==========================================================
    # PHASE 2: TOPIK 1-2 & Giao tiep Co ban (Day 201 - 550)
    # ==========================================================
    phase2 = "Phase 2: TOPIK 1-2 & Giao tiep Co ban (Day 201 - 550)"
    topik12_grammar = [
        "The -아서/어서: Boi vi / Va roi (nguyen nhan hoac trinh tu hanh dong)",
        "The -기 때문에: Boi vi (van viet, trang trong hon -아서)",
        "The -ㄴ/은데, -는데: Nhung ma / Ma thi / Trong truong hop ay... (da nang)",
        "The -지만: Nhung, mac du (noi 2 menh de trai nguoc)",
        "The -면/으면: Neu... thi... (cau dieu kien)",
        "The -거나: Hoac la ... hoac la (lua chon giua 2 viec)",
        "The -(으)ㄹ 때: Khi (dang lam / se lam) viec gi",
        "The -기 전에: Truoc khi lam gi",
        "The -ㄴ/은 후에: Sau khi lam gi",
        "The -(으)면서: Vua lam A vua lam B (dong thoi)",
        "The -(으)려고: De / Voi muc dich (dien dat muc tieu)",
        "The -기 위해서: De / Nham muc dich (van viet hon -(으)려고)",
        "The -(으)ㄹ게요: Toi se... (cam ket / y dinh cua nguoi noi)",
        "The -(으)ㄹ까요?: Chung ta ... nhe? / Lieu co khong? (de nghi hoac suy doan)",
        "The -(으)ㄹ 것 같다: Co ve nhu / Toi nghi la (suy doan)",
        "The -아/어 보다: Thu lam / Da tung (thu nghiem trai nghiem)",
        "The -아/어 보이다: Trong co ve, truong nhu (dien ta an tuong ben ngoai)",
        "The -게 되다: Tro nen / Dan tro thanh (su thay doi khong chu dong)",
        "The -아/어지다: Tro nen (su thay doi dan dan cua tinh trang)",
        "The -(으)ㄹ 수 없다: Khong the (Nang cao: cach dung tu nhien)",
        "Kinh ngu co ban (존댓말): -습니다/입니다 — Cach noi trang trong nhat",
        "Kinh ngu chu ngu: 아버지 → 아버님, 선생님 — Cach su dung dung",
        "Tinh tu chu ngu: 크다/커다 → 크신, 많다 → 많으신 — Khi noi ve nguoi lon tuoi",
        "Bat buoc phai: -(으)야 하다 / -(으)야 되다 — Phan biet 2 cau truc",
        "Khong can phai: -지 않아도 되다 / -지 않아도 괜찮다",
        "Cam doan: -면 안 되다 (Neu lam thi khong duoc)",
        "De nghi lam gi: -아/어 드릴까요? (Toi co the giup ban... khong?) — Kinh ngu",
    ]
    vocab_topik12 = [
        "So thich & Giai tri: 취미, 여행, 요리, 독서, 음악, 영화, 게임, 등산",
        "Du lich Han Quoc: 제주도, 경복궁, 명동, 홍대, 교통카드, 환전, 숙박",
        "Suc khoe & Benh vien: 아프다, 약, 병원, 처방전, 수술, 주사, 입원",
        "Mua sam & Trang phuc: 옷, 사이즈, 세일, 영수증, 교환, 환불, 카드",
        "Nha hang & Do an: 메뉴, 주문, 계산서, 포장, 배달, 맛있다, 맵다",
        "Dich vu cong: 은행, 우체국, 주민센터, 계좌, 이체, 공과금",
        "Cong ty & Lam viec: 회의, 출장, 보고서, 야근, 회식, 휴가, 월급",
        "Han quoc han lam viec: 회사원, 부장, 과장, 대리, 사원, 인턴",
        "Cong nghe: 스마트폰, SNS, 유튜브, 검색, 업로드, 다운로드",
        "Tinh cam & Quan he: 사랑, 우정, 친구, 선후배, 동료, 이별, 결혼",
        "Thoi tiet & Moi truong: 계절, 장마, 미세먼지, 태풍, 지진, 환경",
        "Giao duc: 대학교, 전공, 장학금, 졸업, 취업, 입학 시험",
    ]
    pron_topik12 = [
        "Intonation cau hoi vs cau tran thuat: Hoi thoai doc to va so sanh",
        "Noi nhanh / Nuot am: 뭐예요? → /뭐에요/, 괜찮아요 → /괜차나요/",
        "Phan biet am giong nhau: 바보/파파, 달/탈, 살/쌀 — Minimal pairs nang cao",
        "Shadowing TOPIK1: Luyen nhai hoi thoai tieng Han toc do binh thuong",
        "Nhip dieu & Stress trong cum tu tieng Han (Seoul Standard)",
        "Loi phat am pho bien cua nguoi Viet: Sai am ㅓ, ㅡ, am cang kk/tt/pp",
        "Lien am phuc tap: 않아요 → /아나요/, 싫어요 → /시러요/",
        "Luyen fluency: Noi khong dung 30 giay ve ban than bang tieng Han",
    ]

    cycle_idx = 0
    while day <= 550:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(topik12_grammar)
            add("Ngu phap TOPIK1-2: " + topik12_grammar[gram_idx], phase2, "topik12")
        elif mod == 1:
            voc_idx = (cycle_idx // 7) % len(vocab_topik12)
            add("Tu vung TOPIK1-2: " + vocab_topik12[voc_idx], phase2, "topik12")
        elif mod == 2:
            pron_idx = (cycle_idx // 7) % len(pron_topik12)
            add("Phat am TOPIK1-2: " + pron_topik12[pron_idx], phase2, "topik12")
        elif mod == 3:
            add("Doc hieu TOPIK1-2: Email / Tin nhan KakaoTalk / Quang cao don gian 100-150 chu", phase2, "topik12")
        elif mod == 4:
            add("Nghe hieu TOPIK1-2: Hoi thoai doi song toc do binh thuong — Tra loi cau hoi noi dung", phase2, "topik12")
        elif mod == 5:
            add("Giao tiep TOPIK1-2: Shadowing + Role-play thuc te (O sieu thi, Kham benh, Dat phong khach san)", phase2, "topik12")
        else:
            add("On tap TOPIK1-2: Viet doan van 80-100 chu + Mini test Ngu phap", phase2, "topik12")
        cycle_idx += 1

    # ==========================================================
    # PHASE 3: TOPIK 3 & Tieng Han Trung cap (Day 551 - 1000)
    # ==========================================================
    phase3 = "Phase 3: TOPIK 3 & Tieng Han Trung cap (Day 551 - 1000)"
    topik3_grammar = [
        "The -더니: Toi thay rang truoc kia... bay gio... (kinh nghiem ca nhan qua khu)",
        "The -더라고요: Hoa ra la... (nhan xet dua tren kinh nghiem thi nghiem)",
        "The -던: Tinh tu hoi tuong — 먹던 음식 (Mon an toi hay an truoc kia)",
        "The -았/었던: Hoi tuong viec da xay ra xong hoac trang thai da thay doi",
        "The -(으)ㄴ/는 척하다: Gia vo nhu la / Gia bo dang",
        "The -(으)ㄴ/는 셈이다: Coi nhu la / Ve co ban la",
        "The -(으)ㄹ 뻔하다: Suyt nua thi... (suy nghi o day!)",
        "The -(으)ㄹ 텐데: Le ra / Chac la se... nhung (ket hop dieu kien + ket qua)",
        "The -에 따라: Tuy theo / Phu thuoc vao (quan he dieu kien)",
        "The -에 대해(서): Ve chu de / Lien quan den",
        "The -에 비해(서): So voi / Tuong phan voi",
        "The -에 관해(서): Lien quan den (van viet hon -에 대해)",
        "The -은/는커녕: Khong nhung khong co A ma nguoc lai B (Thay vi... lai...)",
        "The -도록: De / Den muc ma (muc tieu / ket qua)",
        "The -느라고: Boi vi dang ban lam A ma... (giai thich ly do khong lam duoc B)",
        "The -는 바람에: Boi vi / Do (nguyen nhan bat ngo gay ra ket qua tieu cuc)",
        "The -고 보니: Sau khi lam/xem thi hoa ra... (kham pha sau hanh dong)",
        "The -다 보니: Cu lam mai thi roi... (ket qua tu nhien theo thoi gian)",
        "The -다 보면: Neu cu lam mai thi se... (du doan ket qua trong tuong lai)",
        "The -기로 하다: Quyet dinh lam / Nhat tri lam",
    ]
    vocab_topik3 = [
        "Thanh ngu tieng Han (관용어) nhom 1: 눈이 높다, 손이 크다, 입이 무겁다",
        "Thanh ngu tieng Han (관용어) nhom 2: 발이 넓다, 배가 아프다, 코가 납작해지다",
        "Tu vung Xa hoi & Moi truong: 환경 문제, 기후 변화, 재활용, 대기 오염",
        "Tu vung Kinh te co ban: 경제, 물가, 금리, 주식, 투자, 소비, 저축",
        "Tu vung Chinh tri & Xa hoi: 선거, 정부, 정책, 국회, 국민, 민주주의",
        "Han tu (한자어) pho bien nhom 1: 교육(敎育), 문화(文化), 사회(社會)",
        "Han tu (한자어) pho bien nhom 2: 경제(經濟), 정치(政治), 환경(環境)",
        "Tu dong nghia & Sac thai: 크다/거대하다/방대하다 — Khi nao dung cai nao",
        "Phrasal verbs tieng Han (Dong tu kep): 잡아당기다, 밀어내다, 끌어올리다",
        "Tu vung Tram cam: kinh ngu 주다/드리다, 먹다/드시다, 자다/주무시다",
        "Collocations pho bien: 결정을 내리다, 연락을 취하다, 책임을 지다",
        "Tu vung Y te nang cao: 증상, 진단, 처방, 수술, 입원, 퇴원, 재활",
    ]
    pron_topik3 = [
        "Shadowing TOPIK3: K-drama / KBS News nhai theo 1 phut",
        "Accent tieng Han Seoul vs tieng Han Gyeongsang (Mien Nam) — Nhan biet",
        "Phan biet loi noi trang trong va ban trang: 먹어요 vs 먹습니다 qua phat am",
        "Luyen noi Spontaneous 60 giay ve mot chu de — Dung tu nhien, khong doc script",
        "Filler words chuan tieng Han: 음..., 그러니까..., 뭐랄까..., 있잖아...",
        "Intonation nang cao: Bieu lo cam xuc qua giong — Ngan ngac, Vui, Buon, Buc boi",
    ]

    cycle_idx = 0
    while day <= 1000:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(topik3_grammar)
            add("Ngu phap TOPIK3: " + topik3_grammar[gram_idx], phase3, "topik3")
        elif mod == 1:
            voc_idx = (cycle_idx // 7) % len(vocab_topik3)
            add("Tu vung TOPIK3: " + vocab_topik3[voc_idx], phase3, "topik3")
        elif mod == 2:
            pron_idx = (cycle_idx // 7) % len(pron_topik3)
            add("Phat am TOPIK3: " + pron_topik3[pron_idx], phase3, "topik3")
        elif mod == 3:
            add("Doc hieu TOPIK3: Bai bao ngan / Blog 200-300 chu — Skimming & Tim y chinh", phase3, "topik3")
        elif mod == 4:
            add("Nghe hieu TOPIK3: KBS Radio / Podcast chu de doi song — Note-taking", phase3, "topik3")
        elif mod == 5:
            add("Giao tiep TOPIK3: Shadowing K-drama + Dien dat quan diem ca nhan 2-3 phut", phase3, "topik3")
        else:
            add("Viet TOPIK3: Viet doan van 150-200 chu (Cam nhan, Nhat ky, Email)", phase3, "topik3")
        cycle_idx += 1

    # ==========================================================
    # PHASE 4: TOPIK 4 & Tieng Han Thuong cap (Day 1001 - 1500)
    # ==========================================================
    phase4 = "Phase 4: TOPIK 4 & Tieng Han Thuong cap (Day 1001 - 1500)"
    topik4_grammar = [
        "The -(으)ㄹ 따름이다: Chi co the / Chi biet (cam giac bat luc hoac khiem ton)",
        "The -는 한: Mien la / Chung nao con (dieu kien can thiet)",
        "The -(으)ㄹ 뿐만 아니라: Khong nhung ma con (noi them thong tin)",
        "The -고도: Mac du / Dat duoc roi nhung van (bat ngo hoac ma sat)",
        "The -(으)ㄹ 만하다: Dang / Xung dang de (goi y tich cuc)",
        "The -에 달려 있다: Phu thuoc vao / Tuy thuoc vao",
        "The -(으)로 인해(서): Do / Boi vi (nguyen nhan — van viet trang trong)",
        "The -에 의해(서): Boi / Duoc thuc hien boi (bi dong — van viet)",
        "The -을/를 통해(서): Thong qua / Bang (phuong tien / cach thuc)",
        "The -을/를 바탕으로: Dua tren / Lay lam nen tang",
        "The -을/를 중심으로: Lam trung tam / Tap trung vao",
        "The -(으)ㄹ 수밖에 없다: Khong con cach nao khac ngoai viec (bat buoc phai)",
        "The -고 말다: Cuoi cung da... (ket qua khong mong muon xay ra)",
        "The -아/어 버리다: Lam xong het sach / Da het roi (nuance: nhe nhat / hoan toan)",
        "The -(으)ㄴ/는 만큼: Nhieu bang / Tuong xung voi (so sanh muc do)",
        "The -기에: Boi vi (nguyen nhan — van viet nang hon -기 때문에)",
        "Kinh ngu nang cao: Biet on qua 주셔서 감사합니다 vs 해 주셔서 감사합니다",
        "Kinh ngu phu dinh lich su: 드시지 않으세요?, 괜찮으세요?",
        "Van phong cong so: Bao cao, Trinh bay, Email chuyen nghiep tieng Han",
        "Nen tang van viet hoc thuat: Cach trien khai luan diem trong bai viet TOPIK",
    ]
    vocab_topik4 = [
        "Han tu (한자어) hoc thuat nhom 3: 가치(價値), 원칙(原則), 목표(目標)",
        "Han tu (한자어) hoc thuat nhom 4: 개념(概念), 방법(方法), 결과(結果)",
        "Collocations hoc thuat: 기준을 세우다, 문제를 해결하다, 입장을 취하다",
        "Thanh ngu phuc tap nhom 1: 도마 위에 오르다, 발등에 불이 떨어지다",
        "Thanh ngu phuc tap nhom 2: 새발의 피, 눈 가리고 아웅, 가재는 게 편이다",
        "Tu vung Cong nghe & IT: 인공지능, 빅데이터, 플랫폼, 스타트업, 알고리즘",
        "Tu vung Truyen thong & Mang xa hoi: 유튜버, 인플루언서, 댓글, 구독, 라이브",
        "Tu vung Phap ly & Hanh chinh: 계약서, 법률, 조항, 신청서, 민원, 규정",
        "Tu vung Y te chuyen nganh: 진단서, 수술 동의서, 의료 보험, 처방전",
        "Slang / Tieng long mang Han Quoc nhom 1: 갑분싸, 핵노잼, 킹받다, 떡상",
        "Slang tieng long nhom 2: 훈남/훈녀, 쩐다, 존맛, 개웃기다, 뻥치다",
        "Tu vung Van hoa Han: 눈치, 정(情), 빨리빨리, 한(恨), 눈치 문화",
    ]

    cycle_idx = 0
    while day <= 1500:
        mod = cycle_idx % 7
        if mod == 0:
            gram_idx = (cycle_idx // 7) % len(topik4_grammar)
            add("Ngu phap TOPIK4: " + topik4_grammar[gram_idx], phase4, "topik4")
        elif mod == 1:
            voc_idx = (cycle_idx // 7) % len(vocab_topik4)
            add("Tu vung TOPIK4: " + vocab_topik4[voc_idx], phase4, "topik4")
        elif mod == 2:
            add("Phat am TOPIK4: Shadowing KBS 뉴스 / YouTube goc Han — Bat chuoc 100%", phase4, "topik4")
        elif mod == 3:
            add("Doc hieu TOPIK4: Bai bao Naver / Daum 400-500 chu — Phan tich luan diem chinh", phase4, "topik4")
        elif mod == 4:
            add("Nghe hieu TOPIK4: Podcast ban dia toc do cao — Note key ideas & Summary", phase4, "topik4")
        elif mod == 5:
            add("Giao tiep TOPIK4: Trinh bay quan diem co cau truc + Phan bien 2-3 phut", phase4, "topik4")
        else:
            add("Viet TOPIK4: Bai luan TOPIK 600-700 chu — Kien truc luan diem chuan thi", phase4, "topik4")
        cycle_idx += 1

    # ==========================================================
    # PHASE 5: TOPIK 5-6 & Hoc thuat / Van viet (Day 1501 - 2000)
    # ==========================================================
    phase5 = "Phase 5: TOPIK 5-6 & Hoc thuat / Van viet (Day 1501 - 2000)"
    topik56_grammar = [
        "The -(으)로 보아: Nhin tu goc do / Xet theo (van viet phan tich)",
        "The -고 보면: Neu xem xet ky thi / Sau khi nhin lai",
        "The -기 마련이다: La dieu duong nhien / Chac chan phai vay",
        "The -(으)ㄹ 뿐이다: Chi la / Chi the thoi (khong hon khong kem)",
        "The -에 불과하다: Chi khong hon / Chi la mot phan nho cua",
        "The -에 지나지 않다: Chi la / Khong vuot qua khuon kho cua",
        "The -ㄴ/는다는 것은: Viec ma / Dieu rang (dan nhap menh de chu de)",
        "Van phong bao chi: Headlining, Passive Voice, Danh hoa dong tu",
        "Van phong hoc thuat: Trich dan, Ket luan, Muc dich nghien cuu",
        "Dau cau & Cach viet chinh ta tieng Han nang cao",
        "Lich su tieng Han: Han tu goc Trung Quoc vs Tu thuan Han Quoc",
        "Bien the ngon ngu: Tieng Han giai tre vs tieng Han nguoi lon",
    ]

    cycle_idx = 0
    while day <= 2000:
        mod = cycle_idx % 6
        if mod == 0:
            gram_idx = (cycle_idx // 6) % len(topik56_grammar)
            add("Ngu phap TOPIK5-6: " + topik56_grammar[gram_idx] + " — Van viet chinh xac", phase5, "topik56")
        elif mod == 1:
            add("Tu vung TOPIK5-6: Han tu hoc thuat nang cao & Tu mien mieu ta truu tuong nhom " + str((cycle_idx // 6) + 1), phase5, "topik56")
        elif mod == 2:
            add("Doc hieu TOPIK5-6: Phan tich bai bao kinh te / chinh tri / van hoa 600+ chu", phase5, "topik56")
        elif mod == 3:
            add("Nghe hieu TOPIK5-6: KBS World / Podcast kinh doanh toc do ban dia", phase5, "topik56")
        elif mod == 4:
            add("Giao tiep TOPIK5-6: Thuyet trinh chinh thuc + Debate co cau truc ve chu de xa hoi", phase5, "topik56")
        else:
            add("Viet TOPIK5-6: Bai luan hoc thuat 700-800 chu — Chuan TOPIK 6 diem cao", phase5, "topik56")
        cycle_idx += 1

    # ==========================================================
    # PHASE 6: Native & Chuyen gia (Day 2001 - 2500)
    # ==========================================================
    phase6 = "Phase 6: Native & Chuyen gia (Day 2001 - 2500)"
    native_topics = [
        "K-pop Lyrics Analysis: Phan tich ngon ngu trong bai hat — Slang, van hoa, nuance",
        "K-drama Language: Kieu noi cua nhan vat theo tuoi, quan he, hoan canh",
        "Tro choi chu Han (놀이): Nori-pan, 끝말잇기, 스피드퀴즈 — Van hoa ngon ngu",
        "Hai huoc tieng Han: Dad jokes (아재 개그), Pun, Wordplay — Hieu hu but ban dia",
        "Van hoc Han Quoc: Phan tich truyen ngan 현대 문학 (Van hoc hien dai)",
        "Bong Joon-ho & K-cinema: Ngon ngu va ky thuat ke chuyen trong phim Han",
        "Kinh ngu chuyen sau: Hospital / Legal / Business — Tu vung dung trong nghe nghiep",
        "Cheat codes giao tiep: 눈치, 빠르게 반응하는 법 — Hieu y nguoi Han nhanh",
        "Chuan bi phong van viec lam tieng Han: STAR Method bang tieng Han",
        "Di lam o Han Quoc: Van hoa cong so, Hoesik, Sunbae-hoobae relationships",
        "Tu vung vung mien: Gyeonggi-do vs Gyeongsang-do vs Jeolla-do — Nhan dien giong",
        "Phuong ngu Busan-speak: Giong Busan dac trung, tu vung rieng biet",
    ]

    cycle_idx = 0
    while day <= 2500:
        topic_idx = cycle_idx % len(native_topics)
        batch = (cycle_idx // len(native_topics)) + 1
        add("Native Mastery: " + native_topics[topic_idx] + " — Bai " + str(batch), phase6, "native")
        cycle_idx += 1

    return roadmap


def generate_markdown(roadmap_data):
    total = len(roadmap_data)
    md_lines = [
        "# Lộ Trình Học Tiếng Hàn – 2500 Ngày (Từ Hangul Đến TOPIK 6 + Gần Bản Địa)",
        "",
        "> Lưu ý quan trọng về thời gian thực tế: Tiếng Hàn thuộc nhóm ngôn ngữ khó với người Việt (hệ thống Hangul, Batchim phức tạp, Kính ngữ đa cấp),",
        "> để đạt TOPIK 6 cần khoảng 2.000-2.200 giờ học tập chất lượng, và thêm 800-1.200 giờ immersion để gần mức Native.",
        "> Với 30-45 phút/ngày (~0.6 giờ), thực tế sẽ mất khoảng 9-12 năm calendar time để hoàn thành toàn bộ nội dung.",
        "> 2500 'Day' trong file này là số ĐƠN VỊ NỘI DUNG (content units) theo khung TOPIK 1-6, không phải số ngày dương lịch.",
        "> Ở Phase TOPIK 4 trở lên, bạn có thể cần 2-4 ngày thực tế cho 1 'Day' để ôn lại và thực hành đủ — hoàn toàn bình thường.",
        "> Muốn rút ngắn: tăng lên 60-90 phút/ngày. Trình độ Native luôn là quá trình immersion liên tục.",
        "",
        "> Ký hiệu: Vỡ lòng/Hangul | TOPIK 1-2 | TOPIK 3-4 | TOPIK 5-6 | Bản địa — Tất cả đều dùng nhịp 30-45 phút/ngày.",
        "",
        "> Mục tiêu: Học Tiếng Hàn chuẩn sư phạm từ Bảng chữ Hangul đến TOPIK 6 + Near-Native.",
        "> Phạm vi: 6 Phase, 2500 ngày, bao phủ Hangul, Ngữ pháp, Từ vựng, Phát âm, Nghe, Đọc, Nói, Viết, Kính ngữ (존댓말) và Chuyên ngành.",
        "",
    ]

    for day_num in range(1, total + 1):
        if day_num not in roadmap_data:
            continue

        title, phase, level = roadmap_data[day_num]
        emoji, label, lvl_code = get_time(day_num)
        prev_topic = "Bat dau hanh trinh" if day_num == 1 else roadmap_data[day_num - 1][0]

        md_lines.append("## Day " + str(day_num) + " — " + title + " (" + emoji + " " + label + ")")
        md_lines.append("**Prompt:**")
        md_lines.append("Dong vai tro la Gia su tieng Han cap cao (Native Teacher / TOPIK Expert). Hom nay la Day " + str(day_num) + ": " + title + ".")
        md_lines.append("Giai doan: " + phase + ". Trinh do muc tieu: " + lvl_code.upper() + ".")
        md_lines.append("Noi dung hom qua: " + prev_topic + ".")
        md_lines.append("")
        md_lines.append("YEU CAU DAY HOC (Tuy theo loai bai — chi 30-45 phut, vua du tieu hoa):")
        md_lines.append("1. NEU LA HANGUL / PHAT AM: Mo ta cach doc cu the (vi tri luoi, moi, khe ho). Cho 5 tu vi du voi cach doc Romanization. Chi ra loi phat am dien hinh cua nguoi Viet (vi du: Sai am Batchim, Nham phu am cang/boc/thuong) va Drill cu the de sua.")
        md_lines.append("2. NEU LA NGU PHAP: Giai thich Cau truc + Quy tac + Sac thai (Nuance — dung khi nao, voi ai, van noi hay van viet). Cho 3 cau vi du thuc te (Hangul + Romanization + Dich Viet). Chi ro 1-2 loi sai pho bien cua nguoi Viet va cach tranh.")
        md_lines.append("3. NEU LA TU VUNG / THANH NGU / SLANG: Cho nghia chinh xac + vi du cau tu nhien. Phan biet sac thai (trang trong/ban, goi te/sach se). Cho 3-5 collocations pho bien nhat cua tu do.")
        md_lines.append("4. NEU LA DOC/NGHE/NOI/VIET: Cung cap doan hoi thoai / doan van mau 100-200 chu dung trinh do. Chu thich tu moi + Romanization. Giao nhiem vu cu the (tom tat, tra loi cau hoi, viet lai...)")
        md_lines.append("5. LOI SAI PHO BIEN CUA NGUOI VIET (BAT BUOC): Chi ra 2-3 loi nguoi Viet hay mac khi hoc phan nay (do anh huong cau truc tieng Viet, hoac nham with tieng Trung/Nhat). Giai thich vi sao sai va cach sua.")
        md_lines.append("")
        md_lines.append("BAI TAP THUC HANH (Vua van 30-45 phut, khong qua tai):")
        md_lines.append("Giao cho toi 3-5 cau bai tap phu hop (Dich / Dien tu / Sua loi / Tu dat cau). Cho toi lam xong roi moi cham diem va giai thich chi tiet.")
        md_lines.append("")
        md_lines.append("**Bài tập:**")
        md_lines.append("Thoi gian: " + label)
        md_lines.append("Chu de hom nay: " + title)
        md_lines.append("On lai hom qua: " + prev_topic)
        md_lines.append("Tu luyen: Hoan thanh 3-5 cau bai tap do AI giao o tren, nop lai de duoc cham diem & giai thich chi tiet.")
        md_lines.append("")
        md_lines.append("**Tags:** #korean #day" + str(day_num) + " #" + lvl_code)
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
    print("  Phase 1 (Hangul):    Day 1    - 200")
    print("  Phase 2 (TOPIK1-2):  Day 201  - 550")
    print("  Phase 3 (TOPIK3):    Day 551  - 1000")
    print("  Phase 4 (TOPIK4):    Day 1001 - 1500")
    print("  Phase 5 (TOPIK5-6):  Day 1501 - 2000")
    print("  Phase 6 (Native):    Day 2001 - 2500")
