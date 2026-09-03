"""language_profiler.py — Khảo sát & Hoạch định Định danh Tri thức Ngôn ngữ bằng AI.
Học hỏi từ AskCpl (domain_profiles.py):
- Tự động dùng Gemini AI phân tích bản chất ngôn ngữ (chữ viết, thanh điệu, ngữ pháp, văn hóa).
- Tự động suy luận số ngày thực tế cần thiết để đạt trình độ NHƯ NGƯỜI BẢN XỨ (Near-Native / C2).
- Tự động phân bổ số ngày cho 6 Chặng (Vỡ lòng -> Ghép âm -> Sơ cấp -> Trung cấp -> Cao cấp -> Bản xứ).
- Có bộ nhớ đệm Cache (data/language_profiles_cache.json) và cơ chế Fallback an toàn khi offline.
"""

from __future__ import annotations
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(BASE_DIR, "data", "language_profiles_cache.json")

JOURNEY_PHASES = [
    ("Vỡ lòng chữ cái & phát âm", "hệ chữ viết, bảng chữ cái/ký tự, quy tắc phát âm, thanh điệu, khẩu hình môi/lưỡi"),
    ("Ghép âm & Từ đơn sinh tồn", "ghép vần, từ đơn 1-2 âm tiết, số đếm, đại từ, mẫu câu ngắn 2-3 từ sinh tồn"),
    ("Sơ cấp đời sống", "mua sắm, ăn uống, hỏi đường, gia đình, sở thích, câu đơn & thì hiện tại"),
    ("Trung cấp công việc", "kể chuyện quá khứ/tương lai, liên từ, câu phức, giao tiếp công sở, bày tỏ ý kiến"),
    ("Cao cấp học thuật", "tranh biện, thuyết trình, email chuyên nghiệp, đọc báo chí, câu giả định, bị động"),
    ("Như người bản xứ", "thành ngữ (idioms), tiếng lóng (slang), chơi chữ, ẩn dụ, văn hóa & tư duy bản địa"),
]

STAGE_SHORT_TAGS = [
    "[Vỡ lòng]",
    "[Ghép âm]",
    "[Sơ cấp]",
    "[Trung cấp]",
    "[Cao cấp]",
    "[Bản xứ]",
]

LANGUAGE_PROFILE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "category_name": {"type": "STRING"},
        "recommended_days": {"type": "INTEGER"},
        "stage_days": {
            "type": "ARRAY",
            "items": {"type": "INTEGER"}
        },
        "persona": {"type": "STRING"},
        "instruction": {"type": "STRING"},
        "mandatory_milestones": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        }
    },
    "required": ["title", "category_name", "recommended_days", "stage_days", "persona", "instruction"]
}


def load_cached_language_profiles() -> dict:
    """Nạp danh sách hồ sơ ngôn ngữ đã được AI khảo sát từ cache JSON."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8", errors="replace") as f:
                return json.loads(f.read())
        except Exception:
            return {}
    return {}


def save_cached_language_profiles(profiles: dict):
    """Lưu danh sách hồ sơ ngôn ngữ vào cache JSON (đảm bảo thư mục data tồn tại)."""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _build_stages_info(stage_days: list) -> list:
    """Xây dựng cấu trúc danh sách 6 chặng hoàn chỉnh với start_day/end_day."""
    stages_info = []
    current_start = 1
    for i, (name, desc) in enumerate(JOURNEY_PHASES):
        days_count = stage_days[i] if i < len(stage_days) else 30
        stages_info.append({
            "stage_idx": i,
            "stage_num": i + 1,
            "name": name,
            "tag": STAGE_SHORT_TAGS[i] if i < len(STAGE_SHORT_TAGS) else f"[Chặng {i+1}]",
            "desc": desc,
            "target_days": days_count,
            "start_day": current_start,
            "end_day": current_start + days_count - 1,
        })
        current_start += days_count
    return stages_info


def get_rule_based_fallback_profile(language: str) -> dict:
    """Fallback quy tắc chuẩn mực khi AI offline hoặc không có API key.
    Phân loại độ khó theo khoa học ngôn ngữ để đảm bảo số ngày đạt chuẩn BẢN XỨ (600 - 1500 ngày)."""
    lang_lower = (language or "").strip().lower()

    # Nhóm 4: Tượng hình, Kanji/Hanzi, Kính ngữ đa cấp, SOV, Patchim (Nhật, Trung, Hàn, Ả Rập...)
    if any(k in lang_lower for k in ["nhật", "japanese", "japan", "nihongo",
                                     "trung", "chinese", "mandarin", "hán", "hoa", "hsk",
                                     "hàn", "korean", "hangul", "topik",
                                     "ả rập", "arabic", "cantonese"]):
        category_name = "Chuẩn Bản Xứ C2 • Nhóm Tượng Hình & Kính Ngữ Phức Tạp (Nhật / Trung / Hàn / Ả Rập)"
        recommended_days = 1260
        stage_days = [60, 90, 280, 350, 300, 180]  # Tổng 1260 ngày (~3.5 năm)
        persona = f"Chuyên gia Ngôn ngữ & Tư duy Bản xứ {language}"
        instruction = (
            f"Bản ngữ hóa toàn diện {language}: Nắm vững hệ chữ tượng hình/âm tiết, "
            f"ngữ pháp chuyên sâu, văn hóa kính ngữ phân tầng và thành ngữ điển cố đời sống."
        )
        milestones = [
            "chu_viet_can_ban", "ghep_am_sinh_ton", "giao_tiep_a1_a2",
            "cong_so_b1_b2", "kinh_ngu_phan_tang", "thanh_ngu_dien_co",
            "van_hoa_ngam_c2", "chuyen_nganh_capstone"
        ]

    # Nhóm 3: Hệ chữ riêng hoặc biến cách nhiều (Nga, Thái, Hy Lạp, Hindi, Ba Lan, Thổ Nhĩ Kỳ...)
    elif any(k in lang_lower for k in ["nga", "russian", "thái", "thai", "hy lạp", "greek",
                                       "hindi", "ba lan", "polish", "thổ nhĩ kỳ", "turkish",
                                       "ukraine", "hebrew"]):
        category_name = "Chuẩn Bản Xứ C2 • Nhóm Hệ Chữ Riêng & Đa Biến Cách (Nga / Thái / Hy Lạp...)"
        recommended_days = 980
        stage_days = [50, 80, 220, 270, 230, 130]  # Tổng 980 ngày (~2.7 năm)
        persona = f"Chuyên gia Ngôn ngữ & Diễn đạt Thuần thục {language}"
        instruction = (
            f"Bản ngữ hóa {language}: Hệ chữ cái riêng biệt, bảng chia 6-7 cách ngữ pháp, "
            f"tiền tố/hậu tố phái sinh từ và phong cách biểu đạt tự nhiên của người bản địa."
        )
        milestones = [
            "bang_chu_cai_chuan", "chia_cach_ngu_phap", "hoi_thoai_thuc_te",
            "cau_phuc_hop_b2", "van_hoc_bao_chi_c1", "tieng_long_slang_c2"
        ]

    # Nhóm 2: Ngôn ngữ Latinh có chia giống & thì phức tạp (Pháp, Đức, Tây Ban Nha, Ý, Bồ Đào Nha...)
    elif any(k in lang_lower for k in ["pháp", "french", "đức", "german", "tây ban nha", "spanish",
                                       "ý", "italian", "bồ đào nha", "portuguese",
                                       "indonesia", "thụy điển", "swedish", "hà lan", "dutch"]):
        category_name = "Chuẩn Bản Xứ C2 • Ngôn ngữ Latinh Đa Cấu Trúc & Chia Thì (Đức / Pháp / TBN...)"
        recommended_days = 840
        stage_days = [40, 60, 190, 230, 200, 120]  # Tổng 840 ngày (~2.3 năm)
        persona = f"Bậc thầy Ngôn ngữ & Tư duy Bản ngữ {language}"
        instruction = (
            f"Bản ngữ hóa {language}: Khẩu hình âm mũi/rung lưỡi, hệ thống giống đực/cái/trung, "
            f"thể giả định Subjunctive/Konjunktiv và phản xạ tranh luận học thuật."
        )
        milestones = [
            "phat_am_khau_hinh", "chia_thi_va_giong", "giao_tiep_doi_song",
            "the_gia_dinh_b2", "tranh_bien_xa_luan_c1", "thanh_ngu_van_hoa_c2"
        ]

    # Nhóm 1: Latinh phổ biến / Tiếng Anh và các ngôn ngữ khác
    else:
        category_name = "Chuẩn Bản Xứ C2 • Ngôn ngữ Phổ Thông Toàn Cầu (Tiếng Anh...)"
        recommended_days = 700
        stage_days = [35, 50, 160, 190, 165, 100]  # Tổng 700 ngày (~2 năm)
        persona = f"Bậc thầy Diễn đạt & Phản xạ Bản địa {language}"
        instruction = (
            f"Bản ngữ hóa {language}: Xóa bỏ hoàn toàn thói quen dịch thô từ tiếng Việt, "
            f"làm chủ Collocations tự nhiên, Phrasal Verbs đa tầng nghĩa, Slang thời đại và tư duy tranh biện logic."
        )
        milestones = [
            "ngu_am_ipa_chuan", "cau_don_sinh_ton", "tu_tin_giao_tiep_a2",
            "collocations_phrasal_verbs_b2", "academic_writing_c1", "native_slang_nuance_c2"
        ]

    return {
        "language": language,
        "title": f"Lộ trình Bản xứ Toàn diện: {language}",
        "category_name": category_name,
        "total_days": recommended_days,
        "recommended_days": recommended_days,
        "stage_days": stage_days,
        "stages": _build_stages_info(stage_days),
        "persona": persona,
        "instruction": instruction,
        "mandatory_milestones": milestones,
        "is_ai_reasoned": False,
    }


def get_or_create_language_profile(language: str, coord=None, log_fn=None, force_refresh: bool = False) -> dict:
    """Lấy hồ sơ định danh tri thức Bản xứ cho một ngôn ngữ:
    1. Kiểm tra Cache file (nếu có và không force_refresh -> trả về ngay lập tức).
    2. Nếu chưa có hoặc force_refresh: Gọi Gemini AI (qua coord) để phân tích sâu sắc.
    3. Nếu gọi AI thất bại / không có API key: Dùng Rule-based Fallback chuẩn BẢN XỨ.
    """
    lang_clean = (language or "").strip()
    if not lang_clean:
        lang_clean = "Ngoại ngữ"
    lang_key = lang_clean.casefold()

    # 1. Kiểm tra Cache
    if not force_refresh:
        cache = load_cached_language_profiles()
        if lang_key in cache:
            entry = cache[lang_key]
            # Đảm bảo có đầy đủ cấu trúc stages_info
            st_days = entry.get("stage_days") or [35, 50, 160, 190, 165, 100]
            entry["stages"] = _build_stages_info(st_days)
            entry["total_days"] = sum(st_days)
            entry["language"] = lang_clean
            entry["is_ai_reasoned"] = True
            if log_fn:
                log_fn(f"🧠 [AI PROFILER] Nạp từ Cache: '{entry.get('title')}' — Tổng {entry['total_days']} ngày Bản xứ C2.")
            return entry

    # 2. Khảo sát động bằng AI nếu có Coordinator
    if coord is not None:
        if log_fn:
            log_fn(f"🔍 [AI PROFILER] Đang dùng Gemini AI phân tích bản chất ngôn ngữ & số ngày Bản xứ cho '{lang_clean}'...")

        prompt = f"""Bạn là Kiến trúc sư Trưởng Khảo sát & Hoạch định Tri thức Ngôn ngữ Quốc tế.
Hãy phân tích chuyên sâu ngôn ngữ: '{lang_clean}' để thiết lập Hồ Sơ Định Danh Bản Xứ Hóa Toàn Diện (Native-Level Language Blueprint).

Mục tiêu cốt lõi: Đưa người học Việt Nam từ con số 0 (Zero) đạt đến năng lực NHƯ NGƯỜI BẢN XỨ (Near-Native / C2 CEFR).

YÊU CẦU ĐỊNH LƯỢNG QUY MÔ THỰC TẾ VÀ TRUNG THỰC:
1. Đánh giá bản chất ngôn ngữ:
   - Hệ chữ viết (Latinh, Ký tự tượng hình Hanzi/Kanji, Chữ tượng thanh Hangul, Bảng chữ cái Cyrillic, Chữ Abjad/Ả Rập...).
   - Ngữ âm & Thanh điệu (Tones, Pitch Accent, Trọng âm, Khẩu hình).
   - Ngữ pháp & Trật tự từ (SVO, SOV, Biến cách ngữ pháp, Chia thì/giống, Kính ngữ).
   - Độ lệch ngôn ngữ đối với người Việt (Language Distance).
   - Chiều sâu văn hóa, Điển cố, Slang, Thành ngữ, và Ngữ cảnh ngầm (High-Context Culture).

2. 'recommended_days': Số ngày học thực tế (mỗi ngày 1 bài học chất lượng 45-60 phút) để từ con số 0 đạt đến mức BẢN XỨ THỰC THỤ:
   - Nhóm Latinh quen thuộc (Tiếng Anh...): 600 đến 800 ngày.
   - Nhóm Latinh biến cách / Chia giống phức tạp (Pháp, Đức, Tây Ban Nha, Ý, Bồ Đào Nha...): 750 đến 950 ngày.
   - Nhóm Hệ chữ riêng / Biến cách nhiều (Nga, Thái, Hy Lạp, Hindi, Ba Lan, Thổ Nhĩ Kỳ...): 850 đến 1150 ngày.
   - Nhóm Khó nhất đối với người học (Tượng hình, Thanh điệu, Kanji/Hanzi, Ngữ pháp ngược SOV, Kính ngữ đa cấp: Nhật, Trung, Hàn, Ả Rập...): 1200 đến 1600 ngày.
   TUYỆT ĐỐI KHÔNG cào bằng ~300 ngày. Phải định lượng trung thực theo khối lượng kiến thức bản xứ!

3. 'stage_days': Mảng đúng 6 số nguyên biểu thị số ngày phân bổ cho 6 Chặng (tổng các phần tử PHẢI BẰNG recommended_days):
   - Chặng 1: Vỡ lòng (Chữ cái, Khẩu hình phát âm, Quy tắc biến âm)
   - Chặng 2: Ghép âm & Từ đơn sinh tồn (Tập đọc, Mẫu câu ngắn 2-3 từ)
   - Chặng 3: Sơ cấp (Giao tiếp đời sống cơ bản A1-A2)
   - Chặng 4: Trung cấp (Tự tin diễn đạt & Công sở B1-B2)
   - Chặng 5: Cao cấp (Học thuật, Báo chí, Thuyết trình C1)
   - Chặng 6: Bản xứ (Thành ngữ điển cố, Tiếng lóng, Văn hóa ngầm & Tư duy bản địa C2)

4. 'category_name': Định danh độ khó & nhóm ngôn ngữ (ví dụ: 'Chuẩn Bản Xứ C2 • Tượng Hình & Kính Ngữ Phức Tạp (JLPT N1 / C2)').
5. 'persona': Định danh danh xưng người học khi hoàn thành (ví dụ: 'Bậc thầy Ngôn ngữ & Tư duy Bản xứ Tiếng Nhật').
6. 'mandatory_milestones': Mảng 8-15 từ khóa snake_case biểu thị các cột mốc bắt buộc không thể thiếu.
7. 'instruction': Lời khuyên sư phạm chiến lược định hướng toàn bộ khóa học (tối đa 250 từ).

Chỉ trả về JSON DUY NHẤT theo schema, không kèm chữ nào ngoài JSON."""

        try:
            res = coord.request(prompt, response_schema=LANGUAGE_PROFILE_SCHEMA)
            if res.get("ok"):
                raw_text = (res.get("text") or "").strip()
                # Bỏ bọc ```json nếu có
                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
                raw_text = re.sub(r"\s*```$", "", raw_text).strip()
                start = raw_text.find("{")
                end = raw_text.rfind("}")
                if start != -1 and end > start:
                    data = json.loads(raw_text[start:end+1])
                    st_days = data.get("stage_days") or []
                    if isinstance(st_days, list) and len(st_days) == 6 and all(isinstance(x, int) and x > 0 for x in st_days):
                        total_d = sum(st_days)
                        data["recommended_days"] = total_d
                        data["total_days"] = total_d
                        data["language"] = lang_clean
                        data["stages"] = _build_stages_info(st_days)
                        data["is_ai_reasoned"] = True

                        # Lưu vào cache
                        cache = load_cached_language_profiles()
                        # Lưu bản sao nhẹ không chứa duplicate stages
                        to_cache = dict(data)
                        cache[lang_key] = to_cache
                        save_cached_language_profiles(cache)

                        if log_fn:
                            log_fn(f"✅ [AI PROFILER] Khảo sát thành công: {data.get('category_name')} -> Khuyến nghị: {total_d} Ngày Bản Xứ.")
                        return data
        except Exception as e:
            if log_fn:
                log_fn(f"⚠️ [AI PROFILER] Lỗi khảo sát AI: {e}. Đang chuyển sang Profile Fallback chuẩn.")

    # 3. Fallback mặc định
    fallback = get_rule_based_fallback_profile(lang_clean)
    if log_fn:
        log_fn(f"🛡️ [AI PROFILER] Áp dụng Hồ sơ Bản xứ Chuẩn mực: {fallback['category_name']} — {fallback['total_days']} Ngày.")
    return fallback
